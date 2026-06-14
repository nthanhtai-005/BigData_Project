# PLAN — Kiến trúc & triển khai scraper

## Mục tiêu
Cào sản phẩm **theo danh mục** từ Hasaki & Lamthao, xuất ra **schema thống nhất**
(JSON + CSV), phủ tối đa 14 trường yêu cầu, có bằng chứng/đối chiếu.

## Nguyên tắc thiết kế
- **Chỉ dùng JSON API** (đã xác minh) — ổn định hơn parse HTML.
- **Lịch sự với máy chủ**: 1 phiên `requests.Session`, có `--delay` (mặc định 0.5–1s),
  retry + backoff cho lỗi 429/5xx, giới hạn số trang/sản phẩm cấu hình được.
- **Idempotent & resume-friendly**: ghi từng dòng (JSONL) để không mất dữ liệu giữa chừng.
- **Tách nguồn**: `hasaki/` và `lamthao/` riêng, chung `common/` (schema, http, normalize).
- **Trung thực dữ liệu**: trường nguồn không có ⇒ `null` + cờ `data_availability`.

## Cấu trúc thư mục
```
scraper/
├── docs/                  RESEARCH.md, FIELD_MAPPING.md, PLAN.md
├── common/
│   ├── http_client.py     Session + retry/backoff + rate limit + headers
│   ├── schema.py          UnifiedProduct (dataclass) + to_dict/CSV columns
│   └── normalize.py       chuẩn hoá giá, %, ảnh URL, tồn kho
├── hasaki/
│   ├── client.py          gọi 5 endpoint Hasaki (đã có headers mobiledeviceid)
│   ├── categories.py      duyệt cây danh mục (category-left)
│   └── scraper.py         listing→detail→reviews→comments → UnifiedProduct
├── lamthao/
│   ├── client.py          gọi 3 endpoint .json Haravan
│   ├── collections.py     liệt kê collection (collections.json)
│   └── scraper.py         collection listing→detail → UnifiedProduct
├── run.py                 CLI: chọn site, category, giới hạn, output
├── requirements.txt
└── output/                kết quả .jsonl / .csv
```

## Luồng Hasaki
1. `categories.discover()` → danh sách `(slug, id, name)` (seed top-level + mở rộng subCate).
2. Với mỗi category: gọi listing `page=1..ceil(products_total/size)`.
3. Mỗi product (listing đã đủ #1-8,#12,#14). Nếu `--detail`: gọi detail (bổ sung
   #9 comment.total, voucher tiền, breadcrumb, gallery, announce).
4. Nếu `--reviews`: gọi rating-reviews (lấy #10,#11 + N review mẫu) và comments (#13).
5. Map → `UnifiedProduct` → ghi JSONL + CSV.

## Luồng Lamthao
1. `collections.discover()` → tất cả `(handle,id,title)` qua `collections.json` phân trang
   (hoặc nhận handle cụ thể từ CLI).
2. Với mỗi collection: `products.json?page=N` đến khi rỗng.
3. Mỗi product `.json` đã đủ #1-6,#8,#12,#14. Map → `UnifiedProduct`.
4. #7,#9,#10,#11,#13 = `null` (nguồn không có) + cờ availability.

## CLI (run.py) — phác thảo
```
python run.py hasaki  --categories cham-soc-da-mat-c4 --max-pages 2 --detail --reviews
python run.py hasaki  --all-categories --max-pages 1
python run.py lamthao --collections cham-soc-co-the   --max-pages 2
python run.py lamthao --all-collections --max-products 200
```
Tham số chung: `--delay`, `--limit/size`, `--out-dir`, `--format json|csv|both`.

## Kiểm thử (task 7)
- Chạy 1 category nhỏ mỗi site (giới hạn ~1 trang / vài sản phẩm).
- Script `verify_output.py`: kiểm 14 trường, đối chiếu vài giá trị với
  capture (vd Hasaki id=102959: bought_count=1397; Lamthao sole_quantity=48949).
