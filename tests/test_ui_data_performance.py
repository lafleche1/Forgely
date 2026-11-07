"""Read-path caching must preserve external edits and caller isolation."""
import json
from pathlib import Path
from unittest.mock import patch

from forgely_tools import read_settings
from forgely_rune_icons import rune_icon_path


def test_settings_reuses_unchanged_file_and_isolates_mutation(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'prices': {'Vi': 5}}))
    original = Path.read_text
    with patch.object(Path, 'read_text', autospec=True, side_effect=original) as read:
        first = read_settings(path)
        first['prices']['Vi'] = 999
        assert read_settings(path)['prices']['Vi'] == 5
        assert read.call_count == 1
        replacement = path.with_suffix('.new')
        replacement.write_text(json.dumps({'prices': {'Vi': 6}}))
        replacement.replace(path)
        assert read_settings(path)['prices']['Vi'] == 6
        assert read.call_count == 2
    path.unlink()
    assert read_settings(path)['prices'] == {}
    path.write_text('{broken')
    assert read_settings(path)['prices'] == {}
    path.write_text(json.dumps({'prices': {'Vi': 7}}))
    assert read_settings(path)['prices']['Vi'] == 7


def test_icon_catalogue_reuses_parse_but_not_file_existence(tmp_path):
    index = tmp_path / 'index.json'
    index.write_text(json.dumps([{'rune': 'Vi', 'file': 'vi.png'}]))
    icon = tmp_path / 'vi.png'
    icon.touch()
    original = Path.read_text
    with patch.object(Path, 'read_text', autospec=True, side_effect=original) as read:
        assert rune_icon_path('Rune Vi × 2', tmp_path) == icon
        assert rune_icon_path('Vi', tmp_path) == icon
        assert read.call_count == 1
        icon.unlink()
        assert rune_icon_path('Vi', tmp_path) is None
        index.write_text(json.dumps([{'rune': 'Vi', 'file': '../invalid.png'}]))
        assert rune_icon_path('Vi', tmp_path) is None
        assert read.call_count == 2
