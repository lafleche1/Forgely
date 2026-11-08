"""Lecture Tesseract actuelle vs lecture numérique CV calibrée, sans capture.

Les profils CV ont appris ces images : la justesse mesurée ici n'est PAS une
validation indépendante de fiabilité sur de nouveaux jets ou objets.
"""
import argparse,json
from decimal import Decimal
from pathlib import Path
from time import perf_counter_ns
import cv2
import numpy as np
from PIL import Image
from benchmark_ocr_vs_cv import clear_ocr_caches,summary,bbox
from forgely_atelier import read_reliquat_ocr,parse_reliquat,read_atelier,choose_reliquat
from forgely_jet import read_effects_ocr,parse_jet
from forgely_zone_cache import ZoneCache
from runeforge_observer import extract_text
from forgely_cv.numbers import NumericReader
from forgely_cv.geometry import Rect,LayoutProfile
from forgely_cv.detection import InterfaceDetector
from forgely_cv.pipeline import VisionPipeline


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--tess-runs',type=int,default=8)
    parser.add_argument('--cv-runs',type=int,default=500)
    args=parser.parse_args()
    if min(args.tess_runs,args.cv_runs)<2:parser.error('Au moins deux répétitions')
    cv2.setNumThreads(1)
    root=Path(__file__).resolve().parents[1]
    cases=[]
    for name,file in [('gelano','cv_gelano_effects.png'),('cycloide','effects_vitalite_342.png')]:
        path=root/'Tests/fixtures'/file
        image=Image.open(path).convert('RGB')
        bgr=cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)
        profile=root/'Application/forgely_cv/profiles'/name
        reader=NumericReader.from_directory(profile)
        annotations=json.loads((profile.parent/(name+'-annotations.json')).read_text(encoding='utf8'))
        expected_jet={r['name']:int(r['text']) for r in annotations['fields'] if r['kind']=='stat'}
        expected_pool=next(Decimal(r['text'].replace(',','.')) for r in annotations['fields'] if r['kind']=='pool')
        pool_field=next(f for f in reader.fields if f.kind=='pool')
        a,b=pool_field.box,pool_field.guard_box
        left,top=min(a.x,b.x),min(a.y,b.y)
        pool_box=Rect(left,top,max(a.x+a.w,b.x+b.w)-left,max(a.y+a.h,b.y+b.h)-top)
        pool_patch=Image.fromarray(cv2.cvtColor(pool_box.crop(bgr),cv2.COLOR_BGR2RGB))
        def tesseract():
            raw=read_effects_ocr(image,extract_text)
            pool=parse_reliquat(read_reliquat_ocr(pool_patch,extract_text))
            return parse_jet(raw),Decimal(str(pool)) if pool is not None else None
        tesseract()  # Import/discovery warmup, then clear caches before every measured read.
        durations=[];outcomes=[]
        for index in range(args.tess_runs):
            clear_ocr_caches()
            start=perf_counter_ns();jet,pool=tesseract();durations.append((perf_counter_ns()-start)/1e6)
            outcomes.append(dict(jet=jet,pool=str(pool) if pool is not None else None,
                                 exact=jet==expected_jet and pool==expected_pool))
            print(f'{name} Tesseract {index+1}/{args.tess_runs}: {durations[-1]:.2f} ms, exact={outcomes[-1]["exact"]}',flush=True)
        tess={**summary(durations),'runs':len(durations),'exact_reads':sum(r['exact'] for r in outcomes),'outputs':outcomes}
        durations=[];exact=0
        reader.read(bgr)
        for _ in range(args.cv_runs):
            start=perf_counter_ns();result=reader.read(bgr);durations.append((perf_counter_ns()-start)/1e6)
            exact+=int(result.accepted and result.jet==expected_jet and result.pool==expected_pool)
        cv={**summary(durations),'runs':len(durations),'exact_reads':exact,'output':result.as_dict()}
        cases.append(dict(name=name,image_size=list(image.size),expected_jet=expected_jet,expected_pool=str(expected_pool),
                          tesseract=tess,cv_numeric=cv,median_ratio=tess['p50_ms']/cv['p50_ms']))
    report=dict(scope='Jet complet et puits sur les memes crops ; capture et reperage exclus',cases=cases,
        limitations=['Captures CV utilisees pour la calibration : pas de precision independante ni generalisable.',
                     'Repetitions des memes deux images, pas de nouvelles sessions de jeu.',
                     'Tesseract utilise la chaine actuelle de Forgely, pas une optimisation experimentale des seules ROIs numeriques.',
                     'Profils CV partiels et tailles fixes ; resultats inconnus hors calibration.',
                     'Aucune mesure du delai affichage-apparition ni de la capture dans ces chiffres.'])
    full=root/'.test-tmp/current-workshop.png'
    if full.exists():
        image=Image.open(full).convert('RGB');bgr=cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)
        w,h=image.size;anchor=bbox('title',w,h)
        profile=LayoutProfile(Rect(-anchor.x,-anchor.y,w,h),bbox('effects',w,h),bbox('history',w,h))
        detector=InterfaceDetector(anchor.crop(bgr).copy(),profile)
        pipeline=VisionPipeline(detector,numeric_reader=NumericReader.from_directory(root/'Application/forgely_cv/profiles/gelano'))
        pipeline.process(bgr)
        durations=[];exact=0
        for _ in range(100):
            start=perf_counter_ns();result=pipeline.process(bgr);durations.append((perf_counter_ns()-start)/1e6)
            exact+=int(result.numbers is not None and result.numbers.accepted and result.numbers.jet=={'Vitalité':10,'PA':0} and result.numbers.pool==0)
        report['cv_full_frame_tracking']={**summary(durations),'runs':100,'exact_reads':exact,
            'scope':'Image complete + suivi ancre + masques + jet et puits ; capture exclue. Ancre issue de la meme image.'}
        durations=[];exact=0
        for _ in range(3):
            clear_ocr_caches()
            start=perf_counter_ns();r=read_atelier(image,extract_text,ZoneCache(),{})
            jet=parse_jet(r.effects);pool=choose_reliquat(r.effects,r.reliquat)
            durations.append((perf_counter_ns()-start)/1e6)
            exact+=int(jet=={'Vitalité':10,'PA':0} and pool==0)
        report['tesseract_full_frame']={**summary(durations),'runs':3,'exact_reads':exact,
                                      'scope':'Image complete + zones atelier + jet et puits ; capture exclue, caches vides.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    for case in cases:
        print(case['name'],'TESS',case['tesseract']['p50_ms'],'CV',case['cv_numeric']['p50_ms'],'ratio',case['median_ratio'])
    for key in ('cv_full_frame_tracking','tesseract_full_frame'):
        if key in report:print(key,report[key])


if __name__=='__main__':main()
