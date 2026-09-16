# Cài đặt và xử lý sự cố

## Yêu cầu

| Thành phần | Yêu cầu | Trạng thái máy hiện tại (2026-09-09) |
|---|---|---|
| Node.js | **>= 22** | ✅ v24.19.0 (npm 11.17.0) |
| FFmpeg | có trong PATH | ✅ 9.0.1-full_build |
| Chromium | CLI tự tải qua `hyperframes browser` | chưa kiểm tra |
| Giấy phép | Apache 2.0, miễn phí thương mại | ✅ |

## Node trên máy này do nvm-windows quản

PATH trỏ vào symlink `C:\nvm4w\nodejs`, **không** phải `C:\Program Files\nodejs`. Vì vậy
cài Node bằng winget/MSI sẽ không đổi được phiên bản đang chạy — phải dùng `nvm`:

```bash
nvm list                # xem các bản đang có, dấu * là bản đang dùng
nvm use 24.19.0         # chuyển sang Node 24 (đã cài sẵn)
nvm install 22          # chỉ khi cần thêm bản mới
```

Sau khi chuyển, **mở terminal mới**. Nếu vẫn đang trong shell cũ và gặp
`node: command not found`, chạy `hash -r` — bash đang nhớ đường dẫn cũ.

**Cảnh báo:** `nvm use` đổi Node cho **toàn máy**, không riêng dự án này. Dự án nào đang
khoá Node 20 sẽ chịu ảnh hưởng; quay lại bằng `nvm use 20.19.5`.

## Cài skill upstream

Repo này đã copy tĩnh **26 skill** vào `.agents/skills/` + mirror `.claude/skills/`
(gốc 2026-09-09 từ `heygen-com/hyperframes`, project scope, dùng được cho
Claude Code / Opencode / Cursor / Gemini CLI / Copilot).

```bash
npx skills add heygen-com/hyperframes     # cài lại hoặc cập nhật cả bộ
npx hyperframes skills                    # cài/refresh skill từ chính CLI
npx hyperframes skills update             # refresh skill đã cài khi CLI lên bản mới
```

Bộ skill gồm: router `hyperframes`; nhóm kỹ thuật (`hyperframes-core`, `-cli`,
`-animation`, `-keyframes`, `-audio`, `-creative`, `-registry`); nhóm doctrine chuyển cảnh
(`motion-doctrine`, `cut-the-curve`, `seam-craft`, `oversized-cursor`, `captions-overlay`);
nhóm theo loại video (`motion-graphics`, `general-video`, `talking-head-recut`,
`embedded-captions`, `slideshow`, `music-to-video`, `faceless-explainer`,
`product-launch-video`, `pr-to-video`, `changelog-video`, `remotion-to-hyperframes`,
`media-use`, `figma`).

**Luôn vào bằng router `hyperframes`.** Nó đọc trạng thái dự án (`BRIEF.md`,
`hyperframes.json`, `STORYBOARD.md`) và chọn workflow — gọi thẳng skill con dễ bỏ sót ràng buộc.
Trước khi viết animation, nạp thêm `motion-doctrine` (skill này tự nhận là gateway).

## Lệnh CLI — xác minh trên bản 0.8.33

| Nhóm | Lệnh |
|---|---|
| Bắt đầu | `init` `add` `capture` `catalog` `preview` `present` `publish` `render` |
| Kiểm tra | `check` (gộp lint + validate + inspect) · `lint` · `validate` · `inspect` · `snapshot` · `compare` · `grade-compare` · `keyframes` · `beats` |
| Media | `normalize-audio` · `media-treatment` · `transcribe` · `tts` · `remove-background` |
| Hệ thống | `doctor` · `browser` · `info` · `compositions` · `docs` · `benchmark` · `upgrade` |
| Đám mây | `cloud` (HeyGen) · `lambda` (AWS) · `cloudrun` (GCP) · `auth` |

Cờ render hay dùng: `-f 30` · `-q draft|standard|high` · `--strict` ·
`--format mp4|webm|mov|gif|png-sequence` · `--variables '{"title":"..."}'` ·
`--batch rows.json` · `-c <file.html>` · `-o <out>` · `-w auto`.

`--resolution` chỉ phóng to theo bội số nguyên **cùng tỉ lệ** (portrait-4k, 4k…). Tỉ lệ
khung do `data-width`/`data-height` trên root composition quyết định — đưa cờ lệch tỉ lệ
thì render dừng ngay với lỗi "does not match the aspect ratio".

Đã chạy thử toàn tuyến 2026-09-09: `init --example blank` → sửa root thành 1080×1920 →
`render -f 30 -q draft` ra MP4 10s trong 17.1s → `probe-mp4.sh out.mp4 1080x1920 30` báo
spec OK. Lần render đầu CLI tự tải Chrome riêng (~114 MB), nên lần đầu chạy sẽ lâu.

Cờ đổi theo phiên bản — khi CLI lên bản mới, chạy `npx hyperframes render --help`
rồi cập nhật lại file này thay vì đoán.

## Quản lý tiến trình preview

`preview --background` để lại server chạy nền. Theo quy tắc process của dự án:

```bash
npx hyperframes preview --list     # xem cái gì đang chạy
npx hyperframes preview --stop     # dừng khi xong việc
```

Dừng preview trước khi kết thúc phiên làm việc. Đừng để chạy tích tụ.

## Thành phần tuỳ chọn còn thiếu (doctor 2026-09-09)

| Thiếu | Mất khả năng gì | Cài nếu cần |
|---|---|---|
| whisper-cpp | `transcribe` — **không tự sinh phụ đề từ video bác sĩ được**, phải gõ tay hoặc dùng dịch vụ ngoài | build theo hướng dẫn whisper.cpp |
| Kokoro TTS | `tts` giọng đọc offline | `pip install kokoro-onnx soundfile` — hoặc bỏ qua, dùng `ak:elevenlabs` (giọng Việt tốt hơn) |
| MusicGen | sinh nhạc nền cục bộ | `pip install transformers torch soundfile numpy` — hoặc dùng nhạc có bản quyền sẵn |
| Docker | render deterministic trong container | không cần cho quy mô hiện tại |

Ba thứ đầu chỉ ảnh hưởng tiện ích, không chặn render. Riêng phụ đề tiếng Việt: whisper
nhận dạng tiếng Việt còn sai tên riêng và thuật ngữ y khoa — dù cài rồi vẫn phải soát tay.

## Sự cố thường gặp

| Hiện tượng | Nguyên nhân | Xử lý |
|---|---|---|
| Render lỗi ngay, log nhắc engine | Node < 22 | `nvm use 24.19.0`, mở terminal mới |
| Video ra **im lặng** | `<audio>` thiếu `id` | Thêm `id`; `lint` báo `media_missing_id` |
| Cảnh trống, không thấy nội dung | Sai luật scene/opacity của upstream | Đọc lại `hyperframes-core` upstream, đừng tự chế |
| Mỗi lần render ra khác nhau | Có `Date.now()`, `Math.random()` không seed, hoặc gọi mạng | Bỏ hết — HyperFrames yêu cầu deterministic |
| `doctor` báo thiếu trình duyệt | Chưa tải Chromium | `npx hyperframes browser` |
