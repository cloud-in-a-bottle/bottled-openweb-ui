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


def test_cors_is_not_wildcard(stack: OpenhostStack, page: Page) -> None:
    # An arbitrary Origin must not be reflected back and must never be "*"
    # (Open WebUI's default), so third-party sites can't make credentialed
    # cross-origin reads.
    resp = page.request.get(
        stack.url + "/api/config",
        headers={"Origin": "https://evil.example"},
    )
    acao = resp.headers.get("access-control-allow-origin")
    assert acao != "*", resp.headers
    assert acao != "https://evil.example", resp.headers
