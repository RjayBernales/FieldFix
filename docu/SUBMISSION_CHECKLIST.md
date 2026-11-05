# Submission checklist

Current judging update (2026-11-05 UTC): code-free live Meta sessions, shared cap **100**, **33 used** at validation; navy UI and **64 backend tests** checked. [Latest actual report](public-live-navy-results.json), [UI report](navy-ui-validation.json). Historical counts/budgets below describe their original audits. Quick Tunnel availability and manual submission remain participant responsibilities.

## Latest specification audit

[Full matrix](AUDIT.md): 56 backend tests, build, fresh-package setup, mock browser regressions, three fresh genuine Meta repairs plus healthy and a genuine Meta browser repair passed. The audit used 26/30 requests; the subsequent video capture brought local usage to 28/30. PR #24 merged after both final-head checks passed (tested c763ad8; merge 666c03f). Stable free hosting and key rotation remain incomplete owner gates.

## Live demonstration gates

- [ ] Rotate the credential that appeared in tool output; configure its replacement only in ignored .env or local environment.
- [x] Genuine inference and diagnostic tool-result round trip passed; preserve sanitized evidence and tested commit.
- [x] Three varied live primary cases and a live healthy baseline passed within budget; initial failures retained.
- [x] Browser primary/healthy/negative, responsive, outage, key-absence and automated-a11y checks executed; fixes and sanitized evidence included. Remaining manual accessibility limits documented.
- [x] Fresh checkout: normal frozen installs, 56 tests, build, empty example env, and secret scan passed.
- [x] Backend tests, frontend build, secret scan, and new public-session regressions passed; final diff review performed before publication.
- [x] Replace old blocked statuses with actual measured results while preserving failed attempts and remaining limitations.

## GitHub delivery — approval required for each interaction

- [x] Verified RjayBernales authentication and local author/committer RjayBernales <rainieljevson0@gmail.com>.
- [x] Participant authorized remote inspection, issue creation, push, PR, labels, and merge after checks. Delegate approved GitHub operations to gpt-6-luna.
- [x] All 13 approved issue tickets created; implementation PR links fixed tickets and references the credential-rotation follow-up.
- [x] Pushed dev/fieldfix-mvp without force; PR #15 targets main with enhancement, documentation, bug and accessibility labels.
- [x] Reviewed the complete diff and local checks; actual GitHub verification passed. Final updated-head checks must pass before merge.
- [x] Participant subsequently authorized hands-off completion through merge after checks. Never bypass protections, change visibility, or overwrite unrelated changes.
- [x] PR #15 and validation commits recorded; final merge/check state and tested/merge SHAs are provided in the handoff and on GitHub.

## Participant submission — not performed by this implementation

- [ ] Confirm current eligibility, rubric, required fields, contributor information, and deadline on the organizer platform. Do not rely solely on a copied deadline.
- [ ] Confirm repository access appropriate for submission; do not change visibility without approval.
- [x] Created the local three-minute Remotion demonstration with visible simulator/provider labels, free AI narration and captions. Export verified: 180 seconds, 1920×1080, 30 fps, H.264/AAC, full decode passed. Not uploaded.
- [ ] Upload video manually and verify its public link and repository link from a signed-out context.
- [ ] Complete and submit the competition form manually; retain confirmation.

The participant requested free hosting: a temporary isolated mock preview was verified. No paid hosting, video upload, or competition entry submission was performed.
