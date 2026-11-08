"""Apply the offline price update to a matching source installation.

Only files listed in the shipped manifest are replaced. No observation database,
training file or user preference file is included in the payload.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import uuid
from datetime import datetime


def digest(path):
    # Git ZIPs and Windows checkouts can differ only by line endings.
    text = Path(path).read_text(encoding='utf-8-sig')
    data = (text.replace('\r\n', '\n').rstrip('\n') + '\n').encode('utf8')
    return hashlib.sha256(data).hexdigest()


def apply_update(root, payload):
    root, payload = Path(root).resolve(), Path(payload).resolve()
    if not (root / 'Application/forgely.py').is_file():
        raise ValueError('Place cette mise à jour dans le dossier contenant Application/forgely.py.')
    entries = json.loads((payload / 'manifest.json').read_text(encoding='utf8'))['files']
    pending = []
    for row in entries:
        relative = Path(row['path'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Chemin de mise à jour invalide')
        target, source = root / relative, payload / relative
        if digest(source) != row['after']:
            raise ValueError(f'Fichier de mise à jour endommagé : {relative}')
        current = digest(target) if target.exists() else None
        if current == row['after']:
            continue
        if current not in [row['before'], *row.get('before_versions', [])]:
            raise ValueError(f'Version locale différente : {relative}. Aucun fichier remplacé. '
                             'Utilise la dernière version GitHub ou fais adapter la mise à jour à tes sources.')
        pending.append((relative, target, source))
    if not pending:
        return None
    backup = root / ('sauvegarde-prix-tylezia-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6])
    for relative, target, source in pending:
        if target.exists():
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
    written = []
    try:
        for relative, target, source in pending:
            target.parent.mkdir(parents=True, exist_ok=True)
            written.append((relative, target))
            shutil.copy2(source, target)
    except OSError:
        for relative, target in reversed(written):
            saved = backup / relative
            if saved.exists():
                shutil.copy2(saved, target)
            else:
                target.unlink(missing_ok=True)
        raise
    return backup


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    try:
        payload = root / (sys.argv[2] if len(sys.argv) > 2 else 'mise_a_jour_prix_tylezia')
        if not (payload / 'manifest.json').exists():
            sys.path.insert(0, str(root / 'Application'))
            from forgely_tools import activate_tylezia_reference
            settings = activate_tylezia_reference()
            print('Référence Tylezia activée :', len(settings['prices']), 'prix unitaires.')
            return 0
        backup = apply_update(root, payload)
    except (OSError, ValueError, KeyError) as exc:
        print('Mise à jour non appliquée :', exc)
        return 1
    print('Fichiers mis à jour.' if backup else 'Cette mise à jour est déjà installée.')
    if backup:
        print('Sauvegarde :', backup)
    print('Relance OUVRIR FORGELY.bat : les prix Tylezia seront activés au démarrage.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
