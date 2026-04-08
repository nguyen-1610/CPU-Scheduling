"""
files_tab.py – Tab liệt kê tất cả file .txt tìm thấy trên ổ FAT32.

Hiển thị flat list, cho phép chọn file → nhấn "View Details" để mở dialog.
"""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.fat32.directory import FileEntry

if TYPE_CHECKING:
    from src.gui.main_window import MainWindow


class FilesTab(QWidget):
    """Tab 2: Danh sách file .txt + nút View Details."""

    def __init__(self, main_window: MainWindow, parent=None) -> None:
        super().__init__(parent)
        self._main = main_window
        self._entries: List[FileEntry] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Danh sách file .txt trên ổ FAT32")
        f = title.font()
        f.setPointSize(12)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        self._list = QListWidget()
        # Để hệ thống tự chọn font mono tốt nhất
        layout.addWidget(self._list)

        # ── Buttons ──
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        self._btn_view = QPushButton("View Details")
        f2 = self._btn_view.font()
        f2.setBold(True)
        self._btn_view.setFont(f2)
        self._btn_view.setMinimumWidth(120)
        self._btn_view.clicked.connect(self._on_view_details)
        btn_bar.addWidget(self._btn_view)

        self._btn_refresh = QPushButton("Refresh")
        self._btn_refresh.clicked.connect(self._on_refresh)
        btn_bar.addWidget(self._btn_refresh)

        layout.addLayout(btn_bar)

    # ------------------------------------------------------------------
    def display(self, entries: List[FileEntry]) -> None:
        """Cập nhật danh sách từ kết quả duyệt thư mục."""
        self._entries = entries
        self._list.clear()
        for fe in entries:
            item = QListWidgetItem(f"{fe.path}   ({fe.size} bytes)")
            item.setData(Qt.UserRole, fe)
            self._list.addItem(item)

    # ------------------------------------------------------------------
    def _on_view_details(self) -> None:
        current = self._list.currentItem()
        if current is None:
            QMessageBox.information(self, "Thông báo", "Chọn 1 file .txt trước.")
            return

        fe: FileEntry = current.data(Qt.UserRole)
        reader = self._main.reader
        fat    = self._main.fat
        info   = self._main.boot_info

        if reader is None or fat is None:
            QMessageBox.warning(self, "Lỗi", "Chưa kết nối ổ đĩa.")
            return

        # Đọc nội dung file từ cluster chain
        try:
            raw_content = fat.read_chain_data(
                fe.first_cluster,
                reader,
                data_start_lba=info["DataStart"],
                sec_per_clus=info["SecPerClus"],
            )
            # Cắt theo file size thật (loại bỏ padding cluster)
            raw_content = raw_content[:fe.size]
        except Exception as e:
            QMessageBox.critical(self, "Lỗi đọc file", str(e))
            return

        # Mở DetailDialog
        from src.gui.detail_dialog import DetailDialog
        dlg = DetailDialog(fe, raw_content, parent=self)
        dlg.exec()

    # ------------------------------------------------------------------
    def _on_refresh(self) -> None:
        reader = self._main.reader
        fat    = self._main.fat
        info   = self._main.boot_info

        if reader is None or fat is None:
            QMessageBox.warning(self, "Lỗi", "Chưa kết nối ổ đĩa.")
            return

        from src.fat32.directory import list_txt_files
        try:
            entries = list_txt_files(
                reader, fat,
                root_cluster=info["RootClus"],
                data_start_lba=info["DataStart"],
                sec_per_clus=info["SecPerClus"],
            )
            self.display(entries)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi quét thư mục", str(e))
