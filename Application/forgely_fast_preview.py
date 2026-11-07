"""Independent, provisional rune display; never writes observations or advice."""
from dataclasses import dataclass

from forgely_atelier import crop_zone, workshop_visual_fallback
from forgely_continuous_identity import current_icon
from forgely_detection import HistoryTransitionTracker
from forgely_item_icons import icon_distance


@dataclass(frozen=True)
class PreviewRead:
    event: object = None
    needs_confirmation: bool = False
    context_reset: bool = False


class FastRunePreview:
    def __init__(self, rune_names):
        self.tracker = HistoryTransitionTracker(rune_names)
        self.context = None
        self.icon = None

    def read(self, image, context, ocr):
        if not workshop_visual_fallback(image):
            self.reset()
            return PreviewRead(context_reset=True)
        icon = current_icon(image)
        if icon is None:
            self.reset()
            return PreviewRead(context_reset=True)
        changed = (context != self.context or self.icon is None or
                   icon_distance(icon, self.icon) > 17)
        if changed:
            self.reset()
            self.context = context
            self.icon = icon
        history_patch = crop_zone(image, 'history')
        rune_patch = crop_zone(image, 'runes')
        history_patch.info['forgely_preview_zone'] = 'history'
        rune_patch.info['forgely_preview_zone'] = 'runes'
        # Independent OCR on each confirmation; no effects, pool, item-name
        # lookup, fallback scans, database or cached OCR in this fast path.
        history = ocr(history_patch)
        rune = ocr(rune_patch)
        event = self.tracker.observe(history, rune)
        pending = bool(self.tracker.pending_count or
                       (self.tracker.baseline is None and self.tracker._init_count == 1))
        return PreviewRead(event, pending, changed)

    def reset(self):
        self.tracker = HistoryTransitionTracker(self.tracker.rune_names)
        self.context = None
        self.icon = None
