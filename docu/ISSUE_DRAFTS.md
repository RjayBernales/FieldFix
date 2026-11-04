# Development issue tickets awaiting GitHub approval

These are local ticket drafts, not published GitHub issues. Only approved authentication and read-only repository sync have occurred; no implementation push, issue creation, PR, or merge has occurred. Routine corrections are grouped by root cause.

## FF-001 — Local execution restrictions initially blocked live and browser verification

Suggested label: `bug` (environment/validation blocker)

- Reproduction: dependency downloads fail DNS lookup; uvicorn cannot bind 127.0.0.1:8000; Node HTTP listen returns EPERM; agent-browser daemon cannot start. The project .git directory is an empty, read-only mount.
- Impact: genuine Meta inference and a browser end-to-end check cannot be completed in this runtime; the mounted .git cannot be initialized. The original /tmp Git metadata also did not survive the next execution turn.
- Mitigation: offline cached dependency installation, an isolated persistent `.local/git` with local-only exclusions and the agreed author/committer settings (no refs yet), HTTPX ASGI API tests, and a reproducible live harness. No protections or permissions were bypassed.
- Verification: see VALIDATION.md. Resolved after the participant enabled full access: live and browser checks subsequently passed, and approved read-only GitHub sync restored original history. Credentials are now accessible in ignored .env, but network access remains blocked; no key value is recorded.

## FF-002 — Offline frontend install omitted Rollup native optional dependencies

Suggested label: `bug`

- Reproduction: initial Vite production build failed to load @rollup/rollup-linux-x64-gnu; initial frozen installation rejected missing optional package entries.
- Initial offline mitigation pinned Rollup and supplied cached native optional packages. That temporary workaround was removed when network access enabled the Vite 8.3.5 upgrade and registry-backed lock regeneration.
- Impact: build reproducibility on the tested Linux x64 platform. Other operating systems remain untested.
- Verification: npm ci from the offline cache and production build (actual final results in VALIDATION.md).

## FF-003 — Threaded test client stalled in the restricted runtime

Suggested label: `bug`

- Reproduction: Starlette TestClient hung entering its AnyIO thread portal; faulthandler showed the blocking portal startup.
- Fix: run API integration tests through HTTPX ASGITransport with the real application lifespan, and use async route handlers for short local SQLite operations. This fits the single-worker MVP and avoids thread handoff for each endpoint.
- Verification: 39 backend tests passed after the change. The real network/browser path remains a separate pending check.

## FF-004 — Keep credentials out of the tracked environment example

Suggested label: `bug`

- Reproduction: a credential was configured in `.env.example` rather than an ignored local `.env`.
- Impact: the example would be unsafe to commit. It was not committed or published by this implementation. The value appeared during local tool inspection, so rotation is required.
- Fix: moved it to mode-0600 ignored `.env`, restored an empty example value, and added a known-key comparison to the deliverable secret scan. No key is included in this ticket.
- Remaining participant action: rotate the affected key and configure the replacement locally.
- Verification: secret scan confirms the current configured key is absent from deliverables; Git exclusion verification passed after original history was restored.

## FF-005 — Expired proposals and cancelled investigations must terminate cleanly

Suggested label: `bug`

- Reproduction: an unapproved expired proposal could retain an active state; cancellation could leave the underlying inference request running until its timeout.
- Fix: simulator ticks expire pending proposals without configuration writes; cancellation explicitly cancels the incident's background task. Reset/restart retain their separate invalidation behavior. Overall deadline cancellation now also reports an explicit timeout instead of a generic protocol error.
- Verification: regression tests check expiry becomes unresolved with unchanged configuration and that cancelling reaches the waiting provider coroutine.

## FF-006 — Keep provider telemetry bounded and distinguish failure classes

Suggested label: `bug`

- Reproduction: generic connection/protocol failure text could not distinguish transport failures from malformed responses, and usage metadata was accepted wholesale.
- Fix: retain an explicit failure category, HTTP status when returned, returned model ID, and only numeric prompt/completion/total token counts. Hidden reasoning is excluded from replay and persistence.
- Verification: mocked HTTP tests assert the documented developer role/token parameter, proper tool-result replay, actual returned-model field, and absence of raw provider extras and hidden reasoning in persisted/replayed data. This remains mocked protocol evidence, not live validation.

Read-only history sync update: participant approval was received, and a fresh GitHub device sign-in was attempted. OAuth token polling failed DNS resolution after participant authorization. No new credential was confirmed, no source was overwritten, and no remote mutation occurred. Additional approval is not the blocker for that sync; working network access is required.

## FF-007 — Hosted inference latency invalidated otherwise valid repair proposals

Suggested label: `bug`. Fixed locally.

- Live reproduction: the first hosted tool-loop completed five model turns and ten tool calls but rejected two proposals with “Local sampling evidence is stale”; the final finding was unresolved. See live-retry.json.
- Root cause: proposal validation applied the recovery verifier's six-second threshold to the historical sample the model had read, even though independent sampling continued during inference.
- Fix: keep cited evidence immutable and bounded to the investigation window; independently require the acquisition path and current local sample to be available/fresh when proposing. The recovery verifier still requires three distinct post-repair samples and a latest sample no older than six seconds. Configure low reasoning effort for the short diagnostic loop.
- Verification: regressions cover delayed reasoning with continuing sampling and a new acquisition failure despite recent cached samples. Three live primary cases and one live browser approval/recovery workflow subsequently passed.

## FF-008 — Browser polling, resets, and historical provider labels were confusing

Suggested label: `bug`. Fixed locally.

- Reproduction: starting the frontend before the backend showed a raw JSON parsing error; the alert persisted after connectivity recovered. Reset automatically reselected an old incident, and historical records could be viewed under a different current provider mode.
- Fix: bounded frontend requests, readable connection errors with independent recovery state, explicit new-investigation selection after reset, and a provider label on each record.
- Verification: real browser outage/restart, reset, rejection, approval/recovery, healthy baseline, secondary faults, and mode/record checks passed; browser-results.json records the outcomes.

## FF-009 — Automated accessibility audit found low-contrast status labels

Suggested label: `bug`. Fixed locally.

- Reproduction: axe 4.12.1 reported a contrast violation affecting eyebrow, metric, proposal-expiration, and progress labels.
- Fix: darkened the flagged foreground colors, pinned the desktop sidebar position, made the skip link focus the main landmark, and enlarged narrow-screen SVG labels.
- Verification: desktop, mobile, and final live-page audits report zero automated violations. SVG labels retain one automated incomplete category; manual contrast calculations are 6.38:1 on the panel and 5.36:1 on stale-interval shading. No full screen-reader or real-device certification is claimed.

## FF-010 — Cached Vite/esbuild toolchain had published dependency advisories

Suggested label: `bug`. Fixed locally.

- Reproduction: the online npm audit found one high and one moderate advisory with Vite 5.4.21/esbuild.
- Fix: upgrade to Vite 8.3.5 and regenerate the registry-backed lockfile; remove temporary Rollup overrides/platform declarations. Document the supported Node versions.
- Verification: production build, dev-server browser smoke, and npm audit passed; final npm audit reports zero known findings. dependency-audit.json retains the before/after counts.

## FF-011 — Pinned AnyIO version had two published advisories

Suggested label: `bug`. Fixed locally.

- Reproduction: pip-audit reported PYSEC-2026-4025 and PYSEC-2026-4024 in AnyIO 4.12.1.
- Fix: require AnyIO >=4.14.2,<5 and resolve the lock to 4.16.0.
- Verification: all 48 backend tests, live Meta scenarios, and final browser live workflow passed. Final pip-audit reports zero known findings. No exploitation is claimed.

Status summary: FF-001/002/003/005–011 are fixed or environment-resolved and have validation evidence. FF-004 repository hygiene is fixed; participant key rotation remains an external action. All tickets remain unpublished until GitHub approval.
