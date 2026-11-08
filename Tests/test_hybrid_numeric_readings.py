def test_visual_reading_can_complete_a_missing_ocr_line_without_theory():
    from forgely_vision_guidance import merge_observation
    jet,pool,source=merge_observation({'Vitalité':297},{'Vitalité':297,'Dommages Terre':7},2.9,'2.9')
    assert jet=={'Vitalité':297,'Dommages Terre':7} and pool==2.9 and source=='hybrid'


def test_disagreement_blocks_current_reading_instead_of_voting():
    from forgely_vision_guidance import merge_observation
    assert merge_observation({'Force':38},{'Force':37},0,'0')==({},None,'conflict')
    assert merge_observation({'Force':38},{'Force':38},2.9,'1.9')==({},None,'conflict')


def test_zero_exo_and_over_are_real_readings_not_replaced_by_maxima():
    from forgely_vision_guidance import merge_observation
    jet,pool,source=merge_observation({'Force':70},{'Vitalité':0,'PA':1},None,'0')
    assert jet=={'Force':70,'Vitalité':0,'PA':1} and pool==0
