"""Quality first, then observed task-specific cost/latency; deterministic and advisory."""
from decimal import Decimal
from kpis import summarize
from profiles import PROFILES,PROFILE_VERSION,available


def recommend(runs,task_id,objective='balanced'):
    if objective not in {'balanced','cost','speed'}:
        raise ValueError('INVALID_OBJECTIVE')
    comparable=[r for r in runs if r.get('task_id')==task_id and not r['synthetic']
                and r.get('profile_version')==PROFILE_VERSION and r.get('runtime')=='openshell'
                and r['limit']==250000 and r['metric']=='active_context']
    rows=summarize(comparable)
    eligible=[]
    for row in rows:
        key=next((k for k,p in PROFILES.items() if p['model']==row['model']),None)
        if (key is None or not available(key) or row['offered']<2 or row['pending']
                or row['autonomous']!=row['completed'] or not row['usage_complete']
                or row['cost_per_autonomous_success_usd'] is None
                or Decimal(row['cost_per_autonomous_success_usd'])<=0 or not row['median_ms']):
            continue
        eligible.append({**row,'profile':key,'evidence_run_ids':[r['id'] for r in comparable if r['model']==row['model']]})
    if not eligible:
        return {'profile':'glm','model':PROFILES['glm']['model'],'task_id':task_id,'objective':objective,
                'basis':'provisional_default','reason':'At least two complete autonomous successes per comparable profile are required.','candidates':[]}
    cost_min=min(Decimal(r['cost_per_autonomous_success_usd']) for r in eligible)
    time_min=min(r['median_ms'] for r in eligible)
    for row in eligible:
        cost=Decimal(row['cost_per_autonomous_success_usd'])/cost_min
        speed=Decimal(str(row['median_ms']/time_min))
        row['selection_score']=float(cost if objective=='cost' else speed if objective=='speed' else (cost+speed)/2)
    eligible.sort(key=lambda r:(r['selection_score'],r['model']))
    best=eligible[0]
    return {'profile':best['profile'],'model':best['model'],'task_id':task_id,'objective':objective,
            'basis':'best_observed_for_task','reason':'100% recorded autonomy and complete usage; cost and time normalized to the best observed values (equal weights for balanced).',
            'candidates':eligible,'profile_version':PROFILE_VERSION}
