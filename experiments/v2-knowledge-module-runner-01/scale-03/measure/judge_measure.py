"""Inert public adapter for inherited chunked coverage/contradiction scoring.

No CLI parsing, private data loading, credential lookup or paid HTTP on import.
Live judging is unavailable. Explicit synthetic fixtures inject their verdicts;
these scores prove mapping mechanics only, not a real model's correctness.
"""
import collections
import re
from pathlib import Path

JEV_CAP = 6000
CHUNK = 6000


def chunks(text):
    out, cur = [], ''
    for line in text.splitlines(keepends=True):
        if cur and len(cur) + len(line) > CHUNK:
            out.append(cur)
            cur = ''
        cur += line
    return out + ([cur] if cur else [])


def main(*, fixture=None, run_prefix='raw-r'):
    if not isinstance(fixture, dict) or fixture.get('synthetic') is not True:
        raise RuntimeError('live judging unavailable; explicit synthetic fixture required')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', run_prefix):
        raise ValueError('run prefix must be a plain directory-name prefix')
    root = Path(fixture['root'])
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('symlink fixture root denied')
    root = root.resolve(strict=True)
    qs, flat, verdict, ask = (fixture[k] for k in ('questions', 'claims', 'verdicts', 'ask'))
    unique = {x for q in qs for x in q['nuggets']}
    if not unique <= set(verdict) or not unique <= set(flat):
        raise ValueError('missing fixture claims/verdicts')
    recs, calls = [], 0
    for run in (1, 2, 3):
        for q in qs:
            if not q['qid'].isalnum():
                raise ValueError('plain fixture question IDs required')
            path = root / f'{run_prefix}{run}' / f"{q['qid']}.md"
            if any(p.is_symlink() for p in (path, path.parent)):
                raise ValueError('symlink fixture brief denied')
            if not path.exists():
                continue
            per = []
            for part in chunks(path.read_text()):
                if calls >= JEV_CAP:
                    raise RuntimeError('jev cap')
                calls += 1
                # Explicit fixture seam: never a provider/auth/HTTP implementation.
                answers = ask(q, part, [flat[n] for n in q['nuggets']])
                if len(answers) != len(q['nuggets']):
                    raise ValueError('incomplete fixture answer')
                per.append(answers)
            if not per:
                continue
            for i, nugget in enumerate(q['nuggets']):
                recs.append({'run': run, 'qid': q['qid'], 'nugget': nugget,
                             'verdict': verdict[nugget],
                             'covered': max(x[i][0] for x in per),
                             'contradicted': max(x[i][1] for x in per)})
    first12 = {q['qid'] for q in qs[:12]}

    def summary(select):
        out = {}
        for run in (1, 2, 3):
            rows = [r for r in recs if r['run'] == run and select(r)]
            if rows:
                out[run] = {'cov': round(sum(r['covered'] >= .7 for r in rows) / len(rows), 3),
                            'contra': sum(r['contradicted'] >= .7 for r in rows), 'n': len(rows)}
        covs = [v['cov'] for v in out.values()]
        return {'runs': out, 'mean': round(sum(covs) / len(covs), 3) if covs else None,
                'range': [min(covs), max(covs)] if covs else None}

    return {'synthetic': True, 'records': recs, 'key': dict(collections.Counter(verdict[n] for n in unique)),
            'occurrences_superseded': sum(verdict[n] == 'superseded' for q in qs for n in q['nuggets']),
            'original_70': summary(lambda r: True),
            'corrected_70': summary(lambda r: r['verdict'] != 'superseded'),
            'original_12': summary(lambda r: r['qid'] in first12),
            'corrected_12': summary(lambda r: r['qid'] in first12 and r['verdict'] != 'superseded'),
            'fixture_requests': calls}


if __name__ == '__main__':
    raise SystemExit(main())
