"""Local reports distinguish observed outcomes, uncertainty and learning eligibility."""
from collections import Counter, defaultdict
import csv
from html import escape
import json
from pathlib import Path

from forgely_probabilites import wilson
from forgely_video_store import atomic_json, qualify_event


def write_report(session, directory):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    events=[]; groups=defaultdict(Counter); statuses=Counter(); by_item={}
    for event in session.get('events',[]):
        qualification=qualify_event(event)
        row={**event,'qualification':qualification}
        events.append(row)
        state='fiable' if qualification['eligible'] else ('rejeté' if event.get('status')=='rejected' else 'à vérifier')
        statuses[state]+=1
        if qualification['eligible']:
            # Entire pre-state is retained; this is not a universal rune probability.
            context=json.dumps(event['before'],ensure_ascii=False,sort_keys=True)
            groups[(qualification['item'],event['rune'],context)][event['outcome']]+=1
            from forgely_dofocus import reference
            summary=by_item.setdefault(qualification['item'],{'attempts':0,'runes':{},'rune_density':0.,'lost_density':0.,'observed_pool_delta':0.})
            summary['attempts']+=1
            summary['runes'][event['rune']]=summary['runes'].get(event['rune'],0)+1
            summary['rune_density']+=reference(event['rune']).weight
            summary['lost_density']+=qualification['audit']['lost_weight']
            summary['observed_pool_delta']+=event['after']['pool']-event['before']['pool']
    report={'video':session.get('path'),'id':session['id'],'status':session.get('status'),
            'audio_processed':False,'coverage':{'duration':session.get('info',{}).get('duration'),
            'analyzed_until':session.get('cursor'), 'boundaries':session.get('boundaries',[])},
            'counts':dict(statuses),'events':events,'by_item':by_item,
            'limits':['Pas de traitement audio.','Objectif du joueur inconnu sauf indication explicite.',
                      'Échantillonnage : des tentatives rapides peuvent manquer.',
                      'Cohérence visuelle et comptable, pas certification du serveur.',
                      'Une stratégie observée ne prouve pas une amélioration des conseils.']}
    atomic_json(directory/'rapport.json',report)
    with (directory/'tentatives.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        fields=['id','time','item','rune','outcome','eligible','before','after','reasons']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for e in events:
            q=e['qualification']
            values={'id':e['id'],'time':e.get('time'),'item':q['item'],'rune':e.get('rune'),
                    'outcome':e.get('outcome'),'eligible':q['eligible'],
                    'before':json.dumps(e.get('before'),ensure_ascii=False),
                    'after':json.dumps(e.get('after'),ensure_ascii=False),'reasons':'; '.join(q['reasons'])}
            # Spreadsheet formula injection protection for exported free text.
            writer.writerow({k: "'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v for k,v in values.items()})
    esc=lambda value:escape(str(value))
    body=['<!doctype html><html lang="fr"><meta charset="utf-8"><title>Forgely — Session vidéo</title>',
          '<style>body{font:16px Segoe UI,sans-serif;max-width:1200px;margin:30px auto;padding:12px;background:#f6f7fa;color:#202333}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd;padding:8px;text-align:left}pre{white-space:pre-wrap}h1,h2{color:#493887}</style>',
          '<h1>Session réelle — analyse visuelle</h1>',f'<p>{esc(session.get("path"))}</p>',
          f'<p>État : {esc(session.get("status"))} · {len(events)} candidats · {statuses["fiable"]} observations admissibles.</p>',
          '<ul>'+''.join('<li>'+esc(x)+'</li>' for x in report['limits'])+'</ul>',
          '<h2>Consommation et pertes observées par objet</h2><p>Poids total des runes, sans estimation de prix ni des passages non lus.</p>',
          '<pre>'+esc(json.dumps(by_item,ensure_ascii=False,indent=2))+'</pre>',
          '<h2>Fréquences par objet, rune et contexte exact</h2><p>Intervalles à 95 % ; les faibles effectifs restent descriptifs.</p>',
          '<table><tr><th>Objet / rune</th><th>Contexte avant</th><th>SC / SN / EC</th><th>SC : intervalle 95 %</th></tr>']
    for (item,rune,context),counts in sorted(groups.items()):
        n=sum(counts.values());low,high=wilson(counts['SC'],n)
        body.append(f'<tr><td>{esc(item)} / {esc(rune)}</td><td>{esc(context)}</td><td>{counts["SC"]} / {counts["SN"]} / {counts["EC"]} (n={n})</td><td>{100*low:.1f}–{100*high:.1f} %</td></tr>')
    body.append('</table><h2>Tentatives et preuves</h2>')
    for e in events:
        q=e['qualification'];audit=q['audit']
        body.append(f'<details><summary>{esc(e.get("time"))} s · {esc(q["item"])} · {esc(e.get("rune"))} · {esc(e.get("outcome"))} · {"admissible" if q["eligible"] else "à vérifier / rejeté"}</summary>')
        body.append('<pre>'+esc(json.dumps({'before':e.get('before'),'after':e.get('after'),'audit':audit,'reasons':q['reasons'],'evidence':e.get('evidence'),'raw':e.get('raw')},ensure_ascii=False,indent=2))+'</pre></details>')
    body.append('</html>')
    path=directory/'rapport.html'
    path.write_text('\n'.join(body),encoding='utf-8')
    return path
