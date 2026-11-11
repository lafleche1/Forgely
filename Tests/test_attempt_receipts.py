import queue
from types import SimpleNamespace
from unittest.mock import Mock, patch
from PIL import Image
from forgely import Forgely, LatestFrameMailbox
from forgely_pipeline import AcceptedAttemptGroups
from forgely_attempt_activity import record_activity, activity_total
from forgely_data import stats


def test_unclassified_receipt_persists_once_and_updates_feed_without_learning(tmp_path):
    mailbox = LatestFrameMailbox()
    mailbox.publish(Image.new('RGB', (1648, 928)), 'DOFUS', 1, 0)
    app = SimpleNamespace(messages=queue.Queue(),frame_mailbox=mailbox,
        detect_label=Mock(),detect_help=Mock(),last_detected=Mock(),status=Mock(),
        refresh_stats_now=Mock(),refresh_strategy=Mock(),winfo_exists=lambda:False)
    receipt = AcceptedAttemptGroups(1,'session',(('group-signature','root-signature'),),
                                   None,mailbox,mailbox.generation(),'DOFUS')
    app.messages.put(('accepted_attempt_groups',receipt))
    app.messages.put(('accepted_attempt_groups',receipt))
    db = tmp_path/'local.sqlite3'
    def save(*args,**kwargs):return record_activity(*args,**kwargs,db_file=db)
    with patch('forgely.record_activity',side_effect=save), \
         patch('forgely.insert_observation',side_effect=AssertionError('No classified outcome')):
        Forgely.process_messages(app)
    assert activity_total(db_file=db)==1
    assert stats(db_file=db)==(0,{'SC':0,'SN':0,'EC':0})
    assert 'résultat non déterminé' in app.detect_label.configure.call_args.kwargs['text']


def test_initial_history_status_explains_visible_groups_without_recording_old_attempts():
    app=SimpleNamespace(messages=queue.Queue(),detect_label=Mock(),detect_help=Mock(),
                        winfo_exists=lambda:False)
    app.messages.put(('attempt_group_status',{'status':'initial_reference','visible':2,'observed':0}))
    Forgely.process_messages(app)
    assert '2' in app.detect_label.configure.call_args.kwargs['text']
    assert 'initiale' in app.detect_help.configure.call_args.kwargs['text']


def test_local_observations_card_uses_global_counts_without_assigning_unknown_to_selected_item():
    app=Mock()
    app.item.get.return_value='Anneau du Cycloïde'
    app.rune.get.return_value='Vi'
    app.stats_labels={kind:Mock() for kind in ('SC','SN','EC')}
    def classified(item='',**kwargs):
        return (2,{'SC':2,'SN':0,'EC':0}) if not item else (0,{'SC':0,'SN':0,'EC':0})
    def raw(item='',**kwargs):
        return 1 if not item else 0
    with patch('forgely.stats',side_effect=classified),patch('forgely.activity_total',side_effect=raw):
        Forgely.refresh_stats_now(app)
    assert app.total_lbl.configure.call_args.kwargs['text']=='3 tentatives'
