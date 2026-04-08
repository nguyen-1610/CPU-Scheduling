# Giải Thích Logic `src/io/parser.py`

Tài liệu này giải thích file [src/io/parser.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py) theo từng hàm, kèm ví dụ đầu vào/đầu ra và liệt kê những chỗ đang sử dụng parser trong project.

## Mục đích của `parser.py`

`parser.py` dùng để chuyển nội dung input Lab 01 thành 2 cấu trúc dữ liệu:

- `List[QueueConfig]`
- `List[Process]`

Nó không đọc FAT32, không duyệt cluster, không đọc directory entry. Nhiệm vụ của nó chỉ là:

1. Nhận dữ liệu đã có sẵn dưới dạng `str` hoặc `bytes`
2. Tách từng dòng
3. Kiểm tra format có hợp lệ không
4. Tạo object `QueueConfig` và `Process`

## Định dạng input mà parser mong đợi

Ví dụ input hợp lệ:

```txt
3
Q1 5 SJF
Q2 10 SRTN
Q3 8 SJF

P1 0 12 Q1
P2 2 4 Q2
P3 3 8 Q1
P4 5 15 Q3
```

Ý nghĩa:

- Dòng 1: số lượng queue `N`
- `N` dòng tiếp theo: `QueueID TimeSlice Policy`
- Các dòng còn lại: `PID Arrival Burst QueueID`

## Các hàm trong `parser.py`

### 1. `_normalize_lines(lines)`

Vị trí: [src/io/parser.py:8](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:8)

Vai trò:

- Loại bỏ khoảng trắng đầu/cuối mỗi dòng
- Bỏ qua dòng rỗng
- Bỏ qua dòng comment bắt đầu bằng `#`

Đầu vào:

```python
[
    "3\n",
    "Q1 5 SJF\n",
    "\n",
    "# comment\n",
    "P1 0 12 Q1\n",
]
```

Đầu ra:

```python
[
    "3",
    "Q1 5 SJF",
    "P1 0 12 Q1",
]
```

Ý nghĩa logic:

- Hàm này giúp parser ở các bước sau chỉ làm việc với dữ liệu "sạch"
- Nếu file có dòng trống hoặc comment, parser vẫn chạy ổn định

#### Giải thích từng câu code

Code:

```python
def _normalize_lines(lines: Iterable[str]) -> List[str]:
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]
```

Giải thích:

- `def _normalize_lines(...):`
  Hàm này là hàm phụ trợ nội bộ, dùng để chuẩn hóa danh sách dòng trước khi parse.
- `lines: Iterable[str]`
  Tham số `lines` là một tập các chuỗi, có thể là `list`, `generator`, hoặc kết quả từ `splitlines()`.
- `-> List[str]`
  Hàm trả về một danh sách chuỗi đã được làm sạch.
- `ln.strip()`
  Xóa khoảng trắng ở đầu và cuối mỗi dòng.
- `if ln.strip()`
  Chỉ giữ lại dòng không rỗng sau khi đã xóa khoảng trắng.
- `and not ln.strip().startswith("#")`
  Bỏ qua các dòng comment bắt đầu bằng `#`.
- `return [...]`
  Trả về toàn bộ danh sách dòng hợp lệ sau khi xử lý.

### 2. `_parse_lines(lines)`

Vị trí: [src/io/parser.py:12](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:12)

Đây là hàm xử lý logic chính.

Nhiệm vụ:

1. Kiểm tra file có rỗng không
2. Đọc dòng đầu tiên để lấy `N`
3. Đọc `N` dòng queue
4. Kiểm tra từng queue có đúng format không
5. Đọc danh sách process
6. Kiểm tra process có hợp lệ không
7. Tạo object `QueueConfig` và `Process`
8. Sắp xếp process theo `arrival`, nếu bằng nhau thì theo `seq`

#### 2.1 Kiểm tra dòng đầu tiên

Đoạn này nằm ở [src/io/parser.py:13](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:13) đến [src/io/parser.py:25](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:25).

Nó kiểm tra:

- Input rỗng
- Dòng 1 có phải số nguyên không
- `N > 0`
- Số dòng có đủ cho phần queue không

Nếu sai, hàm `raise ValueError`.

Ví dụ lỗi:

```txt
abc
Q1 5 SJF
P1 0 12 Q1
```

Kết quả:

```python
ValueError("Line 1 must be an integer N (number of queues).")
```

#### Giải thích từng câu code trong phần đầu hàm

Code:

```python
def _parse_lines(lines: List[str]) -> Tuple[List[QueueConfig], List[Process]]:
    if not lines:
        raise ValueError("Input file is empty!")

    try:
        n = int(lines[0])
    except ValueError as exc:
        raise ValueError("Line 1 must be an integer N (number of queues).") from exc

    if n <= 0:
        raise ValueError("N must be > 0.")

    if len(lines) < 1 + n:
        raise ValueError("Not enough lines for queue configurations.")
```

Giải thích:

- `def _parse_lines(...):`
  Đây là hàm xử lý chính của parser.
- `lines: List[str]`
  Đầu vào là danh sách dòng đã được chuẩn hóa.
- `if not lines:`
  Kiểm tra xem danh sách có rỗng không.
- `raise ValueError("Input file is empty!")`
  Nếu rỗng thì báo lỗi ngay, không parse tiếp.
- `n = int(lines[0])`
  Lấy dòng đầu tiên và ép kiểu sang số nguyên để biết có bao nhiêu queue.
- `except ValueError as exc:`
  Nếu dòng đầu không chuyển được sang số nguyên thì bắt lỗi.
- `raise ValueError(...) from exc`
  Phát sinh lỗi mới với thông báo dễ hiểu hơn.
- `if n <= 0:`
  Đảm bảo số queue phải lớn hơn 0.
- `if len(lines) < 1 + n:`
  Kiểm tra file có đủ số dòng để chứa phần cấu hình queue hay không.

#### 2.2 Parse queue

Đoạn này nằm ở [src/io/parser.py:27](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:27) đến [src/io/parser.py:47](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:47).

Mỗi dòng queue phải có 3 thành phần:

```txt
Q1 5 SJF
```

Nó sẽ tách ra:

- `qid = "Q1"`
- `ts = 5`
- `policy = "SJF"`

Nó kiểm tra:

- Có đúng 3 token không
- `time_slice` có phải số nguyên không
- `time_slice > 0`
- `policy` chỉ được là `SJF` hoặc `SRTN`

Đầu ra của bước này:

```python
[
    QueueConfig(queue_id="Q1", time_slice=5, policy="SJF"),
    QueueConfig(queue_id="Q2", time_slice=10, policy="SRTN"),
]
```

#### Giải thích từng câu code trong phần parse queue

Code:

```python
queues: List[QueueConfig] = []
for i in range(1, 1 + n):
    parts = lines[i].split()
    if len(parts) != 3:
        raise ValueError(f"Queue config line {i + 1} must have 3 tokens: QID TimeSlice Policy")

    qid, ts_str, policy = parts
    try:
        ts = int(ts_str)
    except ValueError as exc:
        raise ValueError(f"Queue config line {i + 1}: time_slice must be an integer.") from exc

    if ts <= 0:
        raise ValueError(f"Queue config line {i + 1}: time_slice must be > 0 (got {ts}).")

    if policy not in ("SJF", "SRTN"):
        raise ValueError(f"Invalid policy '{policy}' in line {i + 1}. Must be SJF or SRTN.")

    queues.append(QueueConfig(queue_id=qid, time_slice=ts, policy=policy))
```

Giải thích:

- `queues: List[QueueConfig] = []`
  Tạo danh sách rỗng để chứa các queue sau khi parse.
- `for i in range(1, 1 + n):`
  Duyệt từ dòng thứ 2 đến hết phần queue.
- `parts = lines[i].split()`
  Tách dòng hiện tại thành các token theo khoảng trắng.
- `if len(parts) != 3:`
  Mỗi dòng queue bắt buộc phải có đúng 3 phần.
- `qid, ts_str, policy = parts`
  Gán 3 token vào 3 biến.
- `ts = int(ts_str)`
  Chuyển `time_slice` từ chuỗi sang số nguyên.
- `if ts <= 0:`
  Kiểm tra `time_slice` phải dương.
- `if policy not in ("SJF", "SRTN"):`
  Chỉ chấp nhận 2 thuật toán mà đề bài yêu cầu.
- `queues.append(...)`
  Tạo object `QueueConfig` rồi thêm vào danh sách `queues`.

#### 2.3 Parse process

Đoạn này nằm ở [src/io/parser.py:49](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:49) đến [src/io/parser.py:82](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:82).

Mỗi dòng process phải có 4 thành phần:

```txt
P1 0 12 Q1
```

Nó tách ra:

- `pid = "P1"`
- `arrival = 0`
- `burst = 12`
- `qid = "Q1"`

Nó kiểm tra:

- Có đúng 4 token không
- `arrival` và `burst` có phải số nguyên không
- `arrival >= 0`
- `burst > 0`
- `qid` có tồn tại trong danh sách queue đã đọc ở trên không

Mỗi process tạo ra thêm trường `seq` để giữ thứ tự gốc trong file.

Ví dụ đầu ra:

```python
[
    Process(pid="P1", arrival=0, burst=12, queue_id="Q1", seq=0),
    Process(pid="P2", arrival=2, burst=4, queue_id="Q2", seq=1),
]
```

#### Giải thích từng câu code trong phần parse process

Code:

```python
queue_ids = {q.queue_id for q in queues}

processes: List[Process] = []
seq = 0
for i in range(1 + n, len(lines)):
    parts = lines[i].split()
    if len(parts) != 4:
        raise ValueError(f"Process line {i + 1} must have 4 tokens: PID Arrival Burst QueueID")

    pid, arr_str, burst_str, qid = parts
    try:
        arrival = int(arr_str)
        burst = int(burst_str)
    except ValueError as exc:
        raise ValueError(
            f"Process line {i + 1}: arrival and burst must be integers."
        ) from exc

    if arrival < 0:
        raise ValueError(f"Process {pid} (line {i + 1}): arrival time must be >= 0 (got {arrival}).")

    if burst <= 0:
        raise ValueError(f"Process {pid} (line {i + 1}): burst time must be > 0 (got {burst}).")

    if qid not in queue_ids:
        raise ValueError(f"Process {pid} references unknown queue '{qid}' (line {i + 1}).")

    processes.append(Process(pid=pid, arrival=arrival, burst=burst, queue_id=qid, seq=seq))
    seq += 1
```

Giải thích:

- `queue_ids = {q.queue_id for q in queues}`
  Tạo một tập hợp chứa tất cả `queue_id` hợp lệ để kiểm tra nhanh process có tham chiếu đúng queue hay không.
- `processes: List[Process] = []`
  Tạo danh sách rỗng để chứa các process.
- `seq = 0`
  Biến `seq` dùng để lưu thứ tự gốc của process trong file.
- `for i in range(1 + n, len(lines)):`
  Bắt đầu duyệt từ dòng đầu tiên của phần process.
- `parts = lines[i].split()`
  Tách dòng thành các token.
- `if len(parts) != 4:`
  Mỗi dòng process phải có đúng 4 phần.
- `pid, arr_str, burst_str, qid = parts`
  Gán các token vào các biến tương ứng.
- `arrival = int(arr_str)` và `burst = int(burst_str)`
  Chuyển thời gian đến và burst time sang số nguyên.
- `if arrival < 0:`
  Thời gian đến không được âm.
- `if burst <= 0:`
  Burst time phải lớn hơn 0.
- `if qid not in queue_ids:`
  Queue mà process tham chiếu phải tồn tại trong phần queue đã parse ở trên.
- `processes.append(Process(...))`
  Tạo object `Process` rồi thêm vào danh sách.
- `seq += 1`
  Tăng thứ tự để process tiếp theo có `seq` lớn hơn.

#### 2.4 Sắp xếp process

Đoạn này nằm ở [src/io/parser.py:82](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:82).

Lệnh:

```python
processes.sort(key=lambda p: (p.arrival, p.seq))
```

Ý nghĩa:

- Process đến sớm hơn sẽ đứng trước
- Nếu đến cùng lúc thì giữ thứ tự xuất hiện ban đầu trong file

#### Giải thích từng câu code trong phần cuối hàm

Code:

```python
if not processes:
    import warnings

    warnings.warn("Input file has queue configurations but no processes defined.", UserWarning)

processes.sort(key=lambda p: (p.arrival, p.seq))
return queues, processes
```

Giải thích:

- `if not processes:`
  Kiểm tra xem file có queue nhưng không có process nào hay không.
- `import warnings`
  Import module cảnh báo của Python.
- `warnings.warn(...)`
  Không dừng chương trình, chỉ phát cảnh báo để báo rằng input không có process.
- `processes.sort(key=lambda p: (p.arrival, p.seq))`
  Sắp xếp process theo `arrival`, nếu trùng thì theo `seq`.
- `return queues, processes`
  Trả về kết quả cuối cùng cho các hàm gọi bên ngoài.

### 3. `parse_input_text(text)`

Vị trí: [src/io/parser.py:86](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:86)

Vai trò:

- Nhận một chuỗi text
- Tách text thành từng dòng bằng `splitlines()`
- Đưa qua `_normalize_lines(...)`
- Sau đó đưa qua `_parse_lines(...)`

Luồng gọi:

```python
text -> splitlines() -> _normalize_lines(...) -> _parse_lines(...)
```

Ví dụ:

Đầu vào:

```python
text = "2\nQ1 5 SJF\nQ2 10 SRTN\nP1 0 6 Q1\nP2 1 4 Q2\n"
```

Đầu ra:

```python
(queues, processes)
```

Trong đó:

```python
queues == [
    QueueConfig(queue_id="Q1", time_slice=5, policy="SJF"),
    QueueConfig(queue_id="Q2", time_slice=10, policy="SRTN"),
]
```

```python
processes == [
    Process(pid="P1", arrival=0, burst=6, queue_id="Q1", seq=0),
    Process(pid="P2", arrival=1, burst=4, queue_id="Q2", seq=1),
]
```

#### Giải thích từng câu code

Code:

```python
def parse_input_text(text: str) -> Tuple[List[QueueConfig], List[Process]]:
    return _parse_lines(_normalize_lines(text.splitlines()))
```

Giải thích:

- `def parse_input_text(text: str)`
  Đây là hàm public dùng khi đầu vào đang ở dạng chuỗi.
- `text.splitlines()`
  Tách toàn bộ chuỗi thành từng dòng.
- `_normalize_lines(...)`
  Làm sạch các dòng: bỏ dòng rỗng, comment, khoảng trắng thừa.
- `_parse_lines(...)`
  Phân tích logic nội dung sau khi đã được chuẩn hóa.
- `return ...`
  Trả về trực tiếp kết quả parse.

### 4. `parse_input_bytes(raw_bytes, encoding="utf-8-sig")`

Vị trí: [src/io/parser.py:90](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:90)

Vai trò:

- Nhận dữ liệu dạng `bytes`
- Giải mã thành `text`
- Gọi tiếp `parse_input_text(text)`

Luồng gọi:

```python
raw_bytes -> decode(...) -> parse_input_text(...) -> _parse_lines(...)
```

Đây là hàm phù hợp hơn cho Lab 2, vì file `.txt` đã được đọc từ FAT32 thành `bytes` trước đó.

Ví dụ:

Đầu vào:

```python
raw_bytes = b"2\nQ1 5 SJF\nQ2 10 SRTN\nP1 0 6 Q1\nP2 1 4 Q2\n"
```

Đầu ra:

```python
(
    [
        QueueConfig(queue_id="Q1", time_slice=5, policy="SJF"),
        QueueConfig(queue_id="Q2", time_slice=10, policy="SRTN"),
    ],
    [
        Process(pid="P1", arrival=0, burst=6, queue_id="Q1", seq=0),
        Process(pid="P2", arrival=1, burst=4, queue_id="Q2", seq=1),
    ],
)
```

Nếu bytes không decode được:

```python
ValueError("Unable to decode input bytes with utf-8-sig: ...")
```

#### Giải thích từng câu code

Code:

```python
def parse_input_bytes(raw_bytes: bytes, encoding: str = "utf-8-sig") -> Tuple[List[QueueConfig], List[Process]]:
    try:
        text = raw_bytes.decode(encoding)
    except UnicodeDecodeError as exc:
        raise ValueError(f"Unable to decode input bytes with {encoding}: {exc}") from exc

    return parse_input_text(text)
```

Giải thích:

- `def parse_input_bytes(raw_bytes: bytes, encoding: str = "utf-8-sig")`
  Đây là hàm public dùng khi đầu vào đang ở dạng bytes.
- `encoding: str = "utf-8-sig"`
  Mặc định decode theo `utf-8-sig`, giúp xử lý cả trường hợp file có BOM.
- `text = raw_bytes.decode(encoding)`
  Chuyển bytes thành chuỗi.
- `except UnicodeDecodeError as exc:`
  Nếu dữ liệu bytes không decode được thì bắt lỗi.
- `raise ValueError(...) from exc`
  Chuyển lỗi decode kỹ thuật thành thông báo parser dễ hiểu hơn.
- `return parse_input_text(text)`
  Sau khi đã có text, tiếp tục dùng luồng parse chuẩn của hàm `parse_input_text(...)`.

## Đầu vào và đầu ra tổng quát của parser

### Đầu vào

Parser có 2 kiểu đầu vào hợp lệ:

- `str` qua `parse_input_text(text)`
- `bytes` qua `parse_input_bytes(raw_bytes)`

### Đầu ra

Cả hai hàm đều trả về:

```python
Tuple[List[QueueConfig], List[Process]]
```

Cụ thể:

```python
(
    [QueueConfig(...), QueueConfig(...), ...],
    [Process(...), Process(...), ...]
)
```

## Những chỗ đang sử dụng parser trong project

Hiện tại parser đang được dùng ở 2 nơi:

### 1. `src/main.py`

Vị trí: [src/main.py:31](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/main.py:31)

Cách dùng:

```python
with open(input_path, "rb") as f:
    queues, processes = parse_input_bytes(f.read())
```

Ý nghĩa:

- Đây là luồng CLI của Lab 1
- File được đọc từ ổ đĩa bình thường
- Sau đó bytes được đưa vào parser

### 2. `src/gui/detail_dialog.py`

Vị trí: [src/gui/detail_dialog.py:124](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/detail_dialog.py:124)

Cách dùng:

```python
queues, processes = parse_input_bytes(raw_content)
```

Ý nghĩa:

- `raw_content` đã được đọc từ FAT32 trước đó
- Parser chỉ nhận bytes và chuyển thành object
- Đây là luồng phù hợp với Lab 2 hơn

## Những gì `parser.py` không làm

Để tránh nhầm, `parser.py` không làm các việc sau:

- Không đọc boot sector
- Không đọc FAT table
- Không duyệt directory
- Không theo cluster chain
- Không đọc từng sector từ USB
- Không tự tìm file `.txt`

Những việc đó nằm ở:

- [src/fat32/reader.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/reader.py)
- [src/fat32/fat_table.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/fat_table.py)
- [src/fat32/directory.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/fat32/directory.py)
- [src/gui/files_tab.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/files_tab.py)

## Đánh giá theo rule đồ án

Nếu xét riêng `parser.py`:

- Nó không còn tự `open()` file bằng đường dẫn nữa
- Nó nhận `bytes` hoặc `text` đã được chuẩn bị sẵn
- Nó là parser format Lab 01, không phải bộ đọc FAT32

Nếu thầy yêu cầu "phần parser phải đọc FAT32 từng byte" thì parser này không phải nơi làm việc đó. Việc đọc byte FAT32 nằm ở các file trong thư mục `src/fat32/`.

## Tóm tắt ngắn

- `_normalize_lines(...)`: làm sạch dữ liệu dòng
- `_parse_lines(...)`: parse và kiểm tra toàn bộ nội dung
- `parse_input_text(...)`: parser cho dữ liệu dạng chuỗi
- `parse_input_bytes(...)`: parser cho dữ liệu dạng bytes
- Nơi đang dùng parser: [src/main.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/main.py) và [src/gui/detail_dialog.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/detail_dialog.py)
