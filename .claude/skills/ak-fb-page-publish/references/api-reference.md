# Tham chiếu Graph API — đăng bài Page

Endpoint, tham số và giới hạn mà `scripts/fb_page_publish.py` sử dụng.
Phiên bản mặc định: `v21.0` (`META_API_VERSION`).

Base URL: `https://graph.facebook.com/{version}/`

> Graph API bỏ qua request body của `GET` và `DELETE`. Tham số của hai method
> này — kể cả `access_token` — phải nằm trong query string.

---

## Chẩn đoán

### `GET /debug_token`

| Tham số | Bắt buộc | Ghi chú |
|---------|----------|---------|
| `input_token` | có | Token cần kiểm tra |
| `access_token` | có | Token có quyền kiểm tra (dùng chính nó với System User) |

Trả về `data.type`, `data.expires_at` (`0` = không hết hạn), `data.scopes`.

### `GET /me/accounts`

| Tham số | Ghi chú |
|---------|---------|
| `fields` | `id,name,tasks` |
| `limit` | Tối đa 100 |

`tasks` chứa `CREATE_CONTENT` thì token được phép tạo nội dung trên page đó.
Đây là quyền cấp **tài sản**, khác với **scope** của token — cần đủ cả hai.

### `GET /{page-id}?fields=access_token`

Đổi token hệ thống sang Page access token. System User token thường đăng được
trực tiếp nên script lùi về token gốc nếu edge này không trả về gì.

---

## Đăng ảnh

### `POST /{page-id}/photos`

| Tham số | Bắt buộc | Ghi chú |
|---------|----------|---------|
| `source` | có | File nhị phân (multipart) |
| `url` | — | Thay cho `source`, ảnh phải công khai trên Internet |
| `caption` | — | Nội dung bài |
| `published` | — | `false` khi hẹn giờ hoặc khi upload ảnh cho album |
| `scheduled_publish_time` | — | Unix timestamp, đi kèm `published=false` |

Trả về `{"id": "<photo_id>", "post_id": "<page_id>_<post>"}`. Ảnh upload với
`published=false` **không có** `post_id` — nó chỉ là media chờ ghép.

Giới hạn: định dạng JPEG/PNG/GIF/BMP/TIFF, khuyến nghị dưới 10MB, cạnh dài tối
đa 8000px.

---

## Đăng album nhiều ảnh

Hai giai đoạn, không có endpoint một phát.

**Giai đoạn 1** — với mỗi ảnh: `POST /{page-id}/photos` kèm `published=false`,
thu lấy `id`.

**Giai đoạn 2** — `POST /{page-id}/feed`:

| Tham số | Ghi chú |
|---------|---------|
| `message` | Nội dung bài |
| `attached_media[0]` | Chuỗi JSON `{"media_fbid":"<photo_id>"}` |
| `attached_media[1]` | ... đánh số liên tục từ 0 |
| `published` | `false` khi hẹn giờ |
| `scheduled_publish_time` | Unix timestamp |

Trả về `{"id": "<page_id>_<post_id>"}`.

Giới hạn: tối đa **10** phần tử `attached_media`. Thứ tự trong bài đúng bằng
thứ tự index.

---

## Đăng video feed

### Cách 1 — file nhỏ (script dùng khi < 100MB)

`POST /{page-id}/videos`

| Tham số | Ghi chú |
|---------|---------|
| `source` | File nhị phân (multipart) |
| `description` | Nội dung bài |
| `title` | Tiêu đề video |
| `published` / `scheduled_publish_time` | Hẹn giờ |

### Cách 2 — file lớn, chia chunk (script dùng khi >= 100MB)

Ba pha trên cùng endpoint `POST /{page-id}/videos`:

1. `upload_phase=start`, `file_size=<bytes>`
   → trả `upload_session_id`, `video_id`, `start_offset`, `end_offset`
2. Lặp `upload_phase=transfer` với `upload_session_id`, `start_offset`, và
   `video_file_chunk` (multipart). Mỗi lần trả `start_offset`/`end_offset`
   mới; dừng khi `start_offset == end_offset`.
3. `upload_phase=finish` với `upload_session_id` + `description`/`title` +
   tham số hẹn giờ nếu có.

Giới hạn: tối đa 10GB, 4 giờ. Khuyến nghị MP4 (H.264 + AAC).

---

## Đăng Reels

Quy trình riêng, **không hỗ trợ hẹn giờ**.

**Bước 1** — `POST /{page-id}/video_reels` với `upload_phase=start`
→ trả `video_id` và `upload_url`.

**Bước 2** — `POST {upload_url}` (host `https://rupload.facebook.com`, không
phải graph.facebook.com):

| Header | Giá trị |
|--------|---------|
| `Authorization` | `OAuth {page_access_token}` |
| `offset` | `0` |
| `file_size` | Số byte của file |

Body là toàn bộ file nhị phân, không multipart.

**Bước 3** — `POST /{page-id}/video_reels`:

| Tham số | Giá trị |
|---------|---------|
| `upload_phase` | `finish` |
| `video_id` | Từ bước 1 |
| `video_state` | `PUBLISHED` (hoặc `DRAFT`) |
| `description` | Nội dung bài |

Yêu cầu media: MP4/MOV, tỉ lệ 9:16, độ dài 3–90 giây, tối thiểu 540×960,
khuyến nghị 1080×1920. Meta cần vài phút xử lý trước khi Reels hiện lên Page.

---

## Quản lý bài đã hẹn giờ

### `GET /{page-id}/scheduled_posts`

`fields=id,message,scheduled_publish_time,created_time`. Cần scope
`pages_read_user_content`.

Dự phòng khi edge này không dùng được: `GET /{page-id}/feed` với
`is_published=false` cho kết quả tương đương.

### `POST /{post-id}`

| Tham số | Tác dụng |
|---------|----------|
| `scheduled_publish_time` | Dời sang giờ khác |
| `is_published=true` | Đăng ngay bài đang chờ |
| `message` | Sửa nội dung |

### `DELETE /{post-id}`

Xoá bài. Với bài đã hẹn giờ, đây là cách huỷ lịch.

---

## Ràng buộc hẹn giờ

| Ràng buộc | Giá trị |
|-----------|---------|
| Sớm nhất | 10 phút kể từ lúc gọi API |
| Muộn nhất | 6 tháng kể từ lúc gọi API |
| Định dạng | Unix timestamp (giây, UTC) |
| Bắt buộc đi kèm | `published=false` |

---

## Đặc tả media của Meta

Bảng đối chiếu khi chuẩn bị file. `ffprobe` trong skill kiểm được độ dài, độ
phân giải và tỉ lệ; các mục còn lại phải tự xác nhận.

| Vị trí | Tỉ lệ | Kích thước khuyến nghị | Độ dài |
|--------|-------|------------------------|--------|
| Ảnh feed | 1:1 hoặc 4:5 | 1080×1080 / 1080×1350 | — |
| Ảnh ngang | 1.91:1 | 1200×628 | — |
| Video feed | 1:1, 4:5, 16:9 | 1080×1080 trở lên | 1 giây – 4 giờ |
| Reels | 9:16 | 1080×1920 | 3–90 giây |
| Stories | 9:16 | 1080×1920 | tối đa 60 giây |

| Loại | Định dạng | Dung lượng tối đa |
|------|-----------|-------------------|
| Ảnh | JPEG, PNG, GIF, BMP, TIFF | ~10MB khuyến nghị |
| Video | MP4, MOV (H.264 + AAC) | 10GB |
