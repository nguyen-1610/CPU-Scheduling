from __future__ import annotations

from typing import Iterable, List, Tuple

from src.model.entities import Process, QueueConfig


def _normalize_lines(lines: Iterable[str]) -> List[str]:
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


def _parse_lines(lines: List[str]) -> Tuple[List[QueueConfig], List[Process]]:
    if not lines:
        raise ValueError("Input file is empty!")

    try:
        n = int(lines[0])
    except ValueError as exc:
        raise ValueError("Line 1 must be an integer N (number of queues).") from exc

    if n <= 0:
        raise ValueError("N must be > 0.")

    if len(lines) < 1 + n:
        raise ValueError("Not enough lines for queue configurations.")

    queues: List[QueueConfig] = []
    for i in range(1, 1 + n):
        parts = lines[i].split()
        if len(parts) != 3:
            raise ValueError(f"Queue config line {i + 1} must have 3 tokens: QID TimeSlice Policy")

        qid, ts_str, policy = parts
        try:
            ts = int(ts_str)
        except ValueError as exc:
            raise ValueError(f"Queue config line {i + 1}: time_slice must be an integer.") from exc

        if ts <= 0:
            raise ValueError(f"Queue config line {i + 1}: time_slice must be > 0 (got {ts}).")

        if policy not in ("SJF", "SRTN"):
            raise ValueError(f"Invalid policy '{policy}' in line {i + 1}. Must be SJF or SRTN.")

        queues.append(QueueConfig(queue_id=qid, time_slice=ts, policy=policy))

    queue_ids = {q.queue_id for q in queues}

    processes: List[Process] = []
    seq = 0
    for i in range(1 + n, len(lines)):
        parts = lines[i].split()
        if len(parts) != 4:
            raise ValueError(f"Process line {i + 1} must have 4 tokens: PID Arrival Burst QueueID")

        pid, arr_str, burst_str, qid = parts
        try:
            arrival = int(arr_str)
            burst = int(burst_str)
        except ValueError as exc:
            raise ValueError(
                f"Process line {i + 1}: arrival and burst must be integers."
            ) from exc

        if arrival < 0:
            raise ValueError(f"Process {pid} (line {i + 1}): arrival time must be >= 0 (got {arrival}).")

        if burst <= 0:
            raise ValueError(f"Process {pid} (line {i + 1}): burst time must be > 0 (got {burst}).")

        if qid not in queue_ids:
            raise ValueError(f"Process {pid} references unknown queue '{qid}' (line {i + 1}).")

        processes.append(Process(pid=pid, arrival=arrival, burst=burst, queue_id=qid, seq=seq))
        seq += 1

    if not processes:
        import warnings

        warnings.warn("Input file has queue configurations but no processes defined.", UserWarning)

    processes.sort(key=lambda p: (p.arrival, p.seq))
    return queues, processes


def parse_input_text(text: str) -> Tuple[List[QueueConfig], List[Process]]:
    return _parse_lines(_normalize_lines(text.splitlines()))


def parse_input_bytes(raw_bytes: bytes, encoding: str = "utf-8-sig") -> Tuple[List[QueueConfig], List[Process]]:
    try:
        text = raw_bytes.decode(encoding)
    except UnicodeDecodeError as exc:
        raise ValueError(f"Unable to decode input bytes with {encoding}: {exc}") from exc

    return parse_input_text(text)
