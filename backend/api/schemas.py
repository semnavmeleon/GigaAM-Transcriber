from typing import List, Optional
from pydantic import BaseModel


class ComponentInfo(BaseModel):
    id: str
    type: str           # "model" | "addon"
    name: str
    description: str
    size_mb: int
    installed: bool
    active: bool = False
    installing: bool = False
    install_percent: float = 0.0
    install_elapsed: int = 0
    install_error: Optional[str] = None


class SystemInfoResponse(BaseModel):
    cuda_available: bool
    device_name: Optional[str] = None
    components: List[ComponentInfo]


class DownloadProgressResponse(BaseModel):
    percent: float
    done: bool
    running: bool = False
    error: Optional[str] = None
    current_mb: int = 0
    total_mb: int = 448
    variant: str = "v2_ctc"


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
