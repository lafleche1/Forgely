"""Bounded exact-state caches. File revisions include SQLite WAL sidecars."""
from copy import deepcopy
from pathlib import Path
from time import monotonic


def file_revision(path):
    path=Path(path)
    try:
        info=path.stat()
        return str(path.absolute()),info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns
    except OSError:return str(path.absolute()),None


def database_revision(path):
    return file_revision(path),file_revision(str(path)+'-wal')


class AdviceCache:
    def __init__(self,ttl=1.0):
        self.ttl=ttl;self.key=None;self.value=None;self.saved_at=0.;self.hits=0;self.misses=0

    def get(self,key):
        if self.value is not None and self.key==key and monotonic()-self.saved_at<self.ttl:
            self.hits+=1
            return deepcopy(self.value)
        self.misses+=1
        return None

    def put(self,key,value):
        self.key=key;self.value=deepcopy(value);self.saved_at=monotonic()
        return value


def configure_if_changed(widget,**values):
    """Compare actual widget state, so external updates never stale a UI cache."""
    if all(str(widget.cget(key))==str(value) for key,value in values.items()):return False
    widget.configure(**values)
    return True


def capture_wait(period,elapsed):
    """Target a period, not capture-duration plus period; retain a small CPU yield."""
    return max(min(period,.005),period-max(0.,elapsed))
