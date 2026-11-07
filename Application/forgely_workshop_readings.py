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

    def observe(self, jet, pool):
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
