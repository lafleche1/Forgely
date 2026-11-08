"""Exact pool bookkeeping from one complete, verified rune transition.

The caller owns snapshot completeness and must reset after any observation gap.
An unread initial pool is unknown, even when a transition releases weight.
"""
from decimal import Decimal, InvalidOperation

from forgely_dofocus import canonical_stat, reference, RUNE_CHOICES, WEIGHT_PER_POINT


def _decimal(value):
    if isinstance(value, bool):
        raise ValueError('Boolean is not a measurement')
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError('Finite measurement required')
    return result


def _jet(values):
    if not isinstance(values, dict) or not values:
        raise ValueError('Complete characteristics required')
    result = {}
    for name, value in values.items():
        stat = canonical_stat(name)
        if stat in result or stat not in WEIGHT_PER_POINT:
            raise ValueError('Unknown or duplicated characteristic')
        result[stat] = _decimal(value)
    return result


class PoolLedger:
    def __init__(self):
        self.reset()

    @property
    def value(self):
        return self._value

    def reset(self, context=None):
        self._context = context
        self._value = None
        self.origin = 'unknown'
        self.reason = 'Pool baseline unknown; a direct reading is required'
        self._seen = {}

    def _contextualise(self, context):
        if context != self._context:
            self.reset(context)

    def _invalidate(self, reason):
        self._value = None
        self.origin = 'unknown'
        self.reason = reason
        return None

    def observe(self, value, context):
        self._contextualise(context)
        try:
            measured = _decimal(value)
            if measured < 0:
                raise ValueError('Negative pool')
        except (InvalidOperation, ValueError, TypeError):
            return self._invalidate('Invalid direct pool reading')
        self._value = measured
        self.origin = 'read'
        self.reason = 'Direct pool reading'
        return self.value

    def apply(self, before, after, rune, outcome, transition_id, context, complete):
        self._contextualise(context)
        try:
            if complete is not True or outcome not in ('SC', 'SN', 'EC'):
                raise ValueError('Incomplete or unknown transition')
            if transition_id is None:
                raise ValueError('Transition identifier required')
            hash(transition_id)
            old, new = _jet(before), _jet(after)
            if old.keys() != new.keys():
                raise ValueError('Characteristic sets differ')
            ref = reference(rune)
            if ref.weight is None or ref.gain is None:
                raise ValueError('Unknown rune')
            target = next((stat for stat, runes in RUNE_CHOICES.items() if rune in runes), None)
            gain, weight = _decimal(ref.gain), _decimal(ref.weight)
            changes = {stat: new[stat] - old[stat] for stat in old}
            fingerprint = (tuple(sorted(old.items())), tuple(sorted(new.items())), rune, outcome)
            if transition_id in self._seen:
                if self._seen[transition_id] != fingerprint:
                    raise ValueError('Conflicting duplicate transition')
                return self.value
            self._seen[transition_id] = fingerprint
            lost = Decimal(0)
            for stat, delta in changes.items():
                expected = gain if stat == target and outcome != 'EC' else Decimal(0)
                if delta > expected:
                    raise ValueError('Unexpected gain or multiple runes')
                loss = expected - delta
                if outcome == 'SC' and loss:
                    raise ValueError('Critical success contradicts characteristic loss')
                lost += loss * _decimal(WEIGHT_PER_POINT[stat])
            if outcome == 'SC' and target not in changes:
                raise ValueError('Successful rune characteristic missing')
            if outcome == 'SN' and target not in changes:
                raise ValueError('Successful rune characteristic missing')
        except (InvalidOperation, ValueError, TypeError, StopIteration):
            return self._invalidate('Incomplete, contradictory, or ambiguous rune evidence')
        if self.value is None:
            return self._invalidate('Pool baseline unknown; transition cannot establish it')
        if outcome != 'SC':
            self._value = max(Decimal(0), self.value + lost - weight)
        self.origin = 'calculated'
        self.reason = 'Calculated from a complete single-rune transition'
        return self.value
