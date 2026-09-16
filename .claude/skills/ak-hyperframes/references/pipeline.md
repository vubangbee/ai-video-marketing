# Sau khi render: tiếng, soi lỗi, đăng bài

## 1. Âm thanh — ưu tiên làm trong composition

HyperFrames **có** hỗ trợ audio: đặt `<audio>` ngay trong composition, mixer của
framework lo cắt và trộn theo timeline.

```html
<!-- Mỗi <audio> BẮT BUỘC có id, nếu không lint báo media_missing_id và bản render sẽ im lặng -->
<audio id="vo-01" src="./audio/voice.mp3" data-start="0"></audio>
<audio id="bgm"    src="./audio/bgm.mp3"  data-volume="0.18"></audio>
```

Cân âm lượng giữa giọng đọc và nhạc nền bằng lệnh có sẵn (đo LUFS, chỉ sửa `data-volume`,
trần +12 dB):

```bash
npx hyperframes normalize-audio
```

Nhạc nền dưới giọng đọc để khoảng `0.12–0.20`. To hơn là nuốt giọng, nhất là khi
khán giả xem bằng loa điện thoại.

**Chỉ dùng ffmpeg khi** phải ghép tiếng vào một file MP4 đã render xong (ví dụ giọng
ElevenLabs làm sau, hoặc video quay thật):

```bash
ffmpeg -i video.mp4 -i voice.mp3 -c:v copy -c:a aac -shortest out.mp4

# trộn giọng + nhạc nền rồi ghép
ffmpeg -i video.mp4 -i voice.mp3 -i bgm.mp3 \
  -filter_complex "[2:a]volume=0.18[b];[1:a][b]amix=inputs=2:duration=first[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac out.mp4
```

Giọng đọc tiếng Việt sinh bằng `ak:elevenlabs`. CLI có sẵn lệnh `tts` nhưng chạy bằng
model Kokoro cục bộ (chưa cài, và giọng Việt kém hơn) — cứ dùng ElevenLabs. Nghe lại
trước khi ghép: AI đọc sai tên riêng và thuật ngữ y khoa là chuyện thường.

**Phụ đề:** lệnh `npx hyperframes transcribe` cần whisper-cpp — máy chưa có. Hiện tại
gõ lời thoại tay rồi đưa vào workflow `embedded-captions`. Kể cả khi cài whisper,
tiếng Việt vẫn phải soát lại tay.

## 2. Soi bản render — bắt buộc, không được bỏ

Dùng script có sẵn của `ak:motion-graphics`, đường dẫn tương đối từ gốc dự án:

Soi **trước khi render** cho nhanh (render lại tốn thời gian):

```bash
npx hyperframes snapshot          # chụp các khung chính từ composition ra PNG
npx hyperframes check             # lint + validate runtime + layout
```

Soi **sau khi render**, trên chính file giao đi:

```bash
# 1. Kiểm tra thông số thật của file — kèm khẳng định 1080x1920 @30fps, sai thì script fail
scripts/probe-mp4.sh videos/<ten-video>/renders/<file>.mp4 1080x1920 30

# 2. Rút khung tại các mốc giây (đổi mốc theo cảnh của mình)
for t in 0 1.5 3 6; do ffmpeg -y -ss $t -i videos/<ten-video>/renders/<file>.mp4 -frames:v 1 frame-$t.png; done

# 3. Ghép thành 1 ảnh để nhìn cả loạt trong một lần
scripts/contact-sheet.sh sheet.png frame-*.png
```

**Đừng dùng `seek-shot.sh` cho composition HyperFrames.** Script đó cần harness `?t=N`
của pack iart-ai (trang tự `tl.pause(); tl.seek(t)` khi load) — HyperFrames không có,
runtime của nó tự nắm việc seek. Muốn soi trước khi render thì dùng
`npx hyperframes preview`; muốn soi sau khi render thì rút khung từ MP4 như trên.

Danh sách soi (fail cái nào thì sửa composition rồi render lại, đừng chữa bằng ffmpeg):

- [ ] Đúng 1080×1920, 30fps, có track audio nếu video có tiếng
- [ ] Không có khung trắng/đen ở đầu và cuối
- [ ] Dấu tiếng Việt hiện đủ, không bị cắt ngọn, không ô vuông
- [ ] Chữ quan trọng nằm trong dải y 260–1450
- [ ] Số điện thoại, giá, tên dịch vụ đọc được khi thu nhỏ bằng lòng bàn tay
- [ ] Không có câu chữ trong danh sách cấm ở `brand-video.md`
- [ ] Nhạc nền không nuốt giọng đọc

## 3. Bàn giao sang fanpage

Đặt file đúng chỗ trước:

```
videos/<ten-video>/renders/{YYMMDD}-{page}-{slug}.mp4
```

Đăng bằng `ak:fb-page-publish` (page hợp lệ: `BSDQ`, `PTTM`, `ATCYK`, `Sua`):

```bash
# Reels đăng ngay
python .agents/skills/ak-fb-page-publish/scripts/fb_page_publish.py publish-reel \
  --page BSDQ --video videos/mo-thua-sau-tet-reels/renders/260910-BSDQ-nang-mui-hoi-dap.mp4 --message "@caption.txt"

# Reels hẹn giờ — dùng publish-video --schedule với chính file dọc 9:16 đó,
# Meta vẫn xếp thành Reel (xem SKILL.md của ak:fb-page-publish)
python .agents/skills/ak-fb-page-publish/scripts/fb_page_publish.py publish-video \
  --page BSDQ --video videos/mo-thua-sau-tet-reels/renders/260910-BSDQ-nang-mui-hoi-dap.mp4 \
  --title "..." --message "@caption.txt" --schedule "10/09 19:30"
```

Thêm `--dry-run` để thử trước. Caption viết ra file rồi truyền bằng `@caption.txt` —
truyền chuỗi dài có dấu thẳng trên dòng lệnh PowerShell dễ hỏng mã hoá.

## 4. Dọn dẹp

```bash
npx hyperframes preview --stop
```

Đừng để server preview chạy nền sau khi xong việc.
