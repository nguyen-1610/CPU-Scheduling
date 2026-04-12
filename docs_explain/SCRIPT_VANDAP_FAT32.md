# SCRIPT VẤN ĐÁP – PHẦN FAT32

---

## PHẦN 1: CẤU TRÚC FAT32 TRÊN Ổ ĐĨA

### Ổ đĩa = mảng các sector

Toàn bộ ổ đĩa là một mảng các **sector** (thường 512 byte), đánh số từ 0 gọi là LBA (Logical Block Address).
Để đọc byte nào đó trên đĩa, ta cần biết nó nằm ở **LBA nào**, rồi seek đến đó và read.

```
LBA:  0        1        2        3  ...
     [sector][sector][sector][sector]...
```

### Bố cục 3 vùng của FAT32

```
LBA 0:              Boot Sector   ← bản đồ của ổ đĩa
LBA 1 → N:          FAT Table     ← bảng liên kết cluster
LBA N+1 → hết:      Data Region   ← nơi lưu file/thư mục thật
```

**Boot Sector (512 byte đầu tiên)** chứa BPB – tất cả thông số cần thiết:

| Offset | Tên | Kích thước | Ý nghĩa |
|---|---|---|---|
| 11 | BytsPerSec | 2 byte | Số byte mỗi sector |
| 13 | SecPerClus | 1 byte | Số sector mỗi cluster |
| 14 | RsvdSecCnt | 2 byte | Số sector vùng Boot |
| 16 | NumFATs | 1 byte | Số bảng FAT |
| 32 | TotSec32 | 4 byte | Tổng số sector |
| 36 | FATSz32 | 4 byte | Số sector mỗi bảng FAT |
| 44 | RootClus | 4 byte | Cluster đầu tiên của root dir |

Từ BPB tính ra 2 mốc quan trọng:
```
FATStart  = RsvdSecCnt
DataStart = RsvdSecCnt + NumFATs × FATSz32
```

**FAT Table** là mảng số 32-bit, mỗi phần tử = cluster tiếp theo (linked list):
```
FAT[5] = 8  →  FAT[8] = 12  →  FAT[12] = 0x0FFFFFFF (EOC = kết thúc)
```

**Data Region** chia thành các cluster (nhóm sector), đánh số từ **2** (0 và 1 reserved).
Công thức tính LBA của cluster:
```
LBA = DataStart + (cluster - 2) × SecPerClus
```

### Directory Entry = thông tin file/thư mục

Thư mục trong FAT32 là file đặc biệt, nội dung bên trong là các **32-byte entry**:
```
Byte 0-7:   tên file (8 byte ASCII, padding space)
Byte 8-10:  extension (3 byte ASCII)
Byte 11:    attribute (loại entry: file, thư mục, LFN...)
Byte 14-15: CrtTime  (giờ/phút/giây gộp trong 16 bit)
Byte 16-17: CrtDate  (năm/tháng/ngày gộp trong 16 bit)
Byte 20-21: ClusterHI (16 bit cao của cluster đầu)
Byte 26-27: ClusterLO (16 bit thấp của cluster đầu)
Byte 28-31: FileSize  (4 byte)
```

**Bit packing** của date/time – nhiều trường nhồi vào 1 số 16-bit:
```
CrtDate (16 bit): [year:7bit][month:4bit][day:5bit]

day   = raw & 0x1F              ← giữ 5 bit thấp
month = (raw >> 5) & 0x0F       ← bỏ 5 bit day, giữ 4 bit
year  = (raw >> 9) & 0x7F + 1980← bỏ 9 bit, giữ 7 bit, cộng 1980
```

**Ghép cluster** từ 2 mảnh (do tương thích FAT16):
```python
first_cluster = (ClusterHI << 16) | ClusterLO
# ClusterHI chiếm 16 bit trên, ClusterLO chiếm 16 bit dưới
```

**Endianness**: FAT32 dùng **Little Endian** (byte thấp đứng trước). Code dùng `<H`, `<I`, `<B` trong `struct.unpack_from`.

### LFN – tên file dài

Khi tên > 8 ký tự, FAT32 tạo thêm **LFN entry phụ** (attr = 0x0F) đứng trước SFN entry:
- Mỗi LFN entry chứa 13 ký tự UCS-2 rải ở offset 1, 14, 28
- Byte 0 = order number, ghi **ngược** trên đĩa (entry cuối ghi trước)
- Khi đọc: thu thập → sort theo order → ghép lại = tên đầy đủ

---

## PHẦN 2: SƠ ĐỒ TỔNG QUAN

```
Người dùng chọn ổ đĩa
        |
        v
MainWindow._on_connect()          [main_window.py]
        |
        v
DiskReader mở raw device          [reader.py]
        |
        v
_detect_partition() → partition_offset
        |
        v
Đọc Boot Sector → parse BPB       [boot_sector.py]
        |
        v
Cập nhật bytes_per_sector
        |
        v
Đọc toàn bộ FAT Table → RAM       [fat_table.py]
        |
        v
Duyệt root dir + sub-dir đệ quy   [directory.py]
        |
        v
Lọc tất cả file .txt → FileEntry list
        |
        v
Tính RDETSectors từ root chain
        |
        v
Hiển thị Boot Sector + danh sách file lên GUI
        |
        v
Người dùng chọn 1 file → View Details
        |
        v
Đọc nội dung file theo cluster chain
        |
        v
DetailDialog: parse bytes → queues + processes  [parser.py]
        |
        v
run_scheduling()                   [scheduler.py]
        |
        v
Hiển thị thông tin file + process + kết quả scheduling
```

---

## PHẦN 3: LUỒNG CHI TIẾT TỪNG BƯỚC KHI NHẤN "CONNECT"

### Bước 1: Lấy đường dẫn và unmount

**File:** `main_window.py` → hàm `_on_connect()`

- Lấy device path từ dropdown (userData) hoặc text nhập tay
- Đóng kết nối cũ nếu đang mở
- Gọi `unmount_disk_mac(drive)` → chạy lệnh `diskutil unmountDisk`

> Tại sao unmount? macOS đang kiểm soát ổ đĩa. Phải unmount thì kernel mới nhả quyền, ta mới đọc raw sector được.

### Bước 2: Mở raw device + phát hiện MBR

**File:** `reader.py` → `DiskReader.__init__()` + `_detect_partition()`

```python
self._handle = open("/dev/rdiskXsY", "rb")
```

`_detect_partition()`:
- Đọc sector 0, kiểm tra BytsPerSec tại offset 11
- Nếu hợp lệ (512/1024/2048/4096) → đây là VBR, `partition_offset = 0`
- Nếu không hợp lệ → đây là MBR, duyệt partition table tìm FAT32 (type 0x0B/0x0C), lưu LBA bắt đầu vào `partition_offset`

Mọi lần đọc sau đó đều tự động cộng `partition_offset`:
```python
actual_lba = lba + self._partition_offset
```

**RAM:** object `reader` lưu file handle và partition_offset

### Bước 3: Đọc Boot Sector → parse BPB

**File:** `boot_sector.py` → `parse_boot_sector(raw)`

```python
raw_boot = self._reader.read_sector(0)   # đọc 512 byte từ đĩa → RAM
self._boot_info = parse_boot_sector(raw_boot)
validate_fat32(self._boot_info)
```

`struct.unpack_from` tại từng offset → dict các trường BPB.

**RAM:** dict `boot_info` = { BytsPerSec, SecPerClus, FATStart, DataStart, RootClus, TotSec32, ... }

### Bước 4: Cập nhật bytes_per_sector

```python
self._reader.bytes_per_sector = self._boot_info["BytsPerSec"]
```

Bước này cần thiết vì ban đầu `DiskReader` mặc định sector = 512 byte. Sau khi đọc BPB mới biết chính xác. Từ đây trở đi mọi lần `read_sector` đều dùng kích thước đúng.

### Bước 5: Đọc toàn bộ FAT Table vào RAM

**File:** `fat_table.py` → `FATTable.__init__()`

```python
self._fat = FATTable(reader, fat_start_lba=boot_info["FATStart"], fat_size_sectors=boot_info["FATSz32"])
```

Bên trong:
- `read_sectors(FATStart, FATSz32)` → đọc toàn bộ FAT vào RAM
- Parse từng 4 byte: `struct.unpack_from("<I", raw, i*4)[0] & 0x0FFFFFFF`
- Lưu vào `self._entries = [0, 1, 8, 12, ...]`

**RAM:** `fat._entries` = toàn bộ FAT Table (list số nguyên)

> Tại sao load hết lên RAM? Để tra cluster chain nhanh bằng index mảng O(1), không phải đọc đĩa mỗi lần.

### Bước 6: Duyệt thư mục, lọc file .txt

**File:** `directory.py` → `list_txt_files()` → `_walk_directory()` đệ quy

Với mỗi thư mục:
1. `fat.read_chain_data(dir_cluster)` → đọc cluster chain → `raw` bytes
2. Cắt từng 32 byte → entry
3. Phân loại theo byte 0 và attr (byte 11):
   - `first_byte == 0x00` → dừng
   - `first_byte == 0xE5` → entry đã xóa, bỏ qua
   - `attr == 0x0F` → LFN entry phụ, thu thập vào `lfn_parts`
   - `attr & 0x08` → Volume Label, bỏ qua
   - `attr & 0x10` → thư mục con, đệ quy vào
   - còn lại → file thường, kiểm tra có đuôi `.TXT` không
4. File .txt → tạo `FileEntry`, append vào `results`

**RAM:** list `txt_files` = [FileEntry(name, path, size, first_cluster, crt_date, crt_time), ...]

> Chú ý: chỉ đọc **metadata** (entry 32 byte), không đọc **nội dung** file ở bước này.

### Bước 7: Tính RDETSectors

```python
root_chain = self._fat.get_chain(self._boot_info["RootClus"])
self._boot_info["RDETSectors"] = len(root_chain) * self._boot_info["SecPerClus"]
```

FAT32 không có vùng RDET cố định như FAT16. Root directory là 1 cluster chain bình thường. Phải đếm số cluster trong chain rồi nhân `SecPerClus` mới ra số sector thật của RDET.

### Bước 8: Hiển thị lên GUI

```python
self._boot_tab.display(self._boot_info)   # 7 trường BPB
self._files_tab.display(self._txt_files)  # danh sách .txt
```

Mỗi item trong list được gắn kèm object `FileEntry` qua `Qt.UserRole` (ẩn, user không thấy) để lấy lại sau khi click.

---

## PHẦN 4: LUỒNG KHI NHẤN "VIEW DETAILS"

### Bước 9: Lấy FileEntry và đọc nội dung file

**File:** `files_tab.py` → `_on_view_details()`

```python
fe = current.data(Qt.UserRole)   # lấy FileEntry đã gắn sẵn vào item

raw_content = fat.read_chain_data(
    fe.first_cluster, reader, DataStart, SecPerClus
)
raw_content = raw_content[:fe.size]   # cắt bỏ padding cluster
```

> Tại sao cắt `[:fe.size]`? `read_chain_data` đọc nguyên cluster (vd 4096 byte). File thật chỉ 200 byte. 3896 byte còn lại là padding, nếu không cắt thì parser đọc thêm byte rác → lỗi.

**RAM:** `raw_content` = bytes nội dung thật của file

### Bước 10: Parse bytes → queues + processes

**File:** `detail_dialog.py` → `_parse_lab1_input(raw_content)`

```python
queues, processes = parse_input_bytes(raw_content)
# decode bytes → text → đọc từng dòng → QueueConfig + Process
```

### Bước 11: Hiển thị thông tin file

```python
parse_fat_date(fe.crt_date)   # dịch bit → "DD/MM/YYYY"
parse_fat_time(fe.crt_time)   # dịch bit → "HH:MM:SS"
```

### Bước 12: Chạy scheduling

```python
fresh = [Process(pid=p.pid, arrival=p.arrival, burst=p.burst, ...) for p in processes]
# tạo copy mới để không làm hỏng object gốc (remaining/completion còn nguyên)

segments, result_procs = run_scheduling(queues, fresh)
report = buildReport(segments, result_procs)
```

> Tại sao tạo `fresh`? `run_scheduling` thay đổi trực tiếp `remaining` và `completion`. Nếu dùng thẳng, lần sau mở dialog lại thì object đã bị biến đổi → kết quả sai.

---

## PHẦN 5: CÁI GÌ NẰM Ở ĐĨA, CÁI GÌ LÊN RAM

| Dữ liệu | Nằm ở | Lưu trong biến | Tồn tại đến khi |
|---|---|---|---|
| Boot Sector (512 byte) | Đĩa LBA 0 | `boot_info` (dict) | Đóng app |
| FAT Table (toàn bộ) | Đĩa LBA FATStart | `fat._entries` (list int) | Đóng app |
| Nội dung thư mục (raw) | Đĩa (cluster chain) | `raw` (bytes, tạm) | Hàm kết thúc |
| Metadata file | Đĩa (32-byte entry) | `txt_files` (list FileEntry) | Connect lại |
| Nội dung file .txt | Đĩa (cluster chain) | `raw_content` (bytes, tạm) | Dialog đóng |
| Queue + Process | RAM (parse từ bytes) | `queues`, `processes` | Dialog đóng |
| Segments (kết quả) | RAM (tính toán) | `segments` (list Segment) | Dialog đóng |

**Quy tắc nhớ:** Gán vào biến = lên RAM. Biến `self.xxx` = tồn tại lâu dài. Biến local trong hàm = tạm thời, hàm xong thì mất.

---

## PHẦN 6: FILE NÀO CHỨA LOGIC GÌ

### Nhóm đọc FAT32
| File | Nhiệm vụ |
|---|---|
| `fat32/reader.py` | Mở raw device, đọc sector theo LBA, xử lý MBR/VBR offset |
| `fat32/boot_sector.py` | Parse 512 byte Boot Sector → dict BPB |
| `fat32/fat_table.py` | Đọc FAT vào RAM, tra cluster chain, đọc data theo chain |
| `fat32/directory.py` | Duyệt thư mục đệ quy, parse SFN/LFN, lọc .txt |
| `fat32/macos_utils.py` | Detect USB FAT32 trên macOS, unmount trước khi đọc |

### Nhóm giao diện Lab 2
| File | Nhiệm vụ |
|---|---|
| `gui/main_window.py` | Điều phối khi nhấn Connect: reader→boot→fat→directory |
| `gui/boot_tab.py` | Hiện bảng 7 trường BPB |
| `gui/files_tab.py` | Hiện danh sách .txt, đọc nội dung khi View Details |
| `gui/detail_dialog.py` | Parse bytes + chạy scheduling + hiện kết quả |

### Nhóm tái sử dụng từ Lab 1
| File | Nhiệm vụ |
|---|---|
| `io/parser.py` | Decode bytes → queues + processes |
| `controller/scheduler.py` | Điều phối scheduling: round robin queue, gọi SJF/SRTN |
| `algorithms/sjf.py` | Thuật toán SJF (non-preemptive) |
| `algorithms/srtn.py` | Thuật toán SRTN (preemptive) |
| `io/layoutOutput.py` | Format kết quả ra chuỗi: diagram + thống kê |

---

## PHẦN 7: CÂU HỎI VẤN ĐÁP

---

### 7A. PHẦN FAT32

**[Dễ] Q: FAT32 là gì? Ổ đĩa được tổ chức như thế nào?**
FAT32 là hệ thống file. Ổ đĩa được chia thành các sector (thường 512 byte), đánh số từ 0 gọi là LBA. FAT32 có 3 vùng: Boot Sector, FAT Table, Data Region.

**[Dễ] Q: Boot Sector chứa gì? Dùng để làm gì?**
Chứa BPB (BIOS Parameter Block) – các thông số mô tả cấu trúc ổ đĩa như BytsPerSec, SecPerClus, FATStart, DataStart, RootClus. Đây là "bản đồ" để biết các vùng khác nằm ở đâu.

**[Dễ] Q: Cluster là gì?**
Cluster là đơn vị lưu trữ dữ liệu, gồm nhiều sector liên tiếp. File được lưu trong 1 hoặc nhiều cluster. Cluster đánh số từ 2.

**[Dễ] Q: FAT Table dùng để làm gì?**
FAT Table là mảng số 32-bit, mỗi phần tử là cluster tiếp theo của chain. Dùng để biết file nằm rải rác ở những cluster nào trên đĩa (giống linked list).

**[Dễ] Q: Directory entry là gì? Kích thước bao nhiêu?**
Mỗi file/thư mục được mô tả bởi 1 directory entry = 32 byte cố định, chứa tên, attribute, ngày giờ tạo, cluster đầu, kích thước.

**[Dễ] Q: LFN là gì? Khi nào cần dùng?**
Long File Name – tên file dài hơn 8 ký tự. FAT32 tạo thêm các entry phụ (attr=0x0F) đứng trước SFN entry để lưu tên đầy đủ, mỗi entry phụ chứa 13 ký tự UCS-2.

**[Dễ] Q: Code đọc Boot Sector như thế nào?**
`reader.read_sector(0)` → 512 byte. Sau đó `struct.unpack_from` tại từng offset để lấy từng trường BPB.

**[Dễ] Q: `struct.unpack_from("<H", data, 11)` nghĩa là gì?**
Đọc 2 byte tại offset 11 từ `data`, theo định dạng little-endian unsigned short → ra số nguyên 16-bit. `<` = little-endian, `H` = 2 byte.

**[Dễ] Q: Little-endian là gì?**
Byte thấp (giá trị nhỏ) đứng trước byte cao trong bộ nhớ/đĩa. FAT32 dùng toàn bộ little-endian. Ví dụ số 0x1234 lưu là `[0x34][0x12]`.

**[Dễ] Q: `& 0x1F` là làm gì?**
Giữ lại 5 bit thấp nhất. `0x1F = 0001 1111`. Dùng để tách field nhỏ ra khỏi số lớn sau khi bit shift.

**[Trung] Q: Tại sao cluster đánh số từ 2?**
Cluster 0 và 1 trong FAT Table là reserved (lưu media type và flag). Data thật bắt đầu từ cluster 2. Vì vậy khi tính LBA phải trừ 2: `DataStart + (cluster - 2) × SecPerClus`.

**[Trung] Q: Công thức tính LBA của cluster là gì?**
`LBA = DataStart + (cluster - 2) × SecPerClus`. DataStart tính từ BPB: `RsvdSecCnt + NumFATs × FATSz32`.

**[Trung] Q: Tại sao cluster_hi và cluster_lo lại bị tách ra 2 chỗ trong entry?**
Do tương thích ngược với FAT16 – FAT16 chỉ có 16-bit cluster. FAT32 mở rộng lên 32-bit nhưng phải giữ format entry cũ. Phần cao (ClusterHI) thêm ở offset 20, phần thấp (ClusterLO) giữ ở offset 26. Ghép lại: `(hi << 16) | lo`.

**[Trung] Q: Tại sao bit shift `<< 16` thay vì `<< 4` hay số khác?**
Vì ClusterLO rộng 16 bit. Muốn ClusterHI nằm phía trên phải nhường đúng 16 bit chỗ: `hi << 16` đẩy hi lên 16 bit trên, còn 16 bit dưới trống để lo điền vào bằng `|`.

**[Trung] Q: `struct.unpack_from` khác bit shift ở điểm nào?**
`struct.unpack_from`: đọc nhiều byte từ bytes array → 1 số, giải quyết endianness. Bit shift `>> &`: tách field nhỏ trong 1 số, giải quyết bit packing. Hai kỹ thuật dùng nối tiếp nhau: unpack trước ra số, shift sau để tách field.

**[Trung] Q: LFN entry được đọc và ghép lại thế nào?**
LFN entry có attr = 0x0F. Byte 0 chứa order number, bit 6 là flag "entry cuối", `& 0x3F` lấy số thứ tự thật. Các entry ghi ngược trên đĩa (order cao trước). Code thu thập vào `lfn_parts`, sort theo order, ghép lại thành tên đầy đủ.

**[Trung] Q: Tại sao byte 0 = 0xE5 là entry đã xóa mà không xóa hẳn?**
Để xóa nhanh. Thay vì xóa toàn bộ 32 byte, chỉ ghi 0xE5 vào byte đầu. Data vẫn còn trên đĩa nhưng bị đánh dấu. Đó cũng là lý do phần mềm recovery có thể khôi phục file bị xóa.

**[Trung] Q: Tại sao FAT Table được load hết lên RAM?**
Để tra cluster chain nhanh bằng index mảng O(1), không phải đọc đĩa mỗi lần theo chain. Load 1 lần duy nhất khi Connect.

**[Trung] Q: RDET trong FAT32 tính thế nào, khác FAT16 chỗ nào?**
FAT16 có vùng RDET cố định, tính bằng `RootEntCnt × 32 / BytsPerSec`. FAT32 không có – root directory lưu trong cluster chain bình thường. Phải đếm số cluster trong chain của RootClus rồi nhân SecPerClus.

**[Trung] Q: Tại sao phải cắt `raw_content[:fe.size]`?**
`read_chain_data` đọc nguyên cluster (vd 4096 byte). File thật chỉ có vd 200 byte. Phần còn lại là padding của cluster. Không cắt thì parser đọc thêm byte rác → lỗi parse.

**[Khó] Q: Tại sao phải unmount trước khi đọc raw?**
macOS đang mount ổ đĩa, kernel kiểm soát việc đọc/ghi và cache. Muốn đọc raw sector trực tiếp phải unmount để kernel nhả quyền kiểm soát, nếu không sẽ bị lỗi quyền truy cập.

**[Khó] Q: MBR và VBR khác nhau thế nào? Code xử lý thế nào?**
VBR: sector 0 chính là Boot Sector FAT32, `partition_offset = 0`. MBR: sector 0 là bảng phân vùng, Boot Sector nằm sâu hơn. `_detect_partition()` kiểm tra BytsPerSec ở offset 11 – nếu hợp lệ thì là VBR, nếu không thì đọc MBR partition table tìm phân vùng FAT32 type 0x0B/0x0C, lưu LBA vào `partition_offset`. Mọi lần đọc sau đều cộng thêm offset này.

**[Khó] Q: Tại sao mask `& 0x0FFFFFFF` khi đọc FAT entry?**
FAT32 entry = 4 byte (32 bit) nhưng thực tế chỉ dùng 28 bit thấp để lưu cluster number. 4 bit cao là reserved. Mask loại bỏ 4 bit đó để tránh đọc nhầm giá trị.

---

### 7B. PHẦN SCHEDULER (bạn tui phụ trách)

**[Dễ] Q: Project có những thuật toán scheduling nào?**
SJF (Shortest Job First) và SRTN (Shortest Remaining Time Next). Cả hai đều chạy trong hệ thống Multi-Level Queue với Round Robin giữa các queue.

**[Dễ] Q: SJF và SRTN khác nhau điểm gì?**
SJF là non-preemptive: process chạy đến khi hết burst hoặc hết time slice mới dừng, không bị ngắt giữa chừng. SRTN là preemptive: process có thể bị ngắt nếu có process mới đến trong cùng queue với burst ngắn hơn.

**[Dễ] Q: Multi-Level Queue ở đây hoạt động thế nào?**
Có nhiều queue, mỗi queue có thuật toán riêng (SJF hoặc SRTN) và time slice riêng. CPU duyệt qua các queue theo Round Robin: chọn queue có process, chạy đến hết time slice, rồi chuyển sang queue tiếp theo.

**[Dễ] Q: Time slice là gì? Dùng ở đâu?**
Lượng thời gian tối đa mà 1 queue được dùng CPU trong 1 lượt. Khi hết time slice, dù process chưa xong cũng phải nhường cho queue khác.

**[Dễ] Q: Turnaround Time và Waiting Time tính thế nào?**
`Turnaround = Completion - Arrival`. `Waiting = Turnaround - Burst`.

**[Dễ] Q: Input file có format thế nào?**
Dòng 1: số queue N. N dòng tiếp: `QueueID TimeSlice Policy`. Các dòng còn lại: `PID Arrival Burst QueueID`.

**[Dễ] Q: Segment là gì?**
Mỗi lần 1 process chạy liên tục trên CPU được ghi lại là 1 Segment gồm: start, end, queue_id, pid. Dùng để vẽ CPU scheduling diagram.

**[Trung] Q: Khi CPU nhàn rỗi (không có process nào sẵn sàng) thì làm gì?**
Không idle theo từng đơn vị thời gian. Code nhảy thẳng thời gian đến arrival của process tiếp theo: `t = notArrived[0].arrival`. Gọi là "jump time" hay "fast forward".

**[Trung] Q: `pickNextQueue` hoạt động thế nào?**
Tìm queue tiếp theo (tính từ `queuePtr`) có ít nhất 1 process, duyệt theo vòng tròn. Đảm bảo Round Robin công bằng giữa các queue.

**[Trung] Q: Tie-breaking trong SJF và SRTN được xử lý thế nào?**
Khi 2 process có burst bằng nhau: ưu tiên theo arrival time trước, rồi theo seq (thứ tự xuất hiện trong file). Key so sánh: `(remaining, arrival, seq)`.

**[Trung] Q: Tại sao SRTN cần tham số `nextArrivalTime`?**
Để biết khi nào thì phải dừng lại nhường cho process mới đến trong cùng queue. SRTN giới hạn `dt = min(remaining, budget, nextArrivalTime - t)` để không chạy qua mốc có process mới.

**[Trung] Q: `registry.py` dùng pattern gì? Tại sao?**
Plugin/Registry pattern. Thay vì `if policy == "SJF": ... elif policy == "SRTN": ...` rải khắp code, tập trung vào 1 dict `_REGISTRY`. Thêm algorithm mới chỉ cần `register_policy("NEW", runner)`, không sửa code lõi.

**[Trung] Q: Tại sao `processes.sort(key=lambda p: (p.arrival, p.seq))` trong parser?**
Đảm bảo danh sách process được sắp xếp theo thứ tự đến. `notArrived` trong scheduler dựa vào thứ tự này để admit process đúng thời điểm (`notArrived[0].arrival` là arrival gần nhất).

**[Khó] Q: Tại sao tạo `fresh` Process trước khi chạy scheduling?**
`run_scheduling` thay đổi trực tiếp `remaining` và `completion` của từng Process object. Nếu dùng thẳng object gốc, lần sau mở DetailDialog lại thì remaining=0, completion đã set → kết quả sai. Fresh copy đảm bảo mỗi lần bắt đầu từ trạng thái ban đầu.

**[Khó] Q: SRTN chỉ preempt bởi process cùng queue hay khác queue?**
Chỉ cùng queue. `peek_next_arrival_time(notArrived, qId)` chỉ xét process có cùng `qId`. Process từ queue khác không gây preempt trong SRTN, chỉ Round Robin queue mới chuyển sang queue khác.

**[Khó] Q: SJF có bị giới hạn bởi time slice không? Tại sao?**
Có. `dt = min(p.remaining, budget)`. SJF chạy trong Multi-Level Queue nên phải tuân theo time slice của queue đó. Khi hết budget thì dừng, nhường cho queue khác theo Round Robin. Đây là SJF trong ngữ cảnh multi-level, không phải SJF thuần túy độc lập.
