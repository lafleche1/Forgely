"""Bounded collection of uncertain visual rows, separate from FM learning."""
import hashlib
from pathlib import Path
from functools import lru_cache
from time import monotonic
import cv2
import numpy as np
from forgely_cv.numbers import number_mask,NumericReader
from forgely_cv.glyphs import segment_glyphs
from forgely_jet import parse_jet, norm


@lru_cache(maxsize=1)
def calibrated_export_readers():
    """Curated labelled exports, with separate held-out captures in Tests."""
    root=Path(__file__).parent/'forgely_cv'/'profiles'
    return tuple(NumericReader.from_directory(root/name) for name in
        ('cycloide_442x625_v1','cycloide_442x625_after_v1','gelano_442x625_v1','padgref_negative_v1',
         'padgref_live_top_v1','padgref_live_bottom_v1','white_zero_pa_9x11_v1',
         'white_zero_pa_kido_20261110','white_zero_pa_normalized_20261110',
         'white_zero_pa_normalized_212821'))


def complete_stat_line(image):
    """Return a tight whole text run, never a clipped word or Min/Max pair."""
    mask=number_mask(image)
    all_parts=segment_glyphs(mask)
    parts=[p for p in all_parts if p.box.h>=5 and p.box.w<image.shape[1]*.8]
    groups=[]
    for part in parts:
        if (groups and part.line==groups[-1][-1].line and
                part.box.x-groups[-1][-1].box.x-groups[-1][-1].box.w<=max(9,part.box.h)):
            groups[-1].append(part)
        else:groups.append([part])
    groups=[g for g in groups if len(g)>=3]
    if not groups:return None
    hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
    chromatic=cv2.inRange(hsv,(0,65,110),(179,255,255))
    group=max(groups,key=lambda g:(sum(cv2.countNonZero(p.box.crop(chromatic)) for p in g),sum(p.box.w for p in g)))
    left=min(p.box.x for p in group);right=max(p.box.x+p.box.w for p in group)
    top=min(p.box.y for p in group);bottom=max(p.box.y+p.box.h for p in group)
    # Preserve a short minus/plus immediately before the number. Filtering
    # tiny components for line detection must not turn -4 into +4.
    for part in reversed(all_parts):
        if (part.line==group[0].line and part.box.h<5 and
                0<=left-part.box.x-part.box.w<=3):
            left=part.box.x;top=min(top,part.box.y);bottom=max(bottom,part.box.y+part.box.h)
    if left<=1 or right>=image.shape[1]-1 or top<=1 or bottom>=image.shape[0]-1:
        return None
    return image[max(0,top-3):min(image.shape[0],bottom+3),max(0,left-3):min(image.shape[1],right+3)].copy()


def effect_rows(image):
    """Find purple table bands, discard Min/Max columns and clipped rows.

    This collector is deliberately conservative: unusual tables produce fewer
    candidates rather than unbounded screenshots of the surrounding desktop.
    """
    h,w=image.shape[:2]
    color=cv2.inRange(image,(60,30,30),(150,105,105))
    blue,green,red=cv2.split(image)
    color[(blue.astype(int)<red.astype(int)+8)|(blue.astype(int)<green.astype(int)+8)]=0
    rows=np.flatnonzero((color[:,round(w*.06):round(w*.95)]>0).mean(axis=1)>.55)
    if not len(rows):
        return []
    bands=np.split(rows,np.flatnonzero(np.diff(rows)>1)+1)
    result=[]
    for band in bands:
        top,bottom=int(band[0]),int(band[-1])+1
        if top<h*.12 or top==0 or bottom>=h or not 12<=bottom-top<=70:
            continue
        patch=image[top:bottom].copy()
        line=complete_stat_line(patch)
        if line is not None:result.append(line)
    return result


class ReviewCollector:
    def __init__(self,store,interval=2,automatic=True,review_ocr=None):
        self.store,self.interval=store,interval
        self.automatic,self.review_ocr=automatic,review_ocr
        self.last_time=-1e10
        self.last_key=None
        self.last_result=None
        self.readers={}
        self.line_readers={}
        self.revision=-1
        from forgely_reading_review import ReviewReader
        self.bundled=calibrated_export_readers()
        self.reference_bank=ReviewReader(self.bundled)
        from forgely_cv.lines import GenericLineReader
        self.generic_bank=GenericLineReader(self.bundled)
        # Migrate only unanswered machine crops; never alter confirmed labels.
        from forgely_reading_review import decode
        for example in self.store.pending():
            if example['kind']!='stat':continue
            row=self.store.get(example['id']);old=decode(row['image'])
            line=complete_stat_line(old)
            if line is None or self.reference_bank.read_visible(line).jet:
                self.store.retire(row['id'])
            elif old.shape!=line.shape or not np.array_equal(old,line):
                self.store.retire(row['id'])
                self.store.offer(line,scale=row['scale'],suggestion=row['suggestion'] or '',context=row['context'] or '')

    def retire_recognized(self):
        """Remove obsolete questions when trusted references now read the row."""
        from forgely_reading_review import decode,ReviewReader
        from forgely_cv.lines import GenericLineReader
        banks={}
        refresh=self.store.revision()!=self.revision
        for candidate in [*self.store.pending(),*self.store.automatic_pending()]:
            row=self.store.get(candidate['id'])
            image=decode(row['image'])
            scale=row['scale']
            if scale not in banks:
                if not refresh and scale in self.readers:
                    banks[scale]=(self.line_readers[scale],self.readers[scale])
                else:
                    manual=self.store.reader(scale)
                    refs=[*self.bundled,*(manual.readers if manual else [])]
                    banks[scale]=(GenericLineReader(refs),ReviewReader(refs))
            if row['kind']=='stat':
                line=complete_stat_line(image)
                if line is None:continue
                reader=banks[scale][0]
                resolved=reader.read_line(line) is not None
            else:
                reader=banks[scale][1]
                resolved=reader.read_visible(image).pool is not None
            if resolved:self.store.retire(row['id'])

    def observe(self,effects,pool,effects_text,pool_text,*,context,token,expected=None):
        self.expected=expected or {}
        now=monotonic()
        collect_allowed=now-self.last_time>=self.interval
        if collect_allowed:self.last_time=now
        if collect_allowed:self.retire_recognized()
        if any(word in norm(effects_text) for word in ('prix moyen','quantite en','panoplie','comparer avec','valeurs theor')):
            return None
        bgr=cv2.cvtColor(np.asarray(effects.convert('RGB')),cv2.COLOR_RGB2BGR)
        pool_bgr=cv2.cvtColor(np.asarray(pool.convert('RGB')),cv2.COLOR_RGB2BGR)
        key=hashlib.sha256(repr((bgr.shape,pool_bgr.shape,context,sorted(self.expected.items()),effects_text,pool_text)).encode()+
                          number_mask(bgr).tobytes()+number_mask(pool_bgr).tobytes()).hexdigest()
        revision=self.store.revision()
        if key==self.last_key and revision==self.revision and not self.store.automatic_pending():
            return {**self.last_result,'token':token} if self.last_result is not None else None
        if revision!=self.revision:
            self.readers.clear();self.line_readers.clear();self.revision=revision
        scale=f'effects:{effects.width}x{effects.height}:bright-v1'
        pool_scale=f'pool:{pool.width}x{pool.height}:bright-v1'
        for name in (scale,pool_scale):
            if name not in self.readers:
                from forgely_reading_review import ReviewReader
                manual=self.store.reader(name)
                references=[*self.bundled,*(manual.readers if manual else [])]
                self.readers[name]=ReviewReader(references)
                from forgely_cv.lines import GenericLineReader
                self.line_readers[name]=GenericLineReader(references)
        reader=self.readers[scale]
        generic=self.line_readers[scale]
        visual_jet=generic.read_effects(bgr)
        patches=effect_rows(bgr)
        proposals=list(parse_jet(effects_text).items())
        # Never pair a label to a row by index when OCR missed any row.
        aligned=len(proposals)==len(patches)
        for index,patch in enumerate(patches):
            fast=generic.read_line(patch)
            known_jet=dict([fast]) if fast else reader.read_visible(patch).jet
            if known_jet:
                if aligned and known_jet!=dict([proposals[index]]):
                    pass  # A disagreement is a review candidate too.
                else:
                    continue
            if not collect_allowed:continue
            suggestion=(f'{proposals[index][1]} {proposals[index][0]}' if aligned else
                        '\n'.join(f'{v} {k}' for k,v in proposals))
            ident=self.store.offer(patch,scale=scale,suggestion=suggestion,context=context)
            if ident and self.automatic:self.store.defer_automatic(ident)
        pool_reader=self.readers[pool_scale]
        pool_read=pool_reader.read_visible(pool_bgr) if pool_reader else None
        if collect_allowed and (not pool_read or pool_read.pool is None):
            ident=self.store.offer(pool_bgr,scale=pool_scale,suggestion=pool_text,context=context,kind='pool')
            if ident and self.automatic:self.store.defer_automatic(ident)
        if collect_allowed and self.automatic:self.process_automatic()
        from forgely_vision_guidance import reference_report
        result=dict(pending=len(self.store.pending()),token=token,
                    automatic_pending=len(self.store.automatic_pending()),
                    reference=reference_report(self.expected,visual_jet),
                    visual_jet=visual_jet,
                    visual_pool=str(pool_read.pool) if pool_read and pool_read.pool is not None else None,
                    used_for_advice=False)
        self.last_key,self.last_result=key,result
        return dict(result)

    def process_automatic(self):
        """One targeted corroboration per cycle; unknown digit shapes never train.

        Automatic labels need agreement of full-panel OCR, independent row OCR,
        and already validated pixel glyphs. Two distinct examples are required
        before an automatic label is available to the visual catalogue.
        """
        from PIL import Image
        from forgely_reading_review import decode
        from forgely_cv.lines import GenericLineReader
        waiting=self.store.automatic_pending()
        if not waiting:return
        # Spend the single targeted OCR budget on a documented natural line
        # first. Extra/exo lines remain eligible; their values are never clamped.
        from forgely_dofocus import canonical_stat
        required={canonical_stat(k) for k in getattr(self,'expected',{})}
        waiting.sort(key=lambda r:not bool(required & {canonical_stat(k) for k in parse_jet(r['suggestion'] or '')}))
        row=self.store.get(waiting[0]['id']);image=decode(row['image'])
        references=[*self.bundled]
        manual=self.store.reader(row['scale'])
        if manual:references.extend(manual.readers)
        candidate=GenericLineReader(references).number_candidate(image,row['kind'])
        if candidate is not None:
            native,text,value,number_box,label_box=candidate
            # Candidate extraction trims margins; stored rectangles must remain
            # relative to the archived image rather than the trimmed preview.
            _,_,offset,_=cv2.minMaxLoc(cv2.matchTemplate(image,native,cv2.TM_SQDIFF))
            ox,oy=offset
            if not np.array_equal(image[oy:oy+native.shape[0],ox:ox+native.shape[1]],native):
                self.store._state(row['id'],'needs_review');return
            number_box=(number_box[0]+ox,number_box[1]+oy,*number_box[2:])
            label_box=(label_box[0]+ox,label_box[1]+oy,*label_box[2:])
            if self.review_ocr is None:
                from runeforge_observer import extract_text
                ocr=extract_text
            else:ocr=self.review_ocr
            targeted_text=ocr(Image.fromarray(cv2.cvtColor(native,cv2.COLOR_BGR2RGB)))
            if row['kind']=='pool':
                from decimal import Decimal
                from forgely_atelier import parse_reliquat
                a,b=parse_reliquat(row['suggestion'] or ''),parse_reliquat(targeted_text)
                if a is not None and b is not None and Decimal(str(a))==Decimal(str(b))==value:
                    try:
                        self.store.confirm(row['id'],text,'Puits',number_box,label_box,
                                           origin='automatic_numeric_agreement')
                        return
                    except ValueError:pass
                self.store._state(row['id'],'needs_review');return
            from forgely_dofocus import normalise_jet
            proposed=normalise_jet(parse_jet(row['suggestion'] or '')) or {}
            targeted=normalise_jet(parse_jet(targeted_text)) or {}
            if len(targeted)==1:
                name,number=next(iter(targeted.items()))
                visual=GenericLineReader(references).read_line(native)
                if visual is not None and canonical_stat(visual[0])!=name:
                    self.store._state(row['id'],'needs_review');return
                if number==value and proposed.get(name)==value:
                    try:
                        self.store.confirm(row['id'],text,name,number_box,label_box,
                                           origin='automatic_numeric_agreement')
                        return
                    except ValueError:
                        pass
        self.store._state(row['id'],'needs_review')
