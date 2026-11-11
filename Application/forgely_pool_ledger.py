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


CORE_MALUS = frozenset(('Force', 'Intelligence', 'Chance', 'Agilité'))


def attempted_charge(target, current, gain, weight):
    if current < 0:
        if target not in CORE_MALUS:
            return None
        if current + gain < 0:
            return weight / 2
    return weight


def signed_transfer(old, new, target, gain, weight, outcome):
    """Observed core-stat accounting, not a prediction of loss selection.

    Partial target gains and unverified negative densities require direct OCR.
    See docs/ANALYSE_SESSIONS_TETRISTE_193444_193651.md.
    """
    if target not in old:
        raise ValueError('Target absent')
    if outcome == 'SC':
        if any(new[s]-v != (gain if s == target else 0) for s,v in old.items()):
            raise ValueError('Ambiguous critical gain')
        return weight, Decimal(0)
    delta = new[target]-old[target]
    if delta != (gain if outcome == 'SN' else 0):
        raise ValueError('Ambiguous target gain or loss')
    charge = attempted_charge(target,old[target],gain,weight)
    if charge is None:
        raise ValueError('Unverified negative rune density')
    lost = Decimal(0)
    for stat, start in old.items():
        end = new[stat]
        if stat == target:
            continue
        if end > start:
            raise ValueError('Unexpected collateral gain')
        if end == start:
            continue
        if end < 0 and stat not in CORE_MALUS:
            raise ValueError('Unverified negative loss density')
        positive = max(Decimal(0),start)-max(Decimal(0),end)
        negative = min(Decimal(0),start)-min(Decimal(0),end)
        lost += (positive + negative/2)*_decimal(WEIGHT_PER_POINT[stat])
    return charge, lost


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
            signed = any(v<0 for v in (*old.values(),*new.values()))
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
            if signed:
                weight, lost = signed_transfer(old,new,target,gain,weight,outcome)
            for stat, delta in ([] if signed else changes.items()):
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
