from __future__ import annotations

import struct
from typing import Dict, Any


# Bảng mapping: (tên trường, offset, struct format)
_BPB_FIELDS = [
    ("BytsPerSec",  11, "<H"),   
    ("SecPerClus",  13, "<B"),   
    ("RsvdSecCnt",  14, "<H"),   
    ("NumFATs",     16, "<B"),   
    ("TotSec32",    32, "<I"),   
    ("FATSz32",     36, "<I"),   
    ("RootClus",    44, "<I"),   
]


def parse_boot_sector(data: bytes) -> Dict[str, Any]:
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

    bps  = info["BytsPerSec"]
    spc  = info["SecPerClus"]
    rsvd = info["RsvdSecCnt"]
    nfat = info["NumFATs"]
    fsz  = info["FATSz32"]

    info["FATStart"]    = rsvd                      
    info["DataStart"]   = rsvd + nfat * fsz         

    return info


def validate_fat32(info: Dict[str, Any]) -> None:
    bps = info.get("BytsPerSec", 0)
    if bps not in (512, 1024, 2048, 4096):
        raise ValueError(f"BytsPerSec không hợp lệ: {bps}")
    if info.get("NumFATs", 0) not in (1, 2):
        raise ValueError(f"NumFATs không hợp lệ: {info.get('NumFATs')}")
    if info.get("RootClus", 0) < 2:
        raise ValueError(f"RootClus không hợp lệ: {info.get('RootClus')}")
