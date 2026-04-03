"""
boot_tab.py – Tab hiển thị thông tin Boot Sector (BPB) dưới dạng bảng.
"""

from __future__ import annotations

from typing import Dict, Any

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


# Thứ tự hiển thị và nhãn tiếng Việt
_DISPLAY_FIELDS = [
    ("BytsPerSec",  "Bytes per Sector"),
    ("SecPerClus",  "Sectors per Cluster"),
    ("RsvdSecCnt",  "Số sector vùng Boot Sector (Reserved)"),
    ("NumFATs",     "Số bảng FAT"),
    ("FATSz32",     "Số sector mỗi bảng FAT"),
    ("RDETSectors", "Số sector cho RDET"),
    ("TotSec32",    "Tổng số sector trên ổ"),
]


class BootTab(QWidget):
    """Tab 1: Hiển thị 7 trường BPB trong QTableWidget."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Thông tin Boot Sector (BPB)")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(title)

        self._table = QTableWidget(len(_DISPLAY_FIELDS), 2)
        self._table.setHorizontalHeaderLabels(["Trường", "Giá trị"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setColumnWidth(0, 310)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setFont(QFont("Consolas", 10))
        layout.addWidget(self._table)

        # Placeholder rows
        for row, (key, label) in enumerate(_DISPLAY_FIELDS):
            self._table.setItem(row, 0, QTableWidgetItem(label))
            self._table.setItem(row, 1, QTableWidgetItem("—"))

    def display(self, info: Dict[str, Any]) -> None:
        """Cập nhật bảng với dữ liệu từ parse_boot_sector()."""
        for row, (key, label) in enumerate(_DISPLAY_FIELDS):
            value = info.get(key, "N/A")
            self._table.setItem(row, 0, QTableWidgetItem(label))
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(row, 1, item)
