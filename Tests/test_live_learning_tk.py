import os
from pathlib import Path
from unittest.mock import patch
import pytest


@pytest.mark.skipif(os.environ.get('FORGELY_GUI_TESTS')!='1',reason='requires a desktop')
def test_learning_feedback_visible_on_badge_without_opening_main_window(tmp_path):
    if os.environ.get('FORGELY_LEARNING_GUI_CHILD')!='1':
        import subprocess,sys
        result=subprocess.run([sys.executable,'-m','pytest',str(Path(__file__).resolve())+
            '::test_learning_feedback_visible_on_badge_without_opening_main_window','-q','--tb=short'],
            env=dict(os.environ,FORGELY_LEARNING_GUI_CHILD='1'),capture_output=True,text=True,timeout=45)
        assert result.returncode==0,result.stdout+result.stderr
        return
    from forgely import Forgely,physical_pixels
    from forgely_context import save_transition
    from forgely_labo_live import LiveLaboratory
    physical_pixels()
    with patch('forgely.load_plan',return_value=None):app=Forgely()
    try:
        app.live_laboratory.stop()
        app.live_laboratory=LiveLaboratory(tmp_path/'learning.db')
        app.minimize_to_badge();app.update()
        with patch('forgely.complete_learning_profile',return_value={'Force':40}), \
             patch('forgely.save_transition',side_effect=lambda *args,**kw:save_transition(
                *args,db_file=app.live_laboratory.db_file,**kw)):
            app.record_learning('Anneau','Fo','SC',
                {'jet':{'Force':20},'pool':5},{'jet':{'Force':21},'pool':5})
        app.update()
        assert app.state()=='withdrawn'
        assert 'Force +1' in app.learning_summary.get()
        label=app.overlay.learning_label
        assert label.winfo_ismapped() and 'Fo / SC' in label.cget('text')
        assert label.winfo_y()+label.winfo_height()<=app.overlay.winfo_height()
        assert app.live_laboratory.status()['observations']==1
    finally:app.close()
