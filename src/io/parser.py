
from __future__ import annotations

from typing import List, Tuple
from src.model.entities import QueueConfig, Process

def parse_input(file_path: str) -> Tuple[List[QueueConfig], List[Process]]:
    # 1) Đọc file theo từng dòng, lọc bỏ hoàn toàn các dòng rỗng
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    if not lines:
        raise ValueError("Input file is empty!")

    # 2) Đọc số N (số lượng hàng đợi của hệ thống)
    try:
        n = int(lines[0])
    except ValueError:
        raise ValueError("Line 1 must be an integer N (number of queues).")

    if n <= 0:
        raise ValueError("N must be > 0.")

    if len(lines) < 1 + n:
        raise ValueError("Not enough lines for queue configurations.")

    # 3) Đọc N dòng tiếp theo để lấy cấu hình chi tiết cho từng hàng đợi
    queues: List[QueueConfig] = []
    for i in range(1, 1 + n):
        parts = lines[i].split()
        if len(parts) != 3:
            raise ValueError(f"Queue config line {i+1} must have 3 tokens: QID TimeSlice Policy")

        qid, ts_str, policy = parts
        ts = int(ts_str)

        if policy not in ("SJF", "SRTN"):
            raise ValueError(f"Invalid policy '{policy}' in line {i+1}. Must be SJF or SRTN.")

        queues.append(QueueConfig(queue_id=qid, time_slice=ts, policy=policy))

    queue_ids = {q.queue_id for q in queues}

    # 4) Đọc toàn bộ các dòng còn lại để lấy mô tả về tiến trình (process)
    processes: List[Process] = []
    seq = 0
    for i in range(1 + n, len(lines)):
        parts = lines[i].split()
        if len(parts) != 4:
            raise ValueError(f"Process line {i+1} must have 4 tokens: PID Arrival Burst QueueID")

        pid, arr_str, burst_str, qid = parts
        arrival = int(arr_str)
        burst = int(burst_str)

        if qid not in queue_ids:
            raise ValueError(f"Process {pid} references unknown queue '{qid}' (line {i+1}).")

        processes.append(Process(pid=pid, arrival=arrival, burst=burst, queue_id=qid, seq=seq))
        seq += 1

    # 5) Sắp xếp ổn định theo thời gian đến (ưu tiên arrival, cùng arrival thì giữ thứ tự seq)
    processes.sort(key=lambda p: (p.arrival, p.seq))

    return queues, processes