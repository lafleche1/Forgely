"""DOFUS 3 atelier region reader. Conservative: unrecognized interface => no event.

Default coordinates are anchored to the player's 1648x928 reference capture.
They are *not* universal when UI scale/panel layout changes. Keep diagnostic crops
local and never infer a rune from just a row/column containing inventory counts.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import unicodedata
from difflib import SequenceMatcher


# (x1,y1,x2,y2) fractions of the captured DOFUS window.
# Source: supplied 1648x928 screenshot, with workshop at approx 273..1005,138..763.
ZONES = {
    'title': (.325,.148,.530,.188),
    'history': (.168,.266,.289,.786),
    'effects': (.285,.175,.515,.805),
    'runes': (.492,.270,.598,.377),
    'reliquat': (.325,.193,.394,.229),
}

def crop_zone(image, name):
    if name not in ZONES: raise ValueError('Zone inconnue')
    a,b,c,d=ZONES[name]
    w,h=image.size
    return image.crop((round(a*w),round(b*h),round(c*w),round(d*h)))

def normalize(text):
    s=unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in s if not unicodedata.combining(c)).casefold()

WORKSHOP_NAMES = ('joaillomager', 'cordomage', 'costumage', 'forgemage', 'sculptemage', 'joaillomagie', 'cordomagie', 'costumagie', 'forgemagie', 'sculptemagie')


def is_workshop_title(text):
    """Allow modest OCR letter substitution in workshop profession names.

    Use actual word-like OCR tokens, not fuzzy matching against arbitrary text;
    a malformed title must remain close to a known profession.
    """
    raw = normalize(text).replace('0', 'o').replace('1', 'l')
    tokens = re.findall(r'[a-z]{7,18}', raw)
    for token in tokens:
        for profession in WORKSHOP_NAMES:
            if profession in token:
                return True
            if abs(len(token) - len(profession)) <= 2 and SequenceMatcher(None, token, profession).ratio() >= .81:
                return True
    return False

@dataclass(frozen=True)
class AtelierRead:
    active: bool
    title: str
    history: str
    effects: str
    runes: str
    reliquat: str
    reason: str

def title_candidates(image):
    """Multiple conservative crops for DOFUS window borders and UI scaling."""
    from PIL import ImageEnhance, ImageOps
    w, h = image.size
    boxes = [ZONES['title'], (.25,.12,.62,.23), (.23,.10,.66,.26)]
    for box in boxes:
        patch = image.crop((round(box[0]*w),round(box[1]*h),round(box[2]*w),round(box[3]*h)))
        yield patch
        gray = ImageOps.grayscale(patch)
        yield ImageEnhance.Contrast(gray).enhance(3).resize((gray.width*3,gray.height*3))


def specialized_title_candidates(image):
    """Threshold white text on DOFUS's purple header, preserving sharp edges."""
    from PIL import ImageOps
    w, h = image.size
    for box in (ZONES['title'], (.25, .12, .62, .23)):
        patch = image.crop(tuple(round(v * (w if i % 2 == 0 else h)) for i, v in enumerate(box)))
        gray = ImageOps.grayscale(patch)
        for threshold in (155, 180):
            binary = gray.point(lambda pixel, t=threshold: 255 if pixel >= t else 0)
            enlarged = binary.resize((binary.width * 3, binary.height * 3))
            enlarged.info['forgely_title'] = True
            yield enlarged


def workshop_visual_fallback(image):
    """Confirm the fixed-layout FM workshop when its title OCR fails.

    Requires several independent purple-panel and effects-table anchors;
    never use the item icon or the rune history as proof of a workshop.
    A changed interface layout fails closed rather than inventing events.
    """
    from PIL import ImageStat
    rgb = image if image.mode == 'RGB' else image.convert('RGB')
    w, h = rgb.size
    if w < 1100 or h < 650:
        return False
    # Workshop frame and statistics panel in the user's native DOFUS layout.
    # Sample small neighborhoods, not single anti-aliased pixels.
    def mean(x, y):
        cx, cy = round(x*w), round(y*h)
        patch = rgb.crop((cx-3,cy-3,cx+4,cy+4))
        return ImageStat.Stat(patch).mean[:3]
    def purple(x,y):
        r,g,b=mean(x,y)
        return 28 <= r <= 145 and 28 <= g <= 145 and 48 <= b <= 170 and b >= r+8 and b >= g+8
    # Each anchor occupies a different UI element: title strip, left
    # history panel, and two separate rows of the effects table.
    anchors=((.29,.162),(.48,.162),(.20,.31),(.26,.46),(.32,.31),(.32,.46))
    if sum(purple(*pt) for pt in anchors) < 5:
        return False
    # The inventory or another purple DOFUS window alone must not qualify.
    # Two dark alternating effects rows must be present in the workshop.
    rows=(mean(.36,.275),mean(.36,.345),mean(.36,.415))
    return all(15 <= r <= 125 and 15 <= g <= 110 and 25 <= b <= 130 for r,g,b in rows)


def read_atelier(image, ocr, zone_cache=None, title_cache=None):
    # Fast path: a previously verified workshop with independently confirmed
    # visual anchors needs no repeated title OCR until periodic revalidation.
    # The visual check runs on EVERY frame, so closing the workshop invalidates
    # the fast path immediately. A failed visual check still gets normal OCR.
    from time import monotonic
    visual_ok = workshop_visual_fallback(image) if title_cache is not None else False
    cached = bool(visual_ok and title_cache.get("confirmed") and monotonic() - title_cache.get("checked_at", 0) < 20.0)
    title = title_cache.get("title", "") if cached else ""
    confirmed = cached
    if not confirmed and visual_ok:
        confirmed = True
        title = "Atelier de FM (structure visuelle confirmée)"
    if not confirmed:
      for candidate in title_candidates(image):
          candidate_text = ocr(candidate)
          if candidate_text and not title:
              title = candidate_text
          if is_workshop_title(candidate_text):
              title = candidate_text
              confirmed = True
              break
    if not confirmed:
        for candidate in specialized_title_candidates(image):
            candidate_text = ocr(candidate)
            if candidate_text and not title:
                title = candidate_text
            if is_workshop_title(candidate_text):
                title = candidate_text
                confirmed = True
                break
    if not confirmed and (visual_ok or workshop_visual_fallback(image)):
        confirmed = True
        title = 'Atelier de FM (structure visuelle confirmée ; titre OCR indisponible)'
    if title_cache is not None:
        if not cached:
            title_cache.update(confirmed=confirmed, title=title if confirmed else '', checked_at=monotonic())
        if not confirmed:
            title_cache.clear()
    if not confirmed:
        return AtelierRead(False,title,'','','','','Atelier non confirmé : aucune tentative enregistrée')
    def read_zone(name, reader):
        patch = crop_zone(image, name)
        return zone_cache.read(name, patch, reader) if zone_cache is not None else reader(patch)
    history=read_zone('history', ocr)
    from forgely_jet import read_effects_ocr
    effects=read_zone('effects', lambda patch: read_effects_ocr(patch, ocr))
    # IMPORTANT: effects may be served from the zone OCR cache. A highlighted
    # stat can disappear from that cached text, so run the targeted recovery on
    # the CURRENT image, not only when read_effects_ocr() runs on a cache miss.
    from forgely_jet import parse_jet, recover_missing_effects_live
    # A tooltip can contain plausible stat names and numbers. Never append
    # its text to the equipment jet or run the highlighted-line recovery.
    effects_normalized = normalize(effects)
    tooltip_visible = any(token in effects_normalized for token in (
        'prix moyen', 'quantite en', 'comparer avec', 'valeurs theor',
        'panoplie', 'poids 5', 'niveau 1'))
    if tooltip_visible and zone_cache is not None:
        zone_cache.entries.pop('effects', None)
    try:
        if tooltip_visible:
            raise ValueError('Infobulle détectée : lecture du jet ignorée')
        actual_effects_patch = crop_zone(image, 'effects')
        recovered, frame_info = recover_missing_effects_live(
            actual_effects_patch, parse_jet(effects))
        if recovered:
            effects += ''.join('\n{} {}'.format(value, name) for name, value in recovered.items())
            if zone_cache is not None:
                zone_cache.remember('effects', actual_effects_patch, effects)
    except Exception as exc:
        import forgely_jet
        forgely_jet.LAST_HIGHLIGHT_DIAGNOSTIC = {
            'status': 'erreur_lecture_ligne', 'detail': str(exc)[:160]}

    runes=read_zone('runes', ocr)
    reliquat=read_zone('reliquat', lambda patch: read_reliquat_ocr(patch, ocr))
    return AtelierRead(True,title,history,effects,runes,reliquat,'Atelier reconnu ; analyse historique uniquement')

def read_reliquat_ocr(patch, ocr):
    """Use an extra focused OCR pass only when the normal pool read is invalid.

    A missing decimal point must not be guessed from '09': we require a
    visibly transcribed separator in at least one independent OCR pass.
    """
    raw = ocr(patch)
    if parse_reliquat(raw) is not None:
        return raw
    try:
        import pytesseract
        from PIL import ImageEnhance, ImageOps
        gray = ImageOps.grayscale(patch)
        candidates = (patch, ImageEnhance.Contrast(gray).enhance(3).resize(
            (gray.width * 4, gray.height * 4)))
        for candidate in candidates:
            text = pytesseract.image_to_string(candidate, config='--psm 7')
            if parse_reliquat(text) is not None:
                return text
    except Exception:
        pass
    return raw


def parse_reliquat(text):
    """Accept only a clearly written nonnegative pool amount.

    A hyphen is NOT a decimal separator: OCR `reliquat -0.2` conflicts
    with a positive displayed pool and must not become +0.2.
    """
    x = normalize(text).replace('，', ',')
    m = re.search(r'reli[qauo]{2,5}t\s*[:;=>*]\s*([+]?[0-9]{1,4}(?:[,.][0-9]{1,3})?)\b', x)
    if not m:
        m = re.search(r'reliquat\s*[:;=>*]\s*([+]?[0-9]{1,4}(?:[,.][0-9]{1,3})?)\b', x)
    if not m:
        return None
    number = m.group(1).lstrip('+')
    if len(number) > 1 and number.startswith('0') and not any(c in number for c in ',.'):
        return None
    return float(number.replace(',', '.'))


def choose_reliquat(effects_text, dedicated_text):
    """Prioritize explicit effect-table decimals; never guess missing punctuation.

    Repeated-frame stabilization is handled by WorkshopReadings. An explicit
    disagreement between two plausible positive readings stays unknown.
    """
    effects = parse_reliquat(effects_text)
    dedicated = parse_reliquat(dedicated_text)
    effects_decimal = bool(re.search(r'reli\w*\s*[:;=>*]\s*\d+[,.]\d+', normalize(effects_text)))
    dedicated_decimal = bool(re.search(r'reli\w*\s*[:;=>*]\s*\d+[,.]\d+', normalize(dedicated_text)))
    if effects is not None and effects_decimal:
        if dedicated is not None and dedicated_decimal and abs(effects-dedicated)>1e-8:
            return None
        return effects
    # A missing decimal separator in the dedicated crop (e.g. 28 for 2,8)
    # must never override a valid explicitly punctuated effects reading.
    if dedicated is not None and dedicated_decimal:
        return dedicated
    if effects is not None:
        return effects
    # Integer-only OCR may be correct (0, 1, etc.), but if the crop is
    # ambiguous we do not infer a missing comma.
    return dedicated
