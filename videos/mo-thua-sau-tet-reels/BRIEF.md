---
workflow: general-video
flow: automation
storyboard: no
message: "Mỡ thừa sau Tết là bom nổ chậm cho sức khỏe — đăng ký tầm soát miễn phí với BS Đắc Quang"
destination: reels
aspect: 1080x1920
language: vi
length: 72s
audience: "Nữ 30+ quan tâm mỡ thừa vùng thân trên sau Tết"
---

## Intent

Edit video talking-head quay thật (1536×1920, 71.7s) của BS Đắc Quang thành Reels 9:16
1080×1920. Giữ nguyên toàn bộ lời nói (user chốt), reframe crop giữa, phụ đề cụm 3–5 từ
có highlight từ khóa (user chốt), card chữ lớn tại các ý chính, punch-in zoom làm chuyển
cảnh tại ranh giới câu, SFX đồng bộ với card/zoom.

## Assets

- `assets/source.mp4` — bản sao video gốc `../../mo thu sau tet.mp4` (audio lấy trực tiếp từ file này; file `.MP3` cùng tên là cùng track, không dùng thêm)
- Transcript word-level: tái dùng timing từ `../../Video marketing/MỠ THỪA SAU TẾT 04022026(2)/mo-thua-sau-tet-ink/transcript.json`, chữ sửa tay (ASR sai: "tiết"→"Tết", "bác thị quan"→"bác sĩ Quang", "nội chọc"→"nổ chậm"…)
- SFX: thư viện bundled của media-use (`.media/audio/sfx`, ledger `.media/manifest.jsonl`)
- Font: Be Vietnam Pro (local TTF, `assets/fonts/`)

## Customizations

- Không nhạc nền (user không yêu cầu — có thể thêm sau)
- Brand: Trust Blue #1E73BE cho card, amber #F59E0B chỉ cho từ khóa highlight / stamp "MIỄN PHÍ"
- Khung an toàn: chữ trong dải y 260–1450; card ở vùng ngực (y ~660–980), phụ đề đáy ~1420

## Notes

- Không thêm câu chữ vi phạm QC y tế; card chỉ trích lại lời bác sĩ, không bịa cam kết.
- Render chỉ sau khi user duyệt preview.
- `scripts/build.py` sinh `index.html` từ dữ liệu phụ đề/card — sửa ở script, không sửa tay HTML.
