"""The Founder capsule's one way out (register E508). Stdlib only. The operator's code: it runs on the host side, in a
container of its own (`launch.py` `relay_argv`), never in the capsule, and the capsule never holds a copy of it.

With `launch.py --egress contained` the capsule sits on an internal Docker network with no route out
(`CAPSULE_NETWORK`). The relay is the one other member, and the only one with a route; it offers exactly two things:

  * `CONNECT` to the model's API (`MODEL_HOSTS`), for the CLI's `HTTPS_PROXY`: a TLS tunnel the relay cannot read;
  * plain HTTP under `/git/` and `/api/repos/` that forwards git smart-HTTP and GitHub REST calls of the allowed
    repositories alone, adding the GitHub token only the relay holds: the capsule never has it.

Every request is decided by `decide` (pure; the tests hold it) and written to the log as one JSON line, allowed or
denied; a denied one is never forwarded and gets a bare 403. The upstream host comes from the route, never from the
request, and a redirect is handed back, never followed. Names are compared without case, as GitHub compares them; a
path with an empty, `.` or `..` segment, an encoded `/`, `\\`, `.` or NUL, or a character outside RFC 3986's set is
refused before any route is looked at.

    python3 -I egress.py --listen 0.0.0.0:3128 --token-file /run/secrets/relay.env --repo owner/name \\
        --log /log/egress.jsonl
"""

from __future__ import annotations

import argparse
import base64
import http.client
import http.server
import json
import re
import select
import signal
import socket
import ssl
import sys
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

MODEL_HOSTS = (("api.anthropic.com", 443),)  # what CONNECT reaches; the CLI runs with nonessential traffic off
GIT_UPSTREAM = "https://github.com"
API_UPSTREAM = "https://api.github.com"
GIT_ROOT, API_ROOT = "/git/", "/api/repos/"
GIT_ENDPOINTS = (("GET", "/info/refs"), ("POST", "/git-upload-pack"), ("POST", "/git-receive-pack"))
GIT_SERVICES = ("service=git-upload-pack", "service=git-receive-pack")  # the only query /info/refs takes
API_METHODS = ("GET", "HEAD", "POST", "PATCH", "PUT", "DELETE")
REPO_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,38}/[a-z0-9._-]{1,100}")
PATH_RE = re.compile(r"/[A-Za-z0-9._~!$&'()*+,=:@/%-]*")  # RFC 3986 pchar and "/" without ";": no space, no "\"
QUERY_RE = re.compile(r"[A-Za-z0-9._~!$&'()*+,=:@/?%-]*")
ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})|%(?:2[EeFf]|5[Cc]|00)")  # a broken escape; an encoded ".", "/", "\", NUL
FORWARD_HEADERS = ("accept", "accept-encoding", "content-type", "content-encoding", "git-protocol", "user-agent",
                   "x-github-api-version", "if-none-match", "if-modified-since")  # never authorization or cookie
RETURN_HEADERS = ("content-type", "content-encoding", "content-length", "cache-control", "etag", "last-modified",
                  "link", "location", "x-github-request-id", "x-ratelimit-limit", "x-ratelimit-remaining",
                  "x-ratelimit-reset", "x-ratelimit-used", "x-ratelimit-resource")
MAX_BODY = 2 << 30  # the brain's tmpfs in the capsule
UPSTREAM_TIMEOUT_S = 300
TUNNEL_IDLE_S = 15 * 60  # a streamed model answer stays busy; a tunnel idle this long is closed
CHUNK = 64 << 10


@dataclass(frozen=True)
class Policy:
    repos: tuple[str, ...]  # owner/name, lower case
    connect: tuple[tuple[str, int], ...] = MODEL_HOSTS
    git_upstream: str = GIT_UPSTREAM
    api_upstream: str = API_UPSTREAM


@dataclass(frozen=True)
class Decision:
    allow: bool
    reason: str  # "ok", or why the request was refused
    upstream: str = ""  # scheme://host[:port] for HTTP, host:port for CONNECT
    path: str = ""  # the upstream path and query
    auth: str = ""  # "basic" (git) or "bearer" (REST)


def policy(repos, **kw) -> Policy:
    """The relay's policy for these owner/name repositories; ValueError for none or a malformed one."""
    names = []
    for repo in repos:
        name = str(repo).strip().lower()
        if not REPO_RE.fullmatch(name) or name.split("/")[1] in (".", ".."):
            raise ValueError(f"not an owner/name repository: {repo!r}")
        if name not in names:
            names.append(name)
    if not names:
        raise ValueError("no repository is allowed")
    return Policy(tuple(names), **kw)


def _deny(reason: str) -> Decision:
    return Decision(False, reason)


def decide(pol: Policy, method: str, target: str) -> Decision:
    """Whether the relay carries this request, and where to: the whole rule, before any byte goes upstream."""
    if method == "CONNECT":
        return _connect(pol, target)
    if not target.startswith("/"):
        return _deny("absolute_form")  # a proxy request for another host
    path, _, query = target.partition("?")
    if not PATH_RE.fullmatch(path) or not QUERY_RE.fullmatch(query) or ESCAPE_RE.search(path):
        return _deny("unsafe_path")
    if any(seg in ("", ".", "..") for seg in path.split("/")[1:]):
        return _deny("unsafe_path")
    low = path.lower()
    if low.startswith(GIT_ROOT):
        return _git(pol, method, path, query)
    if low.startswith(API_ROOT):
        return _api(pol, method, path, query)
    return _deny("no_route")


def _connect(pol: Policy, target: str) -> Decision:
    host, sep, port = target.rpartition(":")
    if not sep or not port.isdigit() or not host:
        return _deny("connect_target")
    if (host.lower(), int(port)) not in pol.connect:
        return _deny("connect_not_allowed")
    return Decision(True, "ok", f"{host.lower()}:{int(port)}")


def _repo_under(path: str, root: str, repos: tuple[str, ...]) -> tuple[str, str] | None:
    """The allowed repository path lies in, and the rest of path after its name; None for every other repository.
    The name must end at a "/" or at the end: an allowed name is never a prefix of another repository's."""
    low = path.lower()
    for repo in repos:
        if low.startswith(f"{root}{repo}/") or low == f"{root}{repo}":
            return repo, path[len(root) + len(repo):]
    return None


def _git(pol: Policy, method: str, path: str, query: str) -> Decision:
    segs = path.split("/")  # "", "git", owner, name[.git], ...
    if len(segs) > 3 and segs[3].lower().endswith(".git"):
        segs[3] = segs[3][:-len(".git")]
    found = _repo_under("/".join(segs), GIT_ROOT, pol.repos)
    if found is None:
        return _deny("repo_not_allowed")
    repo, rest = found
    if (method, rest) not in GIT_ENDPOINTS:
        return _deny("git_endpoint")
    if query not in (GIT_SERVICES if rest == "/info/refs" else ("",)):
        return _deny("git_endpoint")
    return Decision(True, "ok", pol.git_upstream, f"/{repo}.git{rest}" + (f"?{query}" if query else ""), "basic")


def _api(pol: Policy, method: str, path: str, query: str) -> Decision:
    if method not in API_METHODS:
        return _deny("method")
    found = _repo_under(path, API_ROOT, pol.repos)
    if found is None:
        return _deny("repo_not_allowed")
    repo, rest = found
    return Decision(True, "ok", pol.api_upstream, f"/repos/{repo}{rest}" + (f"?{query}" if query else ""), "bearer")


def auth_header(kind: str, token: str) -> str:
    if kind == "basic":  # git over HTTPS, as the open capsule's extraheader sends it
        return "Basic " + base64.b64encode(f"x-access-token:{token}".encode()).decode()
    return f"Bearer {token}"


def read_token(path: Path) -> str:
    """GITHUB_TOKEN from the relay's env file, read as the capsule's entrypoint reads its own (first line, no CR or
    space); ValueError when it is not there. The value is never printed or logged."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("GITHUB_TOKEN="):
            token = line[len("GITHUB_TOKEN="):].replace("\r", "").replace(" ", "")
            if token:
                return token
            break
    raise ValueError(f"{path} has no GITHUB_TOKEN")


class BadBody(ValueError):
    """A request body the relay will not carry: a malformed chunk, an unknown transfer coding, or too large."""


def read_body(rfile, headers, limit: int = MAX_BODY):
    """The request body as an iterator of byte chunks (None when there is none), decoded from chunked transfer or read
    to its Content-Length; BadBody past limit or for anything else. Also what the tests' fake GitHub reads with."""
    coding = (headers.get("Transfer-Encoding") or "").strip().lower()
    if coding:
        if coding != "chunked":
            raise BadBody(f"transfer coding {coding!r}")
        return _chunks(rfile, limit)
    length = headers.get("Content-Length")
    if length is None:
        return None
    if not length.strip().isdigit() or int(length) > limit:
        raise BadBody("content length")
    return _exact(rfile, int(length))


def _exact(rfile, left: int):
    while left:
        data = rfile.read(min(CHUNK, left))
        if not data:
            raise BadBody("body ended early")
        left -= len(data)
        yield data


def _chunks(rfile, limit: int):
    total = 0
    while True:
        line = rfile.readline(1024)
        size_text = line.split(b";", 1)[0].strip()
        if not line.endswith(b"\n") or not re.fullmatch(rb"[0-9A-Fa-f]{1,16}", size_text):
            raise BadBody("chunk size")
        size = int(size_text, 16)
        if size == 0:
            while rfile.readline(8192) not in (b"\r\n", b"\n", b""):
                pass  # trailers carry nothing the relay forwards
            return
        total += size
        if total > limit:
            raise BadBody("body too large")
        yield from _exact(rfile, size)
        if rfile.readline(3) not in (b"\r\n", b"\n"):
            raise BadBody("chunk end")


def _connection(upstream: str) -> http.client.HTTPConnection:
    parts = urlsplit(upstream)
    if parts.scheme == "https":
        return http.client.HTTPSConnection(parts.hostname, parts.port or 443, timeout=UPSTREAM_TIMEOUT_S,
                                           context=ssl.create_default_context())
    return http.client.HTTPConnection(parts.hostname, parts.port or 80, timeout=UPSTREAM_TIMEOUT_S)


def pump(a: socket.socket, b: socket.socket, idle_s: float = TUNNEL_IDLE_S) -> None:
    """Copy bytes both ways until both sides closed or nothing moved for idle_s."""
    open_ends = {a: b, b: a}
    while open_ends:
        ready, _, _ = select.select(list(open_ends), [], [], idle_s)
        if not ready:
            return
        for src in ready:
            try:
                data = src.recv(CHUNK)
            except OSError:
                data = b""
            dst = open_ends.get(src)
            if dst is None:
                continue
            if data:
                try:
                    dst.sendall(data)
                    continue
                except OSError:
                    return
            del open_ends[src]
            try:
                dst.shutdown(socket.SHUT_WR)
            except OSError:
                pass


class Relay(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, pol: Policy, token: str, log_path: Path) -> None:
        self.policy, self.token, self.log_path = pol, token, log_path
        self.lock = threading.Lock()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(address, Handler)

    def record(self, peer: str, method: str, target: str, decision: Decision) -> None:
        """One line per request, allowed or denied: the denied ones are the read detector. Never a header or a body."""
        row = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "peer": peer, "method": method,
               "target": target[:1024], "decision": "allow" if decision.allow else "deny", "reason": decision.reason}
        line = json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n"
        with self.lock, self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(line)


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # so a client's Expect: 100-continue is answered; every response closes
    server_version, sys_version = "relay", ""
    rbufsize = 0  # unbuffered: nothing a tunnel's client sent early can be stranded in a read buffer
    server: Relay

    def __getattr__(self, name: str):
        if name.startswith("do_"):  # every method, CONNECT and unknown ones too, is decided and recorded
            return self._dispatch
        raise AttributeError(name)

    def log_message(self, *args) -> None:
        pass  # the JSON log is the record

    def parse_request(self) -> bool:
        if super().parse_request():
            return True
        raw = (self.raw_requestline or b"")[:512].decode("latin-1").strip()
        self.server.record(self.client_address[0], "?", raw, _deny("malformed"))
        return False

    def _dispatch(self) -> None:
        self.close_connection = True
        decision = decide(self.server.policy, self.command, self.path)
        self.server.record(self.client_address[0], self.command, self.path, decision)
        if not decision.allow:
            self._answer(403, b"denied\n")
        elif self.command == "CONNECT":
            self._tunnel(decision)
        else:
            self._forward(decision)

    def _answer(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _tunnel(self, decision: Decision) -> None:
        host, _, port = decision.upstream.rpartition(":")
        try:
            upstream = socket.create_connection((host, int(port)), timeout=30)
        except OSError:
            self._answer(502, b"upstream unreachable\n")
            return
        with upstream:
            upstream.settimeout(None)
            self.send_response(200, "Connection established")
            self.end_headers()
            pump(self.connection, upstream)

    def _forward(self, decision: Decision) -> None:
        try:
            body = read_body(self.rfile, self.headers)
        except BadBody:
            self._answer(400, b"bad body\n")
            return
        headers = {k: v for k, v in self.headers.items() if k.lower() in FORWARD_HEADERS}
        headers["Authorization"] = auth_header(decision.auth, self.server.token)
        if self.headers.get("Content-Length") is not None and body is not None:
            headers["Content-Length"] = self.headers["Content-Length"]
        conn = _connection(decision.upstream)
        try:
            conn.request(self.command, decision.path, body=body, headers=headers)
            resp = conn.getresponse()
        except (OSError, http.client.HTTPException, BadBody):
            conn.close()
            self._answer(502, b"upstream failed\n")
            return
        try:
            self.send_response(resp.status, resp.reason)
            for key, value in resp.getheaders():
                if key.lower() in RETURN_HEADERS:
                    self.send_header(key, value)
            self.send_header("Connection", "close")
            self.end_headers()
            if self.command != "HEAD":
                while data := resp.read(CHUNK):
                    self.wfile.write(data)
        finally:
            conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--listen", default="0.0.0.0:3128")
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--repo", action="append", required=True, help="owner/name; repeat for more")
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        pol, token = policy(args.repo), read_token(args.token_file)
    except (OSError, ValueError) as exc:
        print(f"relay: {exc}", file=sys.stderr)
        return 2
    host, _, port = args.listen.rpartition(":")
    server = Relay((host, int(port)), pol, token, args.log)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))  # PID 1 in its container: docker stop ends it at once
    print(f"relay listening on {host}:{port} for {', '.join(pol.repos)}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
