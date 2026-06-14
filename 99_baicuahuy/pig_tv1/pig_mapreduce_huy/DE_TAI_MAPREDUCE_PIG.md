# 4 ĐỀ TÀI MAPREDUCE BẰNG APACHE PIG

> Phần việc của **Huy**: *"Viết 4 chương trình MapReduce bằng Apache Pig cho bài toán cơ bản (max, min, group by, count...)"*.
> Tất cả đọc dữ liệu từ **đầu vào MapReduce trên HDFS** (`/data/bigdata_ecommerce/mapreduce_input/`) — đây chính là dữ liệu nằm dưới bảng Hive external `mapreduce_input_tsv`, **không** đọc file CSV ở máy cá nhân.

## Bối cảnh dữ liệu (rất quan trọng)

Dữ liệu thu thập từ **2 sàn TMĐT**: **Hasaki** và **Lam Thảo**. Trong dữ liệu, 2 sàn này nằm ở cột **`source_name`** với 2 giá trị `hasaki` và `lamthao` (cột `brand_name` là *nhãn hàng* của sản phẩm như Marvis, P/S, Sensodyne... — KHÁC với sàn).

➡️ Vì vậy mọi phép "so sánh Hasaki vs Lam Thảo" trong các đề tài đều lọc/gom nhóm theo **`source_name`**, không phải `brand_name`. (Các đề tài cũ trong file ghi nhầm là "brand" — bản Pig này làm đúng theo `source_name`.)

Các cột của file đầu vào TSV (`mapreduce_input`, ngăn cách bằng Tab, 17 cột, không có dòng tiêu đề):

| # | Cột | Kiểu | # | Cột | Kiểu |
|---|-----|------|---|-----|------|
| 1 | id | int | 10 | market_price | double |
| 2 | name | chararray | 11 | discount_amount | double |
| 3 | source_id | int | 12 | discount_percent | double |
| 4 | brand_id | int | 13 | has_discount | int |
| 5 | **source_name** | chararray | 14 | **sold_count** | long |
| 6 | **category_name** | chararray | 15 | stock_quantity | long |
| 7 | brand_name | chararray | 16 | scraped_at | chararray |
| 8 | num_images | int | 17 | **category_id** | int |
| 9 | **price** | double | | | |

---

## Đề tài 7 (đã có sẵn) — So sánh mức "Thổi giá" (Price Gap)

- **File:** `01_price_gap.pig`
- **Phép toán:** FILTER → FOREACH (tính `market_price - price`) → GROUP BY (source, category) → AVG.
- **Ý nghĩa:** Trung bình mỗi sản phẩm của từng sàn được "giảm/thổi giá" bao nhiêu đồng so với giá niêm yết, theo từng danh mục.
- **Output (`/output/pig_price_gap`):** `source_name , category_name , avg_price_gap`

## Đề tài 8 (đã có sẵn) — Hiệu quả Khoảng Giảm giá (Discount Bucket)

- **File:** `02_discount_bucket.pig`
- **Phép toán:** FILTER → bincond (chia `discount_percent` thành các khoảng 0–10%, 11–20%, 21–30%, 31–50%, >50%) → GROUP BY (source, bucket) → AVG + COUNT.
- **Ý nghĩa:** Mức giảm giá nào giúp bán chạy nhất ở mỗi sàn.
- **Output (`/output/pig_discount_bucket`):** `source_name , discount_bucket , avg_sold_count , num_products`

## ⭐ Đề tài 9 (MỚI) — Quy mô Danh mục & Tổng lượng bán

- **File:** `03_category_scale.pig`
- **Phép toán cơ bản:** FILTER → GROUP BY (source, category) → **COUNT** + **SUM**.
- **Ý nghĩa:** Mỗi sàn có bao nhiêu sản phẩm và bán ra tổng cộng bao nhiêu đơn trong từng danh mục → so sánh độ phủ hàng hóa và sức bán.
- **Output (`/output/pig_category_scale`):** `source_name , category_name , total_products , total_sold`

## ⭐ Đề tài 10 (MỚI) — Khung giá sản phẩm theo Danh mục (Min–Max–Avg)

- **File:** `04_price_range.pig`
- **Phép toán cơ bản:** FILTER → GROUP BY (source, category) → **MIN** + **MAX** + **AVG** → ORDER BY.
- **Ý nghĩa:** Mỗi sàn định giá thấp nhất / cao nhất / trung bình bao nhiêu trong từng danh mục → định vị phân khúc giá của 2 sàn.
- **Output (`/output/pig_price_range`):** `source_name , category_name , min_price , max_price , avg_price`

---

### Tổng hợp các phép toán cơ bản đã dùng (đáp ứng yêu cầu "max, min, group by, count...")

| Phép toán | Bài 1 | Bài 2 | Bài 3 | Bài 4 |
|-----------|:---:|:---:|:---:|:---:|
| FILTER | ✅ | ✅ | ✅ | ✅ |
| GROUP BY (nhiều khóa) | ✅ | ✅ | ✅ | ✅ |
| FOREACH / GENERATE | ✅ | ✅ | ✅ | ✅ |
| AVG | ✅ | ✅ | | ✅ |
| COUNT | | ✅ | ✅ | |
| SUM | | | ✅ | |
| MIN | | | | ✅ |
| MAX | | | | ✅ |
| bincond (phân nhóm) | | ✅ | | |
| ORDER BY | ✅ | ✅ | ✅ | ✅ |
