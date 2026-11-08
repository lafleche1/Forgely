"""Stable, *unattributed* OCR readings from the active DOFUS workshop.

Equipment identity is deliberately NOT part of this tracker. It may stabilize
jet and reliquat before the first rune reveals the item name. A confirmed item
is still required before advice, statistics or item-specific persistence.
"""
from __future__ import annotations


class WorkshopReadings:
    def __init__(self, required_frames=3):
        if required_frames < 2:
            raise ValueError('At least two consistent frames are required')
        self.required_frames = required_frames
        self.reset()

    def reset(self):
        self.context = None
        self.expected = set()
        self.values = {}
        self.fresh = set()
        self.visible = set()
        self.atomic_snapshot = False
        self._page_pool = None
        self._sequence = None
        self.sample = None
        self.streak = 0
        self.jet = None
        self.pool = None
        self.jet_sample = None
        self.jet_streak = 0
        self.partial_jet = None
        self.pool_sample = None
        self.pool_streak = 0
        self.partial_pool = None
        self.last_jet = {}

    def configure(self, context, expected):
        """Bind pages to a verified object. A goal is NOT a complete profile."""
        from forgely_dofocus import canonical_stat
        required = {canonical_stat(k) for k in (expected or ())}
        if (context, required) != (self.context, self.expected):
            self.reset()
            self.context, self.expected = context, required

    def invalidate(self):
        """Keep old numbers for display, never as current evidence after a rune."""
        self.fresh.clear()
        self.jet = self.pool = None
        self.sample = self.jet_sample = self.pool_sample = None
        self.streak = self.jet_streak = self.pool_streak = 0
        self.partial_jet = self.partial_pool = None
        self.atomic_snapshot = False
        self._page_pool = None

    @property
    def display_jet(self):
        """Last stable values for display only; snapshot() is still mandatory."""
        return dict(self.partial_jet or self.jet or self.last_jet)

    @property
    def line_states(self):
        if self.context is None:
            # Numeric stability is independent of the equipment identity.
            # This display status does not authorize item-specific advice.
            keys=self.last_jet.keys() | dict(self.jet_sample or ()).keys()
            return {k: ('confirmed' if k in (self.partial_jet or {}) else
                        'stale' if k in self.last_jet else 'unconfirmed') for k in keys}
        return {k: ('unread' if k not in self.values else
                    'stale' if k not in self.fresh else
                    'confirmed' if k in self.visible else 'offscreen')
                for k in self.expected | self.values.keys()}

    def observe(self, jet, pool, *, sequence=None):
        if sequence is not None:
            if self._sequence is not None and sequence <= self._sequence:
                return False
            self._sequence = sequence
        if self.context is None:
            self.atomic_snapshot = True
            return self._observe_single(jet, pool)
        from forgely_dofocus import normalise_jet
        jet = normalise_jet(jet) or {}
        self.visible = set(jet)
        changed = any(k in self.fresh and self.values[k] != v for k, v in jet.items())
        if changed or (pool is not None and self._page_pool is not None and pool != self._page_pool):
            self.invalidate()
        stable = self._observe_single(jet, pool)
        if stable:
            self.values.update(jet)
            self.fresh.update(jet)
            self._page_pool = pool
        complete = bool(stable and self.expected and
                        (self.expected | self.values.keys()) <= self.fresh)
        self.atomic_snapshot = bool(complete and self.values.keys() <= jet.keys())
        self.jet = dict(self.values) if complete else None
        self.pool = pool if complete else None
        return complete

    def _observe_single(self, jet, pool):
        """Return True only after consecutive identical valid jet/pool readings.

        An empty jet or missing pool invalidates the provisional snapshot. Zero
        pool is valid. Never reuse a stale snapshot after a changed OCR reading.
        """
        # Independently stabilize observed values for diagnostics. These are
        # NEVER treated as an atomic before/after snapshot or used for advice.
        jet_key = tuple(sorted(jet.items())) if jet else None
        if jet_key is None:
            self.jet_sample = None; self.jet_streak = 0; self.partial_jet = None
        elif jet_key == self.jet_sample:
            self.jet_streak += 1
        else:
            self.jet_sample = jet_key; self.jet_streak = 1; self.partial_jet = None
        if self.jet_streak >= self.required_frames:
            self.partial_jet = dict(jet)
            self.last_jet = dict(jet)
        if pool is None:
            self.pool_sample = None; self.pool_streak = 0; self.partial_pool = None
        elif pool == self.pool_sample:
            self.pool_streak += 1
        else:
            self.pool_sample = pool; self.pool_streak = 1; self.partial_pool = None
        if pool is not None and self.pool_streak >= self.required_frames:
            self.partial_pool = pool
        if not jet or pool is None:
            self.sample = None; self.streak = 0; self.jet = None; self.pool = None
            return False
        sample = (tuple(sorted(jet.items())), pool)
        if sample == self.sample:
            self.streak += 1
        else:
            self.sample = sample
            self.streak = 1
            self.jet = None
            self.pool = None
        if self.streak >= self.required_frames:
            self.jet = dict(jet)
            self.pool = pool
            return True
        return False

    def snapshot(self):
        """Return an isolated copy of the stable reading, or None."""
        if self.jet is None or self.pool is None:
            return None
        return dict(self.jet), self.pool
