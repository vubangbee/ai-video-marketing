# Brand, chữ tiếng Việt và khung an toàn cho video

> Nguồn chuẩn duy nhất của repo này: `brands/dr-dac-quang/frame.md`
> (frontmatter là giá trị chuẩn để `templates/talking-head-reels/build.py` đọc).
> File này là bản tóm tắt để đọc nhanh trước khi render — lệch thì theo `frame.md`.

Đọc file này **trước khi viết composition**. Bản web/tài liệu (nếu có) chỉ tham khảo.

## Màu — giữ nguyên, không đổi

| Vai trò | Hex | Dùng trên video |
|---|---|---|
| Trust Blue | `#1E73BE` | Nền khối nhấn, thanh lower-third, viền CTA |
| Slate Gray | `#64748B` | Chữ phụ, chú thích trên nền sáng |
| Golden Amber | `#F59E0B` | **Chỉ dùng để nhấn 1 chi tiết/cảnh** — giá, con số, từ khoá |
| Text Primary | `#111827` | Chữ trên nền sáng |
| Nền sáng | `#FFFFFF` / `#F9FAFB` | Nền cảnh sạch |

Quy tắc video: chữ trắng đặt trên Trust Blue đặc, **không** đặt chữ trắng lên ảnh/video
nền mà không có lớp phủ tối (`rgba(17,24,39,.55)`) hoặc gradient chân chữ. Trên điện
thoại ngoài nắng, chữ không có lớp phủ là mất chữ.

Amber là màu nhấn: một cảnh dùng amber cho **một** thứ. Dùng cho 3 thứ cùng lúc thì
mất tác dụng nhấn và trông rẻ tiền.

## Font — điểm lệch có chủ đích so với brand guideline

Brand quy định **Inter** cho web và tài liệu. Trên video **không dùng Inter cho chữ lớn**:

- Hướng dẫn thiết kế của HyperFrames liệt Inter vào nhóm font bị cấm cho composition
  (quá phổ biến, độ tương phản nét yếu ở cỡ lớn);
- video cần cặp nét tương phản mạnh (300 vs 900), Inter dùng ở cỡ 100px trông như UI
  chứ không như đồ hoạ.

Cặp thay thế — **Be Vietnam Pro** (thiết kế cho tiếng Việt, bộ dấu đầy đủ, có đủ 100→900):

```css
/* Nạp kèm subset vietnamese, luôn kiểm tra dấu hiển thị đúng trước khi render */
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;700;900&display=swap');

:root {
  --font-display: 'Be Vietnam Pro', system-ui, sans-serif;  /* 900 — tiêu đề */
  --font-body:    'Be Vietnam Pro', system-ui, sans-serif;  /* 300/400 — nội dung */
}
```

Inter vẫn dùng được cho **chữ nhỏ dạng UI** trong video (nhãn, watermark, đơn vị).

**Quyết định này lệch khỏi `docs/brand-guidelines.md` §2 và chỉ áp dụng cho video.**
Nếu sếp/khách yêu cầu giữ Inter cho mọi thứ thì báo lại đánh đổi, đừng tự đổi ngược.

**Determinism:** timeline chỉ được đăng ký sau `document.fonts.ready`, nếu không frame
đầu render bằng font dự phòng → mỗi lần render một khác.

## Chữ tiếng Việt — 5 lỗi hay gặp

1. **Dấu bị cắt ngọn.** `line-height` tối thiểu **1.25** cho tiêu đề (chữ Latin không dấu
   để 1.0 được, tiếng Việt thì không). Chữ hai tầng dấu (ế, ộ, ữ) cần chỗ.
2. **VIẾT HOA TOÀN BỘ câu dài có dấu** → khó đọc và dấu chồng nhau. Chỉ viết hoa từ khoá
   ngắn (≤ 3 từ).
3. **Font thiếu bộ Việt** → hiện ô vuông hoặc rơi về font dự phòng. Luôn xác nhận font
   có subset `vietnamese` trước khi dùng.
4. **Ngắt dòng giữa cụm từ** ("chăm / sóc", "hồi phục một / khác"). Ngắt tay ở ranh giới
   có nghĩa, đừng để trình duyệt tự ngắt. **Không dùng `<br>`** — HyperFrames cấm trong
   body text; mỗi dòng là một `<div>` riêng, dòng nối tiếp cùng câu đặt
   `margin-top` hẹp (6px) để không trông như đoạn mới.
5. **`letter-spacing` âm** làm dính dấu vào chữ bên cạnh. Tiếng Việt để `0` hoặc dương nhẹ.

## Cỡ chữ tại 1080×1920

| Vai trò | Cỡ | Nét |
|---|---|---|
| Hook / tiêu đề chính | 96–130px | 900 |
| Tiêu đề phụ | 64–80px | 700 |
| Nội dung | 40–52px | 300/400 |
| Nhãn, đơn vị, ghi chú | 28–34px | 400 |

Dưới 28px trên màn hình điện thoại là không đọc được — đừng dùng.

## Khung an toàn 9:16 (Reels / TikTok)

Canvas `1080 × 1920`. UI của nền tảng đè lên trên và dưới:

```
y 0    ─────────────  ⛔ 0–260px    : nút quay lại, tên tài khoản
y 260  ─────────────  ✅ vùng an toàn
                       chữ quan trọng, mặt người, số điện thoại
y 1450 ─────────────  ⛔ 1450–1920 : caption, nút CTA, tên nhạc, dàn nút phải
y 1920 ─────────────
```

- Lề trái/phải tối thiểu **80px**; chừa thêm **160px** bên phải cho cột nút tim/chia sẻ.
- Logo: góc trên trái trong vùng an toàn, rộng tối thiểu **120px** (theo brand §3).
- Bảng giá, số điện thoại, địa chỉ: **luôn** đặt trong dải y 260–1450.

Video feed 1:1 hoặc 4:5 thì lề 60px là đủ, không có vùng cấm của Reels.

## Câu chữ bị cấm — kiểm tra trước khi render

Vi phạm quảng cáo y tế (Luật Quảng cáo, NĐ 38/2021, NĐ 117/2020):

- "Cam kết 100%", "chắc chắn đẹp", "không đau", "an toàn tuyệt đối", "khỏi hẳn"
- So sánh hạ thấp cơ sở khác ("tốt nhất Hà Nội", "hơn hẳn chỗ X")
- Ảnh before–after **không có văn bản đồng ý của khách** — kể cả ảnh đẹp, kể cả ca thật
- Danh xưng bác sĩ/bệnh viện ngoài phạm vi hành nghề đã cấp phép

Ngoài ra brand cấm: "Revolutionary", "Best-in-class", "Seamless".

Giọng cần đạt: chuyên môn nhưng dễ gần, trung thực, ngắn gọn — không hù doạ, không
bán hàng lộ liễu (`docs/brand-guidelines.md` §4).

## Ảnh và tư liệu

Ánh sáng tự nhiên, người thật, nền gọn. Giữ tông brand khi chỉnh màu. Không dùng ảnh
stock người nước ngoài cho ca "khách hàng của phòng khám" — khán giả nhận ra ngay.
