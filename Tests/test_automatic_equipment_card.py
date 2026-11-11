from forgely_equipment_catalog import EquipmentCatalog


def test_floating_card_hides_old_name_and_shows_stable_numeric_rows():
    from unittest.mock import Mock
    from forgely_dashboard import AtelierDashboard
    from forgely_workshop_readings import WorkshopReadings
    app=Mock()
    app.workshop_readings=WorkshopReadings()
    for i in range(3):app.workshop_readings.observe({'Intelligence':40},1.9,sequence=i)
    app.active_equipment_verified=False;app.live_jet=None
    app.live_after_fusion=True;app.workshop_active=True
    app.equipment_mode.get.return_value='automatic'
    app.item.get.return_value='Anneau du Cycloïde'
    app.manual_equipment=None;app.plan=None
    dashboard=Mock();dashboard.app=app;dashboard.activity=[]
    dashboard.table.get_children.return_value=()
    AtelierDashboard.sync(dashboard)
    title,rows,_,_=app.overlay.sync_equipment.call_args.args
    assert title=='Identification en cours'
    assert rows[0][3]=='Lu · jet partiel'
    assert 'identification' in dashboard.reading_label.configure.call_args.kwargs['text']


def test_automatic_card_uses_confirmed_object_and_never_old_plan():
    from forgely_dashboard import equipment_card
    plan={'item':'Anneau du Cycloïde','stats':{'Vitalité':{'target':300}}}
    state=equipment_card('automatic',True,'GELANO',plan=plan)
    assert state['title']=='Gelano'
    assert state['editable']
    assert state['equipment'].name=='Gelano'
    assert state['targets']=={}
    waiting=equipment_card('automatic',False,'Anneau du Cycloïde',plan=plan)
    assert waiting['title']=='Identification en cours'
    assert not waiting['editable'] and not waiting['targets']


def test_detected_item_targets_are_available_without_changing_mode():
    from forgely_dashboard import equipment_card
    plan={'item':'GELANO','stats':{'Vitalité':{'target':100}}}
    state=equipment_card('automatic',True,'Gelano',plan=plan)
    assert state['targets']=={'Vitalité':100}


def test_open_editor_for_previous_item_is_replaced():
    from unittest.mock import Mock,patch
    from forgely import Forgely
    app=Mock();app.equipment_mode.get.return_value='automatic'
    app.item.get.return_value='GELANO';app.active_equipment_verified=True
    app.manual_equipment=None;app.theme_name='Obsidienne'
    old=app.equipment_picker
    old.selected=EquipmentCatalog().search('Anneau','cycloide')[0]
    old.winfo_exists.return_value=True
    with patch('forgely_equipment_picker.EquipmentPicker') as factory:
        Forgely.open_equipment_picker(app,goals_only=True)
    old.close.assert_called_once()
    assert factory.call_args.kwargs['selected_id']==EquipmentCatalog().search('Anneau','gelano')[0].item_id
