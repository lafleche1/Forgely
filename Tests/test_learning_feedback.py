from unittest.mock import Mock,patch
import pytest
from forgely import Forgely
from forgely_context import save_transition
from forgely_labo_live import LiveLaboratory


def test_saved_attempt_updates_memory_and_feedback_in_same_call(tmp_path):
    app=Mock();app.context_saved=0
    app.live_laboratory=LiveLaboratory(tmp_path/'learning.db')
    before={'jet':{'Force':20},'pool':5};after={'jet':{'Force':21},'pool':5}
    with patch('forgely.complete_learning_profile',return_value={'Force':40}), \
         patch('forgely.save_transition',side_effect=lambda *args,**kw:save_transition(
            *args,db_file=app.live_laboratory.db_file,**kw)):
        Forgely.record_learning(app,'Anneau','Fo','SC',before,after)
    assert app.live_laboratory.estimate('Anneau','Fo',{'Force':20},5)['n']==1
    assert app.context_saved==1
    assert app.last_learning['changes']=={'Force':1}
    assert app.last_learning['item']=='Anneau'
    assert 'Force +1' in app.last_learning['summary']
    app.refresh_strategy.assert_called_once()


def test_incoherent_sc_is_rejected_before_it_can_train(tmp_path):
    app=Mock();app.context_saved=0
    app.live_laboratory=LiveLaboratory(tmp_path/'learning.db')
    with pytest.raises(ValueError):
        Forgely.record_learning(app,'Anneau','Fo','SC',
            {'jet':{'Force':20},'pool':5},{'jet':{'Force':19},'pool':5})
    assert app.context_saved==0
    assert app.live_laboratory.status()['observations']==0
