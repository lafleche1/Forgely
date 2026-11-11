from PIL import Image,ImageDraw
from forgely_equipment_identity import EquipmentIdentityIndex,Reference
from forgely_equipment_prepared import load_prepared,save_prepared


def test_prepared_index_keeps_pixels_hashes_and_invalidates_changed_artwork(tmp_path):
    import numpy as np
    path=tmp_path/'icon.png'
    image=Image.new('RGB',(32,32),'#38394e');ImageDraw.Draw(image).ellipse((4,4,26,28),fill='red')
    image.save(path)
    refs=(Reference(1,'Test','Anneau',(('Force',1,10),),path),)
    index=EquipmentIdentityIndex(refs)
    file=tmp_path/'prepared.npz'
    save_prepared(file,refs,index)
    prepared=load_prepared(file,refs)
    assert prepared is not None
    restored=EquipmentIdentityIndex(refs,prepared=prepared)
    assert np.array_equal(restored.pixels,index.pixels)
    assert np.array_equal(restored.hashes,index.hashes)
    assert restored.profiles==index.profiles
    image.putpixel((15,15),(1,255,10));image.save(path)
    assert load_prepared(file,refs) is None


def test_broken_prepared_cache_is_ignored(tmp_path):
    path=tmp_path/'bad.npz';path.write_bytes(b'not an index')
    assert load_prepared(path,()) is None


def test_interrupted_zip_cache_is_ignored(tmp_path):
    import numpy as np
    path=tmp_path/'interrupted.npz'
    np.savez_compressed(path,first=np.zeros((100,32,32,3),dtype=np.uint8))
    path.write_bytes(path.read_bytes()[:-30])
    assert load_prepared(path,()) is None
