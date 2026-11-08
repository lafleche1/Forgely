"""UI/CLI shared simulation job. Reads a captured context and local evidence only."""
from forgely_virtual import simulate_item


def simulate_context(context,*,db_file=None,**options):
    if not isinstance(context,dict):raise ValueError('Contexte JSON objet attendu')
    required=('jets','targets','natural_max','pool','prices')
    if any(k not in context for k in required):raise ValueError('Jet, cibles, maxima, puits et prix requis')
    sampler=calibration=None
    if db_file is not None:
        from forgely_loss_bank import LossBank
        from forgely_labo_live import LiveLaboratory, compute_snapshot
        item=context.get('item')
        if not item:raise ValueError('Objet requis pour utiliser les transitions réelles')
        bank=LossBank(db_file)
        lab=LiveLaboratory(db_file)
        lab._snapshot=compute_snapshot(db_file)
        sampler=lambda j,p,r,o,rng:bank.sample(item,j,p,r,o,rng)
        calibration=lambda r,j,p:lab.calibration(item,r,j,p)
    result=simulate_item(context['jets'],context['targets'],context['natural_max'],context['pool'],
        prices=context['prices'],level=context.get('level'),budget=context.get('budget'),item=context.get('item'),
        profile_complete=context.get('profile_complete',True),mode=context.get('mode','Chances maximales'),
        losses_for=sampler,context_for=calibration,**options)
    result['context']={k:context.get(k) for k in ('item','level','profile_complete','mode','budget')}
    return result
