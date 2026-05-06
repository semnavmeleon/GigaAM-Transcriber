import logging
import os
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_model = None
_lock = threading.Lock()
_install_state = {"running": False, "done": False, "error": None, "started_at": None}

_HF_MODEL_ID = "oliverguhr/fullstop-punctuation-multilang-large"
_HF_DIR_NAME = "models--oliverguhr--fullstop-punctuation-multilang-large"
_EXPECTED_BYTES = 2_300 * 1024 * 1024  # ~2.3 GB (model.safetensors is 2.24 GB)


def _hf_cache_dir() -> Path:
    hf_home = os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
    return Path(hf_home) / "hub" / _HF_DIR_NAME


def is_available() -> bool:
    try:
        import deepmultilingualpunctuation  # noqa: F401
        return True
    except ImportError:
        return False


def _cache_size() -> int:
    d = _hf_cache_dir()
    if not d.exists():
        return 0
    return sum(f.stat().st_size for f in d.rglob("*") if f.is_file())


def is_installed() -> bool:
    return _cache_size() > 2 * 1024 * 1024 * 1024  # > 2 GB means fully downloaded


def install_progress() -> dict:
    running = _install_state["running"]
    done = _install_state.get("done") or is_installed()
    elapsed = 0
    if _install_state.get("started_at"):
        elapsed = int(time.time() - _install_state["started_at"])
    return {
        "running": running,
        "done": done,
        "error": _install_state.get("error"),
        "percent": 100.0 if done else 0.0,
        "elapsed": elapsed,
    }


def start_install():
    global _install_state
    if _install_state["running"] or is_installed():
        return
    _install_state = {"running": True, "done": False, "error": None, "started_at": time.time()}

    def _run():
        global _install_state, _model
        try:
            from deepmultilingualpunctuation import PunctuationModel
            logger.info("Downloading punctuation model…")
            m = PunctuationModel()
            with _lock:
                _model = m
            _install_state = {"running": False, "done": True, "error": None, "started_at": None}
            logger.info("Punctuation model ready")
        except Exception as e:
            logger.exception("Punctuation install failed")
            _install_state = {"running": False, "done": False, "error": str(e), "started_at": None}

    threading.Thread(target=_run, daemon=True).start()


def uninstall():
    global _model, _install_state
    import shutil
    d = _hf_cache_dir()
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
        logger.info("Punctuation model removed from %s", d)
    with _lock:
        _model = None
    _install_state = {"running": False, "done": False, "error": None}


def _load():
    global _model
    if _model is not None:
        return _model
    if not is_installed():
        return None
    with _lock:
        if _model is not None:
            return _model
        try:
            from deepmultilingualpunctuation import PunctuationModel
            _model = PunctuationModel()
        except Exception as e:
            logger.warning("Could not load punctuation model: %s", e)
            _model = False
    return _model


def punctuate(text: str) -> str:
    if not text.strip():
        return text
    model = _load()
    if not model:
        return text
    try:
        return model.restore_punctuation(text)
    except Exception as e:
        logger.warning("Punctuation inference failed: %s", e)
        return text
