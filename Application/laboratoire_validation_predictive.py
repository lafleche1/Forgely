"""Exemple : python laboratoire_validation_predictive.py observations.csv --sortie validation.json"""
import argparse,json
from pathlib import Path
from forgely_validation_predictive import validate_temporal

def main():
    p=argparse.ArgumentParser(description='Valider les probabilités FM sur des tentatives futures tenues à part')
    p.add_argument('csv');p.add_argument('--sortie',default='validation_predictive.json')
    p.add_argument('--minimum',type=int,default=50)
    p.add_argument('--train-fraction',type=float,default=.8)
    a=p.parse_args()
    result=validate_temporal(a.csv,minimum=a.minimum,train_fraction=a.train_fraction)
    Path(a.sortie).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Validation créée :',a.sortie,'; test couvert :',result['test_couvert'],'/',result['test'])
if __name__=='__main__':main()
