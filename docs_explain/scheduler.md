# Giải thích `src/controller/scheduler.py`

Tài liệu này giải thích file [src/controller/scheduler.py](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/controller/scheduler.py), là bộ điều phối trung tâm của toàn bộ hệ thống scheduling.

## Vai trò của `scheduler.py`

Nếu `algorithms/` là nơi chứa chiến lược chọn process trong từng queue, thì `scheduler.py` là nơi:

- Quản lý thời gian hệ thống `t`
- Quản lý danh sách process chưa đến và đã sẵn sàng
- Chọn queue nào được chạy tiếp theo
- Gọi đúng thuật toán của queue đó
- Thu thập `segments` và cập nhật `completion`

Nói ngắn gọn:

`scheduler.py` là "bộ não điều phối" của cả hệ thống.

## Hàm `admit_new_processes(...)`

Vị trí: [src/controller/scheduler.py:10](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/controller/scheduler.py:10)

Code:

```python
while notArrived and notArrived[0].arrival <= t:
    p = notArrived.pop(0)
    qi = queueIndex[p.queue_id]
    readyLists[qi].append(p)
```

Giải thích:

- `notArrived`
  Danh sách process chưa đến hệ thống.
- `while notArrived and notArrived[0].arrival <= t`
  Chừng nào còn process và process đầu tiên đã đến trước hoặc đúng thời điểm `t`, thì đưa nó vào ready list.
- `p = notArrived.pop(0)`
  Lấy process đầu tiên ra khỏi danh sách chưa đến.
- `qi = queueIndex[p.queue_id]`
  Tìm index của queue mà process này thuộc về.
- `readyLists[qi].append(p)`
  Đưa process vào ready list tương ứng.

Vai trò:

- Chuyển process từ trạng thái "chưa đến" sang trạng thái "sẵn sàng"

## Hàm `is_system_idle(...)`

Vị trí: [src/controller/scheduler.py:23](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/controller/scheduler.py:23)

Code:

```python
return all(len(lst) == 0 for lst in readyLists)
```

Giải thích:

- Kiểm tra tất cả queue có rỗng không
- Nếu tất cả đều rỗng thì CPU đang idle

## Hàm `peek_next_arrival_time(...)`

Vị trí: [src/controller/scheduler.py:27](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/controller/scheduler.py:27)

Code:

```python
for p in notArrived:
    if p.queue_id == queueId:
        return p.arrival
return None
```

Giải thích:

- Duyệt danh sách process chưa đến
- Tìm process đầu tiên thuộc đúng queue đang xét
- Trả về thời điểm process đó sẽ đến
- Nếu không có thì trả `None`

Vai trò:

- Chủ yếu dùng cho SRTN để biết khi nào có process mới cùng queue đến và có thể gây preempt

## Hàm `run_scheduling(...)`

Vị trí: [src/controller/scheduler.py:35](/Users/danhtruongnguyenthanh/Desktop/CPU-Scheduling/src/controller/scheduler.py:35)

Đây là hàm quan trọng nhất.

### Phần 1. Khởi tạo

Code:

```python
if not queues:
    return [], processes

queueIndex = {q.queue_id: i for i, q in enumerate(queues)}

t = 0
queuePtr = 0
segments: List[Segment] = []

notArrived = list(processes)
readyLists: List[List[Process]] = [[] for _ in queues]

total = len(processes)
finishedCount = 0
```

Giải thích:

- `if not queues`
  Nếu không có queue nào thì không thể lập lịch.
- `queueIndex = {...}`
  Tạo bảng tra nhanh từ `queue_id` sang vị trí trong `readyLists`.
- `t = 0`
  Thời gian hệ thống bắt đầu từ 0.
- `queuePtr = 0`
  Con trỏ Round Robin bắt đầu từ queue đầu tiên.
- `segments = []`
  Danh sách đoạn chạy CPU.
- `notArrived = list(processes)`
  Sao chép danh sách process chưa đến.
- `readyLists = [[] for _ in queues]`
  Tạo một ready list cho mỗi queue.
- `total`
  Tổng số process.
- `finishedCount`
  Đếm số process đã hoàn thành.

### Phần 2. Vòng lặp chính

Code:

```python
while finishedCount < total:
    admit_new_processes(t, notArrived, readyLists, queueIndex)
```

Giải thích:

- Vòng lặp tiếp tục cho đến khi tất cả process hoàn thành
- Ở mỗi vòng, phải admit các process đã đến

### Phần 3. Xử lý CPU idle

Code:

```python
if is_system_idle(readyLists):
    if not notArrived:
        break
    t = notArrived[0].arrival
    continue
```

Giải thích:

- Nếu tất cả ready list đều rỗng, CPU đang nhàn rỗi
- Nếu cũng không còn process chưa đến thì thoát luôn
- Nếu vẫn còn process chưa đến, nhảy thẳng thời gian `t` đến mốc arrival tiếp theo

Ý nghĩa:

- Tránh việc tăng thời gian từng đơn vị vô ích
- Đây là kỹ thuật "jump time"

### Phần 4. Chọn queue cần chạy

Code:

```python
qIdx = pickNextQueue(queuePtr, readyLists)
qConf = queues[qIdx]
qId = qConf.queue_id
budget = qConf.time_slice
policyName = qConf.policy
policyRunner = get_policy_runner(policyName)
```

Giải thích:

- `pickNextQueue(...)`
  Chọn queue tiếp theo theo Round Robin giữa các queue.
- `qConf = queues[qIdx]`
  Lấy cấu hình của queue đó.
- `budget = qConf.time_slice`
  Budget là lượng thời gian queue này được dùng trong lượt hiện tại.
- `policyName = qConf.policy`
  Tên thuật toán bên trong queue.
- `policyRunner = get_policy_runner(policyName)`
  Lấy hàm chạy thật tương ứng với policy.

### Phần 5. Vòng lặp xử lý bên trong một queue

Code:

```python
while budget > 0 and len(readyLists[qIdx]) > 0:
```

Giải thích:

- Chừng nào queue hiện tại còn budget và còn process thì tiếp tục phục vụ queue này

### Phần 6. Tìm thời điểm arrival tiếp theo cùng queue

Code:

```python
nextArrivalTime = peek_next_arrival_time(notArrived, qId)
```

Giải thích:

- Tìm xem còn process nào sắp đến thuộc đúng queue hiện tại hay không
- Thông tin này quan trọng với SRTN

### Phần 7. Guard riêng cho SRTN

Code:

```python
if policyName == "SRTN":
    if nextArrivalTime is not None and nextArrivalTime == t:
        prev_len = len(notArrived)
        admit_new_processes(t, notArrived, readyLists, queueIndex)
        if len(notArrived) < prev_len:
            continue
```

Giải thích:

- Nếu đang dùng SRTN và đúng thời điểm này có process mới cùng queue đến
- Thì phải admit process mới trước khi ra quyết định chọn process chạy
- `prev_len` dùng để kiểm tra xem có process nào thực sự vừa được nạp vào không
- Nếu có, `continue` để quay lại đầu vòng lặp và chọn lại process theo trạng thái ready mới

Ý nghĩa:

- Giúp SRTN đúng bản chất preemptive

### Phần 8. Gọi thuật toán của queue

Code:

```python
t, budget = policyRunner(
    qId,
    readyLists[qIdx],
    t,
    budget,
    segments,
    nextArrivalTime,
)
```

Giải thích:

- Gọi thuật toán tương ứng của queue hiện tại
- Thuật toán sẽ cập nhật:
  thời gian `t`, budget còn lại, segment, process completion hoặc remaining

### Phần 9. Admit lại process mới và đếm số process hoàn thành

Code:

```python
admit_new_processes(t, notArrived, readyLists, queueIndex)
finishedCount = sum(1 for p in processes if p.completion is not None)
```

Giải thích:

- Sau khi một đoạn CPU vừa chạy xong, có thể đã đến thời điểm process mới xuất hiện
- Vì vậy phải admit lại
- Sau đó đếm số process đã hoàn thành để quyết định dừng vòng lặp chính

### Phần 10. Chuyển con trỏ Round Robin

Code:

```python
queuePtr = (qIdx + 1) % len(queues)
```

Giải thích:

- Sau khi queue hiện tại dùng xong lượt của nó, con trỏ chuyển sang queue tiếp theo
- Đây là Round Robin giữa các queue

### Phần 11. Trả kết quả

Code:

```python
return segments, processes
```

Giải thích:

- Trả lại toàn bộ các đoạn chạy CPU
- Trả lại danh sách process đã có `completion`

## Kết luận ngắn

`scheduler.py` là bộ điều phối trung tâm:

- chuyển process vào ready list đúng lúc
- phát hiện idle để jump time
- chọn queue theo Round Robin
- chọn thuật toán theo policy
- hỗ trợ SRTN preempt đúng thời điểm
- trả về `segments` và `processes` đã cập nhật
