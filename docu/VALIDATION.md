# FieldFix validation — actual results

Report updated: 2026-11-04T08:20:59.598458+00:00.

**The simulated-station MVP passed local, genuine Meta, public-preview, Docker, and fresh-checkout workflows.** All station values and transport are synthetic. No real hardware, field deployment, model accuracy, environmental safety, or social-impact result is claimed.

## Tested code and delivery

- Local genuine-Meta runtime/dependency commit: `2be09e836d7eab6a2263780d85e968a9ad5f3728` on `dev/fieldfix-mvp`.
- Local genuine-Meta runtime source SHA-256: `c4f20693561652dff25d931e7ad74278351b373eca230c047353abb2d49bca8b`; [manifest](source-manifest.json). This fingerprint is distinct from a Git SHA.
- The genuine-Meta suite/browser evidence uses that exact earlier commit. Free-hosting/session support was subsequently added and tested at `2b905d4d1e6ed806818b61ce40e3c84a020b749f`; no paid inference was rerun for the mock-only public layer. The public-runtime snapshot used SHA-256 `5b50887ebc34e1fa0402da82867f955568de1503539752b611b04a0f83c11ab3`. Subsequent CI/packaging changes are identified by the current source manifest.
- Local commits use `RjayBernales <rainieljevson0@gmail.com>` as author and committer. Original remote history was restored through approved read-only sync; no unrelated history was replaced.
- GitHub delivery is authorized. All thirteen issues were created and verified; confirmed links are in GITHUB_ISSUES.md. Implementation PR: [#15](https://github.com/RjayBernales/FieldFix/pull/15); its check/merge state is authoritative. Publishing and labels were verified; final merge/check results are included in the handoff. The earlier README-only PR #1 is not the implementation PR.

## Environment and limits

Linux x86_64; Python 3.12.13; Node.js 26.9.0; npm 12.0.2; Vite 8.3.5; backend packages pinned in requirements.lock, including AnyIO 4.16.0. One backend worker. HeadlessChrome 151.0.0.0.

The original restricted session denied sockets/DNS and prevented Git restoration. After the participant enabled full access, localhost, package registries, GitHub authentication/read-only sync, hosted Meta inference, and browser checks worked. The initial blocked attempts remain recorded rather than being counted as successes.

## Synthetic station and mocked tests

Provider/model: **mock / deterministic-offline-fixture**. Test station data is synthetic; deterministic recovery tests inject a clock. These checks make no genuine inference calls.

| Check | Actual outcome |
| --- | --- |
| Backend suite after dependency/security fixes | **56 passed**, 4.24 seconds after free-hosting additions; fresh checkout: 56 passed in 6.69 seconds |
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
| TypeScript + Vite 8 production build | **Passed**; 15 modules, JS 200.60 kB / 63.81 kB gzip, CSS 13.57 kB / 3.82 kB gzip |
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
| Clean setup | **Passed** in a new detached Git worktree: documented installs, empty example env, 56 tests, build, and secret scan. [checkout-results.json](checkout-results.json) |

[Dependency audit evidence](dependency-audit.json), [browser checklist and limitations](BROWSER_CHECKLIST.md), and sanitized [screenshots](evidence/) are tracked. Registry/a11y scans are bounded checks, not security or accessibility certification. Other OS/browser/device combinations, zoom/reduced-motion visual checks, live secondary faults, and hardware integration remain untested.

## Credentials, Git approval, and remaining submission steps

The key initially configured in .env.example was moved to mode-0600 ignored .env and removed from the example before any implementation commit/publication. It appeared in local tool output; **participant rotation is still required**. No secret is present in this evidence or the review archive.

The build pack, conversations, local AGENTS instructions, private auth/configuration, and planning remain excluded via the actual local Git metadata's info/exclude. Runtime prompt/tool definitions, source, tests, simulator, dependency locks, README/.env.example, and sanitized validation evidence are tracked.

The participant authorized hands-off GitHub delivery through merge after checks/review. Use only the authorized account; never infer a successful push/PR/merge from a failed API response. Do not force-push, bypass protections, change visibility, submit the competition entry, or upload a video.

The local `.data/fieldfix-review.zip` is generated from an explicit allowlist, checked against the configured key, and includes source/tests/setup/runtime prompts and sanitized evidence. It excludes .env, SQLite, Git/auth metadata, private build pack, caches and dependency directories. It has not been uploaded.

## Free public preview and hands-on guide

[Open the verified temporary app](https://interests-codes-arabic-instructor.trycloudflare.com) · [SELF_TEST_GUIDE.md](SELF_TEST_GUIDE.md) · [DEPLOYMENT.md](DEPLOYMENT.md). The online site runs the actual Python simulator/API/approval/verifier and compiled frontend, with **mock inference only** and no Meta key.

Public HTTPS tests passed session creation, investigation/proposal/approval/recovery, separate-visitor history and proposal isolation, origin checks, and independent logout. The public-page axe audit had zero automated violations (the same documented SVG manual-review category remains incomplete). Actual evidence: [public-preview-results.json](public-preview-results.json), [welcome](evidence/public-welcome.png), [recovery](evidence/public-recovered.png).

The Docker image built and ran as UID 10001, served the static app and session API, and contained no .env or Meta key. New tests check expiry cleanup, quotas/body limits, mock-only startup, and slow session-body handling without holding the global lock.

This is an account-free Cloudflare Quick Tunnel, not permanent hosting: it requires the preview computer/tunnel to stay running, and has no uptime guarantee. No Render service/account was connected or created; a **free-only** blueprint is prepared. No paid service was created. These limits are visible in the README and guide. The public factory refuses Meta/key configuration rather than silently falling back.

GitHub automation: `.github/workflows/verify.yml` pins verified official action commits, installs locked dependencies, runs the backend/frontend/secret checks, and builds the Docker image. It makes no live Meta calls. Both initial remote runs for `bc994b4d55cc7e30bfd99bbf924211ae292d0b22` passed: [push verification](https://github.com/RjayBernales/FieldFix/actions/runs/41798177349) and [PR verification](https://github.com/RjayBernales/FieldFix/actions/runs/41798304777). The final documentation/secret-detector update is checked again on the PR before merging. No branch protections or visibility settings were changed.

Secret-detector regression: the real scanner was exercised in a separate benign fixture directory, then with a synthetic unquoted Meta-format key. It passed the benign tree, rejected the unsafe example, and did not echo the synthetic value. No real key was used in the regression.
