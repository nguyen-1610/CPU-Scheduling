from dataclasses import dataclass
from typing import Optional, Literal

Policy = Literal["SJF", "SRTN"]


@dataclass
class QueueConfig:
    queue_id: str
    time_slice: int
    policy: Policy


@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    queue_id: str
    seq: int = 0  # thứ tự đọc từ file, dùng tie-break

    remaining: int = 0
    completion: Optional[int] = None

    def __post_init__(self):
        if self.burst <= 0:
            raise ValueError(f"Process '{self.pid}': burst must be > 0 (got {self.burst}).")
        if self.remaining == 0:
            self.remaining = self.burst


@dataclass
class Segment:
    start: int
    end: int
    queue_id: str
    pid: str