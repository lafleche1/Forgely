"""Independent, provisional rune display; never writes observations or advice."""
from dataclasses import dataclass
from collections import Counter

from forgely_atelier import crop_zone, workshop_visual_fallback
from forgely_continuous_identity import current_icon
from forgely_detection import HistoryTransitionTracker, explicit_outcome
from forgely_item_icons import icon_distance
from forgely_history_delta import HistoryDeltaMonitor
from forgely_zone_cache import ZoneCache


@dataclass(frozen=True)
class PreviewRead:
    event: object = None
    needs_confirmation: bool = False
    context_reset: bool = False
    changes: tuple = ()
    changes_stable: bool = False


class FastRunePreview:
    def __init__(self, rune_names):
        self.tracker = HistoryTransitionTracker(rune_names)
        self.context = None
        self.icon = None
        self.delta = HistoryDeltaMonitor()
        self.rune_cache = ZoneCache(refresh_seconds=2)
        self.reset_counts = Counter()
        self.reason = self.tracker.reason
        self.diagnostic = {}

    def read(self, image, context, ocr):
        if not workshop_visual_fallback(image):
            self.reset('structure_atelier_absente')
            return PreviewRead(context_reset=True)
        icon = current_icon(image)
        if icon is None:
            self.reset('icone_actuelle_absente')
            return PreviewRead(context_reset=True)
        changed = (context != self.context or self.icon is None or
                   icon_distance(icon, self.icon) > 17)
        if changed:
            self.reset('compte_ou_icone_modifie')
            self.context = context
            self.icon = icon
        history_patch = crop_zone(image, 'history')
        rune_patch = crop_zone(image, 'runes')
        history_patch.info['forgely_preview_zone'] = 'history'
        rune_patch.info['forgely_preview_zone'] = 'runes'
        # History is read independently on each confirmation. Rune text may
        # be reused only while its exact pixels and short TTL are unchanged.
        history = ocr(history_patch)
        delta = self.delta.observe(history)
        has_outcome = any(explicit_outcome(line) for line in history.splitlines())
        event = None
        rune = ''
        if has_outcome:
            rune = self.rune_cache.read('runes', rune_patch, ocr)
            event = self.tracker.observe(history, rune)
            self.reason = self.tracker.reason
        else:
            # Current DOFUS can show only signed stat rows. They are useful
            # observations, never evidence of SC/SN/EC or of a rune's identity.
            self.tracker = HistoryTransitionTracker(self.tracker.rune_names)
            self.reason = 'Variations de caractéristiques · aucun résultat SC/SN/EC explicite'
        pending = bool(self.delta.pending or self.tracker.pending_count or
                       (self.tracker.baseline is None and self.tracker._init_count == 1))
        changes = tuple(delta['new_changes'] or delta.get('candidate_changes', ()))
        from runeforge_observer import find_rune
        self.diagnostic = {'historique_avec_resultat': has_outcome,
                           'rune_reconnue': find_rune(rune, self.tracker.rune_names),
                           'variations': delta['status'], 'reinitialisations': dict(self.reset_counts),
                           'cache_rune_hits': self.rune_cache.hits}
        return PreviewRead(event, pending, changed, changes, bool(delta['new_changes']))

    def reset(self, reason='capture_invalidee'):
        self.reset_counts[reason] += 1
        self.tracker = HistoryTransitionTracker(self.tracker.rune_names)
        self.delta.reset()
        self.rune_cache.clear()
        self.context = None
        self.icon = None
        self.reason = 'Référence invalidée : ' + reason
        self.diagnostic = {'reinitialisations': dict(self.reset_counts)}
