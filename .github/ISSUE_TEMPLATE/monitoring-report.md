---
name: Monitoring report
about: Share a metadata-only monitoring report from macOS or Linux
---

## Collect and review

1. In Pi, run `/monitoring status --save` (no model call). Off/default installs no command;
   if monitoring is unavailable, the collector still reports absent configuration/status.
2. From the host project, run `lazy monitoring report --issue --dry-run` to preview the
   Markdown and exact target without any GitHub calls.
3. Review hostnames, catalog ids/paths and status metadata before sharing. Then run
   `lazy monitoring report --issue` to submit (default: lazy-dinosaur/lazy-harness).
   The optional `monitoring-report` label is added only when present.
4. Alternatively run `lazy monitoring report --out "$HOME/monitoring-report.md"` and
   attach the reviewed file here. Output files must be outside every Git worktree.

The collector makes zero model calls. `--issue` alone authorizes GitHub submission.
It includes tool versions, pinned revisions, allowlisted configuration/status, recent
UTC today/yesterday observe metadata and a sample summary. Saved status may be stale;
its age is reported. No saved snapshot is also useful evidence.

**Never paste or attach** `~/.pi/agent/auth.json` (or any auth.json), API keys/tokens,
environment dumps, private keys, conversation text, session transcripts, prompts,
record bodies, or unfiltered provider errors/raw logs. Credential-like patterns cause
collection to refuse the outbound report. Do not bypass that refusal.

## Expected / observed behavior

<!-- Describe the symptom without conversation text or secrets. Attach only the reviewed report. -->
