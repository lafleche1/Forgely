"""Session goals bound to the visible slot, without inventing equipment identity."""
from forgely_item_icons import normalize_icon,icon_distance
from forgely_continuous_identity import strong_signature_change
from forgely_dofocus import normalise_jet,canonical_stat
from forgely_rules import RUNE_CHOICES
from time import perf_counter_ns


def learning_sources(item, jet, pool, targets, laboratory=None, simulator=None):
    """Real learning only; live advice must never schedule virtual trials.

    The simulator argument is compatibility-only. Manual simulation has its
    own explicit UI/job path and cannot feed this live source selection.
    """
    if not item or not jet or pool is None:
        return {}, None
    from forgely_data import stats_by_rune
    from forgely_learning import complete_learning_profile
    counts = None
    def counts_for(rune):
        nonlocal counts
        if counts is None:counts = stats_by_rune(item=item.strip())
        return dict(counts.get(rune, {'SC':0, 'SN':0, 'EC':0}))
    sources = {'counts_for': counts_for}
    for argument, method in (('contextual_for', 'estimate'), ('context_for', 'calibration')):
        lookup = getattr(laboratory, method, None)
        if callable(lookup):
            sources[argument] = lambda rune, lookup=lookup: lookup(item, rune, jet, pool)
    experience = getattr(laboratory, 'experience', None)
    if callable(experience):
        bounds = complete_learning_profile(item)
        sources['experience_for'] = lambda rune: experience(item, rune, jet, pool, targets, bounds)
    return sources, None


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


def goal_editor_jet(app):
    """Stable observed lines may define a goal before the full jet is valid.

    This never supplies a snapshot for advice or learning. Goals remain bound
    to the visible slot and their revision is checked when saving.
    """
    session=getattr(app,'measured_goals',None)
    if (not isinstance(session,MeasuredGoals) or session.icon is None or session.context is None
            or session.context[0] is not getattr(app,'frame_mailbox',None)
            or not getattr(app,'workshop_active',False)
            or getattr(app,'last_capture_title',None)!=session.context[1]):return None
    from forgely_workshop_readings import WorkshopReadings
    readings=getattr(app,'workshop_readings',None)
    if not isinstance(readings,WorkshopReadings):return None
    snapshot=readings.snapshot()
    if snapshot is not None:return dict(snapshot[0])
    return dict(readings.partial_jet) if readings.partial_jet else None


def maybe_prompt_goals(app):
    session=getattr(app,'measured_goals',None)
    if (not isinstance(session,MeasuredGoals) or session.targets or session.prompted
            or getattr(app,'observation_only',False) or getattr(app,'_goal_prompt_scheduled',False) is True
            or getattr(getattr(app,'overlay',None),'goal_editing',False) is True
            or not goal_editor_jet(app)):return False
    plan=getattr(app,'plan',None) or {}
    if (getattr(app,'active_equipment_verified',False) is True and plan.get('item')==app.item.get()
            and any(v.get('target') is not None for v in plan.get('stats',{}).values())):return False
    app._goal_prompt_scheduled=True
    def open_editor():
        app._goal_prompt_scheduled=False
        app.prompt_measured_goals()
    app.after(0,open_editor)
    return True


def current_snapshot(app):
    if getattr(app, '_copilot_masked', False) is True:
        return None
    session=getattr(app,'measured_goals',None)
    if (not isinstance(session,MeasuredGoals) or session.icon is None or
            not getattr(app,'workshop_active',False) or session.context is None or
            session.context[0] is not getattr(app,'frame_mailbox',None) or
            getattr(app,'last_capture_title',session.context[1])!=session.context[1]):
        return None
    from forgely_live_equipment import confirmed_numeric_snapshot
    snapshot=confirmed_numeric_snapshot(app)
    if snapshot is not None and icon_distance(app._verified_item_context.icon,session.icon)<=17:
        return snapshot
    from forgely_continuous_identity import SlotEvidence
    evidence=getattr(app,'fast_slot_evidence',None)
    if (not isinstance(evidence,SlotEvidence) or evidence.count<3 or
            evidence.context!=(session.context[0],session.context[0].generation(),session.context[1]) or
            not 0<=perf_counter_ns()-evidence.captured_ns<=2_000_000_000 or
            icon_distance(evidence.icon,session.icon)>17):return None
    return app.workshop_readings.snapshot()


class MeasuredGoals:
    def __init__(self):
        self.revision=-1
        self.reset()

    def reset(self):
        self.context=None;self.icon=None;self.signature=()
        self.equipment=None
        self.targets={};self.prompted=False;self.revision+=1

    def observe_slot(self,icon,signature,context):
        icon=normalize_icon(icon)
        if icon is None:return
        changed=(self.context!=context or self.icon is None or
                 icon_distance(self.icon,icon)>17 or
                 strong_signature_change(self.signature,signature))
        if changed:
            self.targets={};self.prompted=False;self.revision+=1
            self.equipment=None
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

    def proposal(self,snapshot,*,item=None,mode='Chances maximales',price_book=None,level=None,context_for=None,
                 counts_for=None,contextual_for=None,experience_for=None,simulation_for=None):
        from forgely_decision import advise
        prices=None  # Legacy currency inputs are ignored by target-first advice.
        if not self.targets:return advise({}, {},pool=None)
        if snapshot is None:return advise({},self.targets,pool=None,after_fusion=True)
        jet,pool=snapshot
        if not item and self.equipment is not None:
            item=self.equipment.identity_name
            if level is None:level=self.equipment.level
        sources = (dict(counts_for=counts_for,context_for=context_for,contextual_for=contextual_for,
                        experience_for=experience_for,simulation_for=simulation_for) if item else {})
        if item:
            from forgely_vision_guidance import reference_for
            bounds=reference_for(item)
            if bounds:
                return advise(jet,self.targets,pool=pool,mode=mode,item=item,predictive_policy=True,price_book=prices,
                              natural_max={k:max(v) for k,v in bounds.items()},profile_complete=True,
                              level=level,**sources)
        # No official name/profile is asserted. The engine can advise on
        # observed lines, while explicitly retaining its incomplete-profile limit.
        from forgely_perfect_goal import signature_equipment
        from forgely_equipment_catalog import equipment_bounds
        inferred=signature_equipment(self.signature)
        maxima=({canonical_stat(k):max(v) for k,v in equipment_bounds(inferred).items()} if inferred else None)
        return advise(jet,self.targets,pool=pool,mode=mode,natural_max=maxima,price_book=prices,
                      profile_complete=maxima is not None,allow_minimal_overshoot=True,predictive_policy=True,
                      level=level,**sources)
