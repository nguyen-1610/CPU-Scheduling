# src/controller/scheduler.py
from __future__ import annotations

from typing import List, Tuple, Optional

from src.model.entities import QueueConfig, Process, Segment
from src.algorithms.roundRobin import pickNextQueue
from src.algorithms.registry import get_policy_runner


def admit_new_processes(
    t: int,
    notArrived: List[Process],
    readyLists: List[List[Process]],
    queueIndex: dict[str, int],
) -> None:
    """
    Chuyển tất cả các tiến trình có thời gian đến (arrival) <= t từ danh sách chưa đến (notArrived)
    vào danh sách sẵn sàng (ready list) của hàng đợi tương ứng.
    Giả định: danh sách notArrived đã được sắp xếp theo thời gian đến và thứ tự xuất hiện (seq).
    """
    while notArrived and notArrived[0].arrival <= t:
        p = notArrived.pop(0)
        qi = queueIndex[p.queue_id]
        readyLists[qi].append(p)


def is_system_idle(readyLists: List[List[Process]]) -> bool:
    return all(len(lst) == 0 for lst in readyLists)


def peek_next_arrival_time(notArrived: List[Process], queueId: str) -> Optional[int]:
    """
    Tìm thời gian đến tiếp theo trong nhóm các tiến trình chưa đến (notArrived) thuộc hàng đợi queueId.
    Trả về None nếu không còn tiến trình nào trong tương lai cho hàng đợi đó.
    """
    for p in notArrived:
        if p.queue_id == queueId:
            return p.arrival
    return None


def run_scheduling(
    queues: List[QueueConfig],
    processes: List[Process],
) -> Tuple[List[Segment], List[Process]]:
    """
    Thực hiện lập lịch cho toàn bộ hệ thống:
    - Định vị hàng đợi theo vòng (Round Robin).
    - Trong mỗi hàng đợi: áp dụng chiến lược SJF hoặc SRTN (dựa vào cấu hình đầu vào).
    Trả về: danh sách các đoạn thời gian thực thi (segments) và danh sách tiến trình (đã cập nhật thời gian hoàn thành).
    """
    if not queues:
        return [], processes

    queueIndex = {q.queue_id: i for i, q in enumerate(queues)}

    t = 0
    queuePtr = 0
    segments: List[Segment] = []

    notArrived = list(processes)  # đã được sắp xếp từ bước đọc file (parser)
    readyLists: List[List[Process]] = [[] for _ in queues]

    total = len(processes)
    finishedCount = 0

    while finishedCount < total:
        admit_new_processes(t, notArrived, readyLists, queueIndex)

        # CPU nhàn rỗi (idle) -> tua nhanh thời gian (jump time) tới tiến trình đến tiếp theo
        if is_system_idle(readyLists):
            if not notArrived: # không còn tiến trình nào đến
                break
            t = notArrived[0].arrival # tua nhanh thời gian tới tiến trình đến tiếp theo
            continue

        qIdx = pickNextQueue(queuePtr, readyLists)
        qConf = queues[qIdx]
        qId = qConf.queue_id
        budget = qConf.time_slice
        policyName = qConf.policy
        policyRunner = get_policy_runner(policyName)

        # Chạy các tiến trình trong hàng đợi hiện tại, trong phạm vi ngân sách thời gian cho phép
        while budget > 0 and len(readyLists[qIdx]) > 0:
            # Tính toán xem bao giờ thì có tiến trình mới gia nhập CÙNG KHỐI HÀNG ĐỢI NÀY,
            # dùng cho việc đánh giá ngắt (preempt) (nếu chiến lược là SRTN thì cần quan tâm).
            nextArrivalTime = peek_next_arrival_time(notArrived, qId)

            # Đảm bảo invariants cho SRTN: nếu có arrival mới đúng tại t thì phải push trước
            if policyName == "SRTN":
                if nextArrivalTime is not None and nextArrivalTime == t:
                    admit_new_processes(t, notArrived, readyLists, queueIndex)
                    continue

            t, budget = policyRunner(
                qId,
                readyLists[qIdx],
                t,
                budget,
                segments,
                nextArrivalTime,
            )

            # Sau khi thời gian tăng lên, có thể sẽ có những tiến trình mới vừa đến, ta cần đưa chúng vào lưới chờ
            admit_new_processes(t, notArrived, readyLists, queueIndex)

            # Cập nhật số lượng tiến trình đã hoàn thành thành công (cách này chậm mà chắc)
            finishedCount = sum(1 for p in processes if p.completion is not None)

        queuePtr = (qIdx + 1) % len(queues)

    return segments, processes