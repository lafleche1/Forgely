import hashlib
import importlib.util
import json
from pathlib import Path
import pytest


def updater():
    path = Path(__file__).parents[2] / 'outils' / 'mettre_a_jour_prix_tylezia.py'
    spec = importlib.util.spec_from_file_location('price_update', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(tmp_path):
    root = tmp_path / 'Forgely'
    (root / 'Application').mkdir(parents=True)
    (root / 'Application/forgely.py').write_text('original\n')
    payload = tmp_path / 'payload'
    (payload / 'Application').mkdir(parents=True)
    (payload / 'Application/forgely.py').write_text('updated\n')
    (payload / 'manifest.json').write_text(json.dumps({'files': [{
        'path': 'Application/forgely.py',
        'before': hashlib.sha256(b'original\n').hexdigest(),
        'after': hashlib.sha256(b'updated\n').hexdigest()}]}))
    return root, payload


def test_update_backs_up_and_is_idempotent(tmp_path):
    root, payload = fixture(tmp_path)
    observations = root / 'observations_locales.sqlite3'
    observations.write_bytes(b'keep user data')
    backup = updater().apply_update(root, payload)
    assert (root / 'Application/forgely.py').read_text() == 'updated\n'
    assert (backup / 'Application/forgely.py').read_text() == 'original\n'
    assert updater().apply_update(root, payload) is None
    assert observations.read_bytes() == b'keep user data'


def test_unknown_local_version_is_not_overwritten(tmp_path):
    root, payload = fixture(tmp_path)
    (root / 'Application/forgely.py').write_text('newer local edits')
    with pytest.raises(ValueError):
        updater().apply_update(root, payload)
    assert (root / 'Application/forgely.py').read_text() == 'newer local edits'


def test_corrupted_payload_is_rejected_before_writing(tmp_path):
    root, payload = fixture(tmp_path)
    (payload / 'Application/forgely.py').write_text('broken')
    with pytest.raises(ValueError):
        updater().apply_update(root, payload)
    assert (root / 'Application/forgely.py').read_text() == 'original\n'


def test_update_accepts_an_explicitly_supported_prior_release(tmp_path):
    root, payload = fixture(tmp_path)
    (root / 'Application/forgely.py').write_text('prior release\n')
    manifest=json.loads((payload/'manifest.json').read_text())
    manifest['files'][0]['before_versions']=[hashlib.sha256(b'prior release\n').hexdigest()]
    (payload/'manifest.json').write_text(json.dumps(manifest))
    updater().apply_update(root,payload)
    assert (root / 'Application/forgely.py').read_text()=='updated\n'
