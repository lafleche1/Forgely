def test_theory_guides_missing_lines_but_never_fills_or_clamps_values():
    from forgely_vision_guidance import reference_report
    jet={'Vitalité':0,'Force':70,'PA':1}
    report=reference_report({'Vitalité':(250,300),'Force':(30,40),'Tacle':(4,6)},jet)
    assert report['missing']==['Tacle']
    assert report['extra']==['PA']
    assert report['below_min']==['Vitalité']
    assert report['above_max']==['Force']
    assert jet=={'Vitalité':0,'Force':70,'PA':1}


def test_aliases_and_negative_natural_stats_are_supported():
    from forgely_vision_guidance import reference_report
    report=reference_report({'Invocations':(1,1),'Tacle':(-6,-4)},{'Invocation':1,'Tacle':-4})
    assert not report['missing'] and not report['extra'] and not report['below_min'] and not report['above_max']
