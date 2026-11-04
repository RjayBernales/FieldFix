#!/usr/bin/env python3
"""Explicit live validation. Writes sanitized results; never prints provider bodies or keys."""
import argparse
import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend'))
from app.agent import MetaProvider, investigate
from app.core import Engine, STATION
from app.settings import Settings
from app.storage import Store
from validate_offline import manifest


def revision():
    r = subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True)
    return r.stdout.strip() if r.returncode==0 else 'uncommitted workspace (set tested_commit after local review)'


async def main(args):
    settings=Settings()
    stamp=datetime.now(timezone.utc).isoformat()
    result=dict(at=stamp,tested_commit=revision(),source_fingerprint=manifest()['fingerprint'],provider='meta',model=settings.model,
                station_data='synthetic software station',runs=[],gate='blocked',limitations=[])
    if not settings.api_key:
        result['limitations'].append('MODEL_API_KEY is not visible to this process. No live request attempted.')
    else:
        engine=Engine(Store(settings.db))
        provider=MetaProvider(settings,engine)
        async def tick():
            while True:
                await asyncio.sleep(2);engine.tick()
        task=asyncio.create_task(tick())
        try:
            for n,scenario in enumerate(['mismatch']*args.primary+(['healthy'] if args.healthy else [])):
                engine.reset(scenario, f'stations/validation-{n+1}/turbidity')
                i=engine.new_incident('meta','Inspect station evidence. Compare local and delivered samples and transport configuration. Cite evidence for your conclusion.')
                started=time.monotonic()
                await investigate(engine,i['id'],provider)
                i=engine.store.get('incidents',i['id'])
                before=i['state']
                proposal=engine.store.get('proposals',i['proposal_id']) if i['proposal_id'] else None
                if i['state']=='awaiting_approval' and args.approve_repairs:
                    # CLI flag explicitly authorizes applying the exact simulated repair proposals in this harness.
                    engine.decide(proposal['id'],STATION,True)
                    while not engine.verify_step(i['id']):await asyncio.sleep(.5)
                i=engine.store.get('incidents',i['id'])
                traces=[json.loads(r[0]) for r in engine.store.db.execute('SELECT body FROM inference WHERE incident_id=?',(i['id'],))]
                evidence=engine.evidence_list(i['id'])
                passed=(i['state']=='resolved') if scenario=='mismatch' else (i['state']=='unresolved' and proposal is None and 'no fault' in i['finding'].lower() and len(evidence)>=3)
                result['runs'].append(dict(scenario=scenario,incident_id=i['id'],result='pass' if passed else 'fail',
                    state=i['state'],state_before_approval=before,finding=i['finding'],elapsed_seconds=round(time.monotonic()-started,2),
                    model_turns=i['model_turns'],tool_calls=i['tool_calls'],inference=traces,evidence=evidence,
                    proposal=proposal,verification=i['verification']))
                # At least two successful inference requests with a diagnostic tool result between them.
                if i['tool_calls'] and sum(t['outcome']=='ok' for t in traces)>=2:result['gate']='passed'
                if i['state'] in {'awaiting_approval','failed'}:
                    if i['state']=='awaiting_approval':engine.decide(proposal['id'],STATION,False)
                    if i['state']=='failed':
                        result['limitations'].append('Live inference did not complete: '+i['finding'])
                        break
        finally:
            task.cancel();await asyncio.gather(task,return_exceptions=True);engine.store.close()
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(gate=result['gate'],runs=len(result['runs']),passed=sum(r['result']=='pass' for r in result['runs']),output=str(output),limitations=result['limitations'])),flush=True)
    return 0 if result['gate']=='passed' and all(r['result']=='pass' for r in result['runs']) else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--primary',type=int,choices=range(1,4),default=1)
    p.add_argument('--healthy',action='store_true')
    p.add_argument('--approve-repairs',action='store_true')
    p.add_argument('--output',default='docu/live-results.json')
    sys.exit(asyncio.run(main(p.parse_args())))
