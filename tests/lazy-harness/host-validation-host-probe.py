"""Unmocked host-mode gate; owns only a disposable harness copy, no app/deps copy."""
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

source = Path(__file__).resolve().parents[2]
namespace = runpy.run_path(str(source / '.lazy-harness/scripts/self-test.py'), run_name='isolated_host_probe')
code = 1
with tempfile.TemporaryDirectory(prefix='host-validation-isolation-') as directory:
    host = Path(directory).resolve() / 'host'
    lazy = host / '.lazy-harness'
    namespace['copy_harness_fixture'](source / '.lazy-harness', lazy, ('.cache', 'state'))
    local = lazy / 'scripts/local/operator.sh'
    (host / '.gitignore').write_text('__pycache__/\n*.pyc\n.lazy-harness/tmp/\n.lazy-harness/state/\n.lazy-harness/.cache/\n')
    local.parent.mkdir(exist_ok=True)
    local.write_text('# host-owned local operation for ' + 'medi' + 'vance' + '\n')
    subprocess.run(['git', 'init', '-q', '--initial-branch=fix/host-validation-probe'], cwd=host, check=True)
    # Disposable fixture history only: never commit in source/candidate/user worktrees.
    subprocess.run(['git', '-c', 'user.name=ValidationFixture', '-c', 'user.email=fixture@example.invalid', '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-qm', 'Test: seed disposable host HEAD'], cwd=host, check=True)
    command = [str(lazy / 'bin/lazy'), 'validate', '--plan', 'standard', '--scope', 'host', '--evidence-cache', 'off', '--format', 'json']
    print(json.dumps({'mode':'isolated-host-probe','command':command,'cwd':str(host),'applicationCopies':0,'dependencyCopies':0}), flush=True)
    result = subprocess.run(command, cwd=host, env=namespace['env_without_lazy_runtime'](LAZY_HOST_ROOT=str(host)), check=False)
    code = result.returncode
print(json.dumps({'mode':'isolated-host-cleanup','fixtureRemoved':not Path(directory).exists(),'exitCode':code}), flush=True)
raise SystemExit(code)
