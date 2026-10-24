"""Shared pytest fixtures.

Deploys the real Open WebUI container through the Cloud in a Bottle router, and
provides a Playwright page logged in as the zone owner (so the router sends
``X-OpenHost-Is-Owner: true`` to the app, as it does for the real owner).
"""

from collections.abc import Iterator

import pytest
from openhost_test_harness import OpenhostStack
from playwright.sync_api import Browser, Page, sync_playwright


@pytest.fixture(scope="session")
def stack() -> Iterator[OpenhostStack]:
    # The deploy window covers the image build (a ~4 GB base image to pull) and
    # Open WebUI's first boot, which runs DB migrations and downloads embedding
    # models from HuggingFace before it binds.
    with OpenhostStack(deploy_timeout=600) as s:
        yield s


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as p:
        b = p.chromium.launch()
        try:
            yield b
        finally:
            b.close()


@pytest.fixture
def page(stack: OpenhostStack, browser: Browser) -> Iterator[Page]:
    context = browser.new_context()
    pg = context.new_page()
    try:
        stack.playwright_login(pg)
        yield pg
    finally:
        context.close()
