"""Scan tracked deliverable candidates, not local secrets/planning material."""
import re
from pathlib import Path

roots=[Path('backend'),Path('frontend/src'),Path('frontend/dist'),Path('scripts'),Path('docu'),Path('rules'),Path('.github')]
files=[p for root in roots for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
files += [Path('README.md'),Path('.env.example'),Path('frontend/package.json'),Path('frontend/package-lock.json'),Path('requirements.lock'),Path('pyproject.toml'),Path('Dockerfile'),Path('.dockerignore'),Path('render.yaml')]
patterns=[re.compile(r'(?i)(?:api[_-]?key|authorization|access[_-]?token)\s*[:=]\s*["\'](?:Bearer )?[A-Za-z0-9_\-]{24,}["\']'),re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}'),re.compile(r'github_pat_[A-Za-z0-9_]{20,}'),re.compile(r'LLM_[A-Za-z0-9_-]{24,}'),re.compile(r'-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----')]
issues=[]
for p in files:
    if p.suffix in {'.png','.jpg','.webm'}:continue
    text=p.read_text(errors='replace')
    if any(pattern.search(text) for pattern in patterns):issues.append(str(p))
# Compare against the actual locally configured key without printing it.
try:
    from dotenv import dotenv_values
    key=dotenv_values('.env').get('MODEL_API_KEY')
except ImportError:
    key=None
if key and len(key)>8:
    for p in files:
        if p.suffix not in {'.png','.jpg','.webm'} and key in p.read_text(errors='replace'):
            issues.append(str(p))
if issues:raise SystemExit('Potential secret in: '+', '.join(issues))
print(f'Pattern secret scan passed for {len(files)} deliverable files. Manual review still required.')
