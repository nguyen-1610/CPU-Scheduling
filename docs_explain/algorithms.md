# Giải thích thư mục `src/algorithms`

Tài liệu này giải thích toàn bộ phần trong thư mục [src/algorithms](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms), gồm:

- `roundRobin.py`
- `sjf.py`
- `srtn.py`
- `registry.py`

Mục tiêu của nhóm file này là cung cấp các thuật toán lập lịch dùng cho từng hàng đợi trong hệ thống Multi-Level Queue.

## Bức tranh tổng quát

Trong project này:

- `scheduler.py` là bộ điều phối chính của cả hệ thống
- `algorithms/` là nơi chứa logic chọn process trong từng hàng đợi

Luồng chung:

```text
scheduler.py
    |
    +-> pickNextQueue()      trong roundRobin.py
    +-> get_policy_runner()  trong registry.py
            |
            +-> sjf()        trong sjf.py
            +-> srtn()       trong srtn.py
```

## 1. `roundRobin.py`

File: [src/algorithms/roundRobin.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/roundRobin.py)

### Hàm `pickNextQueue(queuePtr, ready)`

Vị trí: [src/algorithms/roundRobin.py:5](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/roundRobin.py:5)

Code:

```python
def pickNextQueue(queuePtr: int, ready: Sequence[Sequence[Any]]) -> int:
    n = len(ready)
    if n == 0:
        raise ValueError("No queues configured")

    for k in range(n):
        q = (queuePtr + k) % n
        if len(ready[q]) > 0:
            return q

    raise ValueError("All queues are empty")
```

Giải thích:

- `queuePtr`
  Con trỏ hiện tại đang đứng ở hàng đợi nào.
- `ready`
  Danh sách các ready list tương ứng với từng queue.
- `n = len(ready)`
  Lấy số lượng queue.
- `if n == 0`
  Nếu không có queue nào thì báo lỗi.
- `for k in range(n)`
  Quét tối đa một vòng đầy đủ qua tất cả queue.
- `q = (queuePtr + k) % n`
  Quay vòng tròn từ `queuePtr`.
- `if len(ready[q]) > 0`
  Chọn queue đầu tiên còn process chờ.
- `raise ValueError("All queues are empty")`
  Nếu quét hết mà queue nào cũng rỗng thì báo lỗi.

Vai trò:

- Đây là phần Round Robin giữa các queue
- Nó không chọn process bên trong queue, nó chỉ chọn queue nào sẽ được phục vụ trước

## 2. `sjf.py`

File: [src/algorithms/sjf.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/sjf.py)

### Hàm `pop_sjf(ready)`

Vị trí: [src/algorithms/sjf.py:7](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/sjf.py:7)

Code chính:

```python
best_idx = 0
best_key = (ready[0].remaining, ready[0].arrival, ready[0].seq)
for i in range(1, len(ready)):
    key = (ready[i].remaining, ready[i].arrival, ready[i].seq)
    if key < best_key:
        best_key = key
        best_idx = i

return ready.pop(best_idx)
```

Giải thích:

- `best_idx = 0`
  Tạm xem process đầu tiên là tốt nhất.
- `best_key = (...)`
  Khóa so sánh gồm:
  `remaining`, rồi `arrival`, rồi `seq`.
- `for i in range(1, len(ready))`
  So sánh lần lượt các process còn lại.
- `if key < best_key`
  Nếu tìm được process có khóa nhỏ hơn thì cập nhật.
- `return ready.pop(best_idx)`
  Lấy process tốt nhất ra khỏi ready list.

Ý nghĩa:

- SJF ưu tiên process có thời gian chạy còn lại ngắn nhất
- Nếu hòa thì ưu tiên process đến sớm hơn
- Nếu vẫn hòa thì ưu tiên process xuất hiện sớm hơn trong input

### Hàm `sjf(queue_id, ready, t, budget, segments)`

Vị trí: [src/algorithms/sjf.py:23](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/sjf.py:23)

Luồng chính:

1. Nếu `budget <= 0` hoặc queue rỗng thì trả về ngay
2. Gọi `pop_sjf(ready)` để chọn process tốt nhất
3. Tính `dt = min(p.remaining, budget)`
4. Tạo `Segment(start, end, queue_id, pid)`
5. Cập nhật `p.remaining`
6. Nếu `remaining == 0` thì gán `completion`
7. Nếu chưa xong thì đưa process trở lại queue

Giải thích các dòng quan trọng:

- `dt = min(p.remaining, budget)`
  Process chỉ được chạy tối đa bằng phần còn lại của nó hoặc phần budget còn lại của queue.
- `segments.append(Segment(...))`
  Ghi lại đoạn CPU đã chạy để vẽ output và tính thống kê.
- `p.remaining -= dt`
  Giảm phần việc còn lại.
- `budget -= dt`
  Trừ thời lượng đã dùng khỏi budget của queue.
- `if p.remaining == 0`
  Nếu process xong thì ghi thời điểm hoàn thành.
- `else: ready.append(p)`
  Nếu chưa xong thì đưa trở lại queue.

Lưu ý:

- SJF ở đây là non-preemptive theo từng lần chọn process
- Nhưng do còn bị giới hạn bởi `budget` của queue, một process dài có thể bị dừng vì hết time slice của queue

## 3. `srtn.py`

File: [src/algorithms/srtn.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/srtn.py)

### Hàm `popSrtn(ready)`

Vị trí: [src/algorithms/srtn.py:5](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/srtn.py:5)

Hàm này gần giống `pop_sjf(...)`.

Khác biệt chính:

- Dùng cho SRTN, tức là mỗi lần chọn sẽ lấy process có `remaining` nhỏ nhất ở thời điểm hiện tại
- Vì SRTN là preemptive, việc chọn lại có thể xảy ra sau mỗi mốc arrival mới

### Hàm `srtn(queueId, ready, t, budget, segments, nextArrivalTime)`

Vị trí: [src/algorithms/srtn.py:21](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/srtn.py:21)

Điểm khác của SRTN so với SJF là có thêm `nextArrivalTime`.

Các dòng quan trọng:

- `dt = min(p.remaining, budget)`
  Ban đầu giới hạn bởi phần còn lại của process và budget của queue.
- `if nextArrivalTime is not None and nextArrivalTime > t:`
  Nếu sắp có process mới đến cùng queue, phải xét khả năng bị ngắt.
- `dt = min(dt, nextArrivalTime - t)`
  Chỉ cho process hiện tại chạy đến đúng mốc arrival tiếp theo.
- `if dt <= 0`
  Nếu thời lượng chạy bằng 0 thì trả process lại queue và thoát ra.
- `segments.append(Segment(...))`
  Ghi lại đoạn chạy CPU.
- `if p.remaining == 0`
  Nếu xong thì ghi `completion`.
- `else: ready.append(p)`
  Nếu chưa xong thì trả lại ready list để lần chọn sau có thể bị process khác vượt lên.

Ý nghĩa:

- SRTN luôn ưu tiên process có `remaining` nhỏ nhất
- Khi có process mới đến, scheduler có thể chọn lại process khác nếu process mới "ngắn hơn"

## 4. `registry.py`

File: [src/algorithms/registry.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/registry.py)

Registry là lớp trung gian để `scheduler.py` không phải gọi trực tiếp `sjf()` hoặc `srtn()` bằng `if/else` cứng.

### `PolicyRunner`

Vị trí: [src/algorithms/registry.py:10](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/registry.py:10)

Đây là kiểu hàm chuẩn mà mọi thuật toán phải tuân theo.

Ý nghĩa:

- Nếu sau này thêm policy mới, chỉ cần viết hàm đúng kiểu này rồi đăng ký vào registry

### Hàm `_run_sjf(...)`

Vị trí: [src/algorithms/registry.py:24](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/registry.py:24)

Nó chỉ gọi:

```python
return sjf(queue_id, ready, t, budget, segments)
```

Ý nghĩa:

- Bọc `sjf(...)` vào giao diện chung của registry
- Bỏ qua `next_arrival_time` vì SJF không cần

### Hàm `_run_srtn(...)`

Vị trí: [src/algorithms/registry.py:36](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/registry.py:36)

Nó gọi:

```python
return srtn(queue_id, ready, t, budget, segments, next_arrival_time)
```

Ý nghĩa:

- Bọc `srtn(...)` vào cùng giao diện chuẩn

### Biến `_REGISTRY`

Vị trí: [src/algorithms/registry.py:47](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/registry.py:47)

```python
_REGISTRY = {
    "SJF": _run_sjf,
    "SRTN": _run_srtn,
}
```

Ý nghĩa:

- Ánh xạ tên policy trong input sang hàm chạy thật

### Hàm `register_policy(name, runner)`

Vị trí: [src/algorithms/registry.py:53](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/registry.py:53)

Ý nghĩa:

- Cho phép đăng ký thuật toán mới mà không sửa lõi scheduler

### Hàm `get_policy_runner(name)`

Vị trí: [src/algorithms/registry.py:58](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/algorithms/registry.py:58)

Giải thích:

- Nhận tên policy
- Trả về hàm tương ứng trong registry
- Nếu không có thì báo lỗi `Unknown scheduling policy`

## Kết luận ngắn

- `roundRobin.py` chọn queue tiếp theo
- `sjf.py` chọn process ngắn nhất theo kiểu non-preemptive trong một lần chạy
- `srtn.py` chọn process ngắn nhất còn lại và có thể bị ngắt khi process mới đến
- `registry.py` nối tên policy với hàm chạy thật

Thư mục `algorithms/` là tầng chiến lược của hệ thống scheduling.
