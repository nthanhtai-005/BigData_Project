# HƯỚNG DẪN CHẠY 4 MAPREDUCE BẰNG APACHE PIG (từ A → Z)

> Mục tiêu: chạy 4 chương trình MapReduce viết bằng **Apache Pig**, đọc dữ liệu **từ HDFS** (đầu vào MapReduce do ETL sinh ra, cũng chính là dữ liệu của bảng Hive `mapreduce_input_tsv`), xuất kết quả ra `/output/pig_*` trên HDFS.
>
> Môi trường: Ubuntu Server trên VMware, user **`hadoopnhom6`**, đã cài Hadoop 3.4.1 + Hive 4.1.0 + **Pig 0.18.0** (theo tài liệu cài đặt của nhóm). **Hive đã có sẵn toàn bộ dữ liệu.**

---

## 0. TÓM TẮT NHANH (cho ai muốn làm ngay)

```bash
# 1) Đưa 4 file .pig + run_all.sh vào máy ảo, ví dụ thư mục ~/pig_jobs
# 2) Bật Hadoop nếu chưa bật:
start-dfs.sh && start-yarn.sh && jps
# 3) Chạy tất cả:
cd ~/pig_jobs
bash run_all.sh
```

Nếu chưa quen, hãy làm tuần tự các bước bên dưới.

---

## 1. KIỂM TRA MÔI TRƯỜNG TRƯỚC KHI CHẠY

Đăng nhập đúng user `hadoopnhom6` (vì Hadoop/Hive được cài cho user này):

```bash
whoami          # phải ra: hadoopnhom6
```

### 1.1. Bật HDFS + YARN

```bash
start-dfs.sh
start-yarn.sh
jps
```

`jps` phải thấy đủ **5 tiến trình**: `NameNode`, `DataNode`, `SecondaryNameNode`, `ResourceManager`, `NodeManager`. Thiếu cái nào thì xem mục **Sửa lỗi #6**.

### 1.2. Kiểm tra Pig đã cài

```bash
echo $PIG_HOME          # phải ra: /home/hadoopnhom6/pig
pig --version           # phải in ra: Apache Pig version 0.18.0 ...
```

Nếu báo `pig: command not found` → chạy `source ~/.bashrc` rồi thử lại (xem **Sửa lỗi #5**).

### 1.3. Kiểm tra dữ liệu đầu vào CÓ TỒN TẠI trên HDFS

```bash
hdfs dfs -ls /data/bigdata_ecommerce/mapreduce_input
```

Phải thấy 1 file `part-...` (và `_SUCCESS`). Nếu **không thấy** → dữ liệu chưa được ETL đẩy lên, báo lại bạn phụ trách ETL (TV2). Toàn bộ 4 script Pig đọc đúng thư mục này.

> ⚠️ Đây là dữ liệu **trên HDFS** do pipeline tạo ra, **KHÔNG** phải file `DATA.csv` ở máy cá nhân.

---

## 2. ĐƯA FILE VÀO MÁY ẢO (bước gửi file)

Bạn có file ZIP `pig_mapreduce_huy.zip` ở máy Windows (host). Chọn **MỘT** trong 3 cách:

### Cách A — Dùng nano để dán tay (CHẮC CHẮN CHẠY ĐƯỢC, không cần mạng)

Đây là cách an toàn nhất khi chưa cấu hình được mạng giữa host ↔ VM.

```bash
mkdir -p ~/pig_jobs
cd ~/pig_jobs
nano 01_price_gap.pig
```

Mở file `ALL_PIG_SCRIPTS_COPY_PASTE.txt` (trong ZIP) ở máy host, copy đúng đoạn của **FILE 1** (phần giữa 2 dòng `BAT DAU COPY` / `KET THUC COPY`), dán vào cửa sổ nano, rồi **Ctrl+O → Enter → Ctrl+X**. Làm tương tự cho `02_...`, `03_...`, `04_...`.

> Lưu ý khi dán: nếu trình soạn thảo trên Windows tự đổi dấu nháy `'` thành dấu nháy cong `’`, Pig sẽ báo lỗi cú pháp. Hãy gõ lại các dấu nháy đơn cho thành nháy thẳng `'`. (Xem **Sửa lỗi #4**.)

### Cách B — Dùng SCP (nếu host ↔ VM thông mạng)

Trên máy ảo, lấy IP:

```bash
hostname -I        # ví dụ: 172.172.0.150
```

Trên máy Windows (PowerShell/CMD), tại thư mục chứa file ZIP:

```powershell
scp pig_mapreduce_huy.zip hadoopnhom6@172.172.0.150:~/
```

Quay lại máy ảo:

```bash
cd ~
sudo apt install unzip -y          # nếu chưa có unzip
unzip pig_mapreduce_huy.zip -d pig_jobs
cd pig_jobs/pig_scripts             # hoặc cd vào nơi chứa 4 file .pig
ls
```

### Cách C — Thư mục chia sẻ VMware (Shared Folders)

Nếu đã bật Shared Folders, file host sẽ nằm ở `/mnt/hgfs/<ten_thu_muc_chia_se>/`. Copy vào:

```bash
mkdir -p ~/pig_jobs
cp /mnt/hgfs/<ten_thu_muc>/pig_scripts/*.pig ~/pig_jobs/
cp /mnt/hgfs/<ten_thu_muc>/pig_scripts/run_all.sh ~/pig_jobs/
cd ~/pig_jobs
```

➡️ Kết thúc bước này, trong `~/pig_jobs` phải có: `01_price_gap.pig`, `02_discount_bucket.pig`, `03_category_scale.pig`, `04_price_range.pig` (và `run_all.sh` nếu muốn chạy hàng loạt).

---

## 3. KIỂM TRA CẤU TRÚC DỮ LIỆU (1 lệnh – nên làm)

Để chắc chắn file TSV có đúng 17 cột như script đang giả định:

```bash
hdfs dfs -cat /data/bigdata_ecommerce/mapreduce_input/part-* | head -n 1 | cat -A
```

- Mỗi cột cách nhau bằng ký tự Tab, hiển thị là `^I`. **Đếm số `^I` + 1 = số cột.**
- Nếu ra **17 cột** (thứ tự: id, name, source_id, brand_id, source_name, category_name, brand_name, num_images, price, market_price, discount_amount, discount_percent, has_discount, sold_count, stock_quantity, scraped_at, category_id) → dùng script y nguyên, sang **Bước 4**.
- Nếu ra **11 cột** (bản ETL cũ) → xem **Sửa lỗi #7** để đổi phần `LOAD`.

---

## 4. CHẠY TỪNG CHƯƠNG TRÌNH PIG

> Mỗi script sẽ khởi chạy job MapReduce trên YARN, ghi kết quả ra HDFS rồi `DUMP` (in) ra màn hình. Job đầu thường mất 30–90 giây.

### 4.1. Chạy lần lượt (khuyên dùng lần đầu để dễ thấy lỗi)

```bash
cd ~/pig_jobs

# Bài 1: Price Gap
pig -x mapreduce 01_price_gap.pig

# Bài 2: Discount Bucket
pig -x mapreduce 02_discount_bucket.pig

# Bài 3: Category Scale (COUNT + SUM)
pig -x mapreduce 03_category_scale.pig

# Bài 4: Price Range (MIN + MAX + AVG)
pig -x mapreduce 04_price_range.pig
```

> `-x mapreduce` ép Pig chạy trên cụm Hadoop (đúng yêu cầu "MapReduce"). Có thể chạy gọn `pig 01_price_gap.pig` vì mặc định đã là chế độ mapreduce, nhưng ghi rõ `-x mapreduce` cho chắc.

Kết thúc mỗi lần chạy, Pig in dòng `Success!` và phần `Counters`/`Output(s)` cho biết đã ghi ra `/output/pig_*`. Phần `DUMP` ở cuối in trực tiếp kết quả ra màn hình → **đây là chỗ chụp hình cho báo cáo**.

### 4.2. Hoặc chạy tất cả bằng 1 lệnh

```bash
cd ~/pig_jobs
bash run_all.sh
```

Script `run_all.sh` tự xóa output cũ → chạy cả 4 bài → in kết quả từ HDFS. Rất tiện khi cần chạy lại nhiều lần.

---

## 5. XEM & XUẤT KẾT QUẢ

### 5.1. Xem trực tiếp trên HDFS

```bash
hdfs dfs -ls /output/pig_price_gap
hdfs dfs -cat /output/pig_price_gap/part-*
hdfs dfs -cat /output/pig_discount_bucket/part-*
hdfs dfs -cat /output/pig_category_scale/part-*
hdfs dfs -cat /output/pig_price_range/part-*
```

Mỗi dòng là 1 bản ghi CSV (ngăn cách bằng dấu phẩy), ví dụ `hasaki,Trang Điểm,135000`.

### 5.2. Tải kết quả về máy local (để TV5 vẽ biểu đồ / nộp báo cáo)

```bash
hdfs dfs -getmerge /output/pig_price_gap        ~/pig_jobs/ket_qua_price_gap.csv
hdfs dfs -getmerge /output/pig_discount_bucket  ~/pig_jobs/ket_qua_discount_bucket.csv
hdfs dfs -getmerge /output/pig_category_scale   ~/pig_jobs/ket_qua_category_scale.csv
hdfs dfs -getmerge /output/pig_price_range      ~/pig_jobs/ket_qua_price_range.csv
ls -lh ~/pig_jobs/*.csv
```

`getmerge` gộp các file `part-*` thành 1 file CSV duy nhất ở máy local — dễ mở bằng Excel.

---

## 6. KẾT QUẢ MẪU (để đối chiếu "đúng/sai")

> ⚠️ Bảng dưới đây tính trên **mẫu 100 dòng** mà bạn gửi (file DATA.csv đã cắt bớt) — chỉ để bạn hình dung **HÌNH DẠNG** kết quả và biết script chạy có ra đúng cột/đúng kiểu hay không. Khi chạy thật trên ~11.726 dòng, **con số sẽ khác** nhưng cấu trúc cột phải giống hệt.

**Bài 1 — `pig_price_gap` (source, category, avg_price_gap):**
```
hasaki,Trang Điểm,135000
hasaki,Chăm Sóc Da,80389
hasaki,Chăm Sóc Tóc,40000
hasaki,Chăm Sóc Cá Nhân,38840
hasaki,Chăm Sóc Cơ Thể,30000
lamthao,Thiết Bị Làm Đẹp,152500
lamthao,Nước Hoa,100000
lamthao,Chăm Sóc Da,52083
... (mỗi sàn × mỗi danh mục một dòng)
```

**Bài 2 — `pig_discount_bucket` (source, bucket, avg_sold, num_products):**
```
hasaki,11-20%,716,...
hasaki,21-30%,1403,...
hasaki,31-50%,144,...
lamthao,11-20%,1726,...
lamthao,21-30%,2068,...
```

**Bài 3 — `pig_category_scale` (source, category, total_products, total_sold):**
```
hasaki,Chăm Sóc Da,18,39312
hasaki,Chăm Sóc Cá Nhân,25,5727
...
lamthao,Trang Điểm,10,29153
lamthao,Chăm Sóc Da,12,23922
...
```

**Bài 4 — `pig_price_range` (source, category, min, max, avg):**
```
hasaki,Trang Điểm,520000,850000,685000
hasaki,Chăm Sóc Da,25000,525000,300000
...
lamthao,Thiết Bị Làm Đẹp,155000,1250000,702500
...
```

Trên dữ liệu thật, số danh mục mỗi sàn sẽ nhiều hơn (Hive có 10 danh mục, tổng 11.726 sản phẩm).

---

## 7. SỬA LỖI THƯỜNG GẶP

### Sửa lỗi #1 — `Output directory ... already exists`
Pig không cho ghi đè thư mục output. Xóa output cũ rồi chạy lại:
```bash
hdfs dfs -rm -r /output/pig_price_gap
```
(Đổi tên thư mục tương ứng với bài đang chạy. Hoặc dùng `run_all.sh` vì nó tự xóa.)

### Sửa lỗi #2 — Lỗi quyền ghi `/output` (`Permission denied`)
```bash
hdfs dfs -mkdir -p /output
hdfs dfs -chmod -R 777 /output
```

### Sửa lỗi #3 — Java 17 báo lỗi module (`InaccessibleObjectException`, `cannot access class ... java.base`)
Pig 0.18 chạy với JDK 17 đôi khi cần mở module. Thêm vào cuối `~/.bashrc`:
```bash
export PIG_OPTS="$PIG_OPTS --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.io=ALL-UNNAMED"
```
Rồi `source ~/.bashrc` và chạy lại. (Tài liệu nhóm đã thêm `--add-opens` cho Hadoop, nên thường không gặp lỗi này.)

### Sửa lỗi #4 — `Failed to parse` / lỗi cú pháp ngay đầu script
Hầu như do **dấu nháy cong** `‘ ’` hoặc `“ ”` do copy từ Word/Windows. Mở file kiểm tra:
```bash
grep -n '’\|‘\|“\|”' 01_price_gap.pig
```
Nếu có, mở nano sửa thành nháy thẳng `'`. Hoặc tự thay nhanh:
```bash
sed -i "s/’/'/g; s/‘/'/g" *.pig
```

### Sửa lỗi #5 — `pig: command not found`
```bash
source ~/.bashrc
echo $PIG_HOME            # phải ra /home/hadoopnhom6/pig
ls $PIG_HOME/bin/pig      # file phải tồn tại
```
Nếu vẫn lỗi, chạy trực tiếp: `$PIG_HOME/bin/pig -x mapreduce 01_price_gap.pig`.

### Sửa lỗi #6 — `jps` thiếu tiến trình / job treo ở 0%
HDFS hoặc YARN chưa chạy:
```bash
stop-yarn.sh; stop-dfs.sh
start-dfs.sh; start-yarn.sh
jps
```
Nếu thiếu `NameNode`, kiểm tra log ở `$HADOOP_HOME/logs`. Trường hợp lần đầu/đã format lỗi, cần format lại NameNode (CẨN THẬN: xóa dữ liệu HDFS — chỉ làm nếu cụm rỗng): `hdfs namenode -format`.

### Sửa lỗi #7 — File TSV chỉ có 11 cột (bản ETL cũ)
Nếu Bước 3 đếm ra **11 cột** (id, name, source_id, brand_id, source_name, category_name, brand_name, price, discount_percent, sold_count, category_id), thì phần `market_price`, `discount_amount`... không tồn tại. Khi đó:
- **Bài 1 (Price Gap)** và **Bài 4 (Price Range)** dùng `market_price`/`price` → cần dữ liệu 17 cột. Hãy báo TV2 chạy lại ETL bản mới (ảnh `df_flat_products.select(...)` 17 cột), hoặc tạm bỏ 2 bài này.
- **Bài 2, Bài 3** vẫn chạy được với 11 cột nếu bạn đổi đoạn `LOAD ... AS (...)` thành đúng 11 cột sau:
```pig
raw = LOAD '/data/bigdata_ecommerce/mapreduce_input/part-*'
      USING PigStorage('\t') AS (
          id:int, name:chararray, source_id:int, brand_id:int,
          source_name:chararray, category_name:chararray, brand_name:chararray,
          price:double, discount_percent:double, sold_count:long, category_id:int
      );
```
> Khuyến nghị: chạy bản 17 cột cho đồng bộ với code Java MapReduce của TV4.

### Sửa lỗi #8 — Pig chạy ở chế độ `local` thay vì `mapreduce`
Nếu thấy log ghi `local mode`, ép lại bằng `pig -x mapreduce <file>.pig` và đảm bảo biến `HADOOP_HOME`, `PIG_CLASSPATH=$HADOOP_HOME/etc/hadoop` đã set (đã có trong `~/.bashrc` theo tài liệu nhóm).

### Sửa lỗi #9 — Lỡ gõ `pig` rồi vào dấu nhắc `grunt>`
Bạn đang ở chế độ tương tác. Gõ `quit` để thoát, rồi chạy lại kèm tên file script.

---

## 8. PHỤ LỤC (TUỲ CHỌN) — Đọc TRỰC TIẾP từ bảng Hive bằng HCatLoader

Cách ở trên đọc file TSV trên HDFS — **chính là dữ liệu của bảng Hive `mapreduce_input_tsv`**, nên về bản chất đã là "đọc dữ liệu của Hive". Nếu muốn đọc **trực tiếp từ metastore Hive** (đọc bảng `flat_products_for_mapreduce` theo TÊN cột, không phụ thuộc thứ tự cột), có thể thử HCatLoader:

```bash
pig -useHCatalog -x mapreduce 01_price_gap.pig
```

Và đổi dòng `LOAD` trong script thành:
```pig
raw = LOAD 'bigdata_ecommerce.flat_products_for_mapreduce' USING org.apache.hive.hcatalog.pig.HCatLoader();
```
(các bước GROUP/AVG... giữ nguyên, vì truy cập cột theo tên).

> ⚠️ Cách này yêu cầu HCatalog của Hive nạp đúng cho Pig (set `HCAT_HOME`, thêm các jar `hive-hcatalog-*` vào classpath). Với cặp Pig 0.18 + Hive 4.1 đôi khi vênh thư viện → nếu báo `ClassNotFound`/`NoSuchMethod`, **quay lại cách đọc TSV ở Mục 4** (ổn định và cho ra kết quả y hệt).

---

## 9. CHECKLIST NỘP BÀI

- [ ] 4 file `.pig` đã đưa vào máy ảo và chạy ra `Success!`
- [ ] 4 thư mục `/output/pig_*` tồn tại trên HDFS, `hdfs dfs -cat` ra dữ liệu
- [ ] Chụp màn hình phần `DUMP` (kết quả) của từng bài
- [ ] (tuỳ chọn) `getmerge` ra 4 file CSV gửi TV5 vẽ biểu đồ
- [ ] Thêm mô tả **2 đề tài mới (Bài 3, Bài 4)** vào file đề tài MapReduce của nhóm (xem `DE_TAI_MAPREDUCE_PIG.md`)
