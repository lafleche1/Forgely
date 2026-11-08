"""Theoretical item bounds guide observation; they never supply actual values."""
from forgely_dofocus import canonical_stat,normalise_jet


def reference_for(item):
    from forgely_equipment_catalog import bundled_bounds
    from forgely_tools import natural_bounds
    expected=dict(bundled_bounds(item))
    expected.update(natural_bounds(item))
    return {canonical_stat(k):tuple(v) for k,v in expected.items()}


def reference_report(expected,observed):
    expected={canonical_stat(k):v for k,v in (expected or {}).items()}
    actual=normalise_jet(observed) or {}
    return dict(available=bool(expected),
        missing=[k for k in expected if k not in actual],
        extra=[k for k in actual if k not in expected] if expected else [],
        below_min=[k for k,(lo,hi) in expected.items() if k in actual and actual[k]<min(lo,hi)],
        above_max=[k for k,(lo,hi) in expected.items() if k in actual and actual[k]>max(lo,hi)],
        inferred_values=False)


def merge_observation(ocr_jet,visual_jet,ocr_pool,visual_pool):
    """Fuse measured fields only; disagreeing readers invalidate this frame."""
    from decimal import Decimal,InvalidOperation
    a,b=normalise_jet(ocr_jet),normalise_jet(visual_jet)
    if a is None or b is None:return {},None,'conflict'
    if any(a[k]!=b[k] for k in a.keys() & b.keys()):return {},None,'conflict'
    try:
        p=Decimal(str(visual_pool)) if visual_pool is not None else None
        q=Decimal(str(ocr_pool)) if ocr_pool is not None else None
        if any(v is not None and (not v.is_finite() or v<0) for v in (p,q)):
            return {},None,'conflict'
        if p is not None and q is not None and p!=q:return {},None,'conflict'
    except (InvalidOperation,ValueError,TypeError):return {},None,'conflict'
    return {**a,**b},float(p) if p is not None else ocr_pool,'hybrid' if b or p is not None else 'ocr'
