"""Fake Bifrost gateway: answers the OpenAI-compatible model list with one model, for the provider-wiring test."""

import json
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from typing import Any

MODEL_ID = "fake-bifrost-model"


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, body: Any) -> None:
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/health":
            self._json(200, {"status": "ok"})
        elif path.startswith("/service/") and path.endswith("/models"):
            self._json(200, {"object": "list", "data": [{"id": MODEL_ID, "object": "model", "owned_by": "fake"}]})
        else:
            self._json(404, {"error": f"not found: {path}"})


HTTPServer(("0.0.0.0", 5000), Handler).serve_forever()
