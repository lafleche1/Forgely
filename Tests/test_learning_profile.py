from unittest.mock import Mock,patch
import pytest
from forgely import Forgely


def test_partial_imported_bounds_never_authorize_learning():
    from forgely_learning import complete_learning_profile
    with patch('forgely_dofocus.natural_profile',return_value=None), \
         patch('forgely_equipment_catalog.bundled_bounds',return_value={}), \
         patch('forgely.natural_bounds',return_value={'Force':(1,40)}):
        assert complete_learning_profile('Objet inconnu') is None


def test_even_valid_rune_change_cannot_train_with_missing_natural_line():
    app=Mock();app.context_saved=0
    with patch('forgely.complete_learning_profile',return_value={'Force':40,'Vitalité':300}), \
         patch('forgely.save_transition') as save, pytest.raises(ValueError):
        Forgely.record_learning(app,'Anneau','Fo','SC',
            {'jet':{'Force':20},'pool':5},{'jet':{'Force':21},'pool':5})
    save.assert_not_called()
