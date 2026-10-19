"""Rebuild everything from the Capitaline exports in data/raw/.

    python run_pipeline.py

Order matters: the broad universe (build_lite) feeds shareholding into the full model (build).
"""
import subprocess, sys, time
from pathlib import Path
STEPS = ['load.py', 'build_lite.py', 'build.py', 'rank.py', 'export.py', 'export_lite.py', 'export_rules.py', 'build_html.py', 'build_extra.py']
here = Path(__file__).resolve().parent / 'pipeline'
for s in STEPS:
    t = time.time()
    print(f'→ {s}', flush=True)
    r = subprocess.run([sys.executable, s], cwd=here, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-4000:]); sys.exit(f'Step {s} failed')
    print(f'  done in {time.time()-t:.0f}s')
print('All outputs are in data/work/ and web/artha.html')
