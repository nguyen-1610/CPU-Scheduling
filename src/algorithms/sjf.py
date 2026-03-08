# src/algorithms/sjf.py
"""
Thuật toán SJF (Shortest Job First) - Ưu tiên tiến trình có thời gian xử lý ngắn nhất.
"""

from __future__ import annotations

from typing import List, Tuple
from src.model.entities import Process, Segment


def pop_sjf(ready: List[Process]) -> Process:
    """
    Lấy ra tiến trình có thời gian xử lý còn lại (remaining) ngắn nhất từ hàng đợi sẵn sàng.
    Nếu có nhiều tiến trình có cùng remaining, ưu tiên theo thời gian đến (arrival), rồi theo thứ tự (seq).
    """
    if not ready:
        raise ValueError("ready is empty")

    best_idx = 0
    best_key = (ready[0].remaining, ready[0].arrival, ready[0].seq)
    for i in range(1, len(ready)):
        key = (ready[i].remaining, ready[i].arrival, ready[i].seq)
        if key < best_key:
            best_key = key
            best_idx = i

    return ready.pop(best_idx)


def sjf(
    queue_id: str,
    ready: List[Process],
    t: int,
    budget: int,
    segments: List[Segment],
) -> Tuple[int, int]:
    """
    Thực hiện lập lịch SJF cho một khoảng thời gian (budget).
    - queue_id: ID của hàng đợi.
    - ready: Danh sách tiến trình sẵn sàng.
    - t: Thời gian hiện tại.
    - budget: Thời gian có thể xử lý trong lần này.
    - segments: Danh sách các đoạn xử lý để ghi lại.
    Trả về thời gian mới và budget còn lại.
    """
    if budget <= 0 or not ready:
        return t, budget

    # Lấy tiến trình có thời gian xử lý ngắn nhất
    p = pop_sjf(ready)

    # Tính thời gian xử lý thực tế (không vượt quá budget)
    dt = min(p.remaining, budget)
    start = t
    end = t + dt

    # Ghi lại đoạn xử lý
    segments.append(Segment(start=start, end=end, queue_id=queue_id, pid=p.pid))

    # Cập nhật thời gian còn lại của tiến trình
    p.remaining -= dt
    t = end
    budget -= dt

    # Nếu tiến trình hoàn thành, ghi thời gian hoàn thành
    if p.remaining == 0:
        p.completion = t
    else:
        # Nếu chưa hoàn thành, đưa lại vào hàng đợi
        ready.append(p)

    return t, budget