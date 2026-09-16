# Workflow — từ BRIEF tới Reels giao đi

1. Viết `videos/<ten-video>/BRIEF.md` (workflow, message, aspect 1080x1920, audience).
2. Chuẩn bị `transcript.json` (word-level `{text,start,end}`) + copy `frame.md` brand + viết `edit.yaml` theo `templates/talking-head-reels/edit.example.yaml`.
3. Sinh composition: `python templates/talking-head-reels/build.py --project videos/<ten-video>` → `index.html`.
4. Đọc skill theo thứ tự `AGENTS.md`: `hyperframes` → `motion-doctrine` → `ak-hyperframes` → domain → `hyperframes-core`.
5. Soi trước render: `npx hyperframes check`, `npx hyperframes snapshot` hoặc `preview --background`.
6. Render: `npx hyperframes render -f 30 -q high --strict -o videos/<ten-video>/renders/{YYMMDD}-{page}-{slug}.mp4`.
7. Soi sau render: `scripts/probe-mp4.sh <file> 1080x1920 30`, rút frame + `scripts/contact-sheet.sh`, check checklist `ak-hyperframes/references/pipeline.md` (dấu Việt, safe-zone, cấm từ, nhạc không nuốt giọng).
8. Giọng/nhạc: ưu tiên `<audio>` trong composition (`ak-elevenlabs` cho giọng Việt). Chỉ dùng ffmpeg khi ghép hậu kỳ.
9. Đăng: `ak-fb-page-publish` với page BSDQ|PTTM|ATCYK|Sua. Caption ra file, truyền `@caption.txt`.
10. Dọn: `npx hyperframes preview --stop`.

Video cũ `mo-thua-sau-tet-reels` dùng `videos/.../scripts/build.py` đóng băng riêng (CHUNKS/PUNCHES hardcode) — video mới đi theo template chung `templates/talking-head-reels/`.
