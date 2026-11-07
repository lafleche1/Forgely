"""Local visual themes and versioned appearance preference migration."""
import json
from pathlib import Path

THEMES={
 'Atelier émeraude':dict(BG='#101715',PANEL='#19231F',PANEL2='#273A31',ACCENT='#71D9AA',GOLD='#E6C78B',FG='#ECF4EF',MUTED='#A5B8AE',GREEN='#82DFB2',RED='#F29B99',HOVER='#92E8C2',BUTTON_HOVER='#365343',BUTTON_FG='#10251B'),
 'DOFUS classique':dict(BG='#271E17',PANEL='#433024',PANEL2='#624632',ACCENT='#668528',GOLD='#F2D18B',FG='#FFF1D6',MUTED='#D2BA9A',GREEN='#ACCF66',RED='#F29A82',HOVER='#86A63A',BUTTON_HOVER='#795840',BUTTON_FG='#FFFFFF'),
 'Minimal épuré':dict(BG='#F6F0F3',PANEL='#FFFAFC',PANEL2='#E9DDE9',ACCENT='#8052A4',GOLD='#70468C',FG='#30233A',MUTED='#766A7D',GREEN='#347E5A',RED='#B84D60',HOVER='#986DB5',BUTTON_HOVER='#DFD0E2',BUTTON_FG='#FFFFFF'),
 'Sombre immersif':dict(BG='#171321',PANEL='#282037',PANEL2='#3A2B4E',ACCENT='#9147CF',GOLD='#D9A5FF',FG='#F5EBFF',MUTED='#BAA9CA',GREEN='#A5D47B',RED='#F58DA6',HOVER='#AD65E5',BUTTON_HOVER='#503865',BUTTON_FG='#FFFFFF'),
 'Fantaisie turquoise':dict(BG='#DDF2EE',PANEL='#F4FCF8',PANEL2='#BFE4DE',ACCENT='#168F92',GOLD='#146E7A',FG='#173F44',MUTED='#4D7778',GREEN='#398B5A',RED='#C45F63',HOVER='#23A7A9',BUTTON_HOVER='#A6D9D2',BUTTON_FG='#FFFFFF'),
}
DEFAULT='Atelier émeraude'
PREF=Path.home()/'.forgely'/'apparence.json'

def load_theme(path=None):
    try:
        preferences=json.loads(Path(path or PREF).read_text(encoding='utf8'))
        name=preferences.get('theme')
        if name == 'DOFUS classique' and preferences.get('design_version') != 22:
            return DEFAULT
        return name if name in THEMES else DEFAULT
    except (OSError,ValueError,TypeError,AttributeError):
        return DEFAULT

def save_theme(name,path=None):
    if name not in THEMES:raise ValueError('Thème inconnu')
    target=Path(path or PREF)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps({'theme':name, 'design_version':22},ensure_ascii=False),encoding='utf8')
