import os
from pathlib import Path
from unittest.mock import patch
import threading
import pytest


@pytest.mark.skipif(os.environ.get('FORGELY_GUI_TESTS')!='1',reason='requires desktop')
def test_real_app_uses_local_model_and_persists_virtual_totals_without_game_trials(tmp_path):
    if os.environ.get('FORGELY_ENGINE_GUI_CHILD')!='1':
        import subprocess,sys
        result=subprocess.run([sys.executable,'-m','pytest',str(Path(__file__).resolve())+
            '::test_real_app_uses_local_model_and_persists_virtual_totals_without_game_trials','-q','--tb=short'],
            env=dict(os.environ,FORGELY_ENGINE_GUI_CHILD='1'),capture_output=True,text=True,timeout=45)
        assert result.returncode==0,result.stdout+result.stderr
        return
    from forgely import Forgely,physical_pixels
    from forgely_simulation_journal import SimulationJournal
    from test_simulation_live import cycloid
    physical_pixels()
    with patch('forgely.load_plan',return_value=None):app=Forgely()
    try:
        item,jet=cycloid();jet['Force']=39
        app.simulation_journal=SimulationJournal(tmp_path/'virtual.db')
        ready=threading.Event()
        def on_ready(key):app.publish_simulation(key);ready.set()
        app.simulator.on_ready=on_ready
        app.observation_only=False;app.active_equipment_verified=True;app.workshop_active=True
        app.item.set(item.name);app.plan={'item':item.name,'stats':{'Force':{'target':40}}}
        app.live_jet=jet;app.live_pool=2.7;app.live_after_fusion=False
        app.auto_floating.set(False);app.minimize_to_badge()
        cfg={'strategy':'Chances maximales','budget_kamas':0,'prices':{}}
        with patch('forgely.read_settings',return_value=cfg):
            first=app.strategy_current()
            assert first.estimates['local_simulation']['kind']=='local_dofocus_model'
            assert ready.wait(5)
            app.process_messages();app.update()
            refined=app.strategy_current()
        assert refined.estimates['local_simulation']['outlook']['trials']==48
        assert app.simulation_journal.totals()['virtual']>0
        assert 'Simulées' in app.simulation_totals.get()
        assert refined.sample==0 and app.context_saved==0
        assert app.state()=='withdrawn'
    finally:app.close()
