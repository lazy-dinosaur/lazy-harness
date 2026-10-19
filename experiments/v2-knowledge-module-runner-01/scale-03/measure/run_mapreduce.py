"""Public fixture adapter for inherited G14 map/reduce measurement mechanics.

Original live orchestration used private inputs and automatic estimated charges.
That path is deliberately unavailable here. Synthetic receipts are NOT billing.
No configuration, provider, database, model or credential module is imported.
"""
import json
import math
import os
from pathlib import Path

LUNA_CAP = 3.0
ESTIMATE_PER_QUESTION = 0.012


def _cost(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
        raise RuntimeError('unknown Luna cost: owner must reconcile before continuing')
    return value


def read_ledger(path):
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    pending, completed, spent = set(), {}, 0.0
    for row in rows:
        key = row['run'], row['qid']
        if row['status'] == 'started':
            pending.add(key)
        elif row['status'] == 'reconciled':
            spent += _cost(row['writer_cost_usd'])
            pending.discard(key)
        elif row['status'] == 'done':
            spent += _cost(row.get('writer_cost_usd'))
            pending.discard(key)
            completed[key] = row
        else:
            pending.add(key)
    if pending:
        raise RuntimeError(f'uncertain paid calls: owner must reconcile, no automatic retry: {sorted(pending)}')
    return spent, completed


def estimate_run(todo_count, completed):
    observed = [_cost(row['writer_cost_usd']) for row in completed.values()]
    unit = max(ESTIMATE_PER_QUESTION, sum(observed) / len(observed) if observed else 0.0)
    return unit * todo_count


def main(*, fixture=None):
    """Only explicit synthetic adapters; never discovers private configuration/data.

    fixture = {synthetic: True, root: empty scratch Path, questions: list,
               writer: callable(question)->{brief, writer_cost_usd}}.
    Cost is test input, not provider usage or a financial receipt.
    """
    if not isinstance(fixture, dict) or fixture.get('synthetic') is not True:
        raise RuntimeError('live measurement unavailable; explicit synthetic fixture required')
    root = Path(fixture['root'])
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('symlink fixture root denied')
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError('fixture directory required')
    qs, writer = fixture['questions'], fixture['writer']
    if len(qs) != 70 or len({q['qid'] for q in qs}) != 70:
        raise ValueError('70 distinct synthetic questions required')
    if any(not q['qid'].isalnum() for q in qs):
        raise ValueError('plain synthetic question IDs required')
    ledger = root / 'synthetic-brief-ledger.jsonl'
    if ledger.is_symlink():
        raise ValueError('symlink fixture ledger denied')
    spent, completed = read_ledger(ledger)

    def record(row):
        with ledger.open('a') as stream:
            stream.write(json.dumps({**row, 'synthetic': True}, ensure_ascii=False) + '\n')
            stream.flush()
            os.fsync(stream.fileno())

    for run in (1, 2, 3):
        raw = root / f'raw-mr{run}'
        if raw.is_symlink():
            raise ValueError('symlink fixture output denied')
        raw.mkdir(exist_ok=True)
        todo = []
        for q in qs:
            path = raw / f"{q['qid']}.md"
            if path.is_symlink():
                raise ValueError('symlink fixture brief denied')
            if path.exists() != ((run, q['qid']) in completed):
                raise RuntimeError('raw/ledger mismatch; owner must reconcile')
            if not path.exists():
                todo.append(q)
        if spent + estimate_run(len(todo), completed) > LUNA_CAP:
            return 2
        for q in todo:
            if spent + estimate_run(1, completed) > LUNA_CAP:
                return 2
            identity = {'run': run, 'qid': q['qid']}
            record({**identity, 'status': 'started'})
            try:
                out = writer(q)
                cost = _cost(out.get('writer_cost_usd'))
                (raw / f"{q['qid']}.md").write_text(out['brief'])
                row = {**identity, 'status': 'done', 'writer_cost_usd': cost}
                record(row)
                completed[run, q['qid']] = row
                spent += cost
            except Exception:
                record({**identity, 'status': 'uncertain'})
                # No automatic charge, release, reconciliation or next call.
                raise
            if spent > LUNA_CAP:
                return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
