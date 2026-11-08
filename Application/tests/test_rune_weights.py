import pytest
from forgely_dofocus import reference, RUNE_CHOICES, WEIGHT_PER_POINT
from forgely_probabilites import reference as legacy_reference
import forgely_weights as weights


@pytest.mark.parametrize('rune,gain,weight', [
    ('Vi',5,1), ('Pa Vi',15,3), ('Ra Vi',50,10),
    ('Do',1,20), ('So',1,10), ('Prospe',1,3),
    ('Ga Pa',1,100), ('Ga Pme',1,90), ('Po',1,51),
    ('Do Ren',1,5), ('Pa Do Ren',3,15), ('Ra Do Pou',10,50),
    ('Ré Per Mé',1,10), ('Ré Per Di',1,10), ('de chasse',1,5)])
def test_client_weights_are_identical_in_both_engine_entrypoints(rune,gain,weight):
    assert (reference(rune).gain,reference(rune).weight) == (gain,weight)
    assert (legacy_reference(rune).gain,legacy_reference(rune).weight) == (gain,weight)


def test_signature_is_not_made_into_a_free_combat_rune():
    assert reference('de Signature').weight is None
    assert 'de Signature' not in {r for choices in RUNE_CHOICES.values() for r in choices}


def test_new_tier_can_be_used_and_density_is_not_an_inventory_weight():
    assert 'Ra Do Pou' in RUNE_CHOICES['Dommages Poussée']
    assert WEIGHT_PER_POINT['% Résistance Mêlée'] == 10
    assert reference('Ga Pa').weight != 1  # inventory weight is irrelevant


def test_catalogue_records_all_105_runes_and_honest_provenance():
    data=weights.load_weights()
    assert len(data['runes']) == 105
    assert data['provenance']['game_version'] == '3.7.13.17'
    assert data['provenance']['publisher_verified'] is False
    assert data['provenance']['source_kind'] == 'client_extraction_third_party'
    assert data['provenance']['files']['effectsdata.json']['sha256'] == 'f037f4dc11fc42252c2158f666454a31358f195a2c94f1c956a86866662c1ae5'


def test_returned_provenance_cannot_mutate_active_weights():
    first=weights.load_weights()
    first['runes'][0]['weight']=999
    second=weights.load_weights()
    assert second['runes'][0]['weight']==1
    assert reference('Fo').weight==1
