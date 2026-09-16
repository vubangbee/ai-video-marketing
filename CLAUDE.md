# CLAUDE.md — AI Video Marketing

Repo Reels 9:16 Dr. Đắc Quang + HyperFrames. Mọi quy ước ở `AGENTS.md` — file này chỉ thêm phần Claude-specific.

## Skills (Claude Code đọc ở đây)

Mirror đầy đủ tại `.claude/skills/` (giống hệt `.agents/skills/`):

- `ak-hyperframes` (+ `references/setup.md`, `brand-video.md`, `pipeline.md`)
- `ak-video`, `ak-elevenlabs`
- 26 skill upstream: `hyperframes` (router), `motion-doctrine`, `hyperframes-core`, `general-video`, `motion-graphics`, `talking-head-recut`, `embedded-captions`, `media-use`, ...

Thứ tự bắt buộc: `hyperframes` → `motion-doctrine` → `ak-hyperframes` → domain skill → `hyperframes-core`.
Brand chuẩn: `brands/dr-dac-quang/frame.md`. Tóm tắt guardrails: `.claude/rules/brand-guardrails.md`.

## Lệnh

```bash
npx hyperframes check
npx hyperframes preview --background   # xong nhớ --stop
npx hyperframes render -f 30 -q high --strict -o videos/<ten-video>/renders/<file>.mp4
scripts/probe-mp4.sh videos/<ten-video>/renders/<file>.mp4 1080x1920 30
```

Quy trình chi tiết: `docs/workflow.md`.
