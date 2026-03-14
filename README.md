# CPU Scheduling Simulator

Bài tập lập trình môn **Hệ Điều Hành** – mô phỏng lập lịch CPU đa hàng đợi với các thuật toán **SJF** và **SRTN**, vòng ngoài chọn hàng đợi theo **Round Robin**.

---

## Thành Viên & Phân Công

| Họ và tên | MSSV | Phụ trách |
|-----------|------|-----------|
| Huỳnh Duy Nguyên | 24127467 | Thuật toán SRTN, Registry, cấu trúc repo, Parser, Layout Output |
| Trương Nguyễn Thành Danh | 24127150 | Thuật toán Round Robin, SJF, Scheduler, Model, Main |

---

## Kiến Trúc

```
CPU-Scheduling/
├── public/
│   └── input.txt              # File đầu vào mặc định
├── src/
│   ├── main.py                # Entrypoint
│   ├── model/
│   │   └── entities.py        # Khai báo QueueConfig, Process, Segment
│   ├── io/
│   │   ├── parser.py          # Đọc & validate input.txt
│   │   └── layoutOutput.py    # Định dạng output (CPU diagram + thống kê)
│   ├── algorithms/
│   │   ├── registry.py        # Tra cứu thuật toán theo tên
│   │   ├── sjf.py             # Shortest Job First (non-preemptive)
│   │   ├── srtn.py            # Shortest Remaining Time Next (preemptive)
│   │   └── roundRobin.py      # Chọn hàng đợi tiếp theo
│   └── controller/
│       └── scheduler.py       # Vòng lặp lập lịch chính
└── learning.md                # Tài liệu giải thích thuật toán
```

---

## Cách Chạy

**Yêu cầu:** Python 3.8+

```bash
# Chạy với file input mặc định (public/input.txt) → ghi ra public/output.txt
python3 -m src.main

# Chỉ định cả input lẫn output
python3 -m src.main input.txt output.txt
```

**Định dạng file input:**
```
<số hàng đợi N>
<QueueID> <TimeSlice> <Policy>   # Policy: SJF hoặc SRTN
...                               # (lặp N lần)
<PID> <Arrival> <Burst> <QueueID>
...
```

**Ví dụ:**
```
3
Q1 8 SRTN
Q2 5 SJF
Q3 3 SJF
P1 0 12 Q1
P2 1 6 Q1
P3 2 8 Q2
P4 3 4 Q2
P5 4 10 Q3
```
