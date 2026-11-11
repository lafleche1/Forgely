"""Regressions for repair value, independent of equipment names and rune price."""
import pytest
from forgely_decision import advise
from forgely_equipment_catalog import EquipmentCatalog, equipment_bounds
from forgely_dofocus import reference, RUNE_CHOICES


def rune_stat(rune):
    return next(s for s, runes in RUNE_CHOICES.items() if rune in runes)


def cycloid():
    item = EquipmentCatalog().search('Anneau', 'cycloide')[0]
    natural = {stat: max(bounds) for stat, bounds in equipment_bounds(item).items()}
    jets = dict(natural)
    jets.update({'Vitalité': 294, 'Force': 38, 'Intelligence': 36, 'Agilité': 37,
                 'Dommages Neutre': 3, 'Dommages Terre': 0, 'Dommages Feu': 11,
                 'Dommages Air': 6, 'Initiative': 276, '% Résistance Eau': 0, 'Tacle': 1})
    return jets, natural


@pytest.mark.parametrize('pool', [0, .1, 3, 10, 30, 60])
def test_damaged_cycloid_repairs_heavy_natural_lines_before_light_finishing(pool):
    jets, natural = cycloid()
    proposal = advise(jets, natural, natural, pool, predictive_policy=True)
    if pool==3:
        assert reference(proposal.rune).weight<=pool
        assert proposal.estimates['matrix']['pool_repair_preferred'] is True
        return
    assert rune_stat(proposal.rune) in {
        'Dommages Neutre', 'Dommages Terre', 'Dommages Air', '% Résistance Eau', 'Tacle'}
    ref = reference(proposal.rune)
    stat = rune_stat(proposal.rune)
    assert jets[stat] + ref.gain <= natural[stat]


def test_other_profile_repairs_missing_damage_instead_of_completing_one_vitality_rune():
    jets = {'Vitalité': 195, 'Dommages Terre': 0}
    natural = {'Vitalité': 200, 'Dommages Terre': 10}
    for predictive in (False, True):
        proposal = advise(jets, natural, natural, .1, predictive_policy=predictive)
        assert rune_stat(proposal.rune) == 'Dommages Terre'


def test_light_finishing_is_available_after_heavy_targets_are_restored():
    jets, natural = cycloid()
    jets = dict(natural, **{'Vitalité': 295})
    proposal = advise(jets, natural, natural, .1, predictive_policy=True)
    assert proposal.rune == 'Vi'


def test_large_rune_cannot_cross_a_natural_cap_during_weighted_repair():
    jets = {'Vitalité': 195, 'Dommages Terre': 9}
    natural = {'Vitalité': 200, 'Dommages Terre': 10}
    proposal = advise(jets, natural, natural, .1, predictive_policy=True)
    assert proposal.rune == 'Do Terre'



def test_another_catalogue_item_restores_damage_before_finishing_vitality():
    item = EquipmentCatalog().search('Anneau', 'bolet')[0]
    natural = {stat: max(bounds) for stat, bounds in equipment_bounds(item).items()}
    jets = dict(natural)
    jets['Vitalité'] -= 5
    jets['Dommages'] = 0
    proposal = advise(jets, natural, natural, .1, predictive_policy=True)
    assert rune_stat(proposal.rune) == 'Dommages'
