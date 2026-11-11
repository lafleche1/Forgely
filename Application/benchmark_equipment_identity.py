"""Latency/coverage on bundled references, not a live-screen accuracy estimate."""
import argparse
from collections import Counter
import json
import platform
from pathlib import Path
from time import perf_counter_ns

import numpy as np
from PIL import Image, ImageEnhance

from forgely_equipment_identity import bundled_identity_index, clear_index_cache


def summary(samples):
    return {label: float(np.percentile(samples, percentile)) for label, percentile in
            (('p50_ms', 50), ('p95_ms', 95), ('p99_ms', 99), ('max_ms', 100))} if samples else {}


def benchmark(limit=200, repeats=500):
    clear_index_cache()
    start = perf_counter_ns()
    index = bundled_identity_index()
    cold_ms = (perf_counter_ns() - start) / 1e6
    # Evenly spaced references, deterministic catalogue order; no hand-picked winners.
    indices = np.linspace(0, len(index.references) - 1,
                          min(limit, len(index.references)), dtype=int) if index.references else []
    trials, samples, counts = [], [], Counter()
    for i in indices:
        reference = index.references[i]
        with Image.open(reference.image) as source:
            icon = source.copy()
        for variant, probe in (('reference', icon), ('brightness_1.05', ImageEnhance.Brightness(icon).enhance(1.05))):
            start = perf_counter_ns()
            result = index.resolve(probe, reference.signature, reference.category)
            samples.append((perf_counter_ns() - start) / 1e6)
            outcome = 'abstained' if result.name is None else 'correct' if result.name == reference.name else 'wrong'
            counts[outcome] += 1
            trials.append({'item_id': reference.item_id, 'variant': variant, 'outcome': outcome,
                           'method': result.method, 'candidate_count': len(result.candidates)})
    warm = []
    if len(indices):
        reference = index.references[int(indices[0])]
        with Image.open(reference.image) as source:
            icon = source.copy()
        index.resolve(icon, reference.signature, reference.category)
        for _ in range(repeats):
            start = perf_counter_ns()
            index.resolve(icon, reference.signature, reference.category)
            warm.append((perf_counter_ns() - start) / 1e6)
    return {'python': platform.python_version(), 'platform': platform.platform(),
            'scope': 'Oracle category and natural bounds; original artwork + brightness 1.05. No screen crop/OCR timing.',
            'index_build_ms': cold_ms, 'indexed_items': len(index.references),
            'unreadable_item_count': len(index.unreadable), 'query_count': len(samples),
            'query_latency': summary(samples), 'warm_cache_repeats': repeats,
            'warm_cache_latency': summary(warm), 'outcomes': dict(counts),
            'trials': trials}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=200)
    parser.add_argument('--repeats', type=int, default=500)
    args = parser.parse_args()
    result = benchmark(args.limit, args.repeats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'trials'}))
