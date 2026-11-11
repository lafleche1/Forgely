"""Item-independent numeric rows: font shapes + complete semantic labels.

No equipment name or expected value participates in recognition. Unknown glyphs,
cut labels, collisions and duplicate contradictory rows remain unreadable.
"""
import cv2
from .glyphs import GlyphReader, segment_glyphs
from .numbers import number_mask,parse_number


def tight(mask):
    x,y,w,h=cv2.boundingRect(mask)
    return mask[y:y+h,x:x+w].copy() if w and h else None


class GenericLineReader:
    def __init__(self,readers):
        templates={};self.labels={}
        for reader in readers:
            for group in reader.glyphs._groups.values():
                for char,pixels in group:
                    templates.setdefault(char,[]).append(pixels)
            for field in reader.fields:
                if field.kind!='stat':continue
                mask=tight(field.guard_mask)
                if mask is not None:
                    self.labels.setdefault((mask.shape,mask.tobytes()),set()).add(field.name)
        self.glyphs=GlyphReader(templates,max_error=0)

    def read_line(self,image):
        from forgely_review_collection import complete_stat_line
        image=complete_stat_line(image)
        if image is None:return None
        mask=number_mask(image);parts=segment_glyphs(mask)
        if not parts or len({p.line for p in parts})!=1:return None
        matches=[self.glyphs.recognize(p.pixels) for p in parts]
        for start,match in enumerate(matches):
            if not match.accepted or match.text not in '+-0123456789':continue
            if start and parts[start].box.x-parts[start-1].box.x-parts[start-1].box.w<=3:
                continue  # Do not drop an unknown leading digit or sign.
            end=start+1
            while end<len(parts):
                gap=parts[end].box.x-parts[end-1].box.x-parts[end-1].box.w
                if gap>3 or not matches[end].accepted or matches[end].text not in '+-0123456789':break
                end+=1
            if end==len(parts):continue
            # '%' can touch the value. Exact matching of the entire remaining
            # label distinguishes it from an unrecognized trailing digit.
            text=''.join(m.text for m in matches[start:end]);value=parse_number(text,'stat')
            if value is None:continue
            label=tight(mask[:,parts[end].box.x:])
            if label is None:continue
            names=self.labels.get((label.shape,label.tobytes()),set())
            if len(names)==1:return next(iter(names)),int(value)
        return None

    def read_effects(self,image):
        from forgely_review_collection import effect_rows
        values={}
        for row in effect_rows(image):
            result=self.read_line(row)
            if result:
                name,value=result;values.setdefault(name,set()).add(value)
        return {k:next(iter(v)) for k,v in values.items() if len(v)==1}

    def number_candidate(self,image,kind='stat'):
        """Known digit shapes may locate an unknown label for corroboration.

        This does not assign a characteristic name and cannot itself teach one.
        """
        from forgely_review_collection import complete_stat_line
        image=complete_stat_line(image) if kind=='stat' else image
        if image is None:return None
        parts=segment_glyphs(number_mask(image))
        if not parts or len({p.line for p in parts})!=1:return None
        matches=[self.glyphs.recognize(p.pixels) for p in parts]
        for start,m in enumerate(matches):
            if not m.accepted or m.text not in '+-0123456789':continue
            if start and parts[start].box.x-parts[start-1].box.x-parts[start-1].box.w<=3:return None
            end=start+1
            allowed='+-0123456789' if kind=='stat' else '+-0123456789,.'
            while (end<len(parts) and matches[end].accepted and matches[end].text in allowed
                   and parts[end].box.x-parts[end-1].box.x-parts[end-1].box.w<=3):end+=1
            if end==len(parts) and kind=='stat':return None
            text=''.join(m.text for m in matches[start:end])
            value=parse_number(text,kind)
            if value is None:return None
            def bounds(group):
                x=min(p.box.x for p in group);y=min(p.box.y for p in group)
                r=max(p.box.x+p.box.w for p in group);b=max(p.box.y+p.box.h for p in group)
                return x,y,r-x,b-y
            label_parts=parts[end:] if kind=='stat' else parts[:start]
            if not label_parts:return None
            return image,text,(int(value) if kind=='stat' else value),bounds(parts[start:end]),bounds(label_parts)
        return None
