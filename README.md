# bottled-openweb-ui

[Open WebUI](https://github.com/open-webui/open-webui) packaged for deployment on Cloud in a Bottle. A startup wrapper (`openhost_start.sh`) adapts it to Cloud in a Bottle's data, auth, and domain conventions.

## Deploying

In your Cloud in a Bottle router dashboard, choose **Add App**, use this repository URL, and confirm. The app is served privately at `https://{app_name}.{zone_domain}` — no public paths are configured, so every request is gated to the compute-space owner.

## Authentication

Because Cloud in a Bottle already authenticates the owner, Open WebUI runs in single-user mode (`WEBUI_AUTH=False`): the owner lands directly on the main page as the admin user, with no Open WebUI login.

To use Open WebUI's own multi-user auth instead, set `WEBUI_AUTH=True` in the app's environment.

## Model provider: Bifrost gateway

This app consumes the [Bifrost LLM gateway](https://github.com/imbue-openhost/bottled-bifrost)'s
`openai-compat` service and wires it up as an Open WebUI model provider
automatically — no manual connection setup.

- Installing the app requests the gateway's `full_access` grant (declared as a
  `services.v2.consumes` block in `openhost.toml`). Approve it at install time,
  and make sure the gateway app is installed with at least one provider
  configured in its web UI.
- A local `mitmproxy` (`openhost_bifrost_proxy.py`, started by
  `openhost_start.sh`) exposes the gateway as a plain OpenAI endpoint on
  `127.0.0.1:9000`: it rewrites each request onto the Cloud in a Bottle service-call path
  and attaches the app token, so Open WebUI never holds a credential. Responses
  are streamed for incremental chat output.
- On first boot, Open WebUI is seeded (`OPENAI_API_BASE_URL`) to use that
  endpoint. These are Open WebUI PersistentConfig values, so after first boot the
  owner manages the connection in the UI. The models offered are whatever the
  gateway owner configured (e.g. `openai/gpt-4o`).

## Upgrading Open WebUI

The image is pinned to a release tag in the `Dockerfile`. To upgrade, bump the tag.

## Data

- **Backed up** (`OPENHOST_APP_DATA_DIR`): database, settings, uploads, vector data, secret key.
- **Not backed up** (`OPENHOST_APP_TEMP_DIR`): the model cache (embedding/whisper/tiktoken), which is large and regenerable.

Inject model API keys as environment variables via your Cloud in a Bottle app settings.

## Tests

End-to-end tests drive the real container behind a mock Cloud in a Bottle router using the [openhost-app-test-harness](https://github.com/imbue-openhost/openhost-app-test-harness) and Playwright. Requires podman.

```bash
uv sync
uv run playwright install chromium
uv run pytest
```
