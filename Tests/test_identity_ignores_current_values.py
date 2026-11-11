from forgely_continuous_identity import effect_signature


def test_mutable_current_values_do_not_change_identity_evidence():
    a=effect_signature('31 40 38 Force\n251 300 281 Vitalité\n7 10 11 Dommages Neutre')
    b=effect_signature('31 40 11 Force\n251 300 331 Vitalité\n7 10 5 Dommages Neutre')
    assert a==b
    assert a==(('dommages neutre',7,10),('force',31,40),('vitalite',251,300))


def test_natural_bounds_are_read_only_when_primary_artwork_is_ambiguous():
    from unittest.mock import patch,Mock
    from PIL import Image,ImageDraw
    from forgely_item_identity import ItemIdentityReader
    from forgely_equipment_identity import IdentityDecision
    image=Image.new('RGB',(1648,928),'#38394e');icon=Image.new('RGB',(32,32),'#38394e')
    ImageDraw.Draw(icon).ellipse((4,4,26,28),fill='red')
    ocr=Mock(return_value='31 40 38 Force\n251 300 281 Vitalité\n7 10 11 Dommages Neutre')
    with patch('forgely_item_identity.workshop_visual_fallback',return_value=True), \
         patch('forgely_item_identity.current_icon',return_value=icon), \
         patch('forgely_item_identity.fast_equipment_match',return_value=None), \
         patch('forgely_item_identity.slot_equipment_decision',side_effect=[
             IdentityDecision(None,(),'ambiguous'),IdentityDecision('Objet confirmé',(),'slot_artwork_bounds')]):
        result=ItemIdentityReader(artwork_only=True).read(image,ocr,[])
    assert result.known=='Objet confirmé'
    ocr.assert_called_once()
    assert ('force',31,40) in result.signature
