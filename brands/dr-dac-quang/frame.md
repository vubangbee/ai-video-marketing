---
version: alpha
name: Dr. Đắc Quang — Frame (video / frame layer)
brand: dr-dac-quang
description: >
  Bản video-first của brand phòng khám thẩm mỹ Dr. Đắc Quang. Đơn vị là khung hình
  1080×1920 (Reels / TikTok). Token trong frontmatter là giá trị chuẩn, sao chép nguyên
  văn; phần chữ bên dưới là ngữ cảnh và ràng buộc. Chuyển động không thuộc phạm vi file này.
unit: the frame — 1080×1920 primary; 1080×1350 và 1080×1080 cho feed
principle: màu và font là bất biến · bố cục tự do · chữ trên video lấy từ lời bác sĩ, không bịa

colors:
  primary: "#1E73BE"        # Trust Blue — nền card, thanh lower-third, viền CTA
  primary-deep: "#155A96"
  accent: "#F59E0B"         # Golden Amber — MỘT điểm nhấn mỗi cảnh: từ khóa, giá, con số
  ink: "#111827"            # chữ trên nền sáng, pill tối
  muted: "#64748B"          # chữ phụ trên nền sáng
  paper: "#FFFFFF"
  canvas: "#F9FAFB"
  scrim: "rgba(17,24,39,0.62)"   # lớp phủ bắt buộc dưới chữ trắng đặt trên video

typography:
  family: "Be Vietnam Pro"  # bộ dấu tiếng Việt đầy đủ, có 100→900 (lệch có chủ đích khỏi Inter của brand web)
  fonts:                    # file theo weight, đường dẫn tương đối thư mục brand này
    400: fonts/BeVietnamPro-Regular.ttf
    700: fonts/BeVietnamPro-Bold.ttf
    800: fonts/BeVietnamPro-ExtraBold.ttf
    900: fonts/BeVietnamPro-Black.ttf
  hook:    { px: 96, weight: 900, lineHeight: 1.25 }
  title:   { px: 74, weight: 900, lineHeight: 1.25 }
  stamp:   { px: 96, weight: 900, lineHeight: 1.25 }
  caption: { px: 58, weight: 800, lineHeight: 1.3 }
  pill:    { px: 52, weight: 800, lineHeight: 1.3 }
  sub:     { px: 46, weight: 700, lineHeight: 1.3 }
  name:    { px: 54, weight: 900, lineHeight: 1.3 }
  label:   { px: 34, weight: 700, lineHeight: 1.3 }
  min-px: 28                # dưới 28px trên điện thoại là không đọc được
  letter-spacing: "0"       # tiếng Việt: không âm, dấu sẽ dính chữ bên cạnh

safe-zone:                  # 1080×1920 — UI của Reels/TikTok đè lên trên và dưới
  top: 260
  bottom: 1450
  side: 80
  right-extra: 160          # cột nút tim / chia sẻ bên phải

layout:                     # mặc định cho talking-head 9:16, bác sĩ ngồi giữa khung
  caption-bottom: 1420      # mép dưới pill phụ đề
  card-top: 820             # card highlight nằm ngang ngực, không đè mặt kể cả khi punch-in
  punch-origin: "50% 28%"   # tâm zoom quanh mặt

radii:
  card: "24px"
  caption: "22px"
  pill: "999px"
  name: "16px"

sfx:                        # thư viện SFX brand chọn sẵn (Pixabay Content License)
  whoosh: sfx/whoosh-short.mp3
  pop: sfx/pop.mp3
  impact: sfx/impact-bass.mp3
  chime: sfx/chime.mp3
  sparkle: sfx/sparkle.mp3
  volume: 0.35              # SFX luôn dưới giọng nói

identity:
  doctor: "BS. Trần Đắc Quang"
  role: "Bác sĩ phẫu thuật thẩm mỹ"
  short: "Dr. Đắc Quang"
  pages: [BSDQ, PTTM, ATCYK, Sua]     # mã page dùng trong tên file và ak:fb-page-publish
---

## Tổng quan

Phòng khám thẩm mỹ của bác sĩ phẫu thuật tạo hình. Giọng cần đạt: **chuyên môn nhưng dễ
gần, trung thực, ngắn gọn** — không hù dọa, không bán hàng lộ liễu. Video chủ yếu là
bác sĩ nói chuyện trực tiếp (talking-head) quay tại phòng khám, được dựng thành Reels.

## Màu

- Chữ trắng chỉ đặt trên Trust Blue đặc hoặc trên video có `scrim`. Trên điện thoại
  ngoài nắng, chữ trắng không có lớp phủ là mất chữ.
- Amber là màu nhấn: **một cảnh dùng amber cho một thứ** (từ khóa phụ đề, hoặc stamp
  "MIỄN PHÍ", hoặc con số). Dùng cho ba thứ cùng lúc là mất tác dụng và trông rẻ.
- Không gradient chữ, không neon, không tím-xanh.

## Chữ tiếng Việt — 5 lỗi phải tránh

1. `line-height` tối thiểu 1.25 cho tiêu đề — chữ hai tầng dấu (ế, ộ, ữ) cần chỗ.
2. Không VIẾT HOA câu dài có dấu. Chỉ viết hoa từ khóa ngắn (≤ 4 từ).
3. Font phải có subset `vietnamese` — luôn soi snapshot xem dấu hiện đủ trước khi render.
4. Ngắt dòng ở ranh giới có nghĩa; không dùng `<br>` — mỗi dòng là một `<div>`.
5. `letter-spacing` không âm.

## Khung an toàn 9:16

Chữ quan trọng, mặt người, số điện thoại, giá: **luôn trong dải y 260–1450**. Lề trái
phải 80px; chừa thêm 160px bên phải cho cột nút. Logo (khi có file thật) đặt góc trên
trái trong vùng an toàn, rộng ≥ 120px.

## Câu chữ bị cấm (Luật Quảng cáo, NĐ 38/2021, NĐ 117/2020)

- "Cam kết 100%", "chắc chắn đẹp", "không đau", "an toàn tuyệt đối", "khỏi hẳn"
- So sánh hạ thấp cơ sở khác ("tốt nhất Hà Nội", "hơn hẳn chỗ X")
- Ảnh before–after không có văn bản đồng ý của khách
- Danh xưng ngoài phạm vi hành nghề đã cấp phép
- Brand cấm thêm: "Revolutionary", "Best-in-class", "Seamless"

Phụ đề là lời bác sĩ nói, giữ nguyên văn. Card/overlay do agent viết thì **chỉ trích lại
ý bác sĩ đã nói**, không thêm cam kết.

## Ảnh và tư liệu

Ánh sáng tự nhiên, người thật, nền gọn. Không dùng ảnh stock người nước ngoài cho ca
"khách hàng của phòng khám". Giữ tông brand khi chỉnh màu.
