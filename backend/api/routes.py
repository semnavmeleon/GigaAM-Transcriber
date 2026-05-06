import asyncio
import logging
import os
import shutil
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.api.schemas import (
    ChunkResultSchema,
    DownloadProgressResponse,
    FileResultSchema,
    ModelStatusResponse,
    TaskStatusResponse,
    TranscribeResponse,
)
from backend.core import audio as audio_mod
from backend.core import formatter
from backend.core import model as model_mod
from backend.task_manager import ChunkResult, FileResult, TaskState, task_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

TMP_DIR = Path(os.getenv("TMP_DIR", "./tmp"))
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "2"))
GIGAAM_MODEL_VARIANT = os.getenv("GIGAAM_MODEL", "v2_ctc")

_executor: Optional[ProcessPoolExecutor] = None


def get_executor() -> ProcessPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ProcessPoolExecutor(
            max_workers=MAX_WORKERS,
            initializer=model_mod.worker_init,
            initargs=(GIGAAM_MODEL_VARIANT,),
        )
    return _executor


# ── Model endpoints ──────────────────────────────────────────────────────────

@router.get("/model/status", response_model=ModelStatusResponse)
async def model_status():
    return ModelStatusResponse(
        loaded=model_mod.is_model_loaded() or model_mod.is_model_cached(),
        variant=GIGAAM_MODEL_VARIANT,
    )


@router.post("/model/download", status_code=202)
async def model_download():
    if model_mod.is_model_loaded():
        return {"detail": "already loaded"}
    model_mod.start_download_and_load(GIGAAM_MODEL_VARIANT)
    return {"detail": "download started"}


@router.get("/model/download-progress", response_model=DownloadProgressResponse)
async def model_download_progress():
    prog = model_mod.download_progress()
    return DownloadProgressResponse(
        percent=prog["percent"],
        done=prog["done"],
        error=prog["error"],
        current_mb=prog.get("current_mb", 0),
        total_mb=prog.get("total_mb", 900),
    )


# ── Transcription endpoints ───────────────────────────────────────────────────

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    fmt: str = Form("txt"),
    chunk_size: int = Form(30),
    use_vad: bool = Form(True),
    device: str = Form("cpu"),
):
    if not model_mod.is_model_loaded() and not model_mod.is_model_cached():
        raise HTTPException(status_code=400, detail="Model not loaded")

    task = task_manager.create(fmt=fmt)
    task_dir = TMP_DIR / task.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    task.output_dir = task_dir

    saved: List[Path] = []
    for upload in files:
        dest = task_dir / upload.filename
        with dest.open("wb") as f:
            while chunk := await upload.read(1024 * 1024):
                f.write(chunk)
        saved.append(dest)

    background_tasks.add_task(
        _run_transcription, task.task_id, saved, fmt, chunk_size, use_vad, device
    )
    return TranscribeResponse(task_id=task.task_id)


async def _run_transcription(
    task_id: str,
    files: List[Path],
    fmt: str,
    chunk_size: int,
    use_vad: bool,
    device: str,
):
    task = task_manager.get(task_id)
    if not task:
        return

    task.state = TaskState.RUNNING
    task.total_files = len(files)
    loop = asyncio.get_event_loop()
    executor = get_executor()
    start_time = time.time()

    for file_path in files:
        if task.cancel_event.is_set():
            break

        file_result = FileResult(filename=file_path.name)
        task.current_file = file_path.name
        task.done_chunks = 0
        task.total_chunks = 0

        try:
            # Use file index as name — avoids special chars (brackets, Cyrillic)
            # in paths that break ffmpeg on Windows
            file_idx = len(task.results)
            wav_path = str(task.output_dir / f"audio_{file_idx:04d}.wav")
            await loop.run_in_executor(None, audio_mod.convert_to_wav, str(file_path), wav_path)

            file_result.duration = await loop.run_in_executor(None, audio_mod.get_duration, wav_path)
            chunk_tmp = str(task.output_dir / f"chunks_{file_idx:04d}")
            os.makedirs(chunk_tmp, exist_ok=True)

            if use_vad:
                chunks = await loop.run_in_executor(
                    None, audio_mod.split_vad, wav_path, chunk_size, chunk_tmp
                )
            else:
                chunks = await loop.run_in_executor(
                    None, audio_mod.split_fixed, wav_path, chunk_size, chunk_tmp
                )

            task.total_chunks = len(chunks)

            for idx, (chunk_path, start, end) in enumerate(chunks):
                if task.cancel_event.is_set():
                    break
                try:
                    text = await loop.run_in_executor(
                        executor, model_mod.worker_transcribe, chunk_path
                    )
                    file_result.chunks.append(ChunkResult(index=idx, start=start, end=end, text=text))
                except Exception as e:
                    logger.error("Chunk %d of %s failed: %s", idx, file_path.name, e)
                    file_result.chunks.append(
                        ChunkResult(index=idx, start=start, end=end, text="", error=str(e))
                    )
                task.done_chunks = idx + 1

            # Write result file
            content = formatter.render(file_path.name, file_result.chunks, fmt)
            ext = formatter.file_extension(fmt)
            out_file = task.output_dir / (file_path.stem + ext)
            out_file.write_text(content, encoding="utf-8")

        except Exception as e:
            logger.exception("File %s failed: %s", file_path.name, e)
            file_result.error = str(e)

        task.results.append(file_result)
        task.done_files += 1

    task.state = TaskState.DONE if not task.cancel_event.is_set() else TaskState.CANCELLED
    task.finished_at = time.time()
    task_manager.cleanup_expired()


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
                ChunkResultSchema(
                    index=c.index, start=c.start, end=c.end,
                    text=c.text, error=c.error,
                )
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

    media_types = {
        ".txt": "text/plain",
        ".srt": "text/plain",
        ".json": "application/json",
    }
    return FileResponse(
        path=str(result_path),
        media_type=media_types.get(ext, "application/octet-stream"),
        filename=result_path.name,
    )
