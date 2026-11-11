from forgely_workshop_readings import WorkshopReadings


def test_one_unstable_line_does_not_restart_other_visible_confirmations():
    r=WorkshopReadings();r.configure('item',{'Force','Vitalité'})
    r.observe({'Force':38,'Vitalité':244},0)
    r.observe({'Force':39,'Vitalité':244},0)
    r.observe({'Force':38,'Vitalité':244},0)
    assert r.partial_jet=={'Vitalité':244}
    assert r.line_states['Vitalité']=='confirmed'
    assert r.snapshot() is None
    assert 'Force' in r.waiting_reason
    assert 'Vitalité' not in r.waiting_reason
    r.observe({'Force':38,'Vitalité':244},0)
    assert r.observe({'Force':38,'Vitalité':244},0)
    assert r.snapshot()==({'Vitalité':244,'Force':38},0)


def test_missing_line_does_not_lose_other_confirmed_visible_values():
    r=WorkshopReadings();r.configure('item',{'Force','Vitalité'})
    for _ in range(3):r.observe({'Force':38,'Vitalité':244},0)
    for _ in range(3):r.observe({'Force':39},0)
    assert r.partial_jet=={'Force':39}
    assert r.line_states['Force']=='confirmed'
    assert r.line_states['Vitalité']=='stale'
    assert r.snapshot() is None
    r.invalidate()
    assert r.partial_jet is None and r.snapshot() is None
