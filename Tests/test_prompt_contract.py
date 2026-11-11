from forgely_decision import advise
from forgely_predictive import rank_options
from forgely_dofocus import reference
from forgely_pricing import PriceBook


def test_legacy_prices_cannot_change_target_advice():
    args = ({'Force': 39, 'Intelligence': 39}, {'Force': 40, 'Intelligence': 40},
            {'Force': 40, 'Intelligence': 40}, 0)
    baseline = advise(*args, predictive_policy=True)
    book = PriceBook({'Fo': 100000, 'Ine': 1}, server='test', observed_on='2026-11-08')
    actual = advise(*args, predictive_policy=True, price_book=book)
    assert actual.rune == baseline.rune
    assert 'pricing' not in actual.estimates


def test_complete_target_rollouts_take_priority_over_nominal_pool_repairs():
    def row(rune, score, success):
        return (score, rune, 'Force', 'fm_classique', reference(rune),
                {'prediction': {'SC': success, 'SN': 0, 'EC': 100-success},
                 'decision_trace': {'sequence_used': True}}, None, 1, 10, 40)
    # Ra wins the full-target rollouts; Fo wins both phase and next-rune odds.
    options = [row('Ra Fo', .8, 30), row('Fo', .2, 90)]
    ranked, meta = rank_options(options, {'Force': 10}, {'Force': 40}, 2)
    assert ranked[0][1] == 'Ra Fo'
    assert len(ranked) == 2
    assert meta['sequence_preserved'] is True


def test_no_candidate_is_blocked_not_success():
    result = advise({'Unknown': 0}, {'Unknown': 1}, {'Unknown': 2}, 0)
    assert result.rune is None
    assert result.kind != 'atteint'


def test_contract_is_visible_in_copilot_rules_and_old_mode_migrates():
    from forgely_expert import rules_text
    from forgely_rules import MODES, objective_mode
    assert MODES == ('Chances maximales',)
    assert objective_mode('Budget optimis\u00e9') == MODES[0]
    text = rules_text()
    assert 'Contrat de conseil Forgely' in text
    assert 'facteur deux' in text
    assert 'prix unitaire)' not in text
