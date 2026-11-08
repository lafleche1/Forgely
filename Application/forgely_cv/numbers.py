"""Lecture numérique sur des colonnes et libellés explicitement calibrés.

Pas d'OCR externe. Les noms des statistiques viennent des annotations manuelles,
jamais leurs valeurs. Un garde visuel du libellé évite d'associer un nombre à
une ancienne ligne après changement d'objet ou déplacement de l'interface.
"""
from dataclasses import dataclass
from collections import deque
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import cv2
import numpy as np
from .geometry import Rect
from .glyphs import GlyphReader, segment_glyphs


def number_mask(bgr, mode='bright'):
    """Masque natif sans redimensionnement, ni suppression de ponctuation."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    if mode == 'bright':
        return cv2.inRange(hsv, (0, 0, 130), (179, 255, 255))
    if mode == 'white':
        return cv2.inRange(hsv, (0, 0, 160), (179, 80, 255))
    raise ValueError('Masque numérique inconnu : '+mode)


def parse_number(text, kind):
    """Decimal conserve exactement le reliquat ; aucun O corrigé en zéro."""
    if kind not in ('stat','pool'):
        raise ValueError('Type de champ inconnu')
    if not re.fullmatch(r'[+-]?\d+(?:[.,]\d{1,3})?',text):
        return None
    integer=re.split(r'[.,]',text.lstrip('+-'))[0]
    if len(integer)>1 and integer.startswith('0'):
        return None  # 01 ne doit pas devenir 1 si la virgule de 0,1 disparaît.
    try:
        value=Decimal(text.replace(',','.'))
    except InvalidOperation:
        return None
    if abs(value)>30000 or kind=='pool' and text.startswith('-'):
        return None
    if kind=='stat' and ('.' in text or ',' in text):
        return None
    return value


@dataclass
class NumericField:
    name: str
    kind: str
    box: Rect
    guard_box: Rect
    guard_mask: np.ndarray
    mode: str = 'bright'
    guard_mode: str = 'bright'
    guard_error: float = .03

    def __post_init__(self):
        if self.kind not in ('stat','pool') or not self.name or not 0<=self.guard_error<=.1:
            raise ValueError('Champ numérique invalide')
        if self.guard_mask.dtype!=np.uint8 or self.guard_mask.ndim!=2 or self.guard_mask.shape!=(self.guard_box.h,self.guard_box.w):
            raise ValueError('Garde visuel incompatible')
        if cv2.countNonZero(self.guard_mask)<3:
            raise ValueError('Garde visuel vide')


@dataclass
class NumericReading:
    jet: dict
    pool: Decimal | None
    fields: dict
    accepted: bool

    def as_dict(self):
        # Le puits reste une chaîne décimale exacte dans les exports JSON.
        return dict(jet=self.jet,pool=str(self.pool) if self.pool is not None else None,
                    fields=self.fields,accepted=self.accepted,
                    temporal_confirmation=False,source='local_glyph_templates')


class NumericReader:
    def __init__(self, glyphs, fields, image_size=None, scale_tag='native'):
        self.glyphs,self.fields,self.image_size,self.scale_tag=glyphs,list(fields),image_size,scale_tag
        if not self.fields or len({f.name for f in self.fields})!=len(self.fields):
            raise ValueError('Champs absents ou noms dupliqués')
        if sum(f.kind=='pool' for f in self.fields)>1:
            raise ValueError('Un seul champ de reliquat autorisé')

    def read_visible(self, image):
        """Find calibrated labels anywhere in a native-pixel effects panel.

        The label, not its old row index, anchors the numeric ROI. Missing,
        clipped or duplicated labels remain unknown. No resize is applied:
        another UI scale requires its own glyph/label references.
        """
        from dataclasses import replace
        masks = {}
        fields = []
        missing = {}
        for field in self.fields:
            if field.guard_mode not in masks:
                masks[field.guard_mode] = number_mask(image, field.guard_mode)
            mask = masks[field.guard_mode]
            guard = field.guard_mask
            h, w = guard.shape
            if h > mask.shape[0] or w > mask.shape[1]:
                missing[field.name] = {'accepted': False, 'error': 'libelle_hors_vue'}
                continue
            scores = cv2.matchTemplate(mask, guard, cv2.TM_SQDIFF)
            # Binary XOR distance expressed as a fraction of all native pixels.
            scores /= float(255**2 * h * w)
            _, _, (x, y), _ = cv2.minMaxLoc(scores)
            error = float(scores[y, x])
            scores[max(0,y-h+1):y+h, max(0,x-w+1):x+w] = 1
            second = float(scores.min())
            # matchTemplate accumulates floating-point roundoff even for two
            # identical binary patches (e.g. 2e-17 instead of zero). The actual
            # guard is checked again by XOR in read(), so this epsilon never
            # relaxes a requested exact pixel comparison.
            search_error=max(field.guard_error,1e-6)
            if error > search_error or second <= search_error:
                missing[field.name] = {'accepted': False, 'error': 'libelle_absent_ou_ambigu'}
                continue
            dx, dy = x-field.guard_box.x, y-field.guard_box.y
            box = field.box.moved(dx, dy)
            # Never infer digits from a cropped number at a viewport edge.
            if not Rect(0,0,image.shape[1],image.shape[0]).contains(box):
                missing[field.name] = {'accepted': False, 'error': 'nombre_tronque'}
                continue
            # A longer value pushes its label rightward. Reusing the old width
            # could silently read the last digit of 111 as 1. Scan the complete
            # adjacent run to the left, stopping only at a genuine word gap.
            label_before = field.guard_box.x+field.guard_box.w <= field.box.x
            right = (min(image.shape[1],box.x+max(96,box.w*4)) if label_before else box.x+box.w)
            left = box.x if label_before else max(0, right-max(96, box.w*4))
            scan = Rect(left, box.y, right-left, box.h)
            pieces = segment_glyphs(number_mask(scan.crop(image), field.mode))
            if not pieces or len({p.line for p in pieces}) != 1:
                missing[field.name] = {'accepted': False, 'error': 'nombre_absent_ou_ambigu'}
                continue
            if label_before:
                group = [pieces[0]]
                for piece in pieces[1:]:
                    if piece.box.x-group[-1].box.x-group[-1].box.w>3:
                        break
                    group.append(piece)
            else:
                group = [pieces[-1]]
                for piece in reversed(pieces[:-1]):
                    if group[0].box.x-piece.box.x-piece.box.w > 3:
                        break
                    group.insert(0,piece)
            if (not label_before and group[0].box.x == 0 or
                    label_before and group[-1].box.x+group[-1].box.w == scan.w):
                missing[field.name] = {'accepted': False, 'error': 'nombre_tronque'}
                continue
            box = Rect(left+group[0].box.x, box.y,
                       group[-1].box.x+group[-1].box.w-group[0].box.x, box.h)
            fields.append(replace(field, box=box, guard_box=field.guard_box.moved(dx,dy)))
        if not fields:
            return NumericReading({}, None, missing, False)
        result = NumericReader(self.glyphs, fields).read(image)
        result.fields.update(missing)
        result.accepted = result.accepted and not missing
        return result

    @classmethod
    def from_directory(cls, folder):
        root=Path(folder).resolve()
        data=json.loads((root/'numbers.json').read_text(encoding='utf8'))
        fields=[]
        for row in data['fields']:
            path=(root/row['guard']).resolve()
            if not path.is_relative_to(root):
                raise ValueError('Garde hors du profil')
            guard=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE)
            if guard is None:raise ValueError('Garde absent : '+str(path))
            fields.append(NumericField(row['name'],row['kind'],Rect(**row['box']),
                Rect(**row['guard_box']),guard,row.get('mode','bright'),row.get('guard_mode','bright')))
        # Exact par défaut : un chiffre absent ne doit pas être remplacé par
        # un autre à une faible distance. Tolérance à augmenter après validation.
        glyphs=GlyphReader.from_directory(root/'font',max_error=0,ambiguity_margin=.025)
        return cls(glyphs,fields,tuple(data['image_size']),data.get('scale_tag','native'))

    def read(self, game_bgr):
        jet, pool, details = {}, None, {}
        size=(game_bgr.shape[1],game_bgr.shape[0])
        if self.image_size is not None and size!=self.image_size:
            return NumericReading({},None,{'profile':{'error':'dimensions_incompatibles'}},False)
        for field in self.fields:
            try:
                guard=number_mask(field.guard_box.crop(game_bgr),field.guard_mode)
                # Comparer l'union des pixels de texte, et non le fond majoritaire.
                union=cv2.countNonZero(cv2.bitwise_or(guard,field.guard_mask))
                mismatch=cv2.countNonZero(cv2.bitwise_xor(guard,field.guard_mask))/max(1,union)
                if mismatch>field.guard_error:
                    details[field.name]={'accepted':False,'error':'libelle_ou_position_modifie'}
                    continue
                mask=number_mask(field.box.crop(game_bgr),field.mode)
                pieces=segment_glyphs(mask)
                # Un nombre appartient à une seule ligne et ses caractères sont
                # proches : ne pas joindre les colonnes Min/Max/Modif en un entier.
                if not pieces or len({p.line for p in pieces})!=1 or any(
                        b.box.x-a.box.x-a.box.w>3 for a,b in zip(pieces,pieces[1:])):
                    details[field.name]={'accepted':False,'error':'vide_ou_espacement_ambigu'}
                    continue
                matches=[self.glyphs.recognize(p.pixels) for p in pieces]
                text=''.join(m.text for m in matches)
                value=parse_number(text,field.kind) if all(m.accepted for m in matches) else None
                details[field.name]={'text':text,'accepted':value is not None,
                                     'error':None if value is not None else 'glyphe_ou_nombre_inconnu'}
                if value is not None:
                    if field.kind=='pool':pool=value
                    else:jet[field.name]=int(value)
            except ValueError as exc:
                details[field.name]={'accepted':False,'error':str(exc)}
        accepted=len(details)==len(self.fields) and all(row.get('accepted') for row in details.values())
        return NumericReading(jet,pool,details,accepted)


class NumericStabilizer:
    """Confirmation temporelle facultative, distincte de la reconnaissance.

    L'appelant fournit un contexte d'objet/session et l'identifiant de capture.
    Répéter le même frame ne compte jamais comme plusieurs observations.
    """
    def __init__(self, frames=3, max_age_ms=1000):
        if type(frames) is not int or frames<2 or max_age_ms<=0:
            raise ValueError('Stabilisation invalide')
        self.frames,self.max_age_ns=frames,int(max_age_ms*1e6)
        self.reset()

    def reset(self):
        self._context=None;self._sequence=None;self._key=None;self.count=0
        self._captured_ns=None;self._times=deque(maxlen=self.frames)

    def observe(self, reading, *, context, sequence, captured_ns, now_ns=None):
        from time import perf_counter_ns
        now=perf_counter_ns() if now_ns is None else now_ns
        if (context is None or type(sequence) is not int or not reading.accepted
                or not 0<=now-captured_ns<=self.max_age_ns):
            self.reset();return False
        if context!=self._context:
            self.reset();self._context=context
        if self._sequence is not None and sequence<=self._sequence:
            self.count=0;self._key=None
            return False
        if self._captured_ns is not None and captured_ns<=self._captured_ns:
            self.count=0;self._key=None;self._sequence=sequence
            return False
        self._sequence=sequence
        self._captured_ns=captured_ns
        key=(tuple(sorted(reading.jet.items())),reading.pool)
        if key!=self._key:self._times.clear()
        self._times.append(captured_ns)
        while self._times and now-self._times[0]>self.max_age_ns:
            self._times.popleft()
        self.count=len(self._times)
        self._key=key
        return self.count>=self.frames


def calibrate_numbers(image, annotations, output):
    """Construire un profil à partir de ROIs et de transcriptions MANUELLES.

    L'image annotée devient une donnée de calibration : sa relecture n'est pas
    une validation indépendante. Les valeurs attendues ne sont pas conservées
    dans le profil d'inférence ; seuls formes et libellés sont enregistrés.
    """
    root=Path(output)
    if (root/'numbers.json').exists():
        raise ValueError('Ce profil existe déjà : choisir un nouveau dossier pour préserver la calibration')
    root.mkdir(parents=True,exist_ok=True)
    font=root/'font';font.mkdir(exist_ok=True)
    fields=[];glyphs=[];index=0
    for row in [*annotations['fields'],*annotations.get('samples',[])]:
        if 'kind' in row and parse_number(row['text'],row['kind']) is None:
            raise ValueError('Transcription numérique invalide : '+row['name'])
        rect=Rect(*row['box']);mode=row.get('mode','bright')
        mask=number_mask(rect.crop(image),mode)
        pieces=segment_glyphs(mask)
        text=row['text']
        if not re.fullmatch(r'[+\-0-9.,]+',text) or len(pieces)!=len(text) or len({p.line for p in pieces})!=1:
            raise ValueError(f"Découpage à vérifier pour {row.get('name',text)} : {len(pieces)} composants / {len(text)} caractères")
        for char,piece in zip(text,pieces):
            name=f'U+{ord(char):04X}-{index:04d}.png';index+=1
            if not cv2.imwrite(str(font/name),piece.pixels):raise OSError('Écriture du glyphe impossible')
            glyphs.append({'char':char,'file':name})
        if 'kind' in row:
            guard_box=Rect(*row['guard_box']);guard_mode=row.get('guard_mode','bright')
            guard=number_mask(guard_box.crop(image),guard_mode)
            guard_name=f'guard-{len(fields):03d}.png'
            field=NumericField(row['name'],row['kind'],rect,guard_box,guard,mode,guard_mode)
            cv2.imwrite(str(root/guard_name),field.guard_mask)
            from dataclasses import asdict
            fields.append(dict(name=field.name,kind=field.kind,box=asdict(rect),guard_box=asdict(guard_box),
                               guard=guard_name,mode=mode,guard_mode=guard_mode))
    (font/'manifest.json').write_text(json.dumps({'glyphs':glyphs},indent=2),encoding='utf8')
    data=dict(image_size=[image.shape[1],image.shape[0]],scale_tag=annotations.get('scale_tag','native'),fields=fields,
              calibration_only=True,supported_characters=sorted({r['char'] for r in glyphs}))
    (root/'numbers.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    return NumericReader.from_directory(root)
