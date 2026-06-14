# Hasaki & Lamthao API Catcher

Extension cho Chrome/Edge (Manifest V3) dùng để **bắt toàn bộ lời gọi API** (fetch & XMLHttpRequest) trên hai trang:

- https://hasaki.vn/
- https://lamthaocosmetics.vn/

Mục đích: thu thập (cào) dữ liệu sản phẩm từ chính các API mà trang web gọi. Extension **tự động bỏ qua các domain của Google** (Analytics, Tag Manager, GoogleAPIs, DoubleClick…).

---

## Yêu cầu

- Chrome hoặc Edge phiên bản **111 trở lên** (do dùng content script chạy ở `world: "MAIN"`).

## Cài đặt (chế độ Developer / Load unpacked)

1. Mở trình duyệt, vào địa chỉ:
   - Chrome: `chrome://extensions`
   - Edge: `edge://extensions`
2. Bật **Developer mode** (Chế độ nhà phát triển) ở góc trên bên phải.
3. Bấm **Load unpacked** (Tải tiện ích đã giải nén) và chọn thư mục `hasaki-lamthao-api-catcher`.
4. Extension sẽ xuất hiện với tên **Hasaki & Lamthao API Catcher**.

## Cách sử dụng

1. Mở `hasaki.vn` hoặc `lamthaocosmetics.vn`.
2. Nhấn **`Ctrl + Alt + N`** để **bắt đầu ghi**. Một nhãn đỏ `● REC API` hiện ở góc phải trên + badge trên icon hiển thị số request đã bắt.
3. Duyệt sản phẩm, danh mục, cuộn trang, mở chi tiết sản phẩm… để trang gọi API. Mọi API (trừ Google) sẽ được ghi lại.
4. Nhấn **`Ctrl + Alt + N`** lần nữa để **dừng ghi** (tùy chọn).
5. Nhấn **`Ctrl + Alt + M`** để **tải dữ liệu** về máy dưới dạng file `api-capture-....json`.

> Có thể bấm vào icon extension để mở popup: xem trạng thái, số request, nút Ghi/Dừng, Tải về, và Xóa dữ liệu.

### Phím tắt

| Phím tắt | Chức năng |
|---|---|
| `Ctrl + Alt + N` | Bắt đầu / Dừng ghi |
| `Ctrl + Alt + M` | Tải dữ liệu đã bắt (.json) |

## Định dạng dữ liệu xuất

```json
{
  "exportedAt": "2026-06-09T00:00:00.000Z",
  "source": "Hasaki & Lamthao API Catcher",
  "total": 123,
  "records": [
    {
      "type": "fetch",
      "method": "GET",
      "url": "https://hasaki.vn/wap/v2/...",
      "status": 200,
      "contentType": "application/json",
      "requestBody": null,
      "responseBody": "{...JSON trả về...}",
      "page": "https://hasaki.vn/danh-muc/...",
      "ts": 1733712000000
    }
  ]
}
```

- `type`: `fetch` hoặc `xhr`
- `requestBody` / `responseBody`: nội dung gửi đi / nhận về (dạng chuỗi)
- `page`: URL trang đang mở khi bắt được request
- `ts`: thời điểm (epoch ms)

> Mẹo: dữ liệu sản phẩm thường nằm ở các record có `contentType` chứa `json`. Bạn có thể lọc theo `url` (vd. chứa `product`, `category`, `search`) sau khi xuất file.

## Ghi chú kỹ thuật

- Dữ liệu được lưu trong `chrome.storage.local` nên **không mất** khi chuyển trang hoặc đóng/mở lại tab. Dùng nút **Xóa dữ liệu** (hoặc `CLEAR` trong popup) để xóa khi muốn bắt đầu phiên mới.
- Chỉ đọc nội dung cho response dạng **text/JSON/XML…**; các response nhị phân (ảnh, font, video) chỉ ghi metadata (`[skipped ...]`) để tránh phình bộ nhớ.
- Mỗi `responseBody` được giới hạn tối đa ~2 MB; phần dư bị cắt và đánh dấu `...[truncated]`.

## Tùy chỉnh

- **Thêm/bớt domain bị bỏ qua**: sửa mảng `BLOCKED_HOSTS` ở đầu file `src/interceptor.js`.
- **Đổi danh sách website áp dụng**: sửa `matches` và `host_permissions` trong `manifest.json`.
- Sau khi sửa file, vào trang extensions và bấm **Reload** (biểu tượng ↻) trên thẻ extension.

## Cấu trúc thư mục

```
hasaki-lamthao-api-catcher/
├── manifest.json
├── README.md
└── src/
    ├── interceptor.js   # MAIN world: override fetch/XHR, lọc domain Google
    ├── content.js       # ISOLATED world: cầu nối, phím tắt, toast, tải file
    ├── background.js     # Service worker: lưu trữ, trạng thái, export, badge
    ├── popup.html        # Giao diện điều khiển
    └── popup.js
```

## Lưu ý sử dụng hợp lệ

Công cụ này chỉ phục vụ thu thập dữ liệu công khai cho mục đích cá nhân/hợp pháp. Hãy tôn trọng Điều khoản sử dụng (Terms of Service) của từng website và các quy định pháp luật liên quan, tránh gửi request quá nhiều gây ảnh hưởng tới máy chủ.
