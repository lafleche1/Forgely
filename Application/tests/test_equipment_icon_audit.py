from PIL import Image
from forgely_icon_audit import audit_icons


def test_audit_counts_files_items_pixels_and_missing_separately(tmp_path):
    a = tmp_path / '1.png'
    image = Image.new('RGB', (20, 20), 'red')
    image.save(a)
    (tmp_path / '2.png').write_bytes(a.read_bytes())
    image.save(tmp_path / '3.png', compress_level=0)
    (tmp_path / '4.png').write_bytes(b'broken')
    report = audit_icons(tmp_path, {1: [10, 11], 2: [12], 3: [13], 5: [14]}, phash_threshold=0)
    assert report['files_found'] == 4
    assert report['readable_files'] == 3
    assert report['exact_file_groups'] == [['1.png', '2.png']]
    assert report['exact_pixel_groups'] == [['1.png', '2.png', '3.png']]
    assert report['exact_pixel_item_groups'] == [[10, 11, 12, 13]]
    assert report['missing_icon_ids'] == [5]
    assert report['missing_item_ids'] == [14]
    assert len(report['unreadable']) == 1
    assert len(report['phash_pairs']) == 3
    assert report['phash_nonidentical_pixel_pairs'] == 0
