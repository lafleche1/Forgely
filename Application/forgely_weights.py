"""Versioned rune densities from a third-party extraction of the game client.

This is not an Ankama-published table or a source of success probabilities.
No networking or training occurs here. Both advisor entrypoints use this table.
"""
from functools import lru_cache
import json
from math import isfinite
from pathlib import Path

PATH = Path(__file__).parent / 'references' / 'poids_runes_client_3_7_13_17.json'


@lru_cache(maxsize=1)
def _load():
    data = json.loads(PATH.read_text(encoding='utf8'))
    if data.get('schema') != 1 or len(data.get('runes', [])) != 105:
        raise ValueError('Catalogue de densités incomplet')
    seen = set()
    for row in data['runes']:
        if row['rune'] in seen:
            raise ValueError('Rune en doublon')
        seen.add(row['rune'])
        if row['kind'] == 'signature_non_combat':
            if any(row[k] is not None for k in ('gain', 'weight', 'unit_weight')):
                raise ValueError('Signature sans densité de combat')
            continue
        if any(type(row[k]) not in (int, float) or not isfinite(row[k]) or row[k] <= 0
               for k in ('gain', 'weight', 'unit_weight')):
            raise ValueError('Densité invalide')
        if abs(row['gain'] * row['unit_weight'] - row['weight']) > 1e-6:
            raise ValueError('Gain et densité incohérents')
    return data


def load_weights():
    # Callers must not be able to mutate the active catalogue through this API.
    from copy import deepcopy
    return deepcopy(_load())
