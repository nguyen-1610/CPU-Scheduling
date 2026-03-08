
from dataclasses import dataclass
from typing import Optional, Literal

Policy = Literal["SJF", "SRTN"]

# QUEUE
@dataclass
class QueueConfig: 
    queue_id: str
    time_slice: int
    policy: Policy

# PROCESS
@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    queue_id: str
    seq: int = 0  # Dùng để phân định tie-break, luôn giữ sự ổn định thuận theo dữ liệu đọc từ file đầu tiên

    remaining: int = 0
    completion: Optional[int] = None

    def __post_init__(self):
        # set bắt đầu = burst
        if self.remaining == 0:
            self.remaining = self.burst

# SEGMENT
@dataclass
class Segment:
    start: int
    end: int
    queue_id: str
    pid: str