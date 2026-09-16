#!/usr/bin/env python3
"""Lop cau hinh dung chung cho skill ak:fb-page-publish.

Gom vao mot cho: doc bien moi truong, bang fanpage, va viec doi gio hen dang
do nguoi dung nhap sang unix timestamp ma Graph API hieu duoc.

Chay truc tiep file nay de tu kiem tra cau hinh:
    python config.py
"""

import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent

# Ten page tieng Viet co dau se vo tren console cp1252 mac dinh cua Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Bo resolve env tap trung cua AgentKit neu co; khong thi dung python-dotenv.
_claude_scripts = _SCRIPTS_DIR.parents[2] / "scripts"
if _claude_scripts.exists():
    sys.path.insert(0, str(_claude_scripts))
try:
    from resolve_env import resolve_env as _resolve_env  # type: ignore
except ImportError:
    _resolve_env = None
    try:
        from dotenv import load_dotenv
    except ImportError:
        load_dotenv = None

_ENV_LOADED = False

# Skill anh em giu token Meta dung chung; token cua skill nay bo trong thi
# ke thua tu do thay vi bat nguoi dung dan lai lan nua.
_ADS_ENV = _SCRIPTS_DIR.parents[1] / "ak-ads-management" / "scripts" / ".env"

GRAPH_HOST = "https://graph.facebook.com"

# Gioi han cua Meta cho bai hen gio, tinh tu thoi diem goi API.
SCHEDULE_MIN_LEAD = timedelta(minutes=10)
SCHEDULE_MAX_LEAD = timedelta(days=180)


class ConfigError(Exception):
    """Cau hinh thieu hoac sai - thong diep da san sang in cho nguoi dung."""


def _load_env_files():
    """Nap .env cua skill nay vao os.environ (mot lan cho moi tien trinh).

    Chay ca khi co resolve_env cua AgentKit: bo resolve do tim theo ten skill
    khong co tien to 'ak-', nen se khong thay .env cua thu muc nay.
    """
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    if not load_dotenv:
        return
    for env_file in (_SCRIPTS_DIR.parent / ".env", _SCRIPTS_DIR / ".env"):
        if env_file.exists():
            load_dotenv(env_file, override=False)


def _read_env_file(path: Path, key: str) -> str:
    """Doc mot khoa tu file .env bat ky, khong dung toi os.environ."""
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == key:
            return v.strip().strip("\"'")
    return ""


def resolve(name: str, default: str = "") -> str:
    """Lay gia tri bien moi truong theo thu tu uu tien cua AgentKit.

    META_ACCESS_TOKEN la truong hop dac biet: rong thi lay tiep tu .env cua
    skill ak-ads-management, vi hai skill dung chung mot System User token.
    """
    _load_env_files()
    val = os.getenv(name, "")
    if not val and _resolve_env:
        val = _resolve_env(name, skill="fb-page-publish") or ""

    if not val and name == "META_ACCESS_TOKEN":
        val = _read_env_file(_ADS_ENV, name)

    return val or default


def graph_url(path: str) -> str:
    """Ghep URL Graph API day du, vi du graph_url('me/accounts')."""
    version = resolve("META_API_VERSION", "v21.0")
    return f"{GRAPH_HOST}/{version}/{path.lstrip('/')}"


def access_token() -> str:
    """Token Meta dang dung; raise neu chua cau hinh o dau ca."""
    token = resolve("META_ACCESS_TOKEN")
    if not token:
        message = ("Chua co META_ACCESS_TOKEN.\n"
                   f"  Dien vao {_SCRIPTS_DIR / '.env'}")
        # Chi nhac toi skill anh em khi no that su co mat: ban skill copy di
        # noi khac khong co no, nhac ra chi lam nguoi dung di tim vo ich.
        if _ADS_ENV.exists():
            message += f"\n  hoac de trong de ke thua tu {_ADS_ENV}"
        message += "\n  Cach lay token: references/setup-permissions.md"
        raise ConfigError(message)
    return token


def credentials_path() -> Path:
    """Duong dan tuyet doi toi file JSON key cua service account Google."""
    raw = resolve("GOOGLE_DRIVE_CREDENTIALS")
    if not raw:
        raise ConfigError(
            "Chua co GOOGLE_DRIVE_CREDENTIALS.\n"
            f"  Tro toi file JSON key cua service account trong {_SCRIPTS_DIR / '.env'}"
        )
    path = Path(raw)
    if not path.is_absolute():
        path = _SCRIPTS_DIR / path
    if not path.exists():
        raise ConfigError(f"Khong tim thay file key Google: {path}")
    return path


def download_dir() -> Path:
    """Thu muc luu media tai tu Drive. Bo trong => thu muc temp cua he dieu hanh."""
    raw = resolve("DRIVE_DOWNLOAD_DIR")
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = _SCRIPTS_DIR / path
    else:
        import tempfile
        path = Path(tempfile.gettempdir()) / "fb-page-publish"
    path.mkdir(parents=True, exist_ok=True)
    return path


def ffprobe_path() -> str:
    """Duong dan toi ffprobe, hoac chuoi rong neu may khong co.

    Tim theo thu tu: FFPROBE_PATH trong .env -> PATH cua tien trinh -> thu muc
    goi winget cua Gyan.FFmpeg. Buoc cuoi la vi winget them PATH o muc User,
    nen shell dang mo san tu truoc khi cai se khong thay ffprobe.
    """
    import shutil

    configured = resolve("FFPROBE_PATH")
    if configured and Path(configured).exists():
        return configured

    found = shutil.which("ffprobe")
    if found:
        return found

    winget_pkgs = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if winget_pkgs.exists():
        for exe in winget_pkgs.glob("Gyan.FFmpeg*/**/bin/ffprobe.exe"):
            return str(exe)

    return ""


def load_pages() -> list:
    """Doc bang fanpage FB_PAGE_*_N, dung khi hut so thu tu.

    Tra ve list dict {code, id, name}, giu nguyen thu tu khai bao trong .env.
    """
    pages = []
    idx = 1
    while True:
        page_id = resolve(f"FB_PAGE_ID_{idx}")
        if not page_id:
            break
        pages.append({
            "code": resolve(f"FB_PAGE_CODE_{idx}", page_id),
            "id": page_id,
            "name": resolve(f"FB_PAGE_NAME_{idx}", ""),
        })
        idx += 1

    if not pages:
        raise ConfigError(
            "Bang fanpage trong. Khai bao FB_PAGE_CODE_1 / FB_PAGE_ID_1 / "
            f"FB_PAGE_NAME_1 trong {_SCRIPTS_DIR / '.env'}.\n"
            "Lay Page ID bang: python fb_page_publish.py check-auth"
        )
    return pages


def pages_table(pages: list) -> str:
    """Bang page dang text, dung chung cho thong bao loi va lenh list-pages."""
    width = max((len(p["code"]) for p in pages), default=4)
    lines = [f"  {p['code']:<{width}}  {p['id']:<18}  {p['name']}" for p in pages]
    return "\n".join(lines)


def resolve_page(ref: str) -> dict:
    """Tim page theo ma ngan, Page ID, hoac mot phan ten.

    Khop theo 3 vong, dung o vong dau tien co ket qua: ma ngan (bo qua hoa
    thuong) -> Page ID -> ten chua chuoi tim kiem. Khop nhieu hon mot page thi
    raise, vi dang nham page la loi khong rut lai duoc mot cach em tham.
    """
    if not ref:
        raise ConfigError("Chua chi dinh page. Dung --page <ma|id|ten>.")

    pages = load_pages()
    needle = ref.strip().lower()

    exact_code = [p for p in pages if p["code"].lower() == needle]
    if len(exact_code) == 1:
        return exact_code[0]

    by_id = [p for p in pages if p["id"] == ref.strip()]
    if len(by_id) == 1:
        return by_id[0]

    by_name = [p for p in pages if needle in p["name"].lower()]
    if len(by_name) == 1:
        return by_name[0]

    matched = by_name or exact_code
    if len(matched) > 1:
        raise ConfigError(
            f"'{ref}' khop {len(matched)} page, khong ro chon cai nao:\n"
            + pages_table(matched)
            + "\nDung ma ngan hoac Page ID cho chinh xac."
        )

    raise ConfigError(
        f"Khong tim thay page nao khop '{ref}'. Cac page dang cau hinh:\n"
        + pages_table(pages)
    )


def local_timezone():
    """Mui gio dung de hieu gio nguoi dung nhap va de in gio ra man hinh.

    Nhan ten vung IANA (Asia/Bangkok) hoac UTC offset (UTC+7, UTC-05:00).
    Khong nhan dang duoc thi lui ve UTC+7.
    """
    name = resolve("DEFAULT_TIMEZONE", "Asia/Bangkok").strip()
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:
        pass
    m = re.match(r"^UTC([+-])(\d{1,2})(?::?(\d{2}))?$", name, re.IGNORECASE)
    if m:
        sign = 1 if m.group(1) == "+" else -1
        offset = timedelta(hours=int(m.group(2)), minutes=int(m.group(3) or 0))
        return timezone(sign * offset)
    return timezone(timedelta(hours=7))


_DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d-%m-%Y %H:%M",
    "%Y/%m/%d %H:%M",
    "%d/%m %H:%M",       # nam mac dinh la nam hien tai
    "%H:%M",             # ngay mac dinh la hom nay
)


def parse_schedule(text: str) -> int:
    """Doi gio hen dang sang unix timestamp, kiem tra gioi han cua Meta.

    Nhan: '2026-09-10 19:30', '10/09/2026 19:30', '10/09 19:30', '19:30',
    '+2h', '+90m', '+3d', hoac chinh unix timestamp.
    Gio nhap duoc hieu theo DEFAULT_TIMEZONE.
    """
    if not text:
        raise ConfigError("Chua co thoi gian hen dang.")

    text = text.strip()
    tz = local_timezone()
    now = datetime.now(tz)

    # Dang tuong doi: +2h, +90m, +3d
    rel = re.match(r"^\+\s*(\d+)\s*([mhd])$", text, re.IGNORECASE)
    if rel:
        amount, unit = int(rel.group(1)), rel.group(2).lower()
        delta = {"m": timedelta(minutes=amount),
                 "h": timedelta(hours=amount),
                 "d": timedelta(days=amount)}[unit]
        target = now + delta
    elif text.isdigit() and len(text) == 10:
        target = datetime.fromtimestamp(int(text), tz)
    else:
        target = None
        for fmt in _DATETIME_FORMATS:
            try:
                parsed = datetime.strptime(text, fmt)
            except ValueError:
                continue
            # Bo sung phan ngay/nam ma dinh dang ngan khong co.
            if "%Y" not in fmt and "%y" not in fmt:
                parsed = parsed.replace(year=now.year)
            if "%d" not in fmt:
                parsed = parsed.replace(month=now.month, day=now.day)
            target = parsed.replace(tzinfo=tz)
            break
        if target is None:
            raise ConfigError(
                f"Khong hieu thoi gian '{text}'.\n"
                "  Dang ho tro: '2026-09-10 19:30', '10/09/2026 19:30',\n"
                "               '10/09 19:30', '19:30', '+2h', '+90m', '+3d'"
            )

    lead = target - now
    if lead < SCHEDULE_MIN_LEAD:
        minutes = int(lead.total_seconds() // 60)
        raise ConfigError(
            "Meta yeu cau hen gio cach hien tai it nhat 10 phut.\n"
            f"  Gio nhap: {target:%d/%m/%Y %H:%M} (con {minutes} phut)"
        )
    if lead > SCHEDULE_MAX_LEAD:
        raise ConfigError(
            "Meta chi cho hen gio toi da 6 thang.\n"
            f"  Gio nhap: {target:%d/%m/%Y %H:%M} (con {lead.days} ngay)"
        )
    return int(target.timestamp())


def format_timestamp(ts) -> str:
    """Unix timestamp -> chuoi gio dia phuong de in ra man hinh."""
    if not ts:
        return "-"
    try:
        return datetime.fromtimestamp(int(ts), local_timezone()).strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError, OSError):
        return str(ts)


def _self_test():
    """Kiem tra nhanh cau hinh, dung khi chay `python config.py`."""
    print(f"Thu muc scripts : {_SCRIPTS_DIR}")
    print(f"Mui gio         : {resolve('DEFAULT_TIMEZONE', 'Asia/Bangkok')}")
    print(f"Graph API       : {graph_url('me/accounts')}")

    token = resolve("META_ACCESS_TOKEN")
    if token:
        own = bool(_read_env_file(_SCRIPTS_DIR / ".env", "META_ACCESS_TOKEN"))
        source = ".env cua skill nay" if own else "ke thua ak-ads-management"
        print(f"Token Meta      : co ({len(token)} ky tu, {source})")
    else:
        print("Token Meta      : CHUA CO")

    try:
        print(f"Drive key       : {credentials_path()}")
    except ConfigError as exc:
        print(f"Drive key       : {exc}")

    print(f"Thu muc tai ve  : {download_dir()}")
    print(f"ffprobe         : {ffprobe_path() or 'KHONG CO (bo qua kiem tra video)'}")

    pages = load_pages()
    print(f"\nFanpage da cau hinh ({len(pages)}):")
    print(pages_table(pages))

    print("\nThu doc gio hen dang:")
    for sample in ("+2h", "+30m", "25/12/2026 08:00"):
        print(f"  {sample:<18} -> {format_timestamp(parse_schedule(sample))}")

    print("\nThu tim page:")
    for sample in (pages[0]["code"], pages[-1]["id"]):
        p = resolve_page(sample)
        print(f"  {sample:<18} -> {p['code']} / {p['name']}")


if __name__ == "__main__":
    try:
        _self_test()
    except ConfigError as exc:
        print(f"LOI CAU HINH: {exc}", file=sys.stderr)
        sys.exit(1)
