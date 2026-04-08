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

import sys

from src.fat32.macos_utils import detect_fat32_devices, unmount_disk_mac

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget,
    QMessageBox, QStatusBar, QComboBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

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
        self.statusBar().showMessage("Nhấn Detect USB để tìm ổ FAT32, hoặc nhập path thủ công.")

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

        if True:
            # macOS: Dropdown chọn USB + nút Detect
            lbl = QLabel("Ổ USB FAT32:")
            lbl.setFont(QFont()) # Default font

            self._device_combo = QComboBox()
            self._device_combo.setMinimumWidth(300)
            self._device_combo.setEditable(True)
            self._device_combo.setPlaceholderText("Nhấn Detect USB hoặc nhập path...")

            self._btn_detect = QPushButton("🔍 Detect USB")
            self._btn_detect.setMinimumWidth(120)
            self._btn_detect.clicked.connect(self._on_detect_usb)

            drive_bar.addWidget(lbl)
            drive_bar.addWidget(self._device_combo)
            drive_bar.addWidget(self._btn_detect)

            # Tự động detect khi mở app
            self._on_detect_usb()
        else:
            # Windows: Nhập ký tự ổ đĩa
            lbl = QLabel("Drive letter:")
            self._drive_input = QLineEdit()
            self._drive_input.setPlaceholderText("E")
            self._drive_input.setMaximumWidth(60)
            self._drive_input.returnPressed.connect(self._on_connect)

            drive_bar.addWidget(lbl)
            drive_bar.addWidget(self._drive_input)

        self._btn_connect = QPushButton("Connect")
        f = self._btn_connect.font()
        f.setBold(True)
        self._btn_connect.setFont(f)
        self._btn_connect.setMinimumWidth(100)
        self._btn_connect.clicked.connect(self._on_connect)

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
    #  macOS: Auto-detect FAT32 USB devices
    # ==================================================================
    def _on_detect_usb(self) -> None:
        """Sử dụng macos_utils để tìm các ổ FAT32."""
        self._device_combo.clear()
        devices = detect_fat32_devices()
        
        for drive_path, label in devices:
            self._device_combo.addItem(label, drive_path)

        if not devices:
            self.statusBar().showMessage("Không tìm thấy ổ USB FAT32 nào. Hãy cắm USB rồi thử lại.")
        else:
            self.statusBar().showMessage(f"Tìm thấy {len(devices)} ổ USB FAT32. Chọn ổ rồi nhấn Connect.")


    # ==================================================================
    #  Connect handler
    # ==================================================================
    def _on_connect(self) -> None:
        # Lấy device path từ combo box (userData) hoặc text nhập tay
        idx = self._device_combo.currentIndex()
        if idx >= 0 and self._device_combo.itemData(idx):
            drive = self._device_combo.itemData(idx)
        else:
            drive = self._device_combo.currentText().strip()

        if not drive:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn hoặc nhập ổ đĩa.")
            return

        # Đóng kết nối cũ (nếu có)
        if self._reader is not None:
            try:
                self._reader.close()
            except Exception:
                pass

        try:
            # macOS: Tự động unmount trước khi đọc raw device
            if drive.startswith("/dev/"):
                self.statusBar().showMessage(f"Đang unmount {drive}...")
                if not unmount_disk_mac(drive):
                    QMessageBox.warning(
                        self, "Unmount thất bại",
                        f"Không thể unmount {drive}.\n"
                        "Hãy thử đóng các ứng dụng đang dùng USB rồi thử lại."
                    )
                    return

            self.statusBar().showMessage(f"Đang kết nối {drive}...")
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

            # 3.5) Tính toán số sector thực tế của RDET
            # FAT32: Root Dir là 1 cluster chain, ta đếm số cluster rồi nhân spc
            root_chain = self._fat.get_chain(self._boot_info["RootClus"])
            self._boot_info["RDETSectors"] = len(root_chain) * self._boot_info["SecPerClus"]

            # 4) Cập nhật tabs
            self._boot_tab.display(self._boot_info)
            self._files_tab.display(self._txt_files)

            offset_msg = ""
            if self._reader.partition_offset > 0:
                offset_msg = f"  ·  MBR offset: {self._reader.partition_offset}"

            self.statusBar().showMessage(
                f"Kết nối {drive} thành công  ·  "
                f"Tìm thấy {len(self._txt_files)} file .txt"
                f"{offset_msg}"
            )

        except PermissionError as e:
            QMessageBox.critical(
                self, "Lỗi quyền truy cập",
                f"{e}\n\nHãy cấp quyền trong terminal:\n"
                f"  sudo chmod 666 {drive}"
            )
            self.statusBar().showMessage("Lỗi: không có quyền truy cập.")
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
