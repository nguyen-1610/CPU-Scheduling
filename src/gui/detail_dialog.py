"""
detail_dialog.py - Dialog chi tiet: info file + bang process + Gantt chart + metrics.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.controller.scheduler import run_scheduling
from src.fat32.directory import FileEntry, parse_fat_date, parse_fat_time
from src.io.layoutOutput import buildReport
from src.io.parser import parse_input_bytes
from src.model.entities import Process


class DetailDialog(QDialog):
    def __init__(self, entry: FileEntry, raw_content: bytes, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Chi tiet - {entry.name}")
        self.setMinimumSize(860, 600)
        self.resize(980, 760)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        info_box = QGroupBox("Thong tin file")
        info_box.setFont(QFont("Segoe UI", 10, QFont.Bold))
        info_form = QFormLayout(info_box)
        info_form.addRow("Ten file:", QLabel(entry.name))
        info_form.addRow("Duong dan:", QLabel(entry.path))
        info_form.addRow("Ngay tao:", QLabel(parse_fat_date(entry.crt_date)))
        info_form.addRow("Gio tao:", QLabel(parse_fat_time(entry.crt_time)))
        info_form.addRow("Kich thuoc:", QLabel(f"{entry.size} bytes"))
        layout.addWidget(info_box)

        queues, processes, error = self._parse_lab1_input(raw_content)
        if error:
            layout.addWidget(QLabel(f"Loi parse: {error}"))
            return

        proc_box = QGroupBox("Danh sach Process")
        proc_box.setFont(QFont("Segoe UI", 10, QFont.Bold))
        proc_layout = QVBoxLayout(proc_box)

        queue_map = {q.queue_id: q for q in queues}
        proc_table = QTableWidget(len(processes), 6)
        proc_table.setHorizontalHeaderLabels([
            "PID",
            "Arrival",
            "Burst",
            "Queue",
            "TimeSlice",
            "Algorithm",
        ])
        proc_table.setFont(QFont("Consolas", 9))
        proc_table.setEditTriggers(QTableWidget.NoEditTriggers)
        proc_table.setAlternatingRowColors(True)
        proc_table.horizontalHeader().setStretchLastSection(True)

        for row, p in enumerate(processes):
            qcfg = queue_map.get(p.queue_id)
            values = [
                p.pid,
                str(p.arrival),
                str(p.burst),
                p.queue_id,
                str(qcfg.time_slice) if qcfg else "?",
                qcfg.policy if qcfg else "?",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                proc_table.setItem(row, col, item)

        proc_layout.addWidget(proc_table)
        layout.addWidget(proc_box)

        try:
            fresh = [
                Process(
                    pid=p.pid,
                    arrival=p.arrival,
                    burst=p.burst,
                    queue_id=p.queue_id,
                    seq=p.seq,
                )
                for p in processes
            ]
            segments, result_procs = run_scheduling(queues, fresh)
        except Exception as exc:
            layout.addWidget(QLabel(f"Loi scheduling: {exc}"))
            return

        report_box = QGroupBox("Scheduling Output")
        report_box.setFont(QFont("Segoe UI", 10, QFont.Bold))
        report_layout = QVBoxLayout(report_box)

        report_view = QPlainTextEdit()
        report_view.setReadOnly(True)
        report_view.setFont(QFont("Consolas", 9))
        report_view.setPlainText(buildReport(segments, result_procs).rstrip())
        report_view.setMinimumHeight(360)
        report_layout.addWidget(report_view)
        layout.addWidget(report_box)

    @staticmethod
    def _parse_lab1_input(raw_content: bytes):
        try:
            queues, processes = parse_input_bytes(raw_content)
            return queues, processes, None
        except ValueError as exc:
            return [], [], str(exc)
