"""Confirmed visual reads and display continuity; no synthetic rune events."""
from forgely_item_icons import normalize_icon,icon_distance
from dataclasses import dataclass


def numeric_frame_signature(image):
    """Source pixels in a common RGB mode, independent of history animation."""
    from forgely_atelier import crop_zone
    from forgely_continuous_identity import crop_current_item
    patches = (crop_zone(image, 'current_jet'), crop_zone(image, 'reliquat'),
               crop_current_item(image))
    return (image.size, tuple((patch.size, 'RGB', patch.convert('RGB').tobytes()) for patch in patches))


def _numeric_text_ink(entry):
    """Keep every foreground stroke, including signs and decimal dots.

    Compare glyphs without letting a low-contrast panel shimmer invalidate
    them. There is no resizing, smoothing or count-based pixel tolerance.
    """
    import numpy as np
    from PIL import Image
    size,mode,pixels=entry
    rgb=np.asarray(Image.frombytes(mode,size,pixels).convert('RGB')).astype('int16')
    background=np.median(rgb,axis=1,keepdims=True)
    ink=(abs(rgb-background).max(2)>35)&(rgb.max(2)>90)
    return ink.tobytes()


@dataclass(frozen=True)
class ConfirmedAtelierRead:
    context: tuple
    signature: tuple
    atelier: object
    numeric: tuple
    zones: tuple = ()
    numeric_signature: tuple | None = None
    complete: bool = True

    def matches(self,context,signature):
        # Reuse is exact, deliberately stricter than the noisy change detector.
        return self.complete and self.context==context and self.signature==signature

    def matches_numeric(self, context, image):
        return self.numeric_mismatch_reason(context,image) is None

    def numeric_mismatch_reason(self,context,image):
        if self.context!=context:return 'contexte_fenetre'
        if self.numeric_signature is None:return 'provenance_absente'
        current=numeric_frame_signature(image)
        if self.numeric_signature[0]!=current[0]:return 'dimensions'
        source_patches,current_patches=self.numeric_signature[1],current[1]
        for name,old,new in zip(('jet','reliquat'),source_patches[:2],current_patches[:2]):
            if old[0]!=new[0]:return name
            if old!=new and _numeric_text_ink(old)!=_numeric_text_ink(new):return name
        old,new=source_patches[2],current_patches[2]
        if old!=new:
            from PIL import Image
            a=Image.frombytes(old[1],old[0],old[2])
            b=Image.frombytes(new[1],new[0],new[2])
            # Use the same artwork tolerance as independent identity tracking,
            # rather than demanding byte-identical icon shading for numbers.
            if icon_distance(a,b)>17:return 'icone'
        return None


def read_current_atelier(confirmed,context,signature,read):
    if isinstance(confirmed,ConfirmedAtelierRead) and confirmed.matches(context,signature):
        return confirmed.atelier,True
    return read(),False


class IconReplacement:
    """A hidden icon is not a change; require independent matching replacements."""
    def __init__(self):
        self.icon=None;self.count=0;self.frame=None

    def observe(self,reference,icon,frame=None):
        icon=normalize_icon(icon)
        if icon is None:
            self.icon=None;self.count=0;self.frame=None
            return 'hidden'
        if icon_distance(reference,icon)<=17:
            self.icon=None;self.count=0;self.frame=None
            return 'same'
        if self.icon is None or icon_distance(self.icon,icon)>17:
            self.icon=icon.copy();self.count=0;self.frame=None
        if frame is None or frame!=self.frame:
            self.count+=1;self.frame=frame
        return 'changed' if self.count>=3 else 'pending'


def advice_key(app):
    """An edited goal or mode must not keep the previous goal's advice."""
    measured=getattr(app,'measured_goals',None)
    targets=getattr(measured,'targets',{})
    plan=getattr(app,'plan',None) or {}
    if not targets:
        targets={k:v['target'] for k,v in plan.get('stats',{}).items() if v.get('target') is not None}
    from forgely_tools import read_settings
    return (app.item.get(),tuple(sorted(targets.items())),app.goal_mode.get(),
            read_settings().get('strategy','Chances maximales'))


def held_advice(app):
    if getattr(app,'_copilot_masked',False) is not True:return None
    if getattr(app,'_held_advice_key',None)!=advice_key(app):return None
    return getattr(app,'current_proposal',None)


def numeric_snapshot_covers(app,context,frame_id):
    """Delayed history must not invalidate a confirmed post-rune capture."""
    stamp=getattr(app,'_stable_numeric_frame',None)
    return bool(type(frame_id) is int and isinstance(stamp,tuple) and len(stamp)==3
        and stamp[0]==context and stamp[2]==app.item.get()
        and type(stamp[1]) is int and stamp[1]>=frame_id
        and getattr(app,'live_after_fusion',True) is False
        and app.workshop_readings.snapshot() is not None)


def advice_unavailable_reason(app):
    """A retained display is never permission to act on stale numbers."""
    if getattr(app,'running',None) is False:
        return 'Observation arrêtée'
    if getattr(app,'workshop_active',None) is False:
        return 'Lecture du jeu en attente'
    from forgely_workshop_readings import WorkshopReadings
    readings=getattr(app,'workshop_readings',None)
    if isinstance(readings,WorkshopReadings) and readings.context is not None and readings.snapshot() is None:
        return readings.waiting_reason
    if getattr(app,'_copilot_masked',False) is True:
        return 'Conseil suspendu · atelier à relire'
    return None
