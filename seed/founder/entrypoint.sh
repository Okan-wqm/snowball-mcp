#!/bin/sh
# One Founder session inside the capsule. launch.py starts it with a read-only root and these mounts:
#   /run/secrets/founder.env  read-only: GITHUB_TOKEN (brain repo only), CLAUDE_CODE_OAUTH_TOKEN
#   /work/brain               empty tmpfs: the brain is cloned fresh every session (GitHub is its only home)
#   /work/referee             read-only: the last signed result the referee wrote about the brain
#   /work/target              read-only: the target clone (reading only; never run its code here)
#   /work/logs                this session's own transcript folder (earlier sessions are not shown: memory is the ledger)
# Environment: BRAIN_REPO (owner/name), BRAIN_SEED (the pilot's seed commit), FOUNDER_MODEL, FOUNDER_MAX_TURNS,
# FOUNDER_MAX_BUDGET_USD.
set -eu

secret() { sed -n "s/^$1=//p" /run/secrets/founder.env | head -n 1 | tr -d '\r '; }
GITHUB_TOKEN=$(secret GITHUB_TOKEN)
CLAUDE_CODE_OAUTH_TOKEN=$(secret CLAUDE_CODE_OAUTH_TOKEN)
: "${GITHUB_TOKEN:?founder.env has no GITHUB_TOKEN}"
: "${CLAUDE_CODE_OAUTH_TOKEN:?founder.env has no CLAUDE_CODE_OAUTH_TOKEN}"
export CLAUDE_CODE_OAUTH_TOKEN

# A fresh, empty Claude configuration every session: nothing carries over except what is in the brain repository.
export CLAUDE_CONFIG_DIR="$(mktemp -d)"
printf '{"mcpServers":{}}\n' > "$CLAUDE_CONFIG_DIR/no-mcp.json"

# Git as the Founder, with the brain-only token passed as a header (never on a command line or in a URL).
git config --global user.name "Snowball Founder"
git config --global user.email "founder@snowball.invalid"
git config --global init.defaultBranch main
git config --global --add safe.directory /work/target
git config --global --add safe.directory /work/brain  # the tmpfs mount point belongs to root; the clone is ours
basic=$(printf 'x-access-token:%s' "$GITHUB_TOKEN" | base64 | tr -d '\n')
git config --global http.https://github.com/.extraheader "AUTHORIZATION: basic $basic"
unset GITHUB_TOKEN basic

git clone --quiet "https://github.com/${BRAIN_REPO}.git" /work/brain
# History before the pilot's seed commit is earlier rehearsal code, not the Founder's to read (E154). Cut the
# clone there: those commits are not in the capsule at all, and pushing from a shallow clone still works.
if [ -n "${BRAIN_SEED:-}" ]; then
  git -C /work/brain merge-base --is-ancestor "$BRAIN_SEED" HEAD  # set -e: a seed the brain does not hold stops here
  printf '%s\n' "$BRAIN_SEED" > /work/brain/.git/shallow
  git -C /work/brain reflog expire --expire=now --all
  git -C /work/brain gc --quiet --prune=now
fi
before=$(git -C /work/brain rev-parse HEAD 2>/dev/null || echo none)

stamp=${SESSION_STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}
cd /work/brain
rc=0
claude -p "$(cat /opt/founder/prompt.md)" \
  --model "${FOUNDER_MODEL:-claude-opus-5-5}" \
  --max-turns "${FOUNDER_MAX_TURNS:-200}" \
  --max-budget-usd "${FOUNDER_MAX_BUDGET_USD:-50}" \
  --setting-sources "" --no-session-persistence \
  --strict-mcp-config --mcp-config "$CLAUDE_CONFIG_DIR/no-mcp.json" \
  --dangerously-skip-permissions \
  --output-format stream-json --verbose \
  > "/work/logs/session-$stamp.jsonl" 2> "/work/logs/session-$stamp.err" || rc=$?

git -C /work/brain fetch --quiet origin main 2>/dev/null || true
after=$(git -C /work/brain rev-parse origin/main 2>/dev/null || echo none)
unpushed=$(git -C /work/brain status --porcelain 2>/dev/null | wc -l)
echo "founder_session stamp=$stamp claude_exit=$rc brain_before=$before brain_after=$after uncommitted_paths=$unpushed"
exit "$rc"
