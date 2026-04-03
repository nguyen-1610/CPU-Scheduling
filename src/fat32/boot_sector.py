"""
boot_sector.py – Parse BIOS Parameter Block (BPB) từ sector 0 của ổ FAT32.

Trả về dict chứa 7+ trường cần thiết cho Lab 02.
"""

from __future__ import annotations

import struct
from typing import Dict, Any


# Bảng mapping: (tên trường, offset, struct format)
_BPB_FIELDS = [
    ("BytsPerSec",  11, "<H"),   # Bytes per sector
    ("SecPerClus",  13, "<B"),   # Sectors per cluster
    ("RsvdSecCnt",  14, "<H"),   # Reserved sectors (Boot Sector region)
    ("NumFATs",     16, "<B"),   # Number of FAT tables
    ("TotSec32",    32, "<I"),   # Total sectors on disk
    ("FATSz32",     36, "<I"),   # Sectors per FAT
    ("RootClus",    44, "<I"),   # Starting cluster of root directory
]


def parse_boot_sector(data: bytes) -> Dict[str, Any]:
    """
    Parse BPB từ 512-byte boot sector.

    Parameters
    ----------
    data : bytes
        Dữ liệu boot sector (ít nhất 512 byte).

    Returns
    -------
    dict
        Chứa các trường BPB và một số giá trị tính toán bổ sung.

    Raises
    ------
    ValueError
        Nếu thiếu magic signature 0x55AA.
    """
    if len(data) < 512:
        raise ValueError(f"Boot sector phải có ≥ 512 byte (nhận được {len(data)}).")

    # Kiểm tra magic signature
    sig = struct.unpack_from("<H", data, 510)[0]
    if sig != 0xAA55:
        raise ValueError( # Báo lỗi nếu không phải FAT32
            f"Boot sector signature không hợp lệ: 0x{sig:04X} (cần 0xAA55). "
            "Ổ đĩa có thể không phải FAT32."
        )

    # Parse từng trường BPB
    info: Dict[str, Any] = {}
    for name, offset, fmt in _BPB_FIELDS:
        info[name] = struct.unpack_from(fmt, data, offset)[0]

    # ── Giá trị tính toán ──
    bps  = info["BytsPerSec"]
    spc  = info["SecPerClus"]
    rsvd = info["RsvdSecCnt"]
    nfat = info["NumFATs"]
    fsz  = info["FATSz32"]

    info["FATStart"]    = rsvd                       # LBA đầu vùng FAT
    info["DataStart"]   = rsvd + nfat * fsz          # LBA đầu vùng Data
    info["RDETSectors"] = spc                        # Sectors cho Root Dir (tối thiểu 1 cluster)

    return info


def validate_fat32(info: Dict[str, Any]) -> None:
    """Kiểm tra nhanh các trường BPB có hợp lệ cho FAT32 hay không."""
    bps = info.get("BytsPerSec", 0)
    if bps not in (512, 1024, 2048, 4096):
        raise ValueError(f"BytsPerSec không hợp lệ: {bps}")
    if info.get("NumFATs", 0) not in (1, 2):
        raise ValueError(f"NumFATs không hợp lệ: {info.get('NumFATs')}")
    if info.get("RootClus", 0) < 2:
        raise ValueError(f"RootClus không hợp lệ: {info.get('RootClus')}")
