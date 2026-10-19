"""G14 acceptance ledger, standalone: python3 test_brief_mapreduce_offline.py.
No pytest/conftest, database imports, subprocesses, network, or model calls.
"""
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent


def deny(*args, **kwargs):
    raise AssertionError('offline test attempted transport/process')


# Guard before importing the implementation; inject only the collection seam.
socket.socket.connect = deny
socket.socket.connect_ex = deny
socket.create_connection = deny
socket.getaddrinfo = deny
subprocess.Popen = deny
fake_worker = types.ModuleType('worker_tools')
fake_worker.collect_wide = deny
spec = importlib.util.spec_from_file_location('brief_under_test', ROOT / 'brief.py')
brief = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {'worker_tools': fake_worker}):
    spec.loader.exec_module(brief)


def document(areas=('A', 'B', 'C', 'D'), per_view=1):
    head = '# 모은 지식: task\n\n영역 목록: ' + ', '.join(areas) + '\n\n'
    lines = [head]
    for view in range(4):
        lines.append(f'## view{view}\n\n')
        for area in areas:
            lines.append(f'### 영역 {area}\n')
            for n in range(per_view):
                lines.append(f'- [{area}-{view}-{n}@1] 조건=값; Identifier/path; ' + '한' * 20 + '\n')
            lines.append('\n')
    return ''.join(lines)


class BriefMapReduceOffline(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def invoke(self, doc, runner):
        with patch.object(fake_worker, 'collect_wide', return_value=(doc, {'collected': 16, 'relevant': 4})), \
                patch.object(brief.time, 'time', side_effect=[10, 11, 12]):
            return brief.brief('unused', 'host', ' task ', ['query'], deny, change=' change ', runner=runner)

    def test_flag_off_identical_prompt_path_document_and_dict(self):
        doc = document()
        # Invalid new options are ignored completely when off.
        os.environ.update(LH_BRIEF_PART_CHARS='bad', LH_BRIEF_PARALLEL='bad')
        seen = []
        def runner(prompt, cwd):
            path = Path(cwd) / 'knowledge.md'
            seen.append(path)
            expected = brief._prompt().replace('{QUESTION}', 'task').replace('{FILE}', str(path)).replace('{CHANGE}', '하려는 변경: change')
            self.assertEqual(prompt, expected)
            self.assertEqual(path.read_bytes(), doc.encode())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
            return 'answer', {'usage': {'cost_usd': .25}}
        out = self.invoke(doc, runner)
        self.assertEqual(out, {'brief': 'answer', 'collected': 16, 'relevant': 4, 'collected_chars': len(doc),
                               'brief_chars': 6, 'writer_cost_usd': .25, 'collect_sec': 1, 'write_sec': 1})
        self.assertFalse(seen[0].parent.exists())

    def test_area_packing_across_four_views(self):
        doc = document()
        parts = brief.split_by_area(doc, 900)
        self.assertEqual(len(parts), 2)  # two whole areas fit in each part
        for part in parts:
            self.assertLessEqual(len(part), 900)
            self.assertTrue(part.startswith(doc.split('## ')[0]))
        for area in 'ABCD':
            owners = [part for part in parts if f'[{area}-0-0@1]' in part]
            self.assertEqual(len(owners), 1)
            for view in range(4):
                self.assertIn(f'[{area}-{view}-0@1]', owners[0])

    def test_oversized_area_split_only_at_line_boundaries(self):
        doc = document(('A',), per_view=8)
        parts = brief.split_by_area(doc, 350)
        self.assertGreater(len(parts), 1)
        expected = [line for line in doc.splitlines() if line.startswith('- ')]
        actual = [line for part in parts for line in part.splitlines() if line.startswith('- ')]
        self.assertEqual(actual, expected)
        for part in parts:
            self.assertLessEqual(len(part), 350)
            self.assertIn('영역 목록: A\n', part)
            self.assertIn('### 영역 A\n', part)
        with self.assertRaisesRegex(ValueError, 'fragment line'):
            brief.split_by_area(doc, 60)
        with self.assertRaises(ValueError):
            brief.split_by_area(doc, 0)

    def test_short_collection_uses_legacy_single_call(self):
        os.environ['LH_BRIEF_MAPREDUCE'] = '1'
        doc = document(('A',))
        calls = []
        def runner(prompt, cwd):
            calls.append(prompt)
            self.assertNotIn('MAP 단계', prompt)
            self.assertNotIn('REDUCE 단계', prompt)
            self.assertEqual((Path(cwd) / 'knowledge.md').read_text(), doc)
            return 'short', .02
        out = self.invoke(doc, runner)
        self.assertEqual(len(calls), 1)
        self.assertEqual(out['map_parts'], 1)
        self.assertEqual(out['map_cost_usd'], 0)
        self.assertEqual(out['reduce_cost_usd'], 0)
        self.assertEqual(out['writer_cost_usd'], .02)
        self.assertEqual(brief.split_by_area(doc, len(doc)), [doc])

    def test_parallel_maps_reduce_all_notes_cost_and_cleanup(self):
        os.environ.update(LH_BRIEF_MAPREDUCE='1', LH_BRIEF_PART_CHARS='500', LH_BRIEF_PARALLEL='2')
        barrier = threading.Barrier(2)
        lock = threading.Lock()
        active = peak = 0
        calls, paths = [], []
        def runner(prompt, cwd):
            nonlocal active, peak
            path = Path(prompt.split('파일: ')[1].split('\n')[0])
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(Path(cwd).stat().st_mode & 0o777, 0o700)
            with lock:
                paths.append(path)
                calls.append(path.name)
            if path.name.startswith('part-'):
                self.assertNotIn('8,000', prompt)
                self.assertIn('MAP 단계', prompt)
                with lock:
                    active += 1
                    peak = max(peak, active)
                barrier.wait(timeout=5)
                with lock:
                    active -= 1
                index = int(path.stem.split('-')[1])
                return f'partial-{index} [alias-{index}]', {'usage': {'cost_usd': index / 100}}
            self.assertEqual(path.name, 'partials.md')
            self.assertIn(brief.LIMIT_RULE, prompt)
            self.assertIn('REDUCE 단계', prompt)
            self.assertIn('기능별로 분리', prompt)
            self.assertEqual(path.read_text(), '\n\n'.join(f'# 부분 정리 {i}\npartial-{i} [alias-{i}]' for i in range(1, 5)))
            return 'final', .05
        out = self.invoke(document(), runner)
        self.assertEqual(out['map_parts'], 4)
        self.assertEqual(len(calls), 5)
        self.assertEqual(peak, 2)
        self.assertAlmostEqual(out['map_cost_usd'], .10)
        self.assertAlmostEqual(out['reduce_cost_usd'], .05)
        self.assertAlmostEqual(out['writer_cost_usd'], .15)
        self.assertTrue(all(not path.parent.exists() for path in paths))

    def test_map_failure_raises_and_never_reduces(self):
        os.environ.update(LH_BRIEF_MAPREDUCE='1', LH_BRIEF_PART_CHARS='500')
        paths = []
        def runner(prompt, cwd):
            paths.append(Path(cwd))
            self.assertNotIn('REDUCE 단계', prompt)
            if 'part-2.md' in prompt:
                raise RuntimeError('map failed')
            return 'partial', .01
        with self.assertRaisesRegex(RuntimeError, 'map failed'):
            self.invoke(document(), runner)
        self.assertTrue(paths)
        self.assertTrue(all(not p.exists() for p in paths))

    def test_reduce_failure_and_single_failure_cleanup(self):
        for enabled in ('0', '1'):
            with self.subTest(enabled=enabled):
                os.environ.update(LH_BRIEF_MAPREDUCE=enabled, LH_BRIEF_PART_CHARS='500')
                paths = []
                def runner(prompt, cwd):
                    paths.append(Path(cwd))
                    if 'MAP 단계' in prompt:
                        return 'partial', .01
                    raise RuntimeError('final failed')
                with self.assertRaisesRegex(RuntimeError, 'final failed'):
                    self.invoke(document(), runner)
                self.assertTrue(all(not p.exists() for p in paths))

    def test_unknown_cost_is_not_zero_and_reduce_limit_can_be_disabled(self):
        os.environ.update(LH_BRIEF_MAPREDUCE='1', LH_BRIEF_PART_CHARS='500', LH_BRIEF_LIMIT='0')
        def runner(prompt, cwd):
            self.assertNotIn('8,000', prompt)
            return ('partial', None) if 'MAP 단계' in prompt else ('final', .01)
        out = self.invoke(document(), runner)
        self.assertIsNone(out['map_cost_usd'])
        self.assertIsNone(out['writer_cost_usd'])
        self.assertEqual(out['reduce_cost_usd'], .01)


class MeasurementOffline(unittest.TestCase):
    def test_estimate_and_ledger_resume_fail_closed(self):
        module = runpy.run_path(str(ROOT / 'scale-03/measure/run_mapreduce.py'))
        self.assertEqual(module['LUNA_CAP'], 3)
        self.assertAlmostEqual(module['estimate_run'](70, {}), .84)
        self.assertEqual(module['estimate_run'](2, {(1, 'q'): {'writer_cost_usd': .03}}), .06)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'ledger.jsonl'
            self.assertEqual(module['read_ledger'](path), (0, {}))
            started = {'run': 1, 'qid': 'q', 'status': 'started'}
            path.write_text(json.dumps(started) + '\n')
            with self.assertRaisesRegex(RuntimeError, 'uncertain paid'):
                module['read_ledger'](path)
            done = {**started, 'status': 'done', 'writer_cost_usd': .03}
            path.write_text(json.dumps(started) + '\n' + json.dumps(done) + '\n')
            spent, completed = module['read_ledger'](path)
            self.assertEqual(spent, .03)
            self.assertIn((1, 'q'), completed)
            path.write_text(json.dumps({**done, 'writer_cost_usd': None}) + '\n')
            with self.assertRaisesRegex(RuntimeError, 'unknown Luna cost'):
                module['read_ledger'](path)

    def test_generation_70_questions_three_runs_and_cap_before_next_run(self):
        module = runpy.run_path(str(ROOT / 'scale-03/measure/run_mapreduce.py'))
        with self.assertRaisesRegex(RuntimeError, 'synthetic fixture'):
            module['main']()
        for cost, expected_calls, expected_status in ((.001, 210, 0), (.02, 140, 2)):
            with self.subTest(cost=cost), tempfile.TemporaryDirectory() as temp:
                calls = []
                def writer(q):
                    calls.append(q)
                    return {'brief': 'synthetic answer', 'writer_cost_usd': cost}
                fixture = {'synthetic': True, 'root': Path(temp), 'writer': writer,
                           'questions': [{'qid': f'Q{i}', 'question': f'question{i}'} for i in range(70)]}
                self.assertEqual(module['main'](fixture=fixture), expected_status)
                self.assertEqual(module['main'](fixture=fixture), expected_status)
                self.assertEqual(len(calls), expected_calls)
                spent, completed = module['read_ledger'](Path(temp) / 'synthetic-brief-ledger.jsonl')
                self.assertAlmostEqual(spent, expected_calls * cost)
                self.assertEqual(len(completed), expected_calls)

    def test_failure_never_fabricates_charge_or_continues(self):
        module = runpy.run_path(str(ROOT / 'scale-03/measure/run_mapreduce.py'))
        for cost in (None, -1, True, float('nan'), float('inf')):
            with self.subTest(cost=cost), tempfile.TemporaryDirectory() as temp:
                calls = []
                fixture = {'synthetic': True, 'root': Path(temp),
                           'questions': [{'qid': f'Q{i}'} for i in range(70)],
                           'writer': lambda q: calls.append(q) or {'brief': 'x', 'writer_cost_usd': cost}}
                with self.assertRaisesRegex(RuntimeError, 'unknown Luna cost'):
                    module['main'](fixture=fixture)
                with self.assertRaisesRegex(RuntimeError, 'uncertain paid'):
                    module['main'](fixture=fixture)
                self.assertEqual(len(calls), 1)
                rows = [json.loads(x) for x in (Path(temp) / 'synthetic-brief-ledger.jsonl').read_text().splitlines()]
                self.assertEqual([r['status'] for r in rows], ['started', 'uncertain'])
                self.assertTrue(all('writer_cost_usd' not in r for r in rows))

    def test_judge_default_and_custom_prefix_with_explicit_fixture(self):
        module = runpy.run_path(str(ROOT / 'scale-03/measure/judge_measure.py'))
        with self.assertRaisesRegex(RuntimeError, 'synthetic fixture'):
            module['main']()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for run in (1, 2, 3):
                for prefix in ('raw-r', 'raw-mr'):
                    raw = root / f'{prefix}{run}'
                    raw.mkdir()
                    (raw / 'Q.md').write_text('synthetic fact')
            fixture = {'synthetic': True, 'root': root,
                       'questions': [{'qid': 'Q', 'question': 'task', 'nuggets': ['R:1', 'R:2']}],
                       'claims': {'R:1': 'fact', 'R:2': 'old fact'},
                       'verdicts': {'R:1': 'still_valid', 'R:2': 'superseded'},
                       'ask': lambda q, answer, claims: [(1, 0), (0, 1)]}
            for prefix in ('raw-r', 'raw-mr'):
                result = module['main'](fixture=fixture, run_prefix=prefix)
                self.assertEqual(result['corrected_70']['mean'], 1)
                self.assertEqual(result['original_70']['mean'], .5)
                self.assertEqual(result['fixture_requests'], 3)
                self.assertEqual(len(result['records']), 6)
                self.assertTrue(result['synthetic'])
            with self.assertRaises(ValueError):
                module['main'](fixture=fixture, run_prefix='../escape')
            (root / 'raw-r1/Q.md').unlink()
            (root / 'raw-r1/Q.md').symlink_to(root / 'raw-mr1/Q.md')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                module['main'](fixture=fixture)


if __name__ == '__main__':
    unittest.main(verbosity=2)
