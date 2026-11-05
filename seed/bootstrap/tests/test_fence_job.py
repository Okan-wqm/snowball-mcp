"""E532: the fence is wired. `workflow/fence.yml` judges every open pull request head into the copy's
`brain/integration` (`fence-heads`) and the referee's gate App posts `snowball-fence` on it (`fence-post`), as the tohum
pages `01a`, `01b` and `25a` 3 say; before E532 nothing posted it (independent verifier, finding 5).

The copy is a real git repository built from `test_buildfence`'s synthetic layout, GitHub a local server that answers
as GitHub does, and every request is recorded.
"""

import base64
import hashlib
import http.server
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

from snowball_bootstrap import cli

from test_buildfence import BASE, OWNER

FENCE_YML = (Path(__file__).resolve().parents[1] / "workflow" / "fence.yml").read_text(encoding="utf-8")
COPY = {"id": "copy", "repo": "owner/copy", "kind": "copy", "base_sha": "1" * 40, "identifiers": ["X"],
        "excluded_paths": [], "unit_candidates": ["plant"], "safety_paths": OWNER}


def git(repo, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false",
                           "-c", "commit.gpgsign=false", "-C", str(repo), *args],
                          capture_output=True, check=True).stdout.decode().strip()


def commit_files(repo, files, message):
    """A commit of exactly ``files`` on the checked-out branch; its SHA."""
    for path in git(repo, "ls-files").splitlines():
        if path not in files:
            git(repo, "rm", "-q", path)
    for path, text in files.items():
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_bytes(text.encode())
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


class FakeGitHub(http.server.BaseHTTPRequestHandler):
    """The copy's pull requests and the gate App's endpoints; every request is recorded."""
    pulls: list = []
    standing: dict = {}
    seen: list = []

    def log_message(self, *args):
        pass

    def reply(self, value, code=200):
        body = json.dumps(value).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        self.seen.append(("GET", url.path, dict(urllib.parse.parse_qsl(url.query)), self.headers["Authorization"],
                          None))
        if url.path == "/repos/owner/copy/pulls":
            return self.reply([{"number": n, "head": {"sha": sha}} for n, sha in self.pulls])
        if url.path == "/repos/owner/copy/installation":
            return self.reply({"id": 7})
        found = re.fullmatch(r"/repos/owner/copy/commits/([0-9a-f]{40})/check-runs", url.path)
        if found:
            return self.reply({"check_runs": self.standing.get(found.group(1), [])})
        return self.reply({"message": "Not Found"}, 404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.seen.append(("POST", self.path, {}, self.headers["Authorization"], body))
        if self.path == "/app/installations/7/access_tokens":
            return self.reply({"token": "installation-token"}, 201)
        if self.path == "/repos/owner/copy/check-runs":
            return self.reply({"id": 1}, 201)
        return self.reply({"message": "Not Found"}, 404)


class FenceJobTest(unittest.TestCase):
    """`fence-heads` judges every open head from the copy's own objects; `fence-post` posts each verdict with the gate
    App, unless the App's newest check on that head already says the same."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="e532-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        copy = self.tmp / "copy"
        copy.mkdir()
        git(copy, "init", "-q", "-b", "brain/integration")
        self.base = commit_files(copy, BASE, "base")
        edits = {1: {"plant/src/config.rs": "pub fn load() { let _ = 1; }\n"},
                 2: {"plant/src/main.rs": lambda t: t.replace("mod failsafe;", '#[path = "spare.rs"]\nmod failsafe;')},
                 3: {"plant/src/tests.rs": "\n"}}
        self.heads = {}
        for number, edit in edits.items():
            files = dict(BASE)
            for path, text in edit.items():
                files[path] = text(files[path]) if callable(text) else text
            self.heads[number] = commit_files(copy, files, f"pr {number}")
            git(copy, "update-ref", f"refs/pull/{number}/head", self.heads[number])
            git(copy, "reset", "-q", "--hard", self.base)
        # the branch moved on after the heads left it: a fenced change merged while the gate was open
        merged = dict(BASE, **{"plant/src/failsafe.rs": BASE["plant/src/failsafe.rs"] + "// reviewed\n"})
        self.tip = commit_files(copy, merged, "merged through the open gate")
        self.copy = copy
        self.root = self.tmp / "snap"
        (self.root / "setup").mkdir(parents=True)
        (self.root / "setup" / "summary.json").write_text(json.dumps({
            "seed_commit": "a" * 40, "seed_tree_sha256": "b" * 64, "targets": [COPY]}))
        FakeGitHub.pulls = [(1, self.heads[1]), (2, self.heads[2]), (3, "9" * 40)]  # 3 pushed again since the listing
        FakeGitHub.standing, FakeGitHub.seen = {}, []
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), FakeGitHub)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        patcher = mock.patch.dict(os.environ, {"GITHUB_API_URL": f"http://127.0.0.1:{self.server.server_port}",
                                               "GH_TOKEN": "job-token", "GATE_APP_ID": "42", "GATE_APP_KEY": "pem"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def prev(self, status):
        """The last signed result and its bundle, as `fetch-state` leaves them (`fence.signed_status`)."""
        raw = json.dumps({"k6": {"status": status}}).encode()
        (self.tmp / "result.json").write_bytes(raw)
        digest = base64.b64encode(hashlib.sha256(raw).digest()).decode()
        (self.tmp / "result.json.sigstore.json").write_text(json.dumps(
            {"messageSignature": {"messageDigest": {"algorithm": "SHA2_256", "digest": digest}}}))
        return str(self.tmp / "result.json")

    def heads_run(self, status="exam_strong"):
        out = self.tmp / f"cit-{status}"
        self.assertEqual(cli.main(["fence-heads", "--root", str(self.root), "--prev-result", self.prev(status),
                                   "--work", str(self.tmp / f"work-{status}"), "--out", str(out),
                                   "--remote", str(self.copy)]), 0)
        return out, json.loads((out / "fence.json").read_text())

    def test_every_open_head_is_judged_from_where_it_leaves_the_branch(self):
        # fence_heads_build_ignored build_paths_dropped fence_base_not_merge_base
        """A head that redirects the fenced module from the crate root is red; an honest one beside it is green, and
        green they both are once the signed status is live. Each is judged from its merge base: the branch's newer
        fenced commit is no change of the head's. A head pushed again since the listing waits a run."""
        _out, doc = self.heads_run()
        self.assertEqual(doc["schema"], cli.FENCE_SCHEMA)
        got = {v["pr"]: (v["head"], v["base"], v["conclusion"], v["reasons"]) for v in doc["verdicts"]}
        self.assertNotEqual(self.tip, self.base)
        self.assertEqual(got, {1: (self.heads[1], self.base, "success", []),
                               2: (self.heads[2], self.base, "failure", ["safety_path_closed:plant/src/main.rs"])})
        self.assertEqual(FakeGitHub.seen[0][:4], ("GET", "/repos/owner/copy/pulls",
                                                  {"state": "open", "base": "brain/integration", "per_page": "100",
                                                   "sort": "created", "direction": "asc"}, "Bearer job-token"))
        _out, live = self.heads_run("live")
        self.assertEqual([v["conclusion"] for v in live["verdicts"]], ["success", "success"])

    def test_the_gate_app_posts_each_verdict_that_is_not_standing(self):  # fence_post_reposts_standing
        out, _doc = self.heads_run()
        FakeGitHub.standing = {h: [{"status": "completed", "conclusion": "success"}] for h in self.heads.values()}
        FakeGitHub.seen = []
        with mock.patch.object(cli, "app_jwt", side_effect=lambda app_id, key, now: f"jwt-{app_id}-{key}"):
            self.assertEqual(cli.main(["fence-post", "--root", str(self.root), "--verdicts", str(out)]), 0)
        token = [s for s in FakeGitHub.seen if s[1] == "/app/installations/7/access_tokens"]
        self.assertEqual([(s[3], s[4]) for s in token],
                         [("Bearer jwt-42-pem", {"repositories": ["copy"], "permissions": {"checks": "write"}})])
        lookups = [s for s in FakeGitHub.seen if s[0] == "GET" and s[1].endswith("/check-runs")]
        self.assertEqual({(s[2]["check_name"], s[2]["app_id"], s[3]) for s in lookups},
                         {("snowball-fence", "42", "Bearer installation-token")})
        posted = [s[4] for s in FakeGitHub.seen if s[0] == "POST" and s[1] == "/repos/owner/copy/check-runs"]
        self.assertEqual([(b["head_sha"], b["name"], b["status"], b["conclusion"]) for b in posted],
                         [(self.heads[2], "snowball-fence", "completed", "failure")])  # 1 stands as it is
        self.assertIn("safety_path_closed:plant/src/main.rs", posted[0]["output"]["summary"])

    def test_a_verdict_fence_heads_never_writes_is_refused_before_any_call(self):  # fence_post_trusts_verdicts
        out, doc = self.heads_run()
        red = doc["verdicts"][1]
        for bad in (dict(red, conclusion="success"), dict(red, repo="owner/other"), dict(red, head="HEAD"),
                    dict(red, reasons=["x" * 301]), dict(red, pr="2")):
            with self.subTest(bad=bad):
                (out / "fence.json").write_text(json.dumps(dict(doc, verdicts=[bad])))
                FakeGitHub.seen = []
                with mock.patch.object(cli, "app_jwt", return_value="jwt"):
                    with self.assertRaisesRegex(cli.config.ConfigError, "not one fence-heads writes"):
                        cli.fence_verdicts(json.loads((out / "fence.json").read_text()), {"owner/copy"})
                    self.assertEqual(cli.main(["fence-post", "--root", str(self.root), "--verdicts", str(out)]), 2)
                self.assertEqual(FakeGitHub.seen, [])

    def test_a_head_the_fence_cannot_read_is_red(self):  # fence_unreadable_green
        with mock.patch.object(cli.gitio, "tree_reader", side_effect=cli.gitio.GitError("boom")):
            _out, doc = self.heads_run()
        self.assertEqual({v["pr"]: (v["conclusion"], v["reasons"]) for v in doc["verdicts"]},
                         {1: ("failure", ["fence_unjudged:GitError"]), 2: ("failure", ["fence_unjudged:GitError"])})


def fence_job(name):
    text = FENCE_YML.split("\njobs:\n", 1)[1]
    return re.search(rf"(?ms)^  {name}:\n(.*?)(?=^  [a-z_]+:\n|\Z)", text).group(1)


class FenceWorkflowTest(unittest.TestCase):
    """`workflow/fence.yml`: the job that reads the copy holds no secret; the one that holds the gate App's key runs
    nothing of the copy and reads `cit`'s verdicts only by their hash (`tohum/08` 1)."""

    def test_the_two_jobs_and_what_each_holds(self):  # fence_cit_holds_the_key fence_gate_without_environment
        self.assertEqual(re.findall(r"(?m)^  ([a-z_]+):$", FENCE_YML.split("\njobs:\n", 1)[1]), ["cit", "kapi"])
        self.assertIn("\npermissions: {}\n", FENCE_YML)
        cit, kapi = fence_job("cit"), fence_job("kapi")
        self.assertRegex(cit, r"(?m)^    permissions:\n      contents: read\n      actions: read\n    outputs:")
        for word in ("secrets.", "environment:", "id-token", "docker"):
            self.assertNotIn(word, cit)
        self.assertIn("    environment: gate\n    permissions: {}\n", kapi)
        for word in ("docker", "fence-heads", "fetch-deps", "run-part", "actions/checkout"):
            self.assertNotIn(word, kapi)
        used = re.findall(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}", FENCE_YML)
        self.assertEqual(used, ["GATE_APP_ID", "GATE_APP_KEY"])
        post = kapi.split("- name: The gate App posts snowball-fence", 1)[1]
        self.assertEqual(kapi.count("secrets."), post.count("secrets."))  # the post step's env alone
        self.assertIn("/tmp/sig/bin/python -m snowball_bootstrap fence-post --root snap --verdicts cit", post)

    def test_the_verdicts_are_read_by_their_hash_on_main_only(self):  # fence_verdicts_unverified
        kapi = fence_job("kapi")
        self.assertIn('echo "${{ needs.cit.outputs.cit_sha }}  cit.tar" | sha256sum -c -', kapi)
        self.assertIn('echo "${{ needs.cit.outputs.snap_sha }}  snapshot.tar" | sha256sum -c -', kapi)
        for job in (fence_job("cit"), kapi):
            self.assertIn("github.ref == 'refs/heads/main'", job.split("steps:", 1)[0])
            self.assertIn("python3 -m snowball_bootstrap control --root snap", job)
        self.assertIn("bootstrap.yml@refs/heads/main", fence_job("cit"))  # the status read from the referee's result
        self.assertRegex(fence_job("cit"), r"fence-heads --root snap\s+--prev-result state/prev/result\.json")

    def test_actions_are_pinned_and_no_context_is_expanded_in_a_script(self):
        for uses in re.findall(r"uses: (\S+)", FENCE_YML):
            self.assertRegex(uses, r"@[0-9a-f]{40}$")
        for script in re.findall(r"(?ms)^        run: [|>]\n(.*?)(?=^      - |^  [a-z_]+:\n|\Z)", FENCE_YML) + \
                re.findall(r"(?m)^        run: ([^|>\n].*)$", FENCE_YML):
            self.assertNotRegex(script, r"\$\{\{\s*(github|inputs)\.")

    def test_lines_fit(self):
        self.assertEqual([n for n, line in enumerate(FENCE_YML.splitlines(), 1) if len(line) > 120], [])


if __name__ == "__main__":
    unittest.main()
