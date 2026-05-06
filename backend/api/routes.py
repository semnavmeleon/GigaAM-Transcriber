import asyncio
import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.api.schemas import (
    ChunkResultSchema,
    ComponentInfo,
    DownloadProgressResponse,
    FileResultSchema,
    SystemInfoResponse,
    TaskStatusResponse,
    TranscribeResponse,
)
from backend.core import audio as audio_mod
from backend.core import formatter
from backend.core import model as model_mod
from backend.core import punctuation as punct_mod
from backend.task_manager import ChunkResult, FileResult, TaskState, task_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

TMP_DIR = Path(os.getenv("TMP_DIR", "./tmp"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "2"))

_executor: Optional[ProcessPoolExecutor] = None
_executor_variant: Optional[str] = None


def get_executor(variant: str) -> ProcessPoolExecutor:
    global _executor, _executor_variant
    if _executor is None or _executor_variant != variant:
        if _executor is not None:
            _executor.shutdown(wait=False)
        _executor = ProcessPoolExecutor(
            max_workers=MAX_WORKERS,
            initializer=model_mod.worker_init,
            initargs=(variant,),
        )
        _executor_variant = variant
    return _executor


# ── System / hub info ─────────────────────────────────────────────────────────

@router.get("/system/info", response_model=SystemInfoResponse)
async def system_info():
    import torch
    cuda = torch.cuda.is_available()
    active = model_mod.get_active_variant()

    components: List[ComponentInfo] = []
    for variant in model_mod.AVAILABLE_VARIANTS:
        prog = model_mod.download_progress(variant)
        components.append(ComponentInfo(
            id=variant,
            type="model",
            name=model_mod._VARIANT_LABELS.get(variant, variant),
            description=model_mod._VARIANT_DESC.get(variant, ""),
            size_mb=model_mod._VARIANT_SIZES.get(variant, 448 * 1024 * 1024) // (1024 * 1024),
            installed=model_mod.is_model_cached(variant),
            active=active == variant,
            installing=prog.get("running", False),
            install_percent=prog.get("percent", 0.0),
            install_elapsed=prog.get("elapsed", 0),
            install_current_mb=prog.get("current_mb", 0),
            install_total_mb=prog.get("total_mb", 448),
            install_error=prog.get("error"),
        ))

    pp = punct_mod.install_progress()
    components.append(ComponentInfo(
        id="punctuation",
        type="addon",
        name="Расстановка пунктуации",
        description="deepmultilingualpunctuation · XLM-RoBERTa",
        size_mb=2240,
        installed=punct_mod.is_installed(),
        active=False,
        installing=pp.get("running", False),
        install_percent=pp.get("percent", 0.0),
        install_elapsed=pp.get("elapsed", 0),
        install_current_mb=0,
        install_total_mb=2240,
        install_error=pp.get("error"),
    ))

    return SystemInfoResponse(
        cuda_available=cuda,
        device_name=torch.cuda.get_device_name(0) if cuda else None,
        components=components,
    )


# ── Model endpoints ───────────────────────────────────────────────────────────

@router.post("/model/install", status_code=202)
async def model_install(variant: str = Form(...)):
    if variant not in model_mod.AVAILABLE_VARIANTS:
        raise HTTPException(400, f"Unknown variant")
    model_mod.start_download_and_load(variant)
    return {"detail": f"installing {variant}"}


@router.delete("/model/{variant}", status_code=204)
async def model_uninstall(variant: str):
    if variant not in model_mod.AVAILABLE_VARIANTS:
        raise HTTPException(400, "Unknown variant")
    model_mod.uninstall(variant)
    global _executor, _executor_variant
    if _executor_variant == variant and _executor is not None:
        _executor.shutdown(wait=False)
        _executor = None
        _executor_variant = None


@router.post("/model/set-active", status_code=200)
async def model_set_active(variant: str = Form(...)):
    if variant not in model_mod.AVAILABLE_VARIANTS:
        raise HTTPException(400, "Unknown variant")
    if not model_mod.is_model_cached(variant):
        raise HTTPException(400, "Model not installed")
    model_mod.set_active_variant(variant)
    return {"detail": f"active model set to {variant}"}


@router.get("/model/progress/{variant}", response_model=DownloadProgressResponse)
async def model_progress(variant: str):
    prog = model_mod.download_progress(variant)
    return DownloadProgressResponse(
        percent=prog["percent"],
        done=prog["done"],
        running=prog.get("running", False),
        error=prog.get("error"),
        current_mb=prog.get("current_mb", 0),
        total_mb=prog.get("total_mb", 448),
        variant=prog.get("variant", variant),
    )


# Legacy endpoint — keep for backward compat
@router.post("/model/download", status_code=202)
async def model_download(variant: str = Form(os.getenv("GIGAAM_MODEL", "v2_ctc"))):
    model_mod.start_download_and_load(variant)
    return {"detail": f"loading {variant}"}


@router.get("/model/download-progress", response_model=DownloadProgressResponse)
async def model_download_progress(variant: Optional[str] = None):
    v = variant or model_mod.get_active_variant() or "v2_ctc"
    prog = model_mod.download_progress(v)
    return DownloadProgressResponse(**{
        "percent": prog["percent"], "done": prog["done"],
        "running": prog.get("running", False), "error": prog.get("error"),
        "current_mb": prog.get("current_mb", 0), "total_mb": prog.get("total_mb", 448),
        "variant": prog.get("variant", v),
    })


# ── Punctuation endpoints ─────────────────────────────────────────────────────

@router.post("/punctuation/install", status_code=202)
async def punct_install():
    if not punct_mod.is_available():
        raise HTTPException(400, "deepmultilingualpunctuation package not installed")
    punct_mod.start_install()
    return {"detail": "installing punctuation model"}


@router.delete("/punctuation", status_code=204)
async def punct_uninstall():
    punct_mod.uninstall()


@router.get("/punctuation/progress")
async def punct_progress():
    return punct_mod.install_progress()


# ── Transcription endpoints ───────────────────────────────────────────────────

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    fmt: str = Form("txt"),
    chunk_size: int = Form(15),
    use_vad: bool = Form(True),
    use_punctuation: bool = Form(False),
    model_variant: str = Form(""),
    device: str = Form("cpu"),
):
    variant = model_variant or model_mod.get_active_variant()
    if not variant:
        raise HTTPException(400, "No model installed")
    if not model_mod.is_model_cached(variant):
        raise HTTPException(400, f"Model {variant} not installed")

    task = task_manager.create(fmt=fmt)
    task_dir = TMP_DIR / task.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    task.output_dir = task_dir

    saved: List[tuple] = []
    for idx, upload in enumerate(files):
        ext = Path(upload.filename).suffix.lower()
        dest = task_dir / f"upload_{idx:04d}{ext}"
        with dest.open("wb") as f:
            while chunk := await upload.read(1024 * 1024):
                f.write(chunk)
        saved.append((dest, upload.filename))

    background_tasks.add_task(
        _run_transcription,
        task.task_id, saved, fmt, chunk_size, use_vad,
        use_punctuation, variant,
    )
    return TranscribeResponse(task_id=task.task_id)


async def _run_transcription(
    task_id: str,
    files: List[tuple],
    fmt: str,
    chunk_size: int,
    use_vad: bool,
    use_punctuation: bool,
    model_variant: str,
):
    task = task_manager.get(task_id)
    if not task:
        return

    task.state = TaskState.RUNNING
    task.total_files = len(files)
    loop = asyncio.get_event_loop()
    executor = get_executor(model_variant)

    for file_path, original_name in files:
        if task.cancel_event.is_set():
            break

        file_result = FileResult(filename=original_name)
        task.current_file = original_name
        task.done_chunks = 0
        task.total_chunks = 0

        try:
            chunk_tmp = str(task.output_dir / f"chunks_{file_path.stem}")
            os.makedirs(chunk_tmp, exist_ok=True)

            duration, chunks = await loop.run_in_executor(
                None, audio_mod.load_split, str(file_path), chunk_size, chunk_tmp, use_vad,
            )
            file_result.duration = duration
            task.total_chunks = len(chunks)

            for idx, (chunk_path, start, end) in enumerate(chunks):
                if task.cancel_event.is_set():
                    break
                try:
                    text = await loop.run_in_executor(
                        executor, model_mod.worker_transcribe, chunk_path
                    )
                    if use_punctuation and text.strip():
                        text = await loop.run_in_executor(None, punct_mod.punctuate, text)
                    file_result.chunks.append(ChunkResult(index=idx, start=start, end=end, text=text))
                except Exception as e:
                    logger.error("Chunk %d of %s failed: %s", idx, original_name, e)
                    file_result.chunks.append(
                        ChunkResult(index=idx, start=start, end=end, text="", error=str(e))
                    )
                task.done_chunks = idx + 1

            content = formatter.render(original_name, file_result.chunks, fmt)
            ext = formatter.file_extension(fmt)
            out_file = task.output_dir / (Path(original_name).stem + ext)
            out_file.write_text(content, encoding="utf-8")

        except Exception as e:
            logger.exception("File %s failed: %s", original_name, e)
            file_result.error = str(e)

        task.results.append(file_result)
        task.done_files += 1

    task.state = TaskState.DONE if not task.cancel_event.is_set() else TaskState.CANCELLED
    task.finished_at = time.time()
    task_manager.cleanup_expired()


# ── Task endpoints ────────────────────────────────────────────────────────────

@router.get("/task/{task_id}/status", response_model=TaskStatusResponse)
async def task_status(task_id: str):
    task = task_manager.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    elapsed = None
    if task.finished_at:
        elapsed = task.finished_at - task.created_at
    results = [
        FileResultSchema(
            filename=fr.filename,
            duration=fr.duration,
            error=fr.error,
            chunks=[
                ChunkResultSchema(index=c.index, start=c.start, end=c.end, text=c.text, error=c.error)
                for c in fr.chunks
            ],
        )
        for fr in task.results
    ] if task.results else None

    return TaskStatusResponse(
        state=task.state,
        total_files=task.total_files,
        done_files=task.done_files,
        current_file=task.current_file,
        total_chunks=task.total_chunks,
        done_chunks=task.done_chunks,
        error=task.error,
        elapsed=elapsed,
        fmt=task.fmt,
        results=results,
    )


@router.delete("/task/{task_id}", status_code=204)
async def cancel_task(task_id: str):
    ok = task_manager.cancel(task_id)
    if not ok:
        task = task_manager.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")


@router.get("/task/{task_id}/download")
async def download_result(task_id: str, file: str, fmt: str = "txt"):
    task = task_manager.get(task_id)
    if not task or not task.output_dir:
        raise HTTPException(status_code=404, detail="Task not found")
    stem = Path(file).stem
    ext = formatter.file_extension(fmt)
    result_path = task.output_dir / (stem + ext)
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Result file not found")
    media_types = {".txt": "text/plain", ".srt": "text/plain", ".json": "application/json"}
    return FileResponse(
        path=str(result_path),
        media_type=media_types.get(ext, "application/octet-stream"),
        filename=result_path.name,
    )
