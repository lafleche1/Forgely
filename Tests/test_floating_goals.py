import os
from pathlib import Path
from unittest.mock import Mock,patch
import pytest
from forgely import Forgely


def test_floating_goal_action_opens_editor_without_restoring_main_window():
    app=Mock()
    Forgely.open_floating_goals(app)
    app.open_equipment_picker.assert_called_once_with(goals_only=True,floating=True)
    app.restore.assert_not_called()


@pytest.mark.skipif(os.environ.get('FORGELY_GUI_TESTS')!='1',reason='requires a desktop')
def test_badge_menu_edits_automatic_targets_with_main_window_hidden(tmp_path):
    # Isolate native Tk roots from the remaining desktop test suites.
    if os.environ.get('FORGELY_FLOATING_GOALS_GUI_CHILD')!='1':
        import subprocess,sys
        result=subprocess.run([sys.executable,'-m','pytest',str(Path(__file__).resolve())+
            '::test_badge_menu_edits_automatic_targets_with_main_window_hidden','-q','--tb=short'],
            env=dict(os.environ,FORGELY_FLOATING_GOALS_GUI_CHILD='1'),
            capture_output=True,text=True,timeout=45)
        assert result.returncode==0,result.stdout+result.stderr
        return
    from forgely import physical_pixels
    from forgely_plan import save_plan,load_plan
    physical_pixels()
    with patch('forgely.load_plan',return_value=None):app=Forgely()
    try:
        app.auto_floating.set(False)
        app.set_equipment_mode('automatic')
        app.item.set('ANNEAU DU CYCLOÏDE');app.active_equipment_verified=True
        app.minimize_to_badge();app.update()
        menu=app.overlay.menu
        entries=[i for i in range(menu.index('end')+1)
                 if menu.type(i)=='command' and 'Jet cible' in menu.entrycget(i,'label')]
        assert len(entries)==1
        menu.invoke(entries[0]);app.update()
        editor=app.equipment_picker
        assert app.state()=='withdrawn'
        assert app.overlay.winfo_ismapped() and editor.winfo_ismapped()
        assert editor.attributes('-topmost')
        assert editor.stage=='goals' and editor.selected.name.casefold()=='anneau du cycloïde'
        assert str(editor.transient())==str(app.overlay)
        editor.fill_maximum()
        # Opening the editor removes DOFUS foreground capture permission.
        # Losing live verification must not prevent saving this item's targets.
        app.active_equipment_verified=False
        path=tmp_path/'floating-goals.json'
        with patch('forgely.save_plan',side_effect=lambda item,values,**kw:save_plan(item,values,path,**kw)):
            editor.commit(False)
        assert load_plan(path)['stats']['Force']['target']==40
        assert app.equipment_mode.get()=='automatic' and app.state()=='withdrawn'
        assert app.active_equipment_verified is False
        assert app.overlay.winfo_ismapped()
    finally:app.close()
