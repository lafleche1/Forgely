"""Référence documentaire indicative; ne produit aucune probabilité de SC/SN/EC."""
from __future__ import annotations
import csv
from pathlib import Path

FICHIER = Path(__file__).with_name('reference_poids_fm.csv')

def poids_documentaires():
    with FICHIER.open(encoding='utf-8', newline='') as f:
        return {r['caracteristique']: r for r in csv.DictReader(f)}

def poids_indicatif(caracteristique, quantite=1):
    """Valeur documentaire NON certifiée DOFUS 3; jamais un taux de succès."""
    if quantite < 0: raise ValueError('quantite doit etre positive')
    r = poids_documentaires().get(caracteristique)
    if r is None: return None
    return {'poids':float(r['poids_par_point_indicatif'])*quantite,
            'certifie_dofus3':False, 'statut':r['statut'], 'sources':r['sources'].split(';')}

def probabilite_sc_sn_ec(*args, **kwargs):
    """Pas de données d'essais observés dans les guides publics."""
    return None
