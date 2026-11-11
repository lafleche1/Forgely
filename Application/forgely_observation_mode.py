"""Persist the user-selected advice/collection mode locally."""
import json
from pathlib import Path

def load_observation_mode(data_dir):
    try:
        value=json.loads((Path(data_dir)/'mode_observation.json').read_text(encoding='utf-8'))
        return value.get('observation_only') is True
    except (OSError, ValueError, AttributeError):
        return False

def save_observation_mode(data_dir, enabled):
    directory=Path(data_dir)
    directory.mkdir(parents=True, exist_ok=True)
    target=directory/'mode_observation.json'
    temporary=directory/'mode_observation.json.tmp'
    temporary.write_text(json.dumps({'observation_only':bool(enabled)}),encoding='utf-8')
    temporary.replace(target)


def enable_copilot_for_goals(app):
    """Saving an advisory goal explicitly resumes advice, never live evidence."""
    if getattr(app,'observation_only',False) is not True:return
    from forgely_data import DATA_DIR
    save_observation_mode(DATA_DIR,False)
    app.observation_only=False
    update=getattr(app,'update_mode_button',None)
    if callable(update):update()
