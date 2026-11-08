# Predictive matrix implementation plan

> **For agentic workers:** Use executing-plans for the integrated engine/UI and an isolated pure ledger implementation. Track completed steps below.

**Goal:** Apply the user's pool strategy and present matrix state, prediction and optimal/risky alternatives.
**Architecture:** Versioned heuristic policy consumes legal candidate runes and observed values. A separate Decimal ledger calculates pool transitions only from a known baseline and complete single-rune observations. The current OCR, identity and freshness safeguards remain in force.
**Tech stack:** Python, Decimal, existing decision engine and Tk widgets.
**Spec:** User request dated 2026-11-08 in this conversation.

## Global constraints
- Requested success bands are labelled user-supplied theoretical estimates, not measured game rates.
- No guarantee of no losses, no guaranteed creation of pool, and no fabricated hidden baseline.
- SC preserves pool; SN/EC accounting requires observed losses and confirmed rune/outcome.
- No automatic game action. No rune price/rentability in kamas without actual prices.

## Review focus
- Fractional pool 0.9 remains low pool rather than zero or an unhandled gap.
- Pool boundaries 0/20/51 and absent appropriate legal runes have explicit behavior.
- Unread natural characteristics do not become zero or define saturation.
- Hidden pool becomes unknown after skipped/multiple/conflicting transitions.
- Every displayed option comes from legal candidates and keeps stale-reading advice blocked.

## Tasks
- [x] Add failing policy tests for bands, phases, heavy/light filtering, alternative selection and structured output.
- [x] Implement `forgely_predictive.py`; activate policy in live app paths through an explicit engine flag.
- [x] Implement Decimal pool ledger with deduplication/context/complete-evidence tests in separate files.
- [x] Connect pool ledger to observed frame/event lifecycle; read pool has precedence and calculated pool remains labelled.
- [x] Present the three required sections in details and a compact version in the floating panel.
- [x] Run targeted tests, review, full suite, and document the policy and limits.
