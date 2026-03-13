from __future__ import annotations
from typing import List, Tuple, Optional
from src.model.entities import Process, Segment

def popSrtn(ready: List[Process]) -> Process:
    """Lấy process có thời gian xử lý còn lại (remaining) ngắn nhất; tie-break theo arrival rồi seq (remaining -> arrival -> seq)."""
    if not ready:
        raise ValueError("ready is empty")

    bestIdx = 0
    bestKey = (ready[0].remaining, ready[0].arrival, ready[0].seq)
    for i in range(1, len(ready)):
        key = (ready[i].remaining, ready[i].arrival, ready[i].seq)
        if key < bestKey:
            bestKey = key
            bestIdx = i

    return ready.pop(bestIdx)


def srtn(
    queueId: str,
    ready: List[Process],
    t: int,
    budget: int,
    segments: List[Segment],
    nextArrivalTime: Optional[int],
) -> Tuple[int, int]:
    """
    Chạy 1 bước SRTN (preemptive). dt bị giới hạn bởi nextArrivalTime
    để đảm bảo process mới được đưa vào trước khi tiếp tục chọn lịch.
    """
    if budget <= 0 or not ready:
        return t, budget

    # Bảo đảm: Nếu đúng ngay mốc thời gian có tiến trình mới gia nhập (arrival), thì bộ điều khiển (controller) đã nạp đối tượng đó vào trước khi gọi SRTN
    p = popSrtn(ready)

    # Tính thời lượng xử lý khả thi nhất (dt)
    dt = min(p.remaining, budget)
    if nextArrivalTime is not None and nextArrivalTime > t:
        dt = min(dt, nextArrivalTime - t)

    # dt == 0 nghĩa là controller gọi sai thứ tự – trả về ngay, không làm gì
    if dt <= 0:
        ready.append(p)
        return t, budget

    start = t
    end = t + dt
    segments.append(Segment(start=start, end=end, queue_id=queueId, pid=p.pid))

    p.remaining -= dt
    t = end
    budget -= dt

    if p.remaining == 0:
        p.completion = t
    else:
        ready.append(p)

    return t, budget