"""Build the packaged read-only reference from the auditable authoring JSON."""
import argparse
import json
from forgely_dofocus import REFERENCE_PATH,STORE_PATH
from forgely_dofocus_store import build_database


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',default=str(REFERENCE_PATH))
    parser.add_argument('--destination',default=str(STORE_PATH))
    args=parser.parse_args()
    print(json.dumps(build_database(args.source,args.destination),ensure_ascii=False))


if __name__=='__main__':main()
