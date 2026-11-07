"""Conservative local OCR event extraction for DOFUS forgemagie.

No network requests, no AI, no mouse/keyboard actions. Only unambiguous
rune + outcome pairs can become candidates. This is not guaranteed to read
DOFUS's actual UI until screen captures have been evaluated.
"""
from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass


def normalized(s: str) -> str:
    s = unicodedata.normalize('NFKD', s or '')
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r'\s+', ' ', s).strip()

PATTERNS = {
    'SC': (r'\bsucces\s+critique\b', r'\bcritical\s+success\b'),
    'SN': (r'\bsucces\s+neutre\b', r'\bsucces\s+normal\b'),
    'EC': (r'\bechec\s+critique\b', r'\bechec\b', r'\bfailure\b'),
}


def find_outcome(ocr_text: str):
    s = normalized(ocr_text)
    hits = {k for k, ps in PATTERNS.items() if any(re.search(p, s) for p in ps)}
    return next(iter(hits)) if len(hits) == 1 else None


def find_rune(ocr_text: str, rune_names):
    """Require explicit 'rune' prefix to avoid confusing item stats for uses.

    Conflicting rune mentions are rejected; do not guess from selection UI.
    """
    s = normalized(ocr_text)
    names = sorted(rune_names, key=len, reverse=True)
    matched = []
    for rune in names:
        name = normalized(rune)
        # Allow multiple spaces, but never match 'Vi' inside 'Ra Vi'.
        body = r'\s+'.join(re.escape(part) for part in name.split())
        pat = rf'\brune\s+(?:de\s+)?{body}\b'
        if re.search(pat, s):
            matched.append(rune)
    return matched[0] if len(matched) == 1 else None


@dataclass(frozen=True)
class Candidate:
    outcome: str
    rune: str | None
    evidence: str


class OutcomeTracker:
    """Detect transitions in OCR; drop identical persistent states.

    A repeated identical event without an intervening blank is not detectable
    with OCR polling alone. Context is captured only if rune + outcome coexist.
    """
    def __init__(self, rune_names=()):
        self.last_visible = None
        self.rune_names = tuple(rune_names)

    def observe(self, text: str):
        outcome = find_outcome(text)
        if outcome is None:
            self.last_visible = None
            return None
        rune = find_rune(text, self.rune_names)
        signature = (outcome, rune)
        if signature == self.last_visible:
            return None
        self.last_visible = signature
        return Candidate(outcome=outcome, rune=rune,
                         evidence=' '.join(text.split())[:350])


def extract_text(image, tesseract_cmd=''):
    # One shared cache also coalesces simultaneous preview/observer requests.
    from forgely_ocr_backend import extract_text as recognize
    return recognize(image, tesseract_cmd)
