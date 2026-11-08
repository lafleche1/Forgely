from unittest.mock import Mock


def test_review_queue_never_requests_user_confirmation():
    from forgely import Forgely
    app=Mock()
    app.reading_reviews.store.pending.return_value=[{'id':'old-image'}]
    app.reading_review_status={}
    Forgely.refresh_reading_reviews(app)
    app.overlay.sync_review.assert_called_once_with(0)
    assert app.reading_review_status['pending']==0
    assert app.reading_review_status['automatic_candidates']==1


def test_old_review_action_cannot_open_a_manual_panel():
    from forgely import Forgely
    app=Mock()
    Forgely.show_reading_reviews(app)
    app.overlay.open_review.assert_not_called()


def test_read_numeric_rows_are_not_described_as_unread_workshop():
    from forgely import Forgely
    from forgely_equipment_session import ManualEquipmentSession
    from forgely_equipment_catalog import EquipmentCatalog
    from forgely_workshop_readings import WorkshopReadings
    app=Mock();app.running=True;app.workshop_active=True
    app.active_equipment_verified=False
    app.manual_equipment=ManualEquipmentSession(EquipmentCatalog().search('Anneau','cycloide')[0])
    app.workshop_readings=WorkshopReadings()
    for i in range(3):app.workshop_readings.observe({'Vitalité':297},.9,sequence=i)
    assert 'Jet lu' in Forgely.waiting_for_item_label(app)
