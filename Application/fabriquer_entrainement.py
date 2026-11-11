"""Rebuild the standalone desktop trainer into the Forgely project folder."""
from pathlib import Path
import subprocess
import sys


def main():
    application = Path(__file__).resolve().parent
    project = application.parent
    temporary = project / '.test-tmp' / 'training-exe-build'
    temporary.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
        '--onefile', '--windowed', '--name', 'Entrainement_Forgely',
        '--distpath', str(project), '--workpath', str(temporary / 'work'),
        '--specpath', str(temporary), '--paths', str(application),
        '--icon', str(application / 'assets' / 'forgely.ico')]
    for relative in ['catalogue_objets_noms_fr.csv', 'assets/equipment_bounds.csv',
                     'assets/forgely.ico', 'catalogue_dofus3/index.json',
                     'references/poids_runes_client_3_7_13_17.json']:
        source = application / relative
        command.extend(['--add-data', str(source) + ':' + str(Path(relative).parent)])
    command.append(str(application / 'entrainer_forgely.py'))
    return subprocess.run(command, cwd=project, check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
