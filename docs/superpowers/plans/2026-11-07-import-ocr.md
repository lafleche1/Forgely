# Forgely import and OCR correction plan

**Goal:** Import v21.02 into the existing private repository, restore a reliable test baseline, and remove avoidable OCR confirmation delays.
**Architecture:** Keep the Windows/Python/Tkinter application and conservative two-reading trackers. Fix capture scheduling and cache repeated failed OCR; preserve existing assets and repository history.
**Authorization:** User requested automatic execution of all necessary technical steps and import into `lafleche1/Forgely`.

## Constraints
- No secrets, private logs, local databases, temporary captures or generated caches in Git.
- No guessed negative reliquat or invented rune result.
- Existing GitHub files and commits must be preserved.
- Subsecond latency requires subsequent measurement in DOFUS on Windows; synthetic tests cannot certify it.

## Tasks
- [ ] Import sanitized source and bundled catalogue/assets; preserve existing GitHub base tree.
- [x] Fix official suffix matching falsely promoting full unregistered names; test complete, truncated and ambiguous names.
- [x] Fix UI NameError when no icon reference or known name exists; preserve anonymous item state.
- [x] Cache failed first-row OCR for identical pixels, bounded in size and time; changed pixels retry immediately.
- [x] Publish short confirmation captures after a visual change, without continuous idle OCR; test rapid changes, refresh, and invalidation.
- [x] Update obsolete tests for explicit row geometry, official rune asset, negative reliquat and two-variant OCR.
- [x] Configure reproducible pytest discovery/dependencies in CI; run all tests and compile all Python files.
- [x] Run provisional history/rune preview in its own worker, independently of effects and pool; never persist preview results or use them for advice.
- [ ] Document evidence and remaining Windows validation, upload commit and verify remote tree.

## Review focus
Identical repeated runes must not be deduplicated by value. A current item must not be inferred from a stale history block. Missing or negative reliquat remains unknown. No OCR cache survives changed pixels. Capture failures invalidate scheduling state.

## Progress
Baseline: 12 failing tests, 274 passed, 6 skipped, 16 passing subtests. Test dependencies installed in workspace-only ../deps because user-site installation does not persist between commands.
Ruling: Execute directly under the user's existing authorization; no repeated design/permission handoff.
Final local verification: 297 passed, 6 skipped, 19 passing subtests with Pillow 11.3.0; 129 Python files compiled. Review findings concerning stale context, UI ordering and stopped/restarted sessions addressed with regression tests. Remaining unchecked steps concern remote import and verification.
