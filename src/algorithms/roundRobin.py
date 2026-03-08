
from __future__ import annotations
from typing import Sequence, Any

def pickNextQueue(queuePtr: int, ready: Sequence[Sequence[Any]]) -> int:
    """
    queuePtr: con trỏ hàng đợi hiện tại
    ready: danh sách các hàng đợi
    """
    n = len(ready)
    if n == 0:
        raise ValueError("No queues configured")

    for k in range(n):
        q = (queuePtr + k) % n #quay vòng lại
        if len(ready[q]) > 0:
            return q

    raise ValueError("All queues are empty")