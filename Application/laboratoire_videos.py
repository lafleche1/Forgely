"""Laboratoire VOD indépendant : vidéos locales autorisées -> revue humaine -> CSV vérifié.
Aucune extraction YouTube, aucune observation inventée, aucune injection dans le modèle en direct.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ['video_id','video_url','horodatage_video_s','date_utc','equipement','rune','resultat','source','jet_avant','puits_avant','type_fm','poids_rune','jet_apres','puits_apres','reviseur','statut','notes']
EXPORT = ['date_utc','equipement','rune','resultat','source','jet_avant','puits_avant','type_fm','poids_rune']
VALID_OUTCOMES = {'SC','SN','EC'}
VALID_KINDS = {'fm_classique','over','exo'}

def init_review(path, video_id='', url=''):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
    return path

def validate_review(path):
    accepted=[]; errors=[]; seen=set()
    with Path(path).open(newline='',encoding='utf-8-sig') as f:
        r=csv.DictReader(f)
        if not r.fieldnames or not set(FIELDS).issubset(r.fieldnames):
            raise ValueError('Colonnes manquantes dans la feuille de revue')
        for line,row in enumerate(r,2):
            if (row['statut'] or '').strip().lower() != 'verifie':
                continue
            vid=row['video_id'].strip(); t=row['horodatage_video_s'].strip()
            reviewer=row['reviseur'].strip(); outcome=row['resultat'].strip().upper()
            item=row['equipement'].strip(); rune=row['rune'].strip()
            try:
                ts=float(t); pool=float(row['puits_avant']); weight=float(row['poids_rune'])
                datetime.fromisoformat(row['date_utc'].strip().replace('Z','+00:00'))
                good=(ts>=0 and 0<=pool<1e7 and 0<weight<1e7)
            except (ValueError,TypeError,OverflowError):good=False
            signature=(vid,t)
            if (not vid or not reviewer or not item or not rune or not row['jet_avant'].strip()
                or outcome not in VALID_OUTCOMES or row['type_fm'].strip() not in VALID_KINDS
                or not good or signature in seen):
                errors.append({'ligne':line,'raison':'champs invalides, incomplets ou tentative dupliquee'});continue
            seen.add(signature)
            accepted.append({k:('video_verified' if k=='source' else row[k].strip()) for k in EXPORT})
    return accepted,errors

def export_review(source, destination):
    rows,errors=validate_review(source)
    if errors: raise ValueError('Revue invalide : '+json.dumps(errors,ensure_ascii=False))
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=EXPORT);w.writeheader();w.writerows(rows)
    return {'tentatives_verifiees':len(rows),'sortie':str(destination),'note':'Aucune observation non revue n’est exportée'}

def contact_sheet(video, output, interval=15, limit=80):
    """Echantillonnage local, pour tri visuel. Pas de reconnaissance de tentatives."""
    if not 1<=interval<=3600 or not 1<=limit<=500: raise ValueError('Paramètres invalides')
    try: import cv2
    except ImportError as exc: raise RuntimeError('Installer opencv-python pour analyser les fichiers vidéo locaux') from exc
    from PIL import Image,ImageOps,ImageDraw
    video=Path(video)
    if not video.is_file(): raise FileNotFoundError(video)
    cap=cv2.VideoCapture(str(video))
    if not cap.isOpened(): raise ValueError('Vidéo illisible')
    fps=cap.get(cv2.CAP_PROP_FPS); frames=cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if fps<=0 or frames<=0: cap.release();raise ValueError('Durée vidéo inconnue')
    duration=frames/fps; thumbs=[]
    try:
        for i in range(min(limit,int(duration//interval)+1)):
            second=i*interval;cap.set(cv2.CAP_PROP_POS_MSEC,second*1000)
            ok,frame=cap.read()
            if not ok:continue
            frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            im=Image.fromarray(frame);im.thumbnail((320,180))
            cell=Image.new('RGB',(340,212),'#171321')
            cell.paste(im,((340-im.width)//2,8))
            ImageDraw.Draw(cell).text((12,190),f'{second//60:02d}:{second%60:02d}',fill='white')
            thumbs.append(cell)
    finally:cap.release()
    if not thumbs:raise ValueError('Aucune image lisible')
    columns=3; rows=(len(thumbs)+columns-1)//columns
    sheet=Image.new('RGB',(columns*340,rows*212),'#171321')
    for i,im in enumerate(thumbs):sheet.paste(im,((i%columns)*340,(i//columns)*212))
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(output)
    return {'images':len(thumbs),'duree_s':round(duration,1),'planche':str(output)}



def detect_candidates(video, destination, sample_step=0.5, threshold=0.14, min_gap=1.0, max_candidates=1000):
    """Détecte des changements d'image, PAS des tentatives confirmées.

    Les timestamps candidats facilitent la revue humaine. Aucun événement SC/SN/EC
    n'est inféré, et aucune ligne n'est envoyée au modèle probabiliste.
    """
    if not (0.1 <= sample_step <= 30 and 0.01 <= threshold <= 1 and min_gap >= 0 and 1 <= max_candidates <= 10000):
        raise ValueError('Paramètres de détection invalides')
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError('Installer opencv-python pour les vidéos locales') from exc
    video=Path(video)
    if not video.is_file(): raise FileNotFoundError(video)
    cap=cv2.VideoCapture(str(video))
    if not cap.isOpened(): raise ValueError('Vidéo illisible')
    fps=cap.get(cv2.CAP_PROP_FPS); total=cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if fps<=0 or total<=0: cap.release();raise ValueError('Durée vidéo inconnue')
    duration=total/fps
    candidates=[]; prev=None; last=-float('inf'); t=0.0
    try:
        while t<duration and len(candidates)<max_candidates:
            cap.set(cv2.CAP_PROP_POS_MSEC,t*1000)
            ok,frame=cap.read()
            if not ok: t+=sample_step;continue
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            h,w=gray.shape
            # Zone centrale de l'atelier : moins de bruit provenant du chat / HUD.
            crop=gray[int(h*.2):int(h*.8),int(w*.2):int(w*.8)]
            if crop.size==0: t+=sample_step;continue
            small=cv2.resize(crop,(128,96),interpolation=cv2.INTER_AREA)
            if prev is not None:
                diff=float(cv2.absdiff(small,prev).mean())/255.0
                if diff>=threshold and t-last>=min_gap:
                    candidates.append({'horodatage_video_s':round(t,3),'variation_image':round(diff,4),'statut':'a_verifier'})
                    last=t
            prev=small;t+=sample_step
    finally: cap.release()
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=['horodatage_video_s','variation_image','statut'])
        writer.writeheader();writer.writerows(candidates)
    return {'video':str(video),'duree_s':round(duration,2),'candidats':len(candidates),
            'sortie':str(destination),'tentatives_verifiees':0,
            'avertissement':'Changements visuels uniquement ; chaque tentative doit être vérifiée manuellement.'}

def main():
    p=argparse.ArgumentParser(description='Laboratoire vidéo FM hors de Forgely')
    s=p.add_subparsers(dest='action',required=True)
    a=s.add_parser('init');a.add_argument('csv')
    a=s.add_parser('planche');a.add_argument('video');a.add_argument('image');a.add_argument('--intervalle',type=int,default=15)
    a=s.add_parser('export');a.add_argument('revue');a.add_argument('csv')
    a=s.add_parser('candidats');a.add_argument('video');a.add_argument('csv');a.add_argument('--pas',type=float,default=0.5);a.add_argument('--seuil',type=float,default=0.14);a.add_argument('--ecart',type=float,default=1.0)
    a=p.parse_args()
    if a.action=='init':res={'feuille':str(init_review(a.csv))}
    elif a.action=='planche':res=contact_sheet(a.video,a.image,a.intervalle)
    elif a.action=='candidats':res=detect_candidates(a.video,a.csv,a.pas,a.seuil,a.ecart)
    else:res=export_review(a.revue,a.csv)
    print(json.dumps(res,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
