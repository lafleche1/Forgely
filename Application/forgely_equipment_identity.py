"""Offline, conservative artwork/category/natural-range candidate resolution.

Scores are distances, not calibrated probabilities. A pHash is a prefilter only;
RGB agreement and independent natural bounds are required for automatic naming.
The immutable bundled index is rebuilt on process restart or clear_index_cache().
"""
from __future__ import annotations

from collections import Counter, OrderedDict
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from threading import RLock

import cv2
import numpy as np
from PIL import Image

from forgely_item_icons import normalize_icon
from forgely_items import key_for
from forgely_jet import norm

PHASH_MAX = 8
RGB_MAX = 10.0
RGB_MARGIN = 8.0
MIN_SHARED_BOUNDS = 3
SLOT_RGB_MAX = 24.0
SLOT_RGB_MARGIN = 6.0


def crop_catalogue_slot(image):
    # Include the complete artwork with padding for verified-layout offsets.
    # The legacy temporal tracker keeps its old narrow crop for compatibility.
    w, h = image.size
    return image.crop((round(.380*w), round(.185*h), round(.412*w), round(.250*h)))


def canonical_stat(label):
    value = norm(label).strip().replace('resistances', 'resistance')
    return {'invocations': 'invocation', 'soins': 'soin'}.get(value, value)


def perceptual_hash(image):
    """64-bit pHash: grayscale 32x32 DCT, median AC threshold (DC excluded)."""
    gray = np.asarray(image.convert('L').resize((32, 32), Image.Resampling.LANCZOS), dtype=np.float32)
    block = cv2.dct(gray)[:8, :8].ravel()
    bits = block > np.median(block[1:])
    bits[0] = False
    return int.from_bytes(np.packbits(bits).tobytes(), 'big')


def artwork(image):
    if image.mode in ('RGBA', 'LA') or 'transparency' in image.info:
        rgba = image.convert('RGBA')
        background = Image.new('RGBA', rgba.size, '#38394e')
        image = Image.alpha_composite(background, rgba).convert('RGB')
    return normalize_icon(image)


@dataclass(frozen=True)
class Reference:
    item_id: int
    name: str
    category: str
    signature: tuple
    image: object


@dataclass(frozen=True)
class IdentityDecision:
    name: str | None
    candidates: tuple
    method: str
    distance: float | None = None
    shared_bounds: int = 0
    vetoed_names: tuple = ()
    invalid_evidence: bool = False


class EquipmentIdentityIndex:
    def __init__(self, references, cache_size=512, *, prepared=None):
        references = tuple(references)
        self.references = []
        arrays, hashes, profiles = [], [], []
        self.unreadable = []
        # Multiple items sharing one icon reuse its decoded pixels and DCT.
        decoded = {}
        selected=range(len(references)) if prepared is None else prepared[0]
        for position in selected:
            reference=references[position]
            if prepared is not None:
                self.references.append(reference)
                profiles.append({canonical_stat(k):(lo,hi) for k,lo,hi in reference.signature})
                continue
            try:
                source = reference.image
                if isinstance(source, (str, Path)):
                    path = Path(source)
                    if path not in decoded:
                        with Image.open(path) as image:
                            decoded[path] = artwork(image)
                    patch = decoded[path]
                else:
                    patch = artwork(source)
                if patch is None:
                    self.unreadable.append(reference.item_id)
                    continue
            except (OSError, ValueError):
                self.unreadable.append(reference.item_id)
                continue
            self.references.append(reference)
            arrays.append(np.asarray(patch, dtype=np.int16))
            hashes.append(perceptual_hash(patch))
            profiles.append({canonical_stat(k): (lo, hi) for k, lo, hi in reference.signature})
        self.pixels = np.asarray(arrays, dtype=np.int16) if prepared is None else prepared[1]
        self.hashes = np.asarray(hashes, dtype=np.uint64) if prepared is None else prepared[2]
        if prepared is not None:
            kept=set(selected);self.unreadable=[r.item_id for i,r in enumerate(references) if i not in kept]
        self.profiles = profiles
        self.name_counts = Counter(key_for(r.name) for r in references)
        # Compare decoded artwork, including files with different icon IDs.
        # Keep excluded artwork as a negative reference: removing its pixels
        # could let a similar, otherwise unique object win instead.
        artwork_groups = {}
        for index, pixels in enumerate(self.pixels):
            artwork_groups.setdefault(pixels.tobytes(), []).append(index)
        self.excluded_indices = frozenset(
            index for group in artwork_groups.values()
            if len({key_for(self.references[i].name) for i in group}) > 1
            for index in group)
        self.cache_size = max(0, cache_size)
        self.cache = OrderedDict()
        self.cache_hits = 0
        self._lock = RLock()
        self.slot_cache = OrderedDict()
        self.slot_templates = {}

    def _slot_template(self, index):
        with self._lock:
            cached = self.slot_templates.get(index)
        if cached is not None:
            return cached
        source = self.references[index].image
        if isinstance(source, (str, Path)):
            with Image.open(source) as image:
                rgba = image.convert('RGBA')
        else:
            rgba = source.convert('RGBA')
        box = rgba.getchannel('A').getbbox()
        if box is None:
            return None
        result = rgba.crop(box)
        with self._lock:
            self.slot_templates[index] = result
        return result

    def _sparse_slot_candidates(self, slot):
        """Shortlist artwork by foreground pHash when few bounds are readable.

        Use several padding variants, retain ties, then require the stricter
        pixel comparison below. A pHash alone can never name an equipment.
        """
        pixels = np.asarray(slot.convert('RGB'))
        colors, counts = np.unique(pixels.reshape(-1, 3), axis=0, return_counts=True)
        background = colors[int(counts.argmax())].astype(np.int16)
        mask = (np.max(np.abs(pixels.astype(np.int16) - background), axis=2) > 35).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), dtype=np.uint8))
        _, _, components, _ = cv2.connectedComponentsWithStats(mask)
        boxes = [(int(x), int(y), int(w), int(h)) for x, y, w, h, area in components[1:]
                 if area >= 40 and w >= 8 and h >= 12 and w < slot.width*.9 and h < slot.height*.8]
        boxes = sorted(boxes, key=lambda b: b[2]*b[3], reverse=True)[:3]
        candidates = set()
        for x, y, width, height in boxes:
            for padding in (0, 2, 4):
                crop = slot.crop((max(0, x-padding), max(0, y-padding),
                                  min(slot.width, x+width+padding), min(slot.height, y+height+padding)))
                xor = np.bitwise_xor(self.hashes, np.uint64(perceptual_hash(crop)))
                distances = np.unpackbits(xor.view(np.uint8).reshape(-1, 8), axis=1).sum(axis=1)
                if not len(distances):
                    continue
                cutoff = np.partition(distances, min(31, len(distances)-1))[min(31, len(distances)-1)]
                candidates.update(int(i) for i in np.flatnonzero(distances <= cutoff))
        return candidates, boxes

    def resolve_slot(self, slot, signature=(), category=None):
        """Align complete sprite artwork inside the current slot, not history.

        Natural bounds shortlist candidates before masked, multiscale RGB
        matching. Padding/alpha and small UI scale/position offsets are ignored;
        actual foreground pixels and a distinct runner margin remain mandatory.
        """
        if slot is None or normalize_icon(slot) is None:
            return IdentityDecision(None, (), 'unreadable')
        signature = tuple(sorted(tuple(x) for x in signature))
        observed = {}
        for name, lo, hi in signature:
            name = canonical_stat(name)
            if lo > hi or (name in observed and observed[name] != (lo, hi)):
                return IdentityDecision(None, (), 'conflicting_bounds', invalid_evidence=True)
            observed[name] = (lo, hi)
        sparse = len(observed) < MIN_SHARED_BOUNDS
        key = (slot.size, sha256(slot.convert('RGB').tobytes()).digest(), signature, category)
        with self._lock:
            if key in self.slot_cache:
                self.slot_cache.move_to_end(key)
                return self.slot_cache[key]
        query = np.asarray(slot.convert('RGB'))
        # Window/DPI normalization resamples the small sprite a second time.
        # With independent natural bounds, tolerate subpixel edge shifts to
        # avoid rejecting matching artwork solely for different edge sampling.
        # Sparse evidence retains the stricter, unfiltered pixel comparison.
        if not sparse:
            query = cv2.GaussianBlur(query, (3, 3), .6)
        sparse_candidates, boxes = self._sparse_slot_candidates(slot) if sparse else (None, ())
        score_max = 20.0 if sparse else SLOT_RGB_MAX
        margin_min = 10.0 if sparse else SLOT_RGB_MARGIN
        ranked = []
        for index, reference in enumerate(self.references):
            if sparse and index not in sparse_candidates:
                continue
            if category is not None and reference.category != category:
                continue
            expected = self.profiles[index]
            shared = observed.keys() & expected.keys()
            if ((not sparse and len(shared) < MIN_SHARED_BOUNDS) or
                    any(observed[k] != expected[k] for k in shared)):
                continue
            try:
                rgba = self._slot_template(index)
            except (OSError, ValueError):
                continue
            if rgba is None:
                continue
            best = float('inf')
            for height in range(max(12, round(min(slot.size) * .25)), min(slot.height-2, round(min(slot.size) * .90)) + 1):
                width = round(height * rgba.width / rgba.height)
                if not 8 <= width <= slot.width - 2:
                    continue
                if sparse and not any(.7*bw <= width <= 1.5*bw and .7*bh <= height <= 1.5*bh
                                      for _, _, bw, bh in boxes):
                    continue
                resized = np.asarray(rgba.resize((width, height),
                                    Image.Resampling.BILINEAR if sparse else Image.Resampling.LANCZOS))
                mask = np.asarray(resized[:, :, 3] >= 220, dtype=np.uint8) * 255
                count = int(np.count_nonzero(mask))
                if count < 64:
                    continue
                template = resized[:, :, :3]
                if not sparse:
                    template = cv2.GaussianBlur(template, (3, 3), .6)
                distances = cv2.matchTemplate(query, template, cv2.TM_SQDIFF, mask=mask)
                if sparse:
                    # Do not let a dark sprite match empty panel pixels beside
                    # the actual object. Its centre must align with the object.
                    positions = np.zeros(distances.shape, dtype=bool)
                    for x, y, bw, bh in boxes:
                        left=max(0, round(x+bw/2-width/2-4)); right=min(distances.shape[1], round(x+bw/2-width/2+5))
                        top=max(0, round(y+bh/2-height/2-4)); bottom=min(distances.shape[0], round(y+bh/2-height/2+5))
                        positions[top:bottom, left:right] = True
                    distances = np.where(positions, distances, np.inf)
                score = float(np.sqrt(max(0, float(np.min(distances))) / (count * 3)))
                best = min(best, score)
            if best <= score_max + margin_min:
                ranked.append((best, index, len(shared)))
        ranked.sort()
        candidates = tuple((self.references[i].item_id, self.references[i].name)
                           for distance, i, _ in ranked if distance <= score_max and i not in self.excluded_indices)
        name = None
        if ranked and ranked[0][1] in self.excluded_indices and ranked[0][0] <= score_max:
            decision = IdentityDecision(None, (), 'shared_artwork_excluded', ranked[0][0])
        elif candidates:
            distance, first, shared = ranked[0]
            reference = self.references[first]
            margin = len(ranked) == 1 or ranked[1][0] - distance >= margin_min
            if margin and first not in self.excluded_indices and self.name_counts[key_for(reference.name)] == 1:
                name = reference.name
            method = 'slot_artwork_sparse_bounds' if sparse else 'slot_artwork_bounds'
            decision = IdentityDecision(name, candidates, method if name else 'ambiguous', distance, shared)
        else:
            decision = IdentityDecision(None, (), 'no_match')
        with self._lock:
            if self.cache_size:
                self.slot_cache[key] = decision
                if len(self.slot_cache) > self.cache_size:
                    self.slot_cache.popitem(last=False)
        return decision

    def _rank(self, patch, signature, category):
        key = (sha256(patch.tobytes()).digest(), signature, category)
        with self._lock:
            if key in self.cache:
                self.cache_hits += 1
                self.cache.move_to_end(key)
                return self.cache[key]
        observed = {canonical_stat(k): (lo, hi) for k, lo, hi in signature}
        ranked = []
        vetoed = set()
        if self.references:
            xor = np.bitwise_xor(self.hashes, np.uint64(perceptual_hash(patch)))
            distances = np.unpackbits(xor.view(np.uint8).reshape(-1, 8), axis=1).sum(axis=1)
            indices = np.flatnonzero(distances <= PHASH_MAX)
            pixels = np.asarray(patch, dtype=np.int16)
            for i in indices:
                reference = self.references[i]
                distance = float(np.abs(self.pixels[i] - pixels).mean())
                # Retain runners beyond the acceptance boundary when measuring
                # the margin. Dropping a runner at 10.1 would falsely clear 9.9.
                if distance > RGB_MAX + RGB_MARGIN:
                    continue
                expected = self.profiles[i]
                shared = observed.keys() & expected.keys()
                # One contradictory natural bound is a veto, even on an exact icon.
                if ((category is not None and reference.category != category) or
                        any(observed[k] != expected[k] for k in shared)):
                    if distance <= RGB_MAX:
                        vetoed.add(reference.name)
                    continue
                ranked.append((distance, int(i), len(shared)))
        result = (tuple(sorted(ranked)), tuple(sorted(vetoed)))
        with self._lock:
            if self.cache_size:
                self.cache[key] = result
                if len(self.cache) > self.cache_size:
                    self.cache.popitem(last=False)
        return result

    def resolve(self, icon, signature=(), category=None, name_reader=None):
        patch = artwork(icon) if icon is not None else None
        if patch is None:
            return IdentityDecision(None, (), 'unreadable')
        signature = tuple(sorted(tuple(x) for x in signature))
        bounds = {}
        for label, lo, hi in signature:
            label = canonical_stat(label)
            if lo > hi or (label in bounds and bounds[label] != (lo, hi)):
                return IdentityDecision(None, (), 'conflicting_bounds', invalid_evidence=True)
            bounds[label] = (lo, hi)
        ranked, vetoed = self._rank(patch, signature, category)
        candidates = tuple((self.references[i].item_id, self.references[i].name)
                           for distance, i, _ in ranked if distance <= RGB_MAX and i not in self.excluded_indices)
        # The application consumes name evidence (not official IDs). Even OCR
        # cannot distinguish two catalogue entries bearing the same name.
        vetoed = tuple(sorted(set(vetoed) | {name for _, name in candidates
                                             if self.name_counts[key_for(name)] > 1}))
        if not candidates:
            return IdentityDecision(None, (), 'no_match', vetoed_names=vetoed)
        distance, first, shared = ranked[0]
        best = self.references[first]
        if first in self.excluded_indices:
            return IdentityDecision(None, (), 'shared_artwork_excluded', distance, shared,
                                    tuple(sorted({self.references[i].name for _, i, _ in ranked
                                                  if i in self.excluded_indices})))
        margin = len(ranked) == 1 or ranked[1][0] - distance >= RGB_MARGIN
        unique_name = self.name_counts[key_for(best.name)] == 1
        # Unexpected lines may be an exo or an OCR error: they never strengthen evidence.
        if margin and shared >= MIN_SHARED_BOUNDS and unique_name:
            return IdentityDecision(best.name, candidates, 'icon_bounds', distance, shared, vetoed)
        if name_reader is not None:
            selected = name_reader(candidates)
            matches = [name for _, name in candidates if selected and key_for(name) == key_for(selected)]
            if len(matches) == 1 and self.name_counts[key_for(matches[0])] == 1:
                return IdentityDecision(matches[0], candidates, 'ocr_tiebreak', distance, shared, vetoed)
        return IdentityDecision(None, candidates, 'ambiguous', distance, shared, vetoed)


_index_build_lock = RLock()


@lru_cache(maxsize=1)
def _build_bundled_index():
    from forgely_equipment_catalog import EquipmentCatalog, equipment_bounds, ROOT
    catalogue = EquipmentCatalog()
    references=tuple(
        Reference(item.item_id, item.name, item.category,
                  tuple((canonical_stat(k), *v) for k, v in equipment_bounds(item).items()),
                  ROOT / 'assets' / 'equipment_icons' / f'{item.icon_id}.png')
        for item in catalogue.items)
    from forgely_equipment_prepared import load_prepared,save_prepared
    cache=ROOT/'assets'/'equipment_identity_cache.npz'
    prepared=load_prepared(cache,references)
    result=EquipmentIdentityIndex(references,prepared=prepared)
    if prepared is None:save_prepared(cache,references,result)
    return result


def bundled_identity_index():
    # Both the lightweight and full OCR workers may request the cold index.
    # lru_cache alone allows duplicate concurrent construction.
    with _index_build_lock:
        return _build_bundled_index()


def prepare_equipment_catalogue():
    """Warm the optional numeric index without blocking the GUI thread."""
    try:bundled_identity_index()
    except (OSError,ValueError,KeyError):pass


def clear_index_cache():
    with _index_build_lock:
        _build_bundled_index.cache_clear()
        from forgely_equipment_catalog import _bundled_profiles
        _bundled_profiles.cache_clear()


def fast_equipment_decision(icon, signature=(), category=None, name_reader=None):
    try:
        return bundled_identity_index().resolve(icon, signature, category, name_reader)
    except (OSError, ValueError, KeyError):
        # Missing/inconsistent catalogue is never permission to guess.
        return IdentityDecision(None, (), 'catalogue_unavailable')


def fast_equipment_match(icon, signature=(), category=None):
    return fast_equipment_decision(icon, signature, category).name


def slot_equipment_decision(image, signature=(), category=None):
    try:
        return bundled_identity_index().resolve_slot(crop_catalogue_slot(image), signature, category)
    except (OSError, ValueError, KeyError):
        return IdentityDecision(None, (), 'catalogue_unavailable')


def is_catalogue_identity(name):
    try:
        return bundled_identity_index().name_counts.get(key_for(name), 0) == 1
    except (OSError, ValueError, KeyError):
        return False


def restrict_header_to_candidates(reading, candidates, vetoed_names=(), invalid_evidence=False):
    known, candidate, raw = reading
    vetoed = {key_for(name) for name in vetoed_names}
    if invalid_evidence or any(name and key_for(name) in vetoed for name in (known, candidate)):
        return None, None, raw
    if not candidates:
        return reading
    accepted = [name for _, name in candidates if known and key_for(name) == key_for(known)]
    return (accepted[0], None, raw) if len(accepted) == 1 else (None, None, raw)
