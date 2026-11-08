"""Source-aware DOFUS 3 FM facts; no probabilities fabricated from web guides.
Knowledge is kept distinct from real observations and synthetic simulations.
"""
from __future__ import annotations
from dataclasses import dataclass

GAME_SCOPE = 'DOFUS PC — règles communautaires, pas DOFUS Rétro/Touch'
CHECKED_ON = '2026-11-07'

SOURCES = {
 'huzounet': 'https://huzounet.fr/guides/forgemagie',
 'gamosaurus': 'https://www.gamosaurus.com/jeux/dofus/forgemagie-le-guide-complet-dofus',
 'dofuspourlesnoobs': 'https://www.dofuspourlesnoobs.com/guide-forgemagie.html',
 'fashionista': 'https://dofusfashionista.gg/fr/forgemagie/',
 'jeuxonline': 'https://dofus.jeuxonline.info/article/3736/forgemagie',
 'wiki': 'https://www.wiki-dofus.eu/w/Forgemagie',
 'dofocus': 'https://www.dofocus.fr/guide/',
 'dofocus_about': 'https://www.dofocus.fr/about/',
 'dofusdb': 'https://beta.dofusdb.fr/en/database/objects',
 'portals': 'https://dofus-portals.fr/forgemagie/',
 'client_extraction': 'https://github.com/ledouxm/dofus-sqlite/releases/tag/v6.0_3.7.13.17',
}

@dataclass(frozen=True)
class Fact:
    key: str
    statement: str
    sources: tuple[str,...]
    confidence: str
    scope: str = 'fm'

FACTS = (
 Fact('runtime_weights', 'Les densités actives proviennent d’une extraction tierce du client 3.7.13.17, datée et vérifiée par empreintes des fichiers ; elles ne sont pas certifiées par une publication officielle Ankama. La Signature reste hors combat.', ('client_extraction',), 'donnees_client_extraites_non_certifiees_editeur'),
 Fact('outcomes', 'SC ajoute sans perte ; SN ajoute avec pertes possibles ; EC ne donne pas le bonus et peut dégrader le jet.', ('fashionista','jeuxonline'), 'communautaire_concordant'),
 Fact('weight', 'Poids de la rune = quantité ajoutée × poids unitaire de la caractéristique.', ('jeuxonline','dofuspourlesnoobs'), 'communautaire_concordant'),
 Fact('pool', 'Le reliquat résulte des pertes de poids excédentaires et peut absorber des pertes futures ; ne pas le confondre avec les manques au jet parfait.', ('jeuxonline','fashionista'), 'communautaire_concordant'),
 Fact('exo_over', 'Une ligne absente du jet naturel est un exo ; une ligne au-dessus de sa borne naturelle est un over. Bornes documentées indispensables.', ('fashionista','jeuxonline'), 'communautaire_concordant'),
 Fact('cap101', 'Over : densité totale de la ligne limitée à 101 hors jet naturel supérieur ; exos : densité cumulée limitée à 101. Ne pas additionner tous les surplus d’over comme un plafond global.', ('huzounet','gamosaurus'), 'communautaire_concordant'),
 Fact('sc_pool', 'Un succès critique ajoute le bonus sans consommer le reliquat ; un reliquat suffisant ne garantit pas le succès.', ('huzounet','gamosaurus'), 'communautaire_concordant'),
 Fact('tier20', 'Le repère 20 fois le gain de la rune guide le choix simple/Pa/Ra ; ce n’est ni une probabilité ni une interdiction de pose.', ('gamosaurus',), 'heuristique_communautaire'),
 Fact('balance', 'Remonter progressivement les lignes et éviter de finaliser trop tôt une ligne peut faciliter le travail sur les autres ; pas d’ordre universel de runes.', ('huzounet',), 'heuristique_communautaire'),
 Fact('finish', 'Les overs et exos sont fragiles lors des poses suivantes ; tenir compte des lignes restant à restaurer avant une finition.', ('huzounet','gamosaurus'), 'communautaire_concordant'),
 Fact('malus', 'Les lignes négatives exigent des règles propres et des bornes signées ; le moteur positif doit suspendre leur traitement plutôt que les convertir en bonus ordinaires.', ('huzounet',), 'limite_du_modele'),
 Fact('transcendence', 'La transcendance est une finition qui empêche la FM ultérieure ; vérifier ses conditions spécifiques, distinctes des runes ordinaires.', ('huzounet','gamosaurus'), 'communautaire_concordant'),
 Fact('probabilities', 'Les probabilités de SC/SN/EC dépendent du contexte ; ne pas extrapoler un taux fixe à toutes les runes.', ('fashionista','jeuxonline'), 'prudence_methodologique'),
 Fact('session_pool', 'La persistance du reliquat entre changements de session ou manipulations d’objet doit être vérifiée sur DOFUS 3.', ('fashionista','jeuxonline'), 'incertain'),
 Fact('focus', 'Le focus et le coefficient serveur concernent le BRISAGE, pas la probabilité SC/SN/EC de pose de rune.', ('dofocus',), 'source_explicite', 'brisage'),
 Fact('catalogue', 'Les données d’objets et de runes peuvent être croisées avec DofusDB ; dater et versionner chaque extraction.', ('dofocus_about','dofusdb'), 'source_explicite', 'donnees'),
)

# Divergences identifiées dans les guides : aucune correction silencieuse.
CONFLICTS = {
 'rune_vi': {'issue': 'Un tableau récent affiche une entrée Vi incohérente avec les tableaux classiques (+5 vita, poids 1).', 'sources': ('dofuspourlesnoobs','jeuxonline','client_extraction'), 'policy':'utiliser le référentiel client versionné (+5, poids 1), préserver la provenance non certifiée éditeur ; ne pas importer la valeur ambiguë du guide'},
 'resistances_fixes': {'issue': 'Certains guides attribuent 2 par point de résistance fixe, un autre tableau emploie 6 ; vérifier le type exact de résistance.', 'sources': ('wiki','portals'), 'policy':'ne jamais remplacer la table de poids sans vérification de l’intitulé et du jeu'},
 'puit_estime': {'issue': 'Le manque au jet parfait ne constitue pas en soi le reliquat réel disponible.', 'sources': ('fashionista','jeuxonline'), 'policy':'reliquat non lu = inconnu, jamais déduit du jet'},
 'wax': {'issue': 'Un wiki de serveur alternatif utilise des règles propres au serveur.', 'sources': (), 'policy':'exclure des paramètres de DOFUS officiel'},
}

def advice_context(*, natural_max_known:bool, pool_confirmed:bool, kind:str, rune_weight:float|None):
    """Contextual risk notes, no synthetic success probability."""
    notes=[]
    if not pool_confirmed:
        notes.append('Reliquat non confirmé : conseil suspendu.')
    if not natural_max_known:
        notes.append('Bornes naturelles inconnues : over/exo non vérifiable.')
    if kind in ('exo','over'):
        notes.append('Dépassement du jet naturel : vérifier la densité totale de la ligne over et la densité cumulée des exos.')
    if rune_weight is not None and rune_weight >= 30:
        notes.append('Rune lourde : perte potentiellement coûteuse pour les autres lignes ; probabilité exacte non connue.')
    return tuple(notes)

def sources_for(key):
    for fact in FACTS:
        if fact.key==key:return tuple(SOURCES[k] for k in fact.sources)
    raise KeyError(key)
