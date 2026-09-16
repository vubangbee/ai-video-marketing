# Cấp quyền cho skill ak:fb-page-publish

Hai hệ thống cần cấu hình: token Meta (để đăng bài) và service account Google
(để đọc media/nội dung từ Drive). Làm một lần, dùng mãi.

---

## Phần 1 — Token Meta

### Hiện trạng đã kiểm tra (2026-09-08)

Token đang dùng chung với skill `ak:ads-management`:

| Mục | Giá trị |
|-----|---------|
| Loại | `SYSTEM_USER` |
| Hạn dùng | Không hết hạn |
| Scope đang có | `pages_show_list`, `pages_read_engagement`, `pages_manage_ads`, `ads_management`, `ads_read`, `business_management`, `catalog_management`, `manage_app_solution`, `public_profile`, các scope WhatsApp/Threads |
| **Scope còn thiếu** | **`pages_manage_posts`**, `pages_read_user_content` |
| Page truy cập được | 7 page, tất cả có task `CREATE_CONTENT` |

Thiếu `pages_manage_posts` thì mọi lệnh đăng trả về lỗi `(#200)`. Task
`CREATE_CONTENT` ở cấp tài sản là **chưa đủ** — scope ở cấp token là thứ Graph
API kiểm tra khi nhận request.

### Các bước cấp thêm scope

1. Mở **business.facebook.com** → chọn Business Portfolio đang quản lý các page.
2. **Business Settings** (bánh răng góc trái dưới).
3. **Users → System Users** → chọn system user đang dùng.
4. Kiểm tra tài sản trước: **Add Assets → Pages** → chọn đủ 7 page → bật
   **Manage Page** (hoặc tối thiểu **Create Content**) → **Save Changes**.
5. Bấm **Generate New Token**.
6. Chọn app đang dùng (cùng app với `META_APP_ID` trong
   `.claude/skills/ak-ads-management/scripts/.env`).
7. Tick thêm hai scope:
   - `pages_manage_posts` — bắt buộc, để tạo và sửa bài
   - `pages_read_user_content` — để `list-scheduled` đọc được bài đang chờ
8. **Giữ nguyên** các scope quảng cáo đang có (`ads_management`, `ads_read`,
   `business_management`) — bỏ đi sẽ làm hỏng skill `ak:ads-management`.
9. Bấm **Generate Token**, copy ngay (chỉ hiện một lần).

### Dán token vào đâu

**Quyết định 08/09/2026: dán vào `.env` riêng của skill này** —
`.claude/skills/ak-fb-page-publish/scripts/.env`, khoá `META_ACCESS_TOKEN`.
Giá trị ở đây được ưu tiên hơn token của `ak:ads-management`.

Lý do tách riêng: token quảng cáo và token đăng bài có vòng đời khác nhau. Khi
một bên phải cấp lại token, bên còn lại không bị kéo đổ theo.

Không dán token vào bất kỳ file nào khác, và không đưa token vào lệnh trên
dòng lệnh — chỉ đặt trong `.env`.

### Page chưa nằm trong System User

`check-auth` in `TOKEN KHONG THAY PAGE NAY` nghĩa là page có trong `.env` nhưng
chưa được gán cho System User. Sửa: Business Settings → **Pages** → chọn page →
**Assign Partners/People** → chọn system user → bật **Manage Page** → Save.
Nếu page chưa thuộc Business Portfolio nào thì phải **Add Page** vào Business
trước.

Chiều ngược lại, `check-auth` cũng in mục *"Page token thay nhung chua co trong
.env"* — dùng chính Page ID ở đó để thêm page mới vào `.env`, thay vì đi tìm ID
bằng cách khác.

### Xác minh

```bash
python scripts/fb_page_publish.py check-auth
```

Đúng khi: `Scope bat buoc: DU`, `Scope khuyen nghi: DU`, cả 7 page hiện
`OK (CREATE_CONTENT)`, exit code 0.

### Bảng lỗi Meta

| Mã | Thông điệp | Nguyên nhân | Cách sửa |
|----|-----------|-------------|----------|
| `200` | `Permissions error` | Token thiếu `pages_manage_posts` | Làm lại các bước trên |
| `10` | `application does not have permission` | App chưa được duyệt quyền Page | Kiểm tra App Review, hoặc dùng System User trong cùng Business |
| `190` | `Error validating access token` | Token hết hạn / bị thu hồi / đổi mật khẩu | Tạo token mới |
| `100` + `scheduled_publish_time` | Giờ hẹn không hợp lệ | Đặt lại trong khoảng 10 phút – 6 tháng |
| `1363030` | `Video upload failed` | File hỏng, codec lạ, hoặc quá dài | Chuyển sang MP4 H.264 + AAC |
| `368` | Tạm khoá do vi phạm chính sách | Page bị hạn chế đăng bài | Kiểm tra Page Quality trong Meta Business Suite |

---

## Phần 2 — Service account Google (đọc Drive)

### Hiện trạng đã kiểm tra (2026-09-08)

| Mục | Giá trị |
|-----|---------|
| Key file | `D:\VubangDigital\api\google-sheets-api.json` (dùng chung với `ak:google-sheets`) |
| Email service account | `meta-ads-dashboard@exemplary-works-490106-b2.iam.gserviceaccount.com` |
| Project | `exemplary-works-490106-b2` (số hiệu `1081936233779`) |
| **Google Drive API** | **Đang TẮT** — mọi lệnh Drive trả 403 |

### Bước 1 — Bật Google Drive API

1. Mở <https://console.cloud.google.com/apis/library/drive.googleapis.com?project=1081936233779>
2. Bấm **Enable**.
3. Đợi 1–2 phút để cấu hình lan truyền.

### Bước 2 — Share dữ liệu cho service account

Service account là một tài khoản riêng, **không tự thấy Drive của bạn**. Với
mỗi folder media và mỗi file Google Docs chứa nội dung:

1. Chuột phải trên Drive → **Share**.
2. Dán `meta-ads-dashboard@exemplary-works-490106-b2.iam.gserviceaccount.com`.
3. Chọn quyền **Viewer** (đủ dùng — skill chỉ đọc, không ghi).
4. Bỏ tick "Notify people" rồi **Share**.

Mẹo: share nguyên một folder gốc dùng cho marketing, mọi file bên trong tự kế
thừa quyền — không phải share lại từng file.

Nếu dữ liệu nằm trong **Shared Drive**, phải thêm service account làm thành
viên của chính Shared Drive đó, share từng file không có tác dụng.

### Xác minh

```bash
python scripts/drive_client.py whoami
python scripts/drive_client.py read-doc --url <link google docs đã share>
```

Đúng khi `Drive API : OK` và `read-doc` in ra nội dung tài liệu.

### Bảng lỗi Google

| Thông báo | Nguyên nhân | Cách sửa |
|-----------|-------------|----------|
| `Google Drive API dang TAT` | Chưa bật API | Bước 1 ở trên |
| `Khong thay file/folder id` | Sai id, hoặc chưa share | Bước 2 ở trên |
| `Khong co quyen doc file id` | Share thiếu, hoặc file trong Shared Drive | Thêm service account vào Shared Drive |
| `Khong tim thay file key Google` | Sai `GOOGLE_DRIVE_CREDENTIALS` | Sửa đường dẫn trong `.env` |
