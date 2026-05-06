import logging
import os
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_model = None
_model_lock = threading.Lock()
_download_state = {
    "running": False,
    "done": False,
    "error": None,
}

GIGAAM_MODEL_VARIANT = os.getenv("GIGAAM_MODEL", "v2_ctc")
CACHE_DIR = Path.home() / ".cache" / "gigaam"
EXPECTED_SIZE_BYTES = 950 * 1024 * 1024  # ~950 MB conservative upper bound


def _current_cache_size() -> int:
    if not CACHE_DIR.exists():
        return 0
    return sum(f.stat().st_size for f in CACHE_DIR.rglob("*") if f.is_file())


def is_model_loaded() -> bool:
    return _model is not None


def is_model_cached() -> bool:
    size = _current_cache_size()
    return size > 100 * 1024 * 1024  # >100 MB means something is there


def get_model():
    return _model


def load_model_sync(variant: str = GIGAAM_MODEL_VARIANT):
    global _model
    import gigaam
    logger.info("Loading GigaAM model variant=%s", variant)
    m = gigaam.load_model(variant)
    with _model_lock:
        _model = m
    logger.info("GigaAM model loaded")
    return m


def download_progress() -> dict:
    size = _current_cache_size()
    percent = min(100.0, size / EXPECTED_SIZE_BYTES * 100)
    done = _download_state["done"]
    error = _download_state["error"]
    return {
        "percent": percent if not done else 100.0,
        "done": done,
        "error": error,
        "current_mb": size // (1024 * 1024),
        "total_mb": EXPECTED_SIZE_BYTES // (1024 * 1024),
    }


def start_download_and_load(variant: str = GIGAAM_MODEL_VARIANT):
    global _download_state
    if _download_state["running"] or _download_state["done"]:
        return
    _download_state = {"running": True, "done": False, "error": None}

    def _run():
        global _download_state
        try:
            load_model_sync(variant)
            _download_state["done"] = True
        except Exception as e:
            logger.exception("Model download/load failed")
            _download_state["error"] = str(e)
        finally:
            _download_state["running"] = False

    t = threading.Thread(target=_run, daemon=True)
    t.start()


# Worker-process initializer for ProcessPoolExecutor
_worker_model = None


def worker_init(variant: str):
    global _worker_model
    import gigaam
    logger.info("Worker: loading GigaAM model variant=%s", variant)
    _worker_model = gigaam.load_model(variant)
    logger.info("Worker: model ready")


def worker_transcribe(wav_path: str) -> str:
    global _worker_model
    if _worker_model is None:
        raise RuntimeError("Worker model not initialised")
    result = _worker_model.transcribe(wav_path)
    return result if isinstance(result, str) else str(result)
