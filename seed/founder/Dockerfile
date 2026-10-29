# The Founder's capsule (register E90, E91, E112). The Founder runs here and only here: never as the
# operator, never with the operator's GitHub login or Claude configuration. It holds two secrets, read at
# start from a file the operator mounts read-only: a fine-grained GitHub token that can write only the brain
# repository, and the system's own Claude login token. Its Claude configuration is fresh in every session,
# with no project or local settings, no MCP servers and no auto-memory, so nothing the Founder commits to
# the brain repository can widen its own permissions in the next session.
FROM docker.io/library/node:22-bookworm-slim@sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da AS node

FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# The same claude CLI the referee pins, by sha512 (requirements/claude-cli/package-lock.json).
COPY bootstrap/requirements/claude-cli/ /opt/claude-cli/
RUN npm ci --prefix /opt/claude-cli --no-audit --no-fund \
 && ln -s /opt/claude-cli/node_modules/.bin/claude /usr/local/bin/claude \
 && test "$(claude --version | cut -d' ' -f1)" = "$(node -p 'require("/opt/claude-cli/package.json").dependencies["@anthropic-ai/claude-code"]')"

RUN useradd --create-home --uid 10001 founder
COPY founder/entrypoint.sh /opt/founder/entrypoint.sh
COPY founder/prompt.md /opt/founder/prompt.md
RUN chmod 0555 /opt/founder/entrypoint.sh

ENV DISABLE_AUTOUPDATER=1 \
    CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
    CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 \
    CLAUDE_CODE_NO_MODEL_FALLBACK=1 \
    PYTHONDONTWRITEBYTECODE=1
USER founder
WORKDIR /work
ENTRYPOINT ["/opt/founder/entrypoint.sh"]
