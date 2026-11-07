"""Audit offline des observations, distinct de Forgely et de la simulation."""
import argparse
import json
from forgely_validation import export_report


def main():
    parser = argparse.ArgumentParser(description='Auditer les tentatives de FM vérifiées, sans modifier Forgely')
    parser.add_argument('observations_csv', help='CSV exporté depuis Forgely ou relevé vidéo revu manuellement')
    parser.add_argument('--sortie', default='audit_fm.json')
    parser.add_argument('--minimum', type=int, default=30)
    args = parser.parse_args()
    report = export_report(args.observations_csv, args.sortie, min_samples=args.minimum)
    print(json.dumps({'fichier': args.sortie, 'lignes_acceptees': report['lignes_acceptees'],
                      'lignes_exclues': report['lignes_exclues'], 'groupes': len(report['groupes'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
