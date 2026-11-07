import io
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
from forgely_catalogue import exact_rune_name, image_allowed, find_exact, sync_catalogue, api_url
from forgely_vision import RuneLibrary

def test_exact_names():
    assert exact_rune_name('Rune Vi','Vi')
    assert not exact_rune_name('Rune Pa Vi','Vi')
    assert not exact_rune_name('Rune Vi Rare','Vi')

def test_allowed_domains():
    assert image_allowed('https://static.ankama.com/path/icon.png')
    assert not image_allowed('http://static.ankama.com/img')
    assert not image_allowed('https://ankama.com.evil.org/a')

def test_duplicate_protection():
    assert find_exact([{'name':'Rune Vi','ankama_id':1},{'name':'Rune Vi','ankama_id':2}],'Vi') is None

def test_import_with_fake_api_and_image(tmp_path):
    im=Image.new('RGB',(64,64),'purple');out=io.BytesIO();im.save(out,format='PNG')
    import json
    def fake(url):
        if '/search?' in url:
            return json.dumps([{'name':'Rune Vi','ankama_id':123,'image_urls':{'icon':'https://static.ankama.com/icone.png'}}]).encode()
        return out.getvalue()
    report=sync_catalogue(tmp_path/'catalogue_dofus3',targets=('Vi','Pa Vi'),fetch=fake)
    assert report['ok']==['Vi'];assert 'Pa Vi' in report['errors']
    lib=RuneLibrary(tmp_path/'icones_runes',('Vi','Pa Vi'))
    assert lib.labels()==['Vi']
