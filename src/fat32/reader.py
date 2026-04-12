from __future__ import annotations

import struct


# Các type code FAT32 trong MBR partition table
_FAT32_TYPES = {0x0B, 0x0C}


class DiskReader:

    def __init__(self, device_path: str) -> None:
        self._path = device_path.strip()
        if not self._path.startswith("/") and not " — " in self._path:
            # Nếu chỉ nhập ID như "disk4s1", tự động thêm /dev/rdisk
            self._path = f"/dev/r{self._path}"
        elif "/dev/disk" in self._path and not "/dev/rdisk" in self._path:
            # Chuyển /dev/disk... sang /dev/rdisk... cho macOS
            self._path = self._path.replace("/dev/disk", "/dev/rdisk")
        
        self._bytes_per_sector = 512          # mặc định, cập nhật sau parse BPB
        self._partition_offset = 0            # offset (tính theo sector) tới phân vùng FAT32
        
        try:
            self._handle = open(self._path, "rb")
        except PermissionError:
            raise PermissionError(
                f"Không thể mở {self._path}.\n"
                "Hãy chạy ứng dụng với quyền sudo (Root)."
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Không tìm thấy ổ đĩa {self._path}. "
                "Kiểm tra lại đường dẫn thiết bị."
            )

        # Tự động phát hiện MBR → tìm phân vùng FAT32
        self._detect_partition()

    # ------------------------------------------------------------------
    def _detect_partition(self) -> None:
        """Đọc sector 0, nếu là MBR thì tìm phân vùng FAT32 và lưu offset."""
        self._handle.seek(0)
        sector0 = self._handle.read(512)
        if len(sector0) < 512:
            return

        sig = struct.unpack_from("<H", sector0, 510)[0]
        if sig != 0xAA55:
            return

        # Kiểm tra xem sector 0 có phải Boot Sector FAT32 hợp lệ không
        bps = struct.unpack_from("<H", sector0, 11)[0]
        if bps in (512, 1024, 2048, 4096):
            # Sector 0 đã là VBR (FAT32 boot sector) → không cần offset
            return

        # Sector 0 là MBR → duyệt 4 partition entry (offset 446..510)
        for i in range(4):
            base = 446 + i * 16
            entry = sector0[base:base + 16]
            ptype = entry[4]
            if ptype in _FAT32_TYPES:
                start_lba = struct.unpack_from("<I", entry, 8)[0]
                self._partition_offset = start_lba
                return

    # ------------------------------------------------------------------
    @property
    def partition_offset(self) -> int:
        """Offset (sector) tới phân vùng FAT32 (0 nếu không có MBR)."""
        return self._partition_offset

    @property
    def bytes_per_sector(self) -> int:
        return self._bytes_per_sector

    @bytes_per_sector.setter
    def bytes_per_sector(self, value: int) -> None:
        self._bytes_per_sector = value

    # ------------------------------------------------------------------
    def read_sector(self, lba: int) -> bytes:
        """Đọc 1 sector tại địa chỉ LBA (đã cộng partition offset)."""
        actual_lba = lba + self._partition_offset
        self._handle.seek(actual_lba * self._bytes_per_sector)
        return self._handle.read(self._bytes_per_sector)

    def read_sectors(self, lba: int, count: int) -> bytes:
        """Đọc *count* sectors liên tiếp bắt đầu từ *lba* (đã cộng partition offset)."""
        actual_lba = lba + self._partition_offset
        self._handle.seek(actual_lba * self._bytes_per_sector)
        return self._handle.read(self._bytes_per_sector * count)

    # ------------------------------------------------------------------
    def close(self) -> None:
        self._handle.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
