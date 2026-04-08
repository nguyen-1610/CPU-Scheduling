"""
macos_utils.py – Các hàm hỗ trợ tìm kiếm và xử lý ổ đĩa trên macOS.
"""

import subprocess
import plistlib
from typing import List, Tuple


def detect_fat32_devices() -> List[Tuple[str, str, str]]:
    """
    Sử dụng diskutil để tìm kiếm các phân vùng FAT32 trên ổ đĩa ngoài.
    Trả về: List của (device_path, volume_name, identifier)
    Ví dụ: [("/dev/disk12", "USB_DATA", "disk12s1"), ...]
    """
    found_devices = []
    try:
        # Thử dùng plist để parse chính xác
        result = subprocess.run(
            ["diskutil", "list", "-plist", "external", "physical"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            plist = plistlib.loads(result.stdout.encode())
            disks = plist.get("AllDisksAndPartitions", [])
            for disk in disks:
                disk_id = disk.get("DeviceIdentifier", "")
                partitions = disk.get("Partitions", [])
                for part in partitions:
                    content = part.get("Content", "")
                    if "FAT" in content.upper():
                        part_id = part.get("DeviceIdentifier", "")
                        name = part.get("VolumeName", "") or "Untitled"
                        size = part.get("Size", 0)
                        size_gb = size / (1024 ** 3) if size else 0
                        label = f"/dev/r{disk_id} — {name} ({size_gb:.1f} GB) [{part_id}]"
                        found_devices.append((f"/dev/r{disk_id}", label))
            if found_devices:
                return found_devices

        # Fallback: Parse text nếu plist thất bại
        return _detect_usb_text_fallback()
    except Exception:
        return _detect_usb_text_fallback()


def _detect_usb_text_fallback() -> List[Tuple[str, str]]:
    """Fallback parse text output của diskutil list."""
    devices = []
    try:
        result = subprocess.run(
            ["diskutil", "list", "external"],
            capture_output=True, text=True, timeout=5,
        )
        lines = result.stdout.splitlines()
        current_disk = ""
        for line in lines:
            if line.startswith("/dev/"):
                current_disk = line.split()[0]
            elif "DOS_FAT_32" in line or "Microsoft Basic Data" in line:
                parts = line.split()
                identifier = parts[-1] if parts else ""
                name = " ".join(parts[i+1:-2]) if "DOS_FAT_32" in line else "Unknown"
                label = f"/dev/r{identifier} — {name} [{identifier}]"
                devices.append((f"/dev/r{identifier}", label))
    except Exception:
        pass
    return devices


def unmount_disk_mac(disk_path: str) -> bool:
    """Unmount toàn bộ ổ đĩa để có thể truy cập raw device."""
    try:
        disk_id = disk_path.replace("/dev/", "")
        result = subprocess.run(
            ["diskutil", "unmountDisk", disk_id],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False
