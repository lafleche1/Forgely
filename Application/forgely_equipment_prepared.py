"""Optional numeric artwork cache, invalidated by catalogue/image changes.

No pickle or executable data. A missing or broken cache falls back to the
original PNG preparation. It never supplies names or alters matching rules.
"""
from hashlib import sha256
from pathlib import Path
import json
import os
from tempfile import NamedTemporaryFile
from zipfile import BadZipFile
import numpy as np


def fingerprint(references):
    rows=[];files={}
    for r in references:
        if not isinstance(r.image,(str,Path)):return None
        path=Path(r.image)
        if path not in files:
            try:
                info=path.stat();files[path]=(info.st_size,info.st_mtime_ns)
            except OSError:files[path]=None
        rows.append((r.item_id,r.name,r.category,r.signature,str(path),files[path]))
    return sha256(json.dumps(['artwork-v1',rows],ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def load_prepared(path,references):
    try:
        with np.load(path,allow_pickle=False) as data:
            if str(data['fingerprint'])!=fingerprint(references):return None
            positions=data['positions'];pixels=data['pixels'];hashes=data['hashes']
            n=len(positions)
            if (n>len(references) or positions.dtype.kind not in 'iu' or len(set(map(int,positions)))!=n
                    or any(not 0<=int(i)<len(references) for i in positions)
                    or pixels.dtype!=np.uint8 or pixels.shape!=(n,32,32,3)
                    or hashes.dtype!=np.uint64 or hashes.shape!=(n,)):
                return None
            return positions.tolist(),pixels.astype(np.int16),hashes.copy()
    except (OSError,ValueError,KeyError,TypeError,EOFError,BadZipFile):return None


def save_prepared(path,references,index):
    digest=fingerprint(references)
    if digest is None:return
    positions={id(r):i for i,r in enumerate(references)}
    temporary=None
    try:
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        with NamedTemporaryFile(dir=path.parent,prefix=path.name+'.',suffix='.tmp',delete=False) as file:
            temporary=Path(file.name)
            np.savez_compressed(file,fingerprint=np.array(digest),
                positions=np.array([positions[id(r)] for r in index.references],dtype=np.int64),
                pixels=index.pixels.astype(np.uint8),hashes=index.hashes)
        os.replace(temporary,path)
    except OSError:pass  # read-only installations keep the original slow path
    finally:
        if temporary is not None:
            try:temporary.unlink(missing_ok=True)
            except OSError:pass
