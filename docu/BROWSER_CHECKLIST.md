# Browser workflow verification

Executed in HeadlessChrome 151 on Linux. Actual records: [browser-results.json](browser-results.json); sanitized screenshots: [evidence/](evidence/). The station and transport are simulated in every mode.

- [x] 1440×1000, 768×1024, and 375×812: no page-level horizontal overflow; inspected screenshots and controls.
- [x] Simulator/provider labels visible; historical records identify their own provider.
- [x] Mock transport mismatch: investigate → exact proposal → reject, leaving unresolved.
- [x] Mock transport mismatch: investigate → approve → three post-repair samples → resolved.
- [x] Live Meta transport mismatch: real model/tool loop → visible proposal → browser approval → deterministic recovery, with screenshots.
- [x] Healthy mock baseline: no repair. Sensor failure and unavailable-evidence mock cases: unresolved and no repair.
- [x] Reset clears the previous selection; history remains available explicitly.
- [x] Backend outage shows a readable alert; restarting clears it automatically.
- [x] Pause notice is visible and investigation disabled while paused; resume works.
- [x] Keyboard skip link is visible on focus and Enter focuses main content; controls expose labels/focus styles.
- [x] Desktop, mobile, and final live-page axe WCAG 2 A/AA scans: zero automated violations. One SVG contrast category remains automated-incomplete; manual contrast calculations pass for normal/stale backgrounds.
- [x] Actual browser HAR captures in mock and live modes contain no configured API key. Raw HARs remain local and untracked.

Not completed: a full keyboard-only walkthrough of every control, screen-reader testing, real mobile devices/Safari, zoom/reduced-motion visual audits, and cross-platform installation. Missing-key and malformed request cases were checked through backend API tests rather than additional browser calls. Do not present these automated/headless checks as comprehensive accessibility certification.
