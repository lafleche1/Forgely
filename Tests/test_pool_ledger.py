from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Application'))
from forgely_pool_ledger import PoolLedger


def test_decimal_and_negative_stat_losses():
    ledger = PoolLedger()
    ledger.observe('0.1', 'item')
    assert ledger.apply({'Initiative': -10}, {'Initiative': -13}, 'Fo', 'EC', 1, 'item', True) is None
    ledger.observe('1.1', 'item')
    assert ledger.apply({'Initiative': -10}, {'Initiative': -13}, 'Fo', 'EC', 2, 'item', True) is None
    assert ledger.origin == 'unknown'


def test_success_and_pa_loss():
    ledger = PoolLedger()
    ledger.observe(5, 'item')
    before = {'Force': 10, 'PA': 1}
    assert ledger.apply(before, {'Force': 11, 'PA': 1}, 'Fo', 'SC', 1, 'item', True) == Decimal(5)
    assert ledger.apply(before, {'Force': 11, 'PA': 0}, 'Fo', 'SN', 2, 'item', True) == Decimal(104)


def test_unknown_and_context_changes():
    ledger = PoolLedger()
    assert ledger.apply({'PA': 1}, {'PA': 0}, 'Fo', 'EC', 1, 'a', True) is None
    ledger.observe(10, 'a')
    assert ledger.apply({'PA': 1}, {'PA': 0}, 'Fo', 'EC', 1, 'b', True) is None
    assert ledger.origin == 'unknown'
    ledger.observe(10, 'b')
    ledger.reset('b')
    assert ledger.value is None


def test_duplicate_not_applied_twice():
    ledger = PoolLedger()
    ledger.observe(10, 'a')
    args = ({'PA': 1}, {'PA': 0}, 'Fo', 'EC', 'one', 'a', True)
    assert ledger.apply(*args) == Decimal(109)
    assert ledger.apply(*args) == Decimal(109)
    assert ledger.apply({'PA': 1}, {'PA': -1}, 'Fo', 'EC', 'one', 'a', True) is None


def test_aliases_and_loss_on_successful_target():
    ledger = PoolLedger()
    ledger.observe('2.25', 'item')
    assert ledger.apply({'Points d\'action (PA)': 1, 'Force': -2},
                        {'PA': 1, 'Force': -4}, 'Fo', 'SN', 1, 'item', True) is None


def test_invalid_direct_readings():
    for value in (None, True, -1, 'NaN', 'Infinity'):
        ledger = PoolLedger()
        ledger.observe(10, 'a')
        assert ledger.observe(value, 'a') is None
        assert ledger.origin == 'unknown'


def test_invalid_evidence_drops_baseline():
    cases = [
        ({'Force': 1}, {'Force': 2}, 'Fo', 'SC', False),
        ({'Force': 1}, {'Force': 2, 'PA': 1}, 'Fo', 'SC', True),
        ({'Force': 1}, {'Force': 2}, 'Fo', 'EC', True),
        ({'Force': 1}, {'Force': 3}, 'Fo', 'SC', True),
        ({'Force': 1, 'PA': 1}, {'Force': 2, 'PA': 2}, 'Fo', 'SN', True),
        ({'Force': 1, 'PA': 1}, {'Force': 2, 'PA': 0}, 'Fo', 'SC', True),
        ({'Mystery': 1}, {'Mystery': 0}, 'Fo', 'EC', True),
        ({'Force': 1}, {'Force': 1}, 'unknown', 'EC', True),
    ]
    for before, after, rune, outcome, complete in cases:
        ledger = PoolLedger()
        ledger.observe(10, 'a')
        assert ledger.apply(before, after, rune, outcome, 1, 'a', complete) is None
        assert ledger.origin == 'unknown'
        assert ledger.reason
