"""Deterministic discovery cost bounds, independent of Windows timing noise."""
import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Application'))
import forgely_windows as windows


def window(handle=1, title='Character - Class - 3.7.13.17 - Release',
           rect=(0, 0, 1000, 800), minimized=False):
    return windows.NativeWindow(handle, title, rect, minimized)


def test_versioned_titles_need_no_process_queries(monkeypatch):
    lookup = Mock(return_value='')
    monkeypatch.setattr(windows, 'process_executable', lookup)
    for suffix in ('Release', 'Beta'):
        assert windows.is_game_window(window(title=f'Character - 3.7.13.17 - {suffix}'))
    lookup.assert_not_called()


def test_generic_titles_require_process_verification(monkeypatch):
    lookup = Mock(return_value='browser.exe')
    monkeypatch.setattr(windows, 'process_executable', lookup)
    for title in ('Dofus wiki', 'DOFUS', '3.7 - Release', 'Random document'):
        assert not windows.is_game_window(window(title=title))
    assert lookup.call_count == 4
    lookup.return_value = 'dofus.exe'
    assert windows.is_game_window(window(title='Unfamiliar game title'))


def test_own_window_never_accepted_by_version_shortcut(monkeypatch):
    lookup = Mock(return_value='dofus.exe')
    monkeypatch.setattr(windows, 'process_executable', lookup)
    assert not windows.is_game_window(window(title='Forgely - 3.7.13.17 - Release'))
    lookup.assert_not_called()


def test_hidden_size_candidates_cost_no_process_queries(monkeypatch):
    monkeypatch.setattr(windows, 'native_windows', lambda: [
        window(title='Other', minimized=True),
        window(title='Other', rect=(0, 0, 100, 100)),
    ])
    lookup = Mock(return_value='dofus.exe')
    monkeypatch.setattr(windows, 'process_executable', lookup)
    assert windows.list_dofus_windows() == []
    lookup.assert_not_called()


def test_every_scan_refreshes_geometry_and_owner(monkeypatch):
    first = window(title='Unfamiliar', rect=(10, 20, 1010, 820))
    moved = window(title='Unfamiliar', rect=(100, 200, 1100, 1000))
    scans = iter(([first], [moved], [window(title='Unfamiliar')], []))
    monkeypatch.setattr(windows, 'native_windows', lambda: next(scans))
    # Same HWND can be reassigned to a different process; never reuse its verdict.
    lookup = Mock(side_effect=['dofus.exe', 'dofus.exe', 'browser.exe'])
    monkeypatch.setattr(windows, 'process_executable', lookup)
    assert windows.list_dofus_windows()[0].left == 10
    assert windows.list_dofus_windows()[0].left == 100
    assert windows.list_dofus_windows() == []
    assert windows.list_dofus_windows() == []
    assert lookup.call_count == 3


def test_repeated_capture_scan_query_budget(monkeypatch):
    """120 ms polling: 100 scans of 20 windows need 1,900, not 2,000 opens."""
    desktop = [window()] + [window(handle=i + 2, title='Browser') for i in range(19)]
    monkeypatch.setattr(windows, 'native_windows', Mock(return_value=desktop))
    lookup = Mock(return_value='browser.exe')
    monkeypatch.setattr(windows, 'process_executable', lookup)
    for _ in range(100):
        assert windows.list_dofus_windows() == [desktop[0]]
    assert lookup.call_count == 1900
    assert windows.native_windows.call_count == 100
