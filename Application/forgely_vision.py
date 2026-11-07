"""Conservative local icon recognition using labelled player-owned reference crops.

No external asset scraping, model download, network call or game input.
A visual result is returned ONLY for a close, unambiguous comparison to
locally trained references. Template matching is not universal rune recognition.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import math
from PIL import Image, ImageOps, ImageFilter

SIDE = 32
# Distance thresholds intentionally strict: tune from labeled real captures.
MAX_DISTANCE = 0.10
MIN_MARGIN = 0.055


def canonical(image: Image.Image) -> Image.Image:
    # Image is cropped tightly to the slot/icon, consistently for learning and inference.
    return ImageOps.fit(image.convert('RGB'), (SIDE, SIDE), method=Image.Resampling.LANCZOS)


def features(image: Image.Image):
    im = canonical(image)
    rgb = list(im.getdata())
    gray = list(ImageOps.grayscale(im).getdata())
    # Colors and contours jointly distinguish differently shaped/colored runes.
    edge = list(ImageOps.grayscale(im).filter(ImageFilter.FIND_EDGES).getdata())
    return rgb, gray, edge


def distance(image_a: Image.Image, image_b: Image.Image) -> float:
    ca, ga, ea = features(image_a)
    cb, gb, eb = features(image_b)
    n = len(ga)
    color = sum(sum(abs(a[j]-b[j]) for j in range(3)) for a,b in zip(ca,cb)) / (3*255*n)
    luminance = sum(abs(a-b) for a,b in zip(ga,gb)) / (255*n)
    contours = sum(abs(a-b) for a,b in zip(ea,eb)) / (255*n)
    return .48*color + .22*luminance + .30*contours


@dataclass(frozen=True)
class IconMatch:
    rune: str | None
    distance: float | None
    margin: float | None
    reason: str


class RuneLibrary:
    def __init__(self, directory: Path, rune_names):
        self.directory=Path(directory)
        self.catalogue_directory=self.directory.parent / "catalogue_dofus3"
        self.allowed=set(rune_names)
        self.references=[]
        self.load()

    def load(self):
        self.references=[]
        folders = [self.directory, self.catalogue_directory]
        if self.directory.name == "icones_runes" and self.directory.parent.name == "Forgely":
            folders.append(Path(__file__).parent / "catalogue_dofus3")
        for folder in folders:
            meta=folder/'index.json'
            if not meta.is_file():continue
            try:
                entries=json.loads(meta.read_text(encoding='utf8'))
                if not isinstance(entries,list):continue
                for entry in entries:
                    filename=entry.get('file','')
                    path=folder/filename
                    if (entry.get('rune') in self.allowed and
                        Path(filename).name == filename and filename.endswith('.png') and path.is_file()):
                        with Image.open(path) as im:self.references.append((entry['rune'],canonical(im)))
            except (OSError,ValueError,KeyError,TypeError):
                continue

    def add(self, rune, icon: Image.Image):
        if rune not in self.allowed:raise ValueError('Rune non répertoriée')
        self.directory.mkdir(parents=True,exist_ok=True)
        index=self.directory/'index.json'
        try: data=json.loads(index.read_text(encoding='utf8')) if index.is_file() else []
        except (OSError,ValueError): data=[]
        # Sanitized numeric filename; never derive paths from supplied rune.
        filename=f'icone_{len(data)+1:05d}.png'
        canonical(icon).save(self.directory/filename)
        data.append({'rune':rune,'file':filename})
        index.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
        self.load()

    def labels(self):
        return sorted({r for r,_ in self.references})

    def predict(self, patch: Image.Image):
        if not self.references:return IconMatch(None,None,None,'Bibliothèque d’icônes vide : ajouter des références')
        by_rune={}
        for name,ref in self.references:
            d=distance(patch,ref)
            by_rune[name]=min(d,by_rune.get(name,1.0))
        ranked=sorted(by_rune.items(),key=lambda kv:kv[1])
        winner,best=ranked[0]
        runner=ranked[1][1] if len(ranked)>1 else 1.0
        margin=runner-best
        if best > MAX_DISTANCE:return IconMatch(None,best,margin,'Icône différente des références')
        if len(ranked)>1 and margin < MIN_MARGIN:
            return IconMatch(None,best,margin,'Icône ambiguë : plusieurs runes se ressemblent')
        return IconMatch(winner,best,margin,'Référence visuelle concordante (à vérifier en jeu)')


def icon_patch(image: Image.Image, x: float, y: float, size: int=36) -> Image.Image:
    """Crop around a user-calibrated pixel position in the game window."""
    if not 0 <= x < image.width or not 0 <= y < image.height:
        raise ValueError('Position de rune hors capture')
    h=size//2
    x1=max(0,min(image.width-size,int(x)-h))
    y1=max(0,min(image.height-size,int(y)-h))
    return image.crop((x1,y1,x1+size,y1+size))
