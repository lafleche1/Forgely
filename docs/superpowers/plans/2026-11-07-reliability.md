# Forgely reliability implementation plan

Goal: correct the eight concrete audit findings without fabricating game data.

Architecture: retain the existing capture/preview/observer pipeline. Normalize a verified workshop layout before masking; detect small changes within semantic regions. Close SQLite transactions and connections deterministically. Restore missing reference text files from the project's GitHub repository and rebuild the indexed store. Contextual learning may influence ranking only with sufficient comparable local evidence and never bypass constraints.

1. Add regression tests for small text changes, uniform purple screens, translated/scaled workshop normalization, missing profiles, contextual ranking and Windows database handle release. Run before implementation.
2. Restore the missing tracked reference files from lafleche1/Forgely, validate their schema, and rebuild Application/assets/dofocus/reference.sqlite3. Do not invent percentages or catalogue rows.
3. Fix native-resolution region change detection while ignoring isolated noise and unrelated pixels. Test history/effects/rune changes and map/chat noise.
4. Require independent structural evidence for visual workshop verification. Reacquire the supported workshop frame from panel geometry on each changed layout, normalize it before all readers, and fail closed for ambiguous/unrecognized layouts.
5. Reject item-specific advice when the natural profile is missing or constraints remain unverifiable; preserve existing generic exploratory engine APIs.
6. Add a transaction context manager that explicitly closes SQLite handles; replace transaction-only context managers across application code. Verify persistence, rollback and immediate Windows file removal.
7. Feed sufficient comparable contextual measurements into candidate scores, with bounded influence and visible provenance; reject malformed or insufficient samples. Keep raw aggregate rates out of ranking.
8. Run focused tests then the complete available suite. Report unrelated missing assets and any remaining failures explicitly. Do not publish unverified changes.
