"""
main_window.py – Cửa sổ chính của ứng dụng Lab 02.

Bố cục:
    ┌──────────────────────────────────────┐
    │  [Drive: ___E___]  [Connect]         │
    ├──────────────────────────────────────┤
    │  Tab "Boot Sector"  │  Tab "TXT Files" │
    │                     │                │
    └──────────────────────────────────────┘
"""

from __future__ import annotations

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget,
    QMessageBox, QStatusBar,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from src.fat32.reader import DiskReader
from src.fat32.boot_sector import parse_boot_sector, validate_fat32
from src.fat32.fat_table import FATTable
from src.fat32.directory import list_txt_files, FileEntry

from src.gui.boot_tab import BootTab
from src.gui.files_tab import FilesTab

from typing import Optional, List, Dict, Any


class MainWindow(QMainWindow):
    """Cửa sổ chính – quản lý kết nối FAT32 và chứa các tab."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lab 02 – FAT32 Reader & CPU Scheduling")
        self.setMinimumSize(900, 620)
        self.resize(1000, 700)

        # ── State ──
        self._reader: Optional[DiskReader] = None
        self._boot_info: Dict[str, Any] = {}
        self._fat: Optional[FATTable] = None
        self._txt_files: List[FileEntry] = []

        # ── UI ──
        self._build_ui()
        self.statusBar().showMessage("Nhập ký tự ổ đĩa FAT32 rồi nhấn Connect.")

    # ==================================================================
    #  Build UI
    # ==================================================================
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Drive bar ──
        drive_bar = QHBoxLayout()
        lbl = QLabel("Drive letter:")
        lbl.setFont(QFont("Segoe UI", 10))
        self._drive_input = QLineEdit()
        self._drive_input.setPlaceholderText("E")
        self._drive_input.setMaximumWidth(60)
        self._drive_input.setFont(QFont("Segoe UI", 10))
        self._drive_input.returnPressed.connect(self._on_connect)

        self._btn_connect = QPushButton("Connect")
        self._btn_connect.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._btn_connect.setMinimumWidth(100)
        self._btn_connect.clicked.connect(self._on_connect)

        drive_bar.addWidget(lbl)
        drive_bar.addWidget(self._drive_input)
        drive_bar.addWidget(self._btn_connect)
        drive_bar.addStretch()
        layout.addLayout(drive_bar)

        # ── Tab widget ──
        self._tabs = QTabWidget()
        self._boot_tab = BootTab()
        self._files_tab = FilesTab(self)

        self._tabs.addTab(self._boot_tab, "Boot Sector")
        self._tabs.addTab(self._files_tab, "TXT Files")

        layout.addWidget(self._tabs)

    # ==================================================================
    #  Connect handler
    # ==================================================================
    def _on_connect(self) -> None:
        drive = self._drive_input.text().strip()
        if not drive:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập ký tự ổ đĩa (ví dụ: E).")
            return

        # Đóng kết nối cũ (nếu có)
        if self._reader is not None:
            try:
                self._reader.close()
            except Exception:
                pass

        try:
            self.statusBar().showMessage(f"Đang kết nối ổ {drive}:...")
            self._reader = DiskReader(drive)

            # 1) Đọc + parse Boot Sector
            raw_boot = self._reader.read_sector(0)
            self._boot_info = parse_boot_sector(raw_boot)
            validate_fat32(self._boot_info)

            # Cập nhật bytes_per_sector cho reader
            self._reader.bytes_per_sector = self._boot_info["BytsPerSec"]

            # 2) Đọc FAT
            self._fat = FATTable(
                self._reader,
                fat_start_lba=self._boot_info["FATStart"],
                fat_size_sectors=self._boot_info["FATSz32"],
                bytes_per_sector=self._boot_info["BytsPerSec"],
            )

            # 3) Duyệt thư mục → lọc .txt
            self._txt_files = list_txt_files(
                self._reader,
                self._fat,
                root_cluster=self._boot_info["RootClus"],
                data_start_lba=self._boot_info["DataStart"],
                sec_per_clus=self._boot_info["SecPerClus"],
            )

            # 4) Cập nhật tabs
            self._boot_tab.display(self._boot_info)
            self._files_tab.display(self._txt_files)

            self.statusBar().showMessage(
                f"Kết nối {drive}: thành công  ·  "
                f"Tìm thấy {len(self._txt_files)} file .txt"
            )

        except PermissionError as e:
            QMessageBox.critical(self, "Cần quyền Admin", str(e))
            self.statusBar().showMessage("Lỗi: không có quyền Admin.")
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Không tìm thấy ổ đĩa", str(e))
            self.statusBar().showMessage("Lỗi: ổ đĩa không tồn tại.")
        except ValueError as e:
            QMessageBox.critical(self, "Lỗi FAT32", str(e))
            self.statusBar().showMessage("Lỗi: định dạng FAT32 không hợp lệ.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi không xác định", str(e))
            self.statusBar().showMessage(f"Lỗi: {e}")

    # ==================================================================
    #  Public API cho các tab
    # ==================================================================
    @property
    def reader(self) -> Optional[DiskReader]:
        return self._reader

    @property
    def fat(self) -> Optional[FATTable]:
        return self._fat

    @property
    def boot_info(self) -> Dict[str, Any]:
        return self._boot_info

    # ==================================================================
    def closeEvent(self, event) -> None:
        if self._reader is not None:
            try:
                self._reader.close()
            except Exception:
                pass
        event.accept()
