"""Registre de preuves et calculs de risque, séparés des observations DOFUS 3.

Une source communautaire ou Rétro n'est jamais transformée en mesure DOFUS 3.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from math import log1p, expm1, isfinite

@dataclass(frozen=True)
class Evidence:
    code: str
    source: str
    url: str
    version: str
    nature: str
    proposition: str
    utilisation: str

EVIDENCES = (
    Evidence('retro_2009', 'Devblog 1.27 repris par Dofus Fashionista',
             'https://dofusfashionista.gg/fr/retro/forgemagie/', 'DOFUS Rétro',
             'historique', 'Six scénarios SC/SN/EC publiés pour un ancien système.',
             'comparaison_historique_uniquement'),
    Evidence('exo_lourd', 'Gamosaurus',
             'https://www.gamosaurus.com/jeux/dofus/forgemagie-le-guide-complet-dofus',
             'DOFUS non daté précisément', 'communaute',
             'Exo PA/PM lourd présenté avec 1 % de succès critique.',
             'scenario_illustratif_non_calibrant'),
    Evidence('puits', 'JeuxOnline',
             'https://dofus.jeuxonline.info/article/3736/forgemagie',
             'DOFUS historique', 'guide',
             'Le poids et le puits influencent les pertes; la formule des probabilités n’est pas publiée.',
             'caracteristiques_de_contexte'),
    Evidence('jet_global', 'Tofus', 'https://www.tofus.fr/fiches/forgemagie',
             'DOFUS historique', 'guide',
             'Poids de rune, qualité de jet, poids total et niveau d’objet cités comme facteurs.',
             'variables_candidates_a_valider'),
    Evidence('quatre_issues', 'Communauté DOFUS France',
             'https://www.reddit.com/r/DOFUS_FRANCE/comments/1hv0t9w',
             'DOFUS moderne, témoignage', 'temoignage',
             'Mention de l’échec neutre EN en plus de SC/SN/EC.',
             'audit_de_nomenclature_avant_entrainement'),
    Evidence('video_ml', 'Communauté DOFUS France',
             'https://www.reddit.com/r/DOFUS_FRANCE/comments/1xbfl2r/forgemagie_en_ligne/',
             'DOFUS moderne, témoignage 2026', 'temoignage',
             'Séparation du modèle d’issue et du modèle de pertes après tentative.',
             'hypothese_de_recherche_non_validee'),
    Evidence('serveur_prive', 'Lethaline', 'https://lethaline.com/wiki/lethaline/forgemagie',
             'Serveur privé Rétro', 'hors_perimetre',
             'Probabilités propres au serveur et bonus pack; non transférables.',
             'exclure_des_priors_dofus3'),
)

def catalogue():
    return [asdict(e) for e in EVIDENCES]

def probabilite_au_moins_un_succes(p: float, tentatives: int) -> float:
    """Hypothèse: tentatives indépendantes avec probabilité CONSTANTE p.
    Ne modélise pas les pertes de jet ni le réajustement des probabilités.
    """
    if not isinstance(tentatives,int) or isinstance(tentatives,bool) or tentatives<0:
        raise ValueError('Nombre de tentatives invalide')
    if not isfinite(p) or not 0<=p<=1:
        raise ValueError('Probabilité invalide')
    if p==1: return float(tentatives>0)
    return -expm1(tentatives*log1p(-p))

def tentatives_pour_chance(p: float, cible: float) -> int | None:
    """Seuil de tentatives sous hypothèse de tirages indépendants constants."""
    from math import ceil
    if not isfinite(p) or not isfinite(cible) or not 0<=p<=1 or not 0<cible<1:
        raise ValueError('Paramètres invalides')
    if p==0: return None
    if p==1: return 1
    return ceil(log1p(-cible)/log1p(-p))

def cout_moyen_jusqu_au_succes(p: float, cout_tentative: float) -> float | None:
    """Coût des runes seulement; exclut réparations du jet, sous p constant."""
    if not isfinite(p) or not 0<=p<=1 or not isfinite(cout_tentative) or cout_tentative<0:
        raise ValueError('Paramètres invalides')
    return cout_tentative/p if p else None

def exemple_exo_lourd(tentatives=100):
    """Illustration du taux communautaire de 1 %, PAS une estimation DOFUS 3."""
    return {'hypothese_sc':0.01, 'tentatives':tentatives,
            'au_moins_un_sc':probabilite_au_moins_un_succes(.01,tentatives),
            'portee':'scenario communautaire illustratif, tirages independants et p constant',
            'source':'exo_lourd', 'estimation_dofus3':False}
