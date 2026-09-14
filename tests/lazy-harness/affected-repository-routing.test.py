"""Operative hook -> canonical Bun runner -> owner-specific real Bun tests."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(os.environ.get('LAZY_AFFECTED_SOURCE') or Path(__file__).resolve().parents[2])


class AffectedRepositoryRouting(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='affected two repositories ')
        self.base = Path(self.temp.name)
        self.host = self.base / 'session host'
        self.host.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_', 'LAZY_', 'JCODE_'))}
        # Preserve the full real lifecycle topology, including orchestrator,
        # preceding helpers and runtime adapters; never stub or disable helpers.
        shutil.copytree(SOURCE / '.lazy-harness', self.host / '.lazy-harness',
                        ignore=shutil.ignore_patterns('.cache', 'state', 'logs', '__pycache__', '.runtime'))
        self.owners = [self.base / 'repo A', self.base / 'repo B with spaces']
        self.relative = 'src/same file, component.ts'
        for index, owner in enumerate(self.owners):
            (owner / 'src').mkdir(parents=True)
            subprocess.run(['git', 'init', '-q', str(owner)], env=self.env, check=True)
            (owner / self.relative).write_text('export const value = 1;\n')
            (owner / self.relative.replace('.ts', '.test.ts')).write_text('''import { test, expect } from "bun:test";
import { appendFileSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
test("owning repository and real failure propagation", () => {
  const root = execFileSync("git", ["rev-parse", "--show-toplevel"], {encoding:"utf8"}).trim();
  appendFileSync("executed.jsonl", JSON.stringify({cwd:process.cwd(),root,script:process.env.npm_lifecycle_event}) + "\\n");
  expect(root).toBe(process.cwd());
  expect(existsSync("fail-test")).toBe(false);
});
''')
            script = f'verify-{index}'
            (owner / 'package.json').write_text(json.dumps({'scripts': {script: 'bun test'}}))
            strategy = owner / '.lazy-harness/tests/test-strategy.xml'
            strategy.parent.mkdir(parents=True)
            strategy.write_text(f'<test-strategy><affectedTestRouting command="bun run {script} {{tests}}" /></test-strategy>')
        self.env.update(LAZY_HOST_ROOT=str(self.host), LAZY_HOOK_TIMING='0',
                        LAZY_HARNESS_QUESTION_QUEUE=str(self.base / 'queue.xml'))
        # Deliberately point every inherited Git selector at the wrong repository.
        self.env.update(GIT_DIR=str(self.owners[0] / '.git'), GIT_WORK_TREE=str(self.owners[0]),
                        GIT_COMMON_DIR=str(self.owners[0] / '.git'), GIT_INDEX_FILE=str(self.owners[0] / '.git/index'),
                        GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='core.worktree', GIT_CONFIG_VALUE_0=str(self.owners[0]))

    def tearDown(self):
        self.temp.cleanup()

    def hook(self, calls, engine='legacy'):
        payload = {'recent_tool_calls': calls}
        result = subprocess.run(['bash', str(self.host / '.lazy-harness/hooks/lifecycle/on-response-completed.sh')],
                                cwd=self.host, env={**self.env, 'LAZY_RESPONSE_COMPLETED_ENGINE': engine},
                                input=json.dumps(payload), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout).get('inject', {}).get('body', '') if result.stdout.strip() else ''

    def edits(self):
        return [{'name': 'Edit', 'edit_target': str(owner / self.relative)} for owner in self.owners]

    def test_two_repositories_spaces_mixed_files_config_and_failure(self):
        mixed = self.edits() + [{'name': 'Edit', 'edit_target': '.lazy-harness/planning/note.md',
                                'args_preview': str(self.owners[0] / self.relative)}]
        self.assertEqual(self.hook(mixed), '')
        for index, owner in enumerate(self.owners):
            rows = (owner / 'executed.jsonl').read_text().splitlines()
            self.assertEqual(len(rows), 1)
            self.assertEqual(json.loads(rows[0]), {'cwd': str(owner), 'root': str(owner), 'script': f'verify-{index}'})
        (self.owners[1] / 'fail-test').touch()
        failure = self.hook(self.edits())
        self.assertIn('5d-3 Affected Test Gate', failure)
        self.assertIn(str(self.owners[1]), failure)
        self.assertIn('"exitCode": 1', failure)
        self.assertIn('"repositoryRoot":', failure)
        self.assertNotIn('"scriptName": "verify-0"', failure)

    def test_ambiguous_legacy_targets_do_not_execute_guessed_repositories(self):
        joined = ' '.join(str(owner / self.relative) for owner in self.owners)
        self.assertIn('unresolved edit target', self.hook([{'name': 'Edit', 'edit_target': joined}]))
        for owner in self.owners:
            self.assertFalse((owner / 'executed.jsonl').exists())

    def test_queue_distinguishes_identical_relative_paths_and_deduplicates(self):
        for owner in self.owners:
            (owner / self.relative.replace('.ts', '.test.ts')).unlink()
        self.assertIn('5d-3 Affected Test Gate', self.hook(self.edits()))
        import xml.etree.ElementTree as ET
        questions = ET.parse(self.base / 'queue.xml').getroot().findall('question')
        self.assertEqual(len(questions), 2)
        self.assertNotEqual(questions[0].get('fingerprint'), questions[1].get('fingerprint'))
        self.assertEqual({json.loads(q.findtext('crossRef'))['repositoryRoot'] for q in questions}, set(map(str, self.owners)))
        self.assertEqual(self.hook(self.edits()), '')

    def test_relative_non_git_host_and_package_script_fallback(self):
        (self.host / '.lazy-harness/tests/test-strategy.xml').unlink()
        (self.host / 'src').mkdir()
        (self.host / 'src/local.ts').write_text('export const local = true;')
        (self.host / 'src/local.test.ts').write_text('import { test, expect } from "bun:test"; import { writeFileSync } from "node:fs"; test("local", () => { writeFileSync("local-cwd", process.cwd()); expect(true).toBe(true); });')
        (self.host / 'package.json').write_text(json.dumps({'scripts': {'test:run': 'bun test'}}))
        self.assertEqual(self.hook([{'name': 'Edit', 'edit_target': 'src/local.ts'}]), '')
        self.assertEqual((self.host / 'local-cwd').read_text(), str(self.host))

    def test_foreign_configuration_symlink_is_not_executed(self):
        strategy = self.owners[0] / '.lazy-harness/tests/test-strategy.xml'
        strategy.unlink()
        strategy.symlink_to(self.owners[1] / '.lazy-harness/tests/test-strategy.xml')
        failure = self.hook(self.edits()[:1])
        self.assertIn('Affected path escapes repository', failure)
        self.assertFalse((self.owners[0] / 'executed.jsonl').exists())

    def test_joined_source_then_record_is_explicitly_unresolved(self):
        self.assert_joined_record_source(source_first=True)

    def test_joined_record_then_source_is_explicitly_unresolved(self):
        self.assert_joined_record_source(source_first=False)

    def assert_joined_record_source(self, source_first):
        source = self.owners[0] / 'src/a.ts'
        source.write_text('export const value = true;')
        record = self.host / '.lazy-harness/planning/note.md'
        record.write_text('A genuine record.')
        parts = [str(source), str(record)] if source_first else [str(record), str(source)]
        body = self.hook([{'name': 'Edit', 'edit_target': ' '.join(parts)}])
        self.assertIn('unresolved edit target', body)
        self.assertFalse((self.base / 'queue.xml').exists())
        for owner in self.owners:
            self.assertFalse((owner / 'executed.jsonl').exists())

    def test_existing_single_record_with_source_like_name_stays_silent(self):
        for name in ['note.md', 'source.ts notes.md', 'src/quoted.ts record.md']:
            record = self.host / '.lazy-harness/planning' / name
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text('Record quoting src/a.ts, not an edit of it.')
            self.assertEqual(self.hook([{'name': 'Edit', 'edit_target': str(record)}]), '')

    def lifecycle_targets(self):
        # Include an absolute edit into the original session repository as well
        # as both foreign owners. All three are disposable, real repositories.
        self.env = {k: v for k, v in self.env.items() if not k.startswith('GIT_')}
        subprocess.run(['git', 'init', '-q', str(self.host)], env=self.env, check=True)
        (self.host / 'src').mkdir()
        for relative in [self.relative, self.relative.replace('.ts', '.test.ts'),
                         'package.json', '.lazy-harness/tests/test-strategy.xml']:
            shutil.copy2(self.owners[0] / relative, self.host / relative)
        return self.owners + [self.host]

    def test_full_sandbox_never_executes_real_absolute_owners(self):
        owners = self.lifecycle_targets()
        payload = {'recent_tool_calls': [{'name': 'Edit', 'edit_target': str(p / self.relative)} for p in owners]}
        completed = subprocess.run(['python3', str(self.host / '.lazy-harness/scripts/lifecycle-check.py'),
                                    '--root', str(self.host), '--sandbox', '--format=json'],
                                   cwd=self.host, env=self.env, input=json.dumps(payload), text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        for owner in owners:
            self.assertFalse((owner / 'executed.jsonl').exists(), str(owner))
        self.assertTrue(result['sandbox'])
        self.assertEqual(result['firstOutputHelper'], '.lazy-harness/hooks/lifecycle/helpers/check-affected-tests.sh')
        self.assertIn('not-executed: lifecycle sandbox', result['firstOutput'])
        self.assertFalse((self.base / 'queue.xml').exists())

    def test_full_compare_executes_each_owner_exactly_once_live(self):
        owners = self.lifecycle_targets()
        log = self.base / 'compare.jsonl'
        self.env['LAZY_RESPONSE_COMPLETED_COMPARE_LOG'] = str(log)
        calls = [{'name': 'Edit', 'edit_target': str(p / self.relative)} for p in owners]
        self.assertEqual(self.hook(calls, engine='compare'), '')
        for owner in owners:
            rows = (owner / 'executed.jsonl').read_text().splitlines()
            self.assertEqual(len(rows), 1, str(owner))
            self.assertEqual(json.loads(rows[0])['cwd'], str(owner))
        rows = [json.loads(row) for row in log.read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]['orchestratorSandbox'])
        self.assertEqual(rows[0]['orchestratorHelper'], '.lazy-harness/hooks/lifecycle/helpers/check-affected-tests.sh')
        self.assertTrue(rows[0]['orchestratorOutputEmitted'])
        self.assertFalse(rows[0]['legacyOutputEmitted'])
        # A deliberately non-executing shadow is not evidence of passing tests.
        self.assertFalse(rows[0]['bodyHashMatch'])

    def test_runner_failure_is_not_silent_and_matching_symlink_cannot_escape(self):
        test = self.owners[0] / self.relative.replace('.ts', '.test.ts')
        test.unlink()
        test.symlink_to(self.owners[1] / self.relative.replace('.ts', '.test.ts'))
        failure = self.hook(self.edits()[:1])
        self.assertIn('affected runner unavailable', failure)
        for owner in self.owners:
            self.assertFalse((owner / 'executed.jsonl').exists())


if __name__ == '__main__':
    unittest.main()
