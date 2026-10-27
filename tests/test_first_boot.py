"""First-boot behavior: the OpenHost owner should land directly on Open WebUI's
main page, with Open WebUI's own user setup / login bypassed.

The ``page`` fixture is logged in to the router as the zone owner, so the
router injects ``X-OpenHost-Is-Owner: true`` on every request. Pointing it at
``stack.url`` reproduces what the owner sees on a brand-new deployment.
"""

from openhost_test_harness import OpenhostStack
from playwright.sync_api import Page

# page.request doesn't send fetch metadata, and the router only accepts owner cookie auth
# on same-origin requests, so declare it as the app's own frontend would.
SAME_ORIGIN = {"Sec-Fetch-Site": "same-origin"}


def test_first_boot_lands_on_main_page(stack: OpenhostStack, page: Page) -> None:
    page.goto(stack.url + "/", wait_until="load")

    # Open WebUI is a SPA that, with auth enabled and no session, redirects to
    # its /auth onboarding wall (which has a password field). With auth bypassed
    # it renders the chat UI (#chat-input). Wait for whichever it settles on.
    page.wait_for_selector("input[type='password'], #chat-input", timeout=30_000)

    path = page.evaluate("() => window.location.pathname")
    page.screenshot(path="tests/_first_boot.png", full_page=True)

    # Not parked on the sign-in / sign-up wall...
    assert "/auth" not in path, f"landed on auth wall, url path={path!r}"
    assert page.locator("input[type='password']").count() == 0, (
        "found a password field — login/signup wall is showing"
    )

    # ...and the chat UI is actually present.
    assert page.locator("#chat-input").first.is_visible(), "chat input not visible — not on the main page"


def test_owner_is_authenticated_without_signup(stack: OpenhostStack, page: Page) -> None:
    """The owner should already hold an Open WebUI session (as admin) on first
    boot, without ever creating an account."""
    page.goto(stack.url + "/", wait_until="load")
    page.wait_for_selector("#chat-input", timeout=30_000)

    resp = page.request.get(stack.url + "/api/v1/auths/", headers=SAME_ORIGIN)
    assert resp.status == 200, f"owner is not authenticated to Open WebUI (status {resp.status})"
    assert resp.json().get("role") == "admin", f"owner is not an admin: {resp.json()!r}"
