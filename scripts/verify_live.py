#!/usr/bin/env python3
"""
Post-deploy smoke tests against a live base URL (custom domain or Railway URL).

Usage (from repo root):
  python scripts/verify_live.py https://your-domain.com
  set LIVE_URL=https://your-domain.com && python scripts/verify_live.py

Optional authenticated checks (skipped if unset). Use a test user without MFA,
or the login step will report MFA required and skip the token checks:
  set TEST_EMAIL=you@example.com
  set TEST_PASSWORD=secret

Exit codes: 0 = all critical checks passed, 1 = failure, 2 = bad usage.
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urljoin, urlparse


def _req(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = 20.0,
) -> tuple[int, str]:
    h = dict(headers or {})
    data: bytes | None = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:  # noqa: S310 — user-supplied deploy URL
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, raw
    except Exception as e:
        return -1, str(e)


def _fail(msg: str) -> None:
    print(f"  FAIL: {msg}")


def _ok(msg: str) -> None:
    print(f"  OK:   {msg}")


def _warn(msg: str) -> None:
    print(f"  WARN: {msg}")


def _http_redirect_to_https(https_base: str) -> tuple[str, str]:
    """Try HTTP GET / on same host; expect redirect toward HTTPS or connection refused."""
    p = urlparse(https_base)
    if p.scheme.lower() != "https":
        return "skip", "base URL is not https"
    host = p.netloc
    if not host:
        return "fail", "no host in URL"
    conn = http.client.HTTPConnection(host, timeout=12)
    try:
        conn.request("GET", "/", headers={"User-Agent": "pro-alert-verify-live/1.0"})
        r = conn.getresponse()
        body = r.read(512)
        _ = body
        loc = (r.getheader("Location") or "").strip()
        if r.status in (301, 302, 303, 307, 308):
            if loc.lower().startswith("https:"):
                return "ok", f"HTTP / -> {r.status} to HTTPS"
            return "warn", f"HTTP / -> {r.status} Location={loc!r} (confirm it sends users to HTTPS)"
        if r.status == 200:
            return "warn", "HTTP / returned 200 (prefer redirect to HTTPS at edge)"
        return "warn", f"HTTP / returned {r.status}"
    except OSError as e:
        return "warn", f"HTTP not reachable on port 80 ({e}); many hosts only listen on 443"
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify live deployment (health, ready, auth sanity).")
    ap.add_argument(
        "base_url",
        nargs="?",
        default=os.environ.get("LIVE_URL", "").strip(),
        help="https://your-domain.com (or set LIVE_URL)",
    )
    args = ap.parse_args()
    raw = (args.base_url or "").strip().rstrip("/")
    if not raw:
        print("Usage: python scripts/verify_live.py https://your-domain.com", file=sys.stderr)
        print("   or: set LIVE_URL and run with no arguments.", file=sys.stderr)
        return 2
    if not raw.startswith("http://") and not raw.startswith("https://"):
        raw = "https://" + raw
    base = raw.rstrip("/")

    print(f"LIVE verify: {base}\n")

    critical_fail = False

    # 1) Health
    print("[1] GET /api/health")
    code, text = _req(urljoin(base + "/", "api/health"))
    if code != 200:
        critical_fail = True
        _fail(f"status {code}: {text[:200]}")
    else:
        try:
            j = json.loads(text) if text.strip() else {}
            _ok(f"status {j.get('status', 'ok')!r}")
        except json.JSONDecodeError:
            _ok(f"HTTP 200 (non-JSON body: {text[:80]!r}…)")

    # 2) Ready
    print("\n[2] GET /api/ready")
    code, text = _req(urljoin(base + "/", "api/ready"))
    if code != 200:
        critical_fail = True
        _fail(f"status {code}: {text[:200]}")
    else:
        try:
            j = json.loads(text) if text.strip() else {}
            _ok(f"database: {j.get('database', j)!r}")
        except json.JSONDecodeError:
            _ok("HTTP 200")

    # 3) /api/auth/me without credentials
    print("\n[3] GET /api/auth/me (no auth — expect 401)")
    code, text = _req(urljoin(base + "/", "api/auth/me"))
    if code == 200:
        critical_fail = True
        _fail("returned 200 without a token (should not be public)")
    elif code in (401, 403):
        _ok(f"status {code} (not anonymously accessible)")
    else:
        critical_fail = True
        _fail(f"status {code}: {text[:200]}")

    # 4) Static pages
    print("\n[4] GET / and /login")
    for path in ("/", "/login"):
        code, text = _req(urljoin(base, path))
        if code != 200:
            critical_fail = True
            _fail(f"{path} -> {code}")
        else:
            _ok(f"{path} -> 200 ({len(text)} bytes)")

    # 5) HTTP -> HTTPS hint
    print("\n[5] HTTP port 80 behaviour (optional)")
    level, msg = _http_redirect_to_https(base)
    if level == "ok":
        _ok(msg)
    elif level == "warn":
        _warn(msg)
    else:
        _warn(msg)

    # 6) Authenticated chain
    email = (os.environ.get("TEST_EMAIL") or "").strip()
    password = os.environ.get("TEST_PASSWORD") or ""
    print("\n[6] Authenticated API smoke (optional)")
    if not email or not password:
        _warn("Skipped — set TEST_EMAIL and TEST_PASSWORD to run POST /api/auth/login + /me + /devices + /alerts")
    else:
        code, text = _req(urljoin(base + "/", "api/auth/login"), method="POST", body={"email": email, "password": password})
        if code != 200:
            try:
                detail = json.loads(text).get("detail")
            except json.JSONDecodeError:
                detail = text[:300]
            if isinstance(detail, dict) and detail.get("mfa_required"):
                _warn("Login requires MFA — complete checks in the browser; token smoke skipped.")
            else:
                critical_fail = True
                _fail(f"login status {code}: {detail}")
        else:
            try:
                token = json.loads(text).get("token")
            except json.JSONDecodeError:
                token = None
            if not token:
                critical_fail = True
                _fail("login 200 but no token in JSON")
            else:
                h = {"Authorization": f"Bearer {token}"}
                for label, path in (
                    ("me", "/api/auth/me"),
                    ("devices", "/api/devices/?page=1&limit=5"),
                    ("alerts", "/api/alerts/?page=1&limit=5"),
                ):
                    c2, _ = _req(urljoin(base, path), headers=h)
                    if c2 != 200:
                        critical_fail = True
                        _fail(f"GET {path} -> {c2}")
                    else:
                        _ok(f"GET {path} -> 200")

    print()
    if critical_fail:
        print("[RESULT] FAILED — fix production env or routing before demo.")
        return 1
    print("[RESULT] PASSED — critical live checks OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
