---
name: ak:hyperframes
description: Dựng video từ HTML bằng HyperFrames (HeyGen) cho phòng khám — Reels/TikTok 9:16, lower-third, phụ đề, intro/outro — theo brand DR Đắc Quang, chữ tiếng Việt an toàn, rồi ghép tiếng và soi lỗi bản render. Dùng khi user nói "dựng video bằng HyperFrames", "làm reels từ HTML", "video chữ động", "thêm lower-third/phụ đề vào video bác sĩ".
argument-hint: "[loại-video] [--page BSDQ|PTTM|ATCYK|Sua]"
license: MIT
metadata:
  author: vubangdigital.com
  version: "1.1.0"
  status: ready
  verified_cli: "hyperframes 0.8.33 (2026-09-09)"
---

# HyperFrames cho video phòng khám

Skill này **không dạy lại cách viết composition**. HeyGen đã ship 26 skill chính chủ
(Apache 2.0) làm việc đó, đã cài tại `.agents/skills/`, và chúng cập nhật theo phiên bản
CLI. Skill này chỉ lo phần upstream không biết: **brand DR Đắc Quang, chữ tiếng Việt,
khung an toàn 9:16, ghép tiếng và soi lỗi bản render.**

<args>$ARGUMENTS</args>

## Phạm vi

Xử lý: Reels/TikTok 9:16 cho phòng khám; lower-third, phụ đề, intro/outro chèn vào
video quay thật của bác sĩ; ghép giọng đọc + nhạc; kiểm tra chất lượng bản render;
đặt file đúng `videos/<ten-video>/renders/{YYMMDD}-{page}-{slug}.mp4`.

Không xử lý: viết kịch bản (dùng `ak:video`), chạy quảng cáo (`ak:ads-management`),
video React/Remotion (`ak:remotion` — Remotion tính phí Company License từ 4 người,
HyperFrames Apache 2.0).

## Kiểm tra trước khi bắt đầu

```bash
node --version            # cần >= 22. Máy này dùng nvm: `nvm use 24.19.0` nếu ra v20
npx hyperframes doctor
```

Trạng thái đã xác minh 2026-09-09: Node 24.19.0 ✅, ffmpeg 9.0.1 ✅, Chrome hệ thống ✅.
Thiếu (tuỳ chọn): whisper-cpp → **chưa tự sinh phụ đề được**; Kokoro TTS và MusicGen →
dùng `ak:elevenlabs` thay thế. Xem `references/setup.md`.

## Vào việc: luôn đi qua router upstream

```
skill `hyperframes` (bắt buộc, đọc đầu tiên — nó chọn workflow và tự nạp skill kỹ thuật)
   └─ trước khi viết animation: skill `motion-doctrine`
```

Bảng route cho hai việc của mình:

| Việc | Skill upstream |
|---|---|
| Reels ngắn, chữ động, không lời dẫn | `motion-graphics` |
| Reels nhiều cảnh, có lời dẫn | `general-video` |
| Lower-third / khung số liệu / trích dẫn đè lên video bác sĩ | `talking-head-recut` |
| Phụ đề cho video bác sĩ | `embedded-captions` + `captions-overlay` |
| Nhạc nền, tiếng động, ảnh, giọng đọc | `media-use` |

Đừng tự đoán luật composition — đọc `hyperframes-core` của upstream.

## Trước khi viết HTML: nạp ràng buộc của mình

Đọc `references/brand-video.md` — màu brand, font tiếng Việt, cỡ chữ, khung an toàn 9:16,
câu chữ bị cấm theo quy định quảng cáo y tế.

## Lệnh render đã xác minh (CLI 0.8.33)

```bash
npx hyperframes check                       # lint + validate runtime + layout, một cổng
npx hyperframes preview --background        # xem thử, nhớ --stop khi xong

# Reels 9:16 — tỉ lệ nằm TRONG composition, không phải ở cờ dòng lệnh
# Quy ước output repo này: videos/<ten-video>/renders/
npx hyperframes render -f 30 -q high --strict \
  -o videos/mo-thua-sau-tet-reels/renders/260910-BSDQ-nang-mui-hoi-dap.mp4

# Lower-third / phụ đề để chèn lên video quay thật → xuất nền trong suốt
npx hyperframes render --format mov  -o overlay.mov    # ProRes 4444, giữ alpha
npx hyperframes render --format webm -o overlay.webm   # nhẹ hơn, cho web

# Nhiều biến thể hook/CTA từ 1 composition — mỗi dòng JSON ra 1 file
npx hyperframes render --batch rows.json --resolution portrait --strict
```

**Muốn 9:16 thì khai trong composition, không phải ở cờ render** (đã thử và bị chặn):

```html
<meta name="viewport" content="width=1080, height=1920" />
<div data-composition-id="main" data-width="1080" data-height="1920" data-fps="30" data-duration="10">
```

`--resolution` **chỉ phóng to** theo bội số nguyên cùng tỉ lệ (`portrait-4k`, `4k`…).
Truyền `--resolution portrait` cho composition 1920×1080 thì render fail ngay với thông báo
"does not match the aspect ratio" — đó là hàng rào tốt, đừng cố lách.

`--strict` bắt render fail khi lint lỗi — luôn bật, đừng để video hỏng lọt qua.

## Bốn quy tắc riêng của dự án

1. **Tiếng có dấu quyết định font.** Cặp font trong `references/brand-video.md` chọn theo
   bộ chữ Việt đầy đủ. Font brand (Inter) dùng cho web/tài liệu, không dùng cho chữ lớn.
2. **Chữ quan trọng không được nằm dưới UI của Meta** — khung an toàn 9:16 bắt buộc.
3. **Không câu chữ vi phạm quảng cáo y tế** — danh sách cấm trong `references/brand-video.md`.
4. **Chưa soi bản render thì chưa xong** — checklist trong `references/pipeline.md`.

## Đặt tên file output

```
videos/<ten-video>/renders/{YYMMDD}-{page}-{slug}.mp4
```
Brand chuẩn duy nhất: `brands/dr-dac-quang/frame.md` (frontmatter là chuẩn).
`references/brand-video.md` chỉ là bản tóm tắt, lệch thì theo `frame.md`.

## Tham chiếu

| File | Khi nào đọc |
|------|-------------|
| `references/setup.md` | Node/nvm, doctor báo thiếu, bảng lệnh CLI đầy đủ, sự cố |
| `references/brand-video.md` | Trước khi viết bất kỳ composition nào |
| `references/pipeline.md` | Sau khi có MP4: ghép tiếng, soi lỗi |
