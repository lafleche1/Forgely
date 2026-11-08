"""Perfect targets come from the selected/identified equipment's reference."""
from forgely_equipment_session import ManualEquipmentSession
from forgely_equipment_catalog import equipment_bounds,EquipmentCatalog
from forgely_dofocus import canonical_stat
from forgely_items import key_for
from forgely_jet import norm


def signature_equipment(signature):
    # Use natural Min/Max pairs, never mutable current values. Collapsed
    # generic labels (damage/resistance) cannot prove an equipment identity.
    pairs={norm(k):(lo,hi) for k,lo,hi in signature
           if norm(k) not in ('dommages','resistance')}
    if len(pairs)<3:return None
    matches=[]
    for item in EquipmentCatalog().items:
        bounds={norm(k):tuple(v) for k,v in equipment_bounds(item).items()}
        if set(pairs)<=bounds.keys() and all(bounds[k]==v for k,v in pairs.items()):
            matches.append(item)
            if len(matches)>1:return None
    return matches[0] if matches else None


def perfect_goal(app):
    manual=getattr(app,'manual_equipment',None)
    if isinstance(manual,ManualEquipmentSession) and not manual.invalidated:
        item=manual.equipment
        name,ident,bounds=item.identity_name,item.item_id,equipment_bounds(item)
    elif app.active_equipment_verified:
        from forgely_vision_guidance import reference_for
        name=app.item.get();bounds=reference_for(name)
        matches=[e for e in EquipmentCatalog().items if key_for(e.identity_name)==key_for(name)]
        ident=matches[0].item_id if len(matches)==1 else None
    else:
        from forgely_measured_goals import MeasuredGoals
        session=getattr(app,'measured_goals',None)
        item=signature_equipment(session.signature) if isinstance(session,MeasuredGoals) else None
        if item is None:
            raise ValueError('Jet parfait nécessite un objet sélectionné ou des bornes théoriques reconnues sans ambiguïté.')
        name,ident,bounds=item.identity_name,item.item_id,equipment_bounds(item)
    if not bounds:raise ValueError('Les maximums théoriques de cet objet ne sont pas disponibles.')
    return name,ident,{canonical_stat(k):max(v) for k,v in bounds.items()}
