"""Focused clean repository extraction acceptance. Supervisor runs after source handback.
Direct invocation only; no pytest/conftest, live provider, original tree or SDK.
"""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

MODULE = Path(__file__).resolve().parent
sys.path.insert(0,str(MODULE))
import portable_source as portable


class G16Publication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stack = ExitStack()
        cls.temp = Path(cls.stack.enter_context(tempfile.TemporaryDirectory(prefix='lh-public-g16-')))
        cls.bundle = cls.temp/'source.tar.gz'
        cls.receipt = portable.build(MODULE.parents[1],cls.bundle,repository=True)
        cls.fresh = cls.temp/'repository'
        portable.extract(cls.bundle,cls.receipt['sha256'],cls.fresh,repository=True)
        cls.module = cls.fresh/portable.MODULE_PREFIX
        cls.results = []

    @classmethod
    def tearDownClass(cls):
        print(json.dumps({'sourceDigest':cls.receipt['sourceDigest'],'files':cls.receipt['files'],
                          'workers':cls.results,'liveAcceptance':False},sort_keys=True))
        cls.stack.close()

    def launch(self, command, label):
        scratch = self.temp/label; scratch.mkdir()
        home = self.temp/(label+'-empty-home'); home.mkdir()
        env = {'PATH':os.environ['PATH'],'HOME':str(home),'TMPDIR':str(scratch),
               'PYTHONDONTWRITEBYTECODE':'1','LH_KNOWLEDGE_CONFIG':str(home/'absent.json'),
               'LH_EMBED_PROVIDER':'local','LH_EMBED_MODEL_DIR':str(home/'absent-model')}
        start = time.monotonic()
        result = subprocess.run(command,cwd=scratch,env=env,text=True,capture_output=True,timeout=180)
        self.results.append({'name':label,'exit':result.returncode,'seconds':round(time.monotonic()-start,3)})
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        print(result.stdout+result.stderr)

    def test_exact_repo_manifest_is_reproducible(self):
        second = portable.build(MODULE.parents[1],self.temp/'second.tar.gz',repository=True)
        self.assertEqual(second['sha256'],self.receipt['sha256'])
        files, manifest = portable.verify(self.bundle,self.receipt['sha256'],repository=True)
        self.assertEqual(set(files),set(portable.REPOSITORY_ALLOWLIST)|{portable.MANIFEST})
        self.assertEqual(len(manifest['files']),len(portable.REPOSITORY_ALLOWLIST))
        for name in portable.REPOSITORY_ALLOWLIST:
            self.assertEqual((self.fresh/name).read_bytes(),(MODULE.parents[1]/name).read_bytes())
            self.assertFalse(any(p in ('.local','node_modules','__pycache__') for p in Path(name).parts))
            self.assertNotIn(b'/home/'+b'lazydino/',files[name],name)
            self.assertNotIn(b'0.453291'+b'834',files[name],name)
        with self.assertRaises(ValueError): portable.verify(self.bundle,self.receipt['sha256'])

    def test_focused_python_workers_from_unrelated_cwd_home(self):
        for index, script in enumerate(('test_g16_closure.py','scale-04/test_offline.py',
                'scale-04/test_isolated_scope_offline.py',
                '../v2-native-minlive/unit1-trial-caller-01/test_trial.py')):
            with self.subTest(script=script):
                self.launch([sys.executable,'-I','-B',str(self.module/'test_g16_publication.py'),'--worker',script],f'python-{index}')

    def test_inherited_public_v2_acceptance_preserved(self):
        # The V2 coordinator builds again in its isolated extraction; Git metadata
        # is supplied only to the outer coordinator, so run its worker suites here.
        for index, script in enumerate(portable.PUBLIC_TESTS):
            if script.endswith('.py') and script != 'test_publication_bundle.py':
                with self.subTest(script=script):
                    self.launch([sys.executable,'-I','-B',str(self.module/'test_g16_publication.py'),'--worker',script],f'v2-{index}')
        bun = shutil.which('bun'); self.assertIsNotNone(bun,'Bun is required; no auto-install')
        self.launch([bun,str(self.module/'test_public_loader.ts'),str(self.module)],'loader')

    def test_dynamic_js_hosts_and_injected_broker_without_sdk(self):
        node = shutil.which('node'); self.assertIsNotNone(node,'Node is required; no auto-install')
        self.launch([node,str(self.module/'test_g16_hosts.mjs')],'javascript')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        from test_publication_bundle import worker
        worker(sys.argv[2],repository=True)
    else:
        unittest.main(verbosity=2)
