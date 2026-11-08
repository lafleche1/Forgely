"""Session goals bound to the visible slot, without inventing equipment identity."""
from forgely_item_icons import normalize_icon,icon_distance
from forgely_continuous_identity import strong_signature_change
from forgely_dofocus import normalise_jet,canonical_stat
from forgely_rules import RUNE_CHOICES
from time import perf_counter_ns


def bound_session(app):
    """Retain the chosen slot/goal while numbers are being reread after a rune.

    This is display continuity, not permission to advise on old values.
    """
    session=getattr(app,'measured_goals',None)
    if (not isinstance(session,MeasuredGoals) or not session.targets or session.context is None
            or session.context[0] is not getattr(app,'frame_mailbox',None)
            or not getattr(app,'workshop_active',False)
            or getattr(app,'last_capture_title',session.context[1])!=session.context[1]):return False
    from forgely_continuous_identity import SlotEvidence
    evidence=getattr(app,'fast_slot_evidence',None)
    if isinstance(evidence,SlotEvidence):
        if evidence.context[0] is not session.context[0] or evidence.context[2]!=session.context[1]:return False
        if icon_distance(evidence.icon,session.icon)>17:return False
    return True


def current_snapshot(app):
    session=getattr(app,'measured_goals',None)
    if (not isinstance(session,MeasuredGoals) or session.icon is None or
            not getattr(app,'workshop_active',False) or session.context is None or
            session.context[0] is not getattr(app,'frame_mailbox',None) or
            getattr(app,'last_capture_title',session.context[1])!=session.context[1]):
        return None
    from forgely_continuous_identity import SlotEvidence
    evidence=getattr(app,'fast_slot_evidence',None)
    if (not isinstance(evidence,SlotEvidence) or evidence.count<3 or
            evidence.context!=(session.context[0],session.context[0].generation(),session.context[1]) or
            not 0<=perf_counter_ns()-evidence.captured_ns<=2_000_000_000 or
            icon_distance(evidence.icon,session.icon)>17):return None
    return app.workshop_readings.snapshot()


class MeasuredGoals:
    def __init__(self):
        self.context=None;self.icon=None;self.signature=()
        self.targets={};self.prompted=False;self.revision=0

    def observe_slot(self,icon,signature,context):
        icon=normalize_icon(icon)
        if icon is None:return
        changed=(self.context!=context or self.icon is None or
                 icon_distance(self.icon,icon)>17 or
                 strong_signature_change(self.signature,signature))
        if changed:
            self.targets={};self.prompted=False;self.revision+=1
        self.context=context;self.icon=icon.copy();self.signature=tuple(signature)

    def save(self,targets,observed,revision,*,allowed=()):
        if self.icon is None or revision!=self.revision:
            raise ValueError('L’objet a changé : définis son jet souhaité.')
        observed=normalise_jet(observed) or {}
        values=normalise_jet(targets)
        if not values or any(k not in (observed.keys() | set(allowed)) or k not in RUNE_CHOICES or
                             type(v) is not int or not -20000<=v<=20000
                             for k,v in values.items()):
            raise ValueError('Renseigne des objectifs entiers pour les lignes lues.')
        self.targets=values

    def proposal(self,snapshot,*,item=None,mode='Chances maximales',price_book=None,level=None,context_for=None):
        from forgely_decision import advise
        from forgely_pricing import active_price_book
        prices=price_book if price_book is not None else active_price_book()
        if not self.targets:return advise({}, {},pool=None)
        if snapshot is None:return advise({},self.targets,pool=None,after_fusion=True)
        jet,pool=snapshot
        if item:
            from forgely_vision_guidance import reference_for
            bounds=reference_for(item)
            if bounds:
                return advise(jet,self.targets,pool=pool,mode=mode,item=item,predictive_policy=True,price_book=prices,
                              natural_max={k:max(v) for k,v in bounds.items()},profile_complete=True,
                              level=level,context_for=context_for)
        # No official name/profile is asserted. The engine can advise on
        # observed lines, while explicitly retaining its incomplete-profile limit.
        from forgely_perfect_goal import signature_equipment
        from forgely_equipment_catalog import equipment_bounds
        inferred=signature_equipment(self.signature)
        maxima=({canonical_stat(k):max(v) for k,v in equipment_bounds(inferred).items()} if inferred else None)
        return advise(jet,self.targets,pool=pool,mode=mode,natural_max=maxima,price_book=prices,
                      profile_complete=maxima is not None,allow_minimal_overshoot=True,predictive_policy=True,
                      level=level,context_for=context_for)
