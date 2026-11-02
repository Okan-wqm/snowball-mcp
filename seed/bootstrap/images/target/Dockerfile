# The target toolchain image (register E513, plan D8): node, npm and cargo, so the referee can run the target's own
# tests and the rival's reproducers of a defect in target code. Both bases are pinned by digest (the tags are for the
# reader; the digest is what is pulled). Nothing here is target-specific: the target's dependencies are fetched per
# tree by `snowball_bootstrap.target_run` (`npm ci --ignore-scripts`, `cargo vendor --locked`, nothing executed) and
# mounted read-only into a run with no network.
#
# The Rust toolchain is reached through `/opt/rust/bin`, the toolchain's own directory, and the rustup proxies are
# left off PATH: a `rust-toolchain.toml` in the tree under test then cannot switch the compiler or make rustup reach
# the network for a component or a target. The referee's toolchain is the one named here; a tree that names another
# is reported by `target_run.toolchain_drift`, never followed.
#
# Build (operator, once per change of this file; the pushed digest goes into the referee's operator config):
#   docker build -t <registry>/snowball-target:<tag> seed/bootstrap/images/target
FROM docker.io/library/node:22.23.4-bookworm-slim@sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da \
  AS node

FROM docker.io/library/rust:1.88.0-slim-bookworm@sha256:38bc5a86d998772d4aec2348656ed21438d20fcdce2795b56ca434cf21430d89
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
 && ln -s "$(rustc --print sysroot)" /opt/rust \
 && rustc --version > /opt/rust-version \
 && node --version && npm --version && /opt/rust/bin/cargo --version

ENV PATH=/opt/rust/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    HOME=/tmp \
    CARGO_HOME=/tmp/cargo-home \
    CARGO_TARGET_DIR=/tmp/target \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_AUDIT=false
