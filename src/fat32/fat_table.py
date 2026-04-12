from __future__ import annotations

import struct
from typing import List, Optional

from src.fat32.reader import DiskReader


class FATTable:
    """Đọc + cache toàn bộ FAT, cung cấp hàm tra cluster chain."""

    EOC = 0x0FFFFFF8      # End Of Cluster chain (≥ giá trị này)
    BAD = 0x0FFFFFF7      # Bad cluster marker

    def __init__(
        self,
        reader: DiskReader,
        fat_start_lba: int,
        fat_size_sectors: int,
        bytes_per_sector: int,
    ) -> None:
        raw = reader.read_sectors(fat_start_lba, fat_size_sectors)

        # Mỗi entry FAT32 = 4 byte, mask 28 bit thấp
        count = len(raw) // 4
        self._entries: List[int] = [
            struct.unpack_from("<I", raw, i * 4)[0] & 0x0FFFFFFF
            for i in range(count)
        ]

    # ------------------------------------------------------------------
    def next_cluster(self, cluster: int) -> Optional[int]:
        if cluster < 2 or cluster >= len(self._entries):
            return None
        val = self._entries[cluster]
        if val >= self.EOC or val == self.BAD:
            return None
        return val

    def get_chain(self, start_cluster: int) -> List[int]:
        """Trả về danh sách tất cả cluster trong chain (bao gồm start)."""
        chain: List[int] = []
        cur: Optional[int] = start_cluster
        visited: set[int] = set()          # phòng vòng lặp FAT lỗi
        while cur is not None and cur not in visited:
            chain.append(cur)
            visited.add(cur)
            cur = self.next_cluster(cur)
        return chain

    def read_chain_data(
        self,
        start_cluster: int,
        reader: DiskReader,
        data_start_lba: int,
        sec_per_clus: int,
    ) -> bytes:
        
        chain = self.get_chain(start_cluster)
        bps = reader.bytes_per_sector
        parts: List[bytes] = []
        for cluster in chain:
            lba = data_start_lba + (cluster - 2) * sec_per_clus
            parts.append(reader.read_sectors(lba, sec_per_clus))
        return b"".join(parts)
