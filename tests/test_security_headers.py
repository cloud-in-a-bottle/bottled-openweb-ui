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
    # Navigate first so Open WebUI has finished initializing and the auto-admin
    # (WEBUI_AUTH=False) exists before probing the admin-gated endpoint.
    page.goto(stack.url + "/", wait_until="networkidle")
    page.wait_for_selector("#chat-input", timeout=30_000)

    resp = page.request.get(
        stack.url + "/api/config",
        headers={"Origin": "https://evil.example"},
    )
    # Guard against passing trivially on a non-200 (e.g. Caddy not up, a 401):
    # the assertion below is only meaningful on a real CORS-bearing response.
    assert resp.status == 200, f"unexpected status {resp.status}"

    # With the insecure default (CORS_ALLOW_ORIGIN='*'), a hostile origin would
    # come back allowed: Open WebUI runs with credentials enabled, so Starlette
    # reflects the request origin (and would send '*' if credentials were off).
    # The packaging restricts CORS to the app's own origin, so Starlette omits
    # Access-Control-Allow-Origin entirely for a disallowed origin. A hostile
    # origin must therefore yield no header; if the restriction regressed to the
    # default, this origin would be reflected (or '*') and the assertion fails.
    #
    # There is no positive control (app-origin -> ACAO reflected): the app's own
    # origin isn't reliably known inside the harness, and it isn't needed here.
    # A same-origin frontend never triggers CORS, and dropping the restriction
    # reverts to the permissive default, which this negative check catches.
    acao = resp.headers.get("access-control-allow-origin")
    assert acao is None, f"arbitrary origin was allowed (ACAO={acao!r})"
