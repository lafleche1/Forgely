import sys
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Application'))
import forgely_vision as vision


def test_exact_catalogue_and_noise_distances():
    folder = Path(vision.__file__).parent / 'catalogue_dofus3'
    files = list(folder.glob('*.png'))
    assert len(files) >= 105
    queries = [Image.open(files[0]).convert('RGB'), Image.effect_noise((39,37),80).convert('RGB')]
    for file in files:
        with Image.open(file) as reference:
            for query in queries:
                assert vision.distance(query, reference) == vision._plane_distance(vision._planes(query), vision._planes(reference))


def test_cache_bounded_and_tracks_direct_mutation(tmp_path):
    lib = vision.RuneLibrary(tmp_path/'icons', ['a','b'])
    first = Image.new('RGB',(32,32),'red')
    second = Image.new('RGB',(32,32),'blue')
    lib.references = [('a', first), ('b', second)]
    with patch.object(vision, '_planes', wraps=vision._planes) as planes:
        lib.predict(first)
        assert planes.call_count == 3
        planes.reset_mock()
        lib.predict(first)
        assert planes.call_count == 1
        second.paste('green',(0,0,32,32))
        planes.reset_mock()
        lib.predict(first)
        assert planes.call_count == 2
    lib.references = [('a', first)]
    lib.predict(first)
    assert len(lib._feature_cache) == 1
    lib.load()
    assert not lib._feature_cache
