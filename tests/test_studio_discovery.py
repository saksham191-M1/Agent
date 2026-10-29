"""Offline public-marketing discovery fixtures. No test contacts a live website."""
from __future__ import annotations

import io
import socket
import ssl
import sys
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio import discovery as d
from studio.models import StudioError

SITE = "https://acme.example"
PUBLIC_IP = "93.184.216.34"
HOME = """<!doctype html><html><head>
<title>Acme | Project clarity</title>
<meta property="og:site_name" content="Acme">
<meta name="description" content="Keep project decisions and tasks together.">
<meta name="theme-color" content="#639">
<meta property="og:image" content="/social.png">
<link rel="stylesheet" href="/brand.css">
<link rel="icon" href="/icon.png">
<script type="application/ld+json">{"@type":"Organization","name":"Acme",
"logo":"/logo.png"}</script>
<script>document.title = 'NOT EXECUTED';</script>
</head><body><header><img src="/logo.png" alt="Acme logo">
<nav><a href="/features">Features</a><a href="/login">Sign in</a></nav></header>
<main><h1>Built for independent design teams</h1>
<section class="features"><h2>Keep decisions in one place</h2>
<h2>Pricing for every team</h2><h3>Get started</h3>
<p>The problem: Important decisions get lost in scattered messages.</p></section>
<a href="/start">Get started</a>
<img src="/product-dashboard.png" alt="Product dashboard preview"></main>
<footer><h2>Privacy and terms</h2></footer></body></html>"""
FEATURES = """<html><head><title>Acme features</title></head><body>
<nav><h2>Choose a pricing plan</h2></nav><main><h2>Share a clear project timeline</h2>
<h2>Book a demo</h2><h2>Features</h2><h2>Our customers</h2></main></body></html>"""
CSS = ":root { --brand-primary: #654abc; --accent: rgb(12, 120, 180); } body { font-family: 'Inter', 'Acme Sans', sans-serif; }"


def response(body="", kind="html", status=200, headers=None):
    if isinstance(body, str):
        body = body.encode("utf-8")
    types = {"html": "text/html; charset=utf-8", "css": "text/css; charset=utf-8",
             "robots": "text/plain; charset=utf-8", "image": "image/png"}
    return d._Response(status, {"content-type": types[kind], **(headers or {})}, body)


def png():
    from PIL import Image, PngImagePlugin
    buffer = io.BytesIO()
    image = Image.new("RGB", (32, 20), (51, 102, 153))
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("comment", "Fixture metadata must be stripped")
    image.save(buffer, format="PNG", pnginfo=metadata)
    return buffer.getvalue()


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.destination = Path(self.temp.name) / "assets"
        self.routes = {SITE + "/robots.txt": response("User-agent: *\nAllow: /", "robots")}
        self.calls = []
        self.resolver = patch.object(d, "_resolve_public", return_value=(PUBLIC_IP,)).start()
        self.addCleanup(patch.stopall)
        self.transport = patch.object(d, "_transport", side_effect=self.fake_transport).start()

    def fake_transport(self, url, addresses, cap, deadline):
        self.assertEqual(addresses, (PUBLIC_IP,))
        self.assertGreater(deadline, time.monotonic())
        self.calls.append(url)
        if url not in self.routes:
            raise AssertionError("Unexpected offline fixture request: " + url)
        return self.routes[url]

    def discover(self, url=SITE + "/", progress=None):
        return d.discover_site(url, self.destination, progress)

    def test_extracts_attributed_brand_and_normalized_assets(self):
        from PIL import Image
        image = png()
        self.routes.update({SITE + "/": response(HOME), SITE + "/features": response(FEATURES),
                            SITE + "/brand.css": response(CSS, "css"),
                            SITE + "/logo.png": response(image, "image"),
                            SITE + "/product-dashboard.png": response(image, "image")})
        events = []
        result = self.discover(progress=lambda fraction, message: events.append((fraction, message)))
        brief = result["brief"]
        self.assertEqual(brief["name"], "Acme")
        self.assertEqual(brief["description"], "Keep project decisions and tasks together.")
        self.assertEqual(brief["audience"], "independent design teams")
        self.assertEqual(brief["problem"], "Important decisions get lost in scattered messages.")
        self.assertEqual(brief["benefits"], ["Keep decisions in one place", "Share a clear project timeline"])
        self.assertEqual(brief["cta"], "Get started")
        self.assertEqual(brief["color"], "#663399")
        self.assertEqual(result["brand"]["colors"], ["#663399", "#654abc", "#0c78b4"])
        self.assertEqual(result["brand"]["fonts"], ["Inter", "Acme Sans"])
        self.assertFalse(result["missing"])
        self.assertEqual(set(result["assets"]), {"logo", "screenshot"})
        for path in result["assets"].values():
            self.assertTrue(Path(path).is_absolute())
            self.assertEqual(Path(path).suffix, ".png")
            with Image.open(path) as normalized:
                self.assertEqual(normalized.format, "PNG")
                self.assertEqual(normalized.mode, "RGBA")
                self.assertNotIn("comment", normalized.info)
                self.assertNotIn("exif", normalized.info)
        self.assertNotIn(SITE + "/social.png", self.calls)
        self.assertNotIn(SITE + "/login", self.calls)
        self.assertEqual(self.calls.count(SITE + "/robots.txt"), 1)
        self.assertTrue(any("public marketing image" in w and "not a verified" in w for w in result["warnings"]))
        evidence = result["evidence"]
        self.assertTrue(any(e["field"] == "screenshot" and "public marketing image" in e["method"] for e in evidence))
        self.assertTrue(all(e["confidence"] in {"high", "medium", "low"} for e in evidence))
        self.assertTrue(all(e["source"] in {s["url"] for s in result["sources"]} for e in evidence))
        self.assertEqual(events[-1][0], 1.0)
        self.assertEqual([e[0] for e in events], sorted(e[0] for e in events))
        self.assertIsNotNone(datetime.fromisoformat(result["discovered_at"]).utcoffset())

    def test_missing_data_stays_missing(self):
        self.routes[SITE + "/"] = response("<html><body><p>A simple public page.</p></body></html>")
        result = self.discover()
        self.assertEqual(result["brief"], {"url": SITE + "/"})
        self.assertEqual(result["assets"], {})
        self.assertEqual(result["brand"], {"colors": [], "fonts": []})
        self.assertTrue({"name", "audience", "problem", "benefits", "color", "logo"}.issubset(result["missing"]))
        self.assertFalse(self.destination.exists())

    def test_jsonld_fields_and_no_inferred_audience_or_features(self):
        self.routes[SITE + "/"] = response('''<script type="application/ld+json">
        {"@graph":[{"@type":"Product","name":"Acme","description":"A calm workspace.",
        "audience":{"@type":"Audience","audienceType":"Editors"}}]}</script>
        <h1>The best platform in the world</h1><p>Thousands of people love Acme.</p>''')
        result = self.discover()
        self.assertEqual(result["brief"]["name"], "Acme")
        self.assertEqual(result["brief"]["audience"], "Editors")
        self.assertEqual(result["brief"]["description"], "A calm workspace.")
        self.assertNotIn("benefits", result["brief"])
        self.assertNotIn("problem", result["brief"])

    def test_scripts_hidden_content_and_unrelated_header_photos_are_not_imported(self):
        self.routes[SITE + "/"] = response('''<title>Acme</title><header>
        <img src="/portrait.png" alt="A person in a park"></header>
        <script>Built for imaginary customers</script>
        <section class="features"><h2 hidden>Invent an impressive claim</h2>
        <template><h2>Another invisible claim</h2></template>
        <h2>Keep <span hidden>secret</span>work together</h2></section>''')
        result = self.discover()
        self.assertNotIn("audience", result["brief"])
        self.assertEqual(result["brief"]["benefits"], ["Keep work together"])
        self.assertNotIn("logo", result["assets"])
        self.assertNotIn(SITE + "/portrait.png", self.calls)

    def test_robots_denied_homepage_is_not_fetched(self):
        self.routes[SITE + "/robots.txt"] = response("User-agent: *\nDisallow: /", "robots")
        with self.assertRaisesRegex(StudioError, "homepage.*robots.txt disallows"):
            self.discover()
        self.assertEqual(self.calls, [SITE + "/robots.txt"])

    def test_robots_specific_agent_and_optional_page_denial(self):
        self.routes[SITE + "/robots.txt"] = response(
            "User-agent: JarvisStudioDiscovery\nDisallow: /features\n\nUser-agent: *\nAllow: /", "robots")
        self.routes[SITE + "/"] = response('<title>Acme</title><a href="/features">Features</a>')
        result = self.discover()
        self.assertEqual(result["brief"]["name"], "Acme")
        self.assertNotIn(SITE + "/features", self.calls)
        self.assertTrue(any("robots.txt disallows" in w for w in result["warnings"]))

    def test_missing_robots_is_allowed_but_blocked_robots_fails_closed(self):
        self.routes[SITE + "/robots.txt"] = response(status=404, kind="robots")
        self.routes[SITE + "/"] = response("<title>Acme</title>")
        self.assertEqual(self.discover()["brief"]["name"], "Acme")
        self.routes[SITE + "/robots.txt"] = response(status=403, kind="robots")
        self.calls.clear()
        with self.assertRaisesRegex(StudioError, "robots.txt was blocked"):
            self.discover()
        self.assertNotIn(SITE + "/", self.calls)

    def test_robots_pacing_abstains_instead_of_exceeding_it(self):
        self.routes[SITE + "/robots.txt"] = response("User-agent: *\nCrawl-delay: 10\nAllow: /", "robots")
        with self.assertRaisesRegex(StudioError, "paced crawling"):
            self.discover()
        self.assertEqual(self.calls, [SITE + "/robots.txt"])

    def test_robots_wildcard_denials_and_fractional_pacing_are_conservative(self):
        self.routes[SITE + "/robots.txt"] = response(
            "User-agent: *\nAllow: /\nDisallow: /features/*", "robots")
        self.routes[SITE + "/"] = response('<title>Acme</title><a href="/features/team">Features</a>')
        result = self.discover()
        self.assertNotIn(SITE + "/features/team", self.calls)
        self.assertTrue(any("robots.txt disallows" in w for w in result["warnings"]))
        self.routes[SITE + "/robots.txt"] = response("User-agent: *\nCrawl-delay: 0.5\nAllow: /", "robots")
        self.calls.clear()
        with self.assertRaisesRegex(StudioError, "paced crawling"):
            self.discover()
        self.assertEqual(self.calls, [SITE + "/robots.txt"])

    def test_same_origin_redirect_revalidated_and_final_url_used(self):
        self.routes[SITE + "/"] = response(status=302, headers={"location": "/welcome?campaign=public#top"})
        self.routes[SITE + "/welcome"] = response("<title>Acme</title>")
        result = self.discover()
        self.assertEqual(result["url"], SITE + "/welcome")
        self.assertEqual(result["brief"]["url"], SITE + "/welcome")
        self.assertGreaterEqual(self.resolver.call_count, 6)
        self.assertIn(SITE + "/welcome", self.calls)

    def test_cross_origin_redirect_validated_then_rejected(self):
        self.routes[SITE + "/"] = response(status=301, headers={"location": "https://other.example/"})
        with self.assertRaisesRegex(StudioError, "Cross-origin redirects"):
            self.discover()
        self.assertTrue(any(call.args[0] == "other.example" for call in self.resolver.call_args_list))
        self.assertNotIn("https://other.example/", self.calls)

    def test_redirect_limit(self):
        self.routes[SITE + "/"] = response(status=302, headers={"location": "/"})
        with self.assertRaisesRegex(StudioError, "redirect limit"):
            self.discover()
        self.assertEqual(self.calls.count(SITE + "/"), d.MAX_REDIRECTS + 1)

    def test_dns_is_revalidated_before_each_request(self):
        self.resolver.side_effect = [(PUBLIC_IP,), (PUBLIC_IP,), StudioError("Address is not public")]
        with self.assertRaisesRegex(StudioError, "not public"):
            self.discover()
        self.assertEqual(self.calls, [SITE + "/robots.txt"])

    def test_explicit_cdn_assets_use_their_own_robots_policy(self):
        self.routes[SITE + "/"] = response('''<title>Acme</title>
        <img src="https://media.example/logo.png" alt="Acme logo">
        <a href="https://other.example/features">Features</a>''')
        self.routes["https://media.example/robots.txt"] = response("User-agent: *\nDisallow: /", "robots")
        result = self.discover()
        self.assertIn("https://media.example/robots.txt", self.calls)
        self.assertNotIn("https://media.example/logo.png", self.calls)
        self.assertNotIn("https://other.example/robots.txt", self.calls)
        self.assertNotIn("logo", result["assets"])

    def test_explicit_public_cdn_css_and_logo_are_supported(self):
        self.routes[SITE + "/"] = response('''<title>Acme</title>
        <link rel="stylesheet" href="https://media.example/brand.css">
        <img src="https://media.example/logo.png" alt="Acme logo">''')
        self.routes["https://media.example/robots.txt"] = response("User-agent: *\nAllow: /", "robots")
        self.routes["https://media.example/brand.css"] = response(CSS, "css")
        self.routes["https://media.example/logo.png"] = response(png(), "image")
        result = self.discover()
        self.assertIn("logo", result["assets"])
        self.assertEqual(result["brand"]["fonts"], ["Inter", "Acme Sans"])
        self.assertEqual(self.calls.count("https://media.example/robots.txt"), 1)

    def test_asset_redirect_cannot_silently_change_approved_origin(self):
        self.routes[SITE + "/"] = response('<title>Acme</title><img src="/logo.png" alt="Acme logo">')
        self.routes[SITE + "/logo.png"] = response(status=302, kind="image",
                                                   headers={"location": "https://media.example/logo.png"})
        result = self.discover()
        self.assertNotIn("logo", result["assets"])
        self.assertTrue(any(call.args[0] == "media.example" for call in self.resolver.call_args_list))
        self.assertNotIn("https://media.example/logo.png", self.calls)
        self.assertTrue(any("Cross-origin redirects" in w for w in result["warnings"]))

    def test_private_asset_destination_is_rejected_without_request(self):
        self.routes[SITE + "/"] = response('<title>Acme</title><img alt="Acme logo" src="https://intranet.example/logo.png">')
        def resolve(host, deadline=None):
            if host == "intranet.example":
                raise StudioError("The hostname did not resolve exclusively to public routable addresses.")
            return (PUBLIC_IP,)
        self.resolver.side_effect = resolve
        result = self.discover()
        self.assertEqual(result["assets"], {})
        self.assertFalse(any("intranet" in url for url in self.calls))
        self.assertTrue(any("public routable" in w for w in result["warnings"]))

    def test_svg_uses_raster_icon_fallback_without_rendering(self):
        self.routes[SITE + "/"] = response('''<title>Acme</title>
        <img src="/logo.svg" alt="Acme logo"><link rel="icon" href="/icon.png">''')
        self.routes[SITE + "/icon.png"] = response(png(), "image")
        result = self.discover()
        self.assertIn("logo", result["assets"])
        self.assertNotIn(SITE + "/logo.svg", self.calls)
        self.assertTrue(any("SVG artwork is not rendered" in w for w in result["warnings"]))
        self.assertTrue(any("icon was used" in w for w in result["warnings"]))

    def test_social_image_fallback_is_labelled_not_verified_ui(self):
        self.routes[SITE + "/"] = response('<title>Acme</title><meta property="og:image" content="/social.png">')
        self.routes[SITE + "/social.png"] = response(png(), "image")
        result = self.discover()
        self.assertIn("screenshot", result["assets"])
        item = next(e for e in result["evidence"] if e["field"] == "screenshot")
        self.assertIn("social-card", item["method"])
        self.assertIn("not verified app UI", item["method"])
        self.assertEqual(item["confidence"], "low")

    def test_brand_accent_and_product_visual_are_not_background_and_logo(self):
        self.routes[SITE + "/"] = response('''<title>Acme</title>
        <meta name="theme-color" content="#0c0b0b"><meta property="og:image" content="/logo.png">
        <link rel="stylesheet" href="https://fonts.example/font.css">
        <link rel="stylesheet" href="https://library.example/style.css">
        <link rel="stylesheet" href="/brand.css"><a href="/apply">Apply Now</a>''')
        self.routes[SITE + "/brand.css"] = response(
            ":root{--bg-primary:#0c0b0b;--accent-brand:#c99a4e;--font-display:'Outfit',sans-serif}", "css")
        self.routes["https://fonts.example/robots.txt"] = response("User-agent: *\nDisallow: /", "robots")
        result = self.discover()
        self.assertEqual(result["brief"]["color"], "#c99a4e")
        self.assertEqual(result["brief"]["cta"], "Apply Now")
        self.assertIn("Outfit", result["brand"]["fonts"])
        self.assertNotIn("screenshot", result["assets"])
        self.assertNotIn(SITE + "/logo.png", self.calls)
        self.assertTrue(any("logo/icon" in w for w in result["warnings"]))

    def test_html_css_and_image_counts_are_bounded(self):
        home = "<title>Acme</title>" + "".join(f'<a href="/features/{i}">Features {i}</a>' for i in range(12))
        home += "".join(f'<link rel="stylesheet" href="/style{i}.css">' for i in range(12))
        home += "".join(f'<img src="/logo{i}.png" alt="Acme logo">' for i in range(12))
        self.routes[SITE + "/"] = response(home)
        for i in range(12):
            self.routes[SITE + f"/features/{i}"] = response(f"<title>Feature {i}</title>")
            self.routes[SITE + f"/style{i}.css"] = response(CSS, "css")
            self.routes[SITE + f"/logo{i}.png"] = response(b"not a decodable image", "image")
        result = self.discover()
        self.assertEqual(sum("/features/" in url for url in self.calls), 2)
        self.assertEqual(sum(url.endswith(".css") for url in self.calls), 2)
        self.assertEqual(sum(url.endswith(".png") for url in self.calls), 2)
        self.assertLessEqual(len(self.calls), d.MAX_REQUESTS)
        self.assertEqual(result["assets"], {})

    def test_byte_cap_and_invalid_content_type_fail_homepage_clearly(self):
        self.routes[SITE + "/"] = response(b"x" * (d.BYTE_CAPS["html"] + 1))
        with self.assertRaisesRegex(StudioError, "homepage.*size limit"):
            self.discover()
        self.routes[SITE + "/"] = response("{}", headers={"content-type": "application/json"})
        with self.assertRaisesRegex(StudioError, "homepage.*content type"):
            self.discover()

    def test_blocking_or_login_screens_are_not_marketing_content(self):
        for title in ("Access denied", "Just a moment", "Sign in to Acme"):
            with self.subTest(title=title):
                self.routes[SITE + "/"] = response(f"<title>{title}</title>")
                with self.assertRaisesRegex(StudioError, "homepage.*blocking or login"):
                    self.discover()
        self.routes[SITE + "/"] = response(status=403)
        with self.assertRaisesRegex(StudioError, "HTTP 403.*not bypassed"):
            self.discover()

    def test_encoding_and_compression_are_checked(self):
        self.routes[SITE + "/"] = response(b"\xff\xfe", headers={"content-type": "text/html; charset=utf-16"})
        with self.assertRaisesRegex(StudioError, "unsupported text encoding"):
            self.discover()
        self.routes[SITE + "/"] = response("<title>Acme</title>", headers={"content-encoding": "gzip"})
        with self.assertRaisesRegex(StudioError, "Compressed"):
            self.discover()

    def test_optional_failures_preserve_homepage_draft(self):
        self.routes[SITE + "/"] = response('''<title>Acme</title><a href="/features">Features</a>
        <link rel="stylesheet" href="/bad.css"><img src="/logo.png" alt="Acme logo">''')
        self.routes[SITE + "/features"] = response(status=503)
        self.routes[SITE + "/bad.css"] = response(status=403, kind="css")
        self.routes[SITE + "/logo.png"] = response(b"unavailable image", "image")
        result = self.discover()
        self.assertEqual(result["brief"]["name"], "Acme")
        self.assertTrue(any("feature page" in w for w in result["warnings"]))
        self.assertTrue(any("stylesheet" in w for w in result["warnings"]))
        self.assertTrue(any("logo image" in w for w in result["warnings"]))

    def test_total_request_byte_and_deadline_budgets(self):
        fetcher = d._Fetcher()
        fetcher.requests = d.MAX_REQUESTS
        with self.assertRaisesRegex(StudioError, "request or time limit"):
            fetcher.fetch(SITE + "/", "html")
        fetcher = d._Fetcher()
        fetcher.deadline = time.monotonic() - 1
        with self.assertRaisesRegex(StudioError, "time limit"):
            fetcher.fetch(SITE + "/", "html")
        fetcher = d._Fetcher()
        fetcher.total_bytes = d.MAX_TOTAL_BYTES
        with self.assertRaisesRegex(StudioError, "response size limit"):
            fetcher.fetch(SITE + "/", "html")
        self.assertEqual(self.calls, [SITE + "/robots.txt"])

    def test_input_query_and_fragment_are_not_sent(self):
        self.routes[SITE + "/"] = response("<title>Acme</title>")
        result = self.discover("https://ACME.example./?campaign=news#top")
        self.assertEqual(result["url"], SITE + "/")
        self.assertTrue(all("?" not in url and "#" not in url for url in self.calls))


class NetworkAndImageBoundaryTests(unittest.TestCase):
    def test_normalization_accepts_hostname_but_rejects_non_public_url_forms(self):
        self.assertEqual(d._normalize_url("ACME.example"), SITE + "/")
        invalid = ["http://acme.example/", "https://127.0.0.1/", "https://93.184.216.34/", "https://[::1]/", "https://localhost/",
                   "https://acme.local/", "https://name:password@acme.example/", "https://acme.example:8443/",
                   "https://acme.example/login", "https://acme.example/dashboard", "https://acme.example/admin"]
        for value in invalid:
            with self.subTest(url=value), self.assertRaises(StudioError):
                d._normalize_url(value)

    def test_resolver_rejects_private_and_mixed_destinations(self):
        def answer(ip):
            return (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (ip, 443))
        with patch.object(socket, "getaddrinfo", return_value=[answer(PUBLIC_IP)]):
            self.assertEqual(d._resolve_public("acme.example"), (PUBLIC_IP,))
        for ips in [["10.0.0.8"], ["127.0.0.1"], [PUBLIC_IP, "192.168.1.8"], ["169.254.1.1"], ["224.0.0.1"]]:
            with self.subTest(ips=ips), patch.object(socket, "getaddrinfo", return_value=[answer(ip) for ip in ips]):
                with self.assertRaisesRegex(StudioError, "public routable"):
                    d._resolve_public("acme.example")

    def test_pinned_tls_socket_uses_numeric_address_and_original_sni(self):
        connection = d._PinnedHTTPSConnection("acme.example", PUBLIC_IP, 2)
        self.assertEqual(connection._context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(connection._context.check_hostname)
        context = MagicMock()
        with patch.object(connection, "_context", context), patch.object(socket, "socket") as factory, \
                patch.object(socket, "getaddrinfo") as resolver:
            connection.connect()
            factory.return_value.connect.assert_called_once_with((PUBLIC_IP, 443))
            context.wrap_socket.assert_called_once_with(factory.return_value, server_hostname="acme.example")
            resolver.assert_not_called()

    def test_transport_sends_no_credentials_and_never_automatically_redirects(self):
        fake = MagicMock()
        fake.status = 302
        fake.getheaders.return_value = [("Location", "/welcome"), ("Content-Type", "text/html")]
        with patch.object(d, "_PinnedHTTPSConnection") as factory:
            factory.return_value.getresponse.return_value = fake
            result = d._transport(SITE + "/", (PUBLIC_IP,), 1000, time.monotonic() + 5)
            self.assertEqual(result.status, 302)
            fake.read1.assert_not_called()
            request = factory.return_value.request.call_args
            self.assertEqual(request.args, ("GET", "/"))
            headers = request.kwargs["headers"]
            self.assertEqual(headers["Host"], "acme.example")
            self.assertEqual(headers["Accept-Encoding"], "identity")
            self.assertEqual(headers["User-Agent"], d.USER_AGENT)
            self.assertNotIn("Cookie", headers)
            self.assertNotIn("Authorization", headers)
            self.assertNotIn("Referer", headers)
            factory.return_value.close.assert_called()

    def test_transport_byte_cap_is_enforced_while_reading(self):
        fake = MagicMock()
        fake.status = 200
        fake.getheaders.return_value = [("Content-Type", "text/html")]
        fake.read1.return_value = b"sixsix"
        with patch.object(d, "_PinnedHTTPSConnection") as factory:
            factory.return_value.getresponse.return_value = fake
            with self.assertRaisesRegex(StudioError, "size limit"):
                d._transport(SITE + "/", (PUBLIC_IP,), 5, time.monotonic() + 5)
            factory.return_value.close.assert_called()

    def test_image_pixel_limit_and_metadata_removal(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(d, "MAX_PIXELS", 10):
                with self.assertRaisesRegex(StudioError, "pixel limit"):
                    d._save_raster(png(), Path(tmp), "logo")
            self.assertEqual(list(Path(tmp).iterdir()), [])
            saved = d._save_raster(png(), Path(tmp), "logo")
            with Image.open(saved) as image:
                self.assertEqual(image.size, (32, 20))
                self.assertEqual(image.info, {})

    def test_bounded_worker_times_out_without_waiting_indefinitely(self):
        import threading
        finished = threading.Event()
        def wait_briefly():
            finished.wait(0.1)
        try:
            with self.assertRaisesRegex(StudioError, "bounded test"):
                d._bounded_call(wait_briefly, time.monotonic() + 0.01, "bounded test")
        finally:
            finished.set()


if __name__ == "__main__":
    unittest.main()
