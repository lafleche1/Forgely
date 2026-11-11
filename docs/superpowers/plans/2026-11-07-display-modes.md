# Automatic display modes implementation plan

Goal: follow the physical DOFUS client surface in windowed and fullscreen modes without manual selection or OCR of window decorations.

Architecture: query client corners in screen pixels each scan; retain outer bounds only for PrintWindow, then crop its result. Scope per-monitor DPI awareness to the capture thread. A frame size change invalidates queued OCR before publication. Preserve conservative workshop validation and account locking.

Constraints: Windows, Python, Pillow, existing MSS capture; no game input, no new dependency. Arbitrarily rearranged game panels remain outside the fixed-layout reader's capabilities.

Alternatives: whole-window capture retains the title-bar offset; desktop-only capture includes overlays; client-area capture supports both existing backends and is selected.

Tasks:
- [ ] Add regression tests for decorated and borderless windows, negative monitor coordinates, native cropping, geometry failures and mode transitions.
- [ ] Observe failures, implement physical client geometry and scoped DPI context; route main capture and account probes through the same crop.
- [ ] Invalidate old OCR when captured dimensions change; verify existing mailbox behavior.
- [ ] Run focused tests, full suite and compilation; document any environment limitations and publish changes to a dedicated branch.

Review focus: resize during capture must fail closed; GPU-native capture can remain unavailable; multiple accounts must retain selection; no fixed title-bar offsets; changing display mode must never count as a rune.
