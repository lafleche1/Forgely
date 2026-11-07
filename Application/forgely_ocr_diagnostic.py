"""Conservative, explainable health report for live OCR; no invented confidence score."""
from dataclasses import dataclass

SECTIONS = ('HISTORIQUE', 'EFFETS', 'RUNES (Pa / Ra)', 'RELIQUAT', 'VISION')

@dataclass(frozen=True)
class Diagnostic:
    level: str
    reasons: tuple[str, ...]
    sections: dict[str, str]


def evaluate(raw: str, *, running: bool, item_verified: bool,
             jet_verified: bool, rune_conflict: bool = False) -> Diagnostic:
    raw = raw or ''
    sections = {}
    for index, heading in enumerate(SECTIONS):
        marker = heading + '\n'
        if marker not in raw:
            sections[heading] = ''
            continue
        tail = raw.split(marker, 1)[1]
        next_headers = [tail.find('\n' + h + '\n') for h in SECTIONS[index + 1:]]
        ends = [p for p in next_headers if p >= 0]
        sections[heading] = tail[:min(ends)].strip() if ends else tail.strip()
    reasons = []
    if not running:
        reasons.append('Observateur arrêté : aucune lecture en direct.')
    if not raw.strip():
        reasons.append('Aucune lecture OCR reçue.')
    if not item_verified:
        reasons.append('Équipement non confirmé sur plusieurs images.')
    if not jet_verified:
        reasons.append('Jet et puits non stabilisés sur plusieurs images.')
    if not sections['HISTORIQUE']:
        reasons.append('Historique des tentatives illisible ou absent.')
    if not sections['EFFETS']:
        reasons.append('Caractéristiques illisibles ou absentes.')
    if not sections['RUNES (Pa / Ra)']:
        reasons.append('Zone des runes illisible ou absente.')
    if rune_conflict or 'CONFLIT OCR / icône' in sections['VISION']:
        reasons.append('Conflit entre reconnaissance du texte et de l’icône.')
    # No numerical OCR accuracy is inferred from non-calibrated text.
    level = 'À VÉRIFIER' if reasons else 'LECTURES DISPONIBLES (non certifiées)'
    return Diagnostic(level, tuple(reasons), sections)
