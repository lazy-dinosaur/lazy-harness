#!/bin/bash
# Lazy-Harness weekly-snapshot hook (Principle #18)
# Triggered: manually or via cron (`0 18 * * 5` = 매주 금 18:00 KST)
# Action: rsync snapshot of .lazy-harness/ → .lazy-harness-backup/<ISO-week>/
#
# Quick install (cron):
#   crontab -e
#   0 18 * * 5 cd /home/lazydino/dev/medivance && .lazy-harness/hooks/weekly-snapshot.sh

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
LAZY="$REPO_ROOT/.lazy-harness"
BACKUP_ROOT="$REPO_ROOT/.lazy-harness-backup"
ISO_WEEK=$(date +%Y-W%V)
SNAPSHOT_DIR="$BACKUP_ROOT/$ISO_WEEK"
TIMESTAMP=$(date -Iseconds)

[ ! -d "$LAZY" ] && { echo "no .lazy-harness — abort"; exit 0; }

mkdir -p "$SNAPSHOT_DIR"

# rsync excluding logs (too noisy) and the backup dir itself
rsync -a \
    --exclude='logs/' \
    --exclude='.lazy-harness-backup/' \
    "$LAZY/" "$SNAPSHOT_DIR/"

# Save metadata
cat > "$SNAPSHOT_DIR/.snapshot-meta.json" <<JSON
{
  "timestamp": "$TIMESTAMP",
  "isoWeek": "$ISO_WEEK",
  "trigger": "${1:-manual}",
  "headSha": "$(git rev-parse HEAD 2>/dev/null || echo unknown)",
  "branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
}
JSON

# Log
LOG="$LAZY/logs/actions.jsonl"
mkdir -p "$(dirname "$LOG")"
echo "{\"timestamp\":\"$TIMESTAMP\",\"actor\":\"weekly-snapshot\",\"action\":\"backup\",\"path\":\"$SNAPSHOT_DIR\",\"trigger\":\"${1:-manual}\"}" >> "$LOG"

# Cleanup: keep last 8 weeks
cd "$BACKUP_ROOT" && ls -t | grep -E '^[0-9]{4}-W[0-9]+$' | tail -n +9 | while read OLD; do
    rm -rf "$OLD"
    echo "{\"timestamp\":\"$TIMESTAMP\",\"actor\":\"weekly-snapshot\",\"action\":\"cleanup\",\"removed\":\"$OLD\"}" >> "$LOG"
done

echo "✓ Snapshot: $SNAPSHOT_DIR"
echo "  $(du -sh "$SNAPSHOT_DIR" | cut -f1)"
exit 0
