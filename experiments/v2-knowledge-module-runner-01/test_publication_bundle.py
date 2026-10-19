"""Public source acceptance: fresh checksum-bound extraction, isolated workers.

Run directly: python3 test_publication_bundle.py. Only the coordinator launches
explicit Python/Bun fixture processes and read-only Git metadata for packaging.
Workers deny network, subprocesses, DB drivers and private filesystem reads.
No pytest conftest, original checkout/PYTHONPATH, installed SDK or DB is needed.
"""
import ast
from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import types
import unittest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def worker(script):
    root = Path(__file__).resolve().parent
    scratch = Path(os.environ['TMPDIR']).resolve()
    allowed = (root, scratch, Path(sys.base_prefix) / 'lib')
    blocked = []

    def deny(*args, **kwargs):
        raise AssertionError('offline publication effect denied')

    def audit(event, args):
        if event == 'open':
            raw = args[0]
            if isinstance(raw, int):
                return
            path = Path(os.fsdecode(raw)).resolve()
            if not any(path == base or base in path.parents for base in allowed):
                blocked.append(str(path))
                raise PermissionError('private/outside fixture read denied')
        if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.posix_spawnp',
                     'os.exec', 'os.fork', 'socket.connect', 'socket.getaddrinfo',
                     'socket.bind', 'socket.sendto', 'ctypes.dlopen'):
            raise PermissionError('offline effect denied: ' + event)

    # Offline tests do not require a real database driver merely to import code.
    # This module cannot connect, parse SQL, charge usage or certify PostgreSQL.
    for name in ('psycopg', 'psycopg2'):
        driver = types.ModuleType(name)
        driver.connect = deny
        driver.Error = RuntimeError
        sys.modules[name] = driver
    import socket
    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    socket.create_connection = deny
    socket.getaddrinfo = deny
    subprocess.Popen = deny
    sys.addaudithook(audit)
    before = len(blocked)
    for private in (Path.home() / '.ssh/id_ed25519', Path.home() / '.pi/agent/auth.json',
                    root.parent / 'original-source-canary'):
        try:
            private.read_bytes()
        except PermissionError:
            pass
        else:
            raise AssertionError('private read seam did not reject')
    # HOME is deliberately outside the allowed working scratch, even though empty.
    if len(blocked) != before + 3:
        raise AssertionError('private source/HOME denial coverage missing')
    sys.argv = [str(root / script)]
    runpy.run_path(str(root / script), run_name='__main__')


class PublicationBundle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import portable_source
        cls.p = portable_source
        cls.stack = ExitStack()
        cls.temp = Path(cls.stack.enter_context(tempfile.TemporaryDirectory(prefix='lh-public-v2-')))
        cls.bundle = cls.temp / 'source.tar.gz'
        cls.result = cls.p.build(ROOT, cls.bundle)
        cls.fresh = cls.temp / 'clean-extraction'
        cls.p.extract(cls.bundle, cls.result['sha256'], cls.fresh)
        cls.receipts = []

    @classmethod
    def tearDownClass(cls):
        print(json.dumps({'sourceDigest': cls.result['sourceDigest'], 'files': cls.result['files'],
                          'isolated_workers': cls.receipts}, sort_keys=True))
        cls.stack.close()

    def test_reproducible_exact_safe_manifest_and_seed_closure(self):
        second = self.p.build(ROOT, self.temp / 'second.tar.gz')
        self.assertEqual(second['sha256'], self.result['sha256'])
        files, manifest = self.p.verify(self.bundle, self.result['sha256'])
        self.assertEqual(set(files), set(self.p.ALLOWLIST) | {self.p.MANIFEST})
        self.assertEqual(len(manifest['files']), len(self.p.ALLOWLIST))
        self.assertEqual(sum(n.startswith('migrations/') for n in files), 18)
        for name in self.p.ALLOWLIST:
            self.assertEqual((self.fresh / name).read_bytes(), (ROOT / name).read_bytes())
            parts = Path(name).parts
            self.assertFalse(any(p in ('.local', 'node_modules', '__pycache__', 'scale-04') for p in parts))
            self.assertNotIn(name, ('knowledge.json', 'before.json'))
            body = files[name]
            if name.endswith('.py'):
                ast.parse(body, filename=name)
            # Actual personal source roots and captured private identifiers are forbidden.
            for forbidden in (b'/home/' + b'lazydino/', b'Qron8FAT' + b'7dOWHi1S2Qtjq8',
                              b'treatment-' + b'document-102rev1'):
                self.assertNotIn(forbidden, body, name)
        self.assertIn(b'create', files['migrations/0001_knowledge_init.sql'].lower())
        self.assertNotIn('db_url', json.dumps(manifest))
        with self.assertRaises(FileExistsError):
            self.p.extract(self.bundle, self.result['sha256'], self.fresh)
        with self.assertRaises(ValueError):
            self.p.verify(self.bundle, '0' * 64)

    def test_traversal_links_missing_duplicate_and_tampered_assets_reject(self):
        for index, (name, kind) in enumerate((('../escape', tarfile.REGTYPE), ('config.py', tarfile.SYMTYPE))):
            archive = self.temp / f'bad-{index}.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                info = tarfile.TarInfo(name)
                info.type = kind
                info.linkname = '/etc/passwd' if kind == tarfile.SYMTYPE else ''
                info.size = 0
                tar.addfile(info, io.BytesIO(b''))
            with self.assertRaises(ValueError):
                self.p.extract(archive, self.p.digest(archive.read_bytes()), self.temp / f'bad-dest-{index}')
            self.assertFalse((self.temp / f'bad-dest-{index}').exists())
        files, _ = self.p.verify(self.bundle, self.result['sha256'])
        for mode in ('missing', 'duplicate', 'tampered'):
            archive = self.temp / f'{mode}.tar.gz'
            with tarfile.open(archive, 'w:gz') as tar:
                for name, body in files.items():
                    if mode == 'missing' and name.endswith('0001_knowledge_init.sql'):
                        continue
                    if mode == 'tampered' and name == 'templates.py':
                        body += b'\n# changed\n'
                    for _ in range(2 if mode == 'duplicate' and name == 'config.py' else 1):
                        info = tarfile.TarInfo(name)
                        info.size = len(body)
                        tar.addfile(info, io.BytesIO(body))
            with self.assertRaises(ValueError):
                self.p.verify(archive, self.p.digest(archive.read_bytes()))
        source = self.temp / 'symlink-source'
        source.mkdir()
        first = source / self.p.ALLOWLIST[0]
        first.parent.mkdir(exist_ok=True, parents=True)
        first.symlink_to(ROOT / self.p.ALLOWLIST[0])
        with self.assertRaises(ValueError):
            self.p.inventory(source)

    def isolated(self, command, label):
        scratch = self.temp / label
        scratch.mkdir()
        # HOME must not overlap the worker's allowed scratch/read roots.
        home = self.temp / (label + '-home')
        home.mkdir()
        env = {'PATH': os.environ['PATH'], 'HOME': str(home), 'TMPDIR': str(scratch),
               'PYTHONDONTWRITEBYTECODE': '1', 'LH_KNOWLEDGE_CONFIG': str(home / 'absent.json'),
               'LH_EMBED_PROVIDER': 'local', 'LH_EMBED_MODEL_DIR': str(home / 'absent-model')}
        started = time.monotonic()
        result = subprocess.run(command, cwd=scratch, env=env, text=True, capture_output=True, timeout=90)
        self.receipts.append({'name': label, 'seconds': round(time.monotonic() - started, 3), 'exit': result.returncode})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout + result.stderr)

    def test_all_inherited_offline_and_maintenance_cases_from_clean_extraction(self):
        for name in self.p.PUBLIC_TESTS:
            if name.endswith('.py') and name != Path(__file__).name:
                with self.subTest(script=name):
                    self.isolated([sys.executable, '-I', '-B', str(self.fresh / Path(__file__).name), '--worker', name], name[:-3])

    def test_relocated_javascript_loader_with_inert_host(self):
        bun = shutil.which('bun')
        self.assertIsNotNone(bun, 'Bun is needed for the synthetic loader check; never auto-install')
        self.isolated([bun, str(self.fresh / 'test_public_loader.ts'), str(self.fresh)], 'loader')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        worker(sys.argv[2])
    else:
        unittest.main(verbosity=2)
