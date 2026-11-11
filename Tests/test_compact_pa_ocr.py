import pytest
from forgely_jet import parse_jet


@pytest.mark.parametrize('text,expected', [
    ('Wi1PA',{'PA':1}), ('Wi0PA',{'PA':0}),
    ('Wi-1PA',{'PA':-1}), ('Wi1PM',{'PM':1}),
    ('1PA',{'PA':1}), ('10 Retrait PA',{'Retrait PA':10}),
    ('Wi1PA\n0 PA',{}),
])
def test_explicit_compact_icon_value_is_read_without_guessing(text,expected):
    assert parse_jet(text)==expected


@pytest.mark.parametrize('text',['OPA','WiPA','Wi1PA bonus','Objet Wi1PA',
    'niveau1PA','Wi1PAfoo','[PROFIL] Wi1PA'])
def test_ambiguous_or_non_effect_text_does_not_create_pa(text):
    assert 'PA' not in parse_jet(text)


def test_kido_diagnostic_can_stabilize_complete_jet_and_pool():
    from forgely_workshop_readings import WorkshopReadings
    from forgely_vision_guidance import reference_for
    raw='134 Vitalité\n38 Intelligence\n39 Sagesse\nWi1PA\n18 Prospection\n10% Résistance Feu\n9% Résistance Air'
    reading=WorkshopReadings()
    reading.configure(('confirmed','Médaille Kido'),reference_for('Médaille Kido'))
    for sequence in range(3):
        reading.observe(parse_jet(raw),0.2,sequence=sequence)
    assert reading.snapshot()==(parse_jet(raw),0.2)
    assert reading.snapshot()[0]['PA']==1
    assert reading.waiting_reason is None
