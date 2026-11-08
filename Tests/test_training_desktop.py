"""A real Tk root is tested in a child process to isolate Tcl shutdown."""
from pathlib import Path
import os
import subprocess
import sys


def test_desktop_training_runs_and_saves_without_blocking_tk(tmp_path):
    application = Path(__file__).resolve().parents[1] / 'Application'
    script = r'''
import sys,time,tkinter as tk,threading
from pathlib import Path
from entrainer_forgely import TrainingWindow
import forgely_training
main_thread=threading.get_ident()
training_threads=[]
original_training=forgely_training.run_training
def recording_training(*args,**kwargs):
    training_threads.append(threading.get_ident())
    return original_training(*args,**kwargs)
forgely_training.run_training=recording_training
root=tk.Tk()
root.withdraw()
window=TrainingWindow(root,Path(sys.argv[1]))
assert window.selected_id==14092
assert window.generalization.get() is False
window.extra_value.set('PA')
window.add_extra()
assert window.targets['PA'].get()=='1'
window.targets['PA'].set('')
for stat,value in window.targets.items():
    value.set('40' if stat=='Force' else '')
window.episodes.set('2')
window.max_steps.set('5')
window.evaluations.set('2')
window.start()
assert window.running
deadline=time.monotonic()+30
ticks=0
while window.running and time.monotonic()<deadline:
    root.update()
    time.sleep(.01)
    ticks+=1
assert not window.running,window.status.get()
assert ticks>=1
assert training_threads and all(identifier!=main_thread for identifier in training_threads)
assert window.last_report and window.last_report.is_file(),window.status.get()
assert str(window.report_button['state'])=='normal'
window.close()
'''
    env = dict(os.environ, PYTHONPATH=str(application))
    result = subprocess.run([sys.executable, '-c', script, str(tmp_path)],
                            env=env, text=True, capture_output=True, timeout=40)
    assert result.returncode == 0, result.stdout + result.stderr


def test_closing_desktop_cancels_and_saves_training(tmp_path):
    application = Path(__file__).resolve().parents[1] / 'Application'
    script = r'''
import sys,tkinter as tk,json
from pathlib import Path
from entrainer_forgely import TrainingWindow
root=tk.Tk()
root.withdraw()
window=TrainingWindow(root,Path(sys.argv[1]))
window.episodes.set('100000')
window.start()
window.close()
root.after(30000,root.destroy)
root.mainloop()
assert not window.running
assert window.last_report and window.last_report.is_file()
metrics=json.loads(window.last_report.with_name('metrics.json').read_text(encoding='utf-8'))
assert metrics['cancelled']
assert metrics['episodes_completed']<100000
'''
    env = dict(os.environ, PYTHONPATH=str(application))
    result = subprocess.run([sys.executable, '-c', script, str(tmp_path)],
                            env=env, text=True, capture_output=True, timeout=40)
    assert result.returncode == 0, result.stdout + result.stderr


def test_desktop_footer_remains_visible_at_compact_height(tmp_path):
    application = Path(__file__).resolve().parents[1] / 'Application'
    script = r'''
import sys,tkinter as tk
from pathlib import Path
from entrainer_forgely import TrainingWindow
root=tk.Tk()
window=TrainingWindow(root,Path(sys.argv[1]))
root.geometry('1020x700+30+30')
root.update()
for widget in (window.start_button,window.stop_button,window.progress,window.status_label):
    top=widget.winfo_rooty()-root.winfo_rooty()
    assert 0<=top and top+widget.winfo_height()<=root.winfo_height(),(top,widget.winfo_height(),root.winfo_height())
assert window.status_label.winfo_ismapped()
window.close()
'''
    env = dict(os.environ, PYTHONPATH=str(application))
    result = subprocess.run([sys.executable, '-c', script, str(tmp_path)],
                            env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
