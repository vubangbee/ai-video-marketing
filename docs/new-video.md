# Tạo video mới — hướng dẫn từng bước

Mỗi video là 1 thư mục trong `videos/<ten-video>/`. Làm theo đúng thứ tự, chỗ nào
có `<ten-video>` thì thay bằng tên video của bạn (chữ thường, gạch nối, ví dụ `tri-mun-tham-my`).

## Bước 1 — Dựng khung thư mục (1 lệnh)

```bash
python scripts/new-video.py <ten-video>
```

Lệnh này tạo `videos/<ten-video>/` với `assets/`, `renders/` và copy sẵn:
`hyperframes.json`, `package.json`, `meta.json` (id/name đúng tên video),
`frame.md` (brand), `edit.yaml` (mẫu). Tên chỉ gồm chữ thường, số, gạch nối.

## Bước 2 — Bỏ video gốc vào `assets/`

Copy file bác sĩ quay (dọc, tốt nhất 1080x1920) thành `videos/<ten-video>/assets/source.mp4`.
Trong `edit.yaml`, `source:` và `duration:` phải khớp file này
(`duration` = độ dài giây của video, xem bằng cách mở file lên coi).

## Bước 3 — Làm `transcript.json`

File này là lời thoại chi tiết tới từng từ, để phụ đề bám đúng miệng nói.
Định dạng:

```json
{"words": [{"text": "Mỡ", "start": 0.0, "end": 0.25}, {"text": "thừa", "start": 0.25, "end": 0.5}]}
```

Cách lấy: xuất transcript từ CapCut/Premiere/whisper rồi chuyển về định dạng trên
(start/end tính bằng giây). Tiếng Việt ASR hay sai tên riêng và từ y khoa
("tiết"→"Tết", "nổ chậm"...) — soát tay trước khi đi tiếp.

## Bước 4 — Viết `BRIEF.md`

Ghi rõ video này nói gì, cho ai xem, đăng đâu. Mẫu tối thiểu:

```md
---
workflow: general-video
message: "Một câu: xem xong viewer làm gì"
destination: reels
aspect: 1080x1920
language: vi
length: 60s
audience: "Ai xem"
---

## Intent
Video talking-head của bác sĩ về ..., giữ nguyên lời nói, phụ đề cụm ngắn,
card chữ lớn ở các ý chính.
```

## Bước 5 — Viết `edit.yaml` (phần việc chính)

Mở `videos/<ten-video>/edit.yaml` (copy từ mẫu) và sửa:

- **captions** — phụ đề, mỗi dòng `[từ_đầu, từ_cuối, "chữ hiện", "chữ highlight"]`.
  Chỉ số là **số thứ tự từ trong transcript.json, không phải giây**.
  Cụm ngắn 3–5 từ, highlight 1 từ/cụm. Phụ đề = nguyên văn lời bác sĩ.
- **punches** — `[giây, độ zoom]`, zoom nhanh ở ranh giới câu cho đỡ buồn ngủ
  (ví dụ `[3.88, 1.12]` rồi trả về `[8.0, 1.0]`).
- **cards** — thẻ chữ lớn ở ý chính: `plate` (tiêu đề), `sub`, `pills` (gạch đầu dòng),
  `stamp` (con dấu như "MIỄN PHÍ"), `arrow: down` (mũi tên CTA).
- **lower_third** — bảng tên bác sĩ hiện lúc đầu.
- **end_card_cut** — giây video gốc cắt sang end card (nếu có), để phụ đề nhảy lên cao.

Nhớ 3 luật brand khi viết chữ hiện lên màn hình:
chữ quan trọng trong dải y 260–1450; màu nhấn chỉ 1 chỗ/cảnh;
cấm "cam kết 100%", "không đau", "an toàn tuyệt đối", "tốt nhất...".

## Bước 6 — Sinh `index.html`

```bash
python templates/talking-head-reels/build.py --project videos/<ten-video>
```

Lệnh này đọc `frame.md + edit.yaml + transcript.json` và đẻ ra `index.html`.
**Không sửa tay `index.html`** — sai thì sửa `edit.yaml` rồi chạy lại lệnh.

## Bước 7 — Kiểm tra trước khi render

```bash
cd videos/<ten-video>
npm run check                        # bắt buộc: 0 error mới đi tiếp
npx hyperframes preview --background # mở preview xem thử
```

Duyệt kỹ preview: dấu tiếng Việt đủ không, chữ có lọt vùng cấm không,
câu chữ có dính từ cấm không. Xem xong thì `npx hyperframes preview --stop`.

## Bước 8 — Render

```bash
npx hyperframes render -f 30 -q high --strict -o renders/{YYMMDD}-{page}-{slug}.mp4
```

Ví dụ: `renders/260916-BSDQ-tri-mun.mp4` (`YYMMDD` = ngày đăng, page = mã fanpage).
Cờ `--strict` bắt render fail khi có lỗi — luôn giữ.

## Bước 9 — Soi file render

```bash
cd ../..   # về gốc repo
scripts/probe-mp4.sh videos/<ten-video>/renders/<file>.mp4 1080x1920 30
```

Phải ra `✓ spec OK` (1080x1920, h264, 30fps). Rồi rút vài frame soi mắt:

```bash
for t in 0 1.5 3 6; do ffmpeg -y -ss $t -i videos/<ten-video>/renders/<file>.mp4 -frames:v 1 frame-$t.png; done
scripts/contact-sheet.sh sheet.png frame-*.png
```

Fail chỗ nào → sửa `edit.yaml` → quay lại **bước 6**. Không chữa bằng ffmpeg.

## Tóm tắt vòng lặp

```
sửa edit.yaml → build.py → npm run check → preview → render → probe-mp4
```

Chi tiết kỹ thuật đầy đủ xem `docs/workflow.md`; brand chuẩn xem
`brands/dr-dac-quang/frame.md`.
