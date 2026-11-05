# Development issue registry

All 13 tickets were created under the authorized account. The implementation PR links the fixed tickets for closure. FF-004 remains open for participant credential rotation; its repository hygiene fix is included.

| Reference | Ticket | Disposition |
| --- | --- | --- |
| FF-001 | [#2: FF-001: Local execution restrictions initially blocked live and browser verification](https://github.com/RjayBernales/FieldFix/issues/2) | Fixed/resolved in this implementation; PR closing link |
| FF-002 | [#3: FF-002: Offline frontend install omitted Rollup native optional dependencies](https://github.com/RjayBernales/FieldFix/issues/3) | Fixed/resolved in this implementation; PR closing link |
| FF-003 | [#4: FF-003: Threaded test client stalled in the restricted runtime](https://github.com/RjayBernales/FieldFix/issues/4) | Fixed/resolved in this implementation; PR closing link |
| FF-004 | [#5: FF-004: Keep credentials out of the tracked environment example](https://github.com/RjayBernales/FieldFix/issues/5) | Owner key rotation remains; no secret in repository |
| FF-005 | [#6: FF-005: Expired proposals and cancelled investigations must terminate cleanly](https://github.com/RjayBernales/FieldFix/issues/6) | Fixed/resolved in this implementation; PR closing link |
| FF-006 | [#7: FF-006: Keep provider telemetry bounded and distinguish failure classes](https://github.com/RjayBernales/FieldFix/issues/7) | Fixed/resolved in this implementation; PR closing link |
| FF-007 | [#8: FF-007: Hosted inference latency invalidated otherwise valid repair proposals](https://github.com/RjayBernales/FieldFix/issues/8) | Fixed/resolved in this implementation; PR closing link |
| FF-008 | [#9: FF-008: Browser polling, resets, and historical provider labels were confusing](https://github.com/RjayBernales/FieldFix/issues/9) | Fixed/resolved in this implementation; PR closing link |
| FF-009 | [#10: FF-009: Automated accessibility audit found low-contrast status labels](https://github.com/RjayBernales/FieldFix/issues/10) | Fixed/resolved in this implementation; PR closing link |
| FF-010 | [#11: FF-010: Cached Vite/esbuild toolchain had published dependency advisories](https://github.com/RjayBernales/FieldFix/issues/11) | Fixed/resolved in this implementation; PR closing link |
| FF-011 | [#12: FF-011: Pinned AnyIO version had two published advisories](https://github.com/RjayBernales/FieldFix/issues/12) | Fixed/resolved in this implementation; PR closing link |
| FF-012 | [#13: FF-012: A public demo needs isolated, bounded visitor sessions](https://github.com/RjayBernales/FieldFix/issues/13) | Fixed/resolved in this implementation; PR closing link |
| FF-013 | [#14: FF-013: Slow session-creation bodies must not hold the global session lock](https://github.com/RjayBernales/FieldFix/issues/14) | Fixed/resolved in this implementation; PR closing link |

Implementation PR: [#15](https://github.com/RjayBernales/FieldFix/pull/15). Its live check/merge status is authoritative. All fixes except the separate credential-rotation action are linked for automatic closure.

| UI / hosting follow-up | Ticket | Disposition |
| --- | --- | --- |
| FF-014 | [#16: Improve dashboard hierarchy and readability](https://github.com/RjayBernales/FieldFix/issues/16) | Redesigned with UI/UX Pro Max and Taste; validated desktop/mobile workflows |
| FF-015 | [#17: Stable free preview](https://github.com/RjayBernales/FieldFix/issues/17) | Temporary replacement restored; durable free host remains pending account connection |

| FF-016 | [#19: Implement the approved LPMAS-inspired dashboard layout](https://github.com/RjayBernales/FieldFix/issues/19) | Implemented; browser, responsive, accessibility and build evidence recorded in dashboard-v2-validation.json |

| FF-017 | [#20: Keep mobile evidence rows and expanded payload accessible](https://github.com/RjayBernales/FieldFix/issues/20) | Fixed row geometry and keyboard scrolling; final expanded-state mobile axe has zero violations |

| FF-018 | [#22: Integrate approved FieldFix branding](https://github.com/RjayBernales/FieldFix/issues/22) | Shared accessible/responsive logo and matching favicon implemented; actual evidence in branding-validation.json |
| FF-019 | [#23: Include static branding in review and verification](https://github.com/RjayBernales/FieldFix/issues/23) | ZIP, fingerprint and scanner now include frontend/public; HTML fingerprint/scanner coverage added |

| FF-020 | [#25: Include verification shell scripts in the submission archive](https://github.com/RjayBernales/FieldFix/issues/25) | Fixed .sh allowlist; extracted package frozen install, 56 tests, build and scan passed |
| FF-021 | [#26: Confirm server mode before inference/session claims](https://github.com/RjayBernales/FieldFix/issues/26) | Unknown/startup-error state now neutral; intercepted session probe and real Meta reconnection verified |

| Judging / navy follow-up | Ticket | Disposition |
| --- | --- | --- |
| FF-022 | [#27: Keep investigation provider labels neutral while health is pending](https://github.com/RjayBernales/FieldFix/issues/27) | Fixed; health-pending label remains neutral and recovers after retry |
| FF-023 | [#28: Expose Simulator controls on its dedicated view](https://github.com/RjayBernales/FieldFix/issues/28) | Fixed; Simulator controls open in the dedicated view while Overview remains collapsed |
| FF-024 | [#29: Place session banner and skip navigation in landmarks](https://github.com/RjayBernales/FieldFix/issues/29) | Fixed; all five page accessibility audits report zero violations |
| FF-025 | [#30: Keep tablet navigation labels and diagnostic rows aligned](https://github.com/RjayBernales/FieldFix/issues/30) | Fixed; tablet/mobile layouts checked without document overflow |
| FF-026 | [#31: Include new static runtime and validation assets in the review ZIP](https://github.com/RjayBernales/FieldFix/issues/31) | Fixed; public assets are included and private configuration/video files excluded |
