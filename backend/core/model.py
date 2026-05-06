import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_model = None
_model_lock = threading.Lock()
_current_variant: Optional[str] = None
_active_variant: Optional[str] = None  # user-selected preferred variant
_download_state = {
    "running": False,
    "done": False,
    "error": None,
    "variant": None,
    "started_at": None,
}

GIGAAM_MODEL_VARIANT = os.getenv("GIGAAM_MODEL", "v2_ctc")
CACHE_DIR = Path.home() / ".cache" / "gigaam"

AVAILABLE_VARIANTS = ["v2_ctc", "v2_rnnt"]
_VARIANT_SIZES = {
    "v2_ctc":  448 * 1024 * 1024,
    "v2_rnnt": 448 * 1024 * 1024,
    "v1_ctc":  300 * 1024 * 1024,
    "v1_rnnt": 300 * 1024 * 1024,
}
_VARIANT_LABELS = {
    "v2_ctc":  "GigaAM v2 CTC",
    "v2_rnnt": "GigaAM v2 RNNT",
}
_VARIANT_DESC = {
    "v2_ctc":  "Быстрая модель, подходит для большинства задач",
    "v2_rnnt": "Точнее на сложных записях, медленнее",
}


def _patch_torch_load():
    try:
        import torch
        _orig = torch.load
        def _load_compat(*args, **kwargs):
            kwargs.setdefault('weights_only', False)
            return _orig(*args, **kwargs)
        torch.load = _load_compat
    except Exception:
        pass


def _variant_cache_path(variant: str) -> Path:
    return CACHE_DIR / f"{variant}.ckpt"


def _drop_partial(variant: str):
    p = _variant_cache_path(variant)
    if not p.exists():
        return
    min_bytes = _VARIANT_SIZES.get(variant, 100 * 1024 * 1024) // 2
    if p.stat().st_size < min_bytes:
        logger.warning("Removing partial checkpoint for %s", variant)
        p.unlink()


def _variant_cached(variant: str) -> bool:
    p = _variant_cache_path(variant)
    if not p.exists():
        return False
    expected = _VARIANT_SIZES.get(variant, 448 * 1024 * 1024)
    return p.stat().st_size >= expected * 0.9


def _current_cache_size() -> int:
    if not CACHE_DIR.exists():
        return 0
    return sum(f.stat().st_size for f in CACHE_DIR.rglob("*") if f.is_file())


def is_model_loaded() -> bool:
    return _model is not None


def is_model_cached(variant: Optional[str] = None) -> bool:
    if variant:
        return _variant_cached(variant)
    return _current_cache_size() > 100 * 1024 * 1024


def get_model():
    return _model


def get_current_variant() -> Optional[str]:
    return _current_variant


def get_active_variant() -> Optional[str]:
    """User-selected active variant, falling back to first installed."""
    if _active_variant and _variant_cached(_active_variant):
        return _active_variant
    for v in AVAILABLE_VARIANTS:
        if _variant_cached(v):
            return v
    return None


def set_active_variant(variant: str):
    global _active_variant
    _active_variant = variant


def uninstall(variant: str):
    global _model, _current_variant, _active_variant, _download_state
    p = _variant_cache_path(variant)
    if p.exists():
        p.unlink()
        logger.info("Removed checkpoint for %s", variant)
    # Reset memory state if this was the loaded/active model
    if _current_variant == variant:
        with _model_lock:
            _model = None
            _current_variant = None
    if _active_variant == variant:
        _active_variant = None
    if _download_state.get("variant") == variant:
        _download_state = {"running": False, "done": False, "error": None, "variant": None}


def load_model_sync(variant: str = GIGAAM_MODEL_VARIANT):
    global _model, _current_variant
    _patch_torch_load()
    _drop_partial(variant)
    import gigaam
    logger.info("Loading GigaAM model variant=%s", variant)
    m = gigaam.load_model(variant)
    with _model_lock:
        _model = m
        _current_variant = variant
    logger.info("GigaAM model loaded (variant=%s)", variant)
    return m


def download_progress(variant: Optional[str] = None) -> dict:
    v = variant or _download_state.get("variant") or GIGAAM_MODEL_VARIANT
    expected = _VARIANT_SIZES.get(v, 448 * 1024 * 1024)
    p = _variant_cache_path(v)
    size = p.stat().st_size if p.exists() else 0
    percent = min(99.0, size / expected * 100)  # cap at 99 until fully verified
    running = _download_state["running"] and _download_state.get("variant") == v
    done = _variant_cached(v)
    error = _download_state["error"] if _download_state.get("variant") == v else None
    elapsed = 0
    if _download_state.get("started_at"):
        elapsed = int(time.time() - _download_state["started_at"])
    return {
        "percent": 100.0 if done else percent,
        "done": done,
        "running": running,
        "error": error,
        "current_mb": size // (1024 * 1024),
        "total_mb": expected // (1024 * 1024),
        "variant": v,
        "elapsed": elapsed,
    }


def start_download_and_load(variant: str = GIGAAM_MODEL_VARIANT):
    global _download_state
    if _download_state["running"]:
        return
    if _variant_cached(variant):
        # Already downloaded — just load into memory
        pass
    _download_state = {"running": True, "done": False, "error": None, "variant": variant, "started_at": time.time()}

    def _run():
        global _download_state, _active_variant
        try:
            load_model_sync(variant)
            if _active_variant is None:
                _active_variant = variant
            _download_state = {"running": False, "done": True, "error": None, "variant": variant, "started_at": None}
        except Exception as e:
            logger.exception("Model download/load failed")
            _download_state = {"running": False, "done": False, "error": str(e), "variant": variant, "started_at": None}

    threading.Thread(target=_run, daemon=True).start()


# ── Worker-process helpers ────────────────────────────────────────────────────

_worker_model = None


def worker_init(variant: str):
    global _worker_model
    _patch_torch_load()
    import gigaam
    logger.info("Worker: loading GigaAM model variant=%s", variant)
    _worker_model = gigaam.load_model(variant)
    logger.info("Worker: model ready (variant=%s)", variant)


def worker_transcribe(wav_path: str) -> str:
    global _worker_model
    if _worker_model is None:
        raise RuntimeError("Worker model not initialised")
    result = _worker_model.transcribe(wav_path)
    return result if isinstance(result, str) else str(result)
