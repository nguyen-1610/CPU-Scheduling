# CPU Scheduling – Lab 01 & Lab 02

---

## Thành Viên Nhóm

| Họ và tên | MSSV | Phụ trách |
|---|---|---|
| Huỳnh Duy Nguyên | 24127467 | Section 1, 2 (Boot Sector, List file .txt) |
| Trương Nguyễn Thành Danh | 24127150 | Section 3, 4 (Chi tiết file, Scheduling diagram) |

---

## Mô Tả

Đồ án gồm 2 lab:

- **Lab 01 (CLI):** Mô phỏng lập lịch CPU đa hàng đợi (Multi-Level Queue) với Round Robin xoay vòng giữa các queue, mỗi queue áp dụng thuật toán SJF hoặc SRTN.
- **Lab 02 (GUI):** Đọc trực tiếp ổ USB FAT32 ở dạng raw byte (không dùng API hệ điều hành), tìm file `.txt`, đọc nội dung và chạy lại engine scheduling của Lab 01.

---

## Cấu Trúc Thư Mục

```
24127467_24127150/
├── src/
│   ├── algorithms/          # SJF, SRTN, RoundRobin, Registry (Plugin pattern)
│   ├── controller/          # Engine lập lịch (scheduler.py)
│   ├── io/                  # Parse input / format output report
│   ├── model/               # Data classes: Process, Segment, QueueConfig
│   ├── fat32/               # Đọc raw FAT32: reader, boot_sector, fat_table, directory, macos_utils
│   ├── gui/                 # Giao diện PySide6: main_window, boot_tab, files_tab, detail_dialog
│   ├── main.py              # Entry point Lab 01 (CLI)
│   └── main_gui.py          # Entry point Lab 02 (GUI)
│
├── public/                  # File input/output mẫu
├── requirements.txt         # Dependencies: PySide6
└── README.md
```

---

## Lab 01 – CLI Scheduling

Đọc file `.txt` mô tả queue + process → chạy Round Robin + SJF/SRTN → xuất Gantt chart + bảng metrics ra file.

### Chạy

```bash
python -m src.main <input_file> <output_file>
```

Ví dụ:

```bash
python -m src.main ./public/input.txt ./public/output.txt
```

### Định dạng Input

```
3
Q1 5 SJF
Q2 10 SRTN
Q3 8 SJF

P1 0 12 Q1
P2 2 4 Q2
P3 3 8 Q1
P4 5 15 Q3
P5 8 5 Q2
```

- Dòng 1: Số lượng queue
- N dòng tiếp: `QueueID  TimeSlice  Algorithm` (Algorithm là `SJF` hoặc `SRTN`)
- Các dòng còn lại: `ProcessID  ArrivalTime  BurstTime  QueueID`

---

## Lab 02 – GUI FAT32 Reader

Mở ổ USB FAT32 ở dạng raw → đọc Boot Sector (BPB) → đọc FAT Table → duyệt thư mục đệ quy tìm file `.txt` → parse nội dung → chạy engine Lab 01 → hiển thị kết quả trên GUI.

> **Lưu ý:** Toàn bộ phần đọc FAT32 được thực hiện theo đúng cấu trúc FAT, không sử dụng bất kỳ hàm đọc file nào của hệ điều hành.

### Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# hoặc: .venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### Chạy

**macOS** – cần quyền sudo để đọc raw device:

```bash
sudo python -m src.main_gui
```

Nếu gặp lỗi quyền truy cập, cấp quyền thủ công:

```bash
sudo chmod 666 /dev/rdiskXsY
python -m src.main_gui
```

### Sử dụng

1. Cắm USB định dạng FAT32 (có chứa file `.txt` theo format Lab 01)
2. Nhấn **Detect USB** để tự động tìm ổ – hoặc nhập path thủ công (vd: `/dev/rdisk2s1`)
3. Nhấn **Connect** → app sẽ đọc Boot Sector, FAT Table, duyệt thư mục
4. Tab **Boot Sector**: xem 7 trường BPB (BytsPerSec, SecPerClus, RsvdSecCnt, NumFATs, FATSz32, RDETSectors, TotSec32)
5. Tab **TXT Files**: danh sách tất cả file `.txt` trên ổ (kể cả trong thư mục con)
6. Chọn file → nhấn **View Details** → dialog hiện: thông tin file, bảng process, Gantt chart, bảng Turnaround/Waiting time

---

## Yêu Cầu

- Python 3.10+
- PySide6
- macOS (đọc raw device qua `/dev/rdiskXsY`)
- Quyền sudo (chỉ cần cho Lab 02)
