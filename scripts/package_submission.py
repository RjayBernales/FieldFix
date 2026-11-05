#!/usr/bin/env python3
"""Build a local review archive from an explicit, secret-free source allowlist."""
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]
paths=[p for directory in ('backend','frontend/src','frontend/public','scripts','docu','rules','.github') for p in (ROOT/directory).rglob('*')
       if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.sh','.txt','.tsx','.ts','.css','.html','.json','.md','.png','.jpg','.jpeg','.svg','.yml','.yaml'}]
paths += [ROOT/p for p in ('README.md','.gitignore','.env.example','pyproject.toml','requirements.lock',
          'Dockerfile','.dockerignore','render.yaml','frontend/index.html','frontend/package.json','frontend/package-lock.json','frontend/tsconfig.json','frontend/vite.config.ts')]
key=dotenv_values(ROOT/'.env').get('MODEL_API_KEY')
for path in paths:
    if key and len(key)>8 and key.encode() in path.read_bytes():
        raise SystemExit('Configured key found in candidate: '+str(path.relative_to(ROOT)))
output=ROOT/'.data/fieldfix-review.zip'
output.parent.mkdir(exist_ok=True)
with ZipFile(output,'w',ZIP_DEFLATED) as archive:
    for path in sorted(set(paths)):
        archive.write(path,'FieldFix/'+str(path.relative_to(ROOT)))
print(f'Local review archive: {output} ({len(set(paths))} files)')
print('Archive SHA-256: '+hashlib.sha256(output.read_bytes()).hexdigest())
