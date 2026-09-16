#!/usr/bin/env python3
"""Lay media va noi dung tu Google Drive bang service account.

Mot viec duy nhat: bien link Drive / Google Docs thanh file tren dia hoac
thanh text. Viec dang bai do fb_page_publish.py lo.

    python drive_client.py whoami
    python drive_client.py fetch --url <link anh/video> --out ./media
    python drive_client.py fetch-folder --url <link folder> --types image
    python drive_client.py read-doc --url <link google docs>
"""

import argparse
import io
import json
import re
import sys
from pathlib import Path

import config

DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"

# Google Docs khong tai thang duoc, phai export sang dinh dang khac.
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
SHORTCUT_MIME = "application/vnd.google-apps.shortcut"
FOLDER_MIME = "application/vnd.google-apps.folder"

FILE_FIELDS = "id,name,mimeType,size,shortcutDetails"

# Ky tu Windows khong cho phep dat trong ten file.
_UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Cac dang link Drive/Docs deu chua id o mot trong 3 vi tri nay.
_ID_PATTERNS = (
    re.compile(r"/(?:file|document|spreadsheets|presentation)/d/([A-Za-z0-9_-]{10,})"),
    re.compile(r"/folders/([A-Za-z0-9_-]{10,})"),
    re.compile(r"[?&]id=([A-Za-z0-9_-]{10,})"),
)


class DriveError(Exception):
    """Loi da dich sang thong diep nguoi dung doc duoc."""


def extract_id(url: str) -> str:
    """Boc file id tu moi dang link Drive, hoac tra lai chinh id neu da la id."""
    if not url:
        raise DriveError("Chua co link Drive.")
    url = url.strip()

    for pattern in _ID_PATTERNS:
        m = pattern.search(url)
        if m:
            return m.group(1)

    # Nguoi dung dan thang id thay vi ca link.
    if re.fullmatch(r"[A-Za-z0-9_-]{10,}", url):
        return url

    raise DriveError(
        f"Khong boc duoc file id tu '{url}'.\n"
        "  Dang hop le: https://drive.google.com/file/d/<ID>/view\n"
        "               https://drive.google.com/drive/folders/<ID>\n"
        "               https://docs.google.com/document/d/<ID>/edit"
    )


def service_account_email() -> str:
    """Email cua service account - can share file/folder cho email nay."""
    data = json.loads(config.credentials_path().read_text(encoding="utf-8"))
    return data.get("client_email", "")


def _build(api: str, version: str, scope: str):
    """Google API client tu service account JSON key."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise DriveError(
            f"Thieu thu vien Google ({exc}).\n"
            "  Cai bang: pip install -r requirements.txt"
        ) from exc

    creds = service_account.Credentials.from_service_account_file(
        str(config.credentials_path()), scopes=[scope]
    )
    return build(api, version, credentials=creds, cache_discovery=False)


def build_service():
    """Drive API client."""
    return _build("drive", "v3", DRIVE_SCOPE)


def build_sheets_service():
    """Sheets API client - dung cho lenh read-cell."""
    return _build("sheets", "v4", SHEETS_SCOPE)


def extract_gid(url: str):
    """So hieu tab (gid) trong link Sheets, hoac None neu link khong co."""
    m = re.search(r"[#&]gid=(\d+)", url or "")
    return int(m.group(1)) if m else None


def _translate_http_error(exc, file_id: str = "") -> DriveError:
    """Doi loi HTTP cua Google thanh huong dan sua cu the.

    Ba loi hay gap nhat deu tra ve 403/404 nhung nguyen nhan khac han nhau,
    nen phai tach ra thi nguoi dung moi biet phai lam gi.
    """
    text = str(exc)
    email = ""
    try:
        email = service_account_email()
    except Exception:
        pass

    if "has not been used in project" in text or "accessNotConfigured" in text:
        project = ""
        m = re.search(r"project (\d+)", text)
        if m:
            project = m.group(1)
        return DriveError(
            "Google Drive API dang TAT trong project cua service account.\n"
            "  Bat tai: https://console.cloud.google.com/apis/library/drive.googleapis.com"
            + (f"?project={project}" if project else "")
            + "\n  Bat xong doi 1-2 phut roi chay lai."
        )

    if "404" in text or "notFound" in text:
        return DriveError(
            f"Khong thay file/folder id '{file_id}'.\n"
            "  Hoac id sai, hoac file chua duoc share cho service account:\n"
            f"    {email or '(chay `python drive_client.py whoami` de lay email)'}\n"
            "  Mo file tren Drive > Share > dan email tren > quyen Viewer."
        )

    if "403" in text or "forbidden" in text.lower():
        return DriveError(
            f"Khong co quyen doc file id '{file_id}'.\n"
            f"  Share file cho service account: {email}\n"
            "  Neu file thuoc Shared Drive, phai them service account vao Shared Drive do."
        )

    if "exceeds grid limits" in text:
        return DriveError(
            "O hoac vung ban yeu cau nam ngoai pham vi bang tinh.\n"
            f"  {text.split('returned')[-1].strip()[:160]}"
        )

    return DriveError(f"Loi Google API: {text}")


def get_metadata(service, file_id: str) -> dict:
    """Thong tin file; shortcut duoc giai sang file that truoc khi tra ve."""
    try:
        meta = service.files().get(
            fileId=file_id, fields=FILE_FIELDS, supportsAllDrives=True
        ).execute()
    except Exception as exc:
        raise _translate_http_error(exc, file_id) from exc

    # Shortcut chi la con tro, tai thang se ra file rong.
    if meta.get("mimeType") == SHORTCUT_MIME:
        target = (meta.get("shortcutDetails") or {}).get("targetId")
        if not target:
            raise DriveError(f"Shortcut '{meta.get('name')}' khong tro toi file nao.")
        return get_metadata(service, target)

    return meta


def safe_filename(name: str) -> str:
    """Ten file an toan tren Windows, van giu dau tieng Viet."""
    cleaned = _UNSAFE_CHARS.sub("_", name).strip().rstrip(".")
    return cleaned or "drive-file"


def download_file(service, meta: dict, out_dir: Path, quiet: bool = False) -> dict:
    """Tai mot file nhi phan ve dia, ghi theo chunk de file lon khong ngon RAM."""
    from googleapiclient.http import MediaIoBaseDownload

    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / safe_filename(meta["name"])

    request = service.files().get_media(fileId=meta["id"], supportsAllDrives=True)
    buffer = io.FileIO(dest, "wb")
    try:
        downloader = MediaIoBaseDownload(buffer, request, chunksize=1024 * 1024)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status and not quiet:
                print(f"  {meta['name']}: {int(status.progress() * 100)}%",
                      end="\r", file=sys.stderr)
    except Exception as exc:
        buffer.close()
        dest.unlink(missing_ok=True)
        raise _translate_http_error(exc, meta["id"]) from exc
    finally:
        if not buffer.closed:
            buffer.close()

    if not quiet:
        print(" " * 50, end="\r", file=sys.stderr)

    return {
        "path": str(dest),
        "name": meta["name"],
        "mime_type": meta.get("mimeType", ""),
        "size": dest.stat().st_size,
    }


def list_folder(service, folder_id: str, types: str = "all") -> list:
    """Liet ke file trong folder, sap theo ten - chinh la thu tu anh trong album."""
    mime_filter = {
        "image": " and mimeType contains 'image/'",
        "video": " and mimeType contains 'video/'",
        "all": "",
    }.get(types, "")

    query = f"'{folder_id}' in parents and trashed = false{mime_filter}"
    files, page_token = [], None
    try:
        while True:
            resp = service.files().list(
                q=query,
                orderBy="name_natural",
                fields=f"nextPageToken, files({FILE_FIELDS})",
                pageSize=100,
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute()
            files.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    except Exception as exc:
        raise _translate_http_error(exc, folder_id) from exc

    return [f for f in files if f.get("mimeType") != FOLDER_MIME]


# --- Cac lenh CLI ----------------------------------------------------------

def cmd_whoami(args) -> int:
    """Chan doan: in email service account va kiem tra Drive API con song."""
    email = service_account_email()
    print(f"Service account : {email}")
    print(f"Key file        : {config.credentials_path()}")
    try:
        service = build_service()
        service.files().list(pageSize=1, fields="files(id)").execute()
        print("Drive API       : OK")
        print("\nNho share folder media va file Google Docs cho email tren (quyen Viewer).")
        return 0
    except DriveError as exc:
        print(f"Drive API       : LOI\n\n{exc}")
        return 1
    except Exception as exc:
        print(f"Drive API       : LOI\n\n{_translate_http_error(exc)}")
        return 1


def cmd_fetch(args) -> int:
    """Tai mot file ve dia, in JSON mo ta file da tai."""
    service = build_service()
    meta = get_metadata(service, extract_id(args.url))

    mime = meta.get("mimeType", "")
    if mime == FOLDER_MIME:
        raise DriveError(
            f"'{meta['name']}' la mot folder, khong phai file.\n"
            "  Dung `fetch-folder` de tai toan bo media trong folder."
        )
    if mime.startswith("application/vnd.google-apps"):
        raise DriveError(
            f"'{meta['name']}' la file Google Docs/Sheets, khong phai media.\n"
            "  Dung `read-doc` de lay noi dung text."
        )

    out_dir = Path(args.out) if args.out else config.download_dir()
    result = download_file(service, meta, out_dir, quiet=args.quiet)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_fetch_folder(args) -> int:
    """Tai toan bo media trong folder, in JSON array theo thu tu ten file."""
    service = build_service()
    folder_id = extract_id(args.url)
    files = list_folder(service, folder_id, args.types)

    if not files:
        raise DriveError(
            f"Folder khong co file nao khop loai '{args.types}'.\n"
            "  Kiem tra lai folder, hoac doi --types thanh all."
        )

    out_dir = Path(args.out) if args.out else config.download_dir()
    results = []
    for idx, meta in enumerate(files, 1):
        if not args.quiet:
            print(f"[{idx}/{len(files)}] {meta['name']}", file=sys.stderr)
        results.append(download_file(service, meta, out_dir, quiet=args.quiet))

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


def cmd_read_doc(args) -> int:
    """Lay noi dung caption tu Google Docs (hoac file .txt tai len Drive)."""
    service = build_service()
    file_id = extract_id(args.url)
    meta = get_metadata(service, file_id)
    mime = meta.get("mimeType", "")

    export_mime = "text/markdown" if args.format == "markdown" else "text/plain"
    try:
        if mime == GOOGLE_DOC_MIME:
            raw = service.files().export_media(fileId=meta["id"], mimeType=export_mime).execute()
        elif mime.startswith("text/"):
            raw = service.files().get_media(fileId=meta["id"], supportsAllDrives=True).execute()
        else:
            raise DriveError(
                f"'{meta['name']}' co dinh dang {mime}, khong doc duoc thanh text.\n"
                "  Chi ho tro Google Docs hoac file text (.txt, .md)."
            )
    except DriveError:
        raise
    except Exception as exc:
        raise _translate_http_error(exc, file_id) from exc

    text = raw.decode("utf-8-sig", errors="replace").replace("\r\n", "\n").strip()

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Da ghi {len(text)} ky tu vao {args.out}", file=sys.stderr)
        print(args.out)
    else:
        print(text)
    return 0


def cmd_read_cell(args) -> int:
    """Doc noi dung mot o Google Sheets thanh text.

    Caption cua doi content thuong nam trong mot o cua bang ke hoach noi dung,
    khong phai trong Google Docs. Lenh nay doc thang o do de khoi phai muon
    skill khac.
    """
    service = build_sheets_service()
    sheet_id = extract_id(args.url)
    cell = args.cell.strip()

    # Chua chi dinh tab: suy ra tu gid trong link, hoac tu --sheet.
    if "!" not in cell:
        tab = args.sheet
        if not tab:
            gid = extract_gid(args.url)
            try:
                meta = service.spreadsheets().get(
                    spreadsheetId=sheet_id, fields="sheets.properties"
                ).execute()
            except Exception as exc:
                raise _translate_http_error(exc, sheet_id) from exc

            props = [s["properties"] for s in meta.get("sheets", [])]
            if gid is not None:
                match = [p for p in props if p.get("sheetId") == gid]
                if not match:
                    names = ", ".join(p["title"] for p in props)
                    raise DriveError(
                        f"Khong co tab nao gid={gid} trong bang tinh.\n"
                        f"  Cac tab hien co: {names}"
                    )
                tab = match[0]["title"]
            else:
                tab = props[0]["title"] if props else ""
        cell = f"'{tab}'!{cell}" if tab else cell

    try:
        resp = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=cell,
            valueRenderOption="FORMATTED_VALUE",
        ).execute()
    except Exception as exc:
        raise _translate_http_error(exc, sheet_id) from exc

    rows = resp.get("values", [])
    if not rows or not rows[0] or not str(rows[0][0]).strip():
        raise DriveError(f"O {cell} trong, khong co noi dung.")

    text = str(rows[0][0]).replace("\r\n", "\n").strip()

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Da ghi {len(text)} ky tu tu {cell} vao {args.out}", file=sys.stderr)
        print(args.out)
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="drive_client.py",
        description="Tai media va doc noi dung tu Google Drive bang service account.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("whoami", help="In email service account + kiem tra Drive API")

    p = sub.add_parser("fetch", help="Tai mot file media ve dia")
    p.add_argument("--url", required=True, help="Link Drive hoac file id")
    p.add_argument("--out", help="Thu muc luu (mac dinh DRIVE_DOWNLOAD_DIR)")
    p.add_argument("--quiet", action="store_true", help="An tien do tai")

    p = sub.add_parser("fetch-folder", help="Tai toan bo media trong mot folder")
    p.add_argument("--url", required=True, help="Link folder Drive hoac folder id")
    p.add_argument("--out", help="Thu muc luu (mac dinh DRIVE_DOWNLOAD_DIR)")
    p.add_argument("--types", choices=("image", "video", "all"), default="all",
                   help="Loc theo loai file (mac dinh all)")
    p.add_argument("--quiet", action="store_true", help="An tien do tai")

    p = sub.add_parser("read-doc", help="Doc noi dung Google Docs thanh text")
    p.add_argument("--url", required=True, help="Link Google Docs hoac file id")
    p.add_argument("--format", choices=("text", "markdown"), default="text")
    p.add_argument("--out", help="Ghi ra file thay vi in ra man hinh")

    p = sub.add_parser("read-cell", help="Doc mot o Google Sheets thanh text")
    p.add_argument("--url", required=True,
                   help="Link Google Sheets (giu nguyen phan #gid=... de tu nhan tab)")
    p.add_argument("--cell", required=True,
                   help="O can doc, vi du F19 hoac \"'Content 9'!F19\"")
    p.add_argument("--sheet", help="Ten tab, dung khi link khong co gid")
    p.add_argument("--out", help="Ghi ra file thay vi in ra man hinh")

    return parser


HANDLERS = {
    "whoami": cmd_whoami,
    "fetch": cmd_fetch,
    "fetch-folder": cmd_fetch_folder,
    "read-doc": cmd_read_doc,
    "read-cell": cmd_read_cell,
}


def main() -> int:
    args = build_parser().parse_args()
    try:
        return HANDLERS[args.command](args)
    except (DriveError, config.ConfigError) as exc:
        print(f"\nLOI: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
