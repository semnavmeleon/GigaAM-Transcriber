import json
from typing import List
from backend.task_manager import ChunkResult


def _srt_ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def format_txt(chunks: List[ChunkResult]) -> str:
    parts = [c.text.strip() for c in chunks if c.text and not c.error]
    return " ".join(parts)


def format_srt(chunks: List[ChunkResult]) -> str:
    lines = []
    index = 1
    for c in chunks:
        if c.error or not c.text.strip():
            continue
        lines.append(str(index))
        lines.append(f"{_srt_ts(c.start)} --> {_srt_ts(c.end)}")
        lines.append(c.text.strip())
        lines.append("")
        index += 1
    return "\n".join(lines)


def format_json(filename: str, chunks: List[ChunkResult]) -> str:
    valid = [c for c in chunks if not c.error]
    data = {
        "filename": filename,
        "chunks": [
            {"start": c.start, "end": c.end, "text": c.text.strip()}
            for c in valid
        ],
        "full_text": " ".join(c.text.strip() for c in valid if c.text),
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def render(filename: str, chunks: List[ChunkResult], fmt: str) -> str:
    if fmt == "srt":
        return format_srt(chunks)
    if fmt == "json":
        return format_json(filename, chunks)
    return format_txt(chunks)


def file_extension(fmt: str) -> str:
    return {"txt": ".txt", "srt": ".srt", "json": ".json"}.get(fmt, ".txt")
