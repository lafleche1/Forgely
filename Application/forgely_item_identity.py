"""Lightweight current-item evidence, independent of full rune/effects recovery."""
from dataclasses import dataclass
from time import monotonic
from forgely_atelier import crop_zone,workshop_visual_fallback
from forgely_continuous_identity import current_icon,effect_signature
from forgely_item_vision import crop_item_header,recognize_item_header
from forgely_zone_cache import ZoneCache


@dataclass(frozen=True)
class ItemIdentityRead:
    known: str | None
    candidate: str | None
    raw: str
    icon: object
    signature: tuple


class ItemIdentityReader:
    def __init__(self):
        self.reset()

    def reset(self):
        self.header=None
        self.effects=ZoneCache(refresh_seconds=8)

    def read(self,image,ocr,registered):
        # Unknown workshop geometry must not turn inventory art into identity.
        if not workshop_visual_fallback(image):
            self.reset()
            return None
        icon=current_icon(image)
        if icon is None:
            self.reset()
            return ItemIdentityRead(None,None,'Emplacement actuel illisible',None,())
        patch=crop_item_header(image)
        signature=(patch.size,patch.mode,patch.tobytes())
        now=monotonic()
        unresolved=self.header is not None and not any(self.header[1][:2])
        if self.header is None or self.header[0]!=signature or (unresolved and now-self.header[2]>=1.0):
            reading=recognize_item_header(image,ocr,registered() if callable(registered) else registered)
            self.header=(signature,reading,now)
        known,candidate,raw=self.header[1]
        # Raw table only: no rune/history OCR, no selected-row or strip recovery.
        # Natural Min/Max evidence remains an independent veto on visual matches.
        effects=self.effects.read('identity_effects',crop_zone(image,'effects'),ocr)
        return ItemIdentityRead(known,candidate,raw,icon,effect_signature(effects))


class IdentityFrameGate:
    """Reject older evidence; same-capture enrichment is allowed.

    The slot/name trackers separately deduplicate their confirmation counts.
    """
    def __init__(self):self.previous=None

    def accept(self,mailbox,generation,title,frame_id):
        context=(mailbox,generation,title)
        if self.previous and self.previous[:3]==context and frame_id<self.previous[3]:return False
        self.previous=(*context,frame_id)
        return True
