"""Conservative OCR parser for DOFUS workshop effect values."""
from __future__ import annotations
import re
import unicodedata
import threading
from time import monotonic

def norm(s):
    s=unicodedata.normalize('NFKD',s).lower()
    return ''.join(c for c in s if not unicodedata.combining(c))

BASE_STATS=('Vitalité','Force','Intelligence','Chance','Agilité','Sagesse','Puissance',
            'Initiative','Prospection','PA','PM','Portée','Tacle','Fuite',
            'Invocations','Invocation','Coups Critiques','Dommages Critiques',
            'Soins','Dommages','Pods','Esquive PA','Esquive PM','Retrait PA','Retrait PM',
            'Résistance Critique','Résistance Poussée','Dommages Poussée',
            'Dommages Pièges','Puissance Pièges')
ELEMENTS=('Neutre','Terre','Feu','Eau','Air')
ELEMENTAL_STATS=tuple(f'{kind} {element}' for kind in
    ('Dommages','Résistance','Résistances','% Résistance','% Résistances','% Dommages')
    for element in ELEMENTS)
STATS=BASE_STATS+ELEMENTAL_STATS+tuple(f'{element} Résistance' for element in ELEMENTS)
# Longest names first prevents reading 'Dommages' from 'Dommages Feu'.
SORTED_STATS=sorted(STATS,key=lambda s:len(norm(s)),reverse=True)

def parse_jet(text):
    """Only accept explicit numeric effect lines; never infer missing characteristics."""
    found={}
    for raw in text.splitlines():
        line=norm(raw).replace('％','%').translate(str.maketrans({'−':'-','–':'-','—':'-','﹣':'-','－':'-'}))
        # DOFUS uses the singular label for a one-point damage line.
        line=re.sub(r'\bdommage\b','dommages',line)
        # OCR sometimes reads the zero of a stat as capital O (e.g. O Tacle).
        line=re.sub(r'(?<![\w])o(?=\s+tacle\b)', '0', line)
        # Icons can touch the value, and OCR can insert punctuation.
        line=re.sub(r'(?<=\d)[|:]\s*(?=[a-z])', ' ', line)
        # OCR may place the percent sign before or after the number.
        for stat in SORTED_STATS:
            label=norm(stat)
            # Avoid matching generic names within longer labels.
            # A leading icon often becomes an OCR glyph directly before the number.
            # Require a number immediately before the stat, not the Min/Max columns.
            pattern=r'(?<![\w])([+-]?\s*\d{1,5})\s*%?\s*'+re.escape(label).replace(r'\ ',r'\s+')+r'(?![\w])'
            m=re.search(pattern,line)
            if not m:continue
            end=line[m.end():].lstrip()
            if stat=='Dommages' and end and end[0].isalpha():
                continue
            if stat in ('PA','PM') and re.search(r'\b(?:esquive|retrait)\s*$',line[:m.start()]):
                continue
            # Distinguish percent resistances from flat resistances.
            if stat.startswith('Résistance') or stat.startswith('Résistances'):
                if '%' in line[max(0,m.start()-4):m.end()+2]:
                    stat='% '+stat
            if stat.startswith('% '):
                key=stat
            else:key=stat
            value=int(re.sub(r'\s+', '', m.group(1)))
            if key in found and found[key]!=value:found[key]=None
            else:found[key]=value
            break
    return {k:v for k,v in found.items() if v is not None}

def read_jet(image,extract_text):
    w,h=image.size
    region=image.crop((int(w*.295),int(h*.28),int(w*.61),int(h*.57)))
    return parse_jet(extract_text(region))


# Isolate the actual green effect text from the purple DOFUS background.
# This is independent of the position of the Min/Max header and does not
# presume the first stat is Vitalité (other items may not have Vitalité).
_FIRST_ROW_FAILURES = {}

def green_effect_mask(patch):
    """Extract green numbers + labels without relying on a fixed row offset."""
    from PIL import ImageChops
    # Channel LUTs preserve the integer comparisons exactly while Pillow's
    # native operations avoid a Python loop over every crop pixel.
    red, green, blue = patch.convert('RGB').split()
    red_limit = red.point([min(255, r * 117 // 100) for r in range(256)])
    blue_limit = blue.point([min(255, b * 106 // 100) for b in range(256)])
    positive = [0] + [255] * 255
    enough_green = green.point([0] * 74 + [255] * 182)
    above_red = ImageChops.subtract(green, red_limit).point(positive)
    above_blue = ImageChops.subtract(green, blue_limit).point(positive)
    selected = ImageChops.multiply(enough_green, ImageChops.multiply(above_red, above_blue))
    return ImageChops.invert(selected)


def first_row_candidates(patch):
    """Scan a broad top area instead of assuming row y=9..16%."""
    from PIL import ImageEnhance, ImageOps
    w, h = patch.size
    # Include the region above the table's first row, for shifted interfaces.
    for lo, hi in ((0, .30), (.03, .42), (0, .55)):
        crop = patch.crop((round(w*.31), round(h*lo), w, round(h*hi)))
        if crop.width < 25 or crop.height < 8:
            continue
        mask = green_effect_mask(crop)
        yield mask.resize((mask.width*2, mask.height*2))
        if lo == 0:
            gray = ImageOps.grayscale(crop)
            yield ImageEnhance.Contrast(gray).enhance(2).resize((gray.width*2,gray.height*2))

def read_first_effect_row(patch, ocr_engine=None):
    """Locate Vitalité using several vertical offsets, without guessing its value.

    A row that is shifted by UI scale must not be replaced by the Force row.
    The numeric value is accepted only if OCR also reads the Vitalité label.
    """
    import pytesseract
    import hashlib
    from time import monotonic
    from PIL import ImageOps
    signature = (patch.size, patch.mode, hashlib.sha256(patch.tobytes()).digest())
    if monotonic() - _FIRST_ROW_FAILURES.get(signature, -1e10) < 8.0:
        return ''
    w, h = patch.size
    # Dedicated narrow horizontal strips. The original broad windows could
    # include the header or Force, especially at non-reference UI scales.
    windows = ((.29,.197,.83,.264), (.28,.165,.84,.232),
               (.28,.227,.84,.294), (.28,.135,.84,.202),
               (.28,.257,.84,.324))
    for left, top, right, bottom in windows:
        region = patch.crop((round(w*left),round(h*top),round(w*right),round(h*bottom)))
        if region.width < 25 or region.height < 8:
            continue
        # RGB OCR first: the DOFUS green font is readable in color and the
        # color mask can sometimes remove anti-aliased parts of digits.
        variants = (region, green_effect_mask(region))
        for candidate in variants:
            enlarged = candidate.resize((candidate.width*3,candidate.height*3))
            raw = pytesseract.image_to_string(enlarged,config='--psm 7')
            parsed = parse_jet(raw)
            if 'Vitalité' in parsed:
                _FIRST_ROW_FAILURES.pop(signature, None)
                return f"{parsed['Vitalité']} Vitalité"
    # Equipment without Vitalité must not trigger ten identical subprocesses
    # on every confirmation. Changed pixels always bypass this failure cache.
    if len(_FIRST_ROW_FAILURES) >= 32:
        _FIRST_ROW_FAILURES.pop(next(iter(_FIRST_ROW_FAILURES)))
    _FIRST_ROW_FAILURES[signature] = monotonic()
    return ''

LAST_HIGHLIGHT_DIAGNOSTIC = {"status": "pas_encore_analyse"}

def read_highlighted_effect(patch, existing=None, ocr_engine=None):
    """Recover any selected stat inside DOFUS' pale rectangular highlight.

    Detect horizontal frame edges by bright near-neutral pixels; OCR only the
    interior between matching edges. No assumed stat name or numeric value.
    """
    global LAST_HIGHLIGHT_DIAGNOSTIC
    import pytesseract
    from PIL import ImageOps, ImageEnhance
    rgb = patch.convert('RGB')
    w, h = rgb.size
    if h < 40 or w < 100:
        LAST_HIGHLIGHT_DIAGNOSTIC={'status':'image_trop_petite'}
        return {}, LAST_HIGHLIGHT_DIAGNOSTIC
    x0, x1 = int(w*.24), int(w*.95)
    pixels = rgb.load()
    scores = [0.0] * h
    for y in range(int(h*.09), int(h*.96)):
        count = 0
        for x in range(x0, x1):
            r, g, b = pixels[x, y]
            if min(r, g, b) > 155 and max(r, g, b)-min(r, g, b) < 65:
                count += 1
        scores[y] = count / max(1, x1-x0)
    edge_rows = [y for y in range(int(h*.09), int(h*.96)) if scores[y] > .38]
    groups=[]
    for y in edge_rows:
        if not groups or y > groups[-1][-1]+2:
            groups.append([y])
        else:
            groups[-1].append(y)
    centers=[round(sum(g)/len(g)) for g in groups if len(g)<=12]
    # Selected row is typically 17-38 pixels high at the reference scale.
    # Relative limits permit other resolutions and UI scales.
    pairs=[]
    for i, a in enumerate(centers):
        for b in centers[i+1:]:
            if h*.026 <= b-a <= h*.095:
                pairs.append((a,b))
    for top, bottom in pairs[:18]:
        # Crop INSIDE the outline, excluding vertical and horizontal borders.
        margin=max(2, round((bottom-top)*.12))
        crop=patch.crop((int(w*.30),top+margin,int(w*.94),bottom-margin))
        if crop.width<35 or crop.height<7:
            continue
        variants=(crop, green_effect_mask(crop), ImageEnhance.Contrast(ImageOps.grayscale(crop)).enhance(2.3))
        for variant in variants:
            large=variant.resize((variant.width*3,variant.height*3))
            raw=pytesseract.image_to_string(large,config='--psm 7') if ocr_engine is None else ocr_engine(large)
            parsed=parse_jet(raw)
            new={k:v for k,v in parsed.items() if k not in existing}
            if parsed and all(k in existing and existing[k]==v for k,v in parsed.items()):
                LAST_HIGHLIGHT_DIAGNOSTIC={'status':'ligne_encadree_deja_lue','position':(top,bottom),'ocr':raw.strip()}
                return {}, LAST_HIGHLIGHT_DIAGNOSTIC
            if new:
                LAST_HIGHLIGHT_DIAGNOSTIC={'status':'ligne_encadree_lue','position':(top,bottom),'ocr':raw.strip()}
                return new, LAST_HIGHLIGHT_DIAGNOSTIC
    LAST_HIGHLIGHT_DIAGNOSTIC={'status':'cadre_non_lu','bords_detectes':len(centers),'paires':len(pairs)}
    return {}, LAST_HIGHLIGHT_DIAGNOSTIC



# Never assume that the selected line is Vitalité. The missing line is found
# from visible OCR, and its value must be read from the image itself.
_LIVE_RECOVERY_CACHE = {}
_LIVE_RECOVERY_LOCK = threading.Lock()


class _RecoveryBudgetReached(Exception):
    pass


def recover_missing_effects_live(patch, existing):
    """At most three extra OCR calls per frame, resuming exact-pixel work.

    A changed image or parsed jet never replays earlier text. Completed results
    retain the previous bounded TTL; unfinished work asks for another capture.
    """
    global LAST_HIGHLIGHT_DIAGNOSTIC
    from copy import deepcopy
    import pytesseract
    import os
    signature = (patch.size, patch.mode, patch.tobytes(),
                 tuple(sorted((existing or {}).items())),
                 pytesseract.pytesseract.tesseract_cmd,os.environ.get('TESSDATA_PREFIX'))
    now = monotonic()
    with _LIVE_RECOVERY_LOCK:
        previous = _LIVE_RECOVERY_CACHE.get(signature)
    if previous is not None and now - previous[0] < 8.0 and previous[1] is not None:
        recovered, detail = deepcopy(previous[1])
        LAST_HIGHLIGHT_DIAGNOSTIC = detail
        return recovered, detail
    replay=list(previous[2]) if previous is not None and previous[1] is None and now-previous[0]<8.0 else []
    cursor=0
    calls=0
    def limited_ocr(image,psm=6):
        nonlocal cursor,calls
        if cursor<len(replay):
            result=replay[cursor];cursor+=1
            return result
        if calls>=3:raise _RecoveryBudgetReached()
        result=pytesseract.image_to_string(image,config=f'--psm {psm}')
        calls+=1;cursor+=1;replay.append(result)
        return result
    try:
        result = _recover_missing_effects_live(patch, existing,ocr_engine=limited_ocr)
        entry=(monotonic(),deepcopy(result))
    except _RecoveryBudgetReached:
        LAST_HIGHLIGHT_DIAGNOSTIC={'status':'recuperation_en_cours','ocr_ce_passage':calls,
            'ocr_deja_effectues':len(replay),'limite_par_passage':3}
        result=({},LAST_HIGHLIGHT_DIAGNOSTIC)
        entry=(monotonic(),None,replay)
    with _LIVE_RECOVERY_LOCK:
        if signature not in _LIVE_RECOVERY_CACHE and len(_LIVE_RECOVERY_CACHE) >= 4:
            _LIVE_RECOVERY_CACHE.pop(next(iter(_LIVE_RECOVERY_CACHE)))
        _LIVE_RECOVERY_CACHE[signature] = entry
    return result


def _recover_missing_effects_live(patch, existing,ocr_engine=None):
    global LAST_HIGHLIGHT_DIAGNOSTIC
    from PIL import ImageOps, ImageEnhance
    import pytesseract
    existing = existing or {}
    if len(existing) >= 11:
        LAST_HIGHLIGHT_DIAGNOSTIC = {'status': 'jet_complet', 'nb_stats': len(existing)}
        return {}, LAST_HIGHLIGHT_DIAGNOSTIC
    # First use the outlined-row detector. This is a *live* pass even if the
    # general effects OCR was returned from the cache.
    recovered, detail = read_highlighted_effect(patch, existing,
        ocr_engine=(lambda image:ocr_engine(image,7)) if ocr_engine else None)
    if recovered or detail.get('status')=='ligne_encadree_deja_lue':
        return recovered, detail
    # The outline may be invisible after scaling/antialiasing. Scan the table
    # in thin, overlapping strips, excluding the Min/Max header and footer.
    # This avoids trying to recognize the entire table as one text block.
    w, h = patch.size
    scanned = 0
    for a in (0.15, 0.23, 0.31, 0.39, 0.47, 0.55, 0.63, 0.71, 0.79):
        b = min(.98, a+.115)
        crop = patch.crop((round(w*.29), round(h*a), round(w*.98), round(h*b)))
        if crop.width < 30 or crop.height < 8:
            continue
        # Green-only mask often removes white outline and purple UI clutter.
        for variant in (green_effect_mask(crop), ImageEnhance.Contrast(ImageOps.grayscale(crop)).enhance(2.0)):
            enlarged=variant.resize((variant.width*2, variant.height*2))
            raw=(ocr_engine(enlarged,6) if ocr_engine else pytesseract.image_to_string(enlarged, config='--psm 6'))
            scanned += 1
            parsed=parse_jet(raw)
            fresh={k:v for k,v in parsed.items() if k not in existing}
            if fresh:
                LAST_HIGHLIGHT_DIAGNOSTIC={'status':'ligne_recuperee_balayage',
                    'stats':fresh,'bande':(round(a,3),round(b,3)),
                    'ocr':raw.strip()[:100],'essais':scanned}
                return fresh, LAST_HIGHLIGHT_DIAGNOSTIC
    LAST_HIGHLIGHT_DIAGNOSTIC={'status':'aucune_ligne_recuperee',
        'stats_deja_lues':len(existing),'essais':scanned,
        'detection_cadre':detail}
    return {}, LAST_HIGHLIGHT_DIAGNOSTIC


def read_effects_ocr(patch, ocr):
    """Read effects conservatively, recovering the first and last edge rows.

    Extra OCR only when a target row is absent from full-table OCR. Values
    always come from visible pixels; no equipment template fills missing data.
    """
    text = ocr(patch)
    values = parse_jet(text)
    if 'Tacle' not in values:
        for line in text.splitlines():
            if re.search(r'\btacle\b', norm(line)):
                corrected = re.sub(r'(?<![\w])O(?=0\s+tacle\b)', '', line, flags=re.I)
                if 'Tacle' in parse_jet(corrected):
                    text += '\n' + corrected
                    values = parse_jet(text)
                    break
    if 'Vitalité' not in values:
        try:
            first = read_first_effect_row(patch)
            if first:
                # Do not append duplicate lines with different OCR values.
                # A color-mask pass is recovery only for genuinely missing stats.
                recovered = []
                for line in first.splitlines():
                    entries = parse_jet(line)
                    if entries and all(name not in values for name in entries):
                        recovered.append(line)
                        values.update(entries)
                if recovered:
                    text += '\n' + '\n'.join(recovered)
        except Exception:
            pass
    if 'Tacle' not in values:
        try:
            import pytesseract
            from PIL import ImageEnhance, ImageOps
            strip = patch.crop((round(patch.width*.36), round(patch.height*.74),
                                patch.width, patch.height))
            gray = ImageOps.grayscale(strip)
            for candidate in (strip, ImageEnhance.Contrast(gray).enhance(2.6)):
                enlarged = candidate.resize((candidate.width*2, candidate.height*2))
                candidate_text = pytesseract.image_to_string(enlarged, config='--psm 6')
                if 'Tacle' in parse_jet(candidate_text):
                    text += '\n' + candidate_text
                    break
        except Exception:
            pass
    return text

