# Cloudflare live judging demo

Current verified preview: **https://gtk-driver-politicians-however.trycloudflare.com** (2026-11-05 UTC).

Click **Start live demo**. Remote judges need no account, access code, or contact with the presenter. The server issues an opaque Secure/HttpOnly cookie for an isolated 30-minute station session. The API key stays server-side. The inference badge visibly says Meta; there is no mock fallback.

The shared cumulative cap is **100 requests**, explicitly selected by the owner, with **33 used / 67 remaining** after validation. Each visitor session allows two investigations; creating/resetting a station never resets the durable global counter. There are at most three active live sessions, 12 session creations per minute, bounded bodies/timeouts, and per-session API/mutation quotas. This is controlled public access, not verified user identity. The cap is not a dollar spending guarantee.

[Actual code-free live results](public-live-navy-results.json): two genuine Meta responses, six tool calls, exact technician approval and 3/3 recovery. [Recorded evidence](https://gtk-driver-politicians-however.trycloudflare.com/recorded-demo.html) and the labeled landing-page evidence viewer use stored observations without model calls; they remain useful if the live budget is exhausted. All station values and transport are simulated. The earlier private-code validation remains historical evidence, not the current entry flow.

## Launch the judging host

Install locked dependencies, then run `npm --prefix frontend run build`. Keep the model/base URL/key in ignored `.env`. Configure these non-secret switches there:

```dotenv
FIELDFIX_PROVIDER=meta
FIELDFIX_PUBLIC_LIVE=true
FIELDFIX_LIVE_REQUEST_LIMIT=100
```

Do not erase `.data/fieldfix.sqlite`; it contains the shared counter and sanitized inference usage. The private-code mode remains available by setting `FIELDFIX_PUBLIC_LIVE=false` and supplying a strong `FIELDFIX_DEMO_ACCESS_CODE`. It is not required for current judging access.

Install `cloudflared` on PATH first. This workspace already has the executable at `.local/cloudflared`; use that path in place of `cloudflared` here. Start the free tunnel, then use its exact returned HTTPS origin:

```bash
cloudflared tunnel --url http://127.0.0.1:10000 --no-autoupdate
```

```bash
FIELDFIX_PROVIDER=meta FIELDFIX_PUBLIC_LIVE=true \
FIELDFIX_PUBLIC_ORIGIN=https://YOUR-RETURNED-HOST.trycloudflare.com \
PYTHONPATH=backend .venv/bin/python -m uvicorn app.hosted:create_live_demo_app --factory \
  --host 127.0.0.1 --port 10000 --workers 1 --no-proxy-headers
```

`FIELDFIX_PUBLIC_ORIGIN` can also be placed in ignored `.env`. Never tunnel the ordinary local factory. The hosted gateway retains same-origin checks, session isolation, typed tools, exact approval, and deterministic verification. Logout and expiry cancel session jobs and remove temporary station state; only sanitized inference metadata and budget usage persist in the owner ledger.

Cloudflare Quick Tunnels are temporary. This computer, its network, and both processes must stay running. Earlier endpoints expired with “Tunnel not found”; recreation changes the URL and requires the new exact backend origin. Initial DNS propagation and brief startup 502 responses were observed and rerun after readiness. No permanent named tunnel/domain or Render account is configured. [Official limitations](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/). Hosting is free; Meta usage may consume API credits.

## Optional public mock factory

`app.hosted:create_hosted_app` remains mock-only and refuses any Meta/key configuration. The historical public preview used this factory; it does **not** establish genuine model performance. The following mock-container instructions remain available for offline/public UI testing.

## Mock-factory visitor protection

- Visitors explicitly start a browser session; mutations and station history require an opaque, HttpOnly, SameSite-strict cookie, Secure on HTTPS.
- Each visitor gets a separate SQLite station, incident/proposal history, simulator loop, and approval state. An incident or proposal ID alone cannot authorize another visitor's request.
- Sessions expire after 30 minutes. Logout/expiry cancels background tasks and removes that session's temporary station data.
- Limits: 12 active sessions, 12 creations per minute globally, 600 API requests/minute and 30 mutations/minute per session, ten investigations per session, bounded request bodies/timeouts.
- Exact host/origin checks reject cross-site requests. The public factory refuses startup if configured for Meta or given MODEL_API_KEY. It does not silently fall back.
- The local factory keeps its loopback-only defaults and genuine Meta option.

## Run the same public-demo container locally

```bash
docker build -t fieldfix-demo .
docker run --rm -p 127.0.0.1:10000:10000 \
  -e FIELDFIX_PUBLIC_ORIGIN=http://127.0.0.1:10000 \
  fieldfix-demo
```

Open http://127.0.0.1:10000 and click **Start my demo session**. No API key is needed. The image runs as UID 10001 and excludes local .env, Git/auth metadata, databases, private instructions/build pack, and dependency directories. This container build and session startup were tested.

Without Docker, first build the frontend, then:

```bash
FIELDFIX_PROVIDER=mock MODEL_API_KEY= \
FIELDFIX_PUBLIC_ORIGIN=http://127.0.0.1:10000 PYTHONPATH=backend \
.venv/bin/python -m uvicorn app.hosted:create_hosted_app --factory \
  --host 127.0.0.1 --port 10000 --workers 1 --no-proxy-headers
```

The public factory intentionally does not load the local .env. Never expose the ordinary local factory through a public tunnel.

## Stable free Render URL — prepared, not deployed

The repository includes a Dockerfile and render.yaml selecting **plan: free**. No Render account connection was available, so no Render service/account or paid resource was created.

With an authorized Render account, deploy this public repository using render.yaml or a free Docker web service. Use one instance/worker, `/healthz` for health checks, `FIELDFIX_PROVIDER=mock`, and no Meta key. Render supplies RENDER_EXTERNAL_URL; an explicit FIELDFIX_PUBLIC_ORIGIN may also be set to the exact HTTPS service URL. Automatic deploys are disabled in the blueprint so code changes are reviewed first.

Free Render services sleep after inactivity and have ephemeral storage; that is appropriate for disposable mock sessions. [Free service limits](https://render.com/docs/free). Persistent hosting/live inference is outside this free deployment configuration. Do not choose a paid plan or disk without a new budget authorization.

After a future stable deployment, verify the new URL's full session/approval/recovery flow and replace the README's temporary URL with the actual returned service URL. Do not invent an onrender.com address.
