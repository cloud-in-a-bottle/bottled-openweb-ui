FROM ghcr.io/open-webui/open-webui:v0.9.5

# mitmproxy fronts the Bifrost gateway's service interface as a local OpenAI
# endpoint (see openhost_bifrost_proxy.py). Use the standalone binary so it
# doesn't touch Open WebUI's Python env. Checksum-verified before extracting.
RUN curl -fsSL -o /tmp/mitmproxy.tar.gz https://downloads.mitmproxy.org/12.2.3/mitmproxy-12.2.3-linux-x86_64.tar.gz \
    && echo "2e95286b618fa6fd33e5e62a78c2e5112571d85f42ec2bac29b97ee242bdb5c5  /tmp/mitmproxy.tar.gz" | sha256sum -c - \
    && tar -xzf /tmp/mitmproxy.tar.gz -C /usr/local/bin mitmdump \
    && rm /tmp/mitmproxy.tar.gz

# Caddy (pinned + checksum-verified) is a local sidecar that fronts Open WebUI
# to add the security headers it does not set (see Caddyfile / openhost_start.sh).
RUN curl -fsSL -o /tmp/caddy.tar.gz https://github.com/caddyserver/caddy/releases/download/v2.8.4/caddy_2.8.4_linux_amd64.tar.gz \
    && echo "b8bec15d14fb033562af9f207850027bcbaa1f891edc9efe00d38bf39e1bf9944f8b6b8eba041ddd4c171cd70c905174c704d705be2f23bc678fe1eaf37a2485  /tmp/caddy.tar.gz" | sha512sum -c - \
    && tar -xzf /tmp/caddy.tar.gz -C /usr/local/bin caddy \
    && rm /tmp/caddy.tar.gz

COPY openhost_bifrost_proxy.py /app/openhost_bifrost_proxy.py
COPY Caddyfile /app/Caddyfile
COPY openhost_start.sh /app/openhost_start.sh
RUN chmod +x /app/openhost_start.sh

EXPOSE 8080

CMD ["/app/openhost_start.sh"]
