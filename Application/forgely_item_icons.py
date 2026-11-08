"""Private, offline visual references for equipment in the DOFUS FM history.

The current item's icon is immediately to the LEFT of its name in the first
history row. Never infer a new item from an icon alone: name OCR and a stable
icon must agree over multiple independent frames before local registration.
"""
from __future__ import annotations
from PIL import Image, ImageStat, ImageChops


def crop_item_icon(image, row_y=None):
    """History icon at the heading's ACTUAL row, not the first history row.

    row_y is the absolute pixel y of the heading center, obtained from
    Tesseract word bounding boxes. A missing row must not silently produce
    a misleading first-row icon.
    """
    if row_y is None:
        return None
    w, h = image.size
    # History column begins near 0.168*w; the icon is at its left edge.
    left, right = round(w * .170), round(w * .184)
    top, bottom = round(row_y - h * .013), round(row_y + h * .013)
    return image.crop((left, max(0, top), right, min(h, bottom)))


def history_icon_for_name(image, name):
    """Locate a specific named heading with OCR geometry; fail closed.

    Unlike OCR's flattened text, image_to_data retains the position of each
    word, allowing us to crop the icon beside the matching equipment name.
    """
    if not name:
        return None
    try:
        import pytesseract
        from forgely_atelier import crop_zone, ZONES
        from forgely_items import key_for
        from PIL import ImageEnhance, ImageOps
        region = crop_zone(image, 'history')
        scale = 3
        enlarged = ImageEnhance.Contrast(ImageOps.grayscale(region)).enhance(1.8)
        enlarged = enlarged.resize((region.width * scale, region.height * scale))
        data = pytesseract.image_to_data(enlarged, config='--psm 6', output_type=pytesseract.Output.DICT)
        rows = {}
        for i, word in enumerate(data['text']):
            if not word.strip():
                continue
            key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
            rows.setdefault(key, []).append(i)
        target = key_for(name).replace(' ', '')
        matches = []
        for indices in rows.values():
            phrase = ''.join(key_for(data['text'][i]).replace(' ', '') for i in indices)
            tokens = [key_for(data['text'][i]).replace(' ', '') for i in indices]
            target_words = [key_for(t).replace(' ', '') for t in name.split()]
            # OCR often truncates the last word (CYCLOÏDE -> CYCLO:).
            # Require the first two full words plus a prefix of the third.
            partial = (len(target_words) >= 3 and len(tokens) >= 3 and
                       target_words[0] in tokens and target_words[1] in tokens and
                       any(len(t) >= 4 and target_words[2].startswith(t) for t in tokens))
            from difflib import SequenceMatcher
            fuzzy = (len(target) >= 12 and abs(len(phrase) - len(target)) <= 3
                     and SequenceMatcher(None, target, phrase).ratio() >= .84)
            if (target and target in phrase) or partial or fuzzy:
                center = sum((data['top'][i] + data['height'][i] / 2) for i in indices) / len(indices)
                matches.append(center / scale + image.height * ZONES['history'][1])
        if len(matches) != 1:
            return None
        return normalize_icon(crop_item_icon(image, matches[0]))
    except (ImportError, RuntimeError, ValueError, OSError, KeyError, TypeError):
        return None



def history_icon_by_visual_row(image, slot_icon, name):
    """Fallback when OCR word geometry loses the history heading.

    Scan only the icon column, then OCR the text on the SAME matched row.
    Never associate a historical name on icon similarity alone.
    """
    if not name or slot_icon is None:
        return None
    try:
        import pytesseract
        from forgely_atelier import ZONES
        from forgely_items import key_for
        from PIL import ImageEnhance, ImageOps
        w, h = image.size
        y1, y2 = int(h * ZONES['history'][1]), int(h * ZONES['history'][3])
        candidates = []
        # A heading is one row high. Sampling every 3 px covers small UI offsets.
        for y in range(y1 + 12, y2 - 12, 3):
            patch = normalize_icon(crop_item_icon(image, y))
            if patch is not None:
                d = icon_distance(patch, slot_icon)
                if d <= 35:
                    candidates.append((d, y))
        # Collapse nearby samples into distinct rows, best first.
        rows = []
        for distance, y in sorted(candidates):
            if all(abs(y - previous_y) > 18 for _, previous_y in rows):
                rows.append((distance, y))
        for distance, y in rows[:6]:
            # OCR ONLY the label adjacent to the matching icon, not the full
            # historical list, which may include headings for older items.
            label = image.crop((int(.184*w), max(0,y-14), int(.270*w), min(h,y+14)))
            label = ImageEnhance.Contrast(ImageOps.grayscale(label)).enhance(2.0)
            label = label.resize((label.width*3, label.height*3))
            raw = pytesseract.image_to_string(label, config='--psm 7')
            actual = key_for(raw).replace(' ', '')
            expected = key_for(name).replace(' ', '')
            from difflib import SequenceMatcher
            if expected and (expected in actual or
                             (len(expected) >= 12 and
                              SequenceMatcher(None, expected, actual).ratio() >= .82)):
                return normalize_icon(crop_item_icon(image, y))
    except (ImportError, RuntimeError, ValueError, OSError, KeyError, TypeError):
        return None
    return None

def normalize_icon(image):
    if image is None:
        return None
    image = image.convert('RGB').resize((32, 32), Image.Resampling.LANCZOS)
    # A blank/panel-only crop is not evidence of an equipment icon.
    if max(ImageStat.Stat(image).stddev) < 14:
        return None
    return image


def icon_distance(a, b):
    """Mean absolute RGB difference (0=identical, 255=opposite)."""
    a, b = normalize_icon(a), normalize_icon(b)
    if a is None or b is None:
        return 255.0
    diff = ImageChops.difference(a, b)
    return sum(ImageStat.Stat(diff).mean) / 3.0


class ItemVisualTracker:
    """Require consecutive agreement on both name AND icon before enrollment."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.name = None
        self.icon = None
        self.count = 0
        self.missed = 0

    def observe(self, name, icon):
        from forgely_items import key_for
        patch = normalize_icon(icon)
        if not name or patch is None:
            # Small OCR glitches should not restart an otherwise stable
            # identity. Never confirm on a missing frame, and forget after
            # three misses to avoid carrying a previous item forward.
            self.missed += 1
            if self.missed >= 3:
                self.reset()
            return 0
        key = key_for(name)
        if self.name == key and self.missed < 3 and icon_distance(self.icon, patch) <= 14:
            self.count += 1
        else:
            self.name, self.count = key, 1
        self.missed = 0
        self.icon = patch
        return self.count
