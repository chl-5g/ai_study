#!/usr/bin/env bash
set -euo pipefail
ROOT="/Users/caihaolun/ai_study"
CLONE="$ROOT/_open-agentic-push"
LOG="$ROOT/_open-agentic-push.log"
exec >"$LOG" 2>&1
echo "=== start $(date) ==="
rm -rf "$CLONE"
git clone --depth 1 https://github.com/openagentic-ai/open-agentic.git "$CLONE"
cp "$ROOT/open-agentic-README.md" "$CLONE/README.md"
cd "$CLONE"
git add README.md
git status
git commit -m "docs(README): 架构设计合并简图与项目结构" || { echo "nothing to commit?"; git diff; exit 1; }
git push origin main
echo "=== done $(date) ==="
