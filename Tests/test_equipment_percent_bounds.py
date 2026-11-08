from extract_equipment_assets import effect_bounds
from forgely_equipment_catalog import EquipmentCatalog,equipment_bounds


def test_percent_resistance_is_a_natural_line_even_in_percent_category():
    effect={'characteristic':35,'category':1,'useDice':1,'characteristicOperator':'+'}
    assert effect_bounds(effect,{'diceNum':6,'diceSide':8})==('% Résistance Eau',6,8)


def test_non_resistance_percent_effect_is_not_inferred_as_a_flat_bonus():
    effect={'characteristic':10,'category':1,'useDice':1,'characteristicOperator':'+'}
    assert effect_bounds(effect,{'diceNum':6,'diceSide':8}) is None


def test_negative_natural_bounds_preserve_signs():
    effect={'characteristic':10,'category':0,'useDice':1,'characteristicOperator':'-'}
    assert effect_bounds(effect,{'diceNum':6,'diceSide':8})==('Force',-8,-6)


def test_cycloid_profile_contains_the_percent_resistance_seen_in_game():
    assert equipment_bounds(EquipmentCatalog().get(14092))['% Résistance Eau']==(6,8)
