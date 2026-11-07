"""Conservative equipment recognition from text visible in the DOFUS workshop.

Only registered names can be automatically activated. OCR guesses cannot create
items. Fuzzy correction is restricted to a single, clearly distinct known name.
"""
from __future__ import annotations
import re
import csv
from functools import lru_cache
from pathlib import Path
from difflib import SequenceMatcher
from forgely_items import key_for



@lru_cache(maxsize=1)
def official_names():
    """DOFUS catalogue; no OCR-derived names are inserted into it."""
    path = Path(__file__).with_name('catalogue_objets_noms_fr.csv')
    if not path.exists():
        return ()
    with path.open(encoding='utf-8-sig', newline='') as f:
        return tuple(dict.fromkeys(row['nom_fr'].strip() for row in csv.DictReader(f, delimiter=';')
                                   if row.get('nom_fr', '').strip()))


@lru_cache(maxsize=1)
def _normalized_official_names(names):
    return tuple((key_for(name),name) for name in names)


def match_truncated_official_name(text):
    """Match a left-cropped workshop heading only when the suffix is unique.

    Example: 'AU DU CYCLOÏDE' -> 'Anneau du Cycloïde'. Requires a long,
    multiword suffix; never accepts generic fragments or rune/history text.
    """
    results = set()
    for line in (text or '').splitlines():
        if '[contrôle]' in line:
            line = line.partition(']')[2]
        fragment = key_for(line.strip(' []:;.,-'))
        if len(fragment) < 11 or len(fragment.split()) < 3:
            continue
        for target,name in _normalized_official_names(official_names()):
            if len(target) > len(fragment) and target.endswith(fragment) and len(fragment) / len(target) >= .62:
                results.add(name)
        if len(results) > 1:
            return None
    return next(iter(results)) if len(results) == 1 else None

def crop_item_header(image):
    """Crop the CURRENT item name at the top of the workshop history panel.

    On the 1648x928 DOFUS reference, the selected item's name appears in
    the first history row (roughly x=300..455, y=255..280), *not* in the
    profession/character header. Keep the crop short so previous items and
    history entries cannot be mistaken for the selected equipment.
    """
    w, h = image.size
    return image.crop((round(w * .175), round(h * .270),
                       round(w * .275), round(h * .300)))


def parse_item_header(text):
    """Extract a plausible name from the single current-item header line.

    This is only a candidate: never treat a single OCR reading as a verified
    item. The caller must check a second OCR preprocessing and several frames.
    """
    import unicodedata
    excluded = ('reliquat', 'echec', 'succès', 'succes', 'joaillomager',
                'joaillomagie', 'fusionner', 'inventaire', 'vitalite',
                'resistance', 'effets', 'carac', 'historique', 'rune')
    candidates = []
    for raw in (text or '').splitlines():
        # Decorative icons/arrow markers often appear before the name.
        line = re.sub(r'^[^\wÀ-ÿ]+', '', raw.strip())
        line = re.sub(r'[^\wÀ-ÿ\-\' ]+$', '', line).strip()
        # The tiny equipment artwork immediately left of the name can be
        # misread as a numeric token (e.g. '73 ANNEAU DU CYCLOIDE') after
        # grayscale/upscaling. Remove only a short *leading* numeric glyph
        # token; never remove digits elsewhere or accept numbers as a name.
        line = re.sub(r'^\d{1,3}[\s:;.,-]+(?=[A-Za-zÀ-ÿ])', '', line)
        # OCR may interpret the decorative item icon as a single letter.
        line = re.sub(r'^[A-Za-z] (?=[A-Za-zÀ-ÿ]{3,})', '', line)
        if not line or sum(ch.isdigit() for ch in line) > 4:
            continue
        words = line.split()
        if not (1 <= len(words) <= 9 and 5 <= len(line) <= 70):
            continue
        # A workshop item name is shown in uppercase. This rejects incidental
        # labels (e.g. a 'reliquat' row) that share the same region.
        letters = [ch for ch in line if ch.isalpha()]
        if not letters or sum(ch.isupper() for ch in letters) / len(letters) < .80:
            continue
        folded = key_for(line)
        if any(word in folded.split() for word in excluded):
            continue
        if len(folded) < 5:
            continue
        candidates.append(' '.join(words))
    # Multiple plausible names in one crop means the crop is not trustworthy.
    return candidates[0] if len(candidates) == 1 else None


def enhanced_item_header(image):
    """Second, independent-looking OCR view of the selected item line."""
    from PIL import ImageEnhance, ImageOps
    crop = crop_item_header(image)
    # Keep the object name, but remove the leftmost artwork pixels. In DOFUS
    # those pixels may be read as letters/digits and vary between frames.
    # The original crop remains untouched for the first OCR pass.
    text_only = crop.crop((max(0, round(crop.width * .08)), 0, crop.width, crop.height))
    gray = ImageOps.grayscale(text_only)
    gray = ImageEnhance.Contrast(gray).enhance(1.3)
    return gray.resize((gray.width * 3, gray.height * 3))


def recognize_item_header(image, ocr, registered):
    """Return (known_name, provisional_candidate, raw_text) for the item row.

    Both OCR views are evaluated even if the first one is unreadable. A single
    plausible view can feed the *multi-frame name+icon tracker*, but can never
    register an item on its own. Conflicting readable names are rejected.
    """
    raw = ocr(crop_item_header(image))
    enhanced_raw = ocr(enhanced_item_header(image))
    combined = raw + '\n[contrôle] ' + enhanced_raw
    known_a = identify_known(raw, registered)
    known_b = identify_known(enhanced_raw, registered)
    if known_a and known_b and key_for(known_a) != key_for(known_b):
        return None, None, combined
    # If one view clearly recognizes a registered name and the other is
    # unreadable, keep the known name; if it says something else, reject.
    candidate_a = parse_item_header(raw)
    candidate_b = parse_item_header(enhanced_raw)
    if candidate_a and candidate_b and key_for(candidate_a) != key_for(candidate_b):
        return None, None, combined
    # A cropped name is acceptable as a *candidate* only if the official
    # catalogue has one unique suffix match. Multi-frame icon validation stays
    # mandatory in the observer.
    suffix_name = match_truncated_official_name(combined)
    if not known_a and not known_b and suffix_name:
        return suffix_name, None, combined
    if known_a or known_b:
        known = known_a or known_b
        other = candidate_b if known_a else candidate_a
        if other and key_for(other) != key_for(known):
            return None, None, combined
        return known, None, combined
    candidate = candidate_a or candidate_b
    return None, candidate, combined


def identify_known(text, registered):
    """Find exactly one registered name; refuse ambiguity or partial guesses."""
    hay = key_for(text)
    if not hay:
        return None
    exact = [name for _, name in registered if len(key_for(name)) >= 4 and
             re.search(r'(?<!\w)' + re.escape(key_for(name)) + r'(?!\w)', hay)]
    if len(exact) == 1:
        return exact[0]
    if exact:
        return None
    # OCR often replaces one glyph. Only compare complete OCR lines, not random
    # substrings of the screen, and require an unambiguous large margin.
    candidates = []
    for line in (text or '').splitlines():
        line_key = key_for(line)
        if not 6 <= len(line_key) <= 70:
            continue
        for _, name in registered:
            target = key_for(name)
            if len(target) < 6 or abs(len(line_key)-len(target)) > 2:
                continue
            ratio = SequenceMatcher(None, line_key, target).ratio()
            if ratio >= .91:
                candidates.append((ratio, name))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    best_score, best_name = candidates[0]
    if any(name != best_name and best_score - score < .08 for score, name in candidates[1:]):
        return None
    return best_name


def possible_unknown(text):
    """Offer OCR candidates to the user; never register them automatically."""
    excluded={'joaillomagie','historique','rune selectionnee','niv','niveau','vitalite','sagesse',
              'force','chance','agilite','intelligence','fusionner','reliquat','pa','ra','effets'}
    lines=[]
    for line in (text or '').splitlines():
        line=re.sub(r'[^\wÀ-ÿ\-\' ]',' ',line).strip()
        folded=key_for(line)
        if 5<=len(line)<=48 and not any(token in folded.split() for token in excluded) \
                and not any(char.isdigit() for char in line) and len(line.split())<=6 \
                and not any(x in folded.replace(' ','') for x in ('reliquat','joaillomagie','fusionner')):
            lines.append(line)
    return lines[:2]
