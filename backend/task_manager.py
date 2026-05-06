import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class ChunkResult:
    index: int
    start: float
    end: float
    text: str
    error: Optional[str] = None


@dataclass
class FileResult:
    filename: str
    chunks: List[ChunkResult] = field(default_factory=list)
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class Task:
    task_id: str
    state: TaskState = TaskState.PENDING
    total_files: int = 0
    done_files: int = 0
    current_file: str = ""
    total_chunks: int = 0
    done_chunks: int = 0
    results: List[FileResult] = field(default_factory=list)
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    output_dir: Optional[Path] = None
    fmt: str = "txt"


class TaskManager:
    def __init__(self, ttl_seconds: int = 3600):
        self._tasks: Dict[str, Task] = {}
        self._ttl = ttl_seconds

    def create(self, fmt: str = "txt") -> Task:
        task_id = str(uuid.uuid4())
        task = Task(task_id=task_id, fmt=fmt)
        self._tasks[task_id] = task
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def cancel(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task and task.state == TaskState.RUNNING:
            task.cancel_event.set()
            task.state = TaskState.CANCELLED
            return True
        return False

    def cleanup_expired(self):
        now = time.time()
        expired = [
            tid for tid, t in self._tasks.items()
            if t.finished_at and (now - t.finished_at) > self._ttl
        ]
        for tid in expired:
            task = self._tasks.pop(tid, None)
            if task and task.output_dir and task.output_dir.exists():
                import shutil
                shutil.rmtree(task.output_dir, ignore_errors=True)


task_manager = TaskManager()
