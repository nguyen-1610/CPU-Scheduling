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
import subprocess

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget,
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

_IS_MAC = sys.platform == "darwin"


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
        if _IS_MAC:
            self.statusBar().showMessage("Nhấn Detect USB để tìm ổ FAT32, hoặc nhập path thủ công.")
        else:
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

        if _IS_MAC:
            # macOS: Dropdown chọn USB + nút Detect
            lbl = QLabel("Ổ USB FAT32:")
            lbl.setFont(QFont("Segoe UI", 10))

            self._device_combo = QComboBox()
            self._device_combo.setMinimumWidth(300)
            self._device_combo.setFont(QFont("Segoe UI", 10))
            self._device_combo.setEditable(True)
            self._device_combo.setPlaceholderText("Nhấn Detect USB hoặc nhập path...")

            self._btn_detect = QPushButton("🔍 Detect USB")
            self._btn_detect.setFont(QFont("Segoe UI", 10))
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
            lbl.setFont(QFont("Segoe UI", 10))
            self._drive_input = QLineEdit()
            self._drive_input.setPlaceholderText("E")
            self._drive_input.setMaximumWidth(60)
            self._drive_input.setFont(QFont("Segoe UI", 10))
            self._drive_input.returnPressed.connect(self._on_connect)

            drive_bar.addWidget(lbl)
            drive_bar.addWidget(self._drive_input)

        self._btn_connect = QPushButton("Connect")
        self._btn_connect.setFont(QFont("Segoe UI", 10, QFont.Bold))
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
        """Dùng diskutil list để tìm tất cả phân vùng FAT32 external."""
        self._device_combo.clear()
        try:
            result = subprocess.run(
                ["diskutil", "list", "-plist", "external", "physical"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                # Fallback: parse text output
                self._detect_usb_text()
                return

            import plistlib
            plist = plistlib.loads(result.stdout.encode())
            disks = plist.get("AllDisksAndPartitions", [])

            found = 0
            for disk in disks:
                disk_id = disk.get("DeviceIdentifier", "")
                partitions = disk.get("Partitions", [])
                for part in partitions:
                    content = part.get("Content", "")
                    if "FAT" in content.upper():
                        part_id = part.get("DeviceIdentifier", "")
                        name = part.get("VolumeName", "") or part.get("MountPoint", "")
                        size = part.get("Size", 0)
                        size_gb = size / (1024 ** 3) if size else 0
                        label = f"/dev/{disk_id} — {name} ({size_gb:.1f} GB) [{part_id}]"
                        self._device_combo.addItem(label, f"/dev/{disk_id}")
                        found += 1

            if found == 0:
                self.statusBar().showMessage("Không tìm thấy ổ USB FAT32 nào. Hãy cắm USB rồi thử lại.")
            else:
                self.statusBar().showMessage(f"Tìm thấy {found} ổ USB FAT32. Chọn ổ rồi nhấn Connect.")

        except Exception as e:
            self._detect_usb_text()

    def _detect_usb_text(self) -> None:
        """Fallback: parse text output của diskutil list."""
        try:
            result = subprocess.run(
                ["diskutil", "list", "external"],
                capture_output=True, text=True, timeout=5,
            )
            lines = result.stdout.splitlines()
            current_disk = ""
            found = 0

            for line in lines:
                if line.startswith("/dev/"):
                    # e.g. "/dev/disk12 (external, physical):"
                    current_disk = line.split()[0]
                elif "DOS_FAT_32" in line or "Microsoft Basic Data" in line:
                    parts = line.split()
                    # Tìm tên volume và identifier
                    identifier = parts[-1] if parts else ""
                    # Tìm tên volume (nằm giữa TYPE và SIZE)
                    name = ""
                    for i, p in enumerate(parts):
                        if p in ("DOS_FAT_32", "Microsoft"):
                            name = " ".join(parts[i+1:-2])  # name nằm giữa type và size
                            break
                    label = f"{current_disk} — {name} [{identifier}]"
                    self._device_combo.addItem(label, current_disk)
                    found += 1

            if found == 0:
                self.statusBar().showMessage("Không tìm thấy ổ USB FAT32 nào.")
            else:
                self.statusBar().showMessage(f"Tìm thấy {found} ổ USB FAT32.")

        except Exception:
            self.statusBar().showMessage("Lỗi khi detect USB. Hãy nhập path thủ công.")

    # ==================================================================
    #  macOS: Unmount trước khi đọc raw device
    # ==================================================================
    @staticmethod
    def _unmount_disk_mac(disk_path: str) -> bool:
        """Unmount toàn bộ ổ đĩa để có thể truy cập raw device."""
        try:
            # Lấy disk identifier (vd: /dev/disk12 → disk12)
            disk_id = disk_path.replace("/dev/", "")
            result = subprocess.run(
                ["diskutil", "unmountDisk", disk_id],
                capture_output=True, text=True, timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    # ==================================================================
    #  Connect handler
    # ==================================================================
    def _on_connect(self) -> None:
        if _IS_MAC:
            # Lấy device path từ combo box (userData) hoặc text nhập tay
            idx = self._device_combo.currentIndex()
            if idx >= 0 and self._device_combo.itemData(idx):
                drive = self._device_combo.itemData(idx)
            else:
                drive = self._device_combo.currentText().strip()
        else:
            drive = self._drive_input.text().strip()

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
            if _IS_MAC and drive.startswith("/dev/"):
                self.statusBar().showMessage(f"Đang unmount {drive}...")
                if not self._unmount_disk_mac(drive):
                    QMessageBox.warning(
                        self, "Unmount thất bại",
                        f"Không thể unmount {drive}.\n"
                        "Hãy thử đóng các ứng dụng đang dùng USB rồi thử lại,\n"
                        "hoặc chạy trong terminal:\n"
                        f"  sudo diskutil unmountDisk force {drive}"
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
            if _IS_MAC:
                QMessageBox.critical(
                    self, "Lỗi quyền truy cập",
                    f"{e}\n\nHãy cấp quyền trong terminal:\n"
                    f"  sudo chmod 666 {drive}"
                )
            else:
                QMessageBox.critical(self, "Cần quyền Admin", str(e))
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
