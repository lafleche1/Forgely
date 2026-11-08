"""Repérage d'une ancre fixe et conversion vers des rectangles absolus."""
from dataclasses import dataclass
import cv2
import numpy as np
from .geometry import Rect, LayoutProfile


@dataclass(frozen=True)
class Detection:
    anchor: Rect
    game: Rect
    stats: Rect
    chat: Rect
    score: float


class InterfaceDetector:
    def __init__(self, template, profile: LayoutProfile, threshold=.95, ambiguity_margin=.025):
        if not 0 < threshold <= 1 or not 0 <= ambiguity_margin < 1:
            raise ValueError('Seuil de détection invalide')
        self.template = self._gray(template).copy()
        if min(self.template.shape) < 3 or self.template.std() < 2:
            raise ValueError('Template trop petit ou uniforme : choisir une ancre distinctive')
        self.profile, self.threshold, self.margin = profile, threshold, ambiguity_margin

    @staticmethod
    def _gray(image):
        if not isinstance(image, np.ndarray) or image.dtype != np.uint8 or image.size == 0:
            raise ValueError('Image uint8 non vide requise')
        if image.ndim == 2:
            return np.ascontiguousarray(image)
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError('Image BGR ou gris requise')
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def locate(self, image, origin=(0, 0), search=None):
        """Renvoie None dès que l'ancre est absente, ambiguë ou hors cadre.

        origin : coordonnées écran du coin de la capture (peuvent être négatives).
        search : rectangle absolu facultatif ; permet un suivi local économique.
        La recherche globale coûte davantage que la comparaison d'une petite ROI.
        """
        frame = Rect(origin[0], origin[1], image.shape[1], image.shape[0])
        area = search or frame
        if not frame.contains(area):
            return None
        gray = self._gray(area.crop(image, origin))
        h, w = self.template.shape
        if gray.shape[0] < h or gray.shape[1] < w:
            return None
        scores = cv2.matchTemplate(gray, self.template, cv2.TM_CCOEFF_NORMED)
        _, score, _, (x, y) = cv2.minMaxLoc(scores)
        if not np.isfinite(score) or score < self.threshold:
            return None
        # Supprimer le pic et ses voisinages chevauchants pour chercher une
        # deuxième occurrence distincte, plutôt que forcer arbitrairement un choix.
        scores[max(0, y-h+1):y+h, max(0, x-w+1):x+w] = -1
        second = float(scores.max())
        if score-second < self.margin:
            return None
        anchor = Rect(area.x+x, area.y+y, w, h)
        game = self.profile.game_from_anchor.moved(anchor.x, anchor.y)
        if not frame.contains(game):
            return None
        return Detection(anchor, game, self.profile.stats.moved(game.x, game.y),
                         self.profile.chat.moved(game.x, game.y), float(score))


def locate_game_zone(image, reference, profile, origin=(0, 0), threshold=.95):
    """API simple demandée : (x, y, w, h) absolus, ou None."""
    found = InterfaceDetector(reference, profile, threshold).locate(image, origin)
    return found.game.tuple() if found else None
