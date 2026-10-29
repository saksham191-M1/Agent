"""Bounded, unauthenticated public-marketing importer. Never executes website code.

The resolver and single-request transport are intentionally separate test seams.
Every request, including redirects and robots.txt, uses a validated, pinned IP
with the original hostname for TLS certificate verification and SNI. No browser,
proxy, cookies, credentials, query strings, remote fonts, or AI are involved.
"""
from __future__ import annotations

import http.client
import fnmatch
import io
import ipaddress
import json
import re
import socket
import ssl
import threading
import queue
import time
import warnings as python_warnings
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from .models import StudioError

USER_AGENT = "JarvisStudioDiscovery/1.0 (public marketing import; no scripts or login)"
ROBOT_AGENT = "JarvisStudioDiscovery"
MAX_PAGES = 3
MAX_CSS = 2
MAX_IMAGES = 2
MAX_REQUESTS = 18
MAX_REDIRECTS = 3
MAX_CANDIDATES = 32
MAX_PIXELS = 16_000_000
MAX_TOTAL_BYTES = 14 * 1024 * 1024
DEADLINE_SECONDS = 35
BYTE_CAPS = {"html": 1024 * 1024, "css": 256 * 1024,
             "image": 5 * 1024 * 1024, "robots": 128 * 1024}
_TYPES = {"html": {"text/html", "application/xhtml+xml"},
          "css": {"text/css"}, "robots": {"text/plain"},
          "image": {"image/png", "image/jpeg", "image/webp", "image/gif",
                    "image/bmp", "image/x-icon", "image/vnd.microsoft.icon"}}
_PRIVATE_PATH = re.compile(
    r"(?:^|/)(?:login|log-in|signin|sign-in|signout|logout|admin|wp-admin|"
    r"account|accounts|dashboard|console|settings|oauth|authorize|auth|"
    r"session|token|reset-password|invite|private|api)(?:/|$)", re.I)
_EXCLUDE = re.compile(
    r"\b(?:nav|navigation|footer|header|legal|pricing|price|privacy|terms|cookie|"
    r"copyright|subscribe|newsletter|sign[ -]?up|sign[ -]?in|log[ -]?in|"
    r"get started|try (?:it|for|free)|book (?:a )?demo|contact|frequently asked|"
    r"faq|testimonials?|careers?|customers?|trusted by|free trial)\b", re.I)
_FEATURE = re.compile(r"\b(?:features?|benefits?|capabilities|solutions?)\b", re.I)
_GENERIC_HEADINGS = {"features", "benefits", "product", "our product", "overview",
                     "learn more", "read more", "why us", "how it works", "solutions"}


def _clean(value: str, maximum: int = 800) -> str:
    return " ".join(value.split())[:maximum].strip()


def _normalize_url(value: str, base: str | None = None) -> str:
    """Remove query/fragment data; reject credentials and non-public URL forms."""
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise StudioError("Use a short, public HTTPS website address.")
    value = value.strip()
    if any(ord(c) < 33 or ord(c) == 127 for c in value) or "\\" in value:
        raise StudioError("The website address contains unsupported characters.")
    if base:
        value = urljoin(base, value)
    elif "://" not in value:
        value = "https://" + value
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() != "https" or parts.username is not None or parts.password is not None:
            raise ValueError
        host = (parts.hostname or "").rstrip(".").encode("idna").decode("ascii").lower()
        if parts.port not in (None, 443) or not host or len(host) > 253:
            raise ValueError
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ValueError
        labels = host.split(".")
        if len(labels) < 2 or not re.search(r"[a-z]", labels[-1]):
            raise ValueError
        if all(re.fullmatch(r"(?:0x[0-9a-f]+|[0-9]+)", label) for label in labels):
            raise ValueError
        if any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in labels):
            raise ValueError
        if labels[-1] in {"localhost", "local", "internal", "lan", "home", "onion"}:
            raise ValueError
        decoded = unquote(parts.path or "/")
        if any(ord(c) < 32 or ord(c) == 127 for c in decoded) or "\\" in decoded:
            raise ValueError
        if _PRIVATE_PATH.search(decoded):
            raise StudioError("Only public marketing pages are supported, not login or private application routes.")
        path = quote(parts.path or "/", safe="/%:@!$&'()*+,;=-._~")
        return urlunsplit(("https", host, path, "", ""))
    except (ValueError, UnicodeError):
        raise StudioError("Use a public HTTPS hostname without credentials or a custom port.") from None


def _origin(url: str) -> str:
    return "https://" + urlsplit(url).netloc


def _bounded_call(function, deadline: float, message: str):
    """Bound blocking DNS/HTTP work as well as per-socket waits; never join indefinitely."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise StudioError(message)
    outcome = queue.Queue(maxsize=1)

    def run():
        try:
            outcome.put((True, function()))
        except Exception as exc:
            outcome.put((False, exc))

    threading.Thread(target=run, daemon=True).start()
    try:
        success, value = outcome.get(timeout=remaining)
    except queue.Empty:
        raise StudioError(message) from None
    if not success:
        raise value
    return value


def _resolve_public(host: str, deadline: float | None = None) -> tuple[str, ...]:
    try:
        end = min(deadline or float("inf"), time.monotonic() + 5)
        answers = _bounded_call(lambda: socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM),
                                end, "Public hostname resolution reached its time limit.")
        addresses = tuple(dict.fromkeys(answer[4][0] for answer in answers))
        if not addresses:
            raise ValueError
        for address in addresses:
            ip = ipaddress.ip_address(address)
            if not ip.is_global or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
                raise ValueError
        return addresses
    except (OSError, ValueError):
        raise StudioError("The hostname did not resolve exclusively to public routable addresses.") from None


@dataclass(frozen=True)
class _Response:
    status: int
    headers: dict[str, str]
    body: bytes
    url: str = ""


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, address: str, timeout: float):
        super().__init__(host, port=443, timeout=timeout, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        # A numeric sockaddr goes straight to connect(), not through a second DNS lookup.
        family = socket.AF_INET6 if ":" in self.address else socket.AF_INET
        raw = socket.socket(family, socket.SOCK_STREAM)
        self.sock = raw
        raw.settimeout(self.timeout)
        try:
            target = (self.address, 443, 0, 0) if family == socket.AF_INET6 else (self.address, 443)
            raw.connect(target)
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close()
            raise


def _transport(url: str, addresses: tuple[str, ...], cap: int, deadline: float) -> _Response:
    """One TLS-verified request. Caller owns policy, robots, redirects, and budgets."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise StudioError("Website discovery reached its time limit.")
    parts = urlsplit(url)
    connection = _PinnedHTTPSConnection(parts.hostname, addresses[0], min(5.0, remaining))

    def abort():
        # Also interrupt slow response headers, which http.client reads before our body loop.
        sock = connection.sock
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        connection.close()

    watchdog = threading.Timer(remaining, abort)
    watchdog.daemon = True
    watchdog.start()
    try:
        connection.request("GET", parts.path or "/", headers={
            "Host": parts.netloc, "User-Agent": USER_AGENT, "Accept-Encoding": "identity",
            "Accept": "text/html,text/css,text/plain,image/*;q=0.8", "Connection": "close"})
        response = connection.getresponse()
        headers = {key.lower(): value for key, value in response.getheaders()}
        if headers.get("content-encoding", "identity").strip().lower() not in {"", "identity"}:
            raise StudioError("Compressed website responses are not imported.")
        length = headers.get("content-length")
        if length is not None and (not length.isdigit() or int(length) > cap):
            raise StudioError("The website resource exceeds its download size limit.")
        # Redirect/error bodies are not needed, and are never parsed as marketing content.
        if response.status != 200:
            return _Response(response.status, headers, b"", url)
        chunks = []
        size = 0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise StudioError("Website discovery reached its time limit.")
            sock = connection.sock
            if sock is not None:
                sock.settimeout(min(5.0, remaining))
            chunk = response.read1(min(65536, cap + 1 - size))
            if not chunk:
                break
            size += len(chunk)
            if size > cap:
                raise StudioError("The website resource exceeds its download size limit.")
            chunks.append(chunk)
        return _Response(response.status, headers, b"".join(chunks), url)
    except (OSError, http.client.HTTPException, ValueError):
        raise StudioError("The public website could not be fetched securely within the request timeout.") from None
    finally:
        watchdog.cancel()
        connection.close()


def _extra_robots_rules(text: str) -> tuple[list[str], bool]:
    """Conservatively honor wildcard denials/pacing not understood by robotparser.

    Allow rules never relax these extra denials. This can decline an allowed
    subpath, but cannot use an earlier broad Allow to ignore a later Disallow.
    """
    groups = []
    agents, rules = [], []
    for line in text.splitlines() + [""]:
        line = line.split("#", 1)[0].strip()
        if not line:
            if agents:
                groups.append((agents, rules))
            agents, rules = [], []
            continue
        key, colon, value = line.partition(":")
        if not colon:
            continue
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            if rules:
                groups.append((agents, rules))
                agents, rules = [], []
            agents.append(value.lower())
        elif agents:
            rules.append((key, value))
    selected, specificity = [], -1
    for agents, rules in groups:
        rank = max((0 if agent == "*" else len(agent) for agent in agents
                    if agent == "*" or (agent and agent in ROBOT_AGENT.lower())), default=-1)
        if rank > specificity:
            selected, specificity = [], rank
        if rank >= 0 and rank == specificity:
            selected.extend(rules)
    denied, paced = [], False
    for key, value in selected:
        if key == "disallow" and value:
            pattern = unquote(value)
            anchored = pattern.endswith("$")
            if anchored:
                pattern = pattern[:-1]
            # Only '*' is special in robots patterns; '?' and '[' are literal URL characters.
            pattern = pattern.replace("[", "[[]").replace("?", "[?]")
            denied.append(pattern if anchored else pattern + "*")
        elif key == "crawl-delay":
            try:
                paced = paced or float(value) > 0
            except ValueError:
                paced = True
    return denied, paced


class _Fetcher:
    def __init__(self):
        self.deadline = time.monotonic() + DEADLINE_SECONDS
        self.requests = 0
        self.total_bytes = 0
        self.robots: dict[str, RobotFileParser] = {}
        self.resources: dict[tuple[str, str], _Response] = {}

    def _request(self, url: str, kind: str) -> _Response:
        if self.requests >= MAX_REQUESTS or time.monotonic() >= self.deadline:
            raise StudioError("Website discovery reached its request or time limit.")
        addresses = _resolve_public(urlsplit(url).hostname, self.deadline)
        if time.monotonic() >= self.deadline:
            raise StudioError("Website discovery reached its time limit.")
        self.requests += 1
        response = _bounded_call(lambda: _transport(url, addresses, BYTE_CAPS[kind], self.deadline),
                                 self.deadline, "Website discovery reached its time limit.")
        headers = {key.lower(): value for key, value in response.headers.items()}
        self.total_bytes += len(response.body)
        if len(response.body) > BYTE_CAPS[kind] or self.total_bytes > MAX_TOTAL_BYTES:
            raise StudioError("Website discovery reached its response size limit.")
        if headers.get("content-encoding", "identity").lower().strip() not in {"", "identity"}:
            raise StudioError("Compressed website responses are not imported.")
        return _Response(response.status, headers, response.body, url)

    def _robot_policy(self, origin: str) -> RobotFileParser:
        if origin in self.robots:
            return self.robots[origin]
        url = origin + "/robots.txt"
        policy = RobotFileParser(url)
        # Cache a denial before fetching: every failure remains fail-closed for this origin.
        policy.parse(["User-agent: *", "Disallow: /"])
        self.robots[origin] = policy
        for attempt in range(MAX_REDIRECTS + 1):
            response = self._request(url, "robots")
            if response.status in {301, 302, 303, 307, 308}:
                url = self._redirect(response, url, origin, attempt)
                continue
            policy = RobotFileParser(url)
            if response.status in {404, 410}:
                policy.parse(["User-agent: *", "Allow: /"])
            elif response.status == 200:
                text = _decode_text(response, "robots")
                policy.parse(text.splitlines())
                policy.studio_denied, policy.studio_paced = _extra_robots_rules(text)
            else:
                raise StudioError("robots.txt was blocked or unavailable; this origin was not imported.")
            self.robots[origin] = policy
            return policy
        raise StudioError("robots.txt exceeded the redirect limit.")

    def _redirect(self, response: _Response, current: str, origin: str, attempt: int) -> str:
        if attempt >= MAX_REDIRECTS or not response.headers.get("location"):
            raise StudioError("The website exceeded its redirect limit or sent an invalid redirect.")
        target = _normalize_url(response.headers["location"], current)
        # Validate before even considering a redirect, including rejected origin changes.
        _resolve_public(urlsplit(target).hostname, self.deadline)
        if _origin(target) != origin:
            raise StudioError("Cross-origin redirects are not followed; use the site's final public HTTPS address.")
        return target

    def fetch(self, url: str, kind: str, page_origin: str | None = None) -> _Response:
        url = _normalize_url(url)
        origin = _origin(url)
        if page_origin and origin != page_origin:
            raise StudioError("Additional marketing pages must stay on the approved website origin.")
        if (url, kind) in self.resources:
            return self.resources[(url, kind)]
        for attempt in range(MAX_REDIRECTS + 1):
            # Validate even robots-denied URLs; no cached DNS result is trusted for transport.
            _resolve_public(urlsplit(url).hostname, self.deadline)
            policy = self._robot_policy(origin)
            path = unquote(urlsplit(url).path)
            denied = any(fnmatch.fnmatchcase(path, pattern) for pattern in getattr(policy, "studio_denied", []))
            if denied or not policy.can_fetch(ROBOT_AGENT, url):
                raise StudioError("robots.txt disallows this resource; it was not imported.")
            delay = policy.crawl_delay(ROBOT_AGENT)
            rate = policy.request_rate(ROBOT_AGENT)
            # This short importer does not schedule crawls; abstain rather than exceed advertised pacing.
            if getattr(policy, "studio_paced", False) or (delay and delay > 0) or (rate and rate.requests > 0 and rate.seconds > 0):
                raise StudioError("robots.txt requests paced crawling; automatic discovery abstained.")
            response = self._request(url, kind)
            if response.status in {301, 302, 303, 307, 308}:
                url = self._redirect(response, url, origin, attempt)
                continue
            if response.status != 200:
                raise StudioError(f"The public resource returned HTTP {response.status}; blocked pages are not bypassed.")
            mime = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if mime not in _TYPES[kind]:
                if mime == "image/svg+xml":
                    raise StudioError("SVG artwork is not rendered by this importer; use a public raster logo or icon.")
                raise StudioError(f"The public resource did not provide a supported {kind} content type.")
            self.resources[(response.url, kind)] = response
            return response
        raise StudioError("The website exceeded its redirect limit.")


def _decode_text(response: _Response, kind: str) -> str:
    mime = response.headers.get("content-type", "").split(";", 1)[0].lower().strip()
    if mime not in _TYPES[kind]:
        raise StudioError(f"The public resource did not provide a supported {kind} content type.")
    match = re.search(r"charset\s*=\s*[\"']?([\w-]+)", response.headers.get("content-type", ""), re.I)
    encoding = match.group(1).lower() if match else "utf-8"
    aliases = {"utf8": "utf-8", "utf-8": "utf-8-sig", "us-ascii": "ascii", "ascii": "ascii",
               "iso-8859-1": "iso-8859-1", "windows-1252": "cp1252"}
    if encoding not in aliases:
        raise StudioError("The page declares an unsupported text encoding.")
    try:
        return response.body.decode(aliases[encoding], errors="strict")
    except UnicodeError:
        raise StudioError("The page's text encoding could not be decoded reliably.") from None


class _Page(HTMLParser):
    """Extract small, inert metadata and visible snippets; never load HTML in a browser."""
    def __init__(self, url: str):
        super().__init__(convert_charrefs=True)
        self.url = url
        self.meta: dict[str, str] = {}
        self.title = ""
        self.snippets: list[tuple[str, str, str]] = []
        self.links: list[tuple[str, str]] = []
        self.images: list[dict] = []
        self.stylesheets: list[str] = []
        self.styles: list[str] = []
        self.structured: list[dict] = []
        self.stack: list[tuple[str, str]] = []
        self.captures: list[dict] = []
        self.special: tuple[str, str] | None = None
        self.special_text = ""
        self.nodes = 0

    def handle_starttag(self, tag, attrs):
        self.nodes += 1
        if self.nodes > 15000:
            raise StudioError("The marketing page exceeds the HTML complexity limit.")
        attrs = dict(attrs)
        if self.special:
            return
        if tag in {"script", "style"}:
            self.special = (tag, attrs.get("type", ""))
            self.special_text = ""
            return
        context = " ".join(item[1] for item in self.stack[-8:])
        own = " ".join(str(attrs.get(k) or "") for k in ("id", "class", "role"))[:300]
        if tag in {"nav", "footer", "header"}:
            own += " " + tag
        hidden = "hidden" in attrs or attrs.get("aria-hidden") == "true" or tag in {"template", "noscript"}
        if hidden:
            own += " discovery-hidden"
        context += " " + own
        if tag == "meta" and len(self.meta) < 80:
            key = (attrs.get("property") or attrs.get("name") or "").lower()
            if key and attrs.get("content"):
                self.meta.setdefault(key, _clean(attrs["content"], 2000))
        if tag == "link":
            rel = (attrs.get("rel") or "").lower().split()
            href = attrs.get("href")
            if href and "stylesheet" in rel and len(self.stylesheets) < MAX_CANDIDATES:
                self.stylesheets.append(href)
            if href and any("icon" in token for token in rel) and len(self.images) < MAX_CANDIDATES:
                self.images.append({"url": href, "hint": "site icon", "kind": "logo", "score": 40,
                                    "method": "public site icon (logo fallback)"})
        if tag == "img" and len(self.images) < MAX_CANDIDATES and "discovery-hidden" not in context:
            src = attrs.get("src") or attrs.get("data-src")
            if src:
                hint = _clean(" ".join(str(attrs.get(k) or "") for k in ("alt", "class", "id")) + " " + src)
                if re.search(r"logo|brandmark|wordmark", hint, re.I):
                    kind, score = "logo", 90
                elif "header" in context and attrs.get("alt") and _clean(attrs["alt"]).casefold() in {
                        name.casefold() for name in [self.meta.get("og:site_name", ""),
                        re.split(r"\s[|—–]\s|\s-\s", self.title, maxsplit=1)[0]] if name}:
                    kind, score = "logo", 65
                elif re.search(r"screenshot|dashboard|product[-_ ]?(?:ui|image|preview)|app[-_ ]?(?:ui|preview)|workspace", hint, re.I):
                    kind, score = "screenshot", 80
                else:
                    kind, score = "", 0
                if kind:
                    self.images.append({"url": src, "hint": hint, "kind": kind, "score": score,
                                        "method": "public logo image" if kind == "logo" else "public marketing image (page img; not verified app UI)"})
        if tag in {"title", "h1", "h2", "h3", "p", "a", "button"} and len(self.captures) < 12:
            self.captures.append({"tag": tag, "context": context, "href": attrs.get("href"), "text": ""})
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            if len(self.stack) >= 80:
                raise StudioError("The marketing page exceeds the HTML nesting limit.")
            self.stack.append((tag, own))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        if self.special:
            self.special_text = (self.special_text + data)[:65536]
            return
        if any("discovery-hidden" in item[1] for item in self.stack):
            return
        for capture in self.captures:
            capture["text"] = (capture["text"] + data)[:1200]

    def handle_endtag(self, tag):
        if self.special:
            if tag != self.special[0]:
                return
            if tag == "style" and len(self.styles) < 2:
                self.styles.append(self.special_text[:32768])
            elif self.special[1].lower() == "application/ld+json":
                try:
                    self._structured(json.loads(self.special_text))
                except (ValueError, RecursionError):
                    pass
            self.special = None
            self.special_text = ""
            return
        matching = [i for i, c in enumerate(self.captures) if c["tag"] == tag]
        if matching:
            capture = self.captures.pop(matching[-1])
            text = _clean(capture["text"])
            if text and "discovery-hidden" not in capture["context"]:
                if tag == "title" and not self.title:
                    self.title = text
                elif tag == "a" and capture["href"] and len(self.links) < MAX_CANDIDATES:
                    self.links.append((capture["href"], text))
                if tag in {"h1", "h2", "h3", "p", "a", "button"} and len(self.snippets) < 160:
                    self.snippets.append((tag, text, capture["context"]))
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def _structured(self, value, depth=0):
        if depth > 5 or len(self.structured) >= 24:
            return
        if isinstance(value, list):
            for item in value[:24]:
                self._structured(item, depth + 1)
        elif isinstance(value, dict):
            types = value.get("@type", [])
            types = [types] if isinstance(types, str) else types
            if isinstance(types, list) and any(t in {"Organization", "Product", "SoftwareApplication"} for t in types if isinstance(t, str)):
                self.structured.append(value)
            self._structured(value.get("@graph"), depth + 1)


def _parse_page(response: _Response) -> _Page:
    page = _Page(response.url)
    page.feed(_decode_text(response, "html"))
    page.close()
    labels = [page.title] + [text for tag, text, _ in page.snippets if tag == "h1"]
    if any(re.search(r"\b(?:access denied|just a moment|attention required|checking your browser|"
                     r"verify (?:that )?you are (?:a )?human|sign[ -]?in|log[ -]?in)\b", label, re.I)
           for label in labels):
        raise StudioError("The public page is a blocking or login screen; it was not imported.")
    return page


def _color(value: str) -> str | None:
    value = value.strip().lower()
    if re.fullmatch(r"#[0-9a-f]{3}", value):
        return "#" + "".join(c * 2 for c in value[1:])
    if re.fullmatch(r"#[0-9a-f]{6}", value):
        return value
    match = re.fullmatch(r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", value)
    if match and all(int(v) <= 255 for v in match.groups()):
        return "#" + "".join(f"{int(v):02x}" for v in match.groups())
    return None


def _css_brand(css: str) -> tuple[list[str], list[str]]:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    colors, fonts = [], []
    for match in re.finditer(r"(?:--[\w-]*(?:accent|primary|brand)[\w-]*|accent-color)\s*:\s*([^;}]+)", css, re.I):
        color = _color(match.group(1).strip())
        if color and color not in colors:
            colors.append(color)
        if len(colors) >= 6:
            break
    generic = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "inherit", "initial", "unset",
               "ui-serif", "ui-sans-serif", "ui-monospace", "emoji", "math", "fangsong", "-apple-system"}
    for match in re.finditer(r"(?:font-family|--font[\w-]*)\s*:\s*([^;}]+)", css, re.I):
        for family in match.group(1).split(",")[:8]:
            family = family.strip().strip("\"'")
            if family.lower() not in generic and re.fullmatch(r"[\w -]{1,60}", family) and family not in fonts:
                fonts.append(family)
            if len(fonts) >= 8:
                return colors, fonts
    return colors, fonts


def _save_raster(body: bytes, destination: Path, kind: str) -> str:
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError:
        raise StudioError("Pillow is required to import public image assets.") from None
    try:
        with python_warnings.catch_warnings():
            python_warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(body), formats=("PNG", "JPEG", "WEBP", "GIF", "BMP", "ICO")) as image:
                if image.format not in {"PNG", "JPEG", "WEBP", "GIF", "BMP", "ICO"}:
                    raise StudioError("The public image uses an unsupported raster format.")
                width, height = image.size
                if not width or not height or width * height > MAX_PIXELS or max(width, height) > 8192:
                    raise StudioError("The public image exceeds the pixel limit.")
                image.seek(0)
                image.load()
                normalized = ImageOps.exif_transpose(image).convert("RGBA")
                # New pixel-only image ensures EXIF, ICC, comments, and PNG text are not retained.
                clean = Image.new("RGBA", normalized.size)
                clean.paste(normalized)
                destination.mkdir(parents=True, exist_ok=True)
                path = (destination / f"discovered_{kind}.png").resolve()
                clean.save(path, format="PNG")
                return str(path)
    except StudioError:
        raise
    except (OSError, ValueError, SyntaxError, OverflowError, UnidentifiedImageError,
            Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise StudioError("The public image could not be safely decoded and normalized.") from None


def discover_site(url: str, destination: Path,
                  progress: Callable[[float, str], None] | None = None, *, capture_visuals: bool = False,
                  record_tour: bool = False) -> dict:
    """Return a partial, evidence-backed brand draft and at most two local PNGs.

    Unknown fields stay absent. Marketing copy is attributed, not independently
    verified. ``assets.screenshot`` is only a public marketing image, never a
    browser screenshot or a claim of authenticated application access.
    """
    destination = Path(destination)
    start = _normalize_url(url)
    fetcher = _Fetcher()
    result = {"url": start, "brief": {}, "assets": {}, "brand": {"colors": [], "fonts": []},
              "sources": [], "evidence": [],
              "warnings": ["Imported marketing claims require review; they are not independently verified."],
              "missing": [], "discovered_at": ""}
    brief, brand = result["brief"], result["brand"]

    def notify(fraction, message):
        if progress:
            progress(fraction, message)

    def warn(message):
        if message not in result["warnings"]:
            result["warnings"].append(message)

    def source(address, title):
        if not any(item["url"] == address for item in result["sources"]):
            result["sources"].append({"url": address, "title": _clean(title, 160)})

    def evidence(field, value, address, method, confidence="medium"):
        result["evidence"].append({"field": field, "value": value, "source": address,
                                   "method": method, "confidence": confidence})

    def field(key, value, address, method, confidence="medium", maximum=800):
        if key not in brief and isinstance(value, str) and _clean(value):
            brief[key] = _clean(value, maximum)
            evidence(key, brief[key], address, method, confidence)

    def css_brand(css, address):
        colors, fonts = _css_brand(css)
        for key, values in (("colors", colors), ("fonts", fonts)):
            for value in values:
                if value not in brand[key] and len(brand[key]) < 8:
                    brand[key].append(value)
                    evidence(key, value, address, "CSS declaration (font names only; no font files downloaded)")
        if colors:
            current = brief.get("color", "")
            channels = [int(current[i:i + 2], 16) for i in (1, 3, 5)] if current else []
            # Stylesheets often list --bg-primary before their actual accent.
            accent = next((value for value in colors
                           if max(int(value[i:i + 2], 16) for i in (1, 3, 5))
                           - min(int(value[i:i + 2], 16) for i in (1, 3, 5)) >= 15), colors[0])
            if channels and max(channels) - min(channels) < 15:
                # A neutral browser theme color is normally the background, not the brand accent.
                brief["color"] = accent
                evidence("color", accent, address, "CSS accent replaces neutral theme background")
            else:
                field("color", accent, address, "CSS accent/primary/brand declaration", maximum=7)

    notify(0.05, "Reading public website metadata and robots policy")
    try:
        homepage = fetcher.fetch(start, "html", _origin(start))
        home = _parse_page(homepage)
    except StudioError as exc:
        raise StudioError(f"The homepage could not be imported: {exc}") from None
    origin = _origin(homepage.url)
    result["url"] = homepage.url
    field("url", homepage.url, homepage.url, "final validated public HTTPS response", "high", maximum=2048)
    pages = [home]
    visited = {start, home.url}
    page_attempts = 1
    for href, label in home.links:
        if page_attempts >= MAX_PAGES:
            break
        if not _FEATURE.search(label + " " + href):
            continue
        try:
            address = _normalize_url(href, home.url)
            if address in visited or _origin(address) != origin:
                continue
            visited.add(address)
            page_attempts += 1
            response = fetcher.fetch(address, "html", origin)
            if response.url in {page.url for page in pages}:
                continue
            pages.append(_parse_page(response))
        except StudioError as exc:
            warn(f"An optional feature page was not imported: {exc}")
    notify(0.35, "Extracting attributed marketing copy and brand hints")
    images, stylesheets = [], []
    benefits = []
    for page in pages:
        source(page.url, page.title or "Public marketing page")
        meta = page.meta
        field("name", meta.get("og:site_name"), page.url, "og:site_name", "high", maximum=40)
        field("description", meta.get("description") or meta.get("og:description"), page.url, "meta description", "high")
        for item in page.structured:
            field("name", item.get("name"), page.url, "JSON-LD organization/product name", "high", maximum=40)
            field("description", item.get("description"), page.url, "JSON-LD description", "high")
            audience = item.get("audience")
            if isinstance(audience, dict):
                audience = audience.get("audienceType") or audience.get("name")
            field("audience", audience, page.url, "explicit JSON-LD audience", "high", maximum=100)
            logo = item.get("logo")
            if isinstance(logo, dict):
                logo = logo.get("contentUrl") or logo.get("url")
            if isinstance(logo, str):
                images.append({"url": logo, "kind": "logo", "score": 100,
                               "method": "JSON-LD public logo", "page": page.url})
        if page is home:
            title_name = re.split(r"\s[|—–]\s|\s-\s", page.title, maxsplit=1)[0]
            field("name", title_name, page.url, "HTML title (review product name)", maximum=40)
        field("audience", meta.get("audience"), page.url, "explicit audience metadata", maximum=100)
        theme = _color(meta.get("theme-color", ""))
        if theme:
            field("color", theme, page.url, "theme-color metadata", "high", maximum=7)
            if theme not in brand["colors"] and len(brand["colors"]) < 8:
                brand["colors"].append(theme)
                evidence("colors", theme, page.url, "theme-color metadata", "high")
        for tag, text, context in page.snippets:
            if tag in {"a", "button"} and re.fullmatch(r"(?:apply now|get started|start (?:your |a )?(?:free )?trial|try (?:it |for )?free|book (?:a )?demo|request (?:a )?demo|learn more|explore (?:the )?product)[.!]?", text, re.I):
                field("cta", text, page.url, "public call-to-action text", "high", maximum=40)
            if tag not in {"h1", "h2", "h3", "p"} or _EXCLUDE.search(context):
                continue
            match = re.match(r"(?:built|designed|made) (?:specifically )?for\s+(.+?)[.!]?$", text, re.I)
            if match and len(match.group(1)) <= 100:
                field("audience", match.group(1), page.url, "explicit 'built/designed for' text", maximum=100)
            match = re.match(r"(?:the |your |customer )?problem\s*:\s*(.+)", text, re.I)
            if match:
                field("problem", match.group(1), page.url, "explicit problem statement", maximum=180)
            feature_context = _FEATURE.search(context) or _FEATURE.search(urlsplit(page.url).path)
            if tag in {"h2", "h3"} and feature_context and 12 <= len(text) <= 120 and not _EXCLUDE.search(text) and text.lower().rstrip(".!:") not in _GENERIC_HEADINGS and text not in benefits and len(benefits) < 6:
                benefits.append(text)
                evidence("benefits", text, page.url, "public feature/benefit heading; unverified marketing claim")
        for css in page.styles:
            css_brand(css, page.url)
        images.extend({**image, "page": page.url} for image in page.images)
        og_image = meta.get("og:image") or meta.get("twitter:image")
        if og_image:
            images.append({"url": og_image, "kind": "screenshot", "score": 10,
                           "method": "public marketing image (social-card metadata; not verified app UI)", "page": page.url})
        stylesheets.extend((href, page.url) for href in page.stylesheets)
    if benefits:
        brief["benefits"] = benefits
    seen_css = set()
    # Prioritize first-party branding over third-party fonts within the small request budget.
    stylesheets.sort(key=lambda item: urlsplit(urljoin(item[1], item[0])).netloc != urlsplit(home.url).netloc)
    for href, base in stylesheets[:MAX_CANDIDATES]:
        if len(seen_css) >= MAX_CSS:
            break
        try:
            address = _normalize_url(href, base)
            if address in seen_css:
                continue
            seen_css.add(address)
            response = fetcher.fetch(address, "css")
            css_brand(_decode_text(response, "css"), response.url)
            source(response.url, "Public stylesheet (font names only)")
        except StudioError as exc:
            warn(f"An optional public stylesheet was not imported: {exc}")
    notify(0.65, "Normalizing public logo and marketing images")
    seen_images = set()
    image_attempts = 0
    candidates = sorted(images, key=lambda item: item["score"], reverse=True)[:MAX_CANDIDATES]
    for kind in ("logo", "screenshot"):
        for candidate in candidates:
            if candidate["kind"] != kind or image_attempts >= MAX_IMAGES:
                continue
            try:
                address = _normalize_url(candidate["url"], candidate["page"])
                if kind == "screenshot" and candidate["score"] <= 10 and Path(urlsplit(address).path).stem.lower() in {"logo", "icon", "favicon", "apple-touch-icon"}:
                    warn("The social-card image is a logo/icon, not a product visual; add a product screenshot during review.")
                    continue
                if urlsplit(address).path.lower().endswith(".svg"):
                    warn("SVG artwork is not rendered; a public raster logo/icon is preferred, otherwise add a logo during review.")
                    continue
                if address in seen_images:
                    continue
                seen_images.add(address)
                image_attempts += 1
                response = fetcher.fetch(address, "image")
                path = _save_raster(response.body, destination, kind)
                result["assets"][kind] = path
                source(response.url, "Public logo/icon" if kind == "logo" else "Public marketing image (not a verified app UI capture)")
                evidence(kind, path, response.url, candidate["method"], "medium" if kind == "logo" else "low")
                if kind == "screenshot":
                    warn("The imported screenshot is a public marketing image, not a verified app UI capture or a logged-in dashboard screenshot.")
                elif "fallback" in candidate["method"]:
                    warn("The site's icon was used as a logo fallback; review it before use.")
                break
            except StudioError as exc:
                warn(f"An optional public {kind} image was not imported: {exc}")
    if capture_visuals or record_tour:
        notify(.8, "Capturing actual public-page visuals for the four scenes")
        try:
            from .capture import capture_public_visuals
            captures = capture_public_visuals(homepage.url, destination / "captures", fetcher=fetcher,
                                              homepage=homepage, record_tour=record_tour,
                                              progress=lambda fraction, message: notify(.8 + .18 * fraction, message))
            result["captures"] = captures
            for index, capture in enumerate(captures["captures"], 1):
                key = f"scene_{index}"
                result["assets"][key] = capture["path"]
                evidence(key, capture["path"], capture["source"], "static public-page viewport capture", "high")
            if captures.get("tour"):
                result["assets"]["demo"] = captures["tour"]["path"]
                evidence("demo", captures["tour"]["path"], captures["tour"]["source"], "recorded public-page scrolling; no authenticated task", "high")
            for message in captures["warnings"]:
                warn(message)
        except (StudioError, ImportError) as exc:
            warn(f"Product-page visuals could not be captured: {exc} Upload a product image or real screen recording.")
    for key in ("name", "description", "audience", "problem", "benefits", "cta", "color"):
        if not brief.get(key):
            result["missing"].append(key)
    for key in ("logo", "screenshot"):
        if key not in result["assets"] and not (key == "screenshot" and result["assets"].get("scene_1")):
            result["missing"].append(key)
    if not result["assets"].get("logo"):
        warn("No usable public raster logo was found; add or confirm a logo during review.")
    if brand["fonts"]:
        warn("Font family names were identified only; font files were not downloaded and licensing was not assessed.")
    result["discovered_at"] = datetime.now(timezone.utc).isoformat()
    notify(1.0, "Public website draft ready for review")
    return result
