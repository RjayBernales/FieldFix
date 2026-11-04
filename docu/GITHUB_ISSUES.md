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
