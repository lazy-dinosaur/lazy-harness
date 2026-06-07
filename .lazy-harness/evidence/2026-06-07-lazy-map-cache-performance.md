# Evidence: Lazy Map generated cache performance

## Scope

This evidence capsule records the performance and behavior validation for optimizing repeated `lazy map` query usage with a generated `.lazy-harness/generated/record-index.json` cache.

In scope:

- `lazy map --overview` and `lazy map <term-or-file>` cache behavior.
- `--fresh` source-rebuild escape hatch behavior.
- Benchmark comparison between cached query-map and source rebuild.
- Validation that the optimization remains cue-only and does not make the CLI semantic authority.

Out of scope:

- Product app performance.
- Browser/UI rendering time.
- LLM thinking time, downstream tool scheduling latency, and shell startup outside the measured CLI subprocess.
- Generated cache canonicality; generated files remain non-canonical.

## Environment

- Date: 2026-06-07
- Source root: `/home/lazydino/dev/lazy-harness`
- Branch: `feature/map-first-record-navigation`
- Base commit before this performance work: `7ffcb25 Record iterative downstream validation evidence`
- Runtime: local shell invoking `.lazy-harness/bin/lazy` and Bun-backed TypeScript CLIs.
- Cache file: `.lazy-harness/generated/record-index.json`
- Cache refresh command run before benchmark:

```bash
.lazy-harness/bin/lazy record-index --write --format=md
```

## Commands

Mandatory overview/query evidence before implementation:

```bash
.lazy-harness/bin/lazy map --overview --format=md --limit=20
.lazy-harness/bin/lazy map 'lazy map cache performance benchmark evidence record-index fast path' --format=md --limit=8
.lazy-harness/bin/lazy map 'record-index generated cache --fresh source rebuild query speed self-test' --format=md --limit=8
.lazy-harness/bin/lazy map 'evidence capsule performance measurements reproduce retention privacy' --format=md --limit=8
```

Cache refresh:

```bash
.lazy-harness/bin/lazy record-index --write --format=md
```

Cache behavior smoke:

```bash
.lazy-harness/bin/lazy map --overview --format=json --limit=3 >/tmp/cache-overview2.json
.lazy-harness/bin/lazy map 'record map' --format=json --limit=3 >/tmp/cache-query2.json
.lazy-harness/bin/lazy map 'record map' --format=json --limit=3 --fresh >/tmp/fresh-query2.json
python3 - <<'PY'
import json
for p in ['/tmp/cache-overview2.json','/tmp/cache-query2.json','/tmp/fresh-query2.json']:
    obj=json.load(open(p))
    print(p, obj['mode'], obj['source']['recordIndexCache'])
assert json.load(open('/tmp/cache-query2.json'))['source']['recordIndexCache']['used'] is True
assert json.load(open('/tmp/fresh-query2.json'))['source']['recordIndexCache']['used'] is False
PY
```

Benchmark:

```bash
python3 - <<'PY'
import subprocess, time, statistics, json
cmds={
 'overview-cache':['.lazy-harness/bin/lazy','map','--overview','--format=json','--limit=20'],
 'query-cache':['.lazy-harness/bin/lazy','map','record map','--format=json','--limit=8'],
 'query-fresh':['.lazy-harness/bin/lazy','map','record map','--format=json','--limit=8','--fresh'],
 'record-index':['.lazy-harness/bin/lazy','record-index','--format=json'],
}
summary={}
for name,cmd in cmds.items():
    times=[]
    for _ in range(9):
        t=time.perf_counter()
        p=subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        times.append(time.perf_counter()-t)
        if p.returncode:
            raise SystemExit(p.stderr)
    summary[name]={'medianSeconds':round(statistics.median(times),3),'times':[round(x,3) for x in times]}
print(json.dumps(summary, indent=2))
assert summary['query-cache']['medianSeconds'] < summary['query-fresh']['medianSeconds']
PY
```

## Results

Cache behavior smoke after refresh:

```text
/tmp/cache-overview2.json record-map.overview {'path': '.lazy-harness/generated/record-index.json', 'used': True, 'reason': 'fresh generated cache'}
/tmp/cache-query2.json record-map.inspect {'path': '.lazy-harness/generated/record-index.json', 'used': True, 'reason': 'fresh generated cache'}
/tmp/fresh-query2.json record-map.inspect {'path': '.lazy-harness/generated/record-index.json', 'used': False, 'reason': '--fresh requested source rebuild'}
```

Benchmark result:

```json
{
  "overview-cache": {
    "medianSeconds": 0.035,
    "times": [0.031, 0.032, 0.056, 0.044, 0.035, 0.04, 0.05, 0.032, 0.035]
  },
  "query-cache": {
    "medianSeconds": 0.055,
    "times": [0.046, 0.055, 0.048, 0.055, 0.064, 0.051, 0.05, 0.057, 0.064]
  },
  "query-fresh": {
    "medianSeconds": 0.177,
    "times": [0.17, 0.169, 0.158, 0.161, 0.179, 0.177, 0.185, 0.181, 0.205]
  },
  "record-index": {
    "medianSeconds": 0.156,
    "times": [0.241, 0.17, 0.156, 0.159, 0.162, 0.146, 0.14, 0.144, 0.138]
  }
}
```

Derived comparison:

- Cached query-map median: `0.055s`
- `--fresh` source rebuild query-map median: `0.177s`
- Approximate speedup for repeated token query-map when cache is fresh: `3.2x`
- Cached overview median: `0.035s`
- Full record-index rebuild median: `0.156s`

Implementation behavior added:

- `lazy map` now uses `.lazy-harness/generated/record-index.json` only when it is fresher than canonical inputs.
- Missing, stale, invalid, or unreadable cache triggers source rebuild.
- `--fresh` / `--no-cache` forces source rebuild.
- JSON and Markdown output expose `source.recordIndexCache` / `record-index cache` status.

Self-test coverage added:

- Missing cache path rebuilds.
- Cache is used after `lazy record-index --write`.
- `--fresh` bypasses cache.

## Interpretation

The optimization is useful because the user-confirmed retrieval flow requires repeated query-map calls across multiple candidate tokens/files/layers. With a fresh generated cache, repeated `lazy map <term-or-file>` calls avoid rebuilding the record index each time and are substantially faster in this host.

The optimization does not change semantic boundaries:

- `record-index.json` remains a generated cache, not canonical truth.
- `lazy map` output remains cue-only and does not satisfy search/read debt by itself.
- Real record/source/test reads remain required before answering or mutating.

Known caveats:

- The first query after records/graph/project metadata changes may rebuild if the generated cache is stale.
- To regain the fastest path after record changes, run `.lazy-harness/bin/lazy record-index --write --format=md`.
- Measurements are local-process timings and do not include LLM/tool orchestration or UI rendering.

Confidence: high for local CLI speedup with a fresh cache; medium for exact speedup factor across machines/hosts.

## Reproduce

1. From `/home/lazydino/dev/lazy-harness`, refresh the generated cache:

   ```bash
   .lazy-harness/bin/lazy record-index --write --format=md
   ```

2. Run the cache smoke commands in `## Commands`.
3. Run the benchmark script in `## Commands`.
4. Confirm cached `.lazy-harness/bin/lazy map 'record map' --format=json --limit=8` median is below `.lazy-harness/bin/lazy map 'record map' --format=json --limit=8 --fresh` median.
5. Run source validation:

   ```bash
   .lazy-harness/bin/lazy test
   ```

## Related records

- `.lazy-harness/spec/platform/record-index-header.md`
- `.lazy-harness/tests/record-index-header.md`
- `.lazy-harness/generated/README.md`
- `.lazy-harness/planning/searchable-record-context-retrieval-tasks.md`
- `.lazy-harness/scripts/record-map.ts`
- `.lazy-harness/scripts/record-index.ts`
- Graph ids:
  - `kg_record_map_cache_fast_path`
  - `kg_record_map_cache_fast_path_self_test`

## Retention / privacy

This capsule contains only local benchmark timings, commands, file paths, and generated-cache status. It does not include secrets, credentials, personal data, raw transcripts, raw assistant responses, or product data. Transient benchmark output files under `/tmp` can be discarded after this evidence is committed.
