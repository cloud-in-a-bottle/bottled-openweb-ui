# bottled-openweb-ui

[Open WebUI](https://github.com/open-webui/open-webui), a self-hosted web
interface for large language models, packaged as a Cloud in a Bottle app.

## What you get

- A full chat UI for large language models, with conversations, folders, notes,
  and file/knowledge uploads.
- Owner auto-login: the Cloud in a Bottle router already authenticates you, so
  Open WebUI runs in single-user mode and you land directly in the app as the
  admin, with no separate Open WebUI login.
- A model provider wired up automatically to your instance's Bifrost LLM
  gateway.

## Models

Open WebUI gets its models from the [Bifrost LLM
gateway](https://github.com/imbue-openhost/bottled-bifrost) on your instance.
Install the Bifrost gateway app, configure at least one provider in it, and
approve this app's access grant at install time. The connection is set up for
you on first boot; you can manage it later under Admin Settings, Connections.
Model API keys live in the gateway, not in this app.

## Usage

Open the app and start a chat. Your conversations, uploads, and settings are
saved to your instance.

## Caveats

- Chat replies need the Bifrost gateway installed and configured with a working
  provider; until then the UI loads but has no models to talk to.
- The app runs in single-user mode as the owner. Turning on Open WebUI's own
  multi-user login is a packaging change (edit the startup wrapper and
  redeploy), not a runtime setting.

## Data

Backed up: the database, settings, uploads, vector data, and the session
signing key. Not backed up: the model cache (embedding, speech, and tokenizer
models), which is large and regenerates on demand.

## Resources

2 GB RAM, 1 CPU core.

## License

Open WebUI is distributed under the Open WebUI License, a BSD-3-Clause-style
license with an added branding-protection clause. Because this image bundles
Open WebUI, the image as a whole is conveyed under that license (see LICENSE).
The packaging files original to this repository are additionally offered under
the MIT License; see NOTICE.
