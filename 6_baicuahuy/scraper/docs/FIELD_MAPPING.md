# FIELD MAPPING — 14 trường → đường dẫn JSON cụ thể

Ký hiệu:
- `L.products[i]` = phần tử trong `data.products` của **Hasaki listing**.
- `D.common` = `data.blocks[type==CommonInfo].common_data` của **Hasaki detail**.
- `R` = response **Hasaki rating-reviews**.
- `C` = response **Hasaki comments**.
- `P` = `product` trong **Lamthao `.json`** (`/products/<handle>.json` hoặc phần tử `products[]`).
- `P.v` = `P.variants[k]` (một biến thể).

---

## HASAKI

| # | Trường | Đường dẫn (ưu tiên) | Nguồn dự phòng / Ghi chú |
|---|---|---|---|
| 1 | Tên | `L.name` | `D.common.name`; `english_name` phụ |
| 2 | URL ảnh | `L.image` (ảnh đại diện) | `D.common.gallery[].image` (full album) |
| 3 | ID | `L.id` | `L.sku`; URL `product_url` chứa `-<id>.html` |
| 4 | Giá trước giảm | `L.market_price` | `D.common.market_price` |
| 5 | Giá sau giảm | `L.price` | `D.common.price_detail.final_price` (chuỗi "₫") |
| 6 | Voucher % | `L.discount_percent` | Voucher tiền: `D.common.price_detail.coupons` ("64.000 ₫") |
| 7 | Số sao | `L.rating.average` | `D.common.rating.average` |
| 8 | Số lượt bán | `L.bought_count` | `L.order_count_30` (30 ngày) |
| 9 | Số comment | `D.common.comment.total` | `C.data.meta_data.comments_total` |
| 10 | Comment có ảnh | `R.data.rating.filter[key=='filter_has_image'].count` | =số **review** có ảnh |
| 11 | Phân bố sao | `R.data.rating.stars[]{star,count}` | mảng 5★→1★ |
| 12 | Danh mục | `L.category_name_level` ("A / B / C") | `D.common.category_list[]{id,name,level,url}` breadcrumb; `L.category_id` |
| 13 | Comment | `C.data.comments[]{content,user,created_at,sub_comments[]}` (hỏi đáp) + `R.data.reviews[]{content,rating.star,images,is_bought}` (đánh giá) | lấy mẫu N trang |
| 14 | Tồn kho | `L.quantity` | `D.common.quantity` |

**Trường mở rộng Hasaki nên lấy thêm:** `brand{name,id,url}`, `english_name`,
`promotion_text`, `deal{deal_id,quantity,bought_percent,expired}` (flash sale),
`announce.number` (số công bố Bộ Y Tế), `product_url`, `sku`.

---

## LAMTHAO

| # | Trường | Đường dẫn (ưu tiên) | Ghi chú |
|---|---|---|---|
| 1 | Tên | `P.title` | |
| 2 | URL ảnh | `P.image.src` (đại diện) | album: `P.images[].src`; thêm prefix `https:` nếu thiếu |
| 3 | ID | `P.id` (product) | biến thể: `P.v.id`, `P.v.sku`, `P.v.barcode`; `handle` |
| 4 | Giá trước giảm | `P.v.compare_at_price` | **VND đúng** từ `.json`. Nếu 0/None ⇒ không giảm |
| 5 | Giá sau giảm | `P.v.price` | **VND đúng** từ `.json` |
| 6 | Voucher % | tính: `round((compare-price)/compare*100)` khi `compare>price` | không có field % sẵn |
| 7 | Số sao | — | ❌ không có (ghi `null`) |
| 8 | Số lượt bán | `P.sole_quantity` | = "Đã bán N" (đã xác minh khớp) |
| 9 | Số comment | — | ❌ không có |
| 10 | Comment có ảnh | — | ❌ không có |
| 11 | Phân bố sao | — | ❌ không có |
| 12 | Danh mục | collection đang duyệt `{handle,title}` | + `P.product_type` + `P.tags[]` |
| 13 | Comment | — | ❌ không có (nền tảng tắt review) |
| 14 | Tồn kho | `sum(P.variants[].inventory_quantity)` | tồn kho từng biến thể: `P.v.inventory_quantity` |

**Trường mở rộng Lamthao nên lấy thêm:** `vendor` (=thương hiệu), `product_type`,
`tags[]`, `body_html` (mô tả), `available`, `options[]`, `published_at`,
và mỗi biến thể: `option1/2/3`, `grams`/`weight`, `available`, `inventory_policy`.

---

## Quy tắc chuẩn hoá chung (cả 2 nguồn)

1. **Giá**: lưu số nguyên VND. Hasaki đã là VND. Lamthao `.json` đã là VND. Không ×/÷.
2. **% giảm**:
   - Hasaki: dùng `discount_percent` có sẵn.
   - Lamthao: `has_voucher = compare_at_price > price > 0`; `discount_percent =
     round((compare-price)/compare*100)`.
3. **Tồn kho**: số nguyên. Lamthao = tổng các biến thể.
4. **Ảnh**: chuẩn hoá về URL tuyệt đối `https://...` (Lamthao đôi khi `//host/..`).
5. **Biến thể**: Hasaki 1 listing = 1 sản phẩm (giá đại diện). Lamthao nhiều biến thể
   → schema giữ `variants[]` + giá min/max ở cấp sản phẩm.
6. **Trường thiếu**: ghi `null`, kèm khối `data_availability` đánh dấu `false` để minh bạch.
