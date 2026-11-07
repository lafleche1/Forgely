"""Audit d'un catalogue de VOD : ne convertit jamais un titre en tentative."""
import csv, json, argparse
from pathlib import Path

def audit(catalogue, revue=None):
    with Path(catalogue).open(encoding="utf-8-sig",newline="") as f:
        sources=list(csv.DictReader(f))
    ids=[r["id"] for r in sources]
    if len(ids)!=len(set(ids)):raise ValueError("Doublon dans le catalogue")
    out={"sources_reperees":len(sources),"sources_avec_video_analysee":0,"tentatives_verifiees":0,"probas_exploitables":False,"attention":"Les titres de VOD ne sont pas des tentatives de FM."}
    if revue:
        from laboratoire_videos import validate_review
        valid,errors=validate_review(revue)
        out["tentatives_verifiees"]=len(valid);out["erreurs_revue"]=errors
        out["probas_exploitables"]=len(valid)>=50 and not errors
        out["attention"]="Verifier la version DOFUS 3, le biais de selection et la couverture des echecs avant tout calcul."
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("catalogue");p.add_argument("--revue");a=p.parse_args()
    print(json.dumps(audit(a.catalogue,a.revue),ensure_ascii=False,indent=2))
