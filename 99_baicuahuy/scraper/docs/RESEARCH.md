# RESEARCH — Cào dữ liệu sản phẩm Hasaki.vn & Lamthaocosmetics.vn

> Tài liệu này ghi lại **toàn bộ kết quả nghiên cứu có bằng chứng** (từ dữ liệu API
> capture sẵn có trong `Data_Research/` **và** xác minh trực tiếp (live) bằng HTTP
> request thật). Mọi kết luận đều kèm endpoint + giá trị mẫu thực tế, **không suy đoán**.

Ngày nghiên cứu: 2026-06-09. Công cụ: Python 3.14, urllib (stdlib).

---

## 0. Nguồn dữ liệu đã dùng để nghiên cứu

| Nguồn | Đường dẫn | Vai trò |
|---|---|---|
| API capture Hasaki | `Data_Research/Hasaki/API/api-capture-*.json` (2.8 MB, 171 record) | Bắt request thật của app/web Hasaki |
| API capture Lamthao | `Data_Research/Lamthao/API/api-capture-*.json` (187 KB, 60 record) | Bắt request thật của web Lamthao |
| HTML Hasaki | `Data_Research/Hasaki/HTML/*.html` | Trang category + trang product (xác nhận chéo) |
| HTML Lamthao | `Data_Research/Lamthao/HTML/*.html` | Trang collection + product (Haravan) |
| Extension | `hasaki-lamthao-api-catcher/` | Công cụ đã tạo ra các file capture |

Script phân tích đặt tại `scraper/../_research/`:
`analyze_capture.py`, `dump_schema.py`, `get_path.py`, `probe_html.py`,
`extract_lamthao.py`, `verify_live.py`, `verify_live2.py`.

---

## 1. HASAKI — Kiến trúc & Endpoint

Hasaki dùng **API JSON kiểu mobile** (sạch, có cấu trúc). Đây là nguồn lý tưởng.

### 1.1 Header bắt buộc
Qua test live (`verify_live.py`), endpoint trả `200 + error_code=0` khi gửi:
```
User-Agent: Mozilla/5.0 ... Chrome/149 ...
Referer:    https://hasaki.vn/...
mobiledeviceid: <UUID bất kỳ>      # BẮT BUỘC — thiếu sẽ bị chặn
```
`mobiledeviceid` là 1 UUID v4 tuỳ ý (vd `60fff625-b379-42fa-a60e-f13760c01174`).

### 1.2 Bảng endpoint (đã xác minh)

| Mục đích | Method + URL | Trường quan trọng |
|---|---|---|
| **Cây danh mục** | `GET /api/v4/main/category-left?category_slug=<slug>-c<id>` | `data.categoryLeft.subCate[]{id,name,url,path, subCateItem[]}` |
| **Listing theo danh mục** | `GET /mobile/v3/main/products?cate_path=<slug>-c<id>&page=N&size=40&has_meta_data=1&is_desktop=1` | `data.products[]`, `data.meta_data.products_total`, `data.filter[]` |
| **Chi tiết sản phẩm** | `GET /mobile/v3/detail/product?product_id=<id>&is_desktop=1` | `data.blocks[type=CommonInfo].common_data` |
| **Đánh giá (sao)** | `GET /mobile/v3/detail/product/rating-reviews?product_id=<id>&page=N&size=5&sort=create&filter=filter_all&is_desktop=1` | `data.rating.stars[]`, `data.rating.filter[]`, `data.reviews[]`, `data.total` |
| **Bình luận/hỏi đáp** | `GET /mobile/v1/detail/product/comments?product_id=<id>&page=N&size=5` | `data.meta_data.comments_total`, `data.comments[]` |

### 1.3 Phân trang (listing)
- `size` tối đa quan sát được = 40. `page` bắt đầu từ 1.
- Tổng số sản phẩm: `data.meta_data.products_total` (vd category `cham-soc-da-mat-c4` = **3217**).
- Số trang = `ceil(products_total / size)`.

### 1.4 Cây danh mục — cách suy ra id & slug
- Slug danh mục có dạng `ten-khong-dau-c<ID>` (vd `cham-soc-da-mat-c4` → id = 4).
- `category-left` của 1 slug trả về **các danh mục anh em (subCate)** + **danh mục con (subCateItem)**.
- Top-level (đã thấy trong capture):
  `cham-soc-da-mat-c4`, `trang-diem-c23`, `cham-soc-toc-c96`, `cham-soc-co-the-c12`,
  `nuoc-hoa-c103`, `thoi-trang-c2351`, `gia-dung-doi-song-c2440`,
  `hasaki-clinic-spa-c331`, `my-pham-high-end-c1907`.
- Gọi `/mobile/v3/main/products?cate_path=<top-level>` trả về **toàn bộ sản phẩm
  trong cả cây con** (products_total lớn) → chỉ cần duyệt top-level là đủ phủ;
  duyệt thêm subCate giúp gán danh mục chi tiết hơn.

### 1.5 Bằng chứng giá trị thật (sản phẩm id=102959 — Sữa Rửa Mặt CeraVe)
```
LISTING : market_price=490000  price=369000  discount_percent=25
          quantity=52148 (live) / 52160 (capture)  bought_count=1397
          rating={total:116, average:4.9}
          category_name_level="Chăm Sóc Da Mặt / Làm Sạch Da / Sữa Rửa Mặt"
DETAIL  : comment.total=625   price_detail.coupons="64.000 ₫"  final_price="369.000 ₫"
REVIEWS : stars=[(5,106),(4,10),(3,0),(2,0),(1,0)]  total=116
          filter_has_image.count = số review có ảnh
COMMENTS: comments_total=625
```
> Ghi chú: `quantity` listing đổi giữa capture↔live (52160→52148) ⇒ dữ liệu **động/realtime**.

---

## 2. LAMTHAO — Kiến trúc & Endpoint

Lamthao chạy trên **Haravan** (nền tảng TMĐT giống Shopify của VN). Dấu hiệu xác nhận:
- CDN ảnh `product.hstatic.net/200000868185/...`, `file.hstatic.net/1000308580/...`
- Endpoint `cart.js` (có `token`, `requires_shipping`), `inventory_location.js?variant_id=`
- Biến JS `Haravan.theme`, `var meta = {...}` trong HTML.

→ Hệ quả: Haravan **hỗ trợ các endpoint `.json` công khai** (giống Shopify AJAX API).
Đã xác minh tất cả trả `200 application/json`:

| Mục đích | URL | Ghi chú |
|---|---|---|
| **Danh sách collection** | `GET /collections.json?page=N&limit=250` | `collections[]{id,handle,title,...}`; phân trang theo `page`, hết khi mảng rỗng |
| **Listing theo collection** | `GET /collections/<handle>/products.json?page=N&limit=50` | `products[]` (đủ `variants`); hết khi mảng rỗng |
| **Chi tiết sản phẩm** | `GET /products/<handle>.json` | `product{}` đầy đủ |
| (phụ) Tồn kho theo kho | `GET /inventory_location.js?variant_id=<id>&quantity=1` | danh sách kho có hàng |

**KHÔNG cần header đặc biệt** cho Lamthao (chỉ cần User-Agent thường).

### 2.1 ⚠️ Đơn vị giá — điểm bẫy quan trọng (đã xác minh)
- JSON **nhúng trong HTML** (`var meta`, `data:{...}`, quickview) trả `price=300000`,
  `compare_at_price=600000` — tức **bị ×100** so với giá hiển thị.
- Endpoint **`.json` công khai** trả `price=3000`, `compare_at_price=6000` — **đúng VND**
  (khớp “3.000₫ / 6.000₫” hiển thị trên web).
- **KẾT LUẬN: luôn dùng endpoint `.json`. Giá là VND nguyên (không nhân/chia).**
  Bằng chứng 3 biến thể của 1 sản phẩm (đều hợp lý):
  ```
  9ml   : price=3000     compare=6000     inventory=7331
  250ml : price=144000   compare=180000   inventory=48
  500ml : price=219000   compare=250000   inventory=58
  ```

### 2.2 `sole_quantity` = SỐ LƯỢT BÁN (đã xác minh)
- `product.sole_quantity` trong `.json` = **48949**, **khớp chính xác** chuỗi
  “Đã bán 48949” hiển thị trên thẻ sản phẩm HTML.
- ⇒ Không cần parse HTML để lấy lượt bán; dùng `sole_quantity` từ `.json`.

### 2.3 Tồn kho
- `variants[].inventory_quantity` (vd 7331). Haravan **công khai tồn kho** trong `.json`
  (khác Shopify thường ẩn). Tồn kho sản phẩm = tổng `inventory_quantity` các biến thể.

### 2.4 ❌ KHÔNG có hệ thống đánh giá/sao native (đã xác minh)
- HTML chứa `var productReviewsApp = false;` và `productReviewsProloop = false;`.
- Tab “Đánh giá - Hỏi đáp” chỉ chứa **mô tả sản phẩm tĩnh**, không có dữ liệu sao/bình luận.
- Thẻ sản phẩm hiển thị “5.0” sao **tĩnh** (hard-coded UI theme), **không đáng tin** làm dữ liệu.
- ⇒ Lamthao **không cung cấp**: #7 số sao thực, #9 số comment, #10 comment có ảnh,
  #11 phân bố sao, #13 nội dung comment. (Sẽ ghi `null` + cờ `available=false` trong schema.)

### 2.5 Trường có sẵn trong `.json`
`id, title, handle, vendor(=thương hiệu), product_type, tags[], body_html(mô tả),
images[]{src}, image{src}, options[], sole_quantity, available, created_at,
published_at, updated_at`, và `variants[]{ id, sku, barcode, price, compare_at_price,
inventory_quantity, old_inventory_quantity, option1/2/3, grams, weight, weight_unit,
available, inventory_management, inventory_policy }`.

---

## 3. Đối chiếu khả năng cung cấp 14 trường

| # | Trường yêu cầu | Hasaki | Lamthao |
|---|---|:--:|:--:|
| 1 | Tên sản phẩm | ✅ | ✅ |
| 2 | URL ảnh | ✅ | ✅ |
| 3 | ID | ✅ | ✅ |
| 4 | Giá trước giảm | ✅ | ✅ |
| 5 | Giá sau giảm | ✅ | ✅ |
| 6 | Voucher (%) | ✅ | ✅ (tính từ compare/price) |
| 7 | Số sao | ✅ | ❌ (không có hệ thống) |
| 8 | Số lượt bán | ✅ | ✅ (`sole_quantity`) |
| 9 | Số comment | ✅ | ❌ |
| 10 | Số comment có ảnh | ✅ | ❌ |
| 11 | Phân bố sao 5/4/3.. | ✅ | ❌ |
| 12 | Danh mục | ✅ | ✅ (collection/type/tags) |
| 13 | Nội dung comment | ✅ | ❌ |
| 14 | Tồn kho | ✅ | ✅ |

> **Kết luận trung thực:** Hasaki phủ **14/14**. Lamthao phủ **9/14** (thiếu nhóm
> đánh giá/bình luận vì nền tảng không có). Đây là giới hạn **dữ liệu nguồn**, không
> phải giới hạn scraper. Chi tiết mapping field→đường dẫn JSON: xem `FIELD_MAPPING.md`.
