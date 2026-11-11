from unittest.mock import patch
import runeforge_observer as reader
from forgely_data import RUNES


def test_known_rune_labels_are_prepared_once_but_each_new_text_is_read():
    reader.find_rune('rune Pa Fo',RUNES)
    with patch.object(reader,'normalized',wraps=reader.normalized) as normalize:
        assert reader.find_rune('rune Pa Fo',RUNES)=='Pa Fo'
        assert reader.find_rune('rune Ra Vi',RUNES)=='Ra Vi'
        assert normalize.call_count==2


def test_changed_catalogue_and_conflicting_mentions_are_never_reused():
    assert reader.find_rune('rune Fo',('Fo',))=='Fo'
    assert reader.find_rune('rune Fo',('Vi',)) is None
    assert reader.find_rune('rune Fo puis rune Vi',('Fo','Vi')) is None
    assert reader.find_rune('15 Pa 300 Ra',RUNES) is None
    assert reader.find_rune('rune de Ré Pa',('Ré Pa',))=='Ré Pa'
