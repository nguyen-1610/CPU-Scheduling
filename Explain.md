# Lab 02 – Giải Thích Toàn Bộ Luồng Hoạt Động

> Tài liệu này giải thích **từ A đến Z** cách ứng dụng Lab 02 hoạt động:
> từ lúc nhấn nút "Connect" cho đến lúc hiện Gantt chart trên màn hình.

---

## 1. Bức Tranh Tổng Quan

Lab 02 làm **3 việc chính** theo thứ tự:

```
┌─────────────┐      ┌──────────────────┐      ┌────────────────────┐
│  ĐỌC Ổ ĐĨA  │ ──▶  │  DUYỆT THƯ MỤC   │ ──▶  │  CHẠY LẬP LỊCH CPU  │
│  (FAT32 raw) │      │  (tìm file .txt)  │      │  (tái dùng Lab 01)  │
└─────────────┘      └──────────────────┘      └────────────────────┘
     fat32/                fat32/                  controller/ +
  reader.py             directory.py              algorithms/
  boot_sector.py
  fat_table.py
```

**Ý tưởng cốt lõi:** Thay vì đọc file bằng `open("input.txt")` như Lab 01, Lab 02 phải **tự đọc từng byte trên ổ USB** (raw device) và tự hiểu cấu trúc FAT32 để tìm ra file nằm ở đâu trên đĩa.

---

## 2. Cây Thư Mục Sau Khi Hoàn Thành

```
CPU-Scheduling/
├── src/
│   ├── algorithms/           ← Lab 1 (KHÔNG ĐỤNG)
│   ├── controller/           ← Lab 1 (KHÔNG ĐỤNG)
│   ├── io/                   ← Lab 1 (KHÔNG ĐỤNG)
│   ├── model/                ← Lab 1 (KHÔNG ĐỤNG)
│   │
│   ├── fat32/                ★ MỚI – Đọc ổ đĩa FAT32
│   │   ├── __init__.py
│   │   ├── reader.py         # Bước 1: Mở ổ đĩa, đọc sector
│   │   ├── boot_sector.py    # Bước 2: Hiểu "bản đồ" ổ đĩa
│   │   ├── fat_table.py      # Bước 3: Đọc "mục lục" file
│   │   └── directory.py      # Bước 4: Duyệt thư mục, tìm .txt
│   │
│   ├── gui/                  ★ MỚI – Giao diện PyQt5
│   │   ├── __init__.py
│   │   ├── main_window.py    # Cửa sổ chính
│   │   ├── boot_tab.py       # Tab 1: Info Boot Sector
│   │   ├── files_tab.py      # Tab 2: Danh sách .txt
│   │   └── detail_dialog.py  # Dialog: Gantt chart + metrics
│   │
│   ├── main.py               ← Lab 1 CLI entry point
│   └── main_gui.py           ★ MỚI – Lab 2 GUI entry point
│
├── public/
├── requirements.txt          (đã thêm PyQt5)
└── README.md
```

---

## 3. Luồng Chạy Chi Tiết (Theo Thứ Tự Thời Gian)

### 📌 Giai đoạn 0: Khởi động

```
python -m src.main_gui
```

File `src/main_gui.py` tạo `QApplication` → tạo `MainWindow` → hiện cửa sổ.

```
main_gui.py  →  MainWindow.__init__()
                 ├── Tạo ô nhập Drive letter
                 ├── Tạo nút "Connect"
                 ├── Tạo Tab "Boot Sector"  (BootTab – bảng rỗng)
                 └── Tạo Tab "TXT Files"    (FilesTab – list rỗng)
```

> Lúc này chưa có gì xảy ra. App chờ người dùng nhập ký tự ổ đĩa và nhấn Connect.

---

### 📌 Giai đoạn 1: Nhấn "Connect" → Đọc Boot Sector

Khi nhấn Connect, hàm `MainWindow._on_connect()` chạy:

```
Người dùng nhập "E" → nhấn Connect
         │
         ▼
┌─── reader.py ───────────────────────────────────┐
│                                                   │
│  DiskReader("E")                                  │
│    → Mở \\.\E: bằng open(path, "rb")             │
│    → Giờ có thể đọc bất kỳ byte nào trên ổ đĩa   │
│                                                   │
│  reader.read_sector(0)                            │
│    → seek(0) → read(512 bytes)                    │
│    → Trả về 512 byte đầu tiên = BOOT SECTOR      │
│                                                   │
└───────────────────────────────────────────────────┘
```

> 📝 **Ghi chú:** `\\.\E:` là cách Windows cho phép đọc ổ đĩa ở dạng "raw" –
> tức đọc byte thô, không qua hệ điều hành. **Cần quyền Administrator.**

---

### 📌 Giai đoạn 2: Parse Boot Sector → Hiểu "Bản Đồ" Ổ Đĩa

512 byte đầu tiên của ổ FAT32 chứa **BIOS Parameter Block (BPB)** –
đó là "bản đồ" cho biết ổ đĩa được tổ chức thế nào.

```
┌─── boot_sector.py ──────────────────────────────┐
│                                                   │
│  parse_boot_sector(data_512_bytes)                │
│                                                   │
│  Đọc từng trường bằng struct.unpack_from():       │
│                                                   │
│  Offset 11 (2 byte) → BytsPerSec  = 512          │
│  Offset 13 (1 byte) → SecPerClus  = 8            │
│  Offset 14 (2 byte) → RsvdSecCnt  = 32           │
│  Offset 16 (1 byte) → NumFATs     = 2            │
│  Offset 32 (4 byte) → TotSec32    = 15728640     │
│  Offset 36 (4 byte) → FATSz32     = 15344        │
│  Offset 44 (4 byte) → RootClus    = 2            │
│                                                   │
│  Tính toán thêm:                                  │
│  FATStart  = RsvdSecCnt            = 32           │
│  DataStart = RsvdSecCnt + NumFATs × FATSz32       │
│            = 32 + 2 × 15344       = 30720         │
│                                                   │
└───────────────────────────────────────────────────┘
```

**Giải thích các con số quan trọng:**

| Trường | Ý nghĩa dễ hiểu |
|---|---|
| `BytsPerSec = 512` | Mỗi "ô" trên ổ đĩa chứa 512 byte |
| `SecPerClus = 8` | Mỗi "nhóm ô" (cluster) = 8 ô = 4096 byte |
| `FATStart = 32` | Bảng FAT bắt đầu từ ô số 32 |
| `DataStart = 30720` | Dữ liệu thật (file) bắt đầu từ ô 30720 |
| `RootClus = 2` | Thư mục gốc bắt đầu tại cluster số 2 |

**Hình dung ổ đĩa như một cái kệ sách:**

```
Ổ đĩa FAT32 = [Boot Sector][  Bảng FAT  ][   Vùng Data (file thật)   ]
                 ô 0-31       ô 32-30719     ô 30720 trở đi
                              ↑                ↑
                         "Mục lục"         "Nội dung sách"
```

---

### 📌 Giai đoạn 3: Đọc Bảng FAT → "Mục Lục" Của Ổ Đĩa

Bảng FAT giống như **mục lục** – nó cho biết mỗi file nằm ở những cluster nào.

```
┌─── fat_table.py ────────────────────────────────┐
│                                                   │
│  FATTable(reader, fat_start=32, fat_size=15344)   │
│                                                   │
│  1. Đọc toàn bộ bảng FAT vào RAM                 │
│     → read_sectors(32, 15344)                     │
│     → ~ 7.5 MB dữ liệu                          │
│                                                   │
│  2. Mỗi entry = 4 byte → chứa số cluster tiếp    │
│     FAT[2] = 3    → "cluster 2 nối tới cluster 3"│
│     FAT[3] = 4    → "cluster 3 nối tới cluster 4"│
│     FAT[4] = EOC  → "cluster 4 là cuối cùng"     │
│                                                   │
│  3. get_chain(2) → [2, 3, 4]                     │
│     → "File bắt đầu ở cluster 2, gồm 3 cluster" │
│                                                   │
└───────────────────────────────────────────────────┘
```

**Ví dụ trực quan:**

```
File "input.txt" có 10KB, mỗi cluster = 4KB
→ Cần 3 cluster để chứa file

Bảng FAT nói:
  Cluster 5 → 8 → 12 → HẾT (EOC)

Nghĩa là:
  Phần 1 của file nằm ở cluster 5
  Phần 2 nằm ở cluster 8
  Phần 3 nằm ở cluster 12
  → Ghép lại = toàn bộ file!
```

> ⚠️ **Quan trọng:** Đây chính là lý do cần bảng FAT: file trên ổ đĩa **không nhất thiết nằm liên tiếp**.
> Các phần có thể nằm rải rác, và bảng FAT giống "dây xích" nối chúng lại.

---

### 📌 Giai đoạn 4: Duyệt Thư Mục → Tìm File .txt

```
┌─── directory.py ────────────────────────────────┐
│                                                   │
│  list_txt_files(reader, fat, root_cluster=2, ...) │
│                                                   │
│  1. Đọc nội dung thư mục gốc (bắt từ cluster 2)  │
│     → Dùng fat.read_chain_data(2, ...)            │
│     → Lấy được toàn bộ byte của thư mục          │
│                                                   │
│  2. Mỗi entry thư mục = 32 byte, chứa:           │
│     - Tên file (8 ký tự + 3 extension)           │
│     - Attribute (file? thư mục? đã xóa?)         │
│     - Cluster đầu (file nằm ở đâu)               │
│     - Kích thước file                             │
│     - Ngày/giờ tạo                                │
│                                                   │
│  3. Gặp thư mục con → đệ quy vào (lặp lại)      │
│  4. Gặp file .TXT → thêm vào danh sách kết quả   │
│  5. Gặp 0x00 → hết → dừng                        │
│  6. Gặp 0xE5 → file đã xóa → bỏ qua             │
│                                                   │
└───────────────────────────────────────────────────┘
```

**Ví dụ duyệt:**

```
Thư mục gốc (/)
  ├── [DIR]  homework/     → đệ quy vào
  │           └── [FILE] baitap.txt  ✓ thêm vào list
  ├── [FILE] input.txt     ✓ thêm vào list  
  ├── [FILE] photo.jpg     ✗ không phải .txt, bỏ qua
  └── [DEL]  old.txt       ✗ đã xóa (0xE5), bỏ qua

Kết quả: ["/input.txt", "/homework/baitap.txt"]
```

**Về Long File Name (LFN):**

FAT32 gốc chỉ hỗ trợ tên 8.3 (ví dụ `INPUT~1.TXT`). Để hỗ trợ tên dài như `"bài tập lớn.txt"`, Windows dùng thêm các entry đặc biệt (attr = `0x0F`) đứng **trước** entry chính:

```
Entry LFN #3:  "n.txt"        ← phần cuối tên
Entry LFN #2:  "ài tập lớ"    ← phần giữa
Entry LFN #1:  "b"            ← phần đầu
Entry chính:   "BAITAP~1.TXT" ← tên 8.3 (backup)

→ Ghép LFN: "bài tập lớn.txt"
```

---

### 📌 Giai đoạn 5: Hiển thị trên GUI

Sau khi hoàn tất Giai đoạn 1-4, `MainWindow` cập nhật 2 tab:

```
MainWindow._on_connect()
    │
    ├── self._boot_tab.display(boot_info)
    │   └── Điền 7 trường BPB vào QTableWidget
    │
    └── self._files_tab.display(txt_files)
        └── Điền danh sách FileEntry vào QListWidget
```

---

### 📌 Giai đoạn 6: Chọn File → View Details → Chạy Lập Lịch

Khi nhấn "View Details" trên 1 file .txt:

```
FilesTab._on_view_details()
    │
    │  1. Lấy FileEntry đang chọn (có first_cluster, size)
    │
    │  2. Đọc NỘI DUNG file từ ổ đĩa:
    │     fat.read_chain_data(first_cluster, ...)
    │     → Theo cluster chain → ghép bytes → cắt theo size
    │     → decode("utf-8") → có text giống file input Lab 01!
    │
    │  3. Mở DetailDialog(file_entry, text)
    │
    ▼
DetailDialog.__init__()
    │
    ├── Phần A: Hiển thị info file (tên, ngày, giờ, size)
    │
    ├── Phần B: Parse text theo format Lab 01
    │   │  "3\n Q1 5 SJF\n Q2 10 SRTN\n ..."
    │   │   → queues = [QueueConfig(...), ...]
    │   │   → processes = [Process(...), ...]
    │   └── Hiển thị bảng process
    │
    ├── Phần C: GỌI ENGINE LAB 01
    │   │  segments, procs = run_scheduling(queues, processes)
    │   │                    ↑↑↑ TÁI DÙNG NGUYÊN CODE LAB 01
    │   │
    │   └── Vẽ Gantt chart bằng GanttWidget (QPainter)
    │       Mỗi segment → 1 hình chữ nhật màu
    │       Trục X = thời gian, nhãn = PID
    │
    └── Phần D: Tính metrics
        │  Turnaround = Completion - Arrival
        │  Waiting    = Turnaround - Burst
        └── Average ở dòng cuối
```

> 💡 **Mấu chốt:** Lab 02 không viết lại thuật toán lập lịch.
> Nó chỉ đọc file từ USB bằng cách "thủ công" (FAT32 raw),
> rồi feed dữ liệu vào `run_scheduling()` có sẵn từ Lab 01.

---

## 4. Sơ Đồ Tổng Hợp Luồng Dữ Liệu

```
 ┌────────────────────────────────────────────────────────────────────┐
 │                        NGƯỜI DÙNG                                  │
 │                    Nhập "E" → nhấn Connect                        │
 └───────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
 ┌───────────────────────────────────────────────────────────────┐
 │                     reader.py (DiskReader)                     │
 │               Mở raw device \\.\E: → đọc sector              │
 └──────────┬──────────────────┬─────────────────┬───────────────┘
            │                  │                 │
     read_sector(0)     read_sectors(32,...)   read_sectors(...)
            │                  │                 │
            ▼                  ▼                 ▼
 ┌──────────────┐   ┌──────────────┐   ┌─────────────────────┐
 │ boot_sector  │   │  fat_table   │   │   directory.py      │
 │  .py         │   │   .py        │   │                     │
 │              │   │              │   │  Duyệt thư mục      │
 │ Parse BPB    │   │ Đọc FAT vào │   │  đệ quy, tìm .txt   │
 │ → 7 trường   │   │ RAM, theo    │   │  → List[FileEntry]  │
 │              │   │ cluster chain│   │                     │
 └──────┬───────┘   └──────┬───────┘   └──────────┬──────────┘
        │                  │                      │
        ▼                  ▼                      ▼
 ┌───────────────────────────────────────────────────────────────┐
 │                     main_window.py (GUI)                      │
 │                                                               │
 │  Tab 1: Boot Sector    Tab 2: TXT Files                      │
 │  ┌────────┬────────┐   ┌──────────────────────┐              │
 │  │ Trường │ Giá trị│   │ /input.txt (89 bytes)│              │
 │  │--------│--------│   │ /sub/test.txt         │              │
 │  │ BPS    │ 512    │   │          [View Details]│              │
 │  │ SPC    │ 8      │   └──────────┬─────────────┘              │
 │  └────────┴────────┘              │                            │
 └───────────────────────────────────┼────────────────────────────┘
                                     │ nhấn View Details
                                     ▼
 ┌───────────────────────────────────────────────────────────────┐
 │                   detail_dialog.py                             │
 │                                                               │
 │  1. Đọc nội dung file qua cluster chain                      │
 │  2. Parse text → queues + processes (format Lab 01)           │
 │  3. run_scheduling(queues, processes)  ← TÁI DÙNG LAB 01    │
 │  4. Vẽ Gantt chart (QPainter)                                │
 │  5. Hiển thị bảng Turnaround / Waiting                       │
 └───────────────────────────────────────────────────────────────┘
```

---

## 5. Mapping: 4 Hàm Yêu Cầu ↔ Code

| Hàm yêu cầu | Mô tả | File thực hiện |
|---|---|---|
| **Hàm 1** | Hiển thị Boot Sector | `src/fat32/boot_sector.py` + `src/gui/boot_tab.py` |
| **Hàm 2** | Liệt kê tất cả file .txt | `src/fat32/directory.py` + `src/gui/files_tab.py` |
| **Hàm 3** | Xem chi tiết file .txt | `src/fat32/directory.py` (đọc content) + `src/gui/detail_dialog.py` phần A+B |
| **Hàm 4** | Vẽ Gantt + tính metrics | `src/gui/detail_dialog.py` phần C+D (gọi `run_scheduling()` từ Lab 01) |

---

## 6. Tóm Tắt Một Câu

> **Lab 02 = "Tự đọc ổ USB bằng tay" (FAT32 raw) + "Hiển thị kết quả Lab 01 trên GUI" (PyQt5).**

Lab 01 đã có engine lập lịch hoàn chỉnh. Lab 02 chỉ thêm 2 thứ:
1. **Cách đọc file mới** – không dùng `open()` mà đọc trực tiếp cấu trúc FAT32
2. **Cách hiển thị mới** – không in text ra terminal mà vẽ GUI bằng PyQt5
