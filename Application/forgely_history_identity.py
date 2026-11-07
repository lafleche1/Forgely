"""Associate the FIRST equipment heading in the FM history with its result.

DOFUS keeps older equipment blocks below the active block. Reading the last
visible success/failure without its preceding heading would misattribute an
old attempt. This module never infers a new attempt from a static screenshot.
"""
from __future__ import annotations
from dataclasses import dataclass
from difflib import SequenceMatcher
import re
from forgely_item_vision import identify_known, parse_item_header
from forgely_items import key_for
from runeforge_observer import normalized

_OUTCOME = re.compile(r'\b(?:echec|reussite(?:\s+(?:critique|classique|normale?))?|succes(?:\s+(?:critique|normal|neutre))?)\b')
_NOISE = re.compile(r'\b(?:reliquat|vitalite|chance|agilite|intelligence|force|sagesse|resistance|pa|ra)\b')


@dataclass(frozen=True)
class HistoryIdentity:
    name: str | None
    outcome: str | None
    source: str


def names_agree(a, b):
    """Ignore accents and spaces, not real spelling differences."""
    if not a or not b:
        return False
    x, y = key_for(a).replace(' ', ''), key_for(b).replace(' ', '')
    if x == y:
        return True
    # A single OCR substitution in the full heading should not veto two
    # consistent, higher-resolution OCR readings of that same heading.
    return (min(len(x),len(y)) >= 12 and abs(len(x)-len(y)) <= 1
            and SequenceMatcher(None,x,y).ratio() >= .94)



def _same_heading_with_icon_artifact(primary, history_name):
    """Accept a tiny OCR glyph prefix from the icon on the SAME first row.

    In the supplied DOFUS screenshots, the history OCR sometimes reads
    ``Bar ANNEAU DU CYCLOÏDE`` or ``Ban) ANNEAU DU CYCLOÏDE`` while the
    independent name-only crop reads ``ANNEAU DU CYCLOÏDE``. Do not treat
    these as different equipment, but never ignore a real item name prefix.
    """
    if not primary or not history_name:
        return False
    main = key_for(primary)
    observed = key_for(history_name)
    # Restrict this exception to an *entire* matching name at the end of
    # the OCR row. Only 1-4 junk characters may precede it. A different
    # equipment name, or any extra words after the item, remains a conflict.
    if not observed.endswith(main):
        return False
    prefix = observed[:-len(main)]
    return 1 <= len(prefix.strip()) <= 4 and len(prefix.split()) == 1


def _clean_header_line(raw, registered):
    # The icon and delete button sometimes turn into short stray glyphs.
    # Known names can be matched as full tokens even if OCR includes them.
    known = identify_known(raw, registered)
    if known:
        return known
    line = (raw or '').strip()
    line = re.sub(r'^[^\wÀ-ÿ]+', '', line)
    line = re.sub(r'^\d{1,3}\s+', '', line)
    line = re.sub(r'\s+(?:[D]|[|►▣]|\d{1,2})$', '', line)  # delete icon / trailing OCR glyph
    candidate = parse_item_header(line)
    if not candidate:
        return None
    # Do not register 'US ANNEAUDUCYCLOIDE' or other icon OCR garbage as
    # a brand new equipment. The dedicated name-only OCR is preferred.
    parts = candidate.split()
    if len(parts) > 1 and len(parts[0]) <= 2:
        return None
    if len(parts) > 1 and len(parts[-1]) == 1:
        return None
    return candidate


def first_history_item(history_text, registered=()):
    """Find the topmost item block and whether its OWN result is visible.

    An outcome in an older block must never be assigned to the current item.
    No event is emitted: the existing history transition detector does that.
    """
    lines = [s.strip() for s in (history_text or '').splitlines() if s.strip()]
    first_name = None
    for index, line in enumerate(lines):
        folded = normalized(line)
        if _OUTCOME.search(folded):
            if first_name is None:
                return HistoryIdentity(None, None, 'résultat sans en-tête actif')
            return HistoryIdentity(first_name, folded, 'résultat sous le premier objet')
        if first_name is None:
            # If effects/reliquat precede a name, its heading was probably
            # missed; a later item heading is an OLD block, not the active one.
            if index > 2:
                return HistoryIdentity(None, None, 'en-tête actif absent')
            name = _clean_header_line(line, registered)
            if name:
                first_name = name
            elif _NOISE.search(folded):
                return HistoryIdentity(None, None, 'en-tête actif illisible')
        else:
            if _clean_header_line(line, registered):
                return HistoryIdentity(first_name, None, 'nouveau bloc historique avant résultat')
    return HistoryIdentity(first_name, None, 'en-tête visible, résultat non lu' if first_name else 'aucun en-tête')


def resolve_history_identity(image, history_text, ocr, registered):
    """Return (known, candidate, raw, history_evidence).

    Priority: OCR of the FIRST row (2 views), then first history heading
    only if an outcome belongs to that same heading. Conflicts are rejected.
    """
    from forgely_item_vision import recognize_item_header
    known, candidate, raw = recognize_item_header(image, ocr, registered)
    evidence = first_history_item(history_text, registered)
    primary = known or candidate
    if primary:
        # A history reading of the SAME row is useful corroboration. If it
        # contradicts the dedicated row OCR, never auto-register either name.
        if evidence.name and not (names_agree(primary, evidence.name)
                                  or _same_heading_with_icon_artifact(primary, evidence.name)):
            return None, None, raw, HistoryIdentity(None, None, 'conflit en-tête / historique')
        return known, candidate, raw, evidence
    if evidence.name and evidence.outcome:
        matched = identify_known(evidence.name, registered)
        # Without the dedicated high-resolution heading OCR, never create a
        # novel one-word item or a space-less OCR concatenation. A known item
        # can still be recovered by its canonical registered name.
        if matched:
            return matched, None, raw, evidence
        if len(evidence.name.split()) >= 2:
            return None, evidence.name, raw, evidence
    return None, None, raw, evidence


def visible_history_names(history_text, registered=()):
    """Names visible anywhere, for diagnostics ONLY (may be stale)."""
    names = []
    for line in (history_text or '').splitlines():
        name = _clean_header_line(line, registered)
        if name and key_for(name) not in {key_for(n) for n in names}:
            names.append(name)
    return names


def latest_visible_history_name(history_text, registered=()):
    """Last visible heading in chronological DOFUS history, as a CANDIDATE only.

    Never certifies the equipped item: historical rows can remain on screen
    after replacing the equipment. Callers need independent current-slot proof.
    """
    names = visible_history_names(history_text, registered)
    return names[-1] if names else None
