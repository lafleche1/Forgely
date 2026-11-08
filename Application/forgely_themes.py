"""Local visual themes and versioned appearance preference migration."""
import json
from pathlib import Path

THEMES={
 'Obsidienne':dict(BG='#111318',PANEL='#1C2027',PANEL2='#293039',ACCENT='#56D6A0',GOLD='#E5C78C',FG='#F0F3F6',MUTED='#A6AFBC',GREEN='#72DFAE',RED='#F09198',HOVER='#7BE5B9',BUTTON_HOVER='#37424E',BUTTON_FG='#10251D'),
}
DEFAULT='Obsidienne'
PREF=Path.home()/'.forgely'/'apparence.json'

def load_theme(path=None):
    try:
        preferences=json.loads(Path(path or PREF).read_text(encoding='utf8'))
        name=preferences.get('theme')
        return name if name in THEMES else DEFAULT
    except (OSError,ValueError,TypeError,AttributeError):
        return DEFAULT

def save_theme(name,path=None):
    if name not in THEMES:raise ValueError('Thème inconnu')
    target=Path(path or PREF)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps({'theme':name, 'design_version':23},ensure_ascii=False),encoding='utf8')
