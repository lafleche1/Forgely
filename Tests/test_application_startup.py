"""Exercise the actual desktop constructor, not only individual panels."""
import os
from pathlib import Path
import subprocess
import sys


def test_complete_application_starts_and_closes_with_empirical_worker(tmp_path):
    application=Path(__file__).resolve().parents[1]/'Application'
    script=r'''
from forgely import Forgely
app=Forgely()
try:
    app.update()
    assert app.live_laboratory is not None
    assert app.simulator.empirical_for().sample_count>=0
    assert app.winfo_exists()
    # Replacing the laboratory (e.g. a test/profile reload) must not leave the
    # simulator reading the bound method of the previous instance.
    from types import SimpleNamespace
    original=app.live_laboratory;marker=object()
    try:
        app.live_laboratory=SimpleNamespace(empirical_model=lambda:marker)
        assert app.simulator.empirical_for() is marker
    finally:app.live_laboratory=original
finally:
    app.close()
print('Forgely started and closed successfully')
'''
    env=dict(os.environ,PYTHONPATH=str(application),LOCALAPPDATA=str(tmp_path/'profile'),
             APPDATA=str(tmp_path/'roaming'),TEMP=str(tmp_path),TMP=str(tmp_path))
    result=subprocess.run([sys.executable,'-c',script],cwd=application,env=env,
                          capture_output=True,text=True,timeout=40)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'Forgely started and closed successfully' in result.stdout
