"""Offline validation of REAL, verified FM attempts (never synthetic training data).

This estimates descriptive frequencies only. It cannot estimate conditional
probabilities for a specific jet, pool, or rune from an unconditioned CSV.
"""
from __future__ import annotations
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

OUTCOMES = ('SC', 'SN', 'EC')
VERIFIED_SOURCES = frozenset({'ocr_confirmed', 'manual', 'video_verified'})
REQUIRED = {'date_utc', 'equipement', 'rune', 'resultat', 'source'}


def wilson(successes: int, total: int, z: float = 1.96):
    """Approximate 95% Wilson interval for one outcome (descriptive only)."""
    if total <= 0:
        return None
    p = successes / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total))/denominator
    radius = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total))/denominator
    return [round(max(0., center-radius), 5), round(min(1., center+radius), 5)]


def validate_rows(path, *, min_samples=30):
    """Read explicit reviewed observations. No OCR-auto or unreviewed VOD entries.

    This report intentionally never exports a learned 'game probability' model.
    """
    if not 1 <= min_samples <= 100000:
        raise ValueError('min_samples invalide')
    accepted = defaultdict(Counter)
    skipped = Counter()
    seen = set()
    with Path(path).open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
            raise ValueError('Colonnes attendues : ' + ', '.join(sorted(REQUIRED)))
        for row in reader:
            item = (row['equipement'] or '').strip()
            rune = (row['rune'] or '').strip()
            outcome = (row['resultat'] or '').strip().upper()
            source = (row['source'] or '').strip()
            date = (row['date_utc'] or '').strip()
            if source not in VERIFIED_SOURCES:
                skipped['source_non_verifiee'] += 1
                continue
            if not item or not rune or outcome not in OUTCOMES or not date:
                skipped['ligne_incomplete'] += 1
                continue
            # Exact duplicate rows in exported files are likely accidental;
            # distinct genuine attempts at the same second need unique timestamps.
            signature = (date, item, rune, outcome, source)
            if signature in seen:
                skipped['doublon_exact'] += 1
                continue
            seen.add(signature)
            accepted[(item, rune)][outcome] += 1
    groups = []
    for (item, rune), counts in sorted(accepted.items()):
        n = sum(counts.values())
        groups.append({
            'equipement': item, 'rune': rune, 'observations': n,
            'suffisant_pour_description': n >= min_samples,
            'comptages': {o: counts[o] for o in OUTCOMES},
            'frequences': {o: round(counts[o]/n, 5) for o in OUTCOMES} if n >= min_samples else None,
            'intervalles_95_wilson': {o: wilson(counts[o], n) for o in OUTCOMES} if n >= min_samples else None,
        })
    return {
        'type': 'audit_observations_reelles',
        'taux_dofus_certifies': False,
        'probabilites_conditionnelles_jet_puits': False,
        'note': 'Fréquences descriptives sur tentatives vérifiées; biais de sélection possibles. Ne pas interpréter comme taux universels.',
        'minimum_observations': min_samples,
        'lignes_acceptees': sum(sum(c.values()) for c in accepted.values()),
        'lignes_exclues': dict(skipped),
        'groupes': groups,
    }


def export_report(input_csv, output_json, *, min_samples=30):
    report = validate_rows(input_csv, min_samples=min_samples)
    dest = Path(output_json)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report
