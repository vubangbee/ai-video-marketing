# -*- coding: utf-8 -*-
"""Generate index.html for the Reels edit from word-level transcript timings.

Caption chunks, highlight cards, punch-in cuts and SFX cues are declared here;
the script writes the HyperFrames composition. Re-run after editing any data:

    python scripts/build.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDS = json.load(open(os.path.join(ROOT, "transcript.json"), encoding="utf-8"))["words"]
DURATION = 71.7

# (first word idx, last word idx, corrected text, highlighted phrase)
CHUNKS = [
    (0, 3, "Mỡ thừa sau Tết", "Mỡ thừa"),
    (4, 8, "không chỉ là vấn đề", ""),
    (9, 11, "xấu hay đẹp,", ""),
    (12, 14, "nó là một", ""),
    (15, 18, "quả bom nổ chậm", "bom nổ chậm"),
    (19, 24, "cho sức khỏe của các bạn", "sức khỏe"),
    (25, 29, "Phụ nữ, đặc biệt là", ""),
    (30, 34, "phụ nữ sau tuổi 30", "sau tuổi 30"),
    (35, 39, "thì tốc độ tích mỡ", "tích mỡ"),
    (40, 45, "đặc biệt là vùng thân trên", "thân trên"),
    (46, 50, "diễn ra rất là nhanh", "nhanh"),
    (51, 53, "do ảnh hưởng", ""),
    (54, 59, "các vấn đề về nội tiết,", "nội tiết"),
    (60, 62, "về việc làm,", "việc làm"),
    (63, 67, "về thời gian ăn uống", "ăn uống"),
    (68, 73, "Các bệnh lý về chuyển hóa", "chuyển hóa"),
    (74, 77, "như tiểu đường,", "tiểu đường"),
    (78, 80, "tăng mỡ máu,", "mỡ máu"),
    (81, 87, "và các vấn đề về tim mạch", "tim mạch"),
    (88, 92, "sẽ xuất hiện từ đấy", ""),
    (93, 96, "Là một bác sĩ,", ""),
    (97, 102, "thì bác sĩ Quang mong muốn", "bác sĩ Quang"),
    (103, 108, "các bạn không chỉ có đẹp,", "đẹp"),
    (109, 112, "có tính thẩm mỹ,", "thẩm mỹ"),
    (113, 118, "mà còn có những an toàn,", "an toàn"),
    (119, 123, "bền vững và lâu dài", "bền vững"),
    (124, 128, "Do đó, chương trình", ""),
    (129, 134, "tầm soát mỡ thừa sau Tết", "tầm soát mỡ thừa"),
    (135, 138, "hoàn toàn miễn phí", "miễn phí"),
    (139, 143, "Cái này là tâm huyết", "tâm huyết"),
    (144, 147, "bên bác sĩ Quang", ""),
    (148, 152, "để giúp cho chị em", ""),
    (153, 156, "hiểu đúng, chính xác,", "hiểu đúng"),
    (157, 163, "đọc vị được cơ thể mình", "đọc vị"),
    (164, 168, "Các bạn sẽ nhận được", ""),
    (169, 179, "những kết quả đo lường chính xác", "chính xác"),
    (180, 185, "Các vấn đề, nhất là về", ""),
    (186, 188, "mỡ nội tạng,", "mỡ nội tạng"),
    (189, 195, "về các chỉ số khối BMI", "BMI"),
    (196, 198, "của cơ thể", ""),
    (199, 205, "Rồi là các vùng tích tụ mỡ,", "tích tụ mỡ"),
    (206, 209, "các vùng mỡ khó", ""),
    (210, 213, "giải quyết được bằng", ""),
    (214, 219, "ăn uống hoặc là tập luyện", "tập luyện"),
    (220, 224, "Chương trình tầm soát này,", "tầm soát"),
    (225, 230, "bác sĩ Quang chỉ dành cho", ""),
    (231, 234, "những ai thực sự", ""),
    (235, 239, "quan tâm đến bản thân mình", "bản thân"),
    (240, 243, "Và nhớ nhấn đăng ký", "đăng ký"),
    (244, 247, "ở phía dưới", ""),
    (248, 250, "Bác sĩ Quang", ""),
    (251, 257, "sẽ giúp các bạn lên kế hoạch", "kế hoạch"),
    (258, 259, "dáng đẹp,", "dáng đẹp"),
    (260, 266, "giảm mỡ thừa một cách an toàn,", "an toàn"),
    (267, 272, "hiệu quả và khoa học nhất", "khoa học"),
    (273, 277, "Đặt lịch ngày hôm nay", "Đặt lịch"),
    (278, 284, "để giữ được ưu đãi đặc biệt", "ưu đãi đặc biệt"),
    (285, 290, "từ Dr. Đắc Quang nhé", "Dr. Đắc Quang"),
]

# Camera punch-ins: (time, scale) — snap zooms at sentence boundaries
PUNCHES = [
    (3.88, 1.12), (8.0, 1.0), (16.72, 1.10), (22.52, 1.0), (30.64, 1.14),
    (35.18, 1.0), (40.98, 1.10), (49.12, 1.0), (54.74, 1.12), (59.56, 1.0),
]

# the source cuts to its own animated end card here; captions ride higher over it
END_CARD_CUT = 68.03

# SFX cues: (time, file, volume)
SFX = [(t, "whoosh-short", 0.3) for t, _ in PUNCHES] + [
    (3.88, "impact-bass", 0.4),     # "quả bom nổ chậm"
    (18.72, "pop", 0.35), (19.28, "pop", 0.35), (21.10, "pop", 0.35),  # 3 risk pills
    (33.64, "impact-bass", 0.45),   # MIỄN PHÍ stamp lands
    (33.70, "sparkle", 0.3),
    (45.98, "pop", 0.35), (48.02, "pop", 0.35), (49.76, "pop", 0.35),  # 3 result pills
    (60.18, "chime", 0.35),         # CTA đăng ký
    (68.03, "whoosh-short", 0.3),   # source cut → end card
]


def t(i):
    return WORDS[i]["start"]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def caption_html():
    out = []
    for n, (s, e, text, hl) in enumerate(CHUNKS):
        start = WORDS[s]["start"]
        end = WORDS[e]["end"]
        # hold until the next chunk starts (gap ≤ 0.6s), so the rail never flickers
        if n + 1 < len(CHUNKS):
            nxt = WORDS[CHUNKS[n + 1][0]]["start"]
            end = nxt if nxt - end <= 0.6 else end + 0.3
        else:
            end = DURATION
        body = esc(text)
        if hl:
            body = body.replace(esc(hl), '<span class="hl">%s</span>' % esc(hl), 1)
        cls = "clip cap high" if end > END_CARD_CUT else "clip cap"
        out.append(
            '      <div class="%s" id="cap-%02d" data-start="%.2f" data-duration="%.2f" data-track-index="3">'
            '<div class="cap-inner">%s</div></div>' % (cls, n, start, end - start, body)
        )
    return "\n".join(out)


# bundled-library durations (s) and a lane per family so overlapping cues never share a track
SFX_DUR = {"whoosh-short": 0.57, "pop": 0.72, "impact-bass": 2.12, "chime": 2.5, "sparkle": 1.8}
SFX_TRACK = {"whoosh-short": 12, "impact-bass": 13, "pop": 14, "chime": 16, "sparkle": 16}


def sfx_html():
    out = []
    pops = 0
    for n, (time, name, vol) in enumerate(sorted(SFX)):
        track = SFX_TRACK[name]
        if name == "pop":  # consecutive pops overlap each other, alternate lanes
            track += pops % 2
            pops += 1
        out.append(
            '      <audio id="sfx-%02d" src="assets/sfx/%s.mp3" data-start="%.2f" data-duration="%.2f" data-track-index="%d" data-volume="%.2f"></audio>'
            % (n, name, time, SFX_DUR[name], track, vol)
        )
    return "\n".join(out)


def punch_js():
    lines = []
    for time, scale in PUNCHES:
        lines.append('      tl.to("#cam", { scale: %.2f, duration: 0.28, ease: "power3.out" }, %.2f);' % (scale, time))
    return "\n".join(lines)


TEMPLATE = r"""<!doctype html>
<!-- GENERATED by scripts/build.py — edit the script, then re-run it. -->
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face { font-family: "Be Vietnam Pro"; font-weight: 400; src: url("assets/fonts/BeVietnamPro-Regular.ttf") format("truetype"); }
      @font-face { font-family: "Be Vietnam Pro"; font-weight: 700; src: url("assets/fonts/BeVietnamPro-Bold.ttf") format("truetype"); }
      @font-face { font-family: "Be Vietnam Pro"; font-weight: 800; src: url("assets/fonts/BeVietnamPro-ExtraBold.ttf") format("truetype"); }
      @font-face { font-family: "Be Vietnam Pro"; font-weight: 900; src: url("assets/fonts/BeVietnamPro-Black.ttf") format("truetype"); }

      :root {
        --blue: #1e73be;
        --blue-deep: #155a96;
        --amber: #f59e0b;
        --ink: #111827;
        --paper: #ffffff;
        --scrim: rgba(17, 24, 39, 0.62);
        --font: "Be Vietnam Pro", system-ui, sans-serif;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: #0b1220; }
      #root { position: relative; width: 100%; height: 100%; overflow: hidden; font-family: var(--font); color: var(--paper); }

      /* ---- footage: reframed 4:5 → 9:16 by centre crop, punch-ins on the wrapper ---- */
      #cam { position: absolute; inset: 0; width: 100%; height: 100%; transform-origin: 50% 28%; }
      #a-roll { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 50% 50%; }
      #vignette { position: absolute; inset: 0; pointer-events: none;
        background: linear-gradient(180deg, rgba(11,18,32,0.35) 0%, rgba(11,18,32,0) 22%, rgba(11,18,32,0) 62%, rgba(11,18,32,0.55) 100%); }

      /* ---- caption rail: bottom edge at y=1420, inside the 260–1450 safe band ---- */
      .cap { position: absolute; left: 80px; right: 80px; bottom: 500px; display: flex; justify-content: center; }
      .cap.high { bottom: 780px; } /* over the source end card, clear of its own title text */
      .cap-inner { display: block; width: max-content; max-width: 920px; padding: 18px 34px; border-radius: 22px;
        background: var(--scrim); font-size: 58px; font-weight: 800; line-height: 1.3; text-align: center; letter-spacing: 0;
        color: var(--paper); text-shadow: 0 2px 10px rgba(0,0,0,0.45); }
      .cap-inner .hl { color: var(--amber); }

      /* ---- overlay cards live in the chest band (y 820–1150), clear of the face even when punched in ---- */
      .card { position: absolute; left: 80px; right: 80px; top: 820px; display: flex; flex-direction: column; align-items: center; gap: 18px; }
      .card > * { display: block; }
      .plate { display: block; width: max-content; max-width: 920px; padding: 22px 44px; border-radius: 24px; background: var(--blue);
        font-size: 74px; font-weight: 900; line-height: 1.25; text-align: center; color: var(--paper); box-shadow: 0 18px 50px rgba(11,18,32,0.35); }
      .plate.small { font-size: 46px; font-weight: 700; padding: 14px 32px; background: var(--ink); }
      .plate.amber { background: var(--amber); color: var(--ink); font-size: 96px; padding: 20px 56px; }
      .pill { display: block; width: max-content; padding: 16px 40px; border-radius: 999px; background: var(--paper); color: var(--ink);
        font-size: 52px; font-weight: 800; line-height: 1.3; box-shadow: 0 12px 30px rgba(11,18,32,0.3); }
      .pill.warn { background: var(--ink); color: var(--paper); }
      .pill .tick { color: var(--blue); margin-right: 10px; }

      /* lower-third name plate, left-anchored */
      #name-plate { position: absolute; left: 80px; top: 860px; display: flex; flex-direction: column; align-items: flex-start; gap: 0; }
      #name-plate .name { display: block; width: max-content; padding: 16px 32px; background: var(--blue); font-size: 54px; font-weight: 900; line-height: 1.3; border-radius: 16px 16px 0 0; }
      #name-plate .role { display: block; width: max-content; padding: 10px 32px; background: var(--paper); color: var(--ink); font-size: 34px; font-weight: 700; line-height: 1.3; border-radius: 0 0 16px 16px; }

      .arrow { display: block; width: 120px; height: 120px; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.4)); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="__DURATION__" data-width="1080" data-height="1920" data-fps="30">

      <div id="cam">
        <video id="a-roll" class="clip" src="assets/source.mp4" data-start="0" data-duration="__DURATION__" data-track-index="0" muted playsinline></video>
      </div>
      <div id="vignette"></div>
      <audio id="voice" src="assets/source.mp4" data-start="0" data-duration="__DURATION__" data-track-index="10" data-volume="1"></audio>

      <!-- hook title, before the first card -->
      <div class="clip card" id="card-hook" data-start="0" data-duration="3.2" data-track-index="5">
        <div class="plate">MỠ THỪA SAU TẾT</div>
      </div>

      <!-- "quả bom nổ chậm" -->
      <div class="clip card" id="card-bomb" data-start="3.88" data-duration="3.3" data-track-index="5">
        <div class="plate">QUẢ BOM NỔ CHẬM</div>
        <div class="plate small">cho sức khỏe</div>
      </div>

      <!-- lower-third name plate -->
      <div class="clip" id="name-plate" data-start="8.0" data-duration="6.0" data-track-index="5">
        <div class="name">BS. Trần Đắc Quang</div>
        <div class="role">Bác sĩ phẫu thuật thẩm mỹ</div>
      </div>

      <!-- three metabolic risks -->
      <div class="clip card" id="card-risk" data-start="18.46" data-duration="4.06" data-track-index="5">
        <div class="pill warn" id="risk-1">Tiểu đường</div>
        <div class="pill warn" id="risk-2">Tăng mỡ máu</div>
        <div class="pill warn" id="risk-3">Tim mạch</div>
      </div>

      <!-- the offer -->
      <div class="clip card" id="card-offer" data-start="31.5" data-duration="3.68" data-track-index="5">
        <div class="plate" id="offer-title">TẦM SOÁT MỠ THỪA SAU TẾT</div>
        <div class="plate amber" id="offer-free">MIỄN PHÍ</div>
      </div>

      <!-- what the screening measures -->
      <div class="clip card" id="card-results" data-start="45.9" data-duration="4.9" data-track-index="5">
        <div class="pill" id="res-1"><span class="tick">✓</span>Mỡ nội tạng</div>
        <div class="pill" id="res-2"><span class="tick">✓</span>Chỉ số BMI</div>
        <div class="pill" id="res-3"><span class="tick">✓</span>Vùng tích tụ mỡ</div>
      </div>

      <!-- CTA: register below -->
      <div class="clip card" id="card-cta" data-start="60.18" data-duration="2.5" data-track-index="5">
        <div class="plate">NHẤN ĐĂNG KÝ</div>
        <svg class="arrow" id="cta-arrow" viewBox="0 0 100 100" aria-hidden="true"><path d="M50 10 V78 M20 50 L50 82 L80 50" fill="none" stroke="#f59e0b" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </div>

      <!-- captions:start -->
__CAPTIONS__
      <!-- captions:end -->

__SFX__
    </div>

    <script>
      document.fonts.ready.then(() => {
        const tl = gsap.timeline({ paused: true });

        // ---- camera punch-ins (snap zooms) ----
__PUNCHES__

        // ---- caption rail: each chunk pops in on its own start ----
        document.querySelectorAll(".cap").forEach((clip) => {
          const at = parseFloat(clip.dataset.start);
          tl.fromTo(clip.querySelector(".cap-inner"), { opacity: 0, scale: 0.86, y: 14 }, { opacity: 1, scale: 1, y: 0, duration: 0.2, ease: "back.out(2)" }, at);
        });

        // ---- cards: plates slam in, pills stagger on the spoken word ----
        const slam = (sel, at, dur = 0.32) =>
          tl.fromTo(sel, { opacity: 0, scale: 0.7, y: 30 }, { opacity: 1, scale: 1, y: 0, duration: dur, ease: "back.out(1.8)" }, at);
        const exit = (sel, at) => tl.to(sel, { opacity: 0, y: -24, duration: 0.22, ease: "power2.in" }, at);

        slam("#card-hook .plate", 0.05); exit("#card-hook .plate", 2.95);
        slam("#card-bomb .plate", 3.88, 0.3); exit("#card-bomb > *", 6.95);
        tl.fromTo("#name-plate > *", { opacity: 0, x: -60 }, { opacity: 1, x: 0, duration: 0.4, stagger: 0.1, ease: "power3.out" }, 8.0);
        tl.to("#name-plate > *", { opacity: 0, x: -40, duration: 0.3, ease: "power2.in" }, 13.6);

        slam("#risk-1", 18.72, 0.28); slam("#risk-2", 19.28, 0.28); slam("#risk-3", 21.10, 0.28);
        exit("#card-risk .pill", 22.3);

        slam("#offer-title", 31.6, 0.35);
        tl.fromTo("#offer-free", { opacity: 0, scale: 2.2, rotation: -8 }, { opacity: 1, scale: 1, rotation: -4, duration: 0.3, ease: "power4.out" }, 33.64);
        tl.to("#offer-free", { scale: 1.06, duration: 0.5, ease: "sine.inOut", yoyo: true, repeat: 1 }, 34.0);
        exit("#card-offer > *", 34.95);

        slam("#res-1", 45.98, 0.28); slam("#res-2", 48.02, 0.28); slam("#res-3", 49.76, 0.28);
        exit("#card-results .pill", 50.55);

        slam("#card-cta .plate", 60.18, 0.3);
        tl.fromTo("#cta-arrow", { opacity: 0, y: -30 }, { opacity: 1, y: 0, duration: 0.3, ease: "power2.out" }, 60.4);
        tl.to("#cta-arrow", { y: 22, duration: 0.35, ease: "sine.inOut", yoyo: true, repeat: 3 }, 60.7);
        exit("#card-cta > *", 62.45);

        window.__timelines["main"] = tl;
        if (window.__hfForceTimelineRebind) window.__hfForceTimelineRebind();
      });
    </script>
  </body>
</html>
"""


def main():
    html = (
        TEMPLATE.replace("__DURATION__", "%.1f" % DURATION)
        .replace("__CAPTIONS__", caption_html())
        .replace("__SFX__", sfx_html())
        .replace("__PUNCHES__", punch_js())
    )
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("wrote index.html: %d captions, %d sfx cues, %d punch-ins" % (len(CHUNKS), len(SFX), len(PUNCHES)))


if __name__ == "__main__":
    main()
