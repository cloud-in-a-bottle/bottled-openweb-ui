"""mitmproxy addon: front the Bifrost gateway's OpenAI-compatible service.

Open WebUI talks plain OpenAI to http://127.0.0.1:9000; this addon rewrites each
request onto the OpenHost service-call path and attaches the app token, so the
unmodified OpenAI client reaches Bifrost through the router without ever holding
a credential. Responses are streamed so SSE chat completions arrive
incrementally instead of being buffered whole.

Run via openhost_start.sh; reads OPENHOST_APP_TOKEN and BIFROST_SHORTNAME.
"""

import os

from mitmproxy import http

_TOKEN = os.environ["OPENHOST_APP_TOKEN"]
_PREFIX = "/api/services/v2/call/" + os.environ.get("BIFROST_SHORTNAME", "llm")


def request(flow: http.HTTPFlow) -> None:
    flow.request.path = _PREFIX + flow.request.path
    flow.request.headers["Authorization"] = f"Bearer {_TOKEN}"


def responseheaders(flow: http.HTTPFlow) -> None:
    flow.response.stream = True
