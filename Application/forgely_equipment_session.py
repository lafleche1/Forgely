"""Explicit user-selected identity bound only to this workshop session.

Manual choices must never enroll visual references as automatically verified.
"""
from forgely_continuous_identity import CurrentSlotTracker, strong_signature_change
from forgely_item_icons import normalize_icon, icon_distance
from forgely_equipment_catalog import equipment_bounds
from forgely_jet import norm

class ManualEquipmentSession:
    def __init__(self,equipment):
        self.equipment=equipment
        self.tracker=CurrentSlotTracker(frames=3)
        self.replacement=CurrentSlotTracker(frames=3)
        self.reference_icon=None
        self.reference_signature=()
        self.bound=False
        self.expected={norm(k):v for k,v in equipment_bounds(equipment).items()}
        self.conflicts=0
        self.invalidated=False
        self.reason='Place cet objet dans l’atelier DOFUS.'

    def invalidate(self,reason):
        self.invalidated=True;self.bound=False;self.reason=reason

    def workshop_lost(self):
        if self.invalidated:return
        # An unseen workshop is a pause, not evidence of a replaced item.
        # Keep the verified artwork to check independently on return.
        self.bound=False
        self.tracker.reset();self.replacement.reset();self.conflicts=0
        self.reason='Atelier non visible : sélection conservée, vérification au retour.'

    def observe(self,icon,signature=()):
        if self.invalidated:return False
        icon=normalize_icon(icon)
        if icon is None:
            self.workshop_lost()
            return False
        # A shared icon is not enough: never bind a contradictory natural range.
        conflict=any(k in self.expected and self.expected[k]!=(lo,hi)
                     for k,lo,hi in signature)
        if conflict:
            self.conflicts+=1
            if self.conflicts>=3:
                self.invalidate('Les caractéristiques ne correspondent pas à l’objet choisi. Sélectionne le bon objet.')
            return False
        self.conflicts=0
        different=self.reference_icon is not None and (
            icon_distance(icon,self.reference_icon)>17 or
            strong_signature_change(self.reference_signature,signature))
        if different:
            self.bound=False
            self.tracker.reset()
            stable,_=self.replacement.observe(icon,signature)
            self.reason='Vérification de l’objet : image différente, attente de confirmation.'
            if stable:
                self.invalidate('Objet changé dans DOFUS : sélectionne le nouvel objet dans Forgely.')
            return False
        self.replacement.reset()
        stable,_=self.tracker.observe(icon,signature)
        if stable:
            self.bound=True;self.reason='Objet choisi par l’utilisateur · atelier stable'
            self.reference_icon=icon.copy()
            self.reference_signature=tuple(signature)
        return stable
