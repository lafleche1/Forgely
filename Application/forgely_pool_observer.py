"""Conservative capture adapter for exact pool bookkeeping; no persistence."""
from copy import deepcopy

from forgely_detection import history_signature, new_row_shift
from forgely_dofocus import reference
from forgely_pool_ledger import PoolLedger, _jet


class PoolObserver:
    def __init__(self):
        self.reset()

    def reset(self):
        self.context = None
        self.ledger = PoolLedger()
        self.stable = None
        self.frozen = None
        self.pending_event = None
        self.pending_history = None
        self.candidate = None
        self.candidate_pool = None
        self.read_value = None
        self.read_streak = 0
        self.candidate_readings = set()
        self.streak = 0
        self.last_frame = None
        self.last_result = None

    def _result(self, measured=None, pending=False, reason=None, usable=False):
        if measured is not None:
            result = dict(value=format(measured.normalize(),'f'), origin='read', pending=pending,
                          reason='Direct pool reading')
        elif usable and self.ledger.value is not None:
            result = dict(value=format(self.ledger.value.normalize(),'f'), origin='calculated', pending=pending,
                          reason=self.ledger.reason)
        else:
            result = dict(value=None, origin='unknown', pending=pending,
                          reason=reason or self.ledger.reason)
        self.last_result = result
        return dict(result)

    def observe(self, context, history, jet, visible_pool, event, complete, frame_id):
        if context != self.context:
            self.reset()
            self.context = deepcopy(context)
        if frame_id == self.last_frame and self.last_result is not None:
            return dict(self.last_result)
        if self.last_frame is not None and (not isinstance(frame_id, int) or frame_id != self.last_frame + 1):
            self.reset()
            self.context = deepcopy(context)
        self.last_frame = frame_id
        reading = PoolLedger()
        measured = reading.observe(visible_pool, context) if visible_pool is not None else None
        signature = history_signature(history or '')
        try:
            snapshot = _jet(jet)
        except (ValueError, TypeError, ArithmeticError):
            snapshot = None
        if complete is not True or not signature or snapshot is None:
            self.reset()
            self.context = deepcopy(context)
            self.last_frame = frame_id
            return self._result(measured, reason='Unread or incomplete frame breaks pool continuity')
        candidate = (signature, tuple(sorted(snapshot.items())))
        if candidate == self.candidate:
            self.streak += 1
        else:
            self.candidate = candidate
            self.candidate_pool = None
            self.read_value = None
            self.read_streak = 0
            self.candidate_readings = set()
            self.streak = 1
        if measured is not None:
            self.candidate_readings.add(measured)
            if measured == self.read_value:
                self.read_streak += 1
            else:
                self.read_value = measured
                self.read_streak = 1
                self.candidate_pool = None
            if self.read_streak >= 3:
                self.candidate_pool = measured
            if (self.frozen is None and self.stable is not None
                    and candidate == self.stable[:2] and self.ledger.value is not None
                    and measured != self.ledger.value):
                self.ledger.reset(context)
                self.stable = (signature, candidate[1], None)
        else:
            self.read_value = None
            self.read_streak = 0
        if self.stable is not None and self.frozen is None and candidate != self.stable[:2]:
            self.frozen = deepcopy(self.stable)
        if self.frozen is not None:
            old_history, old_jet, old_pool = self.frozen
            shift = new_row_shift(old_history, signature)
            ambiguous = (signature != old_history and shift != 1)
            ambiguous |= self.pending_history is not None and signature != self.pending_history
            if ambiguous:
                self.ledger.reset(context)
                self.stable = self.frozen = None
                self.pending_event = self.pending_history = None
            else:
                if event is not None and shift == 1:
                    rune, outcome = getattr(event, 'rune', None), getattr(event, 'outcome', None)
                    if reference(rune).weight is not None and outcome in ('SC', 'SN', 'EC'):
                        proposed = (rune, outcome)
                        if self.pending_event is not None and proposed != self.pending_event:
                            self.ledger.reset(context)
                            self.stable = self.frozen = None
                            self.pending_event = self.pending_history = None
                        else:
                            self.pending_event = proposed
                            self.pending_history = signature
                if self.frozen is not None and self.pending_event is not None and self.streak >= 3:
                    self.ledger.reset(context)
                    if old_pool is not None:
                        self.ledger.observe(old_pool, context)
                    rune, outcome = self.pending_event
                    self.ledger.apply(dict(old_jet), snapshot, rune, outcome,
                                      (self.pending_history, frame_id), context, True)
                    self.frozen = None
                    self.pending_event = self.pending_history = None
                    if (self.ledger.value is not None
                            and any(value != self.ledger.value for value in self.candidate_readings)):
                        self.ledger.reset(context)
                    if self.candidate_pool is not None:
                        self.ledger.observe(self.candidate_pool, context)
                    self.stable = (signature, candidate[1], self.ledger.value)
                    return self._result(measured, usable=True)
                if self.frozen is not None and self.pending_event is None and self.streak >= 6:
                    # A stable visual change without a verified outcome cannot
                    # be attributed forever: stop requesting more captures.
                    self.ledger.reset(context)
                    self.stable = self.frozen = None
                    self.pending_event = self.pending_history = None
        if self.frozen is None and self.streak >= 3:
            if self.candidate_pool is not None:
                self.ledger.observe(self.candidate_pool, context)
            self.stable = (signature, candidate[1], self.ledger.value)
        usable = self.frozen is None and self.stable is not None and candidate == self.stable[:2]
        return self._result(measured, pending=self.frozen is not None,
                            reason='Waiting for three complete stable frames and one identified rune',
                            usable=usable)
