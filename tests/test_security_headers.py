"""The Caddy sidecar should add hardening headers to every response, and CORS
should be restricted to the app's own origin rather than Open WebUI's default
``*``.

Open WebUI itself sets none of these headers, which left the owner UI framable
(clickjacking). ``openhost_start.sh`` runs a local Caddy in front of Open WebUI
to add them, and sets ``CORS_ALLOW_ORIGIN`` to the app origin. These tests guard
against Caddy failing to start or the config regressing.
"""

from openhost_test_harness import OpenhostStack
from playwright.sync_api import Page


def test_security_headers_present(stack: OpenhostStack, page: Page) -> None:
    resp = page.request.get(stack.url + "/")
    assert resp.status == 200, f"unexpected status {resp.status}"
    headers = resp.headers

    assert headers.get("x-frame-options") == "DENY", headers
    assert "frame-ancestors 'none'" in (headers.get("content-security-policy") or ""), headers
    assert headers.get("x-content-type-options") == "nosniff", headers
    assert headers.get("referrer-policy") == "no-referrer", headers


def test_cors_does_not_allow_arbitrary_origin(stack: OpenhostStack, page: Page) -> None:
    # Land on the app first so the owner holds a session (matches the other
    # tests), then probe an admin-gated endpoint with a hostile Origin.
    page.goto(stack.url + "/", wait_until="networkidle")
    page.wait_for_selector("#chat-input", timeout=30_000)

    resp = page.request.get(
        stack.url + "/api/config",
        headers={"Origin": "https://evil.example"},
    )
    # Guard against passing trivially on a non-200 (e.g. Caddy not up, a 401):
    # the assertion below is only meaningful on a real CORS-bearing response.
    assert resp.status == 200, f"unexpected status {resp.status}"

    # Open WebUI's insecure default (CORS_ALLOW_ORIGIN='*') echoes the request
    # origin back with credentials; the packaging restricts CORS to the app's
    # own origin. Starlette omits Access-Control-Allow-Origin entirely for a
    # disallowed origin, so a hostile origin must yield no header at all. If the
    # insecure default regressed, this origin would be reflected (or '*') and
    # the assertion would fail.
    acao = resp.headers.get("access-control-allow-origin")
    assert acao is None, f"arbitrary origin was allowed (ACAO={acao!r})"
