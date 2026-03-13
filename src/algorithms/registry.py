from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from src.model.entities import Process, Segment
from src.algorithms.sjf import sjf
from src.algorithms.srtn import srtn


# Kiểu chung định nghĩa cho mọi thuật toán (policy): chạy 1 bước trong 1 hàng đợi
PolicyRunner = Callable[
    [
        str,  # queue_id: Mã hàng đợi
        List[Process], # Danh sách các tiến trình đang đợi
        int,  # t: Thời gian hiện tại
        int,  # budget: Lượng thời gian cho phép chạy (time slice)
        List[Segment], # Lưu vết chạy CPU
        Optional[int],  # next_arrival_time: thời gian tiến trình mới đến (nếu chính sách cần ngắt)
    ],
    Tuple[int, int],
]


def _run_sjf(
    queue_id: str,
    ready: List[Process],
    t: int,
    budget: int,
    segments: List[Segment],
    next_arrival_time: Optional[int] = None,
) -> Tuple[int, int]:
    """
    Hàm trung gian (Adapter) để SJF khớp với khung PolicyRunner.
    SJF (Shortest Job First) chạy không ngắt nên không cần quan tâm next_arrival_time.
    """
    return sjf(queue_id, ready, t, budget, segments)


def _run_srtn(
    queue_id: str,
    ready: List[Process],
    t: int,
    budget: int,
    segments: List[Segment],
    next_arrival_time: Optional[int],
) -> Tuple[int, int]:
    """
    Hàm trung gian (Adapter) cho SRTN: Truyền thời gian tới của tiến trình tiếp theo (next_arrival_time)
    xuống srtn để nó có thể quyết định ngắt (preempt) hợp lý.
    """
    return srtn(queue_id, ready, t, budget, segments, next_arrival_time)


_REGISTRY: Dict[str, PolicyRunner] = {
    "SJF": _run_sjf,
    "SRTN": _run_srtn,
}


def register_policy(name: str, runner: PolicyRunner) -> None:
    """
    Cho phép mở rộng (Extensibility): Đăng ký thêm thuật toán mới ở bên ngoài
    mà không cần phải sửa nội dung code cốt lõi của mạch mô phỏng chính.
    """
    _REGISTRY[name] = runner


def get_policy_runner(name: str) -> PolicyRunner:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise ValueError(f"Unknown scheduling policy: {name}") from None

