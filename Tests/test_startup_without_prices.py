import pytest


def test_startup_does_not_install_currency_preferences(monkeypatch):
    import forgely
    import forgely_tools

    class ReachedTheme(Exception):
        pass

    def unexpected_prices(*args, **kwargs):
        raise AssertionError('Startup must not activate economic preferences')

    def stop_before_widgets():
        raise ReachedTheme

    monkeypatch.setattr(forgely.tk.Tk, '__init__', lambda self: None)
    monkeypatch.setattr(forgely_tools, 'activate_tylezia_reference', unexpected_prices)
    monkeypatch.setattr(forgely, 'load_theme', stop_before_widgets)
    with pytest.raises(ReachedTheme):
        forgely.Forgely()
