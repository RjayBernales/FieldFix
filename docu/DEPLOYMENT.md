# Free demo hosting

Current verified preview: **https://flood-inf-written-automotive.trycloudflare.com**

This is a **temporary Cloudflare Quick Tunnel** to the Python app, not a permanent Render deployment. It requires the preview computer and tunnel process to remain running. Cloudflare provides no uptime guarantee for Quick Tunnels, and the hostname changes if the tunnel is recreated. [Official limitations](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

The original Quick Tunnel expired while its process was still running. This replacement was verified on 2026-11-04 with session startup, diagnosis, approval, 3/3 recovery, and logout. It is a temporary preview; [#17](https://github.com/RjayBernales/FieldFix/issues/17) remains open for a stable free host.

The URL serves the actual FastAPI backend and compiled React dashboard. Online inference is explicitly **mock-only**, with no Meta key and a zero live-request limit. The separate genuine Meta validation is recorded in VALIDATION.md. It is never represented as an online Meta run or a real field deployment.

## Visitor protection

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
