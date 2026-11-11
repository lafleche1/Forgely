from types import SimpleNamespace
from forgely_measured_goals import learning_sources
from forgely_simulation_live import SimulationWorker


def test_live_advice_never_requests_simulation_but_keeps_real_sources(monkeypatch):
    def forbidden(*args,**kwargs):
        raise AssertionError('Live advice must not launch or read simulations')
    monkeypatch.setattr(SimulationWorker,'context',forbidden)
    laboratory=SimpleNamespace(estimate=lambda *args:'observations',
        calibration=lambda *args:'verified calibration',
        experience=lambda *args:'real experience')
    worker=SimulationWorker(trials=16)
    try:
        sources,key=learning_sources('Test',{'Force':39},3,{'Force':40},laboratory,worker)
        assert key is None
        assert 'simulation_for' not in sources
        assert sources['contextual_for']('Fo')=='observations'
        assert sources['context_for']('Fo')=='verified calibration'
        assert sources['experience_for']('Fo')=='real experience'
        assert worker._thread is None
    finally:worker.stop()
