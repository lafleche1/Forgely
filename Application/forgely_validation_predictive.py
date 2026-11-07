"""Validation chronologique hors échantillon des probabilités FM.

Pas d'entraînement sur simulations. Aucun taux affiché sans groupe suffisamment
fourni; le jet est comparé exactement (texte normalisé), sans supposer de bornes.
"""
from __future__ import annotations
import csv, math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from forgely_probabilites_conditionnelles import FIELDS, TYPES, _number, _pool_band, _weight_band
from forgely_validation import VERIFIED_SOURCES, OUTCOMES, wilson


def _date(value):
    try:
        return datetime.fromisoformat(value.strip().replace('Z','+00:00')).timestamp()
    except (ValueError, OverflowError, AttributeError):
        return None


def _key(row):
    pool=_number(row['puits_avant']); weight=_number(row['poids_rune'])
    if pool is None or weight is None:return None
    return (row['equipement'].strip(),row['rune'].strip(),row['type_fm'].strip(),
            _pool_band(pool),_weight_band(weight),' '.join(row['jet_avant'].split()))


def validate_temporal(path, *, train_fraction=.8, minimum=50):
    """Holdout chronologique global; prédictions uniquement sur états exacts déjà vus.

    Brier multiclasses 0=parfait, 2=pire; logloss plus faible = meilleur.
    N'affirme aucune validité si le jeu de test est vide ou non couvert.
    """
    if not .5 <= train_fraction < 1:raise ValueError('Fraction invalide')
    if not 1 <= minimum <= 100000:raise ValueError('Minimum invalide')
    accepted=[]; rejected=Counter(); seen=set()
    with Path(path).open(encoding='utf-8-sig',newline='') as handle:
        reader=csv.DictReader(handle)
        if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError('Colonnes manquantes')
        for row in reader:
            if (row['source'] or '').strip() not in VERIFIED_SOURCES:
                rejected['source_non_verifiee']+=1;continue
            outcome=(row['resultat'] or '').strip().upper()
            date=_date(row['date_utc'] or '')
            if (not row['equipement'].strip() or not row['rune'].strip() or
                not row['jet_avant'].strip() or row['type_fm'].strip() not in TYPES or
                outcome not in OUTCOMES or date is None):
                rejected['contexte_incomplet']+=1;continue
            key=_key(row)
            if key is None:
                rejected['contexte_incomplet']+=1;continue
            signature=(date,key,outcome,row['source'].strip())
            if signature in seen:
                rejected['doublon']+=1;continue
            seen.add(signature)
            accepted.append((date,key,outcome))
    accepted.sort(key=lambda r:r[0])
    cutoff=int(len(accepted)*train_fraction)
    train,test=accepted[:cutoff],accepted[cutoff:]
    counts=defaultdict(Counter)
    for _,key,outcome in train:counts[key][outcome]+=1
    predicted=0; brier=0.; logloss=0.; per_outcome=Counter(); per_key=Counter()
    for _,key,outcome in test:
        c=counts.get(key)
        if not c or sum(c.values())<minimum:continue
        n=sum(c.values())
        # Empirical estimator; Laplace smoothing avoids infinite logloss.
        probabilities={o:(c[o]+1)/(n+3) for o in OUTCOMES}
        brier+=sum((probabilities[o]-(o==outcome))**2 for o in OUTCOMES)
        logloss-=math.log(probabilities[outcome])
        predicted+=1;per_outcome[outcome]+=1;per_key[key]+=1
    return {'type':'validation_chronologique_hors_echantillon',
            'observations_verifiees':len(accepted),'entrainement':len(train),
            'test':len(test),'test_couvert':predicted,
            'couverture':round(predicted/len(test),5) if test else None,
            'brier_multiclasse':round(brier/predicted,6) if predicted else None,
            'logloss':round(logloss/predicted,6) if predicted else None,
            'groupes_couverts':len(per_key),'rejets':dict(rejected),
            'minimum_par_contexte':minimum,'fraction_entrainement':train_fraction,
            'validation_suffisante':predicted>=50,
            'note':'Evaluation hors echantillon, sans fuite temporelle; jet exact. Aucune garantie de calibration. Ne pas activer dans les conseils sans tests de calibration et representativite.'}
