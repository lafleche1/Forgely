"""Small, user-confirmed rune-gutter references; ambiguous tiers stay unknown.

These crops train visual recognition only. They never enter player outcome
counts. New rune families can use selection OCR until independently labelled.
"""
from functools import lru_cache
from pathlib import Path
import json
import numpy as np
from PIL import Image

ROOT=Path(__file__).parent/'references'/'history_unity'


def features(image):
    a=np.asarray(image.convert('RGB')).astype(int)
    background=np.median(a,axis=(0,1))
    mask=(abs(a-background).max(2)>35)&(a.max(2)>90)
    ys,xs=np.where(mask)
    if len(xs)<15:return None
    a[~mask]=0
    icon=Image.fromarray(a.astype('uint8')).crop((int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)))
    icon.thumbnail((28,28))
    square=Image.new('RGB',(30,30));square.paste(icon,((30-icon.width)//2,(30-icon.height)//2))
    return np.asarray(square).astype(float)/255


@lru_cache(maxsize=1)
def references():
    try:
        data=json.loads((ROOT/'index.json').read_text(encoding='utf8'))
        return tuple((row['rune'],features(Image.open(ROOT/row['file']))) for row in data['icons']
                     if Path(row['file']).name==row['file'])
    except (OSError,ValueError,KeyError):return ()


def recognize(image):
    value=features(image)
    if value is None:return None
    scores={}
    for rune,template in references():
        if template is None:continue
        distance=float(np.abs(template-value).mean())
        scores[rune]=min(scores.get(rune,1.),distance)
    ordered=sorted((d,r) for r,d in scores.items())
    if not ordered or ordered[0][0]>.04:return None
    if len(ordered)>1 and ordered[1][0]-ordered[0][0]<.006:return None
    return ordered[0][1]
