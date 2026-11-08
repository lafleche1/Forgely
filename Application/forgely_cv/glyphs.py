"""Mini-lecteur matriciel : références réelles, sans apprentissage externe.

Un profil correspond à UNE police, UNE échelle et UN prétraitement. On ne
redimensionne pas les caractères pour masquer un changement de DPI. Contours
jointifs, ligatures et glyphes touchants restent des limites de cette V1.
"""
from dataclasses import dataclass
import json
from pathlib import Path
import cv2
import numpy as np
from .geometry import Rect


def binary(image):
    if image.ndim != 2 or image.dtype != np.uint8 or not image.size:
        raise ValueError('Masque de glyphes uint8 à un canal requis')
    return np.where(image > 127, 255, 0).astype(np.uint8)


@dataclass(frozen=True)
class Glyph:
    box: Rect
    pixels: np.ndarray
    line: int


@dataclass(frozen=True)
class GlyphMatch:
    text: str
    distance: float
    accepted: bool


def segment_glyphs(mask, line_gap=3):
    """Lignes par projection horizontale, composants par findContours.

    Fusionner les projections X qui se recouvrent conserve le point du i et
    les accents avec leur lettre. Ne pas supprimer les petits composants :
    ils peuvent être des signes, points ou virgules importants.
    """
    mask = binary(mask)
    rows = np.flatnonzero(np.any(mask, axis=1))
    if not len(rows):
        return []
    bands = np.split(rows, np.flatnonzero(np.diff(rows) > line_gap+1)+1)
    glyphs = []
    for number, band in enumerate(bands):
        top, bottom = int(band[0]), int(band[-1])+1
        line = mask[top:bottom]
        contours, _ = cv2.findContours(line.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        components = sorted((cv2.boundingRect(c) for c in contours), key=lambda b: b[0])
        groups = []
        for x, y, w, h in components:
            if groups and x < groups[-1][2]:
                a, b, c, d = groups[-1]
                groups[-1] = (a, min(b, y), max(c, x+w), max(d, y+h))
            else:
                groups.append((x, y, x+w, y+h))
        for x, y, right, bottom_local in groups:
            box = Rect(x, top+y, right-x, bottom_local-y)
            glyphs.append(Glyph(box, box.crop(mask).copy(), number))
    return glyphs


class GlyphReader:
    def __init__(self, templates, max_error=.12, ambiguity_margin=.025):
        if not 0 <= max_error < 1 or not 0 <= ambiguity_margin < 1:
            raise ValueError('Seuil de glyphes invalide')
        self.max_error, self.margin = max_error, ambiguity_margin
        # Regrouper par taille évite de comparer aux variantes incompatibles.
        self._groups = {}
        for char, variants in templates.items():
            if not isinstance(char, str) or len(char) != 1:
                raise ValueError('Une référence doit désigner un seul caractère')
            for image in variants:
                pixels = binary(image)
                box = cv2.boundingRect(pixels)
                if box[2] == 0:
                    raise ValueError('Référence de glyphe vide')
                pixels = pixels[box[1]:box[1]+box[3], box[0]:box[0]+box[2]]
                self._groups.setdefault(pixels.shape, []).append((char, pixels.copy()))

    @classmethod
    def from_directory(cls, folder, **kwargs):
        root = Path(folder).resolve()
        manifest = json.loads((root/'manifest.json').read_text(encoding='utf8'))
        templates = {}
        for entry in manifest['glyphs']:
            path = (root/entry['file']).resolve()
            if not path.is_relative_to(root):
                raise ValueError('Référence hors du dossier de police')
            image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError('Image de glyphe illisible : '+str(path))
            templates.setdefault(entry['char'], []).append(image)
        if not templates:
            raise ValueError('Aucun glyphe calibré dans '+str(root))
        return cls(templates, **kwargs)

    def recognize(self, image):
        pixels = binary(image)
        x, y, w, h = cv2.boundingRect(pixels)
        if not w:
            return GlyphMatch('?', 1., False)
        pixels = pixels[y:y+h, x:x+w]
        distances = {}
        for char, template in self._groups.get(pixels.shape, ()):
            # XOR binaire puis countNonZero en C ; aucune boucle Python par pixel.
            error = cv2.countNonZero(cv2.bitwise_xor(pixels, template))/pixels.size
            distances[char] = min(error, distances.get(char, 1.))
        ranked = sorted(distances.items(), key=lambda row: row[1])
        if not ranked:
            return GlyphMatch('?', 1., False)
        char, error = ranked[0]
        if error > self.max_error or len(ranked) > 1 and ranked[1][1]-error < self.margin:
            return GlyphMatch('?', error, False)
        return GlyphMatch(char, error, True)

    def read(self, mask, space_gap=4):
        """Texte, glyphes et validité. L'inconnu n'est jamais remplacé par zéro."""
        glyphs = segment_glyphs(mask)
        text, matches = '', []
        previous = None
        for glyph in glyphs:
            if previous is not None:
                if glyph.line != previous.line:
                    text += '\n'
                elif glyph.box.x-(previous.box.x+previous.box.w) >= space_gap:
                    text += ' '
            match = self.recognize(glyph.pixels)
            matches.append(match)
            text += match.text
            previous = glyph
        return text, matches, bool(matches) and all(m.accepted for m in matches)
