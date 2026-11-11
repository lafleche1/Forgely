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
        self._line_samples = {}
        self._line_counts = {}

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
        self._line_samples.clear()
        self._line_counts.clear()

    @property
    def display_jet(self):
        """Last stable values for display only; snapshot() is still mandatory."""
        return {**self.last_jet, **(self.jet or {}), **(self.partial_jet or {})}

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
            # Expire hidden rows after any change, but do not restart the
            # independent confirmations of unchanged, currently visible rows.
            samples={k:v for k,v in self._line_samples.items() if jet.get(k)==v}
            counts={k:self._line_counts[k] for k in samples}
            old_pool=(self.pool_sample,self.pool_streak)
            self.invalidate()
            self._line_samples=samples;self._line_counts=counts
            if pool is not None and pool==old_pool[0]:
                self.pool_sample,self.pool_streak=old_pool
        stable = self._observe_single(jet, pool)
        if self.partial_jet:
            self.values.update(self.partial_jet)
            self.fresh.update(self.partial_jet)
        if self.partial_pool is not None:
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
        # One confirmation counter per visible line. A changed or missing
        # field cannot reset unrelated values, nor acquire a guessed value.
        jet_key = tuple(sorted(jet.items())) if jet else None
        self._line_counts={k:(self._line_counts.get(k,0)+1
            if k in self._line_samples and self._line_samples[k]==v else 1)
            for k,v in (jet or {}).items()}
        self._line_samples=dict(jet or {})
        self.jet_sample=jet_key
        self.jet_streak=min(self._line_counts.values(),default=0)
        self.partial_jet={k:v for k,v in (jet or {}).items()
            if self._line_counts[k]>=self.required_frames} or None
        if self.partial_jet:self.last_jet.update(self.partial_jet)
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
        self.sample = sample
        self.streak = min(self.jet_streak,self.pool_streak)
        self.jet = self.pool = None
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

    @property
    def waiting_reason(self):
        """Explain the actual missing measurement without asking to reread all."""
        if self.snapshot() is not None:return None
        if self.context is None:
            missing=set(self.last_jet)-set(self.partial_jet or {})
        else:
            missing=(self.expected | self.values.keys())-self.fresh
        parts=[]
        if missing:
            names=sorted(missing)
            parts.append('À lire ou confirmer : '+', '.join(names[:3])+('…' if len(names)>3 else ''))
        if self.partial_pool is None:parts.append('Reliquat à confirmer')
        return ' · '.join(parts) or 'Confirmation du jet en cours'
