from types import SimpleNamespace
from unittest.mock import Mock, patch
from forgely_decision import Proposal


def test_stopped_observation_does_not_return_previous_live_rune():
    from forgely import Forgely
    old = Proposal('Vi', 'fm_classique', 'Vi', 'old', '')
    app = SimpleNamespace(running=False, observation_only=False,
                          _copilot_masked=True, current_proposal=old)
    with patch('forgely.held_advice', return_value=old):
        result = Forgely._strategy_current(app)
    assert result.rune is None
    assert result.summary == 'Observation arrêtée'


def test_masked_reading_never_replays_old_advice_as_current():
    from forgely import Forgely
    old = Proposal('Vi', 'fm_classique', 'Vi', 'old', '')
    app = SimpleNamespace(running=True, observation_only=False,
                          _copilot_masked=True, current_proposal=old)
    with patch('forgely.held_advice', return_value=old):
        result = Forgely._strategy_current(app)
    assert result.rune is None
    assert result.kind == 'suspendu'


def test_player_signal_explains_stopped_advice_instead_of_showing_rune():
    from forgely_copilote import player_signal
    p = Proposal(None, 'suspendu', 'Observation arrêtée', 'Démarre l’observation.', '')
    signal = player_signal(p, {'Force': 38}, {'Force': 40}, .1, True, False)
    assert signal.title == 'Observation arrêtée'
    assert signal.stop is True
