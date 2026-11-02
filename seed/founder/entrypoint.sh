#!/bin/sh
# One Founder session inside the capsule. launch.py starts it with a read-only root and these mounts:
#   /run/secrets/founder.env  read-only: CLAUDE_CODE_OAUTH_TOKEN, and GITHUB_TOKEN (brain repo only) unless a relay
#                             carries the capsule's GitHub traffic: with RELAY set the token is the relay's alone (E508)
#   /work/brain               empty tmpfs: the brain is cloned fresh every session (GitHub is its only home)
#   /work/referee             read-only: the last signed result the referee wrote about the brain
#   /work/target              read-only: the target clone (reading only; never run its code here)
#   /work/logs                this session's own working folder (earlier sessions are not shown: memory is the ledger);
#                             the transcript there is the Founder's copy, the record is the host's (below)
# Environment: BRAIN_REPO (owner/name), BRAIN_SEED (the pilot's seed commit), FOUNDER_MODEL, FOUNDER_MAX_TURNS,
# FOUNDER_MAX_BUDGET_USD; with contained egress (E508) RELAY, the relay's URL, and HTTPS_PROXY and NO_PROXY.
set -eu
# The record of the session (E508): the CLI's stream goes to this container's stdout, which the launcher writes into a
# host folder the capsule has no mount of. fd 3 is that stdout; everything else this script prints goes to stderr.
exec 3>&1 1>&2

secret() { sed -n "s/^$1=//p" /run/secrets/founder.env | head -n 1 | tr -d '\r '; }
CLAUDE_CODE_OAUTH_TOKEN=$(secret CLAUDE_CODE_OAUTH_TOKEN)
: "${CLAUDE_CODE_OAUTH_TOKEN:?founder.env has no CLAUDE_CODE_OAUTH_TOKEN}"
export CLAUDE_CODE_OAUTH_TOKEN

# A fresh, empty Claude configuration every session: nothing carries over except what is in the brain repository.
export CLAUDE_CONFIG_DIR="$(mktemp -d)"
printf '{"mcpServers":{}}\n' > "$CLAUDE_CONFIG_DIR/no-mcp.json"

git config --global user.name "Snowball Founder"
git config --global user.email "founder@snowball.invalid"
git config --global init.defaultBranch main
git config --global --add safe.directory /work/target
git config --global --add safe.directory /work/brain  # the tmpfs mount point belongs to root; the clone is ours
if [ -n "${RELAY:-}" ]; then
  # Contained egress (E508): no route out. Git reaches GitHub through the relay, which adds the token it alone holds
  # and carries the allowed repositories only; https://github.com/ URLs keep working, rewritten to it.
  if [ -n "$(secret GITHUB_TOKEN)" ]; then
    echo "founder.env holds GITHUB_TOKEN: with a relay the GitHub token is the relay's alone (E508)" >&2
    exit 64
  fi
  git config --global url."$RELAY/git/".insteadOf "https://github.com/"
else
  # Open egress: the brain-only token passed as a header (never on a command line or in a URL).
  GITHUB_TOKEN=$(secret GITHUB_TOKEN)
  : "${GITHUB_TOKEN:?founder.env has no GITHUB_TOKEN}"
  basic=$(printf 'x-access-token:%s' "$GITHUB_TOKEN" | base64 | tr -d '\n')
  git config --global http.https://github.com/.extraheader "AUTHORIZATION: basic $basic"
  unset GITHUB_TOKEN basic
fi

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
# The brain's own agent and skill definitions (E450): agents/ and skills/ of the clone's HEAD, read from git's objects
# and checked here, become this session's plugin `brain` (and nothing else of the brain any configuration); what loaded
# and what was skipped, and why, is /work/logs/brain-definitions.json. A broken definition never stops the session.
python3 /opt/founder/brain_defs.py /work/brain "$CLAUDE_CONFIG_DIR/brain-plugin" /work/logs/brain-definitions.json \
  || echo "brain definitions: the loader exited $?, the session starts without them" >&2
cd /work/brain
# Every default tool but six (E380, E508): RemoteTrigger is the one whose effect can outlive the capsule (a routine in
# the cloud); the Cron tools die with this process and were never used; WebFetch and WebSearch reach the web around
# the capsule's network (a search is served from outside, and its snippets can quote any public repository). Nothing
# else is narrowed. The stream goes to fd 3, the host's record, through tee, which keeps the Founder's copy in
# /work/logs; the CLI's exit code comes back on fd 4, and neither fd is left open to the CLI.
rc=$( { { code=0
claude -p "$(cat /opt/founder/prompt.md)" \
  --model "${FOUNDER_MODEL:-claude-opus-5-5}" \
  --max-turns "${FOUNDER_MAX_TURNS:-200}" \
  --max-budget-usd "${FOUNDER_MAX_BUDGET_USD:-50}" \
  --setting-sources "" --no-session-persistence \
  --strict-mcp-config --mcp-config "$CLAUDE_CONFIG_DIR/no-mcp.json" \
  --plugin-dir "$CLAUDE_CONFIG_DIR/brain-plugin" \
  --disallowedTools "RemoteTrigger,CronCreate,CronDelete,CronList,WebFetch,WebSearch" \
  --dangerously-skip-permissions \
  --output-format stream-json --verbose \
  2> "/work/logs/session-$stamp.err" 3>&- 4>&- || code=$?
echo "$code" >&4; } | tee "/work/logs/session-$stamp.jsonl" >&3 4>&-; } 4>&1 ) || true  # tee's status, not the CLI's
rc=${rc:-1}
git -C /work/brain fetch --quiet origin main 2>/dev/null || true
after=$(git -C /work/brain rev-parse origin/main 2>/dev/null || echo none)
unpushed=$(git -C /work/brain status --porcelain 2>/dev/null | wc -l)
echo "founder_session stamp=$stamp claude_exit=$rc brain_before=$before brain_after=$after uncommitted_paths=$unpushed"
exit "$rc"
