from test_rl_environment import env


def test_action_validation_does_not_materialize_feature_vector(monkeypatch):
    e = env()
    expected = e.get_valid_actions()
    def forbidden():
        raise AssertionError('action validation must not construct state vectors')
    monkeypatch.setattr(e, 'get_state', forbidden)
    assert e.get_valid_actions() == expected
