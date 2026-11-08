"""Comparatif reproductible sur les captures disponibles, sans modifier Forgely.

La V1 ne contient pas de dictionnaire DOFUS : ses temps ne constituent donc
pas des temps de reconnaissance de jet. Aucun apprentissage sur les captures
du test et aucune observation de jeu ne sont enregistrés.
"""
import argparse
import json
from pathlib import Path
from time import perf_counter
import cv2
import numpy as np
from PIL import Image
from forgely_atelier import ZONES, read_atelier, choose_reliquat
from forgely_jet import parse_jet, read_effects_ocr
from runeforge_observer import extract_text
from forgely_zone_cache import ZoneCache
from forgely_cv.geometry import Rect, LayoutProfile
from forgely_cv.detection import InterfaceDetector
from forgely_cv.pipeline import VisionPipeline
from forgely_cv.glyphs import GlyphReader


def summary(times):
    return dict(zip(('p50_ms','p95_ms','p99_ms'), map(float,np.percentile(times,(50,95,99)))))


def clear_ocr_caches():
    import forgely_ocr_backend as backend
    import forgely_jet as jet
    with backend._CONDITION:
        backend._RESULTS.clear()
    jet._FIRST_ROW_FAILURES.clear()
    jet._FIRST_ROW_SUCCESSES.clear()
    with jet._LIVE_RECOVERY_LOCK:
        jet._LIVE_RECOVERY_CACHE.clear()


def bbox(name, w, h):
    a,b,c,d=ZONES[name]
    x,y,right,bottom=round(a*w),round(b*h),round(c*w),round(d*h)
    return Rect(x,y,right-x,bottom-y)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cold-runs',type=int,default=8)
    args=parser.parse_args()
    if args.cold_runs<2:parser.error('Au moins deux répétitions requises')
    cv2.setNumThreads(1)
    image=Image.open(args.image).convert('RGB')
    bgr=cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)
    w,h=image.size
    anchor=bbox('title',w,h)
    profile=LayoutProfile(Rect(-anchor.x,-anchor.y,w,h),bbox('effects',w,h),bbox('history',w,h))
    template=anchor.crop(bgr).copy()
    def pipeline():
        return VisionPipeline(InterfaceDetector(template,profile),GlyphReader({}))
    expected={'Vitalité':10,'PA':0}
    def tess(cache,title):
        result=read_atelier(image,extract_text,cache,title)
        return {'jet':parse_jet(result.effects),'pool':choose_reliquat(result.effects,result.reliquat),
                'readable':result.readable,'active':result.active}
    report={'scope':'Captures statiques disponibles ; acquisition écran exclue des deux chaînes',
            'image_size':[w,h],'expected_gelano':{'jet':expected,'pool':0},
            'limitations':[
                'Une seule capture complète de Gelano ; pas une mesure généralisable au jeu.',
                'Ancre CV découpée dans cette même capture : microbenchmark, pas validation indépendante du repérage.',
                'Aucun dictionnaire de police DOFUS dans la V1 ; lecture de jet/puits non implémentée dans son pipeline.',
                'Les temps V1 incluent contours/masquage et comparaison avec dictionnaire vide, pas une reconnaissance équivalente.',
                'Essais chauds : répétitions de pixels identiques, pas de nouvelles poses de runes.',
                'Chaque durée de bout de chaîne inclut le traitement mais pas la capture ni l’affichage.'
            ]}
    times=[];outputs=[]
    for index in range(args.cold_runs):
        clear_ocr_caches()
        started=perf_counter();outputs.append(tess(ZoneCache(),{}));times.append((perf_counter()-started)*1000)
        print(f'Tesseract froid {index+1}/{args.cold_runs}: {times[-1]:.1f} ms',flush=True)
    report['tesseract_cold']={**summary(times),'runs':len(times),'outputs':outputs,
        'exact_jet_and_pool':sum(row['jet']==expected and row['pool']==0 for row in outputs)}
    cache,title=ZoneCache(),{}
    tess(cache,title)
    times=[];outputs=[]
    for _ in range(50):
        started=perf_counter();outputs.append(tess(cache,title));times.append((perf_counter()-started)*1000)
    report['tesseract_identical_frame_cached']={**summary(times),'runs':len(times),
        'exact_jet_and_pool':sum(row['jet']==expected and row['pool']==0 for row in outputs)}
    for name, iterations, fresh in (('cv_global_search',30,True),('cv_local_tracking',100,False)):
        engine=pipeline();engine.process(bgr)
        times=[];detections=accepted=0
        for _ in range(iterations):
            if fresh:engine=pipeline()
            started=perf_counter();row=engine.process(bgr);times.append((perf_counter()-started)*1000)
            detections+=int(row.detection is not None)
            accepted+=sum(value['accepted'] for value in row.texts.values())
        report[name]={**summary(times),'runs':iterations,'detections':detections,
                      'accepted_chat_lines':accepted,'jet':None,'pool':None,'exact_jet_and_pool':0}
    fixture=Path(__file__).resolve().parents[1]/'Tests/fixtures/effects_vitalite_342.png'
    if fixture.exists():
        patch=Image.open(fixture).convert('RGB');clear_ocr_caches()
        started=perf_counter();raw=read_effects_ocr(patch,extract_text)
        jet=parse_jet(raw)
        report['second_real_effects_crop']={'scope':'Crop seul : pas de localisation ni puits dans cette image',
            'expected_subset':{'Vitalité':342,'Tacle':0},'tesseract_jet':jet,
            'tesseract_ms':(perf_counter()-started)*1000,
            'expected_subset_correct':jet.get('Vitalité')==342 and jet.get('Tacle')==0,
            'cv_jet':None,'cv_reason':'Dictionnaire non calibré et absence de lecture numérique intégrée'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('limitations',)},ensure_ascii=True,indent=2))


if __name__=='__main__':main()
