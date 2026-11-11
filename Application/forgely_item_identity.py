"""Lightweight current-item evidence, independent of full rune/effects recovery."""
from dataclasses import dataclass
from time import monotonic
from forgely_atelier import crop_zone,workshop_visual_fallback,is_workshop_title,crop_identity_workshop_title
from forgely_continuous_identity import current_icon,effect_signature
from forgely_item_vision import crop_item_header,recognize_item_header
from forgely_zone_cache import ZoneCache
from forgely_equipment_identity import fast_equipment_match, fast_equipment_decision, restrict_header_to_candidates, slot_equipment_decision


@dataclass(frozen=True)
class ItemIdentityRead:
    known: str | None
    candidate: str | None
    raw: str
    icon: object
    signature: tuple
    catalogue_verified: bool = False


class ItemIdentityReader:
    def __init__(self, *, allow_name_ocr=False, artwork_only=False):
        # Prefer catalogue artwork; natural Min/Max are a fallback only.
        self.allow_name_ocr=allow_name_ocr
        self.artwork_only=artwork_only
        self.reset()

    def reset(self):
        self.header=None
        self.effects=ZoneCache(refresh_seconds=8)
        self.titles=ZoneCache(refresh_seconds=8)

    def read(self,image,ocr,registered,category=None):
        # Unknown workshop geometry must not turn inventory art into identity.
        if not workshop_visual_fallback(image):
            # A short table (e.g. Gelano) can contain only white/blue values
            # and fail the conservative green three-row visual guard. Match
            # the profession title independently, never the equipment name.
            title=self.titles.read('identity_workshop_title',crop_identity_workshop_title(image),ocr)
            if not is_workshop_title(title):
                self.reset()
                return None
        icon=current_icon(image)
        if icon is None:
            self.reset()
            return ItemIdentityRead(None,None,'Emplacement actuel illisible',None,())
        if self.artwork_only:
            decision=slot_equipment_decision(image,(),category)
            if decision.name:
                return ItemIdentityRead(decision.name,None,
                    'Objet identifié dans le logement actuel',icon,(),True)
        # Read independent natural bounds before considering any name OCR.
        effects=self.effects.read('identity_effects',crop_zone(image,'effects'),ocr)
        bounds=effect_signature(effects)
        visual_name=fast_equipment_match(icon,bounds,category)
        slot_decision=slot_equipment_decision(image,bounds,category) if not visual_name else None
        visual_name=visual_name or (slot_decision.name if slot_decision else None)
        if visual_name:
            return ItemIdentityRead(visual_name,None,'Icône et bornes naturelles concordantes',icon,bounds,True)
        if self.artwork_only or not self.allow_name_ocr:
            return ItemIdentityRead(None,None,'Icône non reconnue ou ambiguë · aucun OCR du nom',icon,bounds)
        decision=fast_equipment_decision(icon,bounds,category)
        candidates=decision.candidates
        patch=crop_item_header(image)
        signature=(patch.size,patch.mode,patch.tobytes(),icon.tobytes(),bounds,category,candidates,
                   decision.vetoed_names,decision.invalid_evidence)
        now=monotonic()
        unresolved=self.header is not None and not any(self.header[1][:2])
        if self.header is None or self.header[0]!=signature or (unresolved and now-self.header[2]>=1.0):
            names=candidates or (registered() if callable(registered) else registered)
            reading=recognize_item_header(image,ocr,names)
            reading=restrict_header_to_candidates(reading,candidates,decision.vetoed_names,decision.invalid_evidence)
            self.header=(signature,reading,now)
        known,candidate,raw=self.header[1]
        # Raw table only: no rune/history OCR, no selected-row or strip recovery.
        # Natural Min/Max evidence remains an independent veto on visual matches.
        return ItemIdentityRead(known,candidate,raw,icon,bounds)


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
