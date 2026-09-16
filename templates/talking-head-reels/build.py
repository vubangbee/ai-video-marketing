#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Talking-head Reels template: generate a HyperFrames index.html for one video project.

Inputs, all inside the project directory (default: current directory, or --project):
  frame.md         brand tokens — copied from brands/<brand>/frame.md (frontmatter is normative)
  transcript.json  word-level timings: {"words": [{"text","start","end"}, ...]}
  edit.yaml        this video's edit: caption chunks, cards, punch-ins, lower-third

Output: index.html, plus brand fonts/SFX synced into assets/fonts and assets/sfx.

    python ../../templates/talking-head-reels/build.py            # from the project dir
    python templates/talking-head-reels/build.py --project videos/<name>

Agent-agnostic: plain Python 3.11+ and PyYAML, no framework hooks.
"""
import argparse
import json
import os
import re
import shutil
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------------- inputs

def load_frame(project):
    """Parse frame.md frontmatter; returns (tokens, brand_dir)."""
    path = os.path.join(project, "frame.md")
    if not os.path.exists(path):
        sys.exit("frame.md not found in %s — copy one from brands/<brand>/frame.md" % project)
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        sys.exit("frame.md has no YAML frontmatter")
    tokens = yaml.safe_load(m.group(1))
    brand = tokens.get("brand")
    if not brand:
        sys.exit("frame.md frontmatter needs `brand: <dir name under brands/>`")
    # repo root = nearest ancestor holding brands/<brand>/
    d = os.path.abspath(project)
    while True:
        cand = os.path.join(d, "brands", brand)
        if os.path.isdir(cand):
            return tokens, cand
        parent = os.path.dirname(d)
        if parent == d:
            sys.exit("brands/%s/ not found above %s" % (brand, project))
        d = parent


def load_edit(project):
    path = os.path.join(project, "edit.yaml")
    if not os.path.exists(path):
        sys.exit("edit.yaml not found in %s — see templates/talking-head-reels/edit.example.yaml" % project)
    return yaml.safe_load(open(path, encoding="utf-8"))


def load_words(project):
    return json.load(open(os.path.join(project, "transcript.json"), encoding="utf-8"))["words"]


def sync_brand_assets(frame, brand_dir, project):
    """Copy brand fonts + SFX into the project's assets/ so the composition is self-contained."""
    for _, rel in frame["typography"]["fonts"].items():
        dst = os.path.join(project, "assets", "fonts", os.path.basename(rel))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(brand_dir, rel), dst)
    for key, rel in frame["sfx"].items():
        if key == "volume":
            continue
        dst = os.path.join(project, "assets", "sfx", os.path.basename(rel))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(brand_dir, rel), dst)


# ----------------------------------------------------------------------------- helpers

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def sfx_file(frame, name):
    return "assets/sfx/" + os.path.basename(frame["sfx"][name])


def sfx_duration(project, frame, name):
    """Read the real duration once so lint sees bounded audio windows (needs ffprobe on PATH)."""
    path = os.path.join(project, sfx_file(frame, name))
    try:
        import subprocess
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return float(out)
    except Exception:
        return 2.5  # safe upper bound when ffprobe is unavailable


# ----------------------------------------------------------------------------- generators

def captions_html(words, edit):
    """Caption rail: one .clip per chunk, held until the next chunk starts (≤0.6s gap)."""
    chunks = edit["captions"]
    duration = float(edit["duration"])
    end_cut = float(edit.get("end_card_cut", 10**9))
    out = []
    for n, (s, e, text, hl) in enumerate(chunks):
        start = words[s]["start"]
        end = words[e]["end"]
        if n + 1 < len(chunks):
            nxt = words[chunks[n + 1][0]]["start"]
            end = nxt if nxt - end <= 0.6 else end + 0.3
        else:
            end = duration
        body = esc(text)
        if hl:
            body = body.replace(esc(hl), '<span class="hl">%s</span>' % esc(hl), 1)
        cls = "clip cap high" if end > end_cut else "clip cap"
        out.append(
            '      <div class="%s" id="cap-%02d" data-start="%.2f" data-duration="%.2f" data-track-index="3">'
            '<div class="cap-inner">%s</div></div>' % (cls, n, start, end - start, body)
        )
    return "\n".join(out)


def cards_html(edit):
    """Cards: plate / sub / pills / stamp / arrow, each an absolutely positioned .clip in the card band."""
    out = []
    for c in edit.get("cards", []):
        cid = c["id"]
        parts = []
        if c.get("plate"):
            parts.append('        <div class="plate" id="%s-plate">%s</div>' % (cid, esc(c["plate"])))
        if c.get("sub"):
            parts.append('        <div class="plate small" id="%s-sub">%s</div>' % (cid, esc(c["sub"])))
        for i, pill in enumerate(c.get("pills", [])):
            text = pill[0]
            style = " warn" if c.get("pills_style") == "warn" else ""
            tick = '<span class="tick">✓</span>' if c.get("pills_style") == "check" else ""
            parts.append('        <div class="pill%s" id="%s-pill-%d">%s%s</div>' % (style, cid, i, tick, esc(text)))
        if c.get("stamp"):
            parts.append('        <div class="plate amber" id="%s-stamp">%s</div>' % (cid, esc(c["stamp"]["text"])))
        if c.get("arrow") == "down":
            parts.append(
                '        <svg class="arrow" id="%s-arrow" viewBox="0 0 100 100" aria-hidden="true">'
                '<path d="M50 10 V78 M20 50 L50 82 L80 50" fill="none" stroke="var(--accent)" '
                'stroke-width="16" stroke-linecap="round" stroke-linejoin="round"/></svg>' % cid
            )
        out.append(
            '      <div class="clip card" id="card-%s" data-start="%.2f" data-duration="%.2f" data-track-index="5">\n%s\n      </div>'
            % (cid, float(c["at"]), float(c["dur"]), "\n".join(parts))
        )
    lt = edit.get("lower_third")
    if lt:
        out.append(
            '      <div class="clip" id="name-plate" data-start="%.2f" data-duration="%.2f" data-track-index="5">\n'
            '        <div class="name">%s</div>\n        <div class="role">%s</div>\n      </div>'
            % (float(lt["at"]), float(lt["dur"]), esc(lt["name"]), esc(lt["role"]))
        )
    return "\n".join(out)


def cards_js(edit):
    """Timeline tweens for cards: slam-in on the spoken word, quick exit before the clip ends."""
    js = []
    for c in edit.get("cards", []):
        cid, at, end = c["id"], float(c["at"]), float(c["at"]) + float(c["dur"])
        if c.get("plate"):
            js.append('        slam("#%s-plate", %.2f, 0.32);' % (cid, at))
        if c.get("sub"):
            js.append('        slam("#%s-sub", %.2f, 0.3);' % (cid, at + 0.15))
        for i, pill in enumerate(c.get("pills", [])):
            js.append('        slam("#%s-pill-%d", %.2f, 0.28);' % (cid, i, float(pill[1])))
        if c.get("stamp"):
            t = float(c["stamp"]["at"])
            js.append(
                '        tl.fromTo("#%s-stamp", { opacity: 0, scale: 2.2, rotation: -8 }, '
                '{ opacity: 1, scale: 1, rotation: -4, duration: 0.3, ease: "power4.out" }, %.2f);' % (cid, t)
            )
            js.append(
                '        tl.to("#%s-stamp", { scale: 1.06, duration: 0.5, ease: "sine.inOut", yoyo: true, repeat: 1 }, %.2f);'
                % (cid, t + 0.36)
            )
        if c.get("arrow") == "down":
            js.append(
                '        tl.fromTo("#%s-arrow", { opacity: 0, y: -30 }, { opacity: 1, y: 0, duration: 0.3, ease: "power2.out" }, %.2f);'
                % (cid, at + 0.22)
            )
            js.append(
                '        tl.to("#%s-arrow", { y: 22, duration: 0.35, ease: "sine.inOut", yoyo: true, repeat: 3 }, %.2f);'
                % (cid, at + 0.52)
            )
        js.append('        exit("#card-%s > *", %.2f);' % (cid, end - 0.25))
    lt = edit.get("lower_third")
    if lt:
        at, end = float(lt["at"]), float(lt["at"]) + float(lt["dur"])
        js.append(
            '        tl.fromTo("#name-plate > *", { opacity: 0, x: -60 }, { opacity: 1, x: 0, duration: 0.4, stagger: 0.1, ease: "power3.out" }, %.2f);'
            % at
        )
        js.append('        tl.to("#name-plate > *", { opacity: 0, x: -40, duration: 0.3, ease: "power2.in" }, %.2f);' % (end - 0.4))
    return "\n".join(js)


def punches_js(edit):
    return "\n".join(
        '        tl.to("#cam", { scale: %.2f, duration: 0.28, ease: "power3.out" }, %.2f);' % (float(s), float(t))
        for t, s in edit.get("punches", [])
    )


def sfx_cues(frame, edit):
    """Derive every SFX cue from the edit: punch-ins, card parts, end-card cut, plus explicit extras."""
    vol = float(frame["sfx"].get("volume", 0.35))
    cues = [(float(t), "whoosh", vol * 0.85) for t, _ in edit.get("punches", [])]
    if edit.get("end_card_cut"):
        cues.append((float(edit["end_card_cut"]), "whoosh", vol * 0.85))
    for c in edit.get("cards", []):
        at = float(c["at"])
        if c.get("sfx"):
            cues.append((at, c["sfx"], vol * 1.15))
        for pill in c.get("pills", []):
            cues.append((float(pill[1]), "pop", vol))
        if c.get("stamp"):
            t = float(c["stamp"]["at"])
            cues += [(t, "impact", vol * 1.3), (t + 0.06, "sparkle", vol * 0.85)]
        if c.get("arrow"):
            cues.append((at, "chime", vol))
    for t, name, v in edit.get("sfx_extra", []):
        cues.append((float(t), name, float(v)))
    return sorted(cues)


def sfx_html(project, frame, edit):
    """One <audio> per cue; lanes per family (pops alternate) so overlapping cues never share a track."""
    lanes = {"whoosh": 12, "impact": 13, "pop": 14, "chime": 16, "sparkle": 16}
    durs = {}
    out, pops = [], 0
    for n, (t, name, v) in enumerate(sfx_cues(frame, edit)):
        if name not in durs:
            durs[name] = sfx_duration(project, frame, name)
        lane = lanes.get(name, 17)
        if name == "pop":
            lane += pops % 2
            pops += 1
        out.append(
            '      <audio id="sfx-%02d" src="%s" data-start="%.2f" data-duration="%.2f" data-track-index="%d" data-volume="%.2f"></audio>'
            % (n, sfx_file(frame, name), t, durs[name], lane, min(v, 1.0))
        )
    return "\n".join(out)


def font_faces(frame):
    fam = frame["typography"]["family"]
    return "\n".join(
        '      @font-face { font-family: "%s"; font-weight: %s; src: url("assets/fonts/%s") format("truetype"); }'
        % (fam, w, os.path.basename(rel))
        for w, rel in frame["typography"]["fonts"].items()
    )


def typo(frame, role):
    t = frame["typography"][role]
    return "font-size: %dpx; font-weight: %d; line-height: %s;" % (t["px"], t["weight"], t["lineHeight"])


# ----------------------------------------------------------------------------- template

TEMPLATE = open(os.path.join(HERE, "index.template.html"), encoding="utf-8").read()


def render(project, frame, edit, words):
    c, sz, lay = frame["colors"], frame["safe-zone"], frame["layout"]
    fill = {
        "__DURATION__": "%.2f" % float(edit["duration"]),
        "__FPS__": str(edit.get("fps", 30)),
        "__SOURCE__": edit["source"],
        "__FONT_FACES__": font_faces(frame),
        "__FONT_FAMILY__": frame["typography"]["family"],
        "__PRIMARY__": c["primary"], "__ACCENT__": c["accent"], "__INK__": c["ink"],
        "__PAPER__": c["paper"], "__SCRIM__": c["scrim"],
        "__SIDE__": str(sz["side"]),
        "__CAPTION_BOTTOM__": str(1920 - int(lay["caption-bottom"])),
        "__CAPTION_HIGH_BOTTOM__": str(1920 - int(lay["caption-bottom"]) + 280),
        "__CARD_TOP__": str(lay["card-top"]),
        "__NAME_TOP__": str(int(lay["card-top"]) + 40),
        "__PUNCH_ORIGIN__": lay.get("punch-origin", "50% 30%"),
        "__T_TITLE__": typo(frame, "title"), "__T_STAMP__": typo(frame, "stamp"),
        "__T_CAPTION__": typo(frame, "caption"), "__T_PILL__": typo(frame, "pill"),
        "__T_SUB__": typo(frame, "sub"), "__T_NAME__": typo(frame, "name"), "__T_LABEL__": typo(frame, "label"),
        "__R_CARD__": frame["radii"]["card"], "__R_CAPTION__": frame["radii"]["caption"],
        "__R_PILL__": frame["radii"]["pill"], "__R_NAME__": frame["radii"]["name"],
        "__CARDS__": cards_html(edit),
        "__CAPTIONS__": captions_html(words, edit),
        "__SFX__": sfx_html(project, frame, edit),
        "__PUNCHES__": punches_js(edit),
        "__CARDS_JS__": cards_js(edit),
    }
    html = TEMPLATE
    for k, v in fill.items():
        html = html.replace(k, v)
    return html


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".", help="video project directory (contains frame.md, edit.yaml, transcript.json)")
    args = ap.parse_args()
    project = os.path.abspath(args.project)

    frame, brand_dir = load_frame(project)
    edit = load_edit(project)
    words = load_words(project)
    sync_brand_assets(frame, brand_dir, project)

    html = render(project, frame, edit, words)
    with open(os.path.join(project, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(
        "wrote index.html — brand %s, %d captions, %d cards, %d punch-ins, %d sfx cues"
        % (frame["brand"], len(edit["captions"]), len(edit.get("cards", [])), len(edit.get("punches", [])), len(sfx_cues(frame, edit)))
    )


if __name__ == "__main__":
    main()
