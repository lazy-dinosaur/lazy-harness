# Future Plan — Portable Reports and Knowledge Normalization

Date: 2026-05-12
Branch: `experimental/lazy-harness`
Status: future plan, not current implementation scope

## 1. User intent

When `lazy-harness` is extracted into its own repository, host projects such as `dev/medivance` still need a way to feed real usage results back into the framework repository.

The desired workflow:

```text
host project uses lazy-harness
→ lazy-harness records outcomes, questions, validations, and gaps
→ host project exports a portable report
→ report is pasted or imported into the framework repo
→ framework maintainers can immediately understand what happened
→ framework improvements are planned from real usage evidence
```

This report must answer:

- Did the framework behave as intended?
- Did DDD/SDD/BDD/TDD/ADR recording happen when required?
- Did missing information become structured questions instead of silent assumptions?
- Did repo-native test routing work?
- Which validations passed or failed?
- Which framework gaps appeared repeatedly?
- What should be improved next?

## 2. Current decision

Do **not** build a DB/RAG system now.

Instead, build a small portable report feature first, with a JSON shape that can later be ingested by DB/RAG without redesign.

```text
Now:
  lazy:report → Markdown + JSON portable report

Later:
  same JSON contract → DB / RAG / vector index / analytics ingest
```

## 3. Recommended near-term feature

Add a framework-owned command after extraction or when report work starts:

```bash
bun run lazy:report
```

Suggested outputs:

```text
.lazy-harness/reports/latest.md
.lazy-harness/reports/latest.json
.lazy-harness/reports/host-report-YYYYMMDD-HHMMSS.md
.lazy-harness/reports/host-report-YYYYMMDD-HHMMSS.json
```

The Markdown file is for humans and copy/paste into the framework repo.
The JSON file is the stable future ingestion contract.

## 4. Report content contract

A useful v1 report should include:

1. Host project identity
   - project name
   - worktree path
   - git branch
   - commit range
   - lazy-harness version/commit if known

2. Activity summary
   - recent actions from `logs/actions.jsonl`
   - recent decisions from `logs/decisions.jsonl`
   - recent validations from `logs/validations.jsonl`

3. Layer impact summary
   - DDD touched or missing
   - SDD touched or missing
   - BDD touched or missing
   - TDD touched or missing
   - ADR touched or missing

4. Structured questions
   - open questions
   - answered questions
   - selected options
   - effects
   - deferred decisions

5. Validation evidence
   - affected runner results
   - actual run commands
   - target tests
   - lint/typecheck/pre-commit/pre-push results
   - warnings or environment issues

6. Framework findings
   - gaps
   - conflicts
   - missing information
   - drift
   - unclear/ambiguous cases
   - proposed framework improvements

7. Copy/paste section
   - short executive summary
   - exact commands/results
   - recommended next framework tasks

## 5. Normalization direction

Keep original human-readable SSOT files separated:

```text
.lazy-harness/domain/      DDD source
.lazy-harness/spec/        SDD source
.lazy-harness/behavior/    BDD source
.lazy-harness/tests/       TDD source
.lazy-harness/decisions/   ADR source
```

Do not merge these into one manually maintained source file. That would create drift.

Instead, report/knowledge commands may generate normalized records from those sources:

```ts
type KnowledgeLayer = 'ddd' | 'sdd' | 'bdd' | 'tdd' | 'adr'

type KnowledgeStatus =
  | 'draft'
  | 'active'
  | 'deprecated'
  | 'conflict'
  | 'missing'

interface KnowledgeRecord {
  id: string
  layer: KnowledgeLayer
  kind: string
  title: string
  summary: string
  sourcePath: string
  sourceAnchor?: string
  status: KnowledgeStatus
  tags: string[]
  confidence: 'low' | 'medium' | 'high'
  links: KnowledgeLink[]
}

interface KnowledgeLink {
  relation:
    | 'defines'
    | 'implements'
    | 'tests'
    | 'decides'
    | 'depends-on'
    | 'conflicts-with'
    | 'supersedes'
  targetId: string
  targetLayer?: KnowledgeLayer
}
```

The generated JSON can later become:

```text
knowledge_records table
knowledge_links table
knowledge_tags table
RAG chunks with layer/source metadata
```

## 6. Future DB/RAG plan

Only after report v1 proves useful:

1. Stabilize report JSON schema.
2. Add `knowledge/index.json` generation.
3. Add schema validation.
4. Add optional export adapters:
   - JSONL
   - SQLite
   - vector/RAG chunk JSONL
5. Add query helpers, for example:
   - Which BDD scenarios are untested?
   - Which ADRs decided this SDD contract?
   - Which DDD terms appear in code but not in domain records?
   - Which host reports repeatedly mention the same framework gap?

## 7. Non-goals for now

Do not implement yet:

- SQLite storage
- vector database
- embeddings
- RAG retrieval server
- schema migrations
- full document parser for every XML/Markdown detail

The next concrete step is only the portable report command.

## 8. Placement in roadmap

Recommended order:

1. Standalone extraction.
2. Project Init Interview.
3. Portable `lazy:report`.
4. Report schema stabilization.
5. Optional knowledge normalization/index.
6. Optional DB/RAG ingestion.
