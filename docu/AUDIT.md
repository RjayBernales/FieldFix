# FieldFix specification audit

Audited 2026-11-04 UTC against the private root build pack, sections 1–11. Tested runtime `08a076e39abb9451c331649449884b1025cff046`. Evidence: [validation report](VALIDATION.md), [fresh live suite](audit-live-results.json), [browser report](audit-browser-results.json). The build pack remains untracked.

| Specification criterion | Outcome and evidence |
| --- | --- |
| Python/FastAPI/SQLite + React/TS/Vite, one worker | Implemented; 56 backend tests and strict frontend build pass |
| Independent 2-second acquisition and topic-based delivery | Implemented; router test and browser mismatch/recovery; varied topics in fresh genuine suite |
| UTC sample/evidence contract, original cached timestamps | Covered by implementation inspection and deterministic recovery tests |
| Typed allowlisted diagnostic/proposal tools | Seven tools inspected; malformed/unknown/extra arguments and wrong station rejected in tests |
| Evidence boundary, no scenario labels or expected answers | Runtime prompt/tools inspected; input/output boundary tests pass; genuine traces contain operational evidence only |
| Bounded genuine model tool loop | Official quickstart/models/tool-calling docs rechecked; 8 turns/12 tools/25s HTTP/120s overall/context limits and persistent 30-request budget inspected and tested |
| No fallback or canned live diagnosis | Separate Meta/mock adapters inspected; mock HTTP failures (401/429/500), malformed response and timeout tests pass without fallback |
| Exact approval and atomic mutation | No approval/rejection, wrong station, expiry, version, reset/restart, replay/concurrency tests pass; browser approve/reject pass |
| Deterministic 3-sample recovery, latest <=6s, 20s timeout | Tests reject cached/pre-repair/duplicate/stale samples; failed repair times out unresolved; current genuine browser and suite recover |
| Healthy baseline | Fresh genuine Meta and mock browser propose no mutation; terminal unresolved means no approved repair, with explicit no-fault finding |
| Sensor failure and insufficient evidence | Mock tests/browser pass with no repair; **not live Meta validated** |
| Dashboard evidence/proposal/progress/history/navigation | Complete local mock and genuine Meta workflow checked; desktop/mobile screenshots and automated accessibility results recorded |
| Public access controls | Isolated cookie sessions, bounds, origin/host checks covered by tests; public is mock-only with no key |
| Clean setup and package | Frozen installs and verification from fresh extracted ZIP pass; shell-script omission fixed. Original installation from a remote clone was not repeated in this audit |
| Secret hygiene | .env ignored/0600, example empty, key absent from browser HAR, scanner passes. **Rotation remains owner-unconfirmed** |
| Git/delivery | dev/fieldfix-mvp, required author/committer, focused fixes; #25/#26 created by delegated authorized GitHub agent. PR24 updated-head checks and merge must be verified before claiming delivery complete |
| Documentation and demo | README, self-test guide, three-minute script and checklist present; outdated temporary URL and budget text corrected |
| Competition submission | **Not complete:** eligibility/form/deadline/public repository/video links need owner verification; no upload or submission performed |

## Fixes made during this audit

1. Include `.sh` files so README's `bash scripts/verify.sh` works in the submission ZIP (commit `ddb7b1d`, issue #25).
2. Show inference/session claims only after the session endpoint confirms the hosting mode (commit `08a076e`, issue #26). The disconnected local Meta screen previously claimed mock inference. Browser regression now shows neutral checking mode and returns to live mode after reconnecting.
3. Update the expired preview link and stale request-budget documentation; preserve historical validation and distinguish the new suite.

## Remaining or untested criteria

- Credential rotation confirmation and a stable free hosting account connection remain open owner actions (#5/#17). Quick Tunnel DNS has expired twice; it is unsuitable as a durable judging link.
- Live secondary faults, hardware/MQTT integration, environmental interpretation, real mobile/Safari, screen-reader and cross-platform checks remain untested/out of scope. One automated SVG contrast category is incomplete.
- Mocked HTTP error tests establish adapter behavior, not observed Meta rate-limit/outage performance.
- The live sample is small and supports a demonstration, not model-accuracy or deployment claims. Monetary cost was not returned.
- Record the video locally with visible provider/simulator labels. Use actual current health budget (26/30 at this audit); do not reset/increase it silently. Leave the remaining four requests for recording.

Use README's launch commands and [DEMO_SCRIPT.md](DEMO_SCRIPT.md). **The core workflow is evidenced; the overall competition submission is not complete.**
