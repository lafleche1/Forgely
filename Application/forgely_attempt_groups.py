"""Bounded, local pixel evidence of unclassified DOFUS attempt groups.

Input must be the normalized atelier history crop. Neutral gray rune icons in
its exclusive left gutter anchor groups; text rows never anchor attempts. This
supports the captured gray icon family only, not arbitrary rune artwork.
Full old groups must remain below a new prefix. Repeated indistinguishable
groups require a complete window with a large blank tail and clear right gutter.
Nothing here classifies outcomes.
The supported surface is a complete, unscrolled history window. No general
scrollbar detector is provided; a caller observing scrolling must reset this
tracker or withhold observations until a new reference can be established.
"""
from dataclasses import dataclass
from hashlib import sha256
import numpy as np
from PIL import Image


def _digest(image):
    return sha256(str(image.size).encode()+image.tobytes()).hexdigest()


@dataclass(frozen=True)
class AttemptGroup:
    signature: str
    root_signature: str
    evidence: object
    top: int
    outcome: None = None
    rune: None = None


def _normalized(patch):
    if patch.width < 60 or patch.height < 60:
        return None
    return patch.convert('RGB').resize((232,round(patch.height*232/patch.width)),Image.Resampling.NEAREST)


def extract_attempt_groups(history_patch):
    """Return icon-anchored groups, including continuation lines as evidence."""
    image=_normalized(history_patch)
    if image is None:return ()
    a=np.asarray(image).astype(int)
    gutter=a[:,:28]
    neutral=(gutter.max(2)-gutter.min(2)<38)&(gutter.mean(2)>105)
    occupied=np.flatnonzero(neutral.sum(1)>=4)
    runs=[]
    for y in occupied:
        if runs and y-runs[-1][-1]<=3:runs[-1].append(int(y))
        else:runs.append([int(y)])
    anchors=[]
    for run in runs:
        lo,hi=run[0],run[-1]+1
        # Header is always above the first supported rune row; taller areas
        # and tiny isolated bright pixels are not icons.
        if lo<30 or not 7<=hi-lo<=16:continue
        ys,xs=np.where(neutral[lo:hi])
        if len(xs)<45 or xs.max()-xs.min()<10:continue
        anchors.append((lo,hi))
    groups=[]
    for i,(lo,hi) in enumerate(anchors):
        end=anchors[i+1][0]-1 if i+1<len(anchors) else image.height
        # Trim only plain background. Keep exact foreground pixels so changed
        # stat/reliquat continuation lines change the group's signature.
        area=a[lo:end]
        background=np.median(a[-min(20,len(a)):],axis=(0,1))
        foreground=(abs(area-background).max(2)>30).sum(1)>=3
        rows=np.flatnonzero(foreground)
        if not len(rows):continue
        bottom=lo+int(rows[-1])+1
        evidence=image.crop((0,lo,232,bottom))
        root=image.crop((0,lo,28,hi))
        groups.append(AttemptGroup(_digest(evidence),_digest(root),evidence,lo))
    return tuple(groups)


class AttemptGroupTracker:
    """Two fresh matching frames confirm a baseline or a conservative insert."""
    def __init__(self):self.reset()

    def reset(self):
        self.context=None
        self.last_frame=None
        self.baseline=None
        self.candidate=None
        self.streak=0
        self.observed_attempts=0

    def observe(self,history_patch,context,frame_id):
        if context!=self.context:
            self.reset();self.context=context
        def report(status,groups=(),new=(),pending=False):
            return dict(status=status,visible_groups=groups,newly_confirmed_groups=new,
                        pending=pending,observed_attempts=self.observed_attempts,
                        classified=False)
        if self.last_frame is not None and frame_id<=self.last_frame:
            return report('duplicate_frame')
        self.last_frame=frame_id
        image=_normalized(history_patch)
        groups=extract_attempt_groups(history_patch)
        if image is None or not groups:
            self.baseline=self.candidate=None;self.streak=0
            return report('anchors_unavailable',groups)
        if any(group.top+group.evidence.height >= image.height-4 for group in groups):
            # A clipped continuation can otherwise match another identically
            # clipped group after a window shift. Never establish or retain a
            # counting reference at an occupied bottom boundary.
            self.baseline=self.candidate=None;self.streak=0
            return report('clipped_window',groups)
        pixels=np.asarray(image).astype(int)
        background=np.median(pixels[-min(20,len(pixels)):],axis=(0,1))
        # The normalized history crop ends at the panel's exclusive right
        # gutter. Occupancy here can indicate a scrollbar/overflow affordance;
        # conservatively abstain rather than interpret a scrolled prefix.
        gutter=abs(pixels[30:,-8:]-background).max(2)>25
        if (gutter.sum(1)>=2).sum()>=8:
            self.baseline=self.candidate=None;self.streak=0
            return report('scrollbar_visible',groups)
        bottom=max(g.top+g.evidence.height for g in groups)
        complete=image.height-bottom>=48
        header=_digest(image.crop((0,0,232,30)))
        keys=tuple(g.signature for g in groups)
        snapshot=(header,keys,complete)
        if snapshot==self.candidate:self.streak+=1
        else:self.candidate=snapshot;self.streak=1
        if self.streak<2:return report('confirmation_pending',groups,pending=True)
        old=self.baseline
        self.baseline=snapshot
        if old is None:return report('initial_reference',groups)
        if old==snapshot:return report('unchanged',groups)
        old_header,old_keys,old_complete=old
        # Duplicate content needs direct whole-window group-count evidence:
        # both windows retain a large empty tail and have a clear scroll gutter.
        unique=len(set(keys))==len(keys) and len(set(old_keys))==len(old_keys)
        added=len(keys)-len(old_keys)
        defensible=unique or (complete and old_complete)
        if (header==old_header and defensible and len(old_keys)>=2 and added>0
                and keys[added:]==old_keys):
            new=groups[:added]
            self.observed_attempts+=len(new)
            return report('new_groups_confirmed',groups,new)
        return report('ambiguous_reference',groups)
