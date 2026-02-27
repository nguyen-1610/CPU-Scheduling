# Trình Lập Lịch CPU (CPU Scheduler)

Đồ án này là một hệ thống mô phỏng việc lập lịch CPU trên hệ điều hành, quản lý tiến trình với sự hỗ trợ của đa hàng đợi (multi-queue). Hệ thống hoạt động theo nguyên tắc **Round Robin** xoay vòng giữa các hàng đợi và sử dụng một trong các thuật toán chuyên sâu như **SJF (Shortest Job First)** hoặc **SRTN (Shortest Remaining Time Next)** ở bên trong mỗi hàng đợi.

Đồ án này thực hiện theo **Kiến trúc Monolith Phân Lớp (Layered Monolith)** và **Kiến trúc Plugin (Plugin-style Architecture)**.

---

## 1. Cấu Trúc Thư Mục và Kiến Trúc Layered Monolith

Mặc dù dự án là một khối duy nhất (Monolith), nhưng các thành phần bên trong được chia cắt và phân rã thành các lớp (Layers) với trách nhiệm độc lập rõ ràng. Điều này giúp mã nguồn dễ đọc, dễ bảo trì và dễ dàng test độc lập.

```text
Time_Scheduling/
├── src/
│   ├── algorithms/        <-- Tầng Thuật Toán (Thuộc Business Logic)
│   │   ├── registry.py    # Nơi đăng ký các "Plugin" thuật toán.
│   │   ├── roundRobin.py  # Điều phối nhảy vòng giữa các hàng đợi.
│   │   ├── sjf.py         # Logic lõi của SJF.
│   │   └── srtn.py        # Logic lõi của SRTN.
│   │
    ├── controller/        <-- Tầng Dịch Vụ Ứng Dụng (Application Service / Logic Mũi Nhọn)
    │   └── scheduler.py   # Nhận input, chứa hàm lập lịch chính `run_scheduling()`, điều phối chạy thuật toán.
    │
    ├── io/                <-- Tầng Giao Tiếp Dữ Liệu (Infrastructure / I-O Layer)
│   │   ├── parser.py      # Đọc file `.txt` đầu vào và parse (chuyển đổi) sang dữ liệu mô hình.
│   │   └── reportWriter.py# Xuất biểu đồ và bảng dữ liệu trạng thái xử lý sau khi mô phỏng xong.
│   │
│   ├── model/             <-- Tầng Thực Thể Lõi (Domain Model)
│   │   └── entities.py    # Khai báo các class data lõi (Process, Segment, QueueConfig).
│   │
│   ├── app.py             <-- Trình điều phối luồng tổng (Facade / Workflow Coordinator).
│   ├── cli.py             <-- Tầng Giao Diện Người Dùng (Presentation Layer / CLI interface).
│   └── main.py            <-- Entry point, gốc rễ kích hoạt chương trình.
│
├── requirements.txt
└── .gitignore
```

### Sự Kết Hợp Layered Monolith Thể Hiện Ở Đâu?

Hệ thống tuân thủ nghiêm ngặt nguyên tắc **Layered Architecture**. Bất kỳ dữ liệu nào đi từ ngoài vào đều phải đi qua các lớp:

1. **Lớp Giao Diện Thể Hiện (Presentation Layer - `cli.py`, `main.py`)**: Đứng ngoài cùng, phân tích tham số từ dòng lệnh (như tên file input/output) và chuyển xuống dưới. Nó hoàn toàn không biết cấu trúc bên trong phần mềm chạy ra sao.
2. **Lớp Phối Hợp Ứng Dụng (Application Workflow - `app.py`)**: Lớp này chỉ chịu trách nhiệm sắp xếp các bước hoạt động tuần tự: Lấy dữ liệu -> Chạy mô phỏng -> Viết báo cáo -> In ra màn hình.
3. **Lớp Chuyên Môn Cốt Lõi (Business Logic - `controller/` & `algorithms/`)**: Đảm nhiệm toàn bộ chất xám của việc lập lịch CPU như khi nào ngắt (preempt), chọn process nào tiếp theo. Lớp này không thực hiện việc đọc/ghi file.
4. **Lớp Hạ Tầng Dữ Liệu (Infrastructure & Model - `io/` & `model/`)**: Làm cầu nối trực tiếp với file văn bản (`io`) và định nghĩa dữ liệu trung tâm (`model`) được dùng chung để giao tiếp xuyên suốt các lớp ở trên.

---

## 2. Kiến Trúc Plugin (Plugin-Style Architecture)

Đây là điểm giúp tăng tính mở rộng (Extensibility) của đồ án.
Tại thư mục `src/algorithms/`, ta có file trung tâm là `registry.py` hoạt động giống hệt một **Plugin Manager** (Trình Quản Lý Tiện Ích Mở Rộng).

### Cơ Chế Hoạt Động (How it works)

1. **Sổ Đăng Ký (Registry):** Trong `registry.py` có một danh sách `_REGISTRY` (Mapping tên thuật toán dạng chuỗi `'SJF'` -> con trỏ đến thẳng hàm thực thi SJF). Tất cả tuân theo cùng một kiểu dáng hàm biểu mẫu `PolicyRunner`.
2. **Tích Hợp Nhẹ Nhàng:** `scheduler.py` ở bên ngoài khi cần chạy một hàng đợi KHÔNG CẦN quan tâm đó là chạy SJF hay SRTN. Nó chỉ yêu cầu: `"Lấy cho tôi hàm runner đang được gắn với tên SJF"`. Khi nhận được cái bóng (adapter) của hàm đó, `scheduler.py` chỉ việc cung cấp thông số đầu vào và nổ máy!
3. **Mở Rộng Không Bằng Cách Chỉnh Sửa:** Khi muốn thêm một thuật toán mới như **FCFS** (First Come First Serve), KHÔNG CẦN chạm vào hay sửa một ký tự nào ở `scheduler.py`. Chỉ cần:
   - Tạo file `fcfs.py` trong `src/algorithms`.
   - Vào `registry.py` để nhúng hàm đó vào bản ghi (vd: `"FCFS": _run_fcfs`).
     -> **Phần mềm lập tức hiểu thêm thuật toán mới**. Code tuân thủ tuyệt đối nguyên lý **Open-Closed Principle (OCP)** trong SOLID (Cho phép mở rộng, hạn chế chỉnh sửa code cũ).

---

## 3. Luồng Hoạt Động Của Hệ Thống (Execution Flow)

Để dễ hình dung về đồ án, dưới đây là luồng chạy từ lúc gõ lệnh chạy ứng dụng cho tới khi in ra bảng kết quả. Trình tự này nằm trọn trong `app.py`.

1. **Khởi Tạo (Bootstrapping):** Bắt đầu từ việc gọi lệnh terminal. File `main.py` khơi động `cli.py` để đọc và xác thực đường dẫn file `input.txt` & `output.txt` từ người dùng.
2. **Đọc Dữ Liệu (`io/parser.py`):** Lấy danh sách cấu hình hàng đợi (`QueueConfig`) và danh sách tiến trình (`Process`), sắp xếp sẵn các tiến trình theo thứ tự xuất hiện gốc vào mảng.
3. **Vòng Lặp Lập Lịch (`controller/scheduler.py`):**
   - Vòng lặp liên tục đẩy các tiến trình nhét vào khung lưới chờ của hàng đợi khi tới giờ (arrival time).
   - Kiểm tra thuật toán **Round Robin** (`algorithms/roundRobin.py`) để quyết định xem bước tới sẽ cho phép hàng đợi số nào chạy CPU.
   - Khi đã biết hàng đợi nào đc phép giữ CPU, hệ thống tra cứu thuật toán con của chính hàng đợi đó (qua _Plugin Registry_) như **SJF** hoặc **SRTN**.
   - Chạy thuật toán con. Trong lúc chạy, nếu có tiến trình nào mới đến mà ảnh hưởng đến thuật toán ngắt, nó sẽ ưu tiên ngắt để nhường chỗ (đối với SRTN).
   - Quá trình này sinh ra một danh sách liên tiếp các đoạn thời hạn CPU (`Segment`).
4. **Viết Báo Cáo (`io/reportWriter.py`):** Xử lý mớ `Segment` đó để gộp lại cho dễ nhìn và xuất ra Diagram. Kèm đó là bảng thống kê Turnaround Time, Waiting Time tính toán trên dữ liệu Completion của từng tiến trình. Cuối cùng, kết quả được xuất ra file `output.txt`.

---

## 4. Hướng Dẫn Chạy (How to run)

Yêu cầu duy nhất là cài **Python 3.7+**.
Dự án được viết hoàn toàn bằng _Thư viện Hệ Thống Chuẩn Python (Python Standard Library)_, không cần `pip install` bất cứ thứ gì thêm. Không yêu cầu cài đặt Docker hay bất cứ DB rườm rà nào hết.

Mở Terminal (Command Prompt) tại gốc thư mục dự án và chạy với cú pháp:

```bash
python -m src.main <đường_dẫn_file_input> <đường_dẫn_file_output>
```

**Ví dụ:**

```bash
python -m src.main ./input_sample.txt ./report_out.txt
```

Nếu chạy xong mà không in lỗi gì ra màn hình, mở file `./report_out.txt` để xem thành quả dạng sơ đồ Gantt và bảng tóm tắt thời gian CPU! Mọi thay đổi thuật toán, thêm thắt hay sửa đổi đều được tối ưu thân thiện tối đa với việc viết test mở rộng về sau.

---

## 5. Định dạng File (Input & Output Files)

Hệ thống giao tiếp đầu cuối thông qua file `.txt`. Bạn cần tự tạo ra các kịch bản test và lưu vào file Text (VD: `input_sample.txt`) để chương trình chạy.

### Cấu trúc File Đầu Vào (`input.txt`)

Trình phân tích cú pháp (`src/io/parser.py`) mong đợi dữ liệu được sắp xếp theo cấu trúc dòng như sau:

- **Dòng 1:** Một số nguyên `N` đại diện cho **số lượng hàng đợi (queues)**.
- **`N` dòng tiếp theo:** Xác định đặc tính của từng hàng đợi (mỗi hàng đợi 1 dòng), chia thành 3 cột cách nhau bởi khoảng trắng:
  `[Tên hàng đợi] [Thời gian cấp phép/Time Slice] [Tên Thuật Toán sẽ dùng]`
- **Các dòng còn lại tới cuối file:** Xác định các tiến trình (process) bốc vào hệ thống, chia thành 4 cột:
  `[Tên tiến trình] [Thời gian đến - Arrival Time] [Thời gian xử lý - Burst Time] [Hàng đợi chỉ định cho tiến trình]`

**Ví dụ một kịch bản đầu vào hợp lệ (`input_sample.txt`):**

```text
3
Q1 5 SJF
Q2 10 SRTN
Q3 8 SJF

P1 0 12 Q1
P2 2 4 Q2
P3 3 8 Q1
P4 5 15 Q3
P5 8 5 Q2
```

### Cấu trúc File Đầu Ra (`output.txt`)

Ngay khi kết thúc mô phỏng, Controller ném kết quả qua cho `src/io/reportWriter.py` để dựng văn bản biểu đồ. File kết quả in ra sẽ trông gồm 2 phần rất trực quan:

1. **Biểu Đồ CPU (CPU Scheduling Diagram):** Liệt kê quá trình chiếm dụng CPU (Gantt Chart dạng text), xem khoảng thời gian từ A đến B thì chương trình nào ở Queue nào đang được chạy.
2. **Bảng Thống Kê (Process Statistics):** Bảng tổng hợp số liệu của toàn bộ các tiến trình với các cột thông số thiết yếu để đánh giá hiệu suất hệ điều hành như:
   - Thời gian đến (`Arrival`)
   - Khối lượng thời gian cần CPU (`Burst`)
   - Mốc thời gian hoàn thành (`Completion`)
   - Tổng thời gian lưu lại trong hệ thống (`Turnaround`)
   - Tổn thất thời gian chờ đợi ở Ready List (`Waiting`)
     Và báo cáo **Trung bình thời gian (Average)** ở dưới cùng.
