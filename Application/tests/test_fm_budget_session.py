"""Economic preferences survive saving and legacy modes normalize."""
import json
import pytest
from forgely_tools import read_settings, save_settings


@pytest.mark.parametrize('mode',['Chances maximales','Budget optimisé','Économique'])
def test_economy_settings_preserve_prices(tmp_path,mode):
    path=tmp_path/'prefs.json'
    save_settings({'strategy':mode,'budget_kamas':500,'prices':{'Fo':2}},path)
    expected={'strategy':mode if mode=='Budget optimisé' else 'Chances maximales','budget_kamas':500,'prices':{'Fo':2}}
    assert read_settings(path)==expected
    assert json.loads(path.read_text(encoding='utf8'))==expected


def test_default_mode_is_chances(tmp_path):
    assert read_settings(tmp_path/'absent')=={'strategy':'Chances maximales','budget_kamas':0,'prices':{}}
