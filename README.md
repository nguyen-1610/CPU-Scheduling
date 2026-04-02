# CPU Scheduling – Lab 01 & Lab 02

Đồ án mô phỏng lập lịch CPU đa hàng đợi (Multi-Level Queue) với Round Robin xoay vòng giữa các queue, mỗi queue áp dụng thuật toán SJF hoặc SRTN.

---

## Cấu Trúc Thư Mục

```
CPU-Scheduling/
├── src/
│   ├── algorithms/          # SJF, SRTN, RoundRobin, Registry (Plugin)
│   ├── controller/          # Engine lập lịch (scheduler.py)
│   ├── io/                  # Đọc input / xuất report
│   ├── model/               # Data classes (Process, Segment, QueueConfig)
│   ├── fat32/               # Đọc raw FAT32 (reader, boot sector, FAT table, directory)
│   ├── gui/                 # Giao diện PyQt5 (main window, tabs, dialog)
│   ├── main.py              # Entry point Lab 01 (CLI)
│   └── main_gui.py          # Entry point Lab 02 (GUI)
│
├── public/                  # File input/output mẫu
├── requirements.txt         # Dependencies (PyQt5)
├── Explain.md               # Giải thích chi tiết luồng hoạt động Lab 02
└── GUIDE_LAB2.md            # Hướng dẫn & khái niệm FAT32
```

---

## Lab 01 – CLI Scheduling

Đọc file `.txt` mô tả queue + process → chạy Round Robin + SJF/SRTN → xuất Gantt chart + bảng metrics ra file.

### Chạy

```bash
python -m src.main <input_file> <output_file>
```

**Ví dụ:**

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
- N dòng tiếp: `QueueID  TimeSlice  Algorithm`
- Các dòng còn lại: `ProcessID  ArrivalTime  BurstTime  QueueID`

---

## Lab 02 – GUI FAT32 Reader

Mở ổ USB FAT32 ở dạng raw → đọc Boot Sector → duyệt thư mục tìm file `.txt` → parse nội dung → chạy engine Lab 01 → hiển thị Gantt chart trên GUI.

### Cài đặt

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Chạy

> ⚠️ **Cần chạy terminal với quyền Administrator** (chuột phải → Run as Administrator)

```bash
python -m src.main_gui
```

### Sử dụng

1. Cắm USB định dạng FAT32 (có chứa file `.txt` theo format Lab 01)
2. Nhập ký tự ổ đĩa (ví dụ: `E`) → nhấn **Connect**
3. Tab **Boot Sector**: xem 7 trường BPB
4. Tab **TXT Files**: danh sách file `.txt` → chọn file → nhấn **View Details**
5. Dialog hiện: thông tin file, bảng process, Gantt chart, bảng metrics

---

## Yêu Cầu

- Python 3.7+
- PyQt5 (chỉ cần cho Lab 02)
- Windows (đọc raw device qua `\\.\X:`)
- Quyền Administrator (chỉ cần cho Lab 02)
