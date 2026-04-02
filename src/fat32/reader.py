r"""
reader.py – Mở raw device FAT32 (Windows) và đọc sector theo LBA.

Cách dùng:
    reader = DiskReader("E")        # Mở \\.\E:
    data   = reader.read_sector(0)  # Đọc sector 0 (Boot Sector)
    reader.close()

Lưu ý: cần quyền Administrator trên Windows.
"""

from __future__ import annotations


class DiskReader:
    """Đọc sector-level từ một ổ đĩa FAT32 qua đường dẫn raw device."""

    def __init__(self, drive_letter: str) -> None:
        """
        Parameters
        ----------
        drive_letter : str
            Ký tự ổ đĩa (ví dụ ``"E"``).  Sẽ mở ``\\\\.\\E:``.
        """
        drive_letter = drive_letter.strip().rstrip(":\\")
        self._path = rf"\\.\{drive_letter}:"
        self._bytes_per_sector = 512          # mặc định, cập nhật sau parse BPB
        try:
            self._handle = open(self._path, "rb")
        except PermissionError:
            raise PermissionError(
                f"Không thể mở {self._path}. "
                "Hãy chạy ứng dụng với quyền Administrator."
            )
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Không tìm thấy ổ đĩa {self._path}. "
                "Kiểm tra lại ký tự ổ đĩa."
            )

    # ------------------------------------------------------------------
    @property
    def bytes_per_sector(self) -> int:
        return self._bytes_per_sector

    @bytes_per_sector.setter
    def bytes_per_sector(self, value: int) -> None:
        self._bytes_per_sector = value

    # ------------------------------------------------------------------
    def read_sector(self, lba: int) -> bytes:
        """Đọc 1 sector tại địa chỉ LBA."""
        self._handle.seek(lba * self._bytes_per_sector)
        return self._handle.read(self._bytes_per_sector)

    def read_sectors(self, lba: int, count: int) -> bytes:
        """Đọc *count* sectors liên tiếp bắt đầu từ *lba*."""
        self._handle.seek(lba * self._bytes_per_sector)
        return self._handle.read(self._bytes_per_sector * count)

    # ------------------------------------------------------------------
    def close(self) -> None:
        self._handle.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
