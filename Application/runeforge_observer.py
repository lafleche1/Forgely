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
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError('OCR manquant : installe pytesseract avec installer.bat') from exc
    if tesseract_cmd.strip():
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd.strip()
    else:
        import shutil
        from pathlib import Path
        import os
        known = Path('C:/Program Files/Tesseract-OCR/tesseract.exe')
        user_known = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Tesseract-OCR' / 'tesseract.exe'
        x86_known = Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Tesseract-OCR' / 'tesseract.exe'
        if shutil.which('tesseract'):
            pytesseract.pytesseract.tesseract_cmd = shutil.which('tesseract')
        elif known.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(known)
        elif user_known.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(user_known)
        elif x86_known.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(x86_known)
    import os
    tessdir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Forgely', 'tessdata')
    if os.path.isfile(os.path.join(tessdir, 'fra.traineddata')) and os.path.isfile(os.path.join(tessdir, 'eng.traineddata')):
        os.environ['TESSDATA_PREFIX'] = tessdir
    try:
        from PIL import ImageOps, ImageEnhance
        gray = ImageOps.grayscale(image)
        if gray.width < 1250:
            gray = gray.resize((gray.width*2, gray.height*2))
        gray = ImageEnhance.Contrast(gray).enhance(2)
        return pytesseract.image_to_string(gray, lang='fra+eng', config='--psm 7' if getattr(image, 'info', {}).get('forgely_title') else '--psm 6')
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError('Tesseract absent. Installe le logiciel Tesseract pour Windows.') from exc
    except pytesseract.TesseractError:
        try:
            return pytesseract.image_to_string(image, lang='eng', config='--psm 6')
        except pytesseract.TesseractError as exc:
            raise RuntimeError('Tesseract ne peut pas lire cette capture.') from exc
