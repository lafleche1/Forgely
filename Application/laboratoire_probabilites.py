"""Usage: python laboratoire_probabilites.py observations.csv --sortie rapport.json"""
import argparse,json
from pathlib import Path
from forgely_probabilites_conditionnelles import audit_conditional

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('csv');parser.add_argument('--sortie',default='probabilites_conditionnelles.json')
    parser.add_argument('--minimum',type=int,default=50)
    args=parser.parse_args()
    report=audit_conditional(args.csv,minimum=args.minimum)
    Path(args.sortie).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Rapport créé :',args.sortie,'—',len(report['groupes']),'groupes')
if __name__=='__main__':main()
