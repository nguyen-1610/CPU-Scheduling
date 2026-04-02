# Lab 02 – Hướng Dẫn & Giải Thích

> **Mục đích:** Đọc file `.txt` từ USB FAT32 bằng cách đọc raw device,
> rồi chạy engine lập lịch CPU từ Lab 01 và hiển thị kết quả trên GUI.

---

## Cách Chạy

```bash
# 1. Kích hoạt venv
.venv\Scripts\activate

# 2. Chạy GUI (cần quyền Administrator)
python -m src.main_gui

# 3. Trong app: nhập ký tự ổ USB (ví dụ: E) → nhấn Connect
```

> ⚠️ **Bắt buộc chạy terminal với quyền Administrator**
> (chuột phải → Run as Administrator)

---

## Cấu Trúc Thư Mục

```
src/
├── algorithms/          Lab 1 – Thuật toán (SJF, SRTN, RoundRobin)
├── controller/          Lab 1 – Engine lập lịch (scheduler.py)
├── io/                  Lab 1 – Đọc/ghi file text
├── model/               Lab 1 – Data classes (Process, Segment, QueueConfig)
│
├── fat32/               Lab 2 – Đọc ổ đĩa FAT32 raw
│   ├── reader.py           Mở \\.\E: → đọc sector theo LBA
│   ├── boot_sector.py      Parse BPB (7 trường thông số ổ đĩa)
│   ├── fat_table.py         Đọc bảng FAT → theo dõi cluster chain
│   └── directory.py         Duyệt thư mục đệ quy → tìm file .txt
│
├── gui/                 Lab 2 – Giao diện PyQt5
│   ├── main_window.py      Cửa sổ chính (chọn drive + tabs)
│   ├── boot_tab.py          Tab 1: Hiển thị Boot Sector info
│   ├── files_tab.py         Tab 2: Danh sách file .txt
│   └── detail_dialog.py     Dialog: thông tin file + Gantt chart + metrics
│
├── main.py              Lab 1 – CLI entry point
└── main_gui.py          Lab 2 – GUI entry point
```

---

## 4 Hàm Chính

### Hàm 1 – Hiển thị Boot Sector
- **File:** `fat32/boot_sector.py` + `gui/boot_tab.py`
- **Logic:** Đọc 512 byte đầu ổ đĩa → parse 7 trường BPB → hiện bảng

### Hàm 2 – Liệt kê file .txt
- **File:** `fat32/directory.py` + `gui/files_tab.py`
- **Logic:** Từ thông số BPB → đọc bảng FAT → duyệt thư mục đệ quy → lọc .txt

### Hàm 3 – Xem chi tiết file
- **File:** `fat32/directory.py` (đọc content) + `gui/detail_dialog.py` (phần A+B)
- **Logic:** Theo cluster chain → đọc bytes → decode UTF-8 → parse format Lab 01

### Hàm 4 – Gantt chart + Metrics
- **File:** `gui/detail_dialog.py` (phần C+D)
- **Logic:** Gọi `run_scheduling()` từ Lab 01 → vẽ Gantt bằng QPainter → tính Turnaround/Waiting

---

## Luồng Dữ Liệu Tóm Tắt

```
Nhập "E" → Connect
    │
    ├── reader.py      → Mở \\.\E:
    ├── boot_sector.py → Parse BPB (bản đồ ổ đĩa)
    ├── fat_table.py   → Đọc bảng FAT (mục lục file)
    ├── directory.py   → Duyệt thư mục → tìm .txt
    │
    └── Hiển thị Tab 1 (Boot Sector) + Tab 2 (danh sách .txt)

Chọn file .txt → View Details
    │
    ├── Đọc nội dung file qua cluster chain
    ├── Parse → queues + processes (format Lab 01)
    ├── run_scheduling()  ← TÁI DÙNG LAB 01
    ├── Vẽ Gantt chart
    └── Hiển thị Turnaround / Waiting
```

---

## Khái Niệm FAT32 Cần Nhớ

| Khái niệm | Giải thích |
|---|---|
| **Sector** | Đơn vị nhỏ nhất, thường 512 byte |
| **Cluster** | Nhóm sectors (VD: 8 sectors = 4KB), đơn vị cấp phát cho file |
| **Boot Sector** | 512 byte đầu tiên, chứa "bản đồ" ổ đĩa (BPB) |
| **Bảng FAT** | "Mục lục" – mỗi entry chỉ tới cluster tiếp theo → tạo thành dây xích |
| **Cluster chain** | Chuỗi cluster liên kết chứa 1 file (5 → 8 → 12 → HẾT) |
| **RDET** | Root Directory Entry Table – thư mục gốc |
| **LFN** | Long File Name – hỗ trợ tên file dài hơn 8.3 ký tự |
| **LBA** | Logical Block Address – "số thứ tự" sector trên ổ đĩa |

---

## Công Thức Quan Trọng

```
LBA của cluster N = DataStart + (N - 2) × SecPerClus
```

Ví dụ: DataStart = 30720, SecPerClus = 8
- Cluster 2 → LBA = 30720 + (2-2)×8 = 30720
- Cluster 5 → LBA = 30720 + (5-2)×8 = 30744
