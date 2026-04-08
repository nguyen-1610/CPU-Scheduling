# Giải thích `src/io/parser.py`

Tài liệu này giải thích file [src/io/parser.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py) theo từng hàm, từng đoạn code chính, ví dụ đầu vào/đầu ra và nơi đang sử dụng trong project.

## Mục đích

`parser.py` có nhiệm vụ chuyển dữ liệu input của Lab 1 từ `text` hoặc `bytes` thành:

- `List[QueueConfig]`
- `List[Process]`

Nó không đọc FAT32, không duyệt cluster, không tự tìm file. Nó chỉ làm phần parse format.

## Định dạng input mong đợi

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

## Hàm `_normalize_lines(lines)`

Vị trí: [src/io/parser.py:8](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:8)

Code:

```python
def _normalize_lines(lines: Iterable[str]) -> List[str]:
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]
```

Giải thích từng câu:

- `lines: Iterable[str]`
  Hàm nhận vào một tập các dòng văn bản.
- `ln.strip()`
  Xóa khoảng trắng đầu/cuối dòng.
- `if ln.strip()`
  Chỉ giữ lại dòng không rỗng.
- `not ln.strip().startswith("#")`
  Bỏ qua dòng comment.
- `return [...]`
  Trả về danh sách dòng đã làm sạch.

Ví dụ:

Đầu vào:

```python
["3\n", "\n", "# ghi chú\n", "Q1 5 SJF\n"]
```

Đầu ra:

```python
["3", "Q1 5 SJF"]
```

## Hàm `_parse_lines(lines)`

Vị trí: [src/io/parser.py:12](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:12)

Đây là hàm xử lý chính.

### Phần 1. Kiểm tra dòng đầu và số lượng queue

Code:

```python
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

- `if not lines`
  Nếu file không có dữ liệu hợp lệ thì báo lỗi.
- `n = int(lines[0])`
  Đọc số lượng queue từ dòng đầu.
- `except ValueError`
  Nếu dòng đầu không phải số nguyên thì báo lỗi rõ ràng.
- `if n <= 0`
  Số queue phải lớn hơn 0.
- `if len(lines) < 1 + n`
  Phải có đủ số dòng để chứa phần queue.

### Phần 2. Parse danh sách queue

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

- `queues = []`
  Tạo danh sách để chứa các queue sau khi parse.
- `for i in range(1, 1 + n)`
  Duyệt qua `N` dòng queue.
- `parts = lines[i].split()`
  Tách dòng thành các token.
- `if len(parts) != 3`
  Mỗi queue phải có đúng 3 trường.
- `qid, ts_str, policy = parts`
  Gán lần lượt mã queue, time slice, policy.
- `ts = int(ts_str)`
  Chuyển time slice sang số nguyên.
- `if ts <= 0`
  Time slice phải dương.
- `if policy not in ("SJF", "SRTN")`
  Chỉ chấp nhận 2 policy hợp lệ.
- `queues.append(...)`
  Tạo object `QueueConfig` rồi thêm vào danh sách.

Ví dụ đầu ra của phần này:

```python
[
    QueueConfig(queue_id="Q1", time_slice=5, policy="SJF"),
    QueueConfig(queue_id="Q2", time_slice=10, policy="SRTN"),
]
```

### Phần 3. Parse danh sách process

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
  Tạo tập hợp các queue hợp lệ để kiểm tra nhanh.
- `processes = []`
  Tạo danh sách process rỗng.
- `seq = 0`
  Biến giữ thứ tự gốc trong file.
- `for i in range(1 + n, len(lines))`
  Duyệt tất cả các dòng process.
- `if len(parts) != 4`
  Mỗi process phải có đúng 4 trường.
- `pid, arr_str, burst_str, qid = parts`
  Gán từng trường cho các biến.
- `arrival = int(arr_str)` và `burst = int(burst_str)`
  Chuyển arrival và burst sang số nguyên.
- `if arrival < 0`
  Arrival không được âm.
- `if burst <= 0`
  Burst phải lớn hơn 0.
- `if qid not in queue_ids`
  Process phải tham chiếu đến queue có tồn tại.
- `processes.append(Process(...))`
  Tạo object `Process`.
- `seq += 1`
  Tăng số thứ tự để giữ tie-break ổn định.

Ví dụ đầu ra:

```python
[
    Process(pid="P1", arrival=0, burst=12, queue_id="Q1", seq=0),
    Process(pid="P2", arrival=2, burst=4, queue_id="Q2", seq=1),
]
```

### Phần 4. Cảnh báo và sắp xếp

Code:

```python
if not processes:
    import warnings
    warnings.warn("Input file has queue configurations but no processes defined.", UserWarning)

processes.sort(key=lambda p: (p.arrival, p.seq))
return queues, processes
```

Giải thích:

- `if not processes`
  Nếu file có queue nhưng không có process nào thì phát cảnh báo.
- `warnings.warn(...)`
  Cảnh báo chứ không dừng chương trình.
- `processes.sort(key=lambda p: (p.arrival, p.seq))`
  Sắp xếp process theo arrival, nếu bằng nhau thì theo seq.
- `return queues, processes`
  Trả kết quả cuối cùng.

## Hàm `parse_input_text(text)`

Vị trí: [src/io/parser.py:86](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:86)

Code:

```python
def parse_input_text(text: str) -> Tuple[List[QueueConfig], List[Process]]:
    return _parse_lines(_normalize_lines(text.splitlines()))
```

Giải thích:

- `text.splitlines()`
  Tách chuỗi thành các dòng.
- `_normalize_lines(...)`
  Làm sạch danh sách dòng.
- `_parse_lines(...)`
  Parse logic chính.
- Hàm này phù hợp khi dữ liệu đầu vào đã ở dạng chuỗi.

## Hàm `parse_input_bytes(raw_bytes, encoding="utf-8-sig")`

Vị trí: [src/io/parser.py:90](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/io/parser.py:90)

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

- `raw_bytes: bytes`
  Đầu vào là dữ liệu nhị phân.
- `encoding="utf-8-sig"`
  Mặc định decode bằng `utf-8-sig`, hỗ trợ cả BOM.
- `text = raw_bytes.decode(encoding)`
  Chuyển bytes thành chuỗi.
- `except UnicodeDecodeError`
  Nếu không decode được thì báo lỗi dễ hiểu.
- `return parse_input_text(text)`
  Sau khi đã có text thì chuyển qua luồng parse thông thường.

## Nơi đang sử dụng parser

Hiện tại parser được gọi ở 2 nơi:

- [src/main.py:31](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/main.py:31)
  CLI Lab 1 đọc bytes từ file input local rồi gọi `parse_input_bytes(...)`
- [src/gui/detail_dialog.py:124](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/gui/detail_dialog.py:124)
  GUI Lab 2 nhận `raw_content` từ FAT32 rồi gọi `parse_input_bytes(...)`

## Kết luận ngắn

- `parser.py` chỉ làm nhiệm vụ parse format
- Không còn tự `open()` file trong chính file parser
- Luồng Lab 2 đang dùng parser đúng kiểu: đọc dữ liệu thành `bytes` trước, rồi mới parse
