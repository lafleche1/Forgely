"""Resolve user-captured rune icons by exact rune name; never guess artwork."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
CATALOG = ROOT / 'catalogue_dofus3'

def _normalize(value: str) -> str:
    return re.sub(r'\s+', ' ', str(value).strip()).casefold()

def rune_icon_path(name: str, catalog: Path | None = None) -> Path | None:
    folder = Path(catalog) if catalog is not None else CATALOG
    try:
        entries = json.loads((folder / 'index.json').read_text(encoding='utf-8'))
        requested = _normalize(name)
        if requested.startswith('rune '):
            requested = requested[5:]
        # Ignore counts appended by advice UI, not prefixes like Ra / Pa.
        requested = re.sub(r'\s*[×x]\s*\d+\s*$', '', requested)
        if not requested or requested == 'stop':
            return None
        matches = [entry for entry in entries if _normalize(entry.get('rune', '')) == requested]
        if len(matches) != 1:
            return None
        filename = matches[0].get('file', '')
        if Path(filename).name != filename or not filename.lower().endswith('.png'):
            return None
        result = folder / filename
        return result if result.is_file() else None
    except (OSError, ValueError, TypeError):
        return None
