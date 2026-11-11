"""One live-state binding after either manual or automatic identity succeeds."""
from forgely_pipeline import VerifiedItemContext


def confirmed_numeric_snapshot(app):
    """Use the shared confirmed identity instead of re-identifying it for goals."""
    proof=getattr(app,'_verified_item_context',None)
    if not isinstance(proof,VerifiedItemContext) or getattr(app,'active_equipment_verified',False) is not True:
        return None
    mailbox=getattr(app,'frame_mailbox',None)
    if (proof.mailbox is not mailbox or proof.generation!=mailbox.generation()
            or proof.title!=getattr(app,'last_capture_title',None)
            or proof.item!=app.item.get()):return None
    readings=app.workshop_readings
    if readings.context!=((mailbox,proof.generation,proof.title),proof.item):return None
    return readings.snapshot()


def bind_confirmed_equipment(app,name,icon,signature,source_context,frame_id):
    app.item.set(name)
    app.active_equipment_verified=True
    if source_context is not None:
        mailbox,generation,title=source_context
        app._verified_item_context=VerifiedItemContext(
            mailbox,generation,title,frame_id,name,icon.copy(),tuple(signature))
    snapshot=(app.workshop_readings.snapshot()
              if app.workshop_readings.context is not None else None)
    if snapshot and app.pending_transition is None:
        app.live_jet,app.live_pool=snapshot
        app.live_after_fusion=False
