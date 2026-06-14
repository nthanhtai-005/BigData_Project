# Scraper sản phẩm Hasaki.vn & Lamthaocosmetics.vn

Cào dữ liệu sản phẩm **theo danh mục** từ 2 trang mỹ phẩm, trích xuất 14 nhóm thông
tin yêu cầu (tên, ảnh, id, giá trước/sau giảm, voucher %, sao, lượt bán, comment, số
comment có ảnh, phân bố sao, danh mục, nội dung comment, tồn kho) + nhiều trường mở rộng.

> Toàn bộ thiết kế dựa trên **nghiên cứu có bằng chứng** (dữ liệu API capture thật +
> xác minh request trực tiếp). Xem `docs/RESEARCH.md`, `docs/FIELD_MAPPING.md`, `docs/PLAN.md`.

---

## 1. Yêu cầu môi trường

- **Python 3.8+** (đã test trên Python 3.14, Windows/PowerShell).
- **KHÔNG cần cài thư viện nào** — chỉ dùng thư viện chuẩn (`urllib`, `json`, `csv`,
  `dataclasses`, `argparse`). Không cần `pip install`.

---

## 2. Chạy nhanh (Quick start)

```powershell
cd D:\Learning\Nhap_moi_big_data\Test\scraper

# Hasaki: 1 danh mục, 3 sản phẩm, đầy đủ chi tiết + đánh giá
python run.py hasaki --categories cham-soc-da-mat-c4 --max-products 3 --detail --reviews

# Lamthao: 1 collection, 5 sản phẩm
python run.py lamthao --collections cham-soc-co-the --max-products 5

# Kiểm tra độ phủ 14 trường + đối chiếu giá trị
python verify_output.py
```

Kết quả lưu ở `output/<site>_<timestamp>.{jsonl,json,csv}`.

### CÀO TẤT CẢ — ĐẦY ĐỦ (tự resume): `python crawl_all.py --delay 0.3`
Đã cào thực tế: Hasaki 9.205 SP (14/14) → `output/hasaki_full.*`; Hasaki listing 8.545 SP (10/14) → `output/hasaki_listing.*`; Lamthao 2.640 SP (9/14) → `output/lamthao_full.*`.

### CÀO TẤT CẢ — ĐẦY ĐỦ (một lệnh, tự resume)

```powershell
python crawl_all.py --delay 0.3
# hoặc thủ công, cùng cơ chế --job resume:
python run.py lamthao --all-collections --job full --delay 0.3
python run.py hasaki  --top-only --detail --reviews --job full --delay 0.3
```

### Kết quả đã cào thực tế

| Dataset | Số SP | Độ phủ | File |
|---|---:|---|---|
| Hasaki đầy đủ 14 trường | **9.205** | 14/14 | `output/hasaki_full.{json,csv}` |
| Hasaki listing toàn sàn | **8.545** | 10/14 | `output/hasaki_listing.{json,csv}` |
| Lamthao toàn bộ collection | **2.640** | 9/14 | `output/lamthao_full.{json,csv}` |

### CÀO TẤT CẢ — ĐẦY ĐỦ (một lệnh, tự resume)

```powershell
# Cào toàn bộ cả 2 trang. Có thể chạy nhiều giờ; nếu bị ngắt, chạy lại TỰ TIẾP TỤC.
python crawl_all.py --delay 0.3

# Hoặc thủ công từng trang (cùng cơ chế --job resume):
python run.py lamthao --all-collections --job full --delay 0.3
python run.py hasaki  --top-only --detail --reviews --job full --delay 0.3
```

> Job ghi vào `output/<site>_<job>.{jsonl,json,csv}`. Chạy lại cùng `--job` = tiếp tục.

### Kết quả đã cào thực tế (phiên gần nhất)

| Dataset | Số SP | Độ phủ | File |
|---|---:|---|---|
| Hasaki (đầy đủ 14 trường) | **9.205** | 14/14 (cột 13=58% vì phần còn lại chưa có comment) | `output/hasaki_full.{json,csv}` |
| Hasaki (listing toàn sàn) | **8.545** | 10/14 (gồm sao/bán/giá/tồn kho) | `output/hasaki_listing.{json,csv}` |
| Lamthao (toàn bộ 148 collection) | **2.640** | 9/14 (nền tảng không có review) | `output/lamthao_full.{json,csv}` |

### CÀO TẤT CẢ — ĐẦY ĐỦ (một lệnh, tự resume)

```powershell
# Cào toàn bộ cả 2 trang (Hasaki 14/14 + Lamthao). Có thể chạy nhiều giờ;
# nếu bị ngắt, chạy lại sẽ TỰ TIẾP TỤC (bỏ qua phần đã cào).
python crawl_all.py --delay 0.3

# Hoặc chạy thủ công từng trang (cùng cơ chế --job resume):
python run.py lamthao --all-collections --job full --delay 0.3
python run.py hasaki  --top-only --detail --reviews --job full --delay 0.3
```

> Mọi job ghi vào `output/<site>_<job>.{jsonl,json,csv}`. Chạy lại cùng `--job` =
> tiếp tục. `.jsonl` là nguồn chống mất dữ liệu; `.json`/`.csv` được dựng lại mỗi lần kết thúc.

### Kết quả đã cào thực tế (phiên gần nhất)

| Dataset | Số SP | Độ phủ | File |
|---|---:|---|---|
| Hasaki (đầy đủ 14 trường) | **9.205** | 14/14 (cột 13 = 58% vì phần còn lại chưa có comment) | `output/hasaki_full.{json,csv}` (52 MB / 5.4 MB) |
| Hasaki (listing toàn sàn) | **8.545** | 10/14 (nhanh, gồm sao/bán/giá/tồn kho) | `output/hasaki_listing.{json,csv}` |
| Lamthao (toàn bộ 148 collection) | **2.640** | 9/14 (nền tảng không có review) | `output/lamthao_full.{json,csv}` (30 MB / 2 MB) |

---

## 3. Cách dùng chi tiết

### 3.1 Hasaki
```powershell
# Cào nhiều danh mục cụ thể (slug có dạng <tên>-c<id>)
python run.py hasaki --categories cham-soc-da-mat-c4 trang-diem-c23 --max-pages 2

# Tự khám phá TOÀN BỘ cây danh mục rồi cào
python run.py hasaki --all-categories --max-pages 1

# Cào nhanh, chỉ listing (vẫn đủ #1-8,12,14), bỏ chi tiết/đánh giá
python run.py hasaki --categories nuoc-hoa-c103 --no-detail

# Tùy chỉnh số review/comment mẫu lấy mỗi sản phẩm
python run.py hasaki --categories cham-soc-toc-c96 --sample-reviews 10 --sample-comments 10
```

| Tham số | Ý nghĩa | Mặc định |
|---|---|---|
| `--categories A B C` | Danh sách slug danh mục `tên-c<id>` | (none) |
| `--all-categories` | Tự khám phá toàn bộ danh mục (qua `category-left`) | off |
| `--no-expand` | Khi `--all-categories`, không mở rộng danh mục con | off |
| `--detail` / `--no-detail` | Lấy/không lấy chi tiết (comment.total, voucher tiền, breadcrumb, gallery) | `--detail` |
| `--reviews` / `--no-reviews` | Lấy/không lấy sao + comment (cần `--detail`) | `--reviews` |
| `--sample-reviews N` | Số review mẫu/sản phẩm | 5 |
| `--sample-comments N` | Số comment mẫu/sản phẩm | 5 |
| `--device-id UUID` | `mobiledeviceid` cố định | random UUID |

### 3.2 Lamthao
```powershell
# Cào nhiều collection cụ thể (handle)
python run.py lamthao --collections cham-soc-co-the cham-soc-da-mat --max-pages 3

# Tự khám phá TOÀN BỘ collection rồi cào
python run.py lamthao --all-collections --max-products 500
```

| Tham số | Ý nghĩa | Mặc định |
|---|---|---|
| `--collections A B` | Danh sách handle collection | (none) |
| `--all-collections` | Tự khám phá toàn bộ collection (qua `collections.json`) | off |

### 3.3 Tham số chung (cả 2 site)

| Tham số | Ý nghĩa | Mặc định |
|---|---|---|
| `--max-pages N` | Giới hạn số trang mỗi danh mục | không giới hạn |
| `--max-products N` | Giới hạn tổng số sản phẩm | không giới hạn |
| `--size N` | Sản phẩm/trang (Hasaki ≤40, Lamthao ≤50) | 40/50 |
| `--delay S` | Độ trễ giữa request (giây) — lịch sự với máy chủ | 0.6 |
| `--retries N` | Số lần retry khi 429/5xx | 4 |
| `--formats jsonl json csv` | Định dạng xuất | cả 3 |
| `--out-dir PATH` | Thư mục output | `scraper/output` |
| `--quiet` | Tắt log từng sản phẩm | off |

---

## 4. Định dạng đầu ra

- **`.jsonl`**: mỗi dòng 1 sản phẩm (đầy đủ object, có `variants`, `reviews`, `comments`) —
  tốt cho xử lý dòng-một (streaming/big data).
- **`.json`**: mảng tất cả sản phẩm (đẹp, dễ đọc).
- **`.csv`**: bảng phẳng (UTF-8 BOM, mở Excel tiếng Việt OK) — các field lồng nhau được
  phẳng hoá/đếm (vd `num_variants`, `num_reviews_sampled`).

### Trường chính trong mỗi sản phẩm (schema thống nhất)
`source, product_id, sku, name, english_name, brand, url, image, images[],
market_price, price, discount_percent, has_voucher, voucher_text, price_min/max,
rating_average, sold_count, sold_count_30d, comment_count, comment_with_image_count,
review_count, star_breakdown{5..1}, category_path, category_breadcrumb[], product_type,
tags[], comments[], reviews[], stock_quantity, variants[], promotion_text, deal,
announce_number, description_html, available, data_availability{}`.

> `data_availability` đánh dấu trường yêu cầu nào **thực sự có dữ liệu** cho từng sản phẩm.

---

## 5. Độ phủ 14 trường (kết quả kiểm thử thực tế)

| # | Trường | Hasaki | Lamthao |
|---|---|:--:|:--:|
| 1 | Tên | ✅ | ✅ |
| 2 | URL ảnh | ✅ | ✅ |
| 3 | ID | ✅ | ✅ |
| 4 | Giá trước giảm | ✅ | ✅* |
| 5 | Giá sau giảm | ✅ | ✅ |
| 6 | Voucher (%) | ✅ | ✅ |
| 7 | Số sao | ✅ | ❌ |
| 8 | Số lượt bán | ✅ | ✅ |
| 9 | Số comment | ✅ | ❌ |
| 10 | Số comment có ảnh | ✅ | ❌ |
| 11 | Phân bố sao | ✅ | ❌ |
| 12 | Danh mục | ✅ | ✅ |
| 13 | Nội dung comment | ✅ | ❌ |
| 14 | Tồn kho | ✅ | ✅ |
| | **Tổng** | **14/14** | **9/14** |

\* Lamthao: `giá trước giảm` chỉ có khi sản phẩm **thực sự giảm giá** (`compare_at_price`).
Sản phẩm không giảm → để `null` + `has_voucher=false` (đúng ngữ nghĩa, không bịa).

**Vì sao Lamthao thiếu 5 trường (7,9,10,11,13)?** Nền tảng Haravan của Lamthao **tắt hệ
thống đánh giá** (`productReviewsApp=false`) — không có dữ liệu sao/bình luận để lấy.
Đây là **giới hạn nguồn dữ liệu**, không phải lỗi scraper. Chi tiết + bằng chứng:
`docs/RESEARCH.md` §2.4.

---

## 6. Kiến trúc mã nguồn

```
scraper/
├── run.py                  # CLI điều phối
├── verify_output.py        # Kiểm thử độ phủ 14 trường + đối chiếu giá trị
├── requirements.txt        # (chỉ stdlib)
├── docs/
│   ├── RESEARCH.md         # Nghiên cứu + bằng chứng (endpoint, giá trị thật)
│   ├── FIELD_MAPPING.md    # 14 trường → đường dẫn JSON cụ thể
│   └── PLAN.md             # Kế hoạch & kiến trúc
├── common/
│   ├── http_client.py      # HTTP (urllib) + retry/backoff + rate-limit
│   ├── schema.py           # UnifiedProduct (dataclass) + REQUIRED_FIELDS + CSV
│   ├── normalize.py        # Chuẩn hoá giá/%/URL ảnh/tồn kho
│   └── writer.py           # Ghi JSONL/JSON/CSV
├── hasaki/
│   ├── client.py           # 5 endpoint Hasaki (kèm header mobiledeviceid)
│   ├── categories.py       # Duyệt cây danh mục
│   └── scraper.py          # listing→detail→reviews→comments→UnifiedProduct
└── lamthao/
    ├── client.py           # 3 endpoint .json (Haravan)
    ├── collections.py      # Liệt kê collection
    └── scraper.py          # collection→products.json→UnifiedProduct
```

### Endpoint sử dụng (đã xác minh live)
**Hasaki** (cần header `mobiledeviceid`):
- `GET /api/v4/main/category-left?category_slug=<slug>-c<id>` — cây danh mục
- `GET /mobile/v3/main/products?cate_path=<slug>-c<id>&page=&size=40&has_meta_data=1&is_desktop=1` — listing
- `GET /mobile/v3/detail/product?product_id=<id>&is_desktop=1` — chi tiết
- `GET /mobile/v3/detail/product/rating-reviews?product_id=<id>&...` — sao + review
- `GET /mobile/v1/detail/product/comments?product_id=<id>&...` — bình luận

**Lamthao** (Haravan, không cần header đặc biệt):
- `GET /collections.json?page=&limit=250` — danh sách collection
- `GET /collections/<handle>/products.json?page=&limit=50` — listing
- `GET /products/<handle>.json` — chi tiết

---

## 7. Lưu ý quan trọng & vận hành

- **Lịch sự với máy chủ**: mặc định có `--delay 0.6s` + jitter + retry/backoff. Khi cào
  toàn site nên giữ delay ≥ 0.5s để tránh bị chặn (HTTP 429). Có thể tăng `--delay`.
- **Giá Lamthao**: scraper dùng endpoint `.json` (VND đúng). **Không** dùng JSON nhúng
  trong HTML vì giá bị ×100 (xem `docs/RESEARCH.md` §2.1).
- **Số lượt bán Lamthao** = `sole_quantity` trong `.json` (đã xác minh khớp “Đã bán N”).
- **Tồn kho Lamthao** = tổng `inventory_quantity` các biến thể.
- **Dữ liệu động**: giá/tồn kho/lượt bán thay đổi theo thời gian thực (đã thấy `quantity`
  Hasaki đổi giữa 2 lần gọi) — bình thường.
- **Dữ liệu lớn**: dùng `.jsonl` + `--max-pages`/`--max-products` để chia mẻ; có thể chạy
  song song nhiều danh mục bằng nhiều tiến trình (mỗi tiến trình 1 nhóm `--categories`).
- **Tuân thủ**: chỉ thu thập dữ liệu công khai cho mục đích cá nhân/hợp pháp; tôn trọng
  Điều khoản sử dụng của từng website và pháp luật liên quan; tránh gửi request quá dày.

---

## 8. Mở rộng về sau (gợi ý)

- Thêm checkpoint/resume (ghi lại danh mục+trang đã cào để chạy tiếp khi gián đoạn).
- Hasaki: lấy thêm `reviews` đa trang (hiện lấy mẫu N theo `--sample-reviews`).
- Lamthao: nếu cần “số comment”, có thể tích hợp Facebook Comments plugin (nếu trang dùng)
  — nhưng dữ liệu này không có trong API chính thức.
- Xuất thẳng vào database (SQLite/Postgres) thay vì file, tái dùng `UnifiedProduct`.
