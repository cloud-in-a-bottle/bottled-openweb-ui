"""The Bifrost gateway should be wired up as an Open WebUI model provider
automatically, with no manual connection setup.

On first boot openhost_start.sh seeds Open WebUI's OpenAI connection to point at
the local mitmproxy (127.0.0.1:9000), which fronts the gateway's service
interface. Here we assert Open WebUI actually holds that connection, and that
models from the gateway show up in Open WebUI: conftest installs a fake Bifrost
(tests/fake_bifrost) providing the same service, so the model list goes Open
WebUI -> mitmproxy (adds the app token, rewrites onto the service-call path) ->
router -> provider.
"""

import time

from openhost_test_harness import OpenhostStack
from playwright.sync_api import Page

# page.request doesn't send fetch metadata, and the router only accepts owner cookie auth
# on same-origin requests, so declare it as the app's own frontend would.
SAME_ORIGIN = {"Sec-Fetch-Site": "same-origin"}

PROXY_BASE_URL = "http://127.0.0.1:9000/openai/v1"
FAKE_BIFROST_MODEL = "fake-bifrost-model"  # served by tests/fake_bifrost/server.py


def test_openai_connection_points_at_bifrost_proxy(stack: OpenhostStack, page: Page) -> None:
    # Land on the app first so the owner holds an admin session (the config
    # endpoint is admin-gated).
    page.goto(stack.url + "/", wait_until="networkidle")
    page.wait_for_selector("#chat-input", timeout=30_000)

    resp = page.request.get(stack.url + "/openai/config", headers=SAME_ORIGIN)
    assert resp.status == 200, f"could not read OpenAI config (status {resp.status})"

    config = resp.json()
    assert config.get("ENABLE_OPENAI_API") is True, f"OpenAI API not enabled: {config!r}"
    base_urls = config.get("OPENAI_API_BASE_URLS", [])
    assert PROXY_BASE_URL in base_urls, f"bifrost proxy not configured as a provider: {base_urls!r}"


def test_bifrost_models_show_up_in_open_webui(stack: OpenhostStack, page: Page) -> None:
    page.goto(stack.url + "/", wait_until="networkidle")
    page.wait_for_selector("#chat-input", timeout=30_000)

    deadline = time.monotonic() + 60
    while True:
        resp = page.request.get(stack.url + "/api/models?refresh=true", headers=SAME_ORIGIN)
        model_ids = [m.get("id") for m in resp.json().get("data", [])] if resp.status == 200 else []
        if FAKE_BIFROST_MODEL in model_ids or time.monotonic() > deadline:
            break
        time.sleep(3)
    assert FAKE_BIFROST_MODEL in model_ids, (
        f"gateway model not offered by Open WebUI (status {resp.status}, models {model_ids!r})"
        f"\n\napp logs:\n{stack.app_logs()[-5000:]}"
    )
