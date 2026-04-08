# Giải thích `src/fat32/fat_table.py`

Tài liệu này giải thích file [src/fat32/fat_table.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py), là phần đọc bảng FAT và lần theo cluster chain.

## Vai trò của `fat_table.py`

Trong FAT32, nội dung của một file có thể nằm rải rác ở nhiều cluster khác nhau.

`fat_table.py` có nhiệm vụ:

- Đọc toàn bộ bảng FAT vào RAM
- Biết cluster nào nối sang cluster nào
- Trả về một cluster chain hoàn chỉnh
- Đọc toàn bộ bytes của một file hoặc thư mục theo cluster chain đó

Nói ngắn gọn:

`fat_table.py` là phần biến bảng FAT thành dữ liệu có thể dùng được.

## Hằng số trong lớp `FATTable`

Vị trí: [src/fat32/fat_table.py:18](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py:18)

```python
EOC = 0x0FFFFFF8
BAD = 0x0FFFFFF7
```

Giải thích:

- `EOC`
  End Of Chain, tức là cluster cuối cùng của một chuỗi.
- `BAD`
  Bad cluster, tức là cluster lỗi.

Ý nghĩa:

- Khi gặp `EOC` hoặc `BAD`, việc lần theo chain phải dừng lại.

## Hàm khởi tạo `__init__(...)`

Vị trí: [src/fat32/fat_table.py:21](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py:21)

Code:

```python
raw = reader.read_sectors(fat_start_lba, fat_size_sectors)

count = len(raw) // 4
self._entries: List[int] = [
    struct.unpack_from("<I", raw, i * 4)[0] & 0x0FFFFFFF
    for i in range(count)
]
```

Giải thích từng câu:

- `reader.read_sectors(fat_start_lba, fat_size_sectors)`
  Đọc toàn bộ bảng FAT từ đĩa vào `raw`.
- `count = len(raw) // 4`
  Mỗi entry FAT32 chiếm 4 byte, nên số entry bằng tổng số byte chia 4.
- `struct.unpack_from("<I", raw, i * 4)[0]`
  Lấy một số nguyên 4 byte tại vị trí `i * 4`.
- `& 0x0FFFFFFF`
  Chỉ giữ lại 28 bit thấp, vì FAT32 chỉ dùng phần này làm giá trị cluster tiếp theo.
- `self._entries = [...]`
  Lưu toàn bộ entry FAT vào bộ nhớ để truy cập nhanh.

Ý nghĩa:

- Sau bước này, chương trình không cần đọc bảng FAT từ đĩa lặp đi lặp lại
- Mọi lần tra cluster tiếp theo đều làm trên RAM

## Hàm `next_cluster(cluster)`

Vị trí: [src/fat32/fat_table.py:38](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py:38)

Code:

```python
if cluster < 2 or cluster >= len(self._entries):
    return None
val = self._entries[cluster]
if val >= self.EOC or val == self.BAD:
    return None
return val
```

Giải thích:

- `if cluster < 2`
  Cluster 0 và 1 không phải cluster dữ liệu hợp lệ.
- `cluster >= len(self._entries)`
  Nếu index vượt ngoài bảng FAT thì không hợp lệ.
- `val = self._entries[cluster]`
  Lấy giá trị entry tương ứng với cluster hiện tại.
- `if val >= self.EOC or val == self.BAD`
  Nếu gặp cuối chuỗi hoặc cluster lỗi thì dừng.
- `return val`
  Trả về cluster tiếp theo trong chain.

Ví dụ:

- FAT[5] = 8 thì `next_cluster(5)` trả `8`
- FAT[12] = EOC thì `next_cluster(12)` trả `None`

## Hàm `get_chain(start_cluster)`

Vị trí: [src/fat32/fat_table.py:50](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py:50)

Code:

```python
chain: List[int] = []
cur: Optional[int] = start_cluster
visited: set[int] = set()
while cur is not None and cur not in visited:
    chain.append(cur)
    visited.add(cur)
    cur = self.next_cluster(cur)
return chain
```

Giải thích từng câu:

- `chain = []`
  Danh sách kết quả các cluster trong chuỗi.
- `cur = start_cluster`
  Bắt đầu từ cluster đầu tiên của file.
- `visited = set()`
  Ghi lại những cluster đã đi qua để tránh vòng lặp vô hạn nếu FAT bị lỗi.
- `while cur is not None and cur not in visited`
  Tiếp tục lần theo chuỗi chừng nào còn cluster hợp lệ và chưa bị lặp.
- `chain.append(cur)`
  Ghi cluster hiện tại vào kết quả.
- `visited.add(cur)`
  Đánh dấu cluster này đã đi qua.
- `cur = self.next_cluster(cur)`
  Đi sang cluster tiếp theo.
- `return chain`
  Trả về toàn bộ chuỗi cluster.

Ví dụ:

Nếu FAT cho biết:

- `5 -> 8`
- `8 -> 12`
- `12 -> EOC`

thì:

```python
get_chain(5) == [5, 8, 12]
```

## Hàm `read_chain_data(...)`

Vị trí: [src/fat32/fat_table.py:61](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py:61)

Code:

```python
chain = self.get_chain(start_cluster)
bps = reader.bytes_per_sector
parts: List[bytes] = []
for cluster in chain:
    lba = data_start_lba + (cluster - 2) * sec_per_clus
    parts.append(reader.read_sectors(lba, sec_per_clus))
return b"".join(parts)
```

Giải thích từng câu:

- `chain = self.get_chain(start_cluster)`
  Lấy toàn bộ danh sách cluster của file hoặc thư mục.
- `bps = reader.bytes_per_sector`
  Lấy số byte mỗi sector.
  Trong code hiện tại biến này chưa được dùng tiếp, nhưng vẫn thể hiện ngữ cảnh đọc theo sector.
- `parts = []`
  Tạo danh sách để chứa bytes đọc từ từng cluster.
- `for cluster in chain`
  Duyệt từng cluster trong chuỗi.
- `lba = data_start_lba + (cluster - 2) * sec_per_clus`
  Tính sector bắt đầu của cluster hiện tại trong vùng Data.
- `reader.read_sectors(lba, sec_per_clus)`
  Đọc toàn bộ cluster hiện tại.
- `parts.append(...)`
  Ghi bytes của cluster đó vào danh sách.
- `return b"".join(parts)`
  Ghép toàn bộ bytes của các cluster lại thành một khối dữ liệu liên tục.

Ý nghĩa:

- Đây là bước quan trọng để lấy nội dung file `.txt` hoặc dữ liệu thư mục
- Dữ liệu đọc ra có thể dài hơn kích thước file thật, nên phía trên GUI còn phải cắt theo `file_size`

## Luồng sử dụng trong project

`FATTable` được dùng ở các chỗ chính sau:

- [src/gui/main_window.py:186](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/main_window.py:186)
  Tạo object `FATTable` sau khi đã có Boot Sector
- [src/fat32/directory.py:119](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/directory.py:119)
  Đọc dữ liệu thư mục theo cluster chain
- [src/gui/files_tab.py:92](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/files_tab.py:92)
  Đọc nội dung file `.txt` đã chọn
- [src/gui/main_window.py:204](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/main_window.py:204)
  Dùng `get_chain(...)` để tính `RDETSectors`

## Kết luận ngắn

`fat_table.py` làm 3 việc cốt lõi:

1. Đọc bảng FAT vào RAM
2. Lần theo chuỗi cluster của file hoặc thư mục
3. Ghép bytes của toàn bộ chain thành dữ liệu hoàn chỉnh

Nếu `reader.py` là phần đọc sector thô, thì `fat_table.py` là phần hiểu được "đi tiếp cluster nào".
