"""Conservative screen-history transition tracking for Forgely (local only).

A changing OCR string is not sufficient proof of a new attempt. Count only a
stable change with a *shift* of previously observed history rows; otherwise
report an uncertain reading. Missing rune/outcome never enters probabilities.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import time
import unicodedata


def norm(value):
    txt = unicodedata.normalize('NFKD', value or '')
    txt = ''.join(c for c in txt if not unicodedata.combining(c))
    txt = txt.lower().replace('œ', 'oe')
    return re.sub(r'\s+', ' ', txt).strip()


def is_empty_history(text):
    """An explicit empty-history banner is valid evidence, not OCR failure."""
    t = norm(text).replace('’', "'")
    return bool(re.search(r"(?:il n[' ]?y a pas d[' ]?historique|aucun historique|historique actuellement vide)", t))


def rows_of(text):
    return tuple(v for line in text.splitlines() if (v := norm(line)) and len(v) <= 95)[:12]


def explicit_outcome(line):
    txt = norm(line)
    if re.search(r'\b(?:succes|reussite)\s+critique\b', txt):
        return 'SC'
    if re.search(r'\b(?:succes|reussite)\s+(?:neutre|normal|classique)\b', txt):
        return 'SN'
    if re.search(r'\bechec\b', txt):
        return 'EC'
    return None


def newest_history(text):
    rows = rows_of(text)
    return explicit_outcome(rows[0]) if rows else None


def history_signature(text):
    return rows_of(text)[:8]


def normalize_rune_name(text, known):
    from runeforge_observer import find_rune
    return find_rune(text, known)


def new_row_shift(old, new):
    """Number of new rows if old prefix is found below the top of new rows.

    Need two overlapping lines to distinguish a genuine push from OCR jitter or
    a player scrolling through the history. If old rows repeat identically,
    require 3 matching rows where possible; never infer from only one row.
    """
    if len(old) < 2 or len(new) < 3:
        return 0
    # In DOFUS the active equipment heading stays at row 0, while its
    # newest rune result is inserted at row 1. Previous results move down.
    # Never treat a newly appearing/different heading as a result itself.
    if old[0] == new[0] and not explicit_outcome(old[0]):
        for shift in (1, 2, 3, 4):
            overlap = min(4, len(old)-1, len(new)-1-shift)
            if overlap >= 2 and new[1+shift:1+shift+overlap] == old[1:1+overlap]:
                return shift
        return 0
    for shift in (1, 2, 3, 4):
        overlap = min(4, len(old), len(new) - shift)
        if overlap < 2:
            continue
        if new[shift:shift + overlap] == old[:overlap]:
            # Prevent treating mere scrolling up / history reordering as event.
            # We still need the header to classify as an explicit new result.
            return shift
    return 0


@dataclass(frozen=True)
class Observation:
    rune: str | None
    outcome: str | None
    evidence: str
    confidence: str
    reason: str = ''


class HistoryTransitionTracker:
    def __init__(self, rune_names, rune_valid_seconds=8):
        self.rune_names = tuple(rune_names)
        self.rune_valid_seconds = rune_valid_seconds
        self.baseline = None
        self.pending_signature = None
        self.pending_count = 0
        self.recent_rune = None
        self.recent_rune_time = -1e10
        self.seen_changes = 0
        self.quarantined = 0
        self.saved = 0
        self.ignored_changes = 0
        self.reason = 'En attente du premier historique stable'
        self._init_candidate = None
        self._init_count = 0

    def invalidate_rune(self):
        """Prevent reuse of a previously-selected rune when visual input is ambiguous."""
        self.recent_rune = None
        self.recent_rune_time = -1e10

    def remember_rune(self, rune_text, now=None):
        now = time.monotonic() if now is None else now
        rune = normalize_rune_name(rune_text, self.rune_names)
        if rune:
            self.recent_rune, self.recent_rune_time = rune, now
        return rune

    def observe(self, history_text, rune_text='', now=None):
        now = time.monotonic() if now is None else now
        self.remember_rune(rune_text, now)
        # Empty workshop history is a legitimate stable state. It cannot
        # represent a rune attempt and must not be classified as unreadable.
        if is_empty_history(history_text):
            self.baseline = None
            self.pending_signature = None
            self.pending_count = 0
            self._init_candidate = None
            self._init_count = 0
            self.reason = 'Historique vide confirmé : attente de la première tentative'
            return None
        signature = history_signature(history_text)
        if signature and not any(explicit_outcome(row) for row in signature):
            # Stat deltas are handled by HistoryDeltaMonitor. Repeatedly
            # confirming their OCR cannot produce evidence of an outcome.
            self.baseline = None
            self.pending_signature = None
            self.pending_count = 0
            self._init_candidate = None
            self._init_count = 0
            self.reason = 'Variations visibles · aucun résultat SC/SN/EC explicite'
            return None
        if len(signature) < 2:
            self.reason = 'Historique illisible ou atelier fermé'
            return None
        if self.baseline is None:
            if signature != self._init_candidate:
                self._init_candidate, self._init_count = signature, 1
                self.reason = 'Initialisation : lecture de référence (1/2)'
                return None
            self._init_count += 1
            if self._init_count >= 2:
                self.baseline = signature
                self.reason = 'Référence créée : attente d’une nouvelle fusion'
            return None
        if signature == self.baseline:
            self.pending_signature = None
            self.pending_count = 0
            self.reason = 'Aucun nouvel événement dans l’historique'
            return None
        if signature != self.pending_signature:
            self.pending_signature = signature
            self.pending_count = 1
            self.reason = 'Historique modifié : confirmation en cours (1/2)'
            return None
        self.pending_count += 1
        if self.pending_count < 2:
            return None
        old = self.baseline
        self.baseline = signature
        self.pending_signature = None
        self.pending_count = 0
        shift = new_row_shift(old, signature)
        if not shift:
            self.ignored_changes += 1
            self.reason = 'Historique différent mais aucune nouvelle ligne fiable (OCR ou défilement)'
            return None
        # With a fixed equipment heading, the inserted result is the first
        # row BELOW it. Older historical results must not be counted.
        header_retained = old[0] == signature[0] and not explicit_outcome(signature[0])
        outcome = explicit_outcome(signature[1] if header_retained else signature[0])
        if not outcome:
            self.ignored_changes += 1
            self.reason = 'Nouvelle ligne, mais SC/SN/EC non explicite : pas de supposition'
            return None
        self.seen_changes += 1
        rune = self.recent_rune if now - self.recent_rune_time <= self.rune_valid_seconds else None
        evidence = '\n'.join(history_text.splitlines()[:8])[:350]
        if not rune:
            self.quarantined += 1
            self.reason = 'Résultat nouveau confirmé, rune illisible : conservé hors statistiques'
            return Observation(None, outcome, evidence, 'incomplète', self.reason)
        self.saved += 1
        self.reason = 'Nouvel événement reconnu : rune et résultat lisibles'
        return Observation(rune, outcome, evidence, 'OCR à vérifier', self.reason)


def crop_regions(image):
    """Positions de départ calibrées sur la capture utilisateur 1920x1080.

    La fenêtre DOFUS doit être maximisée ou approximativement de mêmes
    proportions ; en cas de changement d'échelle, reconfigurer les régions.
    """
    w, h = image.size
    # Colonne HISTORIQUE dans l'atelier, exclude la barre de quêtes.
    history = image.crop((int(w*.162), int(h*.225), int(w*.293), int(h*.450)))
    # Seulement le haut de la fenêtre d'atelier : bouton de rune + infobulle
    # éventuelle ; une icône seule ne peut pas être lue comme texte.
    selected = image.crop((int(w*.310), int(h*.155), int(w*.537), int(h*.290)))
    return history, selected


def read_regions(image, tesseract_executable=''):
    from runeforge_observer import extract_text
    history, selected = crop_regions(image)
    return (extract_text(history, tesseract_executable),
            extract_text(selected, tesseract_executable))
