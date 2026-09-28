import unittest
from pathlib import Path

import policy
import runner
import store
from test_runner import ModuleTests


class PolicyTests(unittest.TestCase):
    def test_each_rule_and_fallback(self):
        base = dict(completion=True, conflict=False, combined="record", review_reasons=[],
                    operation="add", kind="fact", evidence_source="code_test", can_ask_now=False)
        cases = [
            ({"completion": False}, "P01", "hold"),
            ({"conflict": True}, "P02", "queue_for_human"),
            ({"combined": "duplicate_skip"}, "P03", "reject"),
            ({"combined": "no_record"}, "P04", "retain_as_evidence"),
            ({"combined": "needs_review", "review_reasons": ["impact: reference_only (policy pending)"]}, "P05", "retain_as_evidence"),
            ({"combined": "needs_review", "can_ask_now": True}, "P06", "ask_now"),
            ({"combined": "needs_review"}, "P07", "queue_for_human"),
            ({"kind": "decision", "evidence_source": "user_tentative", "can_ask_now": True}, "P08", "ask_now"),
            ({"kind": "decision", "evidence_source": "user_tentative"}, "P09", "queue_for_human"),
            ({}, "P10", "absorb"),
            ({"combined": "unknown"}, None, "hold"),
            ({"combined": "needs_review", "review_reasons": ["impact: reference_only (policy pending)", "other"]}, "P07", "queue_for_human"),
            ({"kind": "decision", "evidence_source": "user_confirmed"}, "P10", "absorb"),
            ({"kind": "fact", "evidence_source": "observed_output"}, "P10", "absorb"),
            ({"kind": "decision", "evidence_source": "observed_output"}, "P09", "queue_for_human"),
        ]
        for overrides, rule_id, action in cases:
            with self.subTest(overrides=overrides):
                self.assertEqual({"rule_id": rule_id, "action": action}, policy.evaluate({**base, **overrides}))

    def test_utterance_fixture(self):
        evidence = Path('/home/lazydino/dev/lazy-harness/.lazy-harness/evidence/jev-utterance-status-15-result.json')
        probabilities = runner.load(evidence)['probabilities']
        for case, expected in [('C1', 'user_confirmed'), ('C7', 'user_tentative'),
                               ('T1', 'user_tentative'), ('B1', 'user_tentative')]:
            with self.subTest(case=case):
                self.assertEqual(expected, policy.apply_utterance_status('user_confirmed', {'probabilities': probabilities[case]}))
        self.assertEqual('official_doc', policy.apply_utterance_status('official_doc', {'probabilities': probabilities['T1']}))
        self.assertEqual('user_confirmed', policy.apply_utterance_status(
            'user_confirmed', {'probabilities': {'confirmed_decision': 1.0}}))

    def test_fact_lint_and_fragment_shape(self):
        fact = {'operation': 'add', 'fact': 'exact word', 'kind': 'fact', 'evidence_source': 'code_test',
                'subject': 'exact word', 'evidence_quote': 'quote', 'keywords': ['word', 'quote']}
        self.assertTrue(runner.lint_fact(fact)['ok'])
        for change, code in [({'kind': 'bad'}, 'E_KIND'), ({'evidence_source': 'bad'}, 'E_SOURCE'),
                             ({'keywords': ['missing']}, 'E_KEYWORD')]:
            self.assertIn(code, {e['code'] for e in runner.lint_fact({**fact, **change})['errors']})
        entry = {'host_id': 'host', 'partition_key': 'domain', 'judgement_id': 'j1', 'entry_id': 'e1',
                 'work_unit_id': 'w1', 'judgement_body': {'facts': [fact]}}
        fragment = store.build_fragment(entry, 0, fact['keywords'], ['r1'], '2026-01-01', 2)
        self.assertEqual({'id', 'host_id', 'workspace_id', 'alias', 'domain', 'seq', 'text', 'keywords',
                          'kind', 'group_id', 'revision', 'active', 'confidence', 'source',
                          'valid_from', 'superseded_at'}, set(fragment))
        self.assertEqual('j1:0', fragment['group_id'])
        self.assertIn('E_GROUP', {e['code'] for e in runner.lint_fact({**fact, 'group': ' '})['errors']})
        fact['group'] = 'decision-a'
        self.assertEqual('j1:decision-a', store.build_fragment(entry, 0, fact['keywords'], ['r1'], '2026-01-01', 2)['group_id'])
        self.assertEqual(('domain-2', 'exact word', 'confirmed'),
                         (fragment['alias'], fragment['text'], fragment['confidence']))
        fact['text'] = 'different'
        with self.assertRaises(ValueError):
            store.build_fragment(entry, 0, [], [], '2026-01-01', 3)


class PolicyDigestTests(unittest.TestCase):
    setUp = ModuleTests.setUp
    register = ModuleTests.register
    fixture = ModuleTests.fixture
    def test_add_and_unconfirmed_decision(self):
        entry = self.register(operation='add', target=None, fact='new')
        path = self.root / 'ledger_entry' / (entry['entry_id'] + '.json')
        row = store.read(path)
        row['judgement_body']['facts'][0].update(kind='fact', evidence_source='user_confirmed', keywords=['new'],
            evidence_refs=[{'type': 'user_utterance', 'locator': 'test/local', 'quote': '좋아 그렇게 하자'}])
        store.write(path, row)
        fixture = self.fixture('update')
        fixture['packet']['template_id'] = 'record-need'
        fixture['packet']['state'] = {'narrative': 'synthetic', 'candidate_fact': 'new',
                                     'evidence_quote': 'new', 'existing_records_excerpt': ''}
        fixture['answers'] = {'is_new': {'type': 'noul', 'noul': .95},
                              'durability': {'type': 'choice', 'choice': 'durable_fact',
                                             'probabilities': {'durable_fact': .97, 'none_or_uncertain': .03}},
                              'should_record': {'type': 'noul', 'noul': .9}}
        fixture['packet']['questions'] = {k: {'type': v['type'], 'instructions': 'Select value',
            'criteria': {'true': None, 'false': None} if v['type'] == 'noul' else
                        {name: None for name in v['probabilities']}}
            for k, v in fixture['answers'].items()}
        self.assertEqual('provisional', store.batch(self.root, 1, {entry['entry_id']: [fixture]})[0]['state'])
        store.complete(self.root, 'unit')
        receipt = store.rows(self.root, 'check_receipt')[0]
        self.assertEqual('absorbed', store.digest(self.root, 'unit', True, {receipt['receipt_id']: fixture})['status'])
        fragment = next(f for f in store.rows(self.root, 'fragments') if f.get('id'))
        self.assertEqual(('new', 'confirmed'), (fragment['text'], fragment['confidence']))
        self.assertEqual('P10', store.rows(self.root, 'absorption')[0]['rule_id'])

        decision = self.register(operation='add', target=None, unit='unit2', fact='new decision')
        path = self.root / 'ledger_entry' / (decision['entry_id'] + '.json')
        row = store.read(path)
        row['judgement_body']['facts'][0].update(kind='decision', evidence_source='ai_inference', why='synthetic reason',
            evidence_refs=[{'type': 'ai_inference', 'locator': 'test/a', 'quote': 'new decision'},
                           {'type': 'official_doc', 'locator': 'test/b', 'quote': 'new decision'}])
        store.write(path, row)
        fixture['packet']['state']['candidate_fact'] = 'new decision'
        fixture['packet']['state']['evidence_quote'] = 'new decision'
        self.assertEqual('provisional', store.batch(self.root, 1, {decision['entry_id']: [fixture]})[0]['state'])
        store.complete(self.root, 'unit2')
        receipt = next(r for r in store.rows(self.root, 'check_receipt') if r['entry_id'] == decision['entry_id'])
        store.digest(self.root, 'unit2', True, {receipt['receipt_id']: fixture})
        self.assertEqual(1, len(store.rows(self.root, 'confirmation_queue')))
        self.assertEqual(1, len([f for f in store.rows(self.root, 'fragments') if f.get('id')]))
        self.assertEqual('P09', next(a for a in store.rows(self.root, 'absorption')
                                     if a['entry_id'] == decision['entry_id'])['rule_id'])
