"""Opt-in DofusDude DOFUS 3 image catalogue importer. Never called automatically.

Downloads a small set of search results and verifies exact names. Images remain
third-party artwork: user must verify redistribution rights before publication.
No game interaction, no user screenshots sent. Errors never become matches.
"""
from __future__ import annotations
import io
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from PIL import Image

BASE = "https://api.dofusdu.de"
MAX_IMAGE_BYTES = 1_500_000
MAX_RESULTS = 15
TARGETS = ("Vi", "Pa Vi", "Ra Vi", "Fo", "Pa Fo", "Ra Fo", "Sa", "Pa Sa", "Ra Sa", "Ine", "Pa Ine", "Ra Ine", "Age", "Pa Age", "Ra Age", "Cha", "Pa Cha", "Ra Cha", "Ga Pa", "Ga Pme")


def norm(s):
    value=unicodedata.normalize('NFKD', s or '')
    return re.sub(r"\s+", " ", ''.join(c for c in value.lower() if not unicodedata.combining(c))).strip()


def exact_rune_name(item_name, target):
    # Strict: no guesswork on names, no Rune Vi = Pa Vi confusion.
    return norm(item_name) in {norm('Rune ' + target), norm('Rune de ' + target), norm(target)}


def api_url(target):
    return BASE + '/dofus3/v1/fr/items/resources/search?' + urlencode({'query':'Rune '+target,'limit':MAX_RESULTS})


def image_allowed(url):
    p=urlsplit(url)
    host=(p.hostname or '').lower()
    return p.scheme=='https' and not p.username and not p.password and p.port in (None,443) and any(host==h or host.endswith('.'+h) for h in ('dofusdu.de','ankama.com','dofus.com'))


def request_json(url, fetch=None):
    if fetch is not None: return json.loads(fetch(url).decode('utf8'))
    req=Request(url, headers={'User-Agent':'Forgely/0.12 (opt-in catalog importer; one-shot)', 'Accept':'application/json'})
    with urlopen(req,timeout=12) as res:
        if res.status!=200: raise RuntimeError('Réponse API non valide')
        raw=res.read(1_000_001)
    if len(raw)>1_000_000:raise ValueError('Réponse API trop volumineuse')
    return json.loads(raw.decode('utf8'))


def image_bytes(url,fetch=None):
    if not image_allowed(url): raise ValueError('Adresse image non autorisée')
    if fetch is not None: raw=fetch(url)
    else:
        req=Request(url,headers={'User-Agent':'Forgely/0.12 (opt-in catalog importer)'})
        # Redirects are checked via final response URL to avoid arbitrary destinations.
        with urlopen(req,timeout=12) as res:
            if not image_allowed(res.geturl()):raise ValueError('Redirection non autorisée')
            raw=res.read(MAX_IMAGE_BYTES+1)
    if len(raw)>MAX_IMAGE_BYTES:raise ValueError('Image trop volumineuse')
    with Image.open(io.BytesIO(raw)) as im:
        im.load()
        if im.width>2048 or im.height>2048 or im.width<8 or im.height<8:
            raise ValueError('Dimensions image incompatibles')
        return im.convert('RGBA')


def find_exact(items,target):
    if isinstance(items,dict):items=items.get('items',[])
    if not isinstance(items,list):return None
    matches=[item for item in items if isinstance(item,dict) and exact_rune_name(str(item.get('name','')),target)]
    # Avoid duplicate or conflicting references; index by unique Ankama id.
    ids={str(m.get('ankama_id')) for m in matches}
    return matches[0] if len(ids)==1 and matches else None


def sync_catalogue(directory: Path, targets=TARGETS, fetch=None):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    report={'ok':[], 'errors':{}, 'source':'DofusDude DOFUS3 FR', 'notes':'Images tierces, usage local uniquement'}
    entries=[]
    for target in targets:
        try:
            match=find_exact(request_json(api_url(target),fetch),target)
            if match is None:raise ValueError('Aucun nom exact et unique trouvé')
            urls=match.get('image_urls') or {}
            icon=urls.get('icon') or urls.get('sd') if isinstance(urls,dict) else None
            if not icon:raise ValueError('Aucune icône fournie par la réponse API')
            image=image_bytes(icon,fetch)
            # Do not re-use previous assets when new data is incomplete.
            filename='rune_'+re.sub('[^0-9A-Za-z]','_',target)+'.png'
            image.save(directory/filename)
            entries.append({'rune':target,'file':filename, 'source':'DofusDude', 'ankama_id':match.get('ankama_id'),'source_name':match.get('name')})
            report['ok'].append(target)
        except Exception as exc:
            report['errors'][target]=str(exc)[:180]
    # Only index files obtained during this sync; no fake entries or partial names.
    (directory/'index.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf8')
    (directory/'rapport.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report
