# CPU Scheduling – Tài Liệu Học Tập & Vấn Đáp

## 1. Bài Toán Là Gì?

**CPU Scheduling** là bài toán quyết định *tiến trình (process) nào được chạy trên CPU tại mỗi thời điểm* khi có nhiều tiến trình cùng tồn tại.

Hệ thống này mô phỏng **Multi-Level Queue Scheduling** — nhiều hàng đợi thứ bậc, mỗi hàng dùng thuật toán riêng, vòng ngoài chọn hàng đợi theo Round Robin.

---

## 2. Các Khái Niệm Cần Nắm

| Khái niệm | Ý nghĩa |
|-----------|---------|
| **Arrival time** | Thời điểm process xuất hiện và sẵn sàng chạy |
| **Burst time** | Tổng thời gian CPU cần để xử lý xong process |
| **Remaining time** | Thời gian còn lại chưa xử lý (= burst lúc đầu, giảm dần) |
| **Completion time** | Thời điểm process hoàn thành |
| **Turnaround time** | `Completion − Arrival` — tổng thời gian kể từ lúc đến đến lúc xong |
| **Waiting time** | `Turnaround − Burst` — thời gian ngồi đợi không được chạy |
| **Time slice (quantum)** | Mỗi hàng đợi được phép chạy tối đa bao nhiêu đơn vị thời gian liên tiếp |

---

## 3. Hai Thuật Toán Lập Lịch

### 3.1 SJF – Shortest Job First (Non-preemptive)

- Luôn chọn process có **burst/remaining ngắn nhất** để chạy trước.
- **Non-preemptive**: không bị ngắt giữa chừng (trừ khi hết `time_slice` của hàng đợi đó).
- Tie-break: cùng remaining → ưu tiên `arrival` nhỏ hơn → rồi `seq` (thứ tự đọc file).

**Ví dụ** (TC02): P1(burst=8), P2(burst=3), P3(burst=5) cùng đến t=0:
```
SJF chọn: P2(3) → P3(5) → P1(8)
```

**Điểm yếu**: Process burst dài có thể bị đói (*starvation*) mãi mãi nếu cứ có process ngắn đến.

---

### 3.2 SRTN – Shortest Remaining Time Next (Preemptive)

- Luôn chọn process có **remaining ngắn nhất** — kể cả so với process đang chạy.
- **Preemptive**: nếu process mới đến có remaining < remaining của process đang chạy → **cướp CPU ngay**.
- `dt` (thời gian chạy 1 bước) bị giới hạn bởi `min(remaining, budget, nextArrivalTime − t)` để đảm bảo tại mỗi sự kiện arrival đều re-evaluate.

**Ví dụ** (TC01): P1(burst=8, arr=0), P2(burst=3, arr=2):
```
t=0: P1 bắt đầu chạy
t=2: P2 đến, remaining(P2)=3 < remaining(P1)=6 → P2 cướp CPU
t=2–5: P2 chạy xong
t=5–11: P1 tiếp tục (remaining=6)
```

**Điểm mạnh**: Turnaround trung bình tối ưu hơn SJF nếu có process ngắn đến liên tục.

---

### 3.3 So Sánh SJF vs SRTN

| | SJF | SRTN |
|-|-----|------|
| Preemptive? | ❌ | ✅ |
| Reaction khi process mới đến | Chờ hết lượt hiện tại | Ngắt ngay nếu mới ngắn hơn |
| Context switch | Ít | Nhiều hơn |
| Avg turnaround | Tốt | Tốt hơn |

---

## 4. Multi-Level Queue + Round Robin (Vòng Ngoài)

Hệ thống có **N hàng đợi**, mỗi hàng đợi có `time_slice` và `policy` riêng.

**Vòng ngoài** chọn hàng đợi theo **Round Robin**: chạy Q1 tối đa `time_slice(Q1)` đơn vị, rồi chuyển sang Q2, Q3, ... rồi lại Q1.

```
Q1(SRTN, ts=8) → Q2(SJF, ts=5) → Q3(SJF, ts=3) → Q1 → Q2 → ...
```

Nếu hàng đợi đang được chọn **rỗng** → bỏ qua, chuyển sang hàng tiếp theo.

---

## 5. Luồng Chạy Của Chương Trình

```
input.txt
    ↓
parse_input()          ← đọc + validate cấu hình queue và danh sách process
    ↓
run_scheduling()       ← vòng lặp chính: admit → chọn queue → chạy policy
    ↓
buildReport()          ← vẽ CPU diagram + tính thống kê
    ↓
stdout
```

---

## 6. Vòng Lặp Trong `run_scheduling`

```python
while finishedCount < total:
    admit_new_processes(t, ...)     # đưa process có arrival <= t vào ready list

    if is_system_idle():
        t = notArrived[0].arrival   # không có gì chạy → nhảy tới arrival tiếp theo

    qIdx = pickNextQueue(...)       # Round Robin chọn queue có process
    budget = time_slice của queue

    while budget > 0 and có process:
        [SRTN guard] admit nếu có arrival mới đúng tại t
        chạy policyRunner(...)      # SJF hoặc SRTN xử lý 1 bước
        admit_new_processes(t, ...) # process mới có thể arrive sau bước vừa chạy
        cập nhật finishedCount
```

**Điểm quan trọng**: `admit_new_processes` được gọi cả trước lẫn sau mỗi bước nhỏ để không bỏ sót process nào vừa đến.

---

## 7. Cấu Trúc File Input

```
3                    ← N hàng đợi
Q1 8 SRTN            ← QueueID  TimeSlice  Policy
Q2 5 SJF
Q3 3 SJF
P1 0 12 Q1           ← PID  Arrival  Burst  QueueID
P2 1 6  Q1
P3 2 8  Q2
```

**Quy tắc validate:**
- `N > 0`
- `TimeSlice > 0`
- `Policy` phải là `SJF` hoặc `SRTN`
- `Arrival >= 0`, `Burst > 0`
- `QueueID` phải là một trong N queue đã khai báo

---

## 8. Cấu Trúc Dự Án

```
src/
├── main.py                    # Entrypoint
├── model/
│   └── entities.py            # QueueConfig, Process, Segment (dataclass)
├── io/
│   ├── parser.py              # Đọc và validate input.txt
│   └── layoutOutput.py        # Vẽ CPU diagram + bảng thống kê
├── algorithms/
│   ├── registry.py            # Tra cứu thuật toán theo tên (SJF/SRTN)
│   ├── sjf.py                 # Thuật toán SJF
│   ├── srtn.py                # Thuật toán SRTN
│   └── roundRobin.py          # Chọn queue tiếp theo (pickNextQueue)
└── controller/
    └── scheduler.py           # Vòng lặp lập lịch chính
```

---

## 9. Các Edge Case Quan Trọng

### CPU Idle Gap
Process đến *muộn* sau khi tất cả đang chạy xong → scheduler **nhảy thẳng** thời gian tới `arrival` tiếp theo thay vì vòng lặp trống.

### SRTN Admit Guard
Khi `nextArrivalTime == t`, phải admit process mới vào **trước khi** `popSrtn` chọn. Nếu không, process mới (ngắn hơn) sẽ bị bỏ qua và process cũ tiếp tục chạy — sai thuật toán.  
Guard bổ sung: nếu `admit` không thay đổi `notArrived` (process đến thuộc queue khác), **không continue** để tránh vòng lặp vô hạn.

### Tie-break
Khi nhiều process có cùng `remaining`: ưu tiên `arrival` nhỏ hơn → rồi `seq` (thứ tự xuất hiện trong file). Đảm bảo kết quả **deterministc** (luôn ra cùng 1 kết quả với cùng input).

### SJF bị cắt bởi `time_slice`
SJF trong dự án này là *non-preemptive trong nội bộ 1 time slot*, nhưng vẫn bị cắt khi hết `time_slice` của hàng đợi (do Round Robin bên ngoài). Khi đó process chưa xong sẽ quay lại ready list của chính queue đó.

---

## 10. Các Câu Hỏi Vấn Đáp Thường Gặp

**Q: Tại sao SRTN cần biết `nextArrivalTime`?**  
A: Để giới hạn `dt` chạy đến đúng thời điểm arrival tiếp theo, rồi re-evaluate xem process mới có ngắn hơn không. Nếu không, SRTN có thể "vô tình" chạy qua thời điểm đó mà không kiểm tra.

**Q: Nếu 2 process có cùng remaining trong SRTN, chọn cái nào?**  
A: Cái có `arrival` nhỏ hơn (đến trước). Nếu cùng arrival thì chọn theo `seq` (thứ tự trong file).

**Q: `Segment` là gì?**  
A: Một khoảng thời gian liên tục `[start, end]` mà một process cụ thể chạy trên một queue cụ thể. Nhiều segment của cùng process được gộp lại trong output cho dễ đọc (`mergeSegments`).

**Q: Tại sao `Waiting Time = Turnaround − Burst`?**  
A: Turnaround = tổng thời gian từ lúc đến đến lúc xong. Trong đó Burst = thời gian thực sự chạy. Phần còn lại chính là thời gian ngồi chờ.

**Q: Tại sao dùng `seq` thay vì chỉ dùng `arrival` cho tie-break?**  
A: Vì nhiều process có thể có `arrival` bằng nhau (cùng đến t=0). `seq` là thứ tự đọc từ file — ổn định và nhất quán.

**Q: Multi-Level Queue và Multi-Level Feedback Queue khác nhau thế nào?**  
A: Dự án này là **Multi-Level Queue** cố định — mỗi process được gán cố định vào 1 queue và không thay đổi. **Feedback Queue** cho phép process di chuyển giữa các queue tùy theo hành vi (dùng nhiều CPU → xuống queue thấp hơn).

---

## 11. Cách Chạy

```bash
cd CPU-Scheduling

# Chạy với file mặc định (public/input.txt)
python3 -m src.main

# Chạy với file test cụ thể
python3 -m src.main public/input_01_basic_srtn.txt
python3 -m src.main public/input_06_srtn_preempt_chain.txt
```
