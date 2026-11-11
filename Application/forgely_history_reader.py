"""Read Unity history groups, not whole-screen guesses or synthetic trials.

The left gutter identifies rune attempts; characteristic icons are excluded
from color classification. Unsigned numbers are gains. Unknown lines, mixed
colors and clipped text prevent outcome certification. Exact pixel caching
avoids OCR on unchanged groups, including repeated confirmation frames.
"""
from collections import OrderedDict
from dataclasses import dataclass
from hashlib import sha256
import re
import numpy as np
from PIL import Image
from forgely_jet import parse_jet, norm
from forgely_dofocus import canonical_stat, RUNE_CHOICES, reference


@dataclass(frozen=True)
class HistoryGroup:
    signature: str
    top: int
    bottom: int
    changes: dict
    pool_direction: int | None
    outcome: str | None
    rune: str | None
    raw: str
    reason: str = ''


def _runs(indices,gap=3):
    runs=[]
    for y in indices:
        if runs and y-runs[-1][-1]<=gap:runs[-1].append(int(y))
        else:runs.append([int(y)])
    return [(r[0],r[-1]+1) for r in runs]


def _foreground(a,background):
    return (abs(a-background).max(2)>35)&(a.max(2)>90)


def _color(a,background):
    pixels=a[_foreground(a,background)]
    if len(pixels)<8:return 'unknown'
    r,g,b=pixels.T
    green=(g>100)&(g>r*1.2)&(g>b*1.1)
    red=(r>130)&(r>g*1.5)&(r>b*1.25)
    if green.mean()>.55:return 'green'
    if red.mean()>.55:return 'red'
    if ((pixels.max(1)-pixels.min(1)<65)&(pixels.mean(1)>100)).mean()>.6:return 'neutral'
    return 'unknown'


class HistoryReader:
    def __init__(self,ocr=None,capacity=256):
        if ocr is None:
            from forgely_ocr_backend import extract_text
            ocr=extract_text
        self.ocr=ocr;self.capacity=capacity;self.cache=OrderedDict();self.frames=OrderedDict()
        self.ocr_calls=0;self.cache_hits=0

    def latest_text(self,image):
        """Read at most three recent groups rather than the whole history."""
        groups=self.read(image,recent_only=True)
        return groups[-1].raw if groups and groups[-1].outcome else self.ocr(image)

    def read(self,image,*,recent_only=False):
        image=image.convert('RGB')
        if image.width<100 or image.height<12:return ()
        frame_key=(id(self.ocr),recent_only,image.size,sha256(image.tobytes()).digest())
        if frame_key in self.frames:
            self.cache_hits+=1;self.frames.move_to_end(frame_key)
            from dataclasses import replace
            return tuple(replace(g,changes=dict(g.changes)) for g in self.frames[frame_key])
        # Native reference is ~260 px wide; use proportional column boundaries
        # for supported UI scales, preserving the original image for OCR.
        scale=image.width/260
        gutter=max(25,round(35*scale));text_x=round(43*scale);color_x=round(64*scale)
        text_end=image.width-max(5,round(12*scale))  # scrollbar is never text
        a=np.asarray(image).astype(int)
        background=np.median(a,axis=(0,1))
        mask=_foreground(a[:,:gutter],background)
        roots=[(lo,hi) for lo,hi in _runs(np.flatnonzero(mask.sum(1)>=max(3,round(3*scale))))
               if 7*scale<=hi-lo<=32*scale]
        groups=[]
        order=range(len(roots)-1,-1,-1) if recent_only else range(len(roots))
        for index in order:
            lo,hi=roots[index]
            end=roots[index+1][0]-2 if index+1<len(roots) else image.height
            rows=_runs(np.flatnonzero(_foreground(a[lo:end,text_x:text_end],background).sum(1)>=max(3,round(3*scale))))
            if not rows:continue
            top=lo+rows[0][0];bottom=lo+rows[-1][1]
            patch=image.crop((text_x,max(0,top-2),text_end,min(end,bottom+2)))
            signature=sha256(str(image.size[0]).encode()+image.crop((0,lo,text_end,bottom)).tobytes()).hexdigest()
            key=(signature,tuple(rows))
            if key in self.cache:
                self.cache_hits+=1;self.cache.move_to_end(key)
                cached=self.cache[key]
            else:
                if recent_only and index<len(roots)-3:
                    cached=({},None,None,None,'','Ancien groupe non relu')
                else:
                    raw=self.ocr(patch);self.ocr_calls+=1
                    lines=[s.strip() for s in raw.splitlines() if s.strip()]
                    colors=[_color(a[lo+y1:lo+y2,color_x:text_end],background) for y1,y2 in rows]
                    cached=self._parse(lines,colors,raw)
                    from forgely_history_icons import recognize
                    icon_rune=recognize(image.crop((0,max(0,lo-2),gutter,min(image.height,hi+2))))
                    changes,direction,outcome,rune,raw,reason=cached
                    if outcome=='EC':rune=icon_rune
                    elif rune and icon_rune and rune!=icon_rune:
                        rune=None;reason='Conflit entre icône de rune et gain observé'
                    cached=changes,direction,outcome,rune,raw,reason
                    self.cache[key]=cached
                    while len(self.cache)>self.capacity:self.cache.popitem(last=False)
            changes,direction,outcome,rune,raw,reason=cached
            if bottom>=image.height and rows[-1][1]+lo>=image.height:
                outcome=None;reason='Ligne coupée au bord inférieur'
            if outcome is not None:
                # Confirmation concerns recognized content, not incidental
                # pixel/compression changes. Keep exact pixels for OCR caching.
                signature=sha256(repr((outcome,rune,sorted(changes.items()),direction)).encode()).hexdigest()
            groups.append(HistoryGroup(signature,lo,bottom,dict(changes),direction,outcome,rune,raw,reason))
        result=tuple(reversed(groups)) if recent_only else tuple(groups)
        self.frames[frame_key]=result
        while len(self.frames)>4:self.frames.popitem(last=False)
        return result

    @staticmethod
    def _parse(lines,colors,raw):
        changes={};direction=0;outcome=None;rune=None;reason=''
        if len(lines)!=len(colors):
            return changes,None,None,None,raw,'Nombre de lignes OCR incohérent'
        stat_colors=[]
        for line,color in zip(lines,colors):
            folded=norm(line).replace('−','-').replace('–','-')
            if 'reliquat' in folded:
                sign=re.search(r'([+-])\s*reliquat',folded)
                if sign is None or direction:
                    reason='Signe ou ligne de reliquat ambigu';break
                direction=1 if sign[1]=='+' else -1
                continue
            parsed=parse_jet(line)
            if len(parsed)!=1:
                reason='Caractéristique ou nombre illisible';break
            stat,value=next(iter(parsed.items()));stat=canonical_stat(stat)
            if stat in changes or value==0 or color=='unknown' or color=='red' and value>0:
                reason='Variation ou couleur ambiguë';break
            changes[stat]=value;stat_colors.append((value,color))
        if not reason:
            positive=any(v>0 for v in changes.values())
            negative=any(v<0 for v in changes.values())
            if positive:
                gain_colors=[c for v,c in stat_colors if v>0]
                if all(c=='green' for c in gain_colors) and not negative and not direction:outcome='SC'
                elif all(c=='neutral' for c in gain_colors) and all(c=='neutral' for v,c in stat_colors):outcome='SN'
            elif all(c=='red' for v,c in stat_colors) and (negative or direction==-1):outcome='EC'
            if outcome is None:reason='Résultat non confirmé par les couleurs et variations'
        # A successful gain identifies the rune only if its stat AND tier are
        # unique. Failure requires independent rune evidence, never a lost stat.
        if outcome in ('SC','SN'):
            gains=[(s,v) for s,v in changes.items() if v>0]
            if len(gains)==1:
                stat,gain=gains[0]
                matches=[r for r in RUNE_CHOICES.get(stat,()) if reference(r).gain==gain]
                if len(matches)==1:rune=matches[0]
        return changes,direction,outcome,rune,raw,reason


@dataclass(frozen=True)
class VisualHistoryRead:
    groups: tuple
    history: str
    event: object = None
    needs_confirmation: bool = False
    reason: str = ''


class VisualHistoryTracker:
    """Adapt bottom-growing Unity groups to existing pre/post-state validators.

    Outcome evidence is pixel/text based. Failure rune identity needs an
    unchanged selection observed before the history changed. Initial history,
    missing frames, ambiguous shifts and context switches never emit an event.
    """
    def __init__(self,reader=None):
        self.reader=reader or HistoryReader();self.reset()

    def reset(self):
        from forgely_detection import HistoryTransitionTracker
        self.tracker=HistoryTransitionTracker(tuple(r for rs in RUNE_CHOICES.values() for r in rs))
        self.context=None;self.last_frame=None;self.stable_rune=None
        self.previous_history=None;self.failure_rune=None;self.pending_history=None

    def observe(self,patch,context,frame_id,selected_rune=None):
        from forgely_detection import history_signature,new_row_shift,Observation
        if context!=self.context or (self.last_frame is not None and frame_id<self.last_frame):
            self.reset();self.context=context
        if frame_id==self.last_frame:
            return VisualHistoryRead((),self.previous_history or '',reason='Capture déjà traitée')
        self.last_frame=frame_id
        groups=self.reader.read(patch,recent_only=True)
        if not groups:
            self.reset();self.context=context;self.last_frame=frame_id
            return VisualHistoryRead((),'',reason='Aucun groupe lisible')
        # Three recent groups provide the new result plus two overlap anchors.
        # Unread older pixels must not reset these semantic confirmations.
        groups=groups[-3:]
        labels={'SC':'réussite critique','SN':'réussite neutre','EC':'échec'}
        history='Historique visuel Unity\n'+'\n'.join(
            labels.get(g.outcome,'lecture incertaine')+' @'+g.signature for g in reversed(groups))
        if self.previous_history is not None and history!=self.previous_history:
            if history!=self.pending_history:
                self.pending_history=history
                self.failure_rune=self.stable_rune if selected_rune==self.stable_rune else None
            elif selected_rune!=self.failure_rune:
                self.failure_rune=None
        newest=groups[-1]
        rune=newest.rune or (self.failure_rune if newest.outcome=='EC' else None)
        if newest.outcome=='EC' and selected_rune and rune!=selected_rune:
            rune=None  # selection and icon disagree: preserve outcome only
        if newest.outcome=='EC' and not rune:self.tracker.invalidate_rune()
        old=self.tracker.baseline
        event=self.tracker.observe(history,'Rune '+rune if rune else '')
        if event is not None:
            # Never assign one result to multiple unseen attempts or to a new
            # reference after scrolling. Existing explicit-text mode is separate.
            if new_row_shift(old or (),history_signature(history))!=1:event=None
            else:
                event=Observation(rune,event.outcome,newest.raw,'visuel à vérifier',
                                  'Couleur, variations et groupe de rune ; bilan avant/après requis',
                                  dict(newest.changes),newest.pool_direction,True)
        stable=not self.tracker.pending_count and self.tracker.baseline==history_signature(history)
        if stable:
            self.previous_history=history;self.pending_history=None
            self.stable_rune=selected_rune
        return VisualHistoryRead(groups,history,event,
            bool(self.tracker.pending_count or self.tracker._init_count==1),self.tracker.reason)
