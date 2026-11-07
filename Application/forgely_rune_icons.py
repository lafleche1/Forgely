"""Resolve user-captured rune icons by exact rune name; never guess artwork."""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
import re
import sys

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
CATALOG = ROOT / 'catalogue_dofus3'

def _normalize(value: str) -> str:
    return re.sub(r'\s+', ' ', str(value).strip()).casefold()

@lru_cache(maxsize=16)
def _catalogue_names(index: Path, signature: tuple) -> dict:
    entries = json.loads(index.read_text(encoding='utf-8'))
    if not isinstance(entries, list):
        raise ValueError('Invalid icon catalogue')
    names = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Invalid icon entry')
        name = _normalize(entry.get('rune', ''))
        # Duplicate labels are ambiguous, even when they use the same file.
        names[name] = None if name in names else entry.get('file', '')
    return names


def rune_icon_path(name: str, catalog: Path | None = None) -> Path | None:
    folder = Path(catalog) if catalog is not None else CATALOG
    requested = _normalize(name)
    if requested.startswith('rune '):
        requested = requested[5:]
    requested = re.sub(r'\s*[×x]\s*\d+\s*$', '', requested)
    if not requested or requested == 'stop':
        return None
    try:
        index = (folder / 'index.json').absolute()
        info = index.stat()
        signature = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        filename = _catalogue_names(index, signature).get(requested)
        if not isinstance(filename, str) or Path(filename).name != filename or not filename.lower().endswith('.png'):
            return None
        result = folder / filename
        # Cache catalogue decoding only: files can appear/disappear independently.
        return result if result.is_file() else None
    except (OSError, ValueError, TypeError):
        return None
