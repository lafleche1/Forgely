"""Diagnostic sur captures existantes, sans vérité terrain d'identité inventée."""
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter_ns
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Application'))
from PIL import Image
from forgely_equipment_catalog import EquipmentCatalog
from forgely_equipment_identity import bundled_identity_index
from forgely_item_identity import ItemIdentityReader
from forgely_item_vision import recognize_item_header
from runeforge_observer import extract_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    bundled_identity_index()  # separate cold initialization from capture latency
    registered = tuple((x.item_id, x.name) for x in EquipmentCatalog().items)
    records = []
    for filename in ('frame_001.png', 'frame_014.png', 'frame_027.png'):
        path = ROOT / 'Tests/fixtures/live_20261107' / filename
        if not path.exists():
            records.append({'file': filename, 'status': 'missing'})
            continue
        with Image.open(path) as source:
            image = source.convert('RGB')
        reader = ItemIdentityReader()
        for repeat in range(2):
            calls = []
            def ocr(patch_image):
                start = perf_counter_ns()
                text = extract_text(patch_image)
                calls.append({'size': patch_image.size, 'elapsed_ms': (perf_counter_ns()-start)/1e6})
                return text
            start = perf_counter_ns()
            with patch('forgely_item_identity.recognize_item_header', wraps=recognize_item_header) as header:
                reading = reader.read(image, ocr, registered)
            records.append({'file': filename, 'repeat': repeat,
                            'elapsed_ms': (perf_counter_ns()-start)/1e6,
                            'name_ocr_passes_requested': 2 * header.call_count,
                            'ocr_calls': calls, 'known': reading.known if reading else None,
                            'candidate': reading.candidate if reading else None,
                            'signature': reading.signature if reading else (),
                            'status': 'read' if reading else 'workshop_not_validated'})
    result = {'scope': 'Three existing unlabeled captures, default fixed geometry; category unknown. '
                        'Real OCR backend, existing OCR cache retained. No precision/recall claim.',
              'records': records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    main()
