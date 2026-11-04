# FieldFix validation — actual results

Report updated: 2026-11-04T05:41:11.006421+00:00.

**Local simulated-station MVP passed its primary offline, live Meta, and browser workflows.** All station values and transport are synthetic. No real hardware, field deployment, model accuracy, environmental safety, or social-impact result is claimed.

## Tested code and delivery

- Runtime and dependency commit: `2be09e836d7eab6a2263780d85e968a9ad5f3728` on `dev/fieldfix-mvp`.
- Runtime source SHA-256: `c4f20693561652dff25d931e7ad74278351b373eca230c047353abb2d49bca8b`; [manifest](source-manifest.json). This fingerprint is distinct from a Git SHA.
- The live suite and final live browser workflow ran against this commit. Subsequent documentation/evidence commits do not change runtime files.
- Local commits use `RjayBernales <rainieljevson0@gmail.com>` as author and committer. Original remote history was restored through approved read-only sync; no unrelated history was replaced.
- Implementation PR: **not opened**; merge: **not performed**. Push, issue creation, labels, PR creation, and merging still require approval. The earlier README-only PR #1 is not the implementation PR.

## Environment and limits

Linux x86_64; Python 3.12.13; Node.js 26.9.0; npm 12.0.2; Vite 8.3.5; backend packages pinned in requirements.lock, including AnyIO 4.16.0. One backend worker. HeadlessChrome 151.0.0.0.

The original restricted session denied sockets/DNS and prevented Git restoration. After the participant enabled full access, localhost, package registries, GitHub authentication/read-only sync, hosted Meta inference, and browser checks worked. The initial blocked attempts remain recorded rather than being counted as successes.

## Synthetic station and mocked tests

Provider/model: **mock / deterministic-offline-fixture**. Test station data is synthetic; deterministic recovery tests inject a clock. These checks make no genuine inference calls.

| Check | Actual outcome |
| --- | --- |
| Backend suite after dependency/security fixes | **48 passed**, 2.69 seconds in the recorded rerun |
| Deterministic offline harness | **4/4 passed**, zero live requests; [offline-results.json](offline-results.json) |
| Simulator/router | Local sampling continues independently while delivery is broken; matching topics resume actual simulated delivery |
| Approval | Rejection/no approval, wrong station, expiry, stale version, reset/restart invalidation, replay and concurrent decisions checked |
| Recovery | Pre-repair, duplicate, cached, future or stale samples do not establish recovery; failed delivery/timeouts remain unresolved |
| Proposal guard | Historical evidence remains immutable; current acquisition must still be available/fresh; inference latency alone does not invalidate a current healthy device |
| Agent boundary | Typed limits, unknown tools, malformed arguments, fixture-control exclusion, evidence references, turn/tool bounds, context bounds, cancellation and overall timeout checked |
| API | In-process HTTPX ASGI workflow, lifecycle, history, local-host/client/origin restrictions, payload limits, missing credentials and disabled controls checked |
| Secondary cases | Mock healthy has no repair; mock acquisition failure and unavailable evidence remain unresolved with no topic repair |

Healthy operation uses terminal state `unresolved` with a no-fault finding: this state machine reserves `resolved` for deterministic post-repair recovery. Offline sample-interval advances are simulated, not measured wall-clock recovery latency.

Mocked Meta HTTP tests separately verify request parameters, schemas, assistant/tool replay and matching IDs, numeric usage allowlisting, hidden-reasoning/key exclusion, returned-model capture, HTTP/timeout/protocol failures, and persistent budget exhaustion. They use HTTPX MockTransport and do not establish hosted model behavior.

## Genuine Meta inference

Official docs checked on 2026-11-04: [quickstart](https://dev.meta.ai/docs/quickstart), [models](https://dev.meta.ai/docs/models), [Chat Completions](https://dev.meta.ai/docs/protocols/chat-completions), and [tool calling](https://dev.meta.ai/docs/tool-calling). Endpoint: `https://api.meta.ai/v1/chat/completions`, Bearer authentication, model `muse-spark-1.3`, low reasoning effort, bounded output. HTTPX implements the documented OpenAI-compatible wire format; no provider SDK assumptions are required.

### Failed attempts retained

| Record | Actual result |
| --- | --- |
| [live-results.json](live-results.json), 01:23 UTC | Restricted-session connection/protocol failure; 0 completed turns, 0 tools, no returned request ID or usage; 3.01 seconds |
| [live-retry.json](live-retry.json), 05:19 UTC | **Genuine inference/tool-result round trip passed**, but repair failed: 5 turns/10 tools, two proposal rejections for stale historical sampling evidence, final unresolved; 51.85 seconds |

These earlier attempts were from uncommitted workspaces and did not capture source hashes. The current fingerprint does not retroactively identify them. The latency failure led to FF-007's guard fix; it was not hidden or relabeled as successful recovery.

### Final repeated suite

Started at `2026-11-04T05:33:30.259513+00:00`. Actual detailed records, timestamps, evidence, proposals, request IDs, usage, and outcomes: [live-final.json](live-final.json).

| Case | Outcome | Elapsed seconds | Model turns | Tool calls |
| --- | --- | ---: | ---: | ---: |
| Mismatch, validation-1 topic | **Passed**, approved repair and recovery resolved | 12.98 | 2 | 6 |
| Mismatch, validation-2 topic | **Passed**, approved repair and recovery resolved | 14.19 | 2 | 6 |
| Mismatch, validation-3 topic | **Passed**, approved repair and recovery resolved | 12.61 | 2 | 6 |
| Healthy baseline, validation-4 topic | **Passed**, evidence-cited no-fault finding and no proposal | 7.44 | 2 | 5 |

Every response reported model `muse-spark-1.3`. Suite usage returned: **18,768 prompt tokens + 3,215 completion tokens = 21,983 total** across eight responses. Monetary cost was not returned and is not estimated. The harness used real inference with synthetic station evidence and explicitly approved the exact simulated repair proposals. Small samples are demonstrations, not accuracy estimates.

### Live browser workflow

The real browser also ran a separate Meta investigation, displayed its proposal, approved it, and observed deterministic recovery. Incident `inc_7a5b0a81d1b9460b`, created at `05:35:26.824311+00:00`, resolved at `05:35:52.239407+00:00` (includes operator/test interaction delay). **2 genuine model turns, 6 tools**, 3 fresh post-repair samples. Returned usage: **4,686 prompt + 800 completion = 5,486 total tokens**; cost not returned.

Evidence: [browser-results.json](browser-results.json), [live proposal](evidence/live-meta-proposal.png), [live recovered dashboard](evidence/live-meta-recovered.png). The visible badge says “Simulated station · live Meta inference.” No mock fallback was used.

At capture, the shared persistent budget showed **16/30 reserved live attempts**: one restricted-session failure, five requests in the first unresolved live loop, eight in the final suite, and two in the browser run. No further paid validation is needed for this snapshot. Changing limits requires usage review; request/token bounds do not guarantee a dollar cap.

## Browser, build, dependency and secret checks

| Check | Actual result / boundary |
| --- | --- |
| TypeScript + Vite 8 production build | **Passed**; 15 modules, JS 197.68 kB / 62.96 kB gzip, CSS 12.43 kB / 3.57 kB gzip |
| Real mock browser workflows | Rejection, approval/recovery, healthy/no-repair, acquisition failure, unavailable evidence, pause/resume, reset/history and provider labels passed |
| Real live Meta browser workflow | **Passed** through the running FastAPI API; proposal, approval, sample delivery and recovery observed |
| Responsive inspection | 375×812, 768×1024 and 1440×1000; no page-level horizontal overflow; screenshots inspected |
| Outage/recovery | Readable backend alert appeared after shutdown and cleared after restart |
| Keyboard | Skip link visible on focus; Enter focuses main landmark. Full keyboard-only/screen-reader audit not claimed |
| axe 4.12.1 WCAG 2 A/AA | Zero automated violations at desktop/mobile/final live page. One automated-incomplete SVG contrast category; manual calculated ratios 6.38:1 normal panel, 5.36:1 stale shading |
| Browser secret absence | Configured key absent from mock and live browser HAR captures, each 23 entries; raw HARs remain excluded/local |
| Source/browser-assets secret scan | Passed pattern and configured-key checks before packaging; no key value is printed or committed |
| npm advisory audit | Initial high/moderate Vite/esbuild findings fixed by Vite 8.3.5; final **0 known findings** |
| Python advisory audit | Two AnyIO 4.12.1 findings fixed with 4.16.0; final **0 known findings** |
| Clean setup | Earlier cached clean export passed; final fresh Git checkout verification is the next local delivery check and will be recorded below |

[Dependency audit evidence](dependency-audit.json), [browser checklist and limitations](BROWSER_CHECKLIST.md), and sanitized [screenshots](evidence/) are tracked. Registry/a11y scans are bounded checks, not security or accessibility certification. Other OS/browser/device combinations, zoom/reduced-motion visual checks, live secondary faults, and hardware integration remain untested.

## Credentials, Git approval, and remaining submission steps

The key initially configured in .env.example was moved to mode-0600 ignored .env and removed from the example before any implementation commit/publication. It appeared in local tool output; **participant rotation is still required**. No secret is present in this evidence or the review archive.

The build pack, conversations, local AGENTS instructions, private auth/configuration, and planning remain excluded via the actual local Git metadata's info/exclude. Runtime prompt/tool definitions, source, tests, simulator, dependency locks, README/.env.example, and sanitized validation evidence are tracked.

Next delivery steps: finish fresh-checkout verification and diff review; obtain approval to create the issue tickets, push dev/fieldfix-mvp, and open/label the implementation PR targeting main. Request separate merge approval after required checks and no unresolved blocking issues. Do not force-push, bypass protections, change visibility, submit the competition entry, or upload a video.

The local `.data/fieldfix-review.zip` is generated from an explicit allowlist, checked against the configured key, and includes source/tests/setup/runtime prompts and sanitized evidence. It excludes .env, SQLite, Git/auth metadata, private build pack, caches and dependency directories. It has not been uploaded.
