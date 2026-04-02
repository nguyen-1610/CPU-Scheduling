"""
detail_dialog.py – Dialog chi tiết: info file + bảng process + Gantt chart + metrics.

Phần A: Thông tin file (tên, ngày tạo, giờ tạo, size)
Phần B: Bảng process (PID, Arrival, Burst, QueueID, TimeSlice, Algorithm)
Phần C: Gantt chart (QPainter)
Phần D: Bảng metrics (Turnaround, Waiting, Average)
"""

from __future__ import annotations

from typing import List, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLabel, QTableWidget, QTableWidgetItem, QScrollArea, QMessageBox,
    QWidget, QSizePolicy,
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QPainter, QColor, QPen

from src.fat32.directory import FileEntry, parse_fat_date, parse_fat_time
from src.model.entities import QueueConfig, Process, Segment
from src.io.parser import parse_input
from src.controller.scheduler import run_scheduling
from src.io.layoutOutput import mergeSegments

import io


# ── Bảng màu cho Gantt chart ────────────────────────────────────────

_COLORS = [
    QColor("#4FC3F7"), QColor("#FF8A65"), QColor("#81C784"),
    QColor("#CE93D8"), QColor("#FFD54F"), QColor("#F06292"),
    QColor("#90CAF9"), QColor("#A5D6A7"), QColor("#FFAB91"),
    QColor("#80CBC4"), QColor("#B39DDB"), QColor("#FFF176"),
]


def _color_for(pid: str) -> QColor:
    """Chọn màu dựa trên PID hash."""
    h = 0
    for c in pid:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return _COLORS[h % len(_COLORS)]


# ── Gantt Widget ─────────────────────────────────────────────────────

class GanttWidget(QWidget):
    """Widget vẽ sơ đồ Gantt bằng QPainter."""

    CELL_W = 40   # pixels per time unit
    CELL_H = 36
    MARGIN_L = 20
    MARGIN_T = 30

    def __init__(self, segments: List[Segment], parent=None) -> None:
        super().__init__(parent)
        self._segments = mergeSegments(segments)
        if self._segments:
            total_time = self._segments[-1].end
        else:
            total_time = 1
        width = self.MARGIN_L + total_time * self.CELL_W + 40
        self.setMinimumSize(max(width, 400), self.MARGIN_T + self.CELL_H + 40)
        self.setFixedHeight(self.MARGIN_T + self.CELL_H + 50)

    def paintEvent(self, event) -> None:
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        font = QFont("Consolas", 8)
        qp.setFont(font)

        if not self._segments:
            qp.drawText(20, 30, "Không có dữ liệu để vẽ.")
            qp.end()
            return

        for seg in self._segments:
            x = self.MARGIN_L + seg.start * self.CELL_W
            w = (seg.end - seg.start) * self.CELL_W
            y = self.MARGIN_T
            h = self.CELL_H

            color = _color_for(seg.pid)
            qp.setBrush(color)
            qp.setPen(QPen(color.darker(130), 1))
            qp.drawRoundedRect(int(x), int(y), int(w), int(h), 4, 4)

            # Nhãn PID + Queue
            qp.setPen(Qt.black)
            label = f"{seg.pid}"
            qp.drawText(QRectF(x, y, w, h), Qt.AlignCenter, label)

            # Tick thời gian bắt đầu
            qp.setPen(Qt.darkGray)
            qp.drawText(int(x + 2), int(y + h + 14), str(seg.start))

        # Tick cuối cùng
        last = self._segments[-1]
        x_end = self.MARGIN_L + last.end * self.CELL_W
        qp.drawText(int(x_end + 2), int(self.MARGIN_T + self.CELL_H + 14), str(last.end))

        qp.end()


# ── Detail Dialog ────────────────────────────────────────────────────

class DetailDialog(QDialog):
    """Dialog xem chi tiết file .txt: info + process table + Gantt + metrics."""

    def __init__(self, entry: FileEntry, file_text: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Chi tiết – {entry.name}")
        self.setMinimumSize(860, 650)
        self.resize(960, 720)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ── Phần A: Thông tin file ──
        info_box = QGroupBox("Thông tin file")
        info_box.setFont(QFont("Segoe UI", 10, QFont.Bold))
        info_form = QFormLayout(info_box)
        info_form.addRow("Tên file:", QLabel(entry.name))
        info_form.addRow("Đường dẫn:", QLabel(entry.path))
        info_form.addRow("Ngày tạo:", QLabel(parse_fat_date(entry.crt_date)))
        info_form.addRow("Giờ tạo:", QLabel(parse_fat_time(entry.crt_time)))
        info_form.addRow("Kích thước:", QLabel(f"{entry.size} bytes"))
        layout.addWidget(info_box)

        # ── Parse nội dung file theo định dạng Lab 01 ──
        queues, processes, error = self._parse_lab1_input(file_text)

        if error:
            layout.addWidget(QLabel(f"⚠ Lỗi parse: {error}"))
            return

        # ── Phần B: Bảng process ──
        proc_box = QGroupBox("Danh sách Process")
        proc_box.setFont(QFont("Segoe UI", 10, QFont.Bold))
        proc_layout = QVBoxLayout(proc_box)

        queue_map = {q.queue_id: q for q in queues}
        proc_table = QTableWidget(len(processes), 6)
        proc_table.setHorizontalHeaderLabels([
            "PID", "Arrival", "Burst", "Queue", "TimeSlice", "Algorithm"
        ])
        proc_table.setFont(QFont("Consolas", 9))
        proc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        proc_table.setAlternatingRowColors(True)
        proc_table.horizontalHeader().setStretchLastSection(True)

        for row, p in enumerate(processes):
            qcfg = queue_map.get(p.queue_id)
            items = [
                p.pid,
                str(p.arrival),
                str(p.burst),
                p.queue_id,
                str(qcfg.time_slice) if qcfg else "?",
                qcfg.policy if qcfg else "?",
            ]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                proc_table.setItem(row, col, item)

        proc_layout.addWidget(proc_table)
        layout.addWidget(proc_box)

        # ── Chạy scheduling ──
        try:
            # Clone processes (reset remaining và completion)
            fresh = [
                Process(pid=p.pid, arrival=p.arrival, burst=p.burst,
                        queue_id=p.queue_id, seq=p.seq)
                for p in processes
            ]
            segments, result_procs = run_scheduling(queues, fresh)
        except Exception as e:
            layout.addWidget(QLabel(f"⚠ Lỗi scheduling: {e}"))
            return

        # ── Phần C: Gantt chart ──
        gantt_box = QGroupBox("Sơ đồ lập lịch CPU (Gantt Chart)")
        gantt_box.setFont(QFont("Segoe UI", 10, QFont.Bold))
        gantt_layout = QVBoxLayout(gantt_box)

        gantt_widget = GanttWidget(segments)
        scroll = QScrollArea()
        scroll.setWidget(gantt_widget)
        scroll.setWidgetResizable(False)
        scroll.setFixedHeight(gantt_widget.height() + 20)
        gantt_layout.addWidget(scroll)
        layout.addWidget(gantt_box)

        # ── Phần D: Bảng metrics ──
        metrics_box = QGroupBox("Bảng thống kê (Metrics)")
        metrics_box.setFont(QFont("Segoe UI", 10, QFont.Bold))
        metrics_layout = QVBoxLayout(metrics_box)

        n_procs = len(result_procs)
        metrics_table = QTableWidget(n_procs + 1, 6)  # +1 cho dòng Average
        metrics_table.setHorizontalHeaderLabels([
            "Process", "Arrival", "Burst", "Completion", "Turnaround", "Waiting"
        ])
        metrics_table.setFont(QFont("Consolas", 9))
        metrics_table.setEditTriggers(QTableWidget.NoEditTriggers)
        metrics_table.setAlternatingRowColors(True)
        metrics_table.horizontalHeader().setStretchLastSection(True)

        sorted_procs = sorted(result_procs, key=lambda p: (p.arrival, p.seq))
        total_ta = 0
        total_wt = 0
        valid = 0

        for row, p in enumerate(sorted_procs):
            if p.completion is not None:
                comp = p.completion
                ta = comp - p.arrival
                wt = ta - p.burst
                total_ta += ta
                total_wt += wt
                valid += 1
            else:
                comp = ta = wt = -1

            items = [p.pid, str(p.arrival), str(p.burst),
                     str(comp), str(ta), str(wt)]
            for col, val in enumerate(items):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                metrics_table.setItem(row, col, item)

        # Dòng Average
        avg_row = n_procs
        if valid > 0:
            avg_ta = total_ta / valid
            avg_wt = total_wt / valid
            avg_items = ["Average", "", "", "",
                         f"{avg_ta:.2f}", f"{avg_wt:.2f}"]
        else:
            avg_items = ["Average", "", "", "", "N/A", "N/A"]

        for col, val in enumerate(avg_items):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignCenter)
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            metrics_table.setItem(avg_row, col, item)

        metrics_layout.addWidget(metrics_table)
        layout.addWidget(metrics_box)

    # ------------------------------------------------------------------
    @staticmethod
    def _parse_lab1_input(text: str):
        """
        Parse nội dung file theo đúng định dạng input Lab 01.
        Tái dùng parser.py bằng cách viết text vào file tạm (in-memory).
        
        Returns: (queues, processes, error_string_or_None)
        """
        lines = [ln.strip() for ln in text.splitlines()
                 if ln.strip() and not ln.strip().startswith("#")]

        if not lines:
            return [], [], "File rỗng hoặc không có dữ liệu hợp lệ."

        try:
            n = int(lines[0])
        except ValueError:
            return [], [], f"Dòng 1 phải là số nguyên N (nhận được: '{lines[0]}')."

        if n <= 0:
            return [], [], "N phải > 0."
        if len(lines) < 1 + n:
            return [], [], "Không đủ dòng cấu hình hàng đợi."

        queues: list[QueueConfig] = []
        for i in range(1, 1 + n):
            parts = lines[i].split()
            if len(parts) != 3:
                return [], [], f"Dòng queue {i+1}: cần 3 token (QID TimeSlice Policy)."
            qid, ts_str, policy = parts
            try:
                ts = int(ts_str)
            except ValueError:
                return [], [], f"Dòng queue {i+1}: TimeSlice không phải số."
            if policy not in ("SJF", "SRTN"):
                return [], [], f"Policy '{policy}' không hợp lệ. Dùng SJF hoặc SRTN."
            queues.append(QueueConfig(queue_id=qid, time_slice=ts, policy=policy))

        queue_ids = {q.queue_id for q in queues}
        processes: list[Process] = []
        seq = 0
        for i in range(1 + n, len(lines)):
            parts = lines[i].split()
            if len(parts) != 4:
                return [], [], f"Dòng process {i+1}: cần 4 token."
            pid, arr_str, burst_str, qid = parts
            try:
                arrival = int(arr_str)
                burst = int(burst_str)
            except ValueError:
                return [], [], f"Dòng {i+1}: arrival/burst không phải số."
            if qid not in queue_ids:
                return [], [], f"Process {pid} tham chiếu queue '{qid}' không tồn tại."
            processes.append(Process(
                pid=pid, arrival=arrival, burst=burst,
                queue_id=qid, seq=seq,
            ))
            seq += 1

        processes.sort(key=lambda p: (p.arrival, p.seq))
        return queues, processes, None
