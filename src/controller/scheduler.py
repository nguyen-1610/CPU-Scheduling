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
    """Chuyển tất cả process có arrival <= t vào ready list tương ứng."""
    while notArrived and notArrived[0].arrival <= t:
        p = notArrived.pop(0)
        qi = queueIndex[p.queue_id]
        readyLists[qi].append(p)


def is_system_idle(readyLists: List[List[Process]]) -> bool:
    return all(len(lst) == 0 for lst in readyLists)


def peek_next_arrival_time(notArrived: List[Process], queueId: str) -> Optional[int]:
    """Thời điểm process tiếp theo đến cho hàng đợi queueId; None nếu không còn."""
    for p in notArrived:
        if p.queue_id == queueId:
            return p.arrival
    return None


def run_scheduling(
    queues: List[QueueConfig],
    processes: List[Process],
) -> Tuple[List[Segment], List[Process]]:

    if not queues:
        return [], processes

    queueIndex = {q.queue_id: i for i, q in enumerate(queues)}

    t = 0
    queuePtr = 0
    segments: List[Segment] = []

    notArrived = list(processes)  # đã được sắp xếp theo arrival từ parser
    readyLists: List[List[Process]] = [[] for _ in queues]

    total = len(processes)
    finishedCount = 0

    while finishedCount < total:
        admit_new_processes(t, notArrived, readyLists, queueIndex)

        # CPU nhàn rỗi (idle) -> tua nhanh thời gian (jump time) tới tiến trình đến tiếp theo
        if is_system_idle(readyLists):
            if not notArrived:
                break
            # Không có process nào sẵn sàng → nhảy thẳng tới arrival tiếp theo
            t = notArrived[0].arrival
            continue

        qIdx = pickNextQueue(queuePtr, readyLists)
        qConf = queues[qIdx]
        qId = qConf.queue_id
        budget = qConf.time_slice
        policyName = qConf.policy
        policyRunner = get_policy_runner(policyName)

        while budget > 0 and len(readyLists[qIdx]) > 0:
            # Tính toán xem bao giờ thì có tiến trình mới gia nhập CÙNG KHỐI HÀNG ĐỢI NÀY,
            # dùng cho việc đánh giá ngắt (preempt) (nếu chiến lược là SRTN thì cần quan tâm).
            nextArrivalTime = peek_next_arrival_time(notArrived, qId)

            # SRTN cần đảm bảo process mới cùng queue được admit trước khi chọn lịch.
            # Guard: nếu admit không giảm notArrived (process đến thuộc queue khác), không continue.
            if policyName == "SRTN":
                if nextArrivalTime is not None and nextArrivalTime == t:
                    prev_len = len(notArrived)
                    admit_new_processes(t, notArrived, readyLists, queueIndex)
                    if len(notArrived) < prev_len:
                        continue

            t, budget = policyRunner(
                qId,
                readyLists[qIdx],
                t,
                budget,
                segments,
                nextArrivalTime,
            )

            admit_new_processes(t, notArrived, readyLists, queueIndex)
            finishedCount = sum(1 for p in processes if p.completion is not None)

        queuePtr = (qIdx + 1) % len(queues)

    return segments, processes