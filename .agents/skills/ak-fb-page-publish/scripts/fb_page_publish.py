#!/usr/bin/env python3
"""Dang bai len fanpage Facebook qua Graph API.

Nhan duong dan file tren dia (khong nhan link Drive - viec do la cua
drive_client.py) va dang len mot hoac nhieu page duoi dang anh, album, video
hoac Reels, ngay lap tuc hoac hen gio bang scheduled_publish_time cua Meta.

    python fb_page_publish.py check-auth
    python fb_page_publish.py list-pages
    python fb_page_publish.py publish-photo --page Sua --image a.jpg --message "..." --schedule "+2h"
    python fb_page_publish.py publish-photo --page Sua,PTTM,ATCYK --image a.jpg --message "..."
    python fb_page_publish.py list-scheduled --page Sua
    python fb_page_publish.py cancel --post-id 123_456
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import requests

import config

# Reels khong upload qua graph.facebook.com ma qua host rupload rieng.
RUPLOAD_HOST = "https://rupload.facebook.com"

# Duoi nguong nay dung multipart mot phat; tren thi phai chia chunk.
CHUNKED_VIDEO_THRESHOLD = 100 * 1024 * 1024
VIDEO_CHUNK_SIZE = 8 * 1024 * 1024

# Meta chi ghep toi da 10 media vao mot bai feed.
MAX_ALBUM_PHOTOS = 10

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}

# Nguong canh bao (khong chan) va nguong chan cung.
PHOTO_WARN_SIZE = 10 * 1024 * 1024
VIDEO_WARN_SIZE = 1024 * 1024 * 1024
VIDEO_MAX_SIZE = 10 * 1024 * 1024 * 1024

# Yeu cau cua Meta cho Reels; chi canh bao chu khong chan, vi Meta van co the
# tu xu ly mot so truong hop bien.
REEL_MIN_SECONDS = 3
REEL_MAX_SECONDS = 90
REEL_MIN_WIDTH = 540
REEL_MIN_HEIGHT = 960

REQUIRED_SCOPES = ("pages_show_list", "pages_read_engagement", "pages_manage_posts")
RECOMMENDED_SCOPES = ("pages_read_user_content",)

# Task o cap tai san (Business Settings > Pages). CREATE_CONTENT du de dang
# anh, nhung upload video/Reels bi tu choi neu chi co mot minh no - xac minh
# 09/09/2026: page chi co CREATE_CONTENT+MODERATE tra (#200) khi dang video,
# them MESSAGING/ADVERTISE/ANALYZE thi dang duoc.
VIDEO_TASKS = {"MANAGE", "ADVERTISE", "ANALYZE", "MESSAGING"}

_PERMISSION_HINT = (
    "Token thieu quyen dang bai len Page.\n"
    "  Vao business.facebook.com > Business Settings > Users > System Users\n"
    "  > Generate New Token, tick 'pages_manage_posts' va 'pages_read_user_content'.\n"
    "  Chi tiet: references/setup-permissions.md"
)


class PublishError(Exception):
    """Loi da dich sang thong diep nguoi dung doc duoc."""


# --- Goi Graph API ---------------------------------------------------------

def _raise_graph_error(payload: dict, status: int):
    """Doi loi Graph API thanh thong diep co huong xu ly."""
    err = payload.get("error", {}) if isinstance(payload, dict) else {}
    code = err.get("code")
    message = err.get("error_user_msg") or err.get("message") or json.dumps(payload)[:400]

    lines = [f"Graph API tra loi (HTTP {status}, code {code}): {message}"]
    if code in (200, 10, 3):
        lines.append("")
        # Code 200 co hai nguyen nhan rat khac nhau. Neu chi nhac scope thi
        # nguoi dung se di cap lai token trong khi token von da du quyen.
        lines.append("Neu dang thao tac tren mot bai da co: kiem tra post_id da dung dang"
                     "\n  '{page_id}_{object_id}' chua. Id tran (khong co dau gach duoi)"
                     "\n  luon bi tu choi. Lay id dung bang: list-scheduled --page <ma>")
        lines.append("")
        lines.append(_PERMISSION_HINT)
    elif code == 190:
        lines.append("")
        lines.append("Token het han hoac bi thu hoi. Tao token moi va cap nhat META_ACCESS_TOKEN.")
    elif code == 100 and "scheduled_publish_time" in message:
        lines.append("")
        lines.append("Gio hen dang phai cach hien tai tu 10 phut den 6 thang.")
    raise PublishError("\n".join(lines))


def graph_request(method: str, path: str, token: str, data=None,
                  files=None, params=None, timeout=300) -> dict:
    """Goi Graph API va tra ve JSON; loi HTTP duoc dich truoc khi raise.

    GET va DELETE phai dua tham so vao query string: Graph API bo qua body
    cua hai method nay, ke ca access_token.
    """
    url = path if path.startswith("http") else config.graph_url(path)
    query = dict(params or {})
    body = dict(data or {})

    if method.upper() in ("GET", "DELETE"):
        query.update(body)
        query["access_token"] = token
        body = None
    else:
        body["access_token"] = token

    try:
        resp = requests.request(method, url, data=body, files=files,
                                params=query, timeout=timeout)
    except requests.RequestException as exc:
        raise PublishError(f"Khong goi duoc Graph API: {exc}") from exc

    try:
        result = resp.json()
    except ValueError:
        result = {"raw": resp.text[:400]}

    if not resp.ok or (isinstance(result, dict) and "error" in result):
        _raise_graph_error(result, resp.status_code)
    return result


_PAGE_TOKEN_CACHE = {}


def page_token(page_id: str) -> str:
    """Doi token he thong sang Page access token cua page can dang.

    System user token thuong dang duoc truc tiep, nen khi Graph khong tra ve
    access_token rieng thi lui ve dung token goc thay vi bao loi.
    """
    if page_id in _PAGE_TOKEN_CACHE:
        return _PAGE_TOKEN_CACHE[page_id]

    base = config.access_token()
    try:
        data = graph_request("GET", page_id, base, params={"fields": "access_token"})
        token = data.get("access_token") or base
    except PublishError:
        token = base

    _PAGE_TOKEN_CACHE[page_id] = token
    return token


def token_for_post(post_id: str) -> str:
    """Page token suy ra tu post_id dang '{page_id}_{post}'.

    Thao tac o cap bai viet (doi gio, dang ngay, xoa) doi Page token chu khong
    nhan token he thong, nen phai boc page_id ra tu chinh post_id.
    """
    page_id = post_id.split("_", 1)[0] if "_" in post_id else ""
    return page_token(page_id) if page_id.isdigit() else config.access_token()


def qualify_post_id(page_id: str, raw_id: str) -> str:
    """Ghep post_id day du dang '{page_id}_{object_id}'.

    Endpoint /photos va /videos o che do hen gio chi tra ve id cua chinh anh
    hoac video, khong kem tien to page. Id tran do KHONG dung duoc voi cancel,
    reschedule hay publish-now - Graph API tra (#200). Ghep tien to ngay tai
    day de cai in ra cho nguoi dung la cai ho dung duoc luon.
    """
    if not raw_id or "_" in raw_id:
        return raw_id
    return f"{page_id}_{raw_id}"


# --- Kiem tra media --------------------------------------------------------

def probe_video(path: Path) -> dict:
    """Do do dai, do phan giai video bang ffprobe. Khong co ffprobe -> {}."""
    exe = config.ffprobe_path()
    if not exe:
        return {}

    cmd = [exe, "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height,duration:format=duration",
           "-of", "json", str(path)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            return {}
        data = json.loads(out.stdout or "{}")
    except (subprocess.SubprocessError, ValueError, OSError):
        return {}

    stream = (data.get("streams") or [{}])[0]
    duration = stream.get("duration") or (data.get("format") or {}).get("duration")
    result = {}
    if stream.get("width"):
        result["width"] = int(stream["width"])
    if stream.get("height"):
        result["height"] = int(stream["height"])
    if duration:
        try:
            result["duration"] = float(duration)
        except ValueError:
            pass
    return result


def check_media(path_str: str, kind: str, is_reel: bool = False) -> dict:
    """Kiem tra file truoc khi upload. Raise neu chac chan Meta se tu choi.

    Van de nao Meta co the tu xu ly duoc thi chi in canh bao ra stderr, de
    nguoi dung tu quyet dinh thay vi bi chan oan.
    """
    path = Path(path_str)
    if not path.exists():
        raise PublishError(f"Khong tim thay file: {path}")
    if not path.is_file():
        raise PublishError(f"Khong phai file: {path}")

    size = path.stat().st_size
    if size == 0:
        raise PublishError(f"File rong: {path}")

    ext = path.suffix.lower()
    info = {"path": str(path), "name": path.name, "size": size, "kind": kind}

    if kind == "image":
        if ext not in IMAGE_EXTENSIONS:
            raise PublishError(
                f"'{path.name}' khong phai file anh (duoi {ext or 'khong co'}).\n"
                f"  Ho tro: {', '.join(sorted(IMAGE_EXTENSIONS))}"
            )
        if size > PHOTO_WARN_SIZE:
            _warn(f"{path.name} nang {_human_size(size)}, Meta co the nen manh hoac tu choi.")
        return info

    if ext not in VIDEO_EXTENSIONS:
        raise PublishError(
            f"'{path.name}' khong phai file video (duoi {ext or 'khong co'}).\n"
            f"  Ho tro: {', '.join(sorted(VIDEO_EXTENSIONS))}"
        )
    if size > VIDEO_MAX_SIZE:
        raise PublishError(f"Video {_human_size(size)} vuot gioi han 10GB cua Meta.")
    if size > VIDEO_WARN_SIZE:
        _warn(f"{path.name} nang {_human_size(size)}, upload se lau.")

    info.update(probe_video(path))

    if not info.get("duration"):
        _warn("Khong doc duoc thong so video (thieu ffprobe hoac file la). "
              "Bo qua kiem tra do dai va ti le khung hinh.")
    elif is_reel:
        _check_reel_specs(info)

    return info


def _check_reel_specs(info: dict):
    """Doi chieu voi yeu cau Reels cua Meta; chi canh bao, khong chan."""
    duration = info.get("duration", 0)
    width, height = info.get("width", 0), info.get("height", 0)

    if duration < REEL_MIN_SECONDS or duration > REEL_MAX_SECONDS:
        _warn(f"Reels dai {duration:.1f}s, Meta yeu cau {REEL_MIN_SECONDS}-{REEL_MAX_SECONDS}s.")
    if width and height:
        ratio = width / height
        if abs(ratio - 9 / 16) > 0.02:
            _warn(f"Reels ti le {width}x{height} ({ratio:.2f}), Meta yeu cau doc 9:16 (0.56).")
        if width < REEL_MIN_WIDTH or height < REEL_MIN_HEIGHT:
            _warn(f"Reels {width}x{height} nho hon toi thieu "
                  f"{REEL_MIN_WIDTH}x{REEL_MIN_HEIGHT}.")


def _human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{int(value)}B" if unit == "B" else f"{value:.1f}{unit}"
        value /= 1024
    return f"{value:.1f}GB"


def _warn(text: str):
    print(f"  CANH BAO: {text}", file=sys.stderr)


# --- Doc tham so dau vao ---------------------------------------------------

def read_message(value: str) -> str:
    """Noi dung bai; '@duong/dan' nghia la doc tu file (output cua read-doc)."""
    if not value:
        return ""
    if value.startswith("@"):
        path = Path(value[1:])
        if not path.exists():
            raise PublishError(f"Khong tim thay file noi dung: {path}")
        return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").strip()
    return value


def collect_images(args) -> list:
    """Danh sach anh tu --images (theo thu tu go) hoac --images-dir (theo ten)."""
    if args.images:
        paths = [p.strip() for p in args.images.split(",") if p.strip()]
    else:
        folder = Path(args.images_dir)
        if not folder.is_dir():
            raise PublishError(f"Khong phai thu muc: {folder}")
        paths = [str(p) for p in sorted(folder.iterdir())
                 if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
        if not paths:
            raise PublishError(f"Thu muc {folder} khong co file anh nao.")

    if len(paths) > MAX_ALBUM_PHOTOS:
        raise PublishError(
            f"Album co {len(paths)} anh, Meta chi cho toi da {MAX_ALBUM_PHOTOS} anh mot bai.\n"
            "  Tach thanh nhieu bai hoac bot anh."
        )
    return paths


def resolve_schedule(args) -> int:
    """Unix timestamp gio hen dang, hoac 0 neu dang ngay."""
    return config.parse_schedule(args.schedule) if args.schedule else 0


def resolve_pages(ref: str) -> list:
    """Danh sach page tu chuoi '--page', ngan cach bang dau phay.

    Dang cung mot bai len 3 page la mot lenh voi mot lan xac nhan, khong phai
    ba lan go lenh.
    """
    refs = [r.strip() for r in (ref or "").split(",") if r.strip()]
    if not refs:
        raise PublishError("Chua chi dinh page. Dung --page <ma|id|ten>.")

    pages, seen = [], set()
    for item in refs:
        page = config.resolve_page(item)
        if page["id"] not in seen:      # go trung khi go ca ma lan ID cua cung page
            seen.add(page["id"])
            pages.append(page)
    return pages


# --- Xac nhan truoc khi dang -----------------------------------------------

def preview(pages: list, kind: str, media: list, message: str, when: int) -> str:
    """Ban tom tat de nguoi dung doi chieu truoc khi bam dang."""
    lines = ["-" * 62]
    if len(pages) == 1:
        lines.append(f"  Page      : {pages[0]['code']} - {pages[0]['name']}")
        lines.append(f"  Page ID   : {pages[0]['id']}")
    else:
        lines.append(f"  Page      : {len(pages)} page")
        for page in pages:
            lines.append(f"              - {page['code']:<9} {page['id']:<18} {page['name']}")

    lines.append(f"  Loai bai  : {kind}")
    lines.append(f"  Dang luc  : {config.format_timestamp(when) if when else 'NGAY BAY GIO'}")

    if media:
        lines.append(f"  Media     : {len(media)} file")
        for item in media:
            extra = ""
            if item.get("duration"):
                extra = f", {item['duration']:.1f}s"
            if item.get("width"):
                extra += f", {item['width']}x{item['height']}"
            lines.append(f"              - {item['name']} ({_human_size(item['size'])}{extra})")

    preview_text = message if len(message) <= 300 else message[:300] + " [...]"
    lines.append(f"  Noi dung  : {preview_text or '(khong co)'}")
    lines.append("-" * 62)
    return "\n".join(lines)


def confirm(args, summary: str) -> bool:
    """In ban tom tat; --dry-run thi dung lai, --yes thi chay thang."""
    print(summary)
    if args.dry_run:
        print("\n[DRY-RUN] Chua goi API. Bo --dry-run de dang that.")
        return False
    if args.yes:
        return True
    if not sys.stdin.isatty():
        raise PublishError(
            "Can xac nhan truoc khi dang. Them --yes de dong y, hoac --dry-run de xem thu."
        )
    return input("\nDang bai nay? [y/N] ").strip().lower() in ("y", "yes")


def _describe_post(page: dict, token: str, post_id: str, when: int,
                   extra=None, fetch_permalink: bool = True) -> dict:
    """Mo ta ket qua mot bai vua dang. Bai hen gio chua co permalink."""
    result = {"page": page["code"], "post_id": post_id}
    if when:
        result["scheduled_publish_time"] = when
        result["scheduled_at"] = config.format_timestamp(when)
        result["permalink"] = None
    elif fetch_permalink:
        try:
            data = graph_request("GET", post_id, token, params={"fields": "permalink_url"})
            result["permalink"] = data.get("permalink_url")
        except PublishError:
            result["permalink"] = None
    if extra:
        result.update(extra)
    return result


def _for_each_page(pages: list, when: int, action, fetch_permalink: bool = True) -> int:
    """Chay `action(page, token)` cho tung page roi tong ket lai.

    Mot page loi khong lam dung ca loat: cac page con lai van dang, cuoi cung
    bao ro page nao hong. Dang duoc mot phan van tot hon dung giua chung ma
    nguoi dung khong biet da dang toi dau.
    """
    results, failures = [], []
    for page in pages:
        if len(pages) > 1:
            print(f"\n--- {page['code']} - {page['name']} ---", file=sys.stderr)
        try:
            token = page_token(page["id"])
            post_id, extra = action(page, token)
            results.append(_describe_post(page, token, post_id, when, extra, fetch_permalink))
        except PublishError as exc:
            failures.append(page["code"])
            print(f"\nLOI tren page {page['code']}: {exc}", file=sys.stderr)

    if results:
        payload = results if len(results) > 1 else results[0]
        print("\n" + json.dumps(payload, ensure_ascii=False, indent=2))
        if when:
            codes = ", ".join(r["page"] for r in results)
            print(f"\nDa hen gio {config.format_timestamp(when)} tren: {codes}")
            print("Xem lai: python fb_page_publish.py list-scheduled "
                  f"--page {results[0]['page']}")

    if failures:
        print(f"\nThat bai {len(failures)}/{len(pages)} page: {', '.join(failures)}",
              file=sys.stderr)
        return 1
    return 0


# --- Lenh: chan doan -------------------------------------------------------

def cmd_check_auth(args) -> int:
    """Kiem tra token: loai, han dung, scope thieu, va danh sach page truy cap duoc."""
    token = config.access_token()

    info = graph_request("GET", "debug_token", token, params={"input_token": token})
    data = info.get("data", {})
    scopes = set(data.get("scopes") or [])
    expires = data.get("expires_at", 0)

    print(f"Token type   : {data.get('type', '?')}")
    print(f"Han dung     : {'khong het han' if not expires else config.format_timestamp(expires)}")

    missing = [s for s in REQUIRED_SCOPES if s not in scopes]
    missing_opt = [s for s in RECOMMENDED_SCOPES if s not in scopes]

    print(f"Scope bat buoc: {'DU' if not missing else 'THIEU ' + ', '.join(missing)}")
    print(f"Scope khuyen nghi: {'DU' if not missing_opt else 'THIEU ' + ', '.join(missing_opt)}")

    accounts = graph_request("GET", "me/accounts", token,
                             params={"fields": "id,name,tasks", "limit": 100})
    granted = {a["id"]: a for a in accounts.get("data", [])}

    pages = config.load_pages()
    width = max(len(p["code"]) for p in pages)
    print(f"\nFanpage trong .env ({len(pages)}):")
    thieu_video = []
    for p in pages:
        acc = granted.get(p["id"])
        tasks = (acc or {}).get("tasks") or []
        if not acc:
            status = "TOKEN KHONG THAY PAGE NAY"
        elif "CREATE_CONTENT" not in tasks:
            status = "THIEU CREATE_CONTENT -> khong dang duoc gi"
        elif not (set(tasks) & VIDEO_TASKS):
            # Anh dang duoc voi CREATE_CONTENT, nhung video/Reels doi them
            # quyen o cap tai san. Bao truoc con hon de nguoi dung upload
            # 30MB roi moi nhan (#200).
            status = "CHI DANG DUOC ANH -> thieu quyen cho video/Reels"
            thieu_video.append(p["code"])
        else:
            status = "OK"
        print(f"  {p['code']:<{width}}  {p['id']:<18}  {status}")
        if tasks:
            print(f"  {'':<{width}}  {'':<18}  tasks: {','.join(sorted(tasks))}")

    extra = [a for pid, a in granted.items() if pid not in {p["id"] for p in pages}]
    if extra:
        print(f"\nPage token thay nhung chua co trong .env ({len(extra)}):")
        for a in extra:
            print(f"  {a['id']:<18}  {a.get('name', '')}")

    if thieu_video:
        print(f"\nCac page chi dang duoc anh: {', '.join(thieu_video)}\n"
              "  Video va Reels se bi tu choi (#200). Mo Business Settings > Pages\n"
              "  > chon page > gan cho system user > bat them quyen ngoai Create Content.",
              file=sys.stderr)

    if missing:
        print("\n" + _PERMISSION_HINT, file=sys.stderr)
        return 1
    if missing_opt:
        print("\nThieu pages_read_user_content: lenh list-scheduled se khong xem duoc "
              "bai da hen gio.", file=sys.stderr)
    return 0


def cmd_list_pages(args) -> int:
    """In bang fanpage tu .env - dung cho cau hoi 'dang len page nao'."""
    pages = config.load_pages()
    width = max(len(p["code"]) for p in pages)
    print(f"{'MA':<{width}}  {'PAGE ID':<18}  TEN")
    for p in pages:
        print(f"{p['code']:<{width}}  {p['id']:<18}  {p['name']}")
    print(f"\n{len(pages)} page. Dung ma ngan o --page, vi du: --page {pages[0]['code']}")
    print(f"Dang cung luc nhieu page: --page {','.join(p['code'] for p in pages[:3])}")
    return 0


# --- Lenh: dang bai --------------------------------------------------------

def cmd_publish_photo(args) -> int:
    """Dang mot anh kem caption, ngay hoac hen gio."""
    pages = resolve_pages(args.page)
    message = read_message(args.message)
    when = resolve_schedule(args)
    media = [check_media(args.image, "image")]

    if not confirm(args, preview(pages, "Anh don", media, message, when)):
        return 0

    def action(page, token):
        data = {"caption": message}
        if when:
            data["published"] = "false"
            data["scheduled_publish_time"] = when
        with open(args.image, "rb") as fh:
            result = graph_request("POST", f"{page['id']}/photos", token,
                                   data=data, files={"source": fh})
        post_id = result.get("post_id") or qualify_post_id(page["id"], result.get("id"))
        return post_id, {"photo_id": result.get("id")}

    return _for_each_page(pages, when, action)


def cmd_publish_album(args) -> int:
    """Dang nhieu anh thanh mot bai album.

    Hai giai doan: upload tung anh o che do unpublished de lay media_fbid,
    roi tao mot bai feed gom cac id do lai.
    """
    pages = resolve_pages(args.page)
    message = read_message(args.message)
    when = resolve_schedule(args)
    paths = collect_images(args)
    media = [check_media(path, "image") for path in paths]

    if not confirm(args, preview(pages, f"Album {len(paths)} anh", media, message, when)):
        return 0

    def action(page, token):
        photo_ids = []
        for idx, path in enumerate(paths, 1):
            print(f"  Upload {idx}/{len(paths)}: {Path(path).name}", file=sys.stderr)
            with open(path, "rb") as fh:
                resp = graph_request("POST", f"{page['id']}/photos", token,
                                     data={"published": "false"}, files={"source": fh})
            photo_ids.append(resp["id"])

        data = {"message": message}
        for idx, photo_id in enumerate(photo_ids):
            data[f"attached_media[{idx}]"] = json.dumps({"media_fbid": photo_id})
        if when:
            data["published"] = "false"
            data["scheduled_publish_time"] = when

        result = graph_request("POST", f"{page['id']}/feed", token, data=data)
        return result["id"], {"photo_ids": photo_ids}

    return _for_each_page(pages, when, action)


def _upload_video_chunked(page_id: str, token: str, path: Path, finish_data: dict) -> dict:
    """Upload video lon theo 3 pha start/transfer/finish cua Graph API."""
    size = path.stat().st_size
    start = graph_request("POST", f"{page_id}/videos", token,
                          data={"upload_phase": "start", "file_size": size})
    session_id = start["upload_session_id"]
    start_offset = int(start["start_offset"])
    end_offset = int(start["end_offset"])

    with open(path, "rb") as fh:
        while start_offset < end_offset:
            fh.seek(start_offset)
            chunk = fh.read(min(VIDEO_CHUNK_SIZE, end_offset - start_offset))
            percent = start_offset / size * 100
            print(f"  Upload {percent:5.1f}% (offset {start_offset})",
                  end="\r", file=sys.stderr)

            resp = graph_request(
                "POST", f"{page_id}/videos", token,
                data={"upload_phase": "transfer",
                      "upload_session_id": session_id,
                      "start_offset": start_offset},
                files={"video_file_chunk": (path.name, chunk, "application/octet-stream")},
            )
            start_offset = int(resp["start_offset"])
            end_offset = int(resp["end_offset"])

    print(" " * 50, end="\r", file=sys.stderr)

    finish = dict(finish_data)
    finish.update({"upload_phase": "finish", "upload_session_id": session_id})
    graph_request("POST", f"{page_id}/videos", token, data=finish)
    return {"id": start["video_id"]}


def cmd_publish_video(args) -> int:
    """Dang video len feed. Duoi 100MB upload mot phat, tren thi chia chunk."""
    pages = resolve_pages(args.page)
    message = read_message(args.message)
    when = resolve_schedule(args)
    media = [check_media(args.video, "video")]

    path = Path(args.video)
    chunked = media[0]["size"] > CHUNKED_VIDEO_THRESHOLD
    label = "Video" + (" (chunked)" if chunked else "")
    if not confirm(args, preview(pages, label, media, message, when)):
        return 0

    def action(page, token):
        data = {"description": message}
        if args.title:
            data["title"] = args.title
        if when:
            data["published"] = "false"
            data["scheduled_publish_time"] = when

        if chunked:
            result = _upload_video_chunked(page["id"], token, path, data)
        else:
            with open(path, "rb") as fh:
                result = graph_request("POST", f"{page['id']}/videos", token,
                                       data=data, files={"source": fh})

        video_id = result.get("id")
        post_id = result.get("post_id")

        # /videos tra ve id cua VIDEO, khong phai id cua bai viet. Hai so nay
        # khac nhau, va ghep '{page_id}_{video_id}' ra mot id doc duoc nhung
        # KHONG phai bai - cancel/reschedule se tac dong sai doi tuong. Chinh
        # doi tuong video co truong post_id tro toi bai that, lay tu do.
        if not post_id and video_id:
            try:
                meta = graph_request("GET", video_id, token, params={"fields": "post_id"})
                post_id = meta.get("post_id")
            except PublishError:
                post_id = None

        return qualify_post_id(page["id"], post_id or video_id), {"video_id": video_id}

    return _for_each_page(pages, when, action)


def cmd_publish_reel(args) -> int:
    """Dang Reels theo quy trinh 3 buoc rieng cua Meta.

    Endpoint /video_reels khong nhan scheduled_publish_time, nen bai len song
    ngay. Muon hen gio Reels thi dung publish-video voi chinh file 9:16 do -
    Meta van xep thanh Reel.
    """
    if args.schedule:
        raise PublishError(
            "Endpoint /video_reels khong nhan scheduled_publish_time.\n"
            "  NHUNG van hen gio Reels duoc: dang chinh file 9:16 do qua\n"
            "    publish-video --schedule \"<gio>\"\n"
            "  Meta van xep thanh Reel (permalink dang /reel/...), xac minh\n"
            "  tren 7 page ngay 09/09/2026.\n"
            "  Hoac bo --schedule de dang Reels ngay bay gio."
        )

    pages = resolve_pages(args.page)
    message = read_message(args.message)
    media = [check_media(args.video, "video", is_reel=True)]

    summary = preview(pages, "Reels (len song ngay, khong huy duoc bang cancel)",
                      media, message, 0)
    if not confirm(args, summary):
        return 0

    path = Path(args.video)
    size = path.stat().st_size

    def action(page, token):
        # Buoc 1: xin cho chua video, nhan video_id + upload_url.
        start = graph_request("POST", f"{page['id']}/video_reels", token,
                              data={"upload_phase": "start"})
        video_id = start["video_id"]
        version = config.resolve("META_API_VERSION", "v21.0")
        upload_url = (start.get("upload_url")
                      or f"{RUPLOAD_HOST}/video-upload/{version}/{video_id}")

        # Buoc 2: day file nhi phan len host rupload (khong phai graph.facebook.com).
        print(f"  Upload {_human_size(size)}...", file=sys.stderr)
        with open(path, "rb") as fh:
            resp = requests.post(
                upload_url,
                headers={"Authorization": f"OAuth {token}",
                         "offset": "0",
                         "file_size": str(size)},
                data=fh,
                timeout=1800,
            )
        if not resp.ok:
            raise PublishError(
                f"Upload Reels that bai (HTTP {resp.status_code}): {resp.text[:300]}")

        # Buoc 3: chot va cho dang.
        graph_request("POST", f"{page['id']}/video_reels", token,
                      data={"upload_phase": "finish",
                            "video_id": video_id,
                            "video_state": "PUBLISHED",
                            "description": message})

        return video_id, {"video_id": video_id,
                          "permalink": f"https://www.facebook.com/reel/{video_id}"}

    code = _for_each_page(pages, 0, action, fetch_permalink=False)
    print("\nMeta can vai phut de xu ly video truoc khi Reels hien tren page.")
    return code


# --- Lenh: quan ly bai da hen gio ------------------------------------------

def cmd_list_scheduled(args) -> int:
    """Liet ke bai dang cho den gio dang tren mot page."""
    page = config.resolve_page(args.page)
    token = page_token(page["id"])
    fields = "id,message,scheduled_publish_time,created_time"

    try:
        data = graph_request("GET", f"{page['id']}/scheduled_posts", token,
                             params={"fields": fields, "limit": 100})
    except PublishError:
        # Edge scheduled_posts khong phai luc nao cung dung duoc; feed voi
        # is_published=false cho ket qua tuong duong.
        data = graph_request("GET", f"{page['id']}/feed", token,
                             params={"fields": fields, "is_published": "false",
                                     "limit": 100})

    posts = data.get("data", [])
    if not posts:
        print(f"Page {page['code']} khong co bai nao dang cho dang.")
        # Hai ly do rat khac nhau cho cung mot ket qua rong.
        print("  - Vua dang video? Meta xu ly video bat dong bo, bai chi hien sau vai")
        print("    chuc giay. Doi mot lat roi chay lai truoc khi ket luan la hong.")
        print("  - Neu doi van khong thay: kiem scope pages_read_user_content bang")
        print("    python fb_page_publish.py check-auth")
        return 0

    print(f"Bai dang cho tren page {page['code']} ({len(posts)}):\n")
    print(f"{'POST ID':<26}  {'GIO DANG':<17}  NOI DUNG")
    for post in posts:
        when = config.format_timestamp(post.get("scheduled_publish_time"))
        text = (post.get("message") or "").replace("\n", " ")[:60]
        print(f"{post['id']:<26}  {when:<17}  {text}")
    return 0


def cmd_reschedule(args) -> int:
    """Doi gio dang cua mot bai da hen."""
    when = config.parse_schedule(args.schedule)
    token = token_for_post(args.post_id)
    graph_request("POST", args.post_id, token, data={"scheduled_publish_time": when})
    print(f"Da doi gio dang bai {args.post_id} sang {config.format_timestamp(when)}.")
    return 0


def cmd_publish_now(args) -> int:
    """Dang ngay mot bai dang cho hen gio."""
    token = token_for_post(args.post_id)
    graph_request("POST", args.post_id, token, data={"is_published": "true"})
    try:
        data = graph_request("GET", args.post_id, token, params={"fields": "permalink_url"})
        link = data.get("permalink_url", "")
    except PublishError:
        link = ""
    print(f"Da dang bai {args.post_id}. {link}")
    return 0


def cmd_cancel(args) -> int:
    """Xoa mot bai da hen gio."""
    token = token_for_post(args.post_id)
    if not args.yes and sys.stdin.isatty():
        if input(f"Xoa bai {args.post_id}? [y/N] ").strip().lower() not in ("y", "yes"):
            print("Da huy.")
            return 0
    graph_request("DELETE", args.post_id, token)
    print(f"Da xoa bai {args.post_id}.")
    return 0


# --- CLI -------------------------------------------------------------------

def _add_publish_flags(parser, schedule: bool = True):
    """Cac co dung chung cho moi lenh dang bai."""
    parser.add_argument(
        "--page", required=True,
        help="Ma ngan, Page ID hoac ten page. Nhieu page: ngan cach bang dau phay")
    parser.add_argument("--message", default="",
                        help="Noi dung bai, hoac @duong/dan/file.txt de doc tu file")
    if schedule:
        parser.add_argument("--schedule",
                            help="Gio dang: '2026-09-10 19:30', '10/09 19:30', '+2h'")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chi in ban xem truoc, khong goi API")
    parser.add_argument("--yes", action="store_true", help="Bo qua buoc hoi xac nhan")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fb_page_publish.py",
        description="Dang anh, album, video, Reels len fanpage Facebook qua Graph API.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check-auth", help="Kiem tra token, scope va quyen tren tung page")
    sub.add_parser("list-pages", help="In bang fanpage dang cau hinh trong .env")

    p = sub.add_parser("publish-photo", help="Dang mot anh")
    _add_publish_flags(p)
    p.add_argument("--image", required=True, help="Duong dan file anh tren dia")

    p = sub.add_parser("publish-album", help="Dang nhieu anh thanh mot bai")
    _add_publish_flags(p)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--images", help="Danh sach duong dan, ngan cach bang dau phay")
    group.add_argument("--images-dir", help="Thu muc anh, sap xep theo ten file")

    p = sub.add_parser("publish-video", help="Dang video len feed")
    _add_publish_flags(p)
    p.add_argument("--video", required=True, help="Duong dan file video tren dia")
    p.add_argument("--title", help="Tieu de video (tuy chon)")

    p = sub.add_parser("publish-reel", help="Dang Reels ngay (hen gio thi dung publish-video)")
    _add_publish_flags(p, schedule=False)
    p.add_argument("--video", required=True, help="Duong dan file video doc 9:16")
    p.add_argument("--schedule", help=argparse.SUPPRESS)

    p = sub.add_parser("list-scheduled", help="Xem cac bai dang cho den gio dang")
    p.add_argument("--page", required=True, help="Ma ngan, Page ID hoac ten page")

    p = sub.add_parser("reschedule", help="Doi gio dang cua mot bai da hen")
    p.add_argument("--post-id", required=True)
    p.add_argument("--schedule", required=True, help="Gio moi")

    p = sub.add_parser("publish-now", help="Dang ngay mot bai dang cho")
    p.add_argument("--post-id", required=True)

    p = sub.add_parser("cancel", help="Xoa mot bai da hen gio")
    p.add_argument("--post-id", required=True)
    p.add_argument("--yes", action="store_true", help="Khong hoi lai")

    return parser


HANDLERS = {
    "check-auth": cmd_check_auth,
    "list-pages": cmd_list_pages,
    "publish-photo": cmd_publish_photo,
    "publish-album": cmd_publish_album,
    "publish-video": cmd_publish_video,
    "publish-reel": cmd_publish_reel,
    "list-scheduled": cmd_list_scheduled,
    "reschedule": cmd_reschedule,
    "publish-now": cmd_publish_now,
    "cancel": cmd_cancel,
}


def main() -> int:
    args = build_parser().parse_args()
    try:
        return HANDLERS[args.command](args)
    except (PublishError, config.ConfigError) as exc:
        print(f"\nLOI: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nDa dung.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
