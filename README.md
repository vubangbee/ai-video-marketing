# AI Video Marketing — Reels Dr. Đắc Quang

Repo dựng video Reels/TikTok 9:16 cho phòng khám: lấy video bác sĩ quay thật,
thêm phụ đề + thẻ chữ + hiệu ứng zoom bằng HyperFrames, render ra MP4 đúng chuẩn nền tảng.

## Bắt đầu nhanh (video mới)

```bash
python scripts/new-video.py <ten-video>   # dựng khung project, vd: tri-mun-tham-my
```

Rồi làm theo từng bước trong **`docs/new-video.md`** (9 bước: bỏ video gốc vào,
viết lời thoại, viết edit, sinh HTML, kiểm tra, render, soi file).

Vòng lặp hàng ngày chỉ có vậy:

```
sửa edit.yaml → build.py → npm run check → preview → render → probe-mp4
```

## Cấu trúc repo

| Thư mục/file | Để làm gì |
|---|---|
| `videos/<ten-video>/` | 1 video = 1 thư mục: `BRIEF.md`, `transcript.json`, `edit.yaml`, `index.html`, `assets/`, `renders/` |
| `brands/dr-dac-quang/` | Chuẩn brand duy nhất (`frame.md`: màu, font, vùng an toàn, từ cấm) + font/SFX/logo |
| `templates/talking-head-reels/` | Khuôn chung sinh `index.html` (`build.py`, `index.template.html`, `edit.example.yaml`) |
| `scripts/` | `new-video.py` (dựng project), `probe-mp4.sh` + `contact-sheet.sh` (soi file render) |
| `docs/` | `new-video.md` (hướng dẫn tạo video), `workflow.md` (quy trình kỹ thuật) |
| `.agents/skills/`, `.claude/skills/` | Spec cho AI agent (26 skill HyperFrames + 3 skill nhà) — người không cần đọc |

## Quy tắc quan trọng nhất

- Sửa ở `edit.yaml`, **không sửa tay `index.html`** sinh ra.
- Chữ quan trọng nằm trong dải an toàn y 260–1450; font và màu lấy từ `frame.md`.
- Phụ đề = nguyên văn lời bác sĩ. Không dùng từ cam kết ("khỏi hẳn", "không đau", "tốt nhất...").
- Luôn `npm run check` (0 error) + soi file render trước khi coi là xong.

Chi tiết cho AI agent xem `AGENTS.md`.
