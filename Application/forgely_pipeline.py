"""Context-bound worker delivery; queued old-session OCR never becomes evidence."""
from dataclasses import dataclass


@dataclass(frozen=True)
class VerifiedItemContext:
    mailbox: object
    generation: int
    title: str
    frame_id: int
    item: str
    icon: object
    signature: tuple


@dataclass(frozen=True)
class AcceptedRuneEvent:
    frame_id: int
    event: object
    item: str | None
    mailbox: object
    generation: int
    title: str
    transition: dict | None = None


def bind_event_item(context,mailbox,generation,title,frame_id,icon,signature,name_hint=None):
    """Only prior, independently confirmed current-slot identity can bind a rune."""
    if (not isinstance(context,VerifiedItemContext) or context.mailbox is not mailbox
            or context.generation!=generation or context.title!=title
            or context.frame_id>frame_id or context.signature!=tuple(signature)
            or icon is None):
        return None
    from forgely_items import key_for
    from forgely_item_icons import icon_distance
    if name_hint and key_for(name_hint)!=key_for(context.item):
        return None
    return context.item if icon_distance(context.icon,icon)<=17 else None


class FrameMessageSink:
    def __init__(self, queue, mailbox, generation, title, stop_event):
        self.queue=queue
        self.mailbox=mailbox
        self.generation=generation
        self.title=title
        self.stop_event=stop_event

    def put(self, message):
        def publish():
            if self.stop_event.is_set():
                return
            kind,data=message
            if kind=='accepted_event':
                self.queue.put(message)
            else:
                self.queue.put(('worker_message',(self.mailbox,self.generation,self.title,kind,data)))
        self.mailbox.deliver_current(self.generation,self.title,publish)
