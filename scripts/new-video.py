#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scaffold a new talking-head Reels project: directories + starter files.

Usage:
    python scripts/new-video.py <ten-video> [--brand dr-dac-quang]

Creates videos/<ten-video>/ with assets/, renders/, and copies:
  hyperframes.json, package.json (as-is),
  meta.json (id/name set to <ten-video>),
  frame.md (from brands/<brand>/),
  edit.yaml (from templates/talking-head-reels/edit.example.yaml).

Next: drop assets/source.mp4, write transcript.json + BRIEF.md,
edit edit.yaml — see docs/new-video.md step 2+.

Agent-agnostic: plain Python 3.11+, no third-party deps.
"""
import argparse
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(ROOT, "templates", "talking-head-reels")
OLD_PROJECT = os.path.join(ROOT, "videos", "mo-thua-sau-tet-reels")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", help="video project dir name (lowercase, hyphens, e.g. tri-mun-tham-my)")
    ap.add_argument("--brand", default="dr-dac-quang", help="dir name under brands/")
    args = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.name):
        sys.exit("name must be lowercase alphanumerics + hyphens, e.g. tri-mun-tham-my")

    project = os.path.join(ROOT, "videos", args.name)
    if os.path.exists(project):
        sys.exit("videos/%s already exists" % args.name)

    brand_frame = os.path.join(ROOT, "brands", args.brand, "frame.md")
    for path in (brand_frame,
                 os.path.join(TEMPLATE_DIR, "edit.example.yaml"),
                 os.path.join(OLD_PROJECT, "hyperframes.json"),
                 os.path.join(OLD_PROJECT, "package.json"),
                 os.path.join(OLD_PROJECT, "meta.json")):
        if not os.path.exists(path):
            sys.exit("missing starter file: %s" % path)

    os.makedirs(os.path.join(project, "assets"))
    os.makedirs(os.path.join(project, "renders"))

    shutil.copyfile(os.path.join(OLD_PROJECT, "hyperframes.json"),
                    os.path.join(project, "hyperframes.json"))
    shutil.copyfile(os.path.join(OLD_PROJECT, "package.json"),
                    os.path.join(project, "package.json"))
    shutil.copyfile(brand_frame, os.path.join(project, "frame.md"))
    shutil.copyfile(os.path.join(TEMPLATE_DIR, "edit.example.yaml"),
                    os.path.join(project, "edit.yaml"))

    meta = json.load(open(os.path.join(OLD_PROJECT, "meta.json"), encoding="utf-8"))
    meta["id"] = args.name
    meta["name"] = args.name
    from datetime import datetime, timezone
    meta["createdAt"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    json.dump(meta, open(os.path.join(project, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print("scaffolded videos/%s — next:" % args.name)
    print("  1. copy footage -> videos/%s/assets/source.mp4" % args.name)
    print("  2. write transcript.json + BRIEF.md (see docs/new-video.md)")
    print("  3. edit edit.yaml, then:")
    print("     python templates/talking-head-reels/build.py --project videos/%s" % args.name)


if __name__ == "__main__":
    main()
