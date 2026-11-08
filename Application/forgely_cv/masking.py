"""Masques binaires HSV : pixels retenus blancs, fond strictement noir.

Les couleurs sont une segmentation, pas la preuve d'un SC/SN/EC. Une perte
rouge peut apparaître dans une tentative qui a aussi augmenté une autre ligne.
Les plages doivent être calibrées sur les vraies captures du joueur.
"""
import cv2
import numpy as np

# OpenCV uint8 : teinte 0..179, saturation et valeur 0..255.
# Le rouge traverse la discontinuité 179 -> 0 et nécessite deux plages.
DEFAULT_RANGES = {
    'green': (((35, 80, 90), (90, 255, 255)),),
    'red': (((0, 90, 90), (12, 255, 255)), ((168, 90, 90), (179, 255, 255))),
    'blue': (((95, 80, 90), (130, 255, 255)),),
}


def chat_masks(bgr, ranges=None):
    if bgr.dtype != np.uint8 or bgr.ndim != 3 or bgr.shape[2] != 3 or not bgr.size:
        raise ValueError('Zone de chat BGR uint8 requise')
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    result = {}
    for name, intervals in (DEFAULT_RANGES if ranges is None else ranges).items():
        mask = np.zeros(hsv.shape[:2], np.uint8)
        for low, high in intervals:
            if any(not 0 <= a <= b <= limit for a, b, limit in zip(low, high, (179, 255, 255))):
                raise ValueError('Plage HSV invalide')
            cv2.bitwise_or(mask, cv2.inRange(hsv, np.array(low, np.uint8), np.array(high, np.uint8)), dst=mask)
        result[name] = mask
    # Pas d'érosion/ouverture par défaut : elle pourrait effacer un signe −
    # ou une virgule. Les icônes de même couleur peuvent aussi rester dans le masque.
    return result


def colored_on_black(bgr, mask):
    """Alternative de debug : conserver la couleur originale sur fond noir."""
    return cv2.bitwise_and(bgr, bgr, mask=mask)
