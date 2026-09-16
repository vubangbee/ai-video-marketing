---
name: ak:motion-graphics
description: Route a motion / animation / video request to the right skill — prefer the in-repo skills (ak-remotion, ak-video, ak-html-video, ak-shader, ak-threejs, ak-media-processing) first; when the request needs a template outside their scope (kinetic typography, TikTok/Reels beat, ad hook-body-CTA variants, ecommerce product loop, editorial map, GSAP scroll motion, Manim math scene, generative illustration), propose the matching iart-ai/motion-skills external pack for the user to install, then run the deliver-and-verify loop on the rendered output.
argument-hint: "[intent-or-pack] [--list|--propose <pack>|--verify <file>]"
metadata:
  author: agentkit
  version: "1.0.0"
  upstream: iart-ai/motion-skills
  upstream_ref: master@945c4c7
  upstream_license: MIT
---

# Motion Graphics

Router + verify-loop toolkit for motion / animation / video work. This skill
does **not** reimplement any motion skill. It:

1. Prefers in-repo skills that already cover the request.
2. When the request needs a template outside their scope, **proposes** the
   matching pack from the external MIT-licensed
   [iart-ai/motion-skills](https://github.com/iart-ai/motion-skills) family and
   waits for the user to run the install command.
3. Ships the upstream deliver-and-verify shell helpers under `scripts/` so any
   rendered artifact — from an in-repo skill or an external pack — can be
   inspected with the same freeze-frame / contact-sheet / probe-MP4 loop.

<args>$ARGUMENTS</args>

## Route in this order

### 1) In-repo skills first

**Prefer when installed; fall through when absent.** The `Kit` column marks
each row's origin. On a marketing-only install `overrides.skills` replaces the
inherited list per the [kit-yaml spec](../../../../docs/specs/kit-yaml-spec.md),
so `core`-marked rows are not automatically available — treat them as
opportunistic routes, not guarantees. Confirm the target skill is discoverable
in the current installation before routing to it (Claude Code `/skills`,
`ak skills list`, or the runtime's skill catalog). Any row whose target is not
installed skips to the next matching row, and only if no row lands does the
request fall through to step 2.

| Request shape | Skill | Kit |
|---|---|---|
| Programmatic video, Remotion (React), data-driven video | `ak:remotion` | core |
| HTML/CSS/JS template → local MP4 (Chromium + ffmpeg) | `ak:html-video` | core |
| HTML-first video via HeyGen HyperFrames CLI | `ak:hyperframes` | core |
| Veo generation, video scripts, storyboards, thumbnails | `ak:video` | marketing |
| GLSL shaders, procedural graphics | `ak:shader` | core |
| Three.js / WebGL / WebGPU / GLTF | `ak:threejs` | core |
| FFmpeg / ImageMagick encode, filter, batch | `ak:media-processing` | core |
| Mermaid diagrams (static, not motion) | `ak:mermaidjs-v11` | marketing |

Only fall through to step 2 when the request needs a template the available
in-repo skills do not carry.

### 2) External pack (propose, do not auto-install)

When the request needs one of the specific templates the packs specialize in
(vertical hook-beat, ad hook/body/CTA variants, chart animation with real
numbers, kinetic type, editorial map, Manim scene, generative illustration…):

1. Look up the pack in `references/packs.md` by trigger phrase.
2. **Print** the install command the user should run:

   ```bash
   npx skills add iart-ai/<pack>
   # or, for Claude Code plugin delivery:
   /plugin marketplace add iart-ai/<pack>
   ```

3. Explain in one sentence what the pack ships and why it fits.
4. Wait for the user's explicit go-ahead before executing anything. Third-party
   skill packs are user-installed, never auto-installed. Never run the install
   command on your own initiative, even when the user's intent seems to imply it.
5. Once installed, its `SKILL.md` files auto-discover in Claude Code, Cursor,
   Codex, and 40+ agents.

Trigger-to-pack routing:

| User intent | Pack |
|---|---|
| "tiktok", "reel", "short", vertical 9:16, hook-cut-cta beat | `tiktok-video-skills` |
| "text-message story", "imessage story clip" | `text-message-video-skills` |
| "youtube video", "podcast clip", horizontal 16:9 episode | `youtube-video-skills` |
| "product video", "unboxing", "before/after", shop loop | `ecommerce-video-skills` |
| "ad creative", "meta ad", "tiktok ad", "google ad variants" | `ad-video-skills` |
| "chart animation", "data video", "kpi reveal", "dashboard" | `data-animation-skills` |
| "explainer", "how-it-works", "educational", tutorial | `explainer-video-skills` |
| "map animation", editorial map, "vox-style map" | `map-animation-skills` |
| "web animation", GSAP, SVG, Lottie, on-scroll motion | `web-animation-skills` |
| "motion design", brand sizzle, logo motion, transition pack | `motion-design-skills` |
| "kinetic typography", "text animation", title cards | `kinetic-typography-skills` |
| "client deliverable", handoff pack, invoice-worthy scope | `freelance-motion-skills` |
| "three.js" as a template repo (not scene from scratch) | `webgl-animation-skills` |
| "manim", math scene, educational animation | `manim-skills` |
| "generative illustration", creative-code artwork | `generative-illustration-skills` |

Some intents overlap. Rules:

- **"tiktok ad"** — start with `tiktok-video-skills` (format wins); fall back
  to `ad-video-skills` only when the variant harness is what the user needs.
- **"chart in an explainer"** — start with `data-animation-skills` (numbers
  first), then use `explainer-video-skills` for the framing.
- **"logo animation on the web"** — `motion-design-skills` for the logo motion,
  then `web-animation-skills` (or in-repo `ak:frontend-development`) for the
  page-side embedding.

See `references/packs.md` for every pack's audience, skill count (as of the
verification date), and detailed trigger phrases.

### 3) Verify what actually rendered

Every pack — and every in-repo video skill — should close with the same
inspection loop. Use the helpers in this skill's `scripts/`. Short form:

**Light tier** (standalone HTML with a `?t=N` seek harness — the convention
web-animation and kinetic-typography packs follow):

```bash
scripts/seek-shot.sh anim.html 0 1.5 3
scripts/contact-sheet.sh sheet.png frame-*.png
```

**Heavy tier** (Remotion / Manim / html-video / any encoded MP4):

```bash
scripts/probe-mp4.sh out/short.mp4 1080x1920 30
```

The MP4 probe reads real width × height / codec / fps / duration straight from
the file with `ffprobe`. It fails loud when the render lies. See
`references/verify-loop.md` for tier selection, real dep list, and per-format
invocations.

## Subcommands

| Subcommand | Behavior | Reference |
|---|---|---|
| `--list` | Print the 15 packs, their audiences, trigger phrases, and install commands | `references/packs.md` |
| `--propose <pack>` | Print the `npx skills add iart-ai/<pack>` command with a one-line rationale; do not execute | (external) |
| `--verify <file>` | Route the file to the right verify helper (`.mp4` → `probe-mp4`, `.html` → `seek-shot` + `contact-sheet`) | `references/verify-loop.md` |
| _(default, no subcommand)_ | Run the "Route in this order" flow above on `$ARGUMENTS` | This file |

## Compose with

Same availability rule as step 1: each item is opportunistic — skip it when
the target skill is not installed.

- `ak:copywriting` — hook line, CTA, on-screen copy. _(core; skip if absent)_
- `ak:brand`, `ak:logo-design`, `ak:design-system` — brand tokens the motion
  templates need. _(marketing)_
- `ak:video script-create` — the extended script when the beat isn't enough.
  _(marketing)_
- `ak:elevenlabs` — voice-over audio. _(marketing)_
- `ak:youtube-thumbnail-design` — thumbnail beside the YouTube pack.
  _(marketing)_
- `ak:paid-ads`, `ak:ads-management` — spend and placement around the creative
  the ad pack produces. _(marketing)_

## Attribution

- Upstream hub: [iart-ai/motion-skills](https://github.com/iart-ai/motion-skills) — MIT.
- The three POSIX scripts under `scripts/` are copied verbatim from upstream
  `tools/verify/` (`master` branch, commit `945c4c7`); each carries an
  origin / license header. Full MIT text and copyright notice: `LICENSE.txt`.
- Showcase artifact (`showcase.gif`, `showcase.html`) is not vendored — view
  it on the upstream README.
- Built by [iart.ai](https://iart.ai) — the AI motion agent.
