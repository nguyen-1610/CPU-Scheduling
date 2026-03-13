
from __future__ import annotations
from typing import List, Tuple, Optional
from src.model.entities import Process, Segment

def popSrtn(ready: List[Process]) -> Process:
    """
    Thuật toán SRTN (Shortest Remaining Time Next): Xếp theo thời gian xử lý còn lại (remaining) từ bé đến lớn.
    Xử lý hòa kết quả (tie-break): Ưu tiên lần lượt theo thứ tự (remaining -> arrival -> seq).
    """
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
    Thực thi 1 khung thời gian theo thuật toán SRTN trong 1 hàng đợi, có thể bị ngắt (preempted) nếu có tiến trình chờ mới.
    - Duyệt tiến trình có trạng thái thời gian cần xử lý thấp nhất.
    - Định mức thời gian chạy (dt) bằng giá trị nhỏ nhất của: thời gian làm việc còn lại, ngân sách chạy cho phép, 
      hoặc quỹ thời gian tính từ hiện tại cho tới khi có tiến trình mới tới (nextArrivalTime - để ngắt hợp lý).
    - Tạo phân đoạn hiển thị (Segment).
    - Điều chỉnh, cập nhật thời lượng xử lý còn lại (remaining) hoặc báo hoàn thành (completion).
    - Nếu tiến trình thực thi chưa xong trọn vẹn tiến độ -> Đưa lại vào hàng chờ (ready) để đợi tới lượt sau.
    Trả về bộ kết quả gồm: (Thời gian định vị hiện thời tNew, Quỹ ngân sách đã tiêu hao budgetLeft).
    """
    if budget <= 0 or not ready:
        return t, budget

    # Bảo đảm: Nếu đúng ngay mốc thời gian có tiến trình mới gia nhập (arrival), thì bộ điều khiển (controller) đã nạp đối tượng đó vào trước khi gọi SRTN
    p = popSrtn(ready)

    # Tính thời lượng xử lý khả thi nhất (dt)
    dt = min(p.remaining, budget)
    if nextArrivalTime is not None and nextArrivalTime > t:
        dt = min(dt, nextArrivalTime - t)

    # Nếu dt == 0, có nghĩa là thời khắc `t` bằng đúng lúc một tiến trình mới tới `nextArrivalTime`, bộ điều khiển xử lý ngắt sai thứ tự
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