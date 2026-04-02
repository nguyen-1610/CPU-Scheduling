# Lab 02 – Checklist

> Deadline: **23h59, ngày 12/04/2026**
> Ngôn ngữ: Python · GUI: PyQt5 · Đọc FAT32 raw (không dùng hàm file OS)

---

## Yêu cầu chung

- [ ] Chọn drive (thẻ nhớ / USB) định dạng FAT32 từ GUI
- [ ] Mở raw device bằng đường dẫn `\\.\X:` (Windows) với quyền Admin
- [ ] **Hàm 1, 2, 3 phải đọc trực tiếp cấu trúc FAT32**, không dùng `open()`, `os.listdir()`, v.v. với file thông thường

---

## Hàm 1 – Hiển thị Boot Sector

- [ ] Đọc sector 0 (512 byte đầu tiên của device)
- [ ] Parse các trường BPB (BIOS Parameter Block):
  - [ ] Bytes per sector (`BPB_BytsPerSec` – offset 11, 2 byte)
  - [ ] Sectors per cluster (`BPB_SecPerClus` – offset 13, 1 byte)
  - [ ] Number of sectors in Boot Sector region (`BPB_RsvdSecCnt` – offset 14, 2 byte)
  - [ ] Number of FAT tables (`BPB_NumFATs` – offset 16, 1 byte)
  - [ ] Number of sectors per FAT table (`BPB_FATSz32` – offset 36, 4 byte)
  - [ ] Number of sectors for RDET (tính từ cluster gốc `BPB_RootClus`, offset 44, 4 byte)
  - [ ] Total number of sectors (`BPB_TotSec32` – offset 32, 4 byte)
- [ ] Hiển thị trong bảng (table widget) trên GUI

---

## Hàm 2 – Liệt kê tất cả file *.txt

- [ ] Tính địa chỉ vùng FAT, Data, và cluster gốc từ thông số Boot Sector
- [ ] Đọc FAT table vào bộ nhớ (để tra cluster chain)
- [ ] Duyệt đệ quy toàn bộ cây thư mục:
  - [ ] Xử lý RDET (root directory) – FAT32: bắt đầu từ `RootClus`
  - [ ] Xử lý SDET (sub-directory entries)
  - [ ] Bỏ qua entry deleted (`0xE5`), entry trống (`0x00`)
  - [ ] Xử lý Long File Name (LFN) entries nếu tên file có LFN
  - [ ] Nhận diện file (attr bit `0x20`) và thư mục (attr bit `0x10`)
- [ ] Lọc chỉ lấy file có đuôi `.TXT` (so sánh không phân biệt hoa thường)
- [ ] Hiển thị danh sách phẳng (flat list) lên GUI – không hiển thị cây thư mục

---

## Hàm 3 – Xem chi tiết file *.txt được chọn

- [ ] Đọc Directory Entry của file được chọn:
  - [ ] Tên file đầy đủ (kèm extension)
  - [ ] Ngày tạo (`CrtDate` – offset 16 trong entry, 2 byte)
  - [ ] Giờ tạo (`CrtTime` – offset 14 trong entry, 2 byte)
  - [ ] Kích thước file (`FileSize` – offset 28 trong entry, 4 byte)
- [ ] Đọc nội dung file theo cluster chain từ FAT
- [ ] Parse nội dung theo định dạng input Lab 01:
  - [ ] Số lượng queue N
  - [ ] Với mỗi queue: QID, TimeSlice, Policy (SJF/SRTN)
  - [ ] Với mỗi process: PID, ArrivalTime, BurstTime, QueueID
- [ ] Hiển thị bảng thông tin process (PID, Arrival, Burst, QueueID, TimeSlice, Algorithm)

---

## Hàm 4 – Vẽ sơ đồ lập lịch + tính metrics

- [ ] Tái sử dụng engine lập lịch từ Lab 01 (`src/controller/scheduler.py`, `src/algorithms/`)
- [ ] Feed dữ liệu đọc từ file (Hàm 3) vào engine
- [ ] Vẽ Gantt chart (scheduling diagram) trên GUI:
  - [ ] Mỗi dải màu = 1 segment (process + queue)
  - [ ] Trục X = thời gian, nhãn start/end
  - [ ] Chú thích màu theo process hoặc queue
- [ ] Hiển thị bảng metrics:
  - [ ] Turnaround Time từng process
  - [ ] Waiting Time từng process
  - [ ] Average Turnaround Time
  - [ ] Average Waiting Time

---

## GUI tổng thể

- [ ] Thanh chọn drive (combobox hoặc input path) + nút "Connect / Read"
- [ ] Tab 1: Boot Sector Info
- [ ] Tab 2: File List (*.txt) + nút "View Details"
- [ ] Tab 3 / Dialog: Chi tiết file + Gantt chart + Metrics
- [ ] Thông báo lỗi thân thiện (không có quyền Admin, không phải FAT32, v.v.)

---

## Kiểm thử

- [ ] Test với USB / thẻ nhớ thật định dạng FAT32 chứa file .txt Lab 01
- [ ] Test với file .txt trong thư mục gốc và trong thư mục con
- [ ] Test file tên dài (LFN)
- [ ] Xác minh kết quả Gantt/metrics khớp với output Lab 01

---

## Nộp bài

- [ ] Đóng gói `MSSV1_MSSV2.zip` (source code, bỏ `__pycache__`, `.venv`, v.v.)
- [ ] Viết báo cáo `MSSV1_MSSV2.PDF` (Times New Roman 13pt, Justify, 1.15)
  - [ ] Thông tin nhóm
  - [ ] Danh sách hàm đã cài đặt
  - [ ] Ghi rõ phần nào dùng tài liệu/công cụ ngoài (citation)
