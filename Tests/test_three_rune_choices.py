from forgely_decision import advise
from forgely_predictive import matrix_payload, report_text
from forgely_dofocus import reference
import os
import pytest


def row(rune, score, rates, n=0):
    return (score, rune, 'Force', 'fm_classique', reference(rune),
            {'prediction': dict(zip(('SC', 'SN', 'EC'), rates), calibration_n=n)},
            None, 0, 10, 40)


def test_three_choices_preserve_recommendation_and_compare_exposure():
    # Best complete-target score wins even when another rune passes more often.
    rows=[row('Pa Fo', 90, (20, 30, 50), 42),
          row('Fo', 80, (40, 50, 10)), row('Ra Fo', 70, (10, 20, 70))]
    data=matrix_payload(rows, {'Force':10}, {'Force':40}, 2,
                        dict(saturation=.25, profile_complete=True))
    assert [x['rune'] for x in data['choices']]==['Pa Fo', 'Fo', 'Ra Fo']
    assert [x['role'] for x in data['choices']]==['recommended', 'prudent', 'stronger']
    assert data['choices'][0]['probabilities']=={'SC':20, 'SN':30, 'EC':50}
    assert data['choices'][0]['real_observations']==42
    assert [x['exposed_weight'] for x in data['choices']]==['1', '0', '8']


def test_live_report_shows_all_choices_and_real_sample_counts():
    p=advise({'Force':10}, {'Force':40}, natural_max={'Force':40},
             pool=30, predictive_policy=True)
    choices=p.estimates['matrix']['choices']
    assert len(choices)==3
    assert choices[0]['rune']==p.rune
    for compact in (False, True):
        text=report_text(p, {'Force':10}, {'Force':40}, {'Force':40}, 30, compact=compact)
        assert 'expérimentales' in text
        for choice in choices:
            assert choice['rune'] in text
        assert all(label in text for label in ('SC', 'SN', 'EC'))
        assert '0 essai' in text


def test_one_compatible_rune_is_not_duplicated_and_partial_rates_stay_unknown():
    p=advise({'Force':39}, {'Force':40}, natural_max={'Force':40},
             pool=3, profile_complete=False, predictive_policy=True)
    choices=p.estimates['matrix']['choices']
    assert len(choices)==1
    assert choices[0]['rune']=='Fo'
    assert choices[0]['probabilities'] is None
    assert choices[0]['real_observations']==0
    assert 'non disponibles' in report_text(p, {'Force':39}, {'Force':40}, {'Force':40}, 3)


def test_invalid_distribution_never_becomes_displayed_odds():
    data=matrix_payload([row('Fo', 1, (80, 50, -30), 40)],
                        {'Force':10}, {'Force':40}, 3,
                        dict(saturation=.25, profile_complete=True))
    assert data['choices'][0]['probabilities'] is None


def test_completed_target_has_no_stale_rune_choices():
    p=advise({'Force':40}, {'Force':40}, natural_max={'Force':40},
             pool=3, predictive_policy=True)
    text=report_text(p, {'Force':40}, {'Force':40}, {'Force':40}, 3, compact=True)
    assert p.rune is None
    assert 'Objectif atteint' in text
    assert 'SC ~' not in text


def test_real_samples_below_calibration_threshold_are_visible_without_changing_odds():
    args=dict(natural_max={'Force':40}, pool=30, predictive_policy=True)
    original=advise({'Force':10}, {'Force':40}, **args)
    learned=advise({'Force':10}, {'Force':40}, **args,
                   context_for=lambda rune: {'verified':True,'counts':{'SC':12,'SN':7,'EC':10}})
    for before,after in zip(original.estimates['matrix']['choices'], learned.estimates['matrix']['choices']):
        assert after['real_observations']==29
        assert after['probabilities']==before['probabilities']
        assert 'non calibré' in after['confidence']


@pytest.mark.skipif(os.environ.get('FORGELY_GUI_TESTS')!='1', reason='requires a desktop')
def test_three_rune_overlay_fits_without_hiding_controls():
    import tkinter as tk
    from tkinter.font import Font
    from forgely_overlay import FloatingBadge
    root=tk.Tk();root.withdraw()
    badge=FloatingBadge(root, lambda:None, lambda:None, lambda:None, on_reviews=lambda:None)
    try:
        p=advise({'Force':10}, {'Force':40}, natural_max={'Force':40}, pool=30, predictive_policy=True)
        text=report_text(p, {'Force':10}, {'Force':40}, {'Force':40}, 30, compact=True)
        badge.show_prediction(text)
        for reviews in (0, 1):
            badge.sync_review(reviews);root.update_idletasks()
            font=Font(root=root, font=badge.feed_label.cget('font'))
            wrapped=0
            for line in text.splitlines():
                current='';wrapped+=1
                for word in line.split():
                    candidate=(current+' '+word).strip()
                    if current and font.measure(candidate)>330:
                        wrapped+=1;current=word
                    else:current=candidate
            assert wrapped*font.metrics('linespace')+4<=badge.feed_label.winfo_height()
            assert badge.feed_label.winfo_y()+badge.feed_label.winfo_height()<=badge.action_buttons[0].winfo_y()
            assert badge.learning_label.winfo_y()+badge.learning_label.winfo_height()<=badge.winfo_height()
    finally:
        badge.destroy();root.destroy()
