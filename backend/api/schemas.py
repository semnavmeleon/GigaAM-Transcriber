from typing import List, Optional
from pydantic import BaseModel


class ModelStatusResponse(BaseModel):
    loaded: bool
    variant: str


class DownloadProgressResponse(BaseModel):
    percent: float
    done: bool
    error: Optional[str] = None
    current_mb: int = 0
    total_mb: int = 900


class TranscribeResponse(BaseModel):
    task_id: str


class ChunkResultSchema(BaseModel):
    index: int
    start: float
    end: float
    text: str
    error: Optional[str] = None


class FileResultSchema(BaseModel):
    filename: str
    chunks: List[ChunkResultSchema] = []
    error: Optional[str] = None
    duration: float = 0.0


class TaskStatusResponse(BaseModel):
    state: str
    total_files: int
    done_files: int
    current_file: str
    total_chunks: int
    done_chunks: int
    error: Optional[str] = None
    elapsed: Optional[float] = None
    fmt: str = "txt"
    results: Optional[List[FileResultSchema]] = None
