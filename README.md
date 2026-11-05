<p align="center">
  <img src="docu/images/fieldfix-readme-logo.svg" alt="FieldFix logo" width="360" />
</p>

<h1 align="center">FieldFix</h1>

<p align="center"><strong>Evidence before action. Verified recovery after repair.</strong></p>

<p align="center">
  AI-assisted troubleshooting for technicians maintaining environmental monitoring stations.<br />
  Find where delivery stops, approve one exact change, and prove that fresh data returns.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.11 or newer" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&amp;logo=fastapi&amp;logoColor=white" alt="FastAPI backend" />
  <img src="https://img.shields.io/badge/React-TypeScript-149ECA?style=flat-square&amp;logo=react&amp;logoColor=white" alt="React and TypeScript" />
  <img src="https://img.shields.io/badge/Meta-Muse-0866FF?style=flat-square&amp;logo=meta&amp;logoColor=white" alt="Meta Muse live inference adapter" />
  <img src="https://img.shields.io/badge/Station-Software_simulator-D99B43?style=flat-square" alt="Software station simulator" />
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="docu/SELF_TEST_GUIDE.md">Try it yourself</a> ·
  <a href="docu/VALIDATION.md">Validation evidence</a> ·
  <a href="docu/DEMO_SCRIPT.md">Demo script</a> ·
  <a href="docu/DEPLOYMENT.md">Hosting guide</a>
</p>

<p align="center">
  <img src="frontend/public/evidence/navy-dashboard.png" alt="FieldFix dashboard showing station telemetry, local and delivered readings, diagnostic activity, and technician repair review" width="100%" />
</p>

<p align="center"><em>Actual application capture. Station readings and transport are simulated; the provider badge identifies the inference mode.</em></p>

## Why FieldFix?

A frozen dashboard is a symptom. The device may still be collecting data while delivery has broken somewhere along the path. Replacing a sensor without checking that path can target the wrong problem.

FieldFix compares local and delivered samples, reads station status and logs, and checks publishing and subscription topics. It turns those observations into an evidence-backed proposal, keeps the technician in control of the exact change, and verifies recovery independently of the model.

**This is a working simulated-station MVP, not a field deployment or environmental safety system.** The [recorded audit](docu/VALIDATION.md) reports 56 deterministic backend tests, three genuine Meta repair cases, a genuine healthy baseline, and a genuine browser approval/recovery workflow. Mocked tests and live inference results are documented separately; these small demonstrations do not establish model accuracy.

## Features

- **Independent station simulation.** Synthetic turbidity samples arrive every two seconds, independently of inference, so acquisition and delivery can be investigated separately.
- **Topic-based delivery.** An in-process router delivers samples only when publishing and subscription topics match. This is simulated transport, not a real MQTT broker.
- **Evidence-backed diagnosis.** Typed tools expose station status, original local and received samples, logs, and transport configuration with evidence references and timestamps.
- **Bounded Meta tool use.** A server-only live provider runs a limited diagnostic loop. The model receives operational evidence rather than simulator labels or expected answers.
- **Exact technician approval.** Each repair proposal binds the station, before/after topic, configuration version, and expiry. Approval, rejection, and replay protection are enforced on the server.
- **Recovery that must be proved.** Resolution requires three distinct post-repair samples, newer sequences, and a latest sample no more than six seconds old. A configuration write alone cannot resolve an incident.
- **A dashboard built for investigation.** Telemetry, freshness, diagnostic activity, evidence inspection, proposal diffs, verification progress, cancellation, and history sit in separate Overview, Investigations, and Simulator views.
- **An explicit offline mode.** The deterministic mock provider supports offline contracts and UI development. Its badge stays visible, and live failures never fall back silently to mock inference.

Healthy operation, sensor-read failure, and unavailable diagnostic evidence are secondary simulator cases. Offline and mock browser checks cover them; the two secondary faults have not been validated with a live model.

## How it works

| Step | What happens |
| --- | --- |
| **1. Observe** | Compare the last delivered reading with current local samples and their original timestamps. |
| **2. Investigate** | The diagnostic agent selects typed tools; FieldFix records structured observations and evidence references. |
| **3. Review** | Inspect the proposed subscription-topic correction and its exact before/after values. Configuration stays unchanged. |
| **4. Approve** | A technician approves that specific, unexpired proposal against the current configuration version. |
| **5. Verify** | The deterministic verifier waits for three distinct fresh samples. Only verified recovery resolves the incident. |

For a guided walkthrough, open the [hands-on self-test guide](docu/SELF_TEST_GUIDE.md).

## Demo and preview

Run the application locally using the commands below. The current [Cloudflare judging demo](https://gtk-driver-politicians-however.trycloudflare.com) uses **genuine Meta Muse inference** with one-click isolated visitor sessions: no account or access code. Each session allows two investigations within one persistent **100-request shared cap**. The [recorded genuine Meta walkthrough](https://gtk-driver-politicians-however.trycloudflare.com/recorded-demo.html) makes no model calls. The separate optional mock factory makes no Meta calls. Account-free tunnel links expire when the host or tunnel stops, so they are not permanent hosting. See [hosting instructions and limits](docu/DEPLOYMENT.md).

The [three-minute demo script](docu/DEMO_SCRIPT.md), [actual validation report](docu/VALIDATION.md), and [specification audit](docu/AUDIT.md) explain the demonstrated behavior and remaining submission criteria. [Brand assets](frontend/public/brand/README.md) document the approved system logo used here and in the application.

## Quick start

Requirements: Python 3.12 recommended (project supports 3.11+), Node.js 20.19+ or 22.12+, npm, and [uv](https://docs.astral.sh/uv/). Tested here with Python 3.12.13, Node 26.9.0, and npm 12.0.2 on Linux x64. Other operating systems remain untested.

From the project root:

```bash
uv venv --python 3.12
uv pip sync requirements.lock
npm --prefix frontend ci --ignore-scripts
test -e .env || cp .env.example .env
```

Keep `.env` private. If it already exists, edit it rather than replacing it. The example intentionally contains no API key. `requirements.lock` pins all backend and test dependencies; `frontend/package-lock.json` locks frontend dependencies. No application installation scripts are needed.

Start the backend in terminal 1:

```bash
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

Start the dashboard in terminal 2:

```bash
npm --prefix frontend run dev
```

Open **http://127.0.0.1:5173**. The Vite server proxies `/api` to the backend. Keep exactly **one backend worker**. The ordinary factory is local-only. The mock public factory and the separate authenticated live Meta factory add isolated visitor sessions; live judging uses quota-controlled cookie sessions and a shared persistent budget; private-code hosting remains optional. See [DEPLOYMENT.md](docu/DEPLOYMENT.md). These launch commands were exercised locally after execution access was enabled; both mock and live Meta browser workflows were checked.

## Mock and live modes

The default `.env.example` selects `FIELDFIX_PROVIDER=mock`. The dashboard visibly identifies mock inference. It is an offline deterministic fixture and provides no evidence of model performance.

For actual Meta inference, edit the ignored `.env` locally:

```dotenv
FIELDFIX_PROVIDER=meta
MODEL_API_KEY=your-local-key
META_BASE_URL=https://api.meta.ai/v1
META_MODEL=muse-spark-1.3
META_REASONING_EFFORT=low
FIELDFIX_LIVE_REQUEST_LIMIT=30
```

Restart the backend after editing settings. These endpoint, model, Bearer authentication, and Chat Completions tool-call conventions were checked against Meta's official [quickstart](https://dev.meta.ai/docs/quickstart), [model catalog](https://dev.meta.ai/docs/models), and [tool calling guide](https://dev.meta.ai/docs/tool-calling) on November 4, 2026. The adapter uses HTTPX directly with the documented OpenAI-compatible wire format, rather than depending on an SDK.

The key never belongs in `.env.example`, source, browser assets, screenshots, or validation output. Live mode without a key rejects investigation requests. Provider failures remain failures and never switch mode.

Each investigation is limited to 8 model turns, 12 tool calls, a 25-second HTTP timeout, and a 120-second overall timeout. The persistent SQLite request counter reserves budget before every live request, including failed attempts; automatic retries are disabled. Review usage before increasing the cumulative limit. Token and request limits do not guarantee a monetary spending cap. SQLite records request IDs, latency, available usage metadata, and sanitized failure outcomes; it does not retain authorization headers or hidden reasoning.

## Reproduce the primary workflow

1. Select **Transport mismatch** in the development controls and click **Reset demo**.
2. Watch the dashboard reading remain stale while local readings change.
3. Click **Investigate station**. Inspect the evidence timeline and the exact subscription-topic proposal.
4. Confirm that configuration has not changed before approval. Rejecting leaves it unchanged.
5. Click **Approve repair** for that proposal. Delivery resumes when the two topics match.
6. Wait for three distinct post-repair samples. The incident becomes **resolved** only after the deterministic verifier passes; verification stops after 20 seconds if unsuccessful.
7. Reset to **Healthy station** and investigate again. Expect an evidence-backed no-fault finding and no repair. A healthy result uses terminal state `unresolved` because this MVP reserves `resolved` for verified post-repair recovery; read its finding text.

Development controls interrupt active investigations and invalidate pending proposals. They never appear in model tools or evidence. Set `FIELDFIX_ENABLE_DEMO=false` to hide/disable them. The API additionally rejects non-loopback clients, unrecognized hosts, cross-origin requests, and oversized request bodies. These local safeguards are not a public deployment authentication system.

## Tests and validation

```bash
bash scripts/verify.sh
```

For reproducible synthetic evidence without network requests, run `.venv/bin/python scripts/validate_offline.py`; it records all four simulator cases and a source fingerprint.

The verification command runs backend tests, strict TypeScript checking and the Vite production build, plus a pattern/known-key secret scan. No live API calls are made by this command.

For explicit live validation, after configuring a working key and network:

```bash
PYTHONPATH=backend .venv/bin/python scripts/validate_live.py --primary 3 --healthy --approve-repairs
```

The flag authorizes this harness to apply the exact simulated repair proposals it receives. The harness shares the configured database's live request budget, resets synthetic state, and records sanitized evidence in `docu/live-results.json`. Run it with the backend stopped to avoid multiple simulator loops or interrupted jobs. A failed transport attempt is recorded as a failure, never as successful live inference. It consumes live requests and may incur charges. It is not a deployment test. Keep the report's tested commit aligned with the code actually executed.

[VALIDATION.md](docu/VALIDATION.md) separates synthetic simulator checks, mocked HTTP/provider tests, and actual Meta attempts. [Browser checklist](docu/BROWSER_CHECKLIST.md) covers the network workflow, responsive sizes, errors, and accessibility. A successful compile or ASGI test does not establish browser usability or model performance.

## Architecture

```text
React dashboard → FastAPI approval and incident API → SQLite
                              ↓
                     bounded diagnostic agent
                         ↙             ↘
               Meta adapter       typed evidence tools
                                         ↓
                           simulated station + topic router
                                         ↓
                           deterministic recovery verifier
```

| Location | Purpose |
| --- | --- |
| `backend/app/core.py`, `storage.py` | Station simulation, transactions, state transitions, proposal approval, recovery |
| `backend/app/tools/` | Typed allowlist and model-facing evidence boundary |
| `backend/app/agent/` | Runtime system prompt, separate mock fixture, live provider, bounded agent loop |
| `backend/app/main.py` | Local API, background jobs, cancellation, development controls |
| `backend/app/hosted.py` | Isolated cookie-authorized free public mock sessions and limits |
| `frontend/src/` | Dashboard and responsive styles |
| `backend/tests/` | Simulator, security, state, recovery, agent and API regression tests |
| `docu/` | Sanitized validation, issue drafts, demo script, submission checklist |

SQLite state lives in ignored `.data/`. Samples retain original UTC timestamps; up to 600 recent samples and 200 operational events are retained. Incidents/evidence remain persisted for review. Restart marks interrupted jobs and awaiting approvals as unresolved/failed rather than resuming unverified work. The verifier polls every half second while the simulator samples every two seconds.

## Limitations and contribution disclosure

This workspace started with a specification and README. The backend, simulator, tools, prompt, agent adapters, UI, tests, and delivery documents were added during this implementation. No existing application scaffold was represented as newly built work.

No real station, MQTT broker, hardware repair, users, field deployment, measured impact, or environmental safety conclusions are claimed. One station, one process, local-only operation, small request budgets, and simulator evidence constrain the demo. Sensor failures request a physical check rather than claiming a hardware fix. Diagnostic access failures remain unresolved.

Genuine Meta tool use, three varied primary cases, a live healthy baseline, and an additional live browser repair workflow passed. An earlier live run exposed a proposal-freshness bug; its failure and the subsequent fix remain recorded. Cross-platform installation, real mobile devices, a full screen-reader audit, live secondary-fault cases, and any field deployment remain unvalidated. These small demonstrations do not establish model accuracy.

## Delivery and submission

Development uses `dev/fieldfix-mvp` with focused commits and PRs targeting `main`. GitHub interactions require owner approval and the authorized account. Runtime assets and sanitized evidence are tracked; conversations, build packs, private planning, and local agent instructions stay untracked through local Git exclusions.

See the [three-minute demo script](docu/DEMO_SCRIPT.md), [submission checklist](docu/SUBMISSION_CHECKLIST.md), and [development issue drafts](docu/ISSUE_DRAFTS.md). Competition submission, repository visibility changes, deployment, and video upload require participant action or separate authorization. No competition entry or video has been submitted.
