"""Read-only empirical loss samples. Never inserts generated states into real DBs."""
from collections import defaultdict
from contextlib import closing
from pathlib import Path
import json
import sqlite3
from forgely_dofocus import normalise_jet, reference, RUNE_CHOICES
from forgely_expert import audit_transition
from forgely_virtual import apply_outcome
from forgely_rules import finite_number


def state_key(item,jets,pool,rune,outcome):
    jets=normalise_jet(jets)
    if not jets or not finite_number(pool,nonnegative=True):return None
    return item,rune,outcome,tuple(sorted(jets.items())),float(pool)


class LossBank:
    def __init__(self,path):
        self.groups=defaultdict(list);self.samples=0
        path=Path(path)
        if not path.exists():return
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
            exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fusion_contexts'").fetchone()
            if not exists:return
            cols={r[1] for r in db.execute('PRAGMA table_info(fusion_contexts)')}
            if not {'calibration_verified','before_json','after_json','source'}.issubset(cols):return
            rows=db.execute("SELECT item,rune,outcome,before_json,after_json FROM fusion_contexts WHERE calibration_verified=1 AND source='local_screen' AND outcome IN ('SN','EC')")
            for item,rune,outcome,start,end in rows:
                try:
                    before,after=json.loads(start),json.loads(end)
                    before={'jet':normalise_jet(before['jet']),'pool':before['pool']}
                    after={'jet':normalise_jet(after['jet']),'pool':after['pool']}
                    if audit_transition(rune,outcome,before,after,complete=True)['status']!='cohérent':continue
                    stat=next(s for s,rs in RUNE_CHOICES.items() if rune in rs)
                    gain=reference(rune).gain if outcome=='SN' else 0
                    losses={s:round(v+(gain if s==stat else 0)-after['jet'][s],6)
                            for s,v in before['jet'].items()}
                    losses={s:v for s,v in losses.items() if v>0}
                    reconstructed=apply_outcome(before['jet'],before['pool'],rune,outcome,losses=losses)
                    if reconstructed!=after:continue
                    self.groups[state_key(item,before['jet'],before['pool'],rune,outcome)].append(losses)
                    self.samples+=1
                except (ValueError,TypeError,KeyError,StopIteration):continue

    def sample(self,item,jets,pool,rune,outcome,rng):
        matches=self.groups.get(state_key(item,jets,pool,rune,outcome))
        return dict(rng.choice(matches)) if matches else None
