"""Keep pre-fusion evidence before the result's new jet reaches the UI."""
from copy import deepcopy
from time import monotonic
from forgely_context import normalize_snapshot, snapshot_diff
from forgely_detection import history_signature, new_row_shift


def complete_learning_profile(item):
    """Only documented or bundled profiles prove all natural lines are present.

    Imported CSV bounds may be partial and cannot authorize training.
    """
    from forgely_dofocus import natural_profile,canonical_stat
    from forgely_equipment_catalog import bundled_bounds
    profile=natural_profile(item)
    if profile:return {canonical_stat(s):v for s,v in profile.items()}
    bounds=bundled_bounds(item)
    return {canonical_stat(s):v[1] for s,v in bounds.items()} if bounds else None


class FusionContextTracker:
    def __init__(self):
        self.reset()

    def reset(self):
        self.context = None
        self.history = None
        self.before = None
        self.frozen = None
        self.frozen_history = None
        self.frozen_at = 0
        self.pending_event = None
        self.pending_frame_id = None
        self.pending_history = None
        self.candidate = None
        self.streak = 0

    def observe(self, context, history, jet, pool, event, *, event_frame_id=None):
        snapshot = normalize_snapshot(jet, pool)
        signature = history_signature(history)
        if not context or snapshot is None or not signature:
            self.reset()
            return None
        if context != self.context:
            self.reset()
            self.context = context
        if self.frozen is not None and monotonic()-self.frozen_at > 8:
            self.reset()
            self.context = context
        if self.pending_event is not None and signature != self.pending_history:
            # Another history update before the post-state was stable makes
            # single-rune attribution impossible; start a fresh baseline.
            self.reset()
            self.context = context
        if self.history is not None and self.frozen is None and (
                signature != self.history or snapshot != self.before):
            self.frozen = deepcopy(self.before)
            self.frozen_history = self.history
            self.frozen_at = monotonic()
        candidate = (signature, tuple(snapshot['jet'].items()), snapshot['pool'])
        self.streak = self.streak+1 if candidate == self.candidate else 1
        self.candidate = candidate
        transition = None
        if event is not None and event.rune and new_row_shift(self.frozen_history or (), signature) == 1:
            self.pending_event = event
            self.pending_frame_id = event_frame_id
            self.pending_history = signature
        if self.pending_event is not None and self.streak >= 2:
            delta = snapshot_diff(self.frozen, snapshot)
            if delta is not None:
                changed = bool(delta['changes'] or delta['pool_delta'])
                if changed or self.pending_event.outcome in ('SN','EC'):
                    transition = {'before': deepcopy(self.frozen), 'after': snapshot,
                                  'rune': self.pending_event.rune, 'outcome': self.pending_event.outcome}
                    if self.pending_frame_id is not None:transition['event_frame_id']=self.pending_frame_id
                    self.pending_event = None
                    self.pending_frame_id = None
                    self.pending_history = None
            else:
                self.reset()
                self.context = context
        # An early jet change must not replace the pre-state while its history
        # still shows the old result. Keep it only for the bounded interval.
        early_jet = self.frozen is not None and signature == self.history
        if self.streak >= 2 and self.pending_event is None and not early_jet:
            self.history = signature
            self.before = snapshot
            self.frozen = None
            self.frozen_history = None
        return transition
