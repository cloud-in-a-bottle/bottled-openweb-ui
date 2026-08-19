#!/usr/bin/env bash
set -euo pipefail

# Adapts Open WebUI to OpenHost conventions, then hands off to the image's
# start.sh. Expects the standard OpenHost environment to be present.

: "${OPENHOST_APP_DATA_DIR:?}"
: "${OPENHOST_APP_TEMP_DIR:?}"
: "${OPENHOST_APP_NAME:?}"
: "${OPENHOST_ZONE_DOMAIN:?}"
: "${OPENHOST_ROUTER_URL:?}"
: "${OPENHOST_APP_TOKEN:?}"

# Persistent, backed-up app state.
export DATA_DIR="$OPENHOST_APP_DATA_DIR"
mkdir -p "$DATA_DIR"

# Model cache: large and regenerable, so keep it in the non-backed-up temp dir.
# Open WebUI hardcodes CACHE_DIR to "$DATA_DIR/cache", so redirect that path to
# the temp dir via a symlink. The temp dir persists across reloads.
CACHE_DIR="$OPENHOST_APP_TEMP_DIR/cache"
mkdir -p "$CACHE_DIR"
# Best-effort seed from the models bundled in the image: fills anything missing
# (first boot, or a wiped cache) without clobbering on-demand downloads or
# failing the boot.
cp -an /app/backend/data/cache/. "$CACHE_DIR/" 2>/dev/null || true
rm -rf "$DATA_DIR/cache"
ln -s "$CACHE_DIR" "$DATA_DIR/cache"

# Persist the session-signing key so logins survive restarts.
export WEBUI_SECRET_KEY_FILE="$DATA_DIR/.webui_secret_key"

# Bypass Open WebUI's own auth; the OpenHost router already gates to the owner.
export WEBUI_AUTH="False"

# Public URL for the app's OpenHost zone.
export WEBUI_URL="https://$OPENHOST_APP_NAME.$OPENHOST_ZONE_DOMAIN"

# Restrict CORS to this app's own origin instead of Open WebUI's default "*".
# The frontend is same-origin so this doesn't affect it; it just stops
# arbitrary third-party sites from making credentialed cross-origin calls.
export CORS_ALLOW_ORIGIN="$WEBUI_URL"

# Front the Bifrost gateway's OpenAI-compatible service as a local endpoint.
# mitmdump reverse-proxies to the router and the addon rewrites each request
# onto the service-call path and attaches the app token (see
# openhost_bifrost_proxy.py). Restart it if it ever exits.
export BIFROST_SHORTNAME="llm"
(
  while true; do
    rc=0
    mitmdump \
      --mode "reverse:$OPENHOST_ROUTER_URL" \
      --listen-host 127.0.0.1 --listen-port 9000 \
      -s /app/openhost_bifrost_proxy.py || rc=$?
    echo "[openhost] mitmdump exited (rc=$rc), restarting in 2s" >&2
    sleep 2
  done
) &

# Auto-configure that endpoint as an Open WebUI model provider. These are
# PersistentConfig values: seeded into the DB on first boot, after which the
# owner can manage the connection in the UI. The placeholder key is overwritten
# by the proxy, which injects the real app token.
export ENABLE_OPENAI_API="True"
export OPENAI_API_BASE_URL="http://127.0.0.1:9000/openai/v1"
export OPENAI_API_KEY="openhost-bifrost"

# Turn off the auto-generated "Follow up" suggestion prompts in chat (also
# PersistentConfig: first-boot default, owner can re-enable in the UI).
export ENABLE_FOLLOW_UP_GENERATION="False"

# Front Open WebUI with a local Caddy that adds the security headers Open WebUI
# omits (X-Frame-Options, CSP frame-ancestors, nosniff, Referrer-Policy). Open
# WebUI binds loopback :8081 (see the exec below); Caddy serves the container's
# public :8080 and reverse-proxies to it. Restart it if it ever exits.
(
  # Keep Caddy's storage in the (writable, non-backed-up) temp dir. Guard the
  # mkdir so a failure here can't silently kill the subshell under `set -e`
  # (which would leave :8080 with no listener); log it and let Caddy try anyway.
  export XDG_CONFIG_HOME="$OPENHOST_APP_TEMP_DIR/caddy"
  export XDG_DATA_HOME="$OPENHOST_APP_TEMP_DIR/caddy"
  mkdir -p "$XDG_CONFIG_HOME" || echo "[openhost] warning: could not create $XDG_CONFIG_HOME" >&2
  while true; do
    rc=0
    caddy run --config /app/Caddyfile --adapter caddyfile || rc=$?
    echo "[openhost] caddy exited (rc=$rc), restarting in 2s" >&2
    sleep 2
  done
) &

# Bind Open WebUI to loopback :8081 behind Caddy. Scope HOST/PORT to this exec
# so they don't leak into the wider environment.
cd /app/backend
exec env HOST="127.0.0.1" PORT="8081" bash /app/backend/start.sh "$@"
