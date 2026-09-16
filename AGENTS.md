# AI Video Marketing — Dr. Đắc Quang Reels

Repo dựng Reels/TikTok 9:16 cho phòng khám từ video bác sĩ quay thật + HyperFrames.
Brand chuẩn duy nhất: `brands/dr-dac-quang/frame.md` (frontmatter là giá trị chuẩn).

## Skills — USE THESE FIRST

Skills là spec chuẩn, mirror 2 nơi (nội dung giống hệt nhau):
- Universal (Opencode / Cursor / Copilot / Gemini): `.agents/skills/*/SKILL.md`
- Claude Code: `.claude/skills/*/SKILL.md`

**Làm video HyperFrames? Luôn đi theo thứ tự này, không đoán:**

```
1. skill `hyperframes` (router upstream — bắt buộc, đọc đầu tiên, nó chọn workflow)
2. skill `motion-doctrine` (trước khi viết animation — gateway chuyển cảnh)
3. skill `ak-hyperframes` (ràng buộc riêng: brand, chữ Việt, safe-zone, soi lỗi, bàn giao)
   └─ đọc `references/brand-video.md`, rồi `brands/dr-dac-quang/frame.md`
4. skill domain theo bảng route trong `ak-hyperframes`:
   general-video | motion-graphics | talking-head-recut | embedded-captions | media-use
5. skill `hyperframes-core` khi viết composition (luật data-start, window.__timelines, deterministic)
```

Kịch bản → `ak-video`. Giọng đọc Việt → `ak-elevenlabs`. Soi file MP4 bằng
`scripts/probe-mp4.sh` và `scripts/contact-sheet.sh`.

## Quy ước repo

- `brands/dr-dac-quang/` — token màu/font/safe-zone/SFX. `frame.md` là chuẩn, đừng copy số lẻ vào HTML.
- `templates/talking-head-reels/` — `build.py + index.template.html + edit.example.yaml`.
  Sinh `index.html` từ `frame.md + edit.yaml + transcript.json`. Sửa ở `edit.yaml`, không sửa tay HTML sinh ra.
- `videos/<ten-video>/` — 1 project HyperFrames: `BRIEF.md`, `transcript.json`, `edit.yaml`,
  `index.html`, `assets/`, `renders/`. File `AGENTS.md`/`CLAUDE.md` trong đó là của CLI, vẫn tuân theo.
  Video mới: làm theo từng bước trong `docs/new-video.md`.
- `scripts/` — `probe-mp4.sh`, `contact-sheet.sh` (nguồn MIT: iart-ai/motion-skills, xem `scripts/LICENSE.motion-skills.txt`).
- Output: `videos/<ten-video>/renders/{YYMMDD}-{page}-{slug}.mp4` (page: BSDQ|PTTM|ATCYK|Sua).

## Commands

```bash
python scripts/new-video.py <ten-video>   # dựng khung project mới
python templates/talking-head-reels/build.py --project videos/<ten-video>
npx hyperframes check                       # cổng duy nhất: lint + validate + layout
npx hyperframes preview --background        # agent preview, xong nhớ --stop
npx hyperframes preview --stop
npx hyperframes render -f 30 -q high --strict -o videos/<ten-video>/renders/<file>.mp4
scripts/probe-mp4.sh videos/<ten-video>/renders/<file>.mp4 1080x1920 30
npx hyperframes doctor                      # khi render lỗi môi trường
npx hyperframes skills update               # refresh skill upstream khi CLI lên bản mới
```

Trong từng project con có thể dùng `npm run check` / `npm run render` (pin `hyperframes@x.y.z`).

## Key Rules

1. 9:16 khai TRONG composition (`data-width="1080" data-height="1920"`), không ở cờ render.
2. Chữ quan trọng trong dải y 260–1450, lề 80px, chừa 160px phải cho cột nút. Be Vietnam Pro, line-height ≥ 1.25, letter-spacing không âm, không `<br>` (mỗi dòng 1 `<div>`).
3. Amber `#F59E0B` 1 điểm nhấn/cảnh. Chữ trắng trên video phải có scrim `rgba(17,24,39,.62)` hoặc nền Trust Blue đặc.
4. Phụ đề = lời bác sĩ, giữ nguyên văn. Card chỉ trích lại ý đã nói — cấm "cam kết 100%", "không đau", "an toàn tuyệt đối", "tốt nhất...", before-after không consent (xem `frame.md`).
5. Deterministic: không `Date.now()`, `Math.random()`, fetch mạng. `<audio>` bắt buộc có `id`. Timeline đăng ký sau `document.fonts.ready`. Luôn `--strict`, luôn `check` + soi render trước khi giao.
