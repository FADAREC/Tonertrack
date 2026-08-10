# TonerTrack

Printer toner visibility for a company fleet. Hosted frontend + backend.

## What it does (v1 / Step 1)

- Fully hosted app (one URL)
- Login / register
- **Trust screen** — clear what we access; Manual only never contacts your network
- **Fleet list** — name, location, status, toner (or Unknown)
- **Add printer (manual)** — no network probe

Network agent (listed IPs only) comes later. Subnet scan is disabled on purpose.

## Trust model

- Only printer IPs you add (when agent exists)
- Never scans the rest of the LAN
- Manual mode always available
- Risks explained before any network path

## Deploy on Render

1. New Web Service from this repo, **Docker** runtime (uses `Dockerfile`).
2. Add Postgres and set `DATABASE_URL`.
3. Set `JWT_SECRET_KEY` (32+ chars), `ENV=production`.
4. Set `CORS_ORIGINS` to your public app URL.
5. Health check: `/health`.

Or use `render.yaml` blueprint.

## Local dev

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export JWT_SECRET_KEY='dev-only-change-me-use-32chars-min!!'
uvicorn main:app --reload
```

Frontend:

```bash
cd frontend && npm install && REACT_APP_API_URL=http://localhost:8000 npm start
```

## Pilot

One office · ~30 printers · ~50% HP · Manual path first.
