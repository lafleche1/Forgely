"""Community-guide rules for DOFUS 3; NOT an official success formula.

Source: https://huzounet.fr/guides/forgemagie (updated 2026-09-30).
Synthetic outcomes must NEVER enter observations in the player database.
"""
from __future__ import annotations
from dataclasses import dataclass

GUIDE_URL = "https://huzounet.fr/guides/forgemagie"
GUIDE_DATE = "2026-09-30"
HEAVY_EXO_THRESHOLD = 20.0  # guide says strictly >20 density
EXTRA_DENSITY_LIMIT = 101.0  # community guide: cap to verify in current game

@dataclass(frozen=True)
class GuideResult:
    label: str
    sc_pct: float | None
    sn_pct: float | None
    ec_pct: float | None
    provenance: str
    note: str


def classify_attempt(*, natural_present: bool | None, current: float | None,
                     natural_max: float | None, proposed: float | None) -> str:
    """Classify the PROPOSED jet; missing natural-range knowledge => unknown."""
    if natural_present is None or proposed is None:
        return "inconnu"
    if not natural_present:
        return "exo" if proposed > 0 else "absent"
    if natural_max is None:
        return "inconnu"
    return "over" if proposed > natural_max else "fm_classique"


def exo_success_reference(*, natural_present: bool | None, rune_density: float | None) -> GuideResult:
    """The guide's narrow >20 exotic exception, not odds for ALL runes."""
    if natural_present is False and rune_density is not None and rune_density > HEAVY_EXO_THRESHOLD:
        return GuideResult("exo_lourd", 1., 0., 99., "guide_communautaire_Huzounet",
                           "Guide: pour une rune >20 sur une ligne absente naturellement, 1 % SC et aucun SN. À confirmer en jeu.")
    return GuideResult("non_documente", None, None, None, "aucune_formule_officielle",
                       "Pas de pourcentage vérifié pour cette situation ; utiliser des observations comparables.")


def reliquat_gain(*, lost_density: float, rune_density: float, current_reliquat: float = 0.) -> float:
    """Estimate surplus from confirmed losses; never infer actual SC/SN/EC from this."""
    if min(lost_density,rune_density,current_reliquat) < 0:
        raise ValueError("Densité et reliquat non négatifs requis")
    return max(0.,current_reliquat + lost_density - rune_density)


def priority_note(*, target_ratio: float | None, rune_density: float | None,
                  reliquat: float | None) -> str:
    """Qualitative priority; never convert heuristics into invented success %s."""
    fragments=[]
    if target_ratio is not None and target_ratio >= 1.:
        fragments.append("jet après rune proche du maximum naturel : passage potentiellement plus difficile")
    if rune_density is not None and reliquat is not None:
        fragments.append("reliquat inférieur au poids de la rune : le jet est davantage exposé" if reliquat < rune_density
                         else "reliquat suffisant pour absorber une dépense de ce poids, sans garantir le passage")
    return "; ".join(fragments) or "Contexte insuffisant pour qualifier la priorité."


def strategic_context(item_type: str) -> str:
    return {
        "concessions": "Prévoir des compromis entre lignes si aucun gros puits n'est disponible.",
        "puits": "Profiter prudemment du reliquat si une ligne lourde chute, puis envisager sa restauration.",
        "brisage": "Stratégie à haut risque : ne pas supposer un puits disponible sans perte confirmée.",
    }.get(item_type, "Type d'équipement non caractérisé ; pas de stratégie spécifique.")
