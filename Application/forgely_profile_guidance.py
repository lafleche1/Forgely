"""Guide conservateur basé sur les jets naturels importés.

Les valeurs théoriques ne deviennent JAMAIS des valeurs observées.
"""
from __future__ import annotations
import csv
from pathlib import Path
from forgely_tools import BOUNDS_PATH
from forgely_jet import norm

_cache = {"path": None, "stamp": None, "profiles": {}}

def _key(value):
    return " ".join(norm(str(value)).split())

def profiles(path=BOUNDS_PATH):
    path=Path(path)
    try:
        stamp=(path.stat().st_mtime_ns,path.stat().st_size)
    except OSError:
        return {}
    if _cache["path"] == str(path) and _cache["stamp"] == stamp:
        return _cache["profiles"]
    result={}
    try:
        with path.open(encoding="utf-8-sig",newline="") as stream:
            for row in csv.DictReader(stream):
                name=_key(row.get("equipement", ""))
                stat=row.get("statistique", "").strip()
                if not name or not stat:continue
                lo,hi=int(row["min"]),int(row["max"])
                if -30000 <= lo <= hi <= 30000:
                    result.setdefault(name,{})[stat]=(lo,hi)
    except (OSError,ValueError,KeyError,TypeError):
        return {}
    _cache.update(path=str(path),stamp=stamp,profiles=result)
    return result

def compare(item,observed,path=BOUNDS_PATH):
    """Returns hints and gaps, without filling observed values from the catalogue."""
    expected=profiles(path).get(_key(item),{})
    if Path(path)==Path(BOUNDS_PATH):
        # Diagnostics and live completeness checks must use the same profile.
        # An older partial CSV must not label a catalogue line as an exo.
        from forgely_vision_guidance import reference_for
        expected=reference_for(item) or expected
    if not expected:return {"available":False,"expected":{},"missing":[],"extra":[],"outside":[]}
    actual={_key(k):(k,v) for k,v in (observed or {}).items()}
    missing=[stat for stat in expected if _key(stat) not in actual]
    extra=[name for key,(name,_) in actual.items() if key not in {_key(s) for s in expected}]
    outside=[]
    for stat,(lo,hi) in expected.items():
        pair=actual.get(_key(stat))
        if pair and isinstance(pair[1],(int,float)) and not isinstance(pair[1],bool) and not lo<=pair[1]<=hi:
            outside.append((stat,pair[1],lo,hi))
    return {"available":True,"expected":expected,"missing":missing,"extra":extra,"outside":outside}
