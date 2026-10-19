"""Harmless tagged fixture only: no product imports, DB, models or network."""
import os
from pathlib import Path
import sys
import time
if not os.environ.get('UNIT1_FIXTURE_OWNER'): raise SystemExit('missing fixture owner')
if sys.argv[1]=='ok':
    print('owned fixture OK',flush=True)
else:
    child=os.fork()
    if child==0:
        Path('grandchild.pid').write_text(str(os.getpid()))
        time.sleep(5)
        os._exit(0)
    Path('child.pid').write_text(str(os.getpid()))
    time.sleep(5)
