---
name: ak:fb-page-publish
description: Đăng ảnh, album, video và Reels lên fanpage Facebook qua Graph API — media lấy từ Google Drive, nội dung nhập trực tiếp hoặc lấy từ Google Docs, đăng ngay hoặc hẹn giờ bằng cơ chế native của Meta. Dùng khi user nói "đăng bài lên fanpage", "lên lịch bài viết", "post lên page", "đăng Reels", hoặc gọi tên một fanpage cụ thể.
argument-hint: "[page] [post-type]"
license: MIT
metadata:
  author: vubangdigital.com
  version: "1.0.0"
  status: ready
---

# Đăng bài fanpage Facebook

Đăng bài lên Facebook Page qua Graph API. Nội dung do người dùng cung cấp,
media lấy từ Google Drive. Không tạo nội dung thay người dùng.

## Phạm vi

Xử lý: đăng ảnh đơn, album nhiều ảnh, video feed, Reels; hẹn giờ và quản lý
bài đã hẹn; tải media và đọc caption từ Google Drive.

Không xử lý: Instagram, TikTok, viết nội dung bằng AI, chỉnh sửa ảnh/video,
trả lời comment và inbox, quảng cáo (dùng `ak:ads-management`).

## Cài đặt (một lần)

1. `pip install -r scripts/requirements.txt`
2. `cp scripts/.env.example scripts/.env` rồi sửa bảng fanpage nếu cần.
3. Cấp quyền cho token Meta — xem `references/setup-permissions.md`. Token cần
   scope `pages_manage_posts` và `pages_read_user_content`.
4. Bật Google Drive API và share folder media cho service account — hướng dẫn
   ở cuối `references/setup-permissions.md`.
5. Kiểm tra:
   ```bash
   python scripts/fb_page_publish.py check-auth
   python scripts/drive_client.py whoami
   ```
   Cả hai phải exit 0 trước khi đăng bài thật.

## Năm câu hỏi bắt buộc trước khi đăng

Hỏi đủ năm câu này trước khi chạy bất cứ lệnh đăng nào. Thiếu thông tin nào thì
hỏi lại đúng thông tin đó — **không đoán, không tự bịa nội dung, không tự chọn
page, không tự chọn giờ**.

1. **Đăng lên page nào?** Chạy `list-pages` và đưa bảng thật cho người dùng
   chọn. Chọn nhiều page thì truyền một lệnh duy nhất với các mã ngăn cách
   bằng dấu phẩy (`--page Sua,PTTM,ATCYK`) — không lặp lệnh.
2. **Định dạng bài là gì?** Ảnh đơn / album nhiều ảnh / video feed / Reels.
3. **Ảnh, video ở đâu?** Link file hoặc link folder trên Google Drive.
4. **Nội dung lấy từ đâu?** Link Google Docs, một ô trong Google Sheets, hay
   dán thẳng text.
5. **Đăng liền hay hẹn giờ?** Nếu hẹn, hỏi giờ cụ thể theo giờ Việt Nam.

Người dùng chọn Reels **và** muốn hẹn giờ: dùng `publish-video --schedule` với
chính file dọc 9:16 đó. Meta vẫn xếp thành Reel. Không cần hỏi lại, không đề
nghị họ đổi định dạng — xem mục Giới hạn đã biết.

## Luồng thực thi

```
list-pages  →  check-auth  →  drive_client fetch / fetch-folder
            →  lấy nội dung  →  SOÁT CHÍNH TẢ  →  [DUYỆT BẢN SỬA]
            →  publish-* --dry-run  →  [DUYỆT BÀI ĐĂNG]
            →  publish-* thật  →  báo permalink
```

## Soát chính tả — bắt buộc trước khi đăng

Không bao giờ đăng nội dung chưa qua bước này. Tự đọc và soát, không dùng
script — đây là việc cần hiểu ngữ nghĩa.

**Cần bắt:**

- Lỗi cơ học: khoảng trắng thừa đầu/cuối dòng, khoảng trắng đôi, thiếu hoặc
  thừa khoảng trắng quanh dấu câu, dòng trống thừa, ngoặc/nháy không cân
- Chính tả: sai dấu hỏi/ngã, sai từ, thiếu từ, lặp từ
- Viết hoa: tiếng Việt chỉ viết hoa chữ đầu câu và tên riêng. "Chuyên Khoa
  Thẩm Mỹ" sai, "Chuyên khoa Thẩm mỹ" đúng
- Thiếu nhất quán: trộn `–` (en dash) với `-` (hyphen), trộn nháy thẳng với
  nháy cong

**KHÔNG tính là lỗi** (quyết định 09/09/2026): emoji, hashtag, dòng tiêu đề
IN HOA, từ tiếng Anh xen kẽ (Inbox, combo), viết tắt ngành (BS, CKI, PTTH).
Đây là văn phong marketing có chủ đích — báo chúng lên chỉ gây nhiễu.

**Cách trình bày:** tách riêng "lỗi chắc chắn" và "điểm thiếu nhất quán".
Mỗi lỗi nêu số dòng, trích nguyên văn chỗ sai, và câu sửa đề xuất. Nói rõ
chỗ nào là quy tắc, chỗ nào là góp ý văn phong.

**Sau khi người dùng duyệt:** chỉ sửa vào **file caption tạm** dùng để đăng.
Không bao giờ ghi ngược lại Google Docs hay ô Sheets nguồn. Giữ một bản gốc
cạnh bên để đối chiếu. Người dùng bỏ sửa mục nào thì giữ nguyên mục đó.

Quy tắc bắt buộc:

- Soát chính tả trước, người dùng duyệt bản sửa xong mới sang `--dry-run`.
- Luôn chạy `--dry-run` trước, đưa bản xem trước cho người dùng đọc.
- Chỉ chạy lệnh đăng thật sau khi người dùng đồng ý rõ ràng trong lượt hiện
  tại. Sự đồng ý ở một bài trước không tính cho bài sau.
- Đăng lên nhiều page: một lệnh, một lần xác nhận. Bản xem trước liệt kê đủ
  tên từng page. Nếu một page lỗi, các page còn lại vẫn đăng và cuối lệnh
  báo rõ page nào hỏng.
- Sau khi đăng, báo lại `post_id`, giờ đăng và permalink (bài hẹn giờ chưa có
  permalink — báo cách xem lại bằng `list-scheduled`).
- `post_id` mà lệnh đăng in ra luôn ở dạng `{page_id}_{object_id}` và dùng
  thẳng được với `cancel` / `reschedule` / `publish-now`. Id trần không có
  dấu gạch dưới sẽ bị Graph API từ chối bằng `(#200)`.

## Lệnh

### Lấy dữ liệu từ Google Drive

```bash
python scripts/drive_client.py whoami
python scripts/drive_client.py fetch --url <link file> --out ./media
python scripts/drive_client.py fetch-folder --url <link folder> --types image --out ./media
python scripts/drive_client.py read-doc --url <link google docs> --out caption.txt
python scripts/drive_client.py read-cell --url <link sheets> --cell F19 --out caption.txt
```

`fetch` in ra JSON có trường `path` — đường dẫn file vừa tải, đưa thẳng vào
lệnh đăng.

`read-cell` đọc một ô Sheets. Giữ nguyên phần `#gid=...` trong link thì nó tự
nhận đúng tab; không có gid thì truyền `--sheet "Tên tab"`.

**Thứ tự ảnh trong album** — hỏi người dùng, đừng tự quyết:

| Cách gọi | Thứ tự |
|---|---|
| `--images-dir <folder>` | tự sắp tăng dần theo tên file |
| `--images a.jpg,b.jpg,c.jpg` | đúng thứ tự gõ, không sắp lại |

Ảnh ở vị trí đầu được Facebook cho vào ô lớn nhất của collage. Bộ có ảnh dọc
lẫn ảnh vuông thì đặt ảnh dọc lên đầu — nó chiếm cột trái, các ảnh vuông xếp
chồng bên phải. Đặt ảnh vuông lên đầu sẽ khiến ảnh dọc bị cắt rất nặng.
Facebook không có tham số bố cục; thứ tự là thứ duy nhất điều khiển được.

### Đăng bài

```bash
python scripts/fb_page_publish.py list-pages
python scripts/fb_page_publish.py check-auth

python scripts/fb_page_publish.py publish-photo --page Sua \
  --image ./media/anh.jpg --message "@caption.txt" --schedule "+2h" --dry-run

# Cùng một bài lên nhiều page, một lệnh một lần xác nhận:
python scripts/fb_page_publish.py publish-photo --page Sua,PTTM,ATCYK \
  --image ./media/anh.jpg --message "@caption.txt" --schedule "+2h"

python scripts/fb_page_publish.py publish-album --page PTTM \
  --images-dir ./media --message "Nội dung" --schedule "10/09 08:30"

python scripts/fb_page_publish.py publish-video --page ATCYK \
  --video ./media/clip.mp4 --title "Tiêu đề" --message "Nội dung" --schedule "+1d"

python scripts/fb_page_publish.py publish-reel --page BSDQ \
  --video ./media/reel.mp4 --message "Nội dung"
```

`--page` nhận một mã, hoặc nhiều mã ngăn cách bằng dấu phẩy. Trùng lặp được
gỡ tự động, nên `--page Sua,108067022357425` chỉ đăng một lần.

`--message` nhận text trực tiếp, hoặc `@đường/dẫn/file.txt` để đọc từ file —
dùng chung với output của `read-doc --out`.

`--schedule` nhận: `"2026-09-10 19:30"`, `"10/09/2026 19:30"`, `"10/09 19:30"`,
`"19:30"`, `"+2h"`, `"+90m"`, `"+3d"`. Giờ hiểu theo `DEFAULT_TIMEZONE`.

### Quản lý bài đã hẹn giờ

```bash
python scripts/fb_page_publish.py list-scheduled --page Sua
python scripts/fb_page_publish.py reschedule --post-id <id> --schedule "11/09 07:00"
python scripts/fb_page_publish.py publish-now --post-id <id>
python scripts/fb_page_publish.py cancel --post-id <id>
```

## Cấu hình

Mọi thông tin truy cập và danh sách fanpage nằm trong `scripts/.env`
(mẫu ở `scripts/.env.example`). Đổi page, thêm page, đổi token, đổi múi giờ
đều chỉ sửa file đó — không sửa code.

| Khoá | Ý nghĩa |
|------|---------|
| `META_ACCESS_TOKEN` | Token đăng bài của skill này. Bỏ trống thì lùi về kế thừa token của `ak:ads-management` — token đó thiếu `pages_manage_posts` nên sẽ không đăng được |
| `META_API_VERSION` | Mặc định `v21.0` |
| `FB_PAGE_CODE_N` / `FB_PAGE_ID_N` / `FB_PAGE_NAME_N` | Bảng fanpage, đánh số liên tục từ 1 |
| `GOOGLE_DRIVE_CREDENTIALS` | Đường dẫn service account JSON |
| `DRIVE_DOWNLOAD_DIR` | Nơi lưu media tải về; trống thì dùng thư mục temp |
| `FFPROBE_PATH` | Trống thì tự dò trong PATH và thư mục winget |
| `DEFAULT_TIMEZONE` | Mặc định `Asia/Bangkok` |

## Giới hạn đã biết

- **Hẹn giờ Reels: dùng `publish-video`, không dùng `publish-reel`.** Endpoint
  `/video_reels` không nhận `scheduled_publish_time`, nhưng cùng file dọc 9:16
  đăng qua `/videos` kèm giờ hẹn thì Meta vẫn xếp thành Reel (permalink dạng
  `/reel/...`). Xác minh trên 7 page ngày 09/09/2026. `publish-reel` chỉ dùng
  khi muốn đăng ngay.
- Hẹn giờ phải cách hiện tại **từ 10 phút đến 6 tháng**.
- Album tối đa **10 ảnh** một bài.
- `list-scheduled` cần scope `pages_read_user_content`; thiếu thì trả rỗng.
- Video Reels được kiểm độ dài, độ phân giải và tỉ lệ bằng ffprobe — chỉ cảnh
  báo, không chặn, vì Meta vẫn xử lý được một số trường hợp biên.
- Bài Reels đã đăng không huỷ bằng `cancel` được (nó lên sóng ngay); phải xoá
  thủ công trên Page.

## Xử lý lỗi thường gặp

| Triệu chứng | Nguyên nhân | Cách xử lý |
|-------------|-------------|------------|
| `code 200` / `code 10` | Token thiếu `pages_manage_posts` | `references/setup-permissions.md` |
| `code 190` | Token hết hạn hoặc bị thu hồi | Tạo token mới, cập nhật `.env` |
| `Google Drive API dang TAT` | Chưa bật Drive API | Bấm link trong thông báo lỗi |
| `Khong thay file/folder id` | Chưa share cho service account | `drive_client.py whoami` lấy email, share quyền Viewer |
| `list-scheduled` trả rỗng dù vừa hẹn | Thiếu `pages_read_user_content` | Cấp thêm scope |

## Chạy bằng agent khác

Gói portable ở `skill-packages/fb-page-publish/` chạy được với Codex, Gemini CLI
hay bất kỳ agent nào có quyền chạy shell. Codex đọc `AGENTS.md` chứ không đọc
`SKILL.md` — hướng dẫn cấu hình từng bước ở `references/setup-codex.md` của gói
đó, đặc biệt là mục bật network cho sandbox.

## Phụ thuộc

`scripts/requirements.txt`: `requests`, `python-dotenv`,
`google-api-python-client`, `google-auth`. Tuỳ chọn: `ffmpeg` (cho `ffprobe`).

Skill liên quan: `ak:ads-management` (cùng Meta app, token riêng),
`ak:google-sheets` (service account dùng chung).

## Bảo mật

- Không tiết lộ nội dung `.env`, token, hay đường dẫn nội bộ.
- Không đăng bài khi người dùng chưa xác nhận rõ ràng.
- Không bịa nội dung, không tự thêm hashtag hay call-to-action ngoài bản
  người dùng đưa.
- Sửa lỗi chính tả phải được duyệt từng mục, và chỉ sửa vào file caption tạm.
  Không bao giờ ghi đè Google Docs hay ô Sheets nguồn.
- Từ chối rõ ràng các yêu cầu ngoài phạm vi thay vì làm nửa vời.
