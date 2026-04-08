# Workflow Lab 2

Tài liệu này mô tả luồng chạy của Lab 2 theo đúng code hiện tại, từ lúc người dùng chọn ổ đĩa đến lúc hiển thị kết quả scheduling.

## Mục tiêu của Lab 2

Lab 2 làm 4 việc chính:

1. Kết nối vào thiết bị FAT32 ở mức raw
2. Đọc cấu trúc FAT32 để tìm tất cả file `.txt`
3. Đọc nội dung file `.txt` đã chọn dưới dạng `bytes`
4. Parse dữ liệu và chạy lại scheduler của Lab 1 để hiển thị kết quả

## Sơ đồ tổng quát

```text
Người dùng chọn ổ đĩa
        |
        v
MainWindow._on_connect()
        |
        v
DiskReader mở raw device
        |
        v
Đọc Boot Sector -> parse BPB
        |
        v
Đọc FAT table
        |
        v
Duyệt root directory + sub-directory
        |
        v
Lọc tất cả file .txt
        |
        v
FilesTab hiển thị danh sách file
        |
        v
Người dùng chọn 1 file -> View Details
        |
        v
Đọc nội dung file theo cluster chain
        |
        v
DetailDialog parse bytes -> queues + processes
        |
        v
run_scheduling()
        |
        v
Hiển thị thông tin file + process + kết quả scheduling
```

## Luồng chi tiết theo từng bước

### Bước 1. Người dùng chọn ổ đĩa và nhấn `Connect`

Điểm bắt đầu nằm ở [src/gui/main_window.py:143](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/main_window.py:143).

Hàm `_on_connect()` có nhiệm vụ:

- Lấy đường dẫn thiết bị hoặc tên ổ đĩa
- Đóng kết nối cũ nếu đang mở
- Gọi `DiskReader(drive)` để mở raw device

Đoạn mở thiết bị nằm ở [src/fat32/reader.py:21](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/reader.py:21) và [src/fat32/reader.py:42](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/reader.py:42).

Ý nghĩa:

- Đây là bước đưa chương trình vào chế độ đọc byte thô từ thiết bị FAT32
- Chương trình không mở file `.txt` bình thường ở bước này

### Bước 2. `DiskReader` xác định offset phân vùng FAT32

Phần này nằm ở [src/fat32/reader.py:59](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/reader.py:59).

Hàm `_detect_partition()`:

- Đọc sector 0
- Kiểm tra đây là Boot Sector trực tiếp hay là MBR
- Nếu là MBR thì duyệt partition table để tìm phân vùng FAT32
- Lưu `partition_offset`

Ý nghĩa:

- Nếu thiết bị có MBR, chương trình cần biết phân vùng FAT32 bắt đầu ở sector nào
- Các lần đọc sau đó đều cộng thêm offset này

### Bước 3. Đọc Boot Sector và parse thông tin BPB

Phần gọi nằm ở [src/gui/main_window.py:177](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/main_window.py:177).

Luồng:

```python
raw_boot = self._reader.read_sector(0)
self._boot_info = parse_boot_sector(raw_boot)
validate_fat32(self._boot_info)
```

Các file liên quan:

- [src/fat32/reader.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/reader.py)
- [src/fat32/boot_sector.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/boot_sector.py)

Thông tin lấy ra gồm:

- `BytsPerSec`
- `SecPerClus`
- `RsvdSecCnt`
- `NumFATs`
- `FATSz32`
- `RootClus`
- `TotSec32`
- `FATStart`
- `DataStart`

Ý nghĩa:

- Đây là bước dựng "bản đồ" của ổ đĩa
- Không có bước này thì không biết bảng FAT và vùng dữ liệu nằm ở đâu

### Bước 4. Cập nhật `bytes_per_sector`

Phần này nằm ở [src/gui/main_window.py:182](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/main_window.py:182).

Sau khi parse Boot Sector xong, chương trình cập nhật:

```python
self._reader.bytes_per_sector = self._boot_info["BytsPerSec"]
```

Ý nghĩa:

- Từ đây trở đi, `DiskReader` sẽ đọc đúng kích thước sector thực tế của thiết bị

### Bước 5. Đọc toàn bộ FAT table

Phần gọi nằm ở [src/gui/main_window.py:185](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/main_window.py:185).

Hàm `FATTable(...)` trong [src/fat32/fat_table.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py) sẽ:

- Đọc toàn bộ bảng FAT vào RAM
- Tách từng entry FAT32
- Cho phép truy ra cluster tiếp theo của một chain

Các hàm quan trọng:

- [src/fat32/fat_table.py:21](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py:21) `__init__(...)`
- [src/fat32/fat_table.py:38](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py:38) `next_cluster(...)`
- [src/fat32/fat_table.py:50](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py:50) `get_chain(...)`
- [src/fat32/fat_table.py:61](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py:61) `read_chain_data(...)`

Ý nghĩa:

- FAT table giống như bản chỉ đường giữa các cluster
- Nếu file nằm rải rác, chương trình sẽ lần theo FAT để ghép lại nội dung đúng thứ tự

### Bước 6. Duyệt thư mục và lọc tất cả file `.txt`

Phần gọi nằm ở [src/gui/main_window.py:193](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/main_window.py:193).

Hàm được gọi:

```python
self._txt_files = list_txt_files(...)
```

Hàm này nằm ở [src/fat32/directory.py:92](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/directory.py:92).

Nó làm những việc sau:

- Bắt đầu từ `RootClus`
- Đọc dữ liệu directory theo cluster chain
- Duyệt từng directory entry 32 byte
- Bỏ qua entry rỗng và entry đã xóa
- Xử lý tên ngắn 8.3 và LFN
- Phân biệt file và thư mục
- Đệ quy xuống thư mục con
- Chỉ giữ lại file có đuôi `.TXT`

Các vị trí chính:

- [src/fat32/directory.py:109](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/directory.py:109) `_walk_directory(...)`
- [src/fat32/directory.py:127](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/directory.py:127) xử lý `0x00` và `0xE5`
- [src/fat32/directory.py:138](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/directory.py:138) xử lý LFN
- [src/fat32/directory.py:167](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/directory.py:167) xử lý thư mục con
- [src/fat32/directory.py:187](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/directory.py:187) lọc `.TXT`

Ý nghĩa:

- Đây là bước tìm ra danh sách file để hiển thị trên GUI
- Chương trình không dùng `os.listdir()` hay duyệt cây thư mục của hệ điều hành

### Bước 7. Tính `RDETSectors`

Phần này nằm ở [src/gui/main_window.py:202](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/main_window.py:202).

Code hiện tại làm:

```python
root_chain = self._fat.get_chain(self._boot_info["RootClus"])
self._boot_info["RDETSectors"] = len(root_chain) * self._boot_info["SecPerClus"]
```

Ý nghĩa:

- Root Directory của FAT32 là một cluster chain
- Chương trình đếm số cluster thật của root directory để tính ra số sector tương ứng

### Bước 8. Hiển thị dữ liệu lên GUI

Phần này nằm ở [src/gui/main_window.py:207](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/main_window.py:207).

Hai tab được cập nhật:

- [src/gui/boot_tab.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/boot_tab.py): hiển thị thông tin Boot Sector
- [src/gui/files_tab.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/files_tab.py): hiển thị danh sách file `.txt`

## Luồng khi người dùng chọn một file `.txt`

### Bước 9. Người dùng nhấn `View Details`

Điểm bắt đầu ở [src/gui/files_tab.py:75](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/files_tab.py:75).

`FilesTab` sẽ:

- Lấy `FileEntry` đang được chọn
- Lấy `reader`, `fat`, `boot_info` từ `MainWindow`
- Gọi `fat.read_chain_data(...)` để đọc nội dung file
- Cắt dữ liệu theo đúng `file size`

Phần đọc nội dung file nằm ở [src/gui/files_tab.py:90](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/files_tab.py:90).

Ý nghĩa:

- Dữ liệu file được đọc từ các cluster trên FAT32
- Kết quả đầu ra là `raw_content: bytes`

### Bước 10. Mở `DetailDialog` và parse nội dung file

Sau khi đọc xong `raw_content`, `FilesTab` gọi:

```python
dlg = DetailDialog(fe, raw_content, parent=self)
```

Vị trí: [src/gui/files_tab.py:105](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/files_tab.py:105)

Trong [src/gui/detail_dialog.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/detail_dialog.py), hàm:

- [src/gui/detail_dialog.py:121](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/detail_dialog.py:121) `_parse_lab1_input(raw_content)`

sẽ gọi:

- [src/gui/detail_dialog.py:124](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/detail_dialog.py:124) `parse_input_bytes(raw_content)`

Ý nghĩa:

- Đây là bước chuyển `bytes` thành danh sách queue và process
- Parser không tự đọc file nữa, nó chỉ nhận bytes đã được đọc từ FAT32

### Bước 11. Chạy scheduler của Lab 1

Sau khi parse xong, `DetailDialog` tạo danh sách process mới và gọi:

- [src/controller/scheduler.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/controller/scheduler.py)

Mục đích:

- Tái sử dụng lại engine của Lab 1
- Sinh ra các segment scheduling và completion time của từng process

## Bước 12. Hiển thị kết quả cuối cùng

`DetailDialog` hiển thị:

- Thông tin file
- Bảng process
- Kết quả scheduling

File giao diện chính:

- [src/gui/detail_dialog.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/detail_dialog.py)

## Vai trò của từng nhóm file

### Nhóm đọc FAT32

- [src/fat32/reader.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/reader.py): mở raw device, đọc sector
- [src/fat32/boot_sector.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/boot_sector.py): parse BPB
- [src/fat32/fat_table.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py): đọc FAT và theo cluster chain
- [src/fat32/directory.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/directory.py): duyệt thư mục, lọc file `.txt`

### Nhóm giao diện Lab 2

- [src/gui/main_window.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/main_window.py): điều phối luồng chính
- [src/gui/boot_tab.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/boot_tab.py): hiển thị Boot Sector
- [src/gui/files_tab.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/files_tab.py): hiển thị danh sách file và đọc nội dung file được chọn
- [src/gui/detail_dialog.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/detail_dialog.py): parse bytes và hiển thị kết quả

### Nhóm tái sử dụng từ Lab 1

- [src/io/parser.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py): parse bytes thành queue/process
- [src/controller/scheduler.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/controller/scheduler.py): chạy scheduling
- [src/algorithms/](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms): các thuật toán SJF, SRTN, Round Robin

## Kết luận ngắn

Workflow của Lab 2 hiện tại là:

1. Mở raw device
2. Đọc Boot Sector
3. Đọc FAT
4. Duyệt thư mục để tìm `.txt`
5. Đọc nội dung file `.txt` theo cluster chain
6. Parse `bytes`
7. Chạy scheduler
8. Hiển thị kết quả trên GUI

Điểm quan trọng là luồng GUI Lab 2 đang đọc file `.txt` từ FAT32 dưới dạng `bytes`, không đi theo kiểu mở file văn bản trực tiếp từ hệ điều hành.
