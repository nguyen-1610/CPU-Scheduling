# Tong hop nhung gi da sua cho Lab 2

## Muc tieu

Lab 2 yeu cau doc file `.txt` tu USB FAT32 bang cach doc raw bytes tu o dia, sau do parse noi dung va hien ket qua lap lich CPU tren giao dien.

Vi vay phan sua duoc lam theo 3 huong chinh:

1. Khong parse bang cach mo file input truc tiep nua.
2. Noi lai phan scheduling cua Lab 1 vao giao dien Lab 2.
3. Chinh giao dien output de giong tinh than Lab 1 hon, nhung chi hien tren GUI, khong ghi ra file output.

---

## 1. Sua parser de dung duoc voi raw bytes cua Lab 2

### File da sua

- `src/io/parser.py`

### Truoc khi sua

`parse_input()` chi nhan duong dan file, roi dung `open(file_path, ...)` de doc noi dung. Cach nay hop voi Lab 1 CLI, nhung khong hop voi Lab 2 vi Lab 2 doc du lieu tu FAT32 thanh mot mang byte truoc roi moi xu ly.

### Sau khi sua

Mình tach parser thanh 3 lop:

- `parse_input_text(text)`: parse tu chuoi text
- `parse_input_bytes(raw_bytes)`: parse tu mang byte
- `parse_input(file_path)`: giu lai cho Lab 1, nhung ben trong doc file dang bytes roi goi parser chung

### Ly do sua

Lam nhu vay thi:

- Lab 1 van chay duoc nhu cu
- Lab 2 co the truyen thang du lieu bytes doc tu FAT32 vao parser
- tranh viec viet lai parser thu cong nhieu noi

---

## 2. Noi parser moi vao luong doc file cua Lab 2

### File da sua

- `src/gui/files_tab.py`

### Truoc khi sua

Sau khi doc `raw_content` tu cluster chain, code decode thanh `text` roi truyen text vao dialog.

### Sau khi sua

`files_tab.py` gio giu nguyen `raw_content` sau khi cat theo dung `file size`, roi truyen truc tiep bytes nay vao `DetailDialog`.

### Ly do sua

Dieu nay dung voi yeu cau Lab 2 hon:

- FAT32 doc ra bytes
- parser cua Lab 2 xu ly tu bytes
- tranh phai decode va parse thu cong o nhieu tang

---

## 3. Bo parser viet tay trong dialog, thay bang parser dung chung

### File da sua

- `src/gui/detail_dialog.py`

### Truoc khi sua

Dialog co 1 ham `_parse_lab1_input(...)` viet tay lai gan nhu toan bo parser cua Lab 1 de parse noi dung file.

### Sau khi sua

Ham nay gio chi con:

- nhan `raw_content: bytes`
- goi `parse_input_bytes(raw_content)`
- tra ve `(queues, processes, error)`

### Ly do sua

Lam nhu vay giup:

- khong bi trung lap logic parse
- de bao tri hon
- neu sau nay doi format parser thi chi can sua 1 noi

---

## 4. Noi lai scheduling cua Lab 1 vao Lab 2

### File da sua

- `src/gui/detail_dialog.py`

### Cach minh noi

Sau khi parse xong:

1. Tao lai danh sach process moi (`fresh`) de reset trang thai `remaining` va `completion`
2. Goi `run_scheduling(queues, fresh)`
3. Lay `segments` va `result_procs`
4. Dua ket qua len giao dien

### Ly do sua

Day la phan "tai su dung Lab 1" dung theo yeu cau de:

- logic scheduling van nam o Lab 1
- Lab 2 chi dong vai tro doc file FAT32 va hien thi GUI

---

## 5. Chinh giao dien output scheduling cho giong Lab 1 hon

### File da sua

- `src/gui/detail_dialog.py`

### Truoc khi sua

Dialog hien:

- thong tin file
- bang process
- Gantt chart
- bang metrics

### Sau khi sua o giai doan giua

Mình da tung them 1 khung text `Scheduling Output (similar Lab 1)` de hien dung format report cua Lab 1 bang `buildReport(...)`.

Format nay gom:

- `CPU SCHEDULING DIAGRAM`
- `PROCESS STATISTICS`

### Sau khi chot theo yeu cau moi nhat cua ban

Mình da tiep tuc sua lai:

- bo han `Gantt Chart`
- bo han bang thong ke cuoi
- bo chu `similar Lab 1`
- chi giu khung text `Scheduling Output`

Noi dung trong khung nay duoc tao boi:

- `buildReport(segments, result_procs)`

### Ly do sua

Vi ban muon giao dien:

- gon hon
- giong output Lab 1
- khong lap thong tin bang nhieu kieu hien thi

---

## 6. Chinh app mo full man hinh khi chay

### File da sua

- `src/main_gui.py`

### Truoc khi sua

App mo bang:

```python
win.show()
```

### Sau khi sua

App mo bang:

```python
win.showMaximized()
```

### Ly do sua

De vua mo app la giao dien o trang thai full man hinh/maximized, dung voi yeu cau moi nhat cua ban.

---

## 7. Nhung gi hien tai giao dien se lam

Khi ban chay `python -m src.main_gui`, luong xu ly se la:

1. Ket noi o FAT32
2. Liet ke file `.txt`
3. Chon 1 file va bam `View Details`
4. Doc bytes cua file tu cluster chain
5. Truyen bytes vao parser moi
6. Chay `run_scheduling()` cua Lab 1
7. Hien trong dialog:
   - thong tin file
   - bang process
   - khung `Scheduling Output` theo format Lab 1

Khong con:

- Gantt chart
- bang metrics rieng o cuoi
- ghi file output cho Lab 2

---

## 8. Kiem tra da lam

Mình da tu kiem tra cac diem sau:

- parser moi nhan duoc `bytes`
- scheduler chay ra ket qua hop le voi input mau
- luong GUI da truyen `raw_content` vao dialog thay vi text parse thu cong

Co 1 dieu can luu y:

- trong moi truong hien tai khong co `PySide6`, nen minh khong mo truc tiep GUI de nhin bang mat duoc
- tuy nhien phan noi logic va cau truc code da duoc sua dung theo yeu cau

---

## 9. Danh sach file da sua

- `src/io/parser.py`
- `src/gui/files_tab.py`
- `src/gui/detail_dialog.py`
- `src/main_gui.py`

---

## 10. Tom tat ngan gon

Ban co the hieu ngan gon la:

- Lab 1: scheduling engine
- Lab 2: doc FAT32 + GUI

Mình da sua de Lab 2:

- doc file bang raw bytes
- parse tu bytes thay vi mo file input truc tiep
- goi lai scheduling cua Lab 1
- hien output scheduling theo kieu Lab 1 tren giao dien
- mo app o che do full man hinh

