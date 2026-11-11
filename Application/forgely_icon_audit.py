"""Reproducible local equipment icon audit; no downloads or game interaction.

Run: python Application/forgely_icon_audit.py --output docs/icon-audit.json
pHash proximity is a screening measurement, never proof of identical artwork.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image

from forgely_equipment_identity import perceptual_hash


def audit_icons(directory, icon_items=None, phash_threshold=6):
    directory = Path(directory)
    icon_items = icon_items or {}
    files = sorted(directory.glob('*.png'))
    byte_groups, pixel_groups = defaultdict(list), defaultdict(list)
    fingerprints, errors, records = [], [], []
    for path in files:
        try:
            raw_hash = sha256(path.read_bytes()).hexdigest()
            with Image.open(path) as source:
                image = source.convert('RGBA')
                # Preserve dimensions and alpha; never classify resized images as exact.
                pixels = struct.pack('>II', *image.size) + image.tobytes()
                pixel_hash = sha256(pixels).hexdigest()
                # Fixed neutral background avoids arbitrary transparent RGB affecting pHash.
                background = Image.new('RGBA', image.size, '#38394e')
                phash = perceptual_hash(Image.alpha_composite(background, image))
            byte_groups[raw_hash].append(path.name)
            pixel_groups[pixel_hash].append(path.name)
            fingerprints.append(phash)
            records.append({'file': path.name, 'sha256': raw_hash, 'pixels_sha256': pixel_hash,
                            'phash': f'{phash:016x}'})
        except (OSError, ValueError) as exc:
            errors.append({'file': path.name, 'error': str(exc)})
    groups = lambda mapping: sorted(sorted(v) for v in mapping.values() if len(v) > 1)
    file_to_items = {f'{icon_id}.png': sorted(ids) for icon_id, ids in icon_items.items()}
    item_groups = []
    for group in pixel_groups.values():
        ids = sorted({item for filename in group for item in file_to_items.get(filename, ())})
        if len(ids) > 1:
            item_groups.append(ids)
    hashes = np.asarray(fingerprints, dtype=np.uint64)
    pairs, nonidentical = [], 0
    for i in range(len(records)):
        xor = np.bitwise_xor(hashes[i + 1:], hashes[i])
        if not len(xor):
            continue
        distances = np.unpackbits(xor.view(np.uint8).reshape(-1, 8), axis=1).sum(axis=1)
        for offset in np.flatnonzero(distances <= phash_threshold):
            j = i + 1 + int(offset)
            exact = records[i]['pixels_sha256'] == records[j]['pixels_sha256']
            nonidentical += not exact
            pairs.append({'a': records[i]['file'], 'b': records[j]['file'],
                          'hamming': int(distances[offset]), 'exact_pixels': exact})
    present = {path.name for path in files}
    missing = sorted(icon_id for icon_id in icon_items if f'{icon_id}.png' not in present)
    manifest = sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
    return {'directory': str(directory), 'files_found': len(files), 'readable_files': len(records),
            'referenced_item_count': sum(len(v) for v in icon_items.values()),
            'referenced_icon_count': len(icon_items),
            'missing_icon_ids': missing,
            'missing_item_ids': sorted(item for icon_id in missing for item in icon_items[icon_id]),
            'unreadable': errors, 'exact_file_groups': groups(byte_groups),
            'exact_pixel_groups': groups(pixel_groups),
            'exact_pixel_item_groups': sorted(item_groups),
            'phash_algorithm': '64-bit DCT 32x32, 8x8 AC median, DC bit zero, fixed #38394e alpha background',
            'phash_threshold': phash_threshold, 'phash_pairs': pairs,
            'phash_nonidentical_pixel_pairs': int(nonidentical),
            'manifest_sha256': manifest, 'files': records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--threshold', type=int, default=6)
    args = parser.parse_args()
    from forgely_equipment_catalog import EquipmentCatalog, ROOT
    catalogue = EquipmentCatalog()
    mapping = defaultdict(list)
    for item in catalogue.items:
        mapping[item.icon_id].append(item.item_id)
    official = audit_icons(ROOT / 'assets/equipment_icons', mapping, args.threshold)
    slot = audit_icons(ROOT / 'assets/equipment_slot_refs', phash_threshold=args.threshold)
    result = {'scope': 'Local supported FM equipment categories; rune/UI icons excluded',
              'official_equipment': official, 'verified_slot_references': slot,
              'catalogue_sha256': sha256((ROOT / 'catalogue_objets_noms_fr.csv').read_bytes()).hexdigest()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'files': official['files_found'], 'items': official['referenced_item_count'],
                      'exact_file_groups': len(official['exact_file_groups']),
                      'exact_pixel_groups': len(official['exact_pixel_groups']),
                      'exact_item_groups': len(official['exact_pixel_item_groups']),
                      'phash_pairs': len(official['phash_pairs']),
                      'phash_nonidentical': official['phash_nonidentical_pixel_pairs'],
                      'missing': len(official['missing_icon_ids']), 'unreadable': len(official['unreadable'])}))


if __name__ == '__main__':
    main()
