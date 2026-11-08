"""Coordonnées en pixels physiques. Aucun redimensionnement implicite."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    def __post_init__(self):
        if any(type(v) is not int for v in (self.x, self.y, self.w, self.h)):
            raise ValueError('Coordonnées entières requises')
        if self.w <= 0 or self.h <= 0:
            raise ValueError('Rectangle vide')

    def moved(self, x, y):
        return Rect(self.x + x, self.y + y, self.w, self.h)

    def contains(self, other):
        return (self.x <= other.x and self.y <= other.y and
                other.x + other.w <= self.x + self.w and
                other.y + other.h <= self.y + self.h)

    def crop(self, image, origin=(0, 0)):
        """Une vue NumPy sans copie ; refuse les rognages silencieux."""
        local = self.moved(-origin[0], -origin[1])
        if not Rect(0, 0, image.shape[1], image.shape[0]).contains(local):
            raise ValueError('Sous-zone hors de la capture')
        return image[local.y:local.y + local.h, local.x:local.x + local.w]

    def tuple(self):
        return self.x, self.y, self.w, self.h


@dataclass(frozen=True)
class LayoutProfile:
    # Offset du jeu par rapport au coin supérieur gauche du template détecté.
    # Un bouton seul ne permet PAS de déduire la taille de la fenêtre du jeu.
    game_from_anchor: Rect
    stats: Rect                  # Relatif au coin supérieur gauche du jeu.
    chat: Rect
    scale_tag: str = 'echelle-native-a-calibrer'

    def __post_init__(self):
        game = Rect(0, 0, self.game_from_anchor.w, self.game_from_anchor.h)
        if not game.contains(self.stats) or not game.contains(self.chat):
            raise ValueError('Les sous-zones doivent être à l’intérieur du jeu')

    def save(self, path):
        Path(path).write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding='utf8')

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text(encoding='utf8'))
        return cls(*(Rect(**data[k]) for k in ('game_from_anchor', 'stats', 'chat')),
                   scale_tag=data.get('scale_tag', 'non-renseigne'))
