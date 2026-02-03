# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the service

```bash
# Start both the webhook endpoint and Cloudflare tunnel
docker compose up -d

# Rebuild and restart after code changes
docker compose up -d --build

# View logs
docker compose logs -f webhook-endpoint

# Stop everything
docker compose down
```

The FastAPI app runs on port 8000 inside the container. Port 8000 is also mapped to the host (useful for local testing; comment it out in `docker-compose.yml` for production).

## Local development (without Docker)

```bash
pip install -r requirements.txt

# Run the FastAPI dev server with auto-reload
uvicorn api.api:app --host 0.0.0.0 --port 8000 --reload
```

The app expects a `webhook-requests/` directory relative to CWD for storing payloads. It is created automatically on first webhook receipt.

## Architecture

Two-container setup via `docker-compose.yml`:

1. **webhook-endpoint** — FastAPI app (`api/api.py`) that receives webhook POST requests and writes each payload to disk as a JSON file under `webhook-requests/freshdesk/<uuid>.json`. The volume mount makes those files available on the host.
2. **cloudflare-tunnel** — `cloudflared` sidecar that exposes the webhook endpoint publicly via a Cloudflare Zero Trust tunnel. It depends on the webhook container being healthy before starting. The tunnel token is provided via the `CLOUDFLARE_TUNNEL_TOKEN` env var (see `.env.example`).

The `cloudflare-tunnel` container has no direct network binding to the host — it reaches `webhook-endpoint` over the internal `webhook-network` bridge. The Cloudflare dashboard routes inbound traffic to `http://webhook-endpoint:8000`.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Service info and endpoint listing |
| GET | `/health` | Liveness check (used by Docker healthcheck) |
| POST | `/webhooks/freshdesk` | Receive and persist a Freshdesk webhook payload |

## Webhook payload storage

Each received webhook is saved as `webhook-requests/freshdesk/<request_id>.json` with the structure:

```json
{
  "request_id": "<uuid>",
  "timestamp": "<ISO 8601 UTC>",
  "source": "freshdesk",
  "payload": { /* original POST body */ }
}
```

The `webhook-requests/` directory is gitignored — payloads are local/ephemeral only.

## Security note

The `.env` file (containing the live tunnel token) is gitignored but a copy currently exists in the working tree. Never commit it. Use `.env.example` as the reference template.
