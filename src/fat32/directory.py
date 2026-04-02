"""
directory.py – Duyệt đệ quy cây thư mục FAT32, lọc file .txt.

Xử lý:
- Short File Name (8.3)
- Long File Name (LFN) entries
- Sub-directory đệ quy
- Bỏ qua entry deleted (0xE5) và entry trống (0x00)
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import List

from src.fat32.reader import DiskReader
from src.fat32.fat_table import FATTable


@dataclass
class FileEntry:
    """Thông tin 1 file tìm được trên ổ FAT32."""
    name: str               # Tên đầy đủ (ví dụ "input.txt")
    path: str               # Đường dẫn logic ("/subdir/input.txt")
    size: int               # Kích thước (byte)
    first_cluster: int      # Cluster đầu tiên
    crt_date: int           # Raw 2-byte ngày tạo
    crt_time: int           # Raw 2-byte giờ tạo


# ── Helpers giải mã ngày / giờ FAT ──────────────────────────────────

def parse_fat_date(raw: int) -> str:
    """Giải mã raw 2-byte FAT date → 'DD/MM/YYYY'."""
    if raw == 0:
        return "N/A"
    day   = raw & 0x1F
    month = (raw >> 5) & 0x0F
    year  = ((raw >> 9) & 0x7F) + 1980
    return f"{day:02d}/{month:02d}/{year}"


def parse_fat_time(raw: int) -> str:
    """Giải mã raw 2-byte FAT time → 'HH:MM:SS'."""
    if raw == 0:
        return "N/A"
    sec  = (raw & 0x1F) * 2
    mins = (raw >> 5) & 0x3F
    hour = (raw >> 11) & 0x1F
    return f"{hour:02d}:{mins:02d}:{sec:02d}"


# ── Parse Short File Name (8.3) ─────────────────────────────────────

def _parse_short_name(entry: bytes) -> str:
    """Trích tên 8.3 từ 32-byte directory entry."""
    name_part = entry[0:8].decode("ascii", errors="replace").rstrip()
    ext_part  = entry[8:11].decode("ascii", errors="replace").rstrip()
    if ext_part:
        return f"{name_part}.{ext_part}"
    return name_part


# ── Parse LFN entry ─────────────────────────────────────────────────

def _parse_lfn_chars(entry: bytes) -> str:
    """Trích ký tự Unicode từ 1 LFN entry (32 byte)."""
    # LFN chars nằm ở 3 vùng trong entry
    chars = []
    # Vùng 1: offset 1–10  (5 UCS-2 chars)
    for i in range(1, 11, 2):
        chars.append(struct.unpack_from("<H", entry, i)[0])
    # Vùng 2: offset 14–25 (6 UCS-2 chars)
    for i in range(14, 26, 2):
        chars.append(struct.unpack_from("<H", entry, i)[0])
    # Vùng 3: offset 28–31 (2 UCS-2 chars)
    for i in range(28, 32, 2):
        chars.append(struct.unpack_from("<H", entry, i)[0])

    # Cắt tại NULL (0x0000) hoặc padding (0xFFFF)
    result = []
    for c in chars:
        if c == 0x0000 or c == 0xFFFF:
            break
        result.append(chr(c))
    return "".join(result)


# ── Duyệt thư mục ───────────────────────────────────────────────────

def list_txt_files(
    reader: DiskReader,
    fat: FATTable,
    root_cluster: int,
    data_start_lba: int,
    sec_per_clus: int,
) -> List[FileEntry]:
    """
    Duyệt đệ quy toàn bộ cây thư mục FAT32 từ *root_cluster*,
    trả về danh sách tất cả file ``.txt`` (không phân biệt hoa thường).
    """
    results: List[FileEntry] = []
    _walk_directory(reader, fat, root_cluster, data_start_lba,
                    sec_per_clus, "/", results)
    return results


def _walk_directory(
    reader: DiskReader,
    fat: FATTable,
    dir_cluster: int,
    data_start_lba: int,
    sec_per_clus: int,
    current_path: str,
    results: List[FileEntry],
) -> None:
    """Duyệt 1 directory (cluster chain), đệ quy vào sub-dir."""
    raw = fat.read_chain_data(dir_cluster, reader, data_start_lba, sec_per_clus)

    lfn_parts: list[tuple[int, str]] = []     # (order, chars)
    num_entries = len(raw) // 32

    for i in range(num_entries):
        entry = raw[i * 32 : (i + 1) * 32]

        first_byte = entry[0]
        # 0x00 = không còn entry tiếp → dừng
        if first_byte == 0x00:
            break
        # 0xE5 = entry đã xoá → bỏ qua
        if first_byte == 0xE5:
            lfn_parts.clear()
            continue

        attr = entry[11]

        # ── LFN entry (attr == 0x0F) ──
        if attr == 0x0F:
            order = first_byte & 0x3F       # số thứ tự LFN (1-based, ngược)
            lfn_parts.append((order, _parse_lfn_chars(entry)))
            continue

        # ── Short entry: file hoặc thư mục ──

        # Bỏ qua Volume Label (attr bit 3)
        if attr & 0x08:
            lfn_parts.clear()
            continue

        # Ghép LFN (nếu có)
        if lfn_parts:
            lfn_parts.sort(key=lambda x: x[0])
            long_name = "".join(chars for _, chars in lfn_parts)
            lfn_parts.clear()
        else:
            long_name = ""

        short_name = _parse_short_name(entry)
        display_name = long_name if long_name else short_name

        # First cluster = (HIGH << 16) | LOW
        cluster_hi = struct.unpack_from("<H", entry, 20)[0]
        cluster_lo = struct.unpack_from("<H", entry, 26)[0]
        first_cluster = (cluster_hi << 16) | cluster_lo

        # ── Thư mục (attr bit 4 = 0x10) ──
        if attr & 0x10:
            # Bỏ qua "." và ".."
            if short_name in (".", "..", ".          ", "..         "):
                continue
            if display_name in (".", ".."):
                continue
            # Đệ quy vào sub-directory
            sub_path = current_path + display_name + "/"
            if first_cluster >= 2:
                _walk_directory(reader, fat, first_cluster,
                                data_start_lba, sec_per_clus,
                                sub_path, results)
            continue

        # ── File thông thường (attr bit 5 = 0x20 hoặc attr == 0) ──
        file_size = struct.unpack_from("<I", entry, 28)[0]
        crt_time  = struct.unpack_from("<H", entry, 14)[0]
        crt_date  = struct.unpack_from("<H", entry, 16)[0]

        # Lọc chỉ lấy .txt (không phân biệt hoa thường)
        if display_name.upper().endswith(".TXT"):
            file_path = current_path + display_name
            results.append(FileEntry(
                name=display_name,
                path=file_path,
                size=file_size,
                first_cluster=first_cluster,
                crt_date=crt_date,
                crt_time=crt_time,
            ))
