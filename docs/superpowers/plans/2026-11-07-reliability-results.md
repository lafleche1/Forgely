# Reliability corrections — 2026-11-07

Implemented the audited capture, advice, reference, connection-lifetime and learning corrections.

- Native RGB change detection preserves small text and same-luminance icon colour changes; unrelated map/chat pixels remain excluded.
- Visual workshop validation requires independent panel contrast, header text and green characteristic glyphs. Uniform purple no longer qualifies.
- The workshop locator reacquires coherent translated/scaled layouts, normalizes coordinates, rejects ambiguity, and expires invalid transforms. Synthetic tests cover translation, scaling and closure; arbitrary independent rearrangement of panels is deliberately not inferred.
- Missing text references restored from lafleche1/Forgely. Missing icons, OCR fixture and supporting assets restored from the existing Downloads/Forgely-main/Forgely-main source copy, without replacing existing code. Indexed Dofocus store rebuilt: 10 items, 17 documented states. No percentages invented.
- Named-item advice requires a complete natural profile and all its observed characteristics. Unknown constraints cannot silently authorize a rune.
- SQLite transaction helpers explicitly commit/rollback and close connections, including Windows file handles. Server contexts close their connections too; tests that created their own unclosed SQLite handles were corrected.
- Contextual observations can affect candidate ranking after at least 30 comparable records. Groups require identical measured jets and exact pool values. Influence is bounded and labelled exploratory; aggregate rune totals never rank candidates.
- Worker-side learning retains the pre-fusion state before UI updates, waits for stable post-state after accepted events, preserves confirmed unchanged failures, and excludes multi-row updates that cannot be attributed to one rune.
- Launcher scripts support both root and application virtual environments. Both build scripts bundle catalogues and reference files and rebuild the indexed store.

Independent review found incomplete observed-jet authorization and delayed post-state training loss; both were corrected with regression coverage. Additional regression checks cover early stat updates, multiple-row history jumps and same-luminance rune changes.

Validation: full pytest suite 458 passed, 15 skipped, 0 failed (26.10 s). Application compilation passed. Real Tk GUI construction, event processing and shutdown passed using isolated test data. Real Tesseract was available for OCR fixture tests.

Validation environment: Python 3.13.17; Pillow 11.3.0; pytest 8.3.5 from its upstream source; dependencies recovered locally/offline. Test-only data and tooling live under .test-tmp. A live DOFUS session and a newly built executable were not exercised; no installer or remote publication is claimed.
