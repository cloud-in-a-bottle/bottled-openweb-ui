"""The Bifrost gateway should be wired up as an Open WebUI model provider
automatically, with no manual connection setup.

On first boot openhost_start.sh seeds Open WebUI's OpenAI connection to point at
the local mitmproxy (127.0.0.1:9000), which fronts the gateway's service
interface. Here we assert Open WebUI actually holds that connection.

The test harness doesn't deploy the Bifrost gateway, so a true end-to-end "list
models from Bifrost" check needs a live instance with both apps installed; this
verifies the configuration side.
"""

from openhost_test_harness import OpenhostStack
from playwright.sync_api import Page

PROXY_BASE_URL = "http://127.0.0.1:9000/openai/v1"


def test_openai_connection_points_at_bifrost_proxy(stack: OpenhostStack, page: Page) -> None:
    # Land on the app first so the owner holds an admin session (the config
    # endpoint is admin-gated).
    page.goto(stack.url + "/", wait_until="networkidle")
    page.wait_for_selector("#chat-input", timeout=30_000)

    resp = page.request.get(stack.url + "/openai/config")
    assert resp.status == 200, f"could not read OpenAI config (status {resp.status})"

    config = resp.json()
    assert config.get("ENABLE_OPENAI_API") is True, f"OpenAI API not enabled: {config!r}"
    base_urls = config.get("OPENAI_API_BASE_URLS", [])
    assert PROXY_BASE_URL in base_urls, f"bifrost proxy not configured as a provider: {base_urls!r}"
