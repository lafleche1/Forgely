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
        from forgely_history_reader import VisualHistoryTracker
        self.visual=VisualHistoryTracker()
        self.visual_frame=0
        self.pending_icon = None
        self.pending_icon_count = 0
        self.suspended = False

    def read(self, image, context, ocr):
        if self.context is not None and context != self.context:
            self.reset('compte_modifie')
        if not workshop_visual_fallback(image):
            self.suspend('structure_atelier_absente')
            return PreviewRead(context_reset=True)
        icon = current_icon(image)
        if icon is None:
            self.suspend('icone_actuelle_absente')
            return PreviewRead(context_reset=True)
        if self.icon is not None and icon_distance(icon, self.icon) > 17:
            # A transient overlay is not a new item. Suspend all events until
            # three consecutive readable captures agree on replacement artwork.
            if self.pending_icon is None or icon_distance(icon, self.pending_icon) > 17:
                self.pending_icon = icon
                self.pending_icon_count = 1
            else:
                self.pending_icon_count += 1
            if self.pending_icon_count < 3:
                self.suspend('changement_icone_a_confirmer', keep_candidate=True)
                return PreviewRead(context_reset=True, needs_confirmation=True)
        else:
            self.pending_icon = None
            self.pending_icon_count = 0
        changed = (context != self.context or self.icon is None or
                   icon_distance(icon, self.icon) > 17)
        if changed:
            self.reset('compte_ou_icone_modifie')
            self.context = context
            self.icon = icon
        self.suspended = False
        history_patch = crop_zone(image, 'history')
        rune_patch = crop_zone(image, 'runes')
        history_patch.info['forgely_preview_zone'] = 'history'
        rune_patch.info['forgely_preview_zone'] = 'runes'
        # Pixel groups can be read without OCR of the entire history or the
        # selection toolbar. This preview remains provisional and never trains.
        self.visual.reader.ocr=ocr
        self.visual_frame+=1
        visual=self.visual.observe(history_patch,context,self.visual_frame)
        if visual.groups and any(g.outcome for g in visual.groups):
            self.reason=visual.reason
            # Old visible groups are the initial reference, not a new rune.
            # Re-emitting them keeps suspending a correctly confirmed jet.
            new_attempt=bool(visual.event or
                visual.needs_confirmation and self.visual.previous_history is not None)
            changes=tuple(visual.groups[-1].changes.items()) if new_attempt else ()
            self.diagnostic={'historique_visuel':True,'groupes':len(visual.groups),
                             'ocr_groupes':self.visual.reader.ocr_calls,
                             'cache_groupes_hits':self.visual.reader.cache_hits}
            return PreviewRead(visual.event,visual.needs_confirmation,changed,changes,
                               bool(visual.event))
        # Reuse text only on exact pixels with a short TTL. Confirmation still
        # requires separate captures; changed pixels always trigger fresh OCR.
        history = self.rune_cache.read('history', history_patch, ocr)
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

    def suspend(self, reason, *, keep_candidate=False):
        """Retain artwork, but never bridge an unreadable interval with events."""
        if not self.suspended:
            self.tracker = HistoryTransitionTracker(self.tracker.rune_names)
            self.delta.reset()
            self.rune_cache.clear()
            self.visual.reset()
        self.suspended = True
        if not keep_candidate:
            self.pending_icon = None
            self.pending_icon_count = 0
        self.reason = 'Lecture suspendue : ' + reason
        self.diagnostic = {'suspendue': reason, 'reinitialisations': dict(self.reset_counts)}

    def reset(self, reason='capture_invalidee'):
        self.reset_counts[reason] += 1
        self.tracker = HistoryTransitionTracker(self.tracker.rune_names)
        self.delta.reset()
        self.rune_cache.clear()
        self.context = None
        self.icon = None
        self.pending_icon = None
        self.pending_icon_count = 0
        self.suspended = False
        self.reason = 'Référence invalidée : ' + reason
        self.diagnostic = {'reinitialisations': dict(self.reset_counts)}
        self.visual.reset()
