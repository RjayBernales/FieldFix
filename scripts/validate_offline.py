#!/usr/bin/env python3
"""Reproducible deterministic simulator/provider evidence. Makes no network calls."""
import asyncio
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.agent import MockProvider, investigate
from app.core import Engine, STATION
from app.storage import Store


class Clock:
    def __init__(self):self.value=1793754000.0
    def __call__(self):return self.value
    def advance(self):self.value+=2


def manifest():
    paths=[p for directory in ('backend','frontend/src','scripts') for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [ROOT/p for p in ('pyproject.toml','requirements.lock','frontend/package.json','frontend/package-lock.json','frontend/tsconfig.json','frontend/vite.config.ts','.env.example')]
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    fingerprint=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    return dict(algorithm='SHA-256',fingerprint=fingerprint,files=hashes)


def commit():
    r=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True)
    return r.stdout.strip() if r.returncode==0 else None


async def main():
    snapshot=manifest()
    output=dict(at=datetime.now(timezone.utc).isoformat(),tested_commit=commit(),source_fingerprint=snapshot['fingerprint'],
                provider='mock',model='deterministic-offline-fixture',station_data='synthetic',
                clock='injected deterministic clock; elapsed sample intervals are simulated',runs=[],live_requests=0)
    for n,scenario in enumerate(('mismatch','healthy','sensor_failure','unavailable')):
        e=Engine(Store(':memory:'),Clock())
        e.reset(scenario, f'custom/site-{n+1}/turbidity')
        before=e.config()['subscription_topic']
        i=e.new_incident('mock','Inspect station evidence and cite observations.')
        await investigate(e,i['id'],MockProvider())
        i=e.store.get('incidents',i['id'])
        proposal=e.store.get('proposals',i['proposal_id']) if i['proposal_id'] else None
        unchanged=e.config()['subscription_topic']==before
        if proposal:
            e.decide(proposal['id'],STATION,True)
            for _ in range(3):e.clock.advance();e.tick();e.verify_step(i['id'])
        i=e.store.get('incidents',i['id'])
        passed=i['state']=='resolved' if scenario=='mismatch' else i['state']=='unresolved' and proposal is None
        output['runs'].append(dict(scenario=scenario,result='pass' if passed else 'fail',state=i['state'],finding=i['finding'],
            unchanged_before_approval=unchanged,model_turns=i['model_turns'],tool_calls=i['tool_calls'],
            evidence=e.evidence_list(i['id']),proposal=proposal,verification=i['verification']))
        e.store.close()
    directory=ROOT/'docu';directory.mkdir(exist_ok=True)
    (directory/'source-manifest.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    (directory/'offline-results.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(dict(provider='mock',source_fingerprint=snapshot['fingerprint'],runs=len(output['runs']),passed=sum(r['result']=='pass' for r in output['runs']),live_requests=0)))
    return 0 if all(r['result']=='pass' for r in output['runs']) else 1


if __name__=='__main__':sys.exit(asyncio.run(main()))
