# FieldFix

An AI troubleshooting assistant for technicians maintaining environmental monitoring stations.

FieldFix is designed to gather diagnostic evidence, propose a bounded repair, request technician approval, and verify recovery using fresh station samples.

**Status: specification stage.** Application code, installation commands, and validation results are not yet available. The architecture and workflow below describe the planned MVP.

## The problem

A frozen monitoring dashboard can hide several different failures: a device may have stopped sampling, transport may be interrupted, or the dashboard may be listening on the wrong topic. Technicians need evidence that separates these possibilities before changing configuration.

## Planned demo

The MVP uses a clearly labeled software simulation of a water turbidity station:

1. Local readings continue changing while dashboard readings become stale.
2. The technician starts an investigation.
3. FieldFix uses diagnostic tools to compare local and received samples, inspect logs, and read transport configuration.
4. The agent proposes an exact subscription-topic correction supported by evidence.
5. The technician approves or rejects the proposal.
6. After an approved repair, a deterministic verifier checks for at least three distinct, fresh post-repair samples before reporting recovery.

The transport is an in-process topic router, not a real MQTT broker. Synthetic station data remains synthetic when a live model analyzes it. This project does not claim real hardware integration, field deployment, or environmental safety assessment.

## Planned architecture

| Component | Technology and responsibility |
| --- | --- |
| Backend | Python 3.11+, FastAPI, and Pydantic; validated tools and approval workflow |
| Persistence | SQLite; samples, evidence, proposals, approvals, and verification outcomes |
| Frontend | React, TypeScript, and Vite; station dashboard and investigation timeline |
| Station simulator | Independent sample generation and topic-based delivery |
| Inference | Backend-only Meta API integration with bounded tool calls |
| Verification | Deterministic freshness, sequence, and post-repair checks |

The initial backend will run with one server worker. API credentials must stay on the server and out of browser assets, logs, and repository history.

## Repair safeguards

- Diagnostic tools expose bounded, structured evidence rather than arbitrary commands.
- Simulator fault labels and expected answers must remain outside model inputs.
- A proposal must identify the station, exact before/after configuration, evidence, configuration version, and expiration.
- Approval applies only to that exact proposal. Expired, replayed, or stale proposals must not mutate configuration.
- A successful configuration write alone does not establish recovery. Failed verification remains unresolved.
- Mock inference must be explicitly labeled and must never silently replace live inference.

## Setup and launch

There is no runnable application in the current workspace yet. Install, launch, and test commands will be added with the implementation and verified from a fresh checkout. Do not treat the planned technology list as a working setup guide.

The implementation will include a secret-free `.env.example`, locked dependencies, and separate documented mock and live modes. Configure credentials locally using environment variables or an ignored `.env`; never commit API keys.

## Validation plan

Validation will cover simulator behavior, evidence boundaries, healthy operation, approval rejection and replay protection, stale configuration, recovery freshness, provider failures, backend tests, frontend checks, and a browser workflow.

Actual outcomes will be recorded in `docu/VALIDATION.md` with the tested commit, environment, scenario, provider/model, timing, tool-call count, available usage metadata, failures, and limitations. That report has not been produced yet.

Synthetic station behavior, mocked tests, and live Meta inference will be reported separately. Planned live validation includes three primary-case runs and a healthy baseline, subject to credentials and a bounded request budget. No live results are claimed at this stage.

## Development and delivery

Implementation is planned on `dev/fieldfix-mvp`, with focused, descriptive commits and PRs targeting `main`. Required checks and diff review must pass before a merge is proposed. GitHub operations require the repository owner's approval and must use the authorized account.

Runtime prompts, tool definitions, source, tests, simulator, dependency files, setup documentation, and sanitized validation evidence belong in version control. Private planning material and local agent instructions remain untracked; local exclusions belong in `.git/info/exclude`.

## Scope and limitations

The MVP prioritizes one station and one transport-mismatch investigation. Additional sensor-read and unavailable-evidence scenarios follow only after the primary workflow works end to end. Hardware repair, fleet management, arbitrary remote commands, and environmental interpretation are outside this scope.

The submission package will document implemented functionality, reproducible validation, limitations, and actual hackathon contributions. Competition submission and video upload remain manual participant steps.
