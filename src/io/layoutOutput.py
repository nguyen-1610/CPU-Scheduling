
from __future__ import annotations
from typing import List
from src.model.entities import Segment, Process

def mergeSegments(segments: List[Segment]) -> List[Segment]:
    """
    Gộp các khoảng thời gian (segment) chạy liên tục của cùng một tiến trình 
    thuộc một hàng đợi nhất định lại thành một đoạn nối tiếp duy nhất cho dễ nhìn.
    """
    if not segments:
        return []

    merged = [segments[0]]
    for cur in segments[1:]:
        last = merged[-1]
        if last.queue_id == cur.queue_id and last.pid == cur.pid and last.end == cur.start:
            last.end = cur.end
        else:
            merged.append(cur)
    return merged

def formatCpuDiagram(segments: List[Segment]) -> str:
    segments = mergeSegments(segments)

    title = "==================== CPU SCHEDULING DIAGRAM ===================="
    col1, col2, col3 = 18, 12, 10
    header = f"{'[Start - End]':<{col1}}{'Queue':<{col2}}{'Process':<{col3}}"
    sep = "-" * (col1 + col2 + col3)

    lines = [title, "", header, sep]
    for s in segments:
        startEnd = f"[{s.start} - {s.end}]"
        lines.append(f"{startEnd:<{col1}}{s.queue_id:<{col2}}{s.pid:<{col3}}")
    return "\n".join(lines)

def formatProcessStats(processes: List[Process]) -> str:
    title = "==================== PROCESS STATISTICS ===================="
    colP, colA, colB, colC, colT, colW = 10, 10, 10, 14, 14, 10
    header = (
        f"{'Process':<{colP}}"
        f"{'Arrival':<{colA}}"
        f"{'Burst':<{colB}}"
        f"{'Completion':<{colC}}"
        f"{'Turnaround':<{colT}}"
        f"{'Waiting':<{colW}}"
    )
    sep = "-" * (colP + colA + colB + colC + colT + colW)

    def pidKey(p: Process):
        # Trích xuất ID số cho tiến trình P1, P2, v.v để sắp thứ tự trực quan giống y hệt mẫu (1, 2, ... 10)
        try:
            return int(p.pid[1:])
        except:
            return p.pid

    ps = sorted(processes, key=pidKey)

    lines = [title, "", header, sep]

    turnaroundList = []
    waitingList = []

    for p in ps:
        if p.completion is None:
            completion = -1
            turnaround = -1
            waiting = -1
        else:
            completion = p.completion
            turnaround = completion - p.arrival
            waiting = turnaround - p.burst
            turnaroundList.append(turnaround)
            waitingList.append(waiting)

        lines.append(
            f"{p.pid:<{colP}}"
            f"{p.arrival:<{colA}}"
            f"{p.burst:<{colB}}"
            f"{completion:<{colC}}"
            f"{turnaround:<{colT}}"
            f"{waiting:<{colW}}"
        )

    lines.append(sep)

    if turnaroundList:
        avgT = sum(turnaroundList) / len(turnaroundList)
        avgW = sum(waitingList) / len(waitingList)
        lines.append(f"Average Turnaround Time : {avgT:.1f}")
        lines.append(f"Average Waiting Time    : {avgW:.1f}")

    return "\n".join(lines)

def buildReport(segments: List[Segment], processes: List[Process]) -> str:
    return formatCpuDiagram(segments) + "\n\n" + formatProcessStats(processes) + "\n"