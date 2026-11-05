"""The operator's `drill-fixtures` command (E499; `tohum/26f` "Canlı prova fikstürleri", `25a` 7, E544): the live
revert-drill fixtures of one import, checked against every rule of `26f`, each cause measured with the toy's own tools,
written to the operator's path alone.

Every git repository is a local one made here; the sandbox is a fake that answers from the plant's bytes, except in
`DockerIntegrationTest`, which runs the real `DockerSandbox` only when docker is there and ``SNOWBALL_DRILL_DOCKER=1``
asks for it (the suite runs under every mutant, and its install step needs the network). The trailing comment on a test
names the mutants it kills (`local/mutate.py`).
"""

import base64
import hashlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from snowball_bootstrap import canon, cli, drillfixtures as df, importer
from snowball_bootstrap.config import ConfigError
from snowball_bootstrap.drillfixtures import FixtureStop, Measurement

ZERO = "0" * 64
TOY = {
    "README.md": b"# textkit\n",
    "textkit/.nvmrc": b"22.23.4\n",
    "textkit/package.json": json.dumps({"name": "textkit", "version": "1.0.0", "private": True, "type": "module",
                                        "scripts": {"lint": "node lint.mjs", "test": "node --test"}}).encode() + b"\n",
    "textkit/package-lock.json": json.dumps({"name": "textkit", "version": "1.0.0", "lockfileVersion": 3,
                                             "requires": True,
                                             "packages": {"": {"name": "textkit", "version": "1.0.0"}}}).encode()
    + b"\n",
    # The toy's own lint tool here: ESLint's JSON report, one error for each `var `, exit 0.
    "textkit/lint.mjs": (b'import { readdirSync, readFileSync } from "node:fs";\n'
                         b'const report = readdirSync("src").filter((f) => f.endsWith(".js")).map((f) => ({\n'
                         b'  filePath: f, warningCount: 0,\n'
                         b'  errorCount: (readFileSync(`src/${f}`, "utf8").match(/\\bvar /g) || []).length }));\n'
                         b"process.stdout.write(JSON.stringify(report));\n"),
    "textkit/src/greet.js": b'export function greet(name) {\n  return "Hello, " + name + "!";\n}\n',
    "textkit/src/slug.js": (b"export function slugify(text) {\n  const lower = text.toLowerCase();\n"
                            b'  return lower.trim().replace(/[^a-z0-9]+/g, "-");\n}\n'),
    "textkit/src/stats.js": (b"export function total(values) {\n  var sum = 0;\n  for (const v of values) {\n"
                             b"    sum = sum + v;\n  }\n  return sum;\n}\n"),
    "textkit/src/permissions.js": b"export function canEdit(user) {\n  return user.editor === true;\n}\n",
    "textkit/test/greet.test.js": (b'import { test } from "node:test";\nimport assert from "node:assert/strict";\n'
                                   b'import { greet } from "../src/greet.js";\n\n'
                                   b'test("greet", () => {\n  assert.equal(greet("Ada"), "Hello, Ada!");\n});\n'),
    "textkit/test/slug.test.js": (b'import { test } from "node:test";\nimport assert from "node:assert/strict";\n'
                                  b'import { slugify } from "../src/slug.js";\n\n'
                                  b'test("slug", () => {\n  assert.equal(slugify("A b"), "a-b");\n});\n'),
}
GREET, SLUG, STATS, PERM = "textkit/src/greet.js", "textkit/src/slug.js", "textkit/src/stats.js", \
    "textkit/src/permissions.js"
KEYWORDS = ["auth", "guard", "security", "session", "token", "secret", "crypto", "tenant", "permission", "role",
            "policy", "payment", "billing", "pii"]
BASE = Measurement("v22.23.4", True, 1, True)


def git(repo, *args, data=None):
    return subprocess.run(["git", "-c", "core.autocrlf=false", *args], cwd=repo, input=data, capture_output=True,
                          check=True).stdout


def repo_of(path: Path, files: dict[str, bytes]) -> Path:
    """A repository whose ``main`` holds ``files`` exactly (bytes, LF as given)."""
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    for key, value in (("core.autocrlf", "false"), ("user.email", "t@example.invalid"), ("user.name", "t")):
        git(path, "config", key, value)
    commit_files(path, files)
    return path


def commit_files(path: Path, files: dict[str, bytes | None], message: str = "c") -> str:
    for rel, content in files.items():
        target = path / rel
        if content is None:
            target.unlink()
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    git(path, "add", "-A")
    git(path, "commit", "-q", "--allow-empty", "-m", message)
    return git(path, "rev-parse", "HEAD").decode().strip()


def chained(rows):
    out, prev = [], ZERO
    for row in rows:
        row = dict(row, prev_hash=prev)
        row["row_hash"] = canon.row_hash(row)
        prev = row["row_hash"]
        out.append(json.dumps(row, separators=(",", ":")).encode("utf-8"))
    return out


def patch_of(repo: Path, rel: str, new: bytes) -> str:
    """The operator's draft as git writes it: ``rel`` changed to ``new`` in ``repo``'s tree, then put back."""
    old = (repo / rel).read_bytes()
    (repo / rel).write_bytes(new)
    try:
        return git(repo, "diff", "--no-color", "--no-ext-diff", "--", rel).decode("utf-8")
    finally:
        (repo / rel).write_bytes(old)


class FakeSandbox:
    """Answers from the bytes of the one file a plant changed (``answers``: new bytes -> measurement); the clean tree
    gets ``base``. ``during`` runs inside each plant's measurement."""

    def __init__(self, answers=None, base=BASE, during=None):
        self.answers, self.base, self.during = answers or {}, base, during
        self.trees, self.closed, self.readied = [], False, False

    def ready(self):
        self.readied = True

    def measure(self, tree, plan):
        self.trees.append(tree)
        changed = [content for rel, (content, _x) in tree.items() if TOY.get(rel) != content]
        if not changed:
            return self.base
        if self.during:
            self.during()
        return self.answers[changed[0]]

    def close(self):
        self.closed = True


class Fixture(unittest.TestCase):
    """A referee checkout after a Stage 0 import, the toy clone, the brain, a catalog of three drafts (one a cause)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dfx-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.toy = repo_of(self.tmp / "toy", TOY)
        brain_files = {f"{importer.TOY_DIR}/{rel}": content for rel, content in TOY.items()}
        brain_files.update({
            "candidates/toy/good/expect.json": b'{"decision": "merge"}\n',
            "candidates/toy/good/diff.patch": patch_of(self.toy, STATS, TOY[STATS].replace(b"var sum", b"let sum"))
            .encode(),
            "candidates/toy/bad-test/expect.json": b'{"decision": "reject", "reason": "tests_red"}\n',
            "candidates/toy/bad-test/diff.patch": patch_of(self.toy, GREET, TOY[GREET].replace(b"Hello", b"Bye"))
            .encode(),
            "referee/ledger/chain.py": b"x = 1\n"})
        self.brain = repo_of(self.tmp / "brain", brain_files)
        self.brain_sha = git(self.brain, "rev-parse", "HEAD").decode().strip()
        self.toy_hash = importer.part_hash(self.toy, "refs/heads/main", importer.TOY_DIR, forbid_operator_names=False,
                                           fold_case=True)
        self.referee = repo_of(self.tmp / "referee", {
            "ledger/chain.py": b"x = 1\n",
            "policy.json": json.dumps({"constitutional": {"security_keywords": KEYWORDS}}).encode(),
            "setup/summary.json": json.dumps(self.summary()).encode()})
        self.import_rows()
        self.private = self.tmp / "private"
        self.private.mkdir()
        self.out = self.private / "fixtures.b64"
        self.drafts = {"build_break": patch_of(self.toy, GREET, TOY[GREET] + b"export function broken( {\n"),
                       "lint_regression": patch_of(self.toy, SLUG, TOY[SLUG].replace(b"const lower", b"var lower")),
                       "test_regression": patch_of(self.toy, GREET, TOY[GREET].replace(b"Hello", b"Hi"))}
        self.answers = {TOY[GREET] + b"export function broken( {\n": Measurement("v22.23.4", False, 2, False),
                        TOY[SLUG].replace(b"const lower", b"var lower"): Measurement("v22.23.4", True, 2, True),
                        TOY[GREET].replace(b"Hello", b"Hi"): Measurement("v22.23.4", True, 1, False)}

    @staticmethod
    def summary(**toy):
        return {"seed_commit": "a" * 40, "seed_tree_sha256": "b" * 64, "targets": [
            dict({"id": "toy", "repo": "o/toy", "kind": "toy", "base_sha": None, "identifiers": [],
                  "excluded_paths": [], "unit_candidates": ["textkit"]}, **toy),
            {"id": "copy", "repo": "o/copy", "kind": "copy", "base_sha": "c" * 40, "identifiers": ["X"],
             "excluded_paths": [], "unit_candidates": ["a"]}]}

    def import_rows(self, **over):
        """The counter: a touch row, then the transfer (its referee tree the checkout's), ``over`` set on it."""
        referee_tree = importer.committed_referee_hash(self.referee, "HEAD")
        transfer = dict({"ts": "2026-11-04T08:00:00Z", "stage": 0, "brain_sha": self.brain_sha,
                         "referee_tree_sha256": referee_tree, "result_sha256": "e" * 64,
                         "toy_tree_sha256": self.toy_hash}, **over)
        lines = chained([{"ts": "2026-11-03T08:00:00Z", "touch": "kill_switch"}, transfer])
        commit_files(self.referee, {"setup/imports.jsonl": b"".join(line + b"\n" for line in lines)})
        self.line = lines[-1]

    def catalog(self, entries=None):
        entries = entries if entries is not None else [{"cause": c, "patch": p} for c, p in self.drafts.items()]
        path = self.private / f"catalog-{len(list(self.private.iterdir()))}.json"
        path.write_text(json.dumps(entries), encoding="utf-8")
        return path

    def produce(self, catalog=None, sandbox=None, out=None, toy_ref="refs/heads/main"):
        self.sandbox = sandbox or FakeSandbox(self.answers)
        return df.produce(self.referee, self.toy, toy_ref, self.brain, catalog or self.catalog(), out or self.out,
                          self.sandbox)

    def refused(self, says, **kw):
        with self.assertRaises(FixtureStop) as caught:
            self.produce(**kw)
        self.assertIn(says, str(caught.exception))
        self.assertFalse(self.out.exists(), "a refusal wrote the value")
        return str(caught.exception)


class ProduceTest(Fixture):
    def test_one_base64_line_of_the_canonical_set_of_the_last_transfer(self):  # drill_fixtures_ids_from_cause
        """E499 (`26f`): one line of base64 (no LF) of the RFC 8785 JSON; the import line's sha256 is its bytes
        without the LF; the ids are 32 fresh lowercase hex characters, distinct, in the order the instances are."""
        done = self.produce()
        value = self.out.read_bytes()
        self.assertNotIn(b"\n", value)
        data = json.loads(base64.b64decode(value, validate=True))
        self.assertEqual(canon.canonical(data), base64.b64decode(value))
        self.assertEqual(set(data), {"import_line_sha256", "instances"})
        self.assertEqual(data["import_line_sha256"], hashlib.sha256(self.line).hexdigest())
        ids = [i["id"] for i in data["instances"]]
        self.assertTrue(all(len(i) == 32 and set(i) <= set("0123456789abcdef") for i in ids))
        self.assertEqual(ids, sorted(set(ids)))
        self.assertEqual(sorted((i["cause"], i["patch"]) for i in data["instances"]), sorted(self.drafts.items()))
        self.assertTrue(all(set(i) == {"id", "cause", "patch"} for i in data["instances"]))
        self.assertEqual(done, {"causes": {c: 1 for c in df.CAUSES}, "instances": 3,
                                "value_sha256": hashlib.sha256(value).hexdigest(), "value_bytes": len(value)})
        self.assertTrue(self.sandbox.readied and self.sandbox.closed)
        self.assertEqual(len(self.sandbox.trees), 4)  # the base once, then each plant
        again = self.tmp / "private" / "again.b64"
        self.produce(out=again)
        other = [i["id"] for i in json.loads(base64.b64decode(again.read_bytes()))["instances"]]
        self.assertFalse(set(ids) & set(other), "the ids are not fresh")

    def test_the_cli_prints_counts_the_sha256_and_the_size_and_never_a_patch_or_an_id(self):
        """E499: only the counts, the value's sha256 and its size reach the terminal."""
        fake = FakeSandbox(self.answers)
        with mock.patch.object(df, "DockerSandbox", lambda image: fake), \
                mock.patch("sys.stderr", new_callable=io.StringIO) as err, \
                mock.patch("sys.stdout", new_callable=io.StringIO) as printed:
            code = cli.main(["drill-fixtures", "--referee", str(self.referee), "--toy", str(self.toy), "--toy-ref",
                             "refs/heads/main", "--brain", str(self.brain), "--catalog", str(self.catalog()),
                             "--out", str(self.out), "--node-image", "node:22@sha256:" + "a" * 64])
        self.assertEqual(code, 0)
        text = printed.getvalue() + err.getvalue()
        data = json.loads(base64.b64decode(self.out.read_bytes()))
        self.assertNotIn(self.out.read_bytes().decode("ascii"), text)  # the value itself: it is base64 of the rest
        for instance in data["instances"]:
            self.assertNotIn(instance["id"], text)
            for secret in (instance["id"], instance["patch"]):  # base64 at each of its three alignments
                for pad in ("", " ", "  "):
                    encoded = base64.b64encode((pad + secret).encode()).decode()
                    self.assertNotIn(encoded[8:40], text)
        for secret in ("broken(", "var lower", "Hi,", "@@", "src/"):
            self.assertNotIn(secret, text)
        self.assertIn(hashlib.sha256(self.out.read_bytes()).hexdigest(), text)

    def test_an_existing_out_is_never_written_over(self):  # drill_fixtures_out_overwritten
        """E499: a set is written once; a path already there, or one that appears while the plants are measured, is
        left exactly as it was."""
        self.out.write_bytes(b"old")
        with self.assertRaises(FixtureStop) as caught:
            self.produce()
        self.assertIn("there already", str(caught.exception))
        self.assertEqual(self.out.read_bytes(), b"old")
        self.out.unlink()
        with self.assertRaises(FixtureStop) as caught:
            self.produce(sandbox=FakeSandbox(self.answers, during=lambda: self.out.write_bytes(b"meanwhile")))
        self.assertIn("appeared", str(caught.exception))
        self.assertEqual(self.out.read_bytes(), b"meanwhile")

    def test_the_value_and_the_drafts_stay_outside_every_repository(self):
        """E499 (`26f`: never a file of a repository): an out path or a catalog inside a git work tree is refused."""
        self.refused("inside the git repository", out=self.referee / "fixtures.b64")
        inside = self.toy / "drafts.json"
        inside.write_text(json.dumps([]), encoding="utf-8")
        self.refused("inside the git repository", catalog=inside)

    def test_an_out_without_its_directory_is_refused_before_anything_is_measured(self):  # drill_fixtures_out_dir_late
        """E499: the value has a private directory to go to before the toy's tools run."""
        missing = self.private / "no-such-dir" / "fixtures.b64"
        with self.assertRaises(FixtureStop) as caught:
            self.produce(out=missing)
        self.assertIn("directory is not there", str(caught.exception))
        self.assertFalse(self.sandbox.readied or self.sandbox.trees)

    def test_without_docker_the_command_stops_and_writes_nothing(self):  # drill_fixtures_docker_skipped
        """E499: the measurement is never skipped: no docker, no value."""
        self.refused("docker is not available",
                     sandbox=df.DockerSandbox("node:22@sha256:" + "a" * 64, docker="no-such-docker-e499"))
        failing = df.DockerSandbox("node:22@sha256:" + "a" * 64,
                                   run=lambda *a, **k: subprocess.CompletedProcess(a, 1, b"", b""))
        self.refused("docker is not available", sandbox=failing)
        self.refused("must name its digest", sandbox=df.DockerSandbox("node:22.23.4-bookworm-slim"))


class BindingRefusedTest(Fixture):
    def test_a_toy_that_is_not_the_lines_toy_tree_is_refused(self):  # drill_fixtures_toy_tree_unchecked
        """E499 (`26f`: the patch applies to that import's toy tree, `toy_tree_sha256`)."""
        commit_files(self.toy, {"README.md": b"# moved\n"})
        self.refused("not the tree the last transfer line names")

    def test_a_checkout_that_is_not_the_lines_referee_is_refused(self):  # drill_fixtures_line_unbound
        """E499: the line binds the set only when the checkout's commit holds the referee tree it names (E471)."""
        commit_files(self.referee, {"ledger/chain.py": b"x = 2\n"})
        with self.assertRaises(ConfigError) as caught:  # stage-open's own refusal (E471), the same rule
            self.produce()
        self.assertIn("referee_tree_sha256", str(caught.exception))
        self.assertFalse(self.out.exists())

    def test_a_last_transfer_without_a_toy_tree_is_refused(self):
        """E499: a batch transfer writes no toy; the set is bound to a transfer that did."""
        self.import_rows(toy_tree_sha256=None)
        self.refused("names no toy tree")

    def test_a_brain_whose_toy_fixture_is_another_tree_is_refused(self):
        """E499: the candidates read are the ones beside the line's toy tree."""
        moved = commit_files(self.brain, {f"{importer.TOY_DIR}/README.md": b"# other\n"})
        self.import_rows(brain_sha=moved)
        self.refused("is not the toy tree the line names")


class DraftRefusedTest(Fixture):
    def test_a_cause_outside_29js_three_is_refused(self):
        """E499 (`26f`): test_regression, build_break or lint_regression."""
        self.refused("its cause is not one of", catalog=self.catalog([{"cause": "impact_miss",
                                                                       "patch": self.drafts["build_break"]}]))

    def test_unequal_cause_counts_or_a_missing_cause_are_refused(self):  # drill_fixtures_counts_unchecked
        """E499 (`26f`: each cause the same count, at least one)."""
        extra = patch_of(self.toy, SLUG, TOY[SLUG].replace(b'"-"', b'"_"'))
        entries = [{"cause": c, "patch": p} for c, p in self.drafts.items()]
        self.refused("the same number of instances", catalog=self.catalog(entries + [
            {"cause": "test_regression", "patch": extra}]))
        self.refused("the same number of instances", catalog=self.catalog(entries[1:]))

    def test_a_file_on_a_security_path_is_refused(self):  # drill_fixtures_security_path_unchecked safety_paths_dropped
        """E499 (`26f`, `14`, `29k`): a lower-case keyword of policy.json in the lower-case path; the toy target's
        safety_paths too (`05`)."""
        perm = patch_of(self.toy, PERM, TOY[PERM].replace(b"=== true", b"!== true"))
        self.refused("on a security path", catalog=self.catalog([{"cause": "test_regression", "patch": perm}]))
        commit_files(self.referee, {"setup/summary.json": json.dumps(self.summary(safety_paths=["textkit/src/slug.js"]))
                                    .encode()})
        self.import_rows()
        self.refused("on a security path", catalog=self.catalog([{"cause": "lint_regression",
                                                                  "patch": self.drafts["lint_regression"]}]))

    def test_the_security_rule_folds_the_case_of_the_keyword_and_of_the_path(self):
        # drill_fixtures_keyword_case_folded drill_fixtures_path_case_folded
        """E499 (`14`, `29k` `security_keyword_substring`): the keyword and the path compared in lower case, so a
        mixed-case keyword of policy.json (`SLUG`) holds a lower-case path and a lower-case keyword a mixed-case one."""
        from types import SimpleNamespace
        bind = df.Binding("a" * 64, "b" * 64, "c" * 40, ("slug",), SimpleNamespace(safety_paths=()))
        self.assertTrue(df._on_security_path("textkit/src/Slug.js", bind))
        self.assertFalse(df._on_security_path("textkit/src/greet.js", bind))
        commit_files(self.referee, {"policy.json": json.dumps(
            {"constitutional": {"security_keywords": ["SLUG", "Perm"]}}).encode()})
        self.import_rows()
        self.assertEqual(df.binding(self.referee).keywords, ("slug", "perm"))
        self.refused("on a security path", catalog=self.catalog([{"cause": "lint_regression",
                                                                  "patch": self.drafts["lint_regression"]}]))

    def test_a_patch_whose_result_is_the_file_it_started_from_is_refused(self):  # drill_fixtures_noop_accepted
        """E499 (`26f`): a plant changes its file; lines replaced by themselves, with an index line naming one blob,
        apply exactly and are still no plant (the measurement would find no cause only after the sandbox's minutes)."""
        blob = df.blob_id(TOY[GREET])[:12]
        noop = (f"diff --git a/{GREET} b/{GREET}\nindex {blob}..{blob} 100644\n--- a/{GREET}\n+++ b/{GREET}\n"
                '@@ -2,1 +2,1 @@\n-  return "Hello, " + name + "!";\n+  return "Hello, " + name + "!";\n')
        self.refused("changes nothing", catalog=self.catalog([{"cause": "test_regression", "patch": noop}]))

    def test_a_file_a_merge_expected_candidate_changes_is_refused(self):  # drill_fixtures_candidate_files_unchecked
        """E499 (`26f`: per file, not per line); a rejected candidate's file is free."""
        stats = patch_of(self.toy, STATS, TOY[STATS].replace(b"return sum", b"return sum + 1"))
        said = self.refused("merge-expected candidate good", catalog=self.catalog([{"cause": "test_regression",
                                                                                     "patch": stats}]))
        self.assertNotIn("stats.js", said)

    def test_a_patch_that_is_no_single_in_place_modification_is_refused(self):  # drill_fixtures_add_accepted
        """E499 (`26f`: one existing regular file changed in place): an added, deleted, renamed or binary file, a
        mode change, two files, a CR and a missing file are each refused."""
        add = "diff --git a/textkit/x.js b/textkit/x.js\nnew file mode 100644\nindex 0000000..e69de29\n"
        delete = "diff --git a/textkit/src/slug.js b/textkit/src/slug.js\ndeleted file mode 100644\n" \
                 "index 1111111..0000000\n--- a/textkit/src/slug.js\n+++ /dev/null\n@@ -1 +0,0 @@\n-x\n"
        rename = "diff --git a/a.js b/b.js\nsimilarity index 100%\nrename from a.js\nrename to b.js\n"
        mode = "diff --git a/textkit/src/slug.js b/textkit/src/slug.js\nold mode 100644\nnew mode 100755\n"
        binary = "diff --git a/textkit/a.bin b/textkit/a.bin\nindex 1111111..2222222 100644\n" \
                 "Binary files a/textkit/a.bin and b/textkit/a.bin differ\n"
        two = self.drafts["lint_regression"] + self.drafts["test_regression"]
        crlf = self.drafts["lint_regression"].replace("\n", "\r\n")
        missing = self.drafts["lint_regression"].replace("textkit/src/slug.js", "textkit/src/gone.js")
        for patch, says in ((add, "adds a file"), (delete, "deletes a file"), (rename, "renames"),
                            (mode, "changes a mode"), (binary, "is binary"), (two, "changes 2 files"),
                            (crlf, "carriage return"), (missing, "no existing regular file")):
            self.refused(says, catalog=self.catalog([{"cause": "lint_regression", "patch": patch}]))

    def test_no_exact_fit_is_refused(self):  # drill_fixtures_context_unchecked drill_fixtures_new_start_unchecked
        """E499 (`26f`: kaydırmadan): a hunk moved by a line, a context line one byte off, and a new start that is not
        the old one moved by the hunks before it are refused, though each would apply with an offset or fuzz."""
        good = self.drafts["lint_regression"]
        moved = good.replace("@@ -1,4 +1,4 @@", "@@ -2,4 +2,4 @@")
        fuzzed = good.replace(" export function slugify(text) {", " export function slugify(text)  {")
        shifted = good.replace("@@ -1,4 +1,4 @@", "@@ -1,4 +2,4 @@")
        self.assertNotEqual(moved, good)
        self.assertNotEqual(fuzzed, good)
        for patch, says in ((moved, "outside the file"), (fuzzed, "does not apply at its lines"),
                            (shifted, "new start")):
            self.refused(says, catalog=self.catalog([{"cause": "lint_regression", "patch": patch}]))

    def test_an_index_line_that_is_not_the_files_blobs_is_refused(self):  # drill_fixtures_index_unchecked
        """E499 (`26c`'s diff.patch form): the index line names the file's blob in this toy tree and the result's, and
        the file's own mode (no mode change)."""
        good = self.drafts["lint_regression"]
        self.assertIn(" 100644\n", good)
        self.refused("another mode", catalog=self.catalog([{"cause": "lint_regression",
                                                            "patch": good.replace(" 100644\n", " 100755\n", 1)}]))
        old, new = good.split("\n")[1].split(" ")[1].split("..")
        self.refused("another blob", catalog=self.catalog([{"cause": "lint_regression",
                                                            "patch": good.replace(old, "1234567", 1)}]))
        self.refused("another result blob", catalog=self.catalog([{"cause": "lint_regression",
                                                                   "patch": good.replace(new, "1234567", 1)}]))

    def test_a_patch_that_is_not_utf8_text_is_refused(self):  # drill_fixtures_surrogate_accepted
        """E499: a lone surrogate (JSON can carry one) is no text git wrote; it is refused as the patch's fault."""
        good = self.drafts["lint_regression"]
        odd = good.replace("@@ -1,4 +1,4 @@", "@@ -1,4 +1,4 @@ \ud800", 1)
        self.assertNotEqual(odd, good)
        self.refused("lone surrogate", catalog=self.catalog([{"cause": "lint_regression", "patch": odd}]))

    def test_a_value_over_48_kb_is_refused(self):  # drill_fixtures_size_unchecked
        """E499, E544 (4): GitHub holds at most 48 KB in one secret."""
        big = b"// " + b"x" * 50_000 + b"\n"
        entries = [{"cause": "build_break", "patch": patch_of(self.toy, GREET, TOY[GREET] + big)},
                   {"cause": "lint_regression", "patch": self.drafts["lint_regression"]},
                   {"cause": "test_regression", "patch": self.drafts["test_regression"]}]
        self.refused("over GitHub's 48 KB", catalog=self.catalog(entries))

    def test_a_catalog_that_is_not_a_list_of_cause_and_patch_is_refused(self):
        """E499: the operator's drafts, read strictly."""
        for entries in ([], {"cause": "x"}, [{"cause": "build_break"}], [{"cause": "build_break", "patch": 1}],
                        [{"cause": "build_break", "patch": "p", "id": "x"}]):
            self.refused("catalog", catalog=self.catalog(entries))


class MeasuredCauseTest(Fixture):
    def test_a_measured_cause_that_is_not_the_declared_one_is_refused(self):  # drill_fixtures_label_unmeasured
        """E499 (`26f`: the patch gives exactly this cause by `29j`'s order)."""
        entries = [{"cause": "lint_regression", "patch": self.drafts["build_break"]},
                   {"cause": "build_break", "patch": self.drafts["lint_regression"]},
                   {"cause": "test_regression", "patch": self.drafts["test_regression"]}]
        self.refused("declared lint_regression, measured build_break", catalog=self.catalog(entries))

    def test_two_causes_or_none_are_refused(self):  # drill_fixtures_ambiguous_accepted
        """E499 (`26f`: each instance has one cause): a red test beside a risen lint total is two; nothing is none."""
        both = dict(self.answers)
        both[TOY[SLUG].replace(b"const lower", b"var lower")] = Measurement("v22.23.4", True, 2, False)
        self.refused("two causes", sandbox=FakeSandbox(both))
        none = dict(self.answers)
        none[TOY[GREET].replace(b"Hello", b"Hi")] = Measurement("v22.23.4", True, 1, True)
        self.refused("no cause", sandbox=FakeSandbox(none))

    def test_a_plant_measured_with_other_tools_than_the_bases_is_refused(self):  # drill_fixtures_plan_unchecked
        """E499 (`26f`: measured with the toy's own tools): a patch to .nvmrc, package.json or package-lock.json would
        measure the plant on another Node or other dependencies than the clean base it is compared with."""
        nvmrc = patch_of(self.toy, "textkit/.nvmrc", b"22.23.5\n")
        manifest = patch_of(self.toy, "textkit/package.json",
                            TOY["textkit/package.json"].replace(b'"1.0.0"', b'"1.0.1"'))
        for patch in (nvmrc, manifest):
            entries = [{"cause": "build_break", "patch": patch},
                       {"cause": "lint_regression", "patch": self.drafts["lint_regression"]},
                       {"cause": "test_regression", "patch": self.drafts["test_regression"]}]
            self.refused("with the base's tools", catalog=self.catalog(entries))
            self.assertEqual(self.sandbox.trees, [], "a tree was measured before every plan was checked")

    def test_the_clean_tree_must_load_green_on_the_toys_node(self):  # drill_fixtures_base_unchecked
        """E499: the base is measured once and must be clean, on the Node `.nvmrc` names."""
        self.refused("does not load", sandbox=FakeSandbox(self.answers, base=Measurement("v22.23.4", True, 1, False)))
        self.refused(".nvmrc names", sandbox=FakeSandbox(self.answers, base=Measurement("v20.0.0", True, 1, True)))

    def test_29js_rule_order_names_the_cause(self):
        """E499 (`29j`): build_break first, its red tests and lint its result; then lint; then a red test."""
        cause = df.measured_cause
        self.assertEqual(cause(BASE, Measurement("v22.23.4", False, 9, False))[0], "build_break")
        self.assertEqual(cause(BASE, Measurement("v22.23.4", True, 2, True))[0], "lint_regression")
        self.assertEqual(cause(BASE, Measurement("v22.23.4", True, 0, False))[0], "test_regression")
        for unnamed in (Measurement("v22.23.4", True, 2, False), Measurement("v22.23.4", True, 1, True),
                        Measurement("v22.23.4", None, 1, False), Measurement("v22.23.4", True, None, False),
                        Measurement("v22.23.4", True, 2, None), Measurement("v20.0.0", False, 1, False)):
            self.assertIsNone(cause(BASE, unnamed)[0], unnamed)
        self.assertIn("flaky", cause(BASE, Measurement("v22.23.4", True, 1, None))[1])

    def test_errors_and_warnings_that_move_apart_name_no_cause(self):  # drill_fixtures_lint_split_ignored
        """E499 (`29j` leaves the lint total's producer unnamed): when ESLint's errors and warnings move apart, a total
        of errors alone, or of warnings alone, would say another thing than their sum, so the plant is refused."""
        cause, base = df.measured_cause, Measurement("v22.23.4", True, 3, True, (2, 1))
        for split, red in (((3, 0), False), ((3, 0), True), ((1, 2), True), ((1, 3), False)):
            found = cause(base, Measurement("v22.23.4", True, sum(split), not red, split))
            self.assertIsNone(found[0], split)
            self.assertIn("moved apart", found[1])
        self.assertEqual(cause(base, Measurement("v22.23.4", True, 4, True, (2, 2)))[0], "lint_regression")
        self.assertEqual(cause(base, Measurement("v22.23.4", True, 3, False, (2, 1)))[0], "test_regression")
        self.assertEqual(cause(base, Measurement("v22.23.4", False, 0, False, (0, 5)))[0], "build_break")


class DiffTest(unittest.TestCase):
    """E499: the seed's own strict unified-diff reader and applier."""

    OLD = b"a\nb\nc\nd\ne\nf\ng\nh\n"

    def edit(self, text):
        return df.in_place_edit(text)

    def test_hunks_apply_at_their_lines_moved_by_the_hunks_before(self):
        """E499: each hunk at its own lines, the later one's new start moved by the hunks before it."""
        text = ("diff --git a/f b/f\nindex 1111111..2222222 100644\n--- a/f\n+++ b/f\n"
                "@@ -1,2 +1,3 @@\n a\n+x\n b\n@@ -7,2 +8,1 @@\n g\n-h\n")
        self.assertEqual(df.apply(self.OLD, self.edit(text).hunks), b"a\nx\nb\nc\nd\ne\nf\ng\n")

    def test_a_missing_last_newline_is_kept_or_changed_exactly(self):
        """E499: git's no-newline marker is a byte of the context: a file whose last line ends otherwise is refused."""
        text = ("diff --git a/f b/f\nindex 1111111..2222222 100644\n--- a/f\n+++ b/f\n"
                "@@ -1,2 +1,2 @@\n a\n-b\n\\ No newline at end of file\n+c\n")
        self.assertEqual(df.apply(b"a\nb", self.edit(text).hunks), b"a\nc\n")
        with self.assertRaises(ValueError):
            df.apply(b"a\nb\n", self.edit(text).hunks)  # the file's b has its newline: the context is not byte for byte

    def test_counts_must_be_the_hunks_lines(self):
        """E499: a hunk's lines are exactly its header's counts, neither fewer nor more, and no stray line."""
        for body in ("@@ -1,2 +1,2 @@\n a\n-b\n", "@@ -1,1 +1,1 @@\n a\n-b\n+c\n", "@@ -1 +1 @@\n-a\n+b\nzz\n"):
            with self.assertRaises(ValueError, msg=body):
                self.edit("diff --git a/f b/f\nindex 1111111..2222222 100644\n--- a/f\n+++ b/f\n" + body)

    def test_hunks_out_of_order_or_overlapping_are_refused(self):  # drill_fixtures_hunks_unordered
        """E499: a hunk that starts before the end of the one ahead of it does not apply, however its lines fit."""
        head = "diff --git a/f b/f\nindex 1111111..2222222 100644\n--- a/f\n+++ b/f\n"
        for body in ("@@ -7,2 +7,1 @@\n g\n-h\n@@ -2,1 +1,1 @@\n-b\n+x\n",  # reordered, its new start consistent
                     "@@ -1,2 +1,2 @@\n a\n-b\n+x\n@@ -2,2 +2,2 @@\n-x\n+b\n c\n"):  # overlapping
            with self.assertRaisesRegex(ValueError, "before the hunk ahead"):
                df.apply(self.OLD, self.edit(head + body).hunks)

    def test_a_hunk_that_changes_nothing_is_refused(self):
        """E499: a hunk of context alone is no plant."""
        with self.assertRaisesRegex(ValueError, "changes nothing"):
            self.edit("diff --git a/f b/f\nindex 1111111..2222222 100644\n--- a/f\n+++ b/f\n@@ -1 +1 @@\n a\n")

    def test_the_files_a_candidate_changes_are_read_by_hunk_counts(self):
        """A removed line that begins with ``--`` is not a header; a rename names both paths."""
        text = ("diff --git a/x.js b/x.js\nindex 1111111..2222222 100644\n--- a/x.js\n+++ b/x.js\n"
                "@@ -1,2 +1,1 @@\n--- a/y.js\n a\n"
                "diff --git a/p.js b/q.js\nsimilarity index 100%\nrename from p.js\nrename to q.js\n")
        self.assertEqual(df.changed_files(text), {"x.js", "p.js", "q.js"})

    def test_git_writes_the_blobs_the_index_line_names(self):
        """E499: `blob_id` is git's own object name, which the index line abbreviates."""
        repo = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, repo, ignore_errors=True)
        (repo / "f").write_bytes(self.OLD)
        named = subprocess.run(["git", "-c", "core.autocrlf=false", "hash-object", "f"], cwd=repo, capture_output=True,
                               check=True).stdout.decode().strip()
        self.assertEqual(df.blob_id(self.OLD), named)


class PlanTest(unittest.TestCase):
    """E499: what the sandbox runs, read from the toy tree."""

    def tree(self, **over):
        files = {rel: (content, False) for rel, content in TOY.items()}
        files.update({rel: (content, False) for rel, content in over.items()})
        return files

    def test_the_project_its_files_its_tests_and_its_node(self):
        """E499: the toy's one Node project, the files node --check reads, the modules it imports (no test file, by
        Node 22's default patterns) and the Node .nvmrc names."""
        plan = df.plan_of(self.tree())
        self.assertEqual(plan.project, "textkit")
        self.assertEqual(plan.node, "v22.23.4")
        self.assertIn("textkit/test/greet.test.js", plan.parse)
        self.assertNotIn("textkit/test/greet.test.js", plan.load)
        self.assertIn("textkit/src/greet.js", plan.load)
        for rel in ("test/a.js", "a/test/b/c.mjs", "a.test.js", "a-test.cjs", "a_test.js", "test-a.js", "test.js"):
            self.assertTrue(df.is_node_test_file(rel), rel)
        for rel in ("src/a.js", "tests/a.js", "atest.js", "test.ts", "contest.js"):
            self.assertFalse(df.is_node_test_file(rel), rel)

    def test_a_tree_the_seed_cannot_measure_as_the_toys_own_is_refused(self):
        """E499: a package outside the npm registry, a test script that is not exactly node --test, an .nvmrc naming no
        version and two lockfiles are each refused before anything runs."""
        lock = json.loads(TOY["textkit/package-lock.json"])
        lock["packages"]["node_modules/x"] = {"version": "1.0.0", "resolved": "https://evil.example/x.tgz",
                                              "integrity": "sha512-x"}
        manifest = json.loads(TOY["textkit/package.json"])
        manifest["scripts"]["test"] = "node --test test/"
        for over, says in (({"textkit/package-lock.json": json.dumps(lock).encode()}, "npm registry"),
                           ({"textkit/package.json": json.dumps(manifest).encode()}, "exactly 'node --test'"),
                           ({"textkit/.nvmrc": b"lts/*\n"}, ".nvmrc"),
                           ({"other/package-lock.json": b"{}"}, "2 package-lock.json")):
            with self.assertRaisesRegex(FixtureStop, says.replace(".", r"\.").replace("*", r"\*")):
                df.plan_of(self.tree(**over))


class DockerSandboxTest(unittest.TestCase):
    """E499: the sandbox's containers, as `DockerSandbox` asks docker for them (docker itself replaced)."""

    def setUp(self):
        self.calls = []
        self.plan = df.plan_of({rel: (content, False) for rel, content in TOY.items()})

    def docker(self, argv, **kw):
        self.calls.append(argv)
        out = b""
        if argv[1] == "run" and "65534:65534" in argv:
            test = {"status": 1, "timed_out": False, "tests": 2, "red": ["test/a.test.js:3:1 a"]}
            if "DFX_LINT=1" in argv:
                out = json.dumps({"node": "v22.23.4", "parse": [{"status": 0}] * len(self.plan.parse),
                                  "load": [{"status": 0}] * len(self.plan.load),
                                  "lint": {"status": 0, "timed_out": False,
                                           "stdout": '[{"errorCount": 1, "warningCount": 2}]'},
                                  "test": test}).encode()
            else:
                out = json.dumps({"node": "v22.23.4", "parse": [], "load": [], "lint": None, "test": test}).encode()
        return subprocess.CompletedProcess(argv, 0, out, b"")

    def test_only_the_install_is_online(self):  # drill_fixtures_measured_online drill_fixtures_install_runs_scripts
        """E499: npm ci --ignore-scripts is the only step with a network; each tree is measured with --network none,
        read-only, unprivileged, its dependencies mounted read-only; the volume is removed at the end."""
        box = df.DockerSandbox("node:22@sha256:" + "a" * 64, run=self.docker)
        tree = {rel: (content, False) for rel, content in TOY.items()}
        self.assertEqual(box.measure(tree, self.plan), Measurement("v22.23.4", True, 3, False, (1, 2)))
        box.measure(tree, self.plan)
        runs = [argv for argv in self.calls if argv[1] == "run"]
        # one install for the one lockfile, and MF12's four runs of each of two measurements, each its own container
        self.assertEqual(len(runs), 1 + 2 * df.TEST_RUNS)
        install, measured = runs[0], runs[1:]
        self.assertNotIn("--network", install)
        self.assertIn("npm ci --ignore-scripts --no-audit --no-fund --registry=https://registry.npmjs.org/",
                      install[-1])
        for argv in measured:
            self.assertEqual(argv[argv.index("--network") + 1], "none")
            self.assertIn("--read-only", argv)
            self.assertTrue(any(a.endswith(",dst=/deps,readonly") for a in argv))
            self.assertEqual(argv[argv.index("--user") + 1], "65534:65534")
        volume = next(a for a in install if a.startswith("type=volume")).split(",")[1].split("=")[1]
        box.close()
        self.assertEqual(self.calls[-1][:4], ["docker", "volume", "rm", "-f"])
        self.assertEqual(self.calls[-1][4], volume)

    def test_each_of_mf12s_four_runs_is_a_fresh_container_and_only_the_first_does_the_rest(self):
        # drill_fixtures_reruns_in_one_container
        """E499, `29j` `flaky` ("taze kapsayıcıda yeniden koşuları"): the first container parses, imports, lints and
        runs the tests once; each of the three reruns is another container, named apart, that only runs them."""
        box = df.DockerSandbox("node:22@sha256:" + "a" * 64, run=self.docker)
        box.measure({rel: (content, False) for rel, content in TOY.items()}, self.plan)
        measured = [argv for argv in self.calls if argv[1] == "run" and "65534:65534" in argv]
        self.assertEqual(len(measured), df.TEST_RUNS)
        names = [argv[argv.index("--name") + 1] for argv in measured]
        self.assertEqual(len(set(names)), df.TEST_RUNS)
        self.assertEqual([argv.count("DFX_LINT=1") for argv in measured], [1, 0, 0, 0])
        for argv in measured[1:]:
            self.assertIn("DFX_PARSE=[]", argv)
            self.assertIn("DFX_LOAD=[]", argv)
        self.assertNotIn("DFX_PARSE=[]", measured[0])

    def test_the_tests_are_red_per_test_as_mf12_has_it(self):  # drill_fixtures_flaky_taken_for_red
        """E499, `29j` `flaky` `per_test_rule`: a test is red when it fails in all four runs, flaky when it fails in
        some; tests that fail in different runs, none in all, are no red test (no cause), whatever each run says."""
        red = lambda *ids, tests=5: {"status": 1, "tests": tests, "red": list(ids)}  # noqa: E731
        ok = {"status": 0, "tests": 5, "red": []}
        a, b, c = "t/a.js:3:1 a", "t/b.js:3:1 b", "t/c.js:3:1 c"
        self.assertIs(df.tests_green([ok] * 4), True)
        self.assertIs(df.tests_green([red(a)] * 4), False)
        self.assertIs(df.tests_green([red(a, b), red(a), red(a, c), red(a)]), False)  # a in all four, b and c flaky
        self.assertIsNone(df.tests_green([red(a), red(b), red(a), red(b)]))  # every run red, no test red in all
        self.assertIsNone(df.tests_green([red(a), ok, ok, ok]))
        self.assertIsNone(df.tests_green([ok, ok, ok, red(a)]))
        for runs in ([ok, ok, ok, dict(ok, timed_out=True)], [ok, ok, ok, dict(ok, status=None)],
                     [ok, ok, ok, dict(ok, tests=0)], [ok, ok, ok, dict(ok, tests=None)],
                     [ok, ok, ok, {"status": 1, "tests": 5, "red": []}],  # died, no test named
                     [ok, ok, ok, {"status": 0, "tests": 5, "red": None}],
                     [ok, ok, ok, {"status": 1, "tests": 1, "red": [a, b]}]):
            self.assertIsNone(df.tests_green(runs), runs)
        for runs in ([ok] * 3, [ok] * 5, {"status": 0}, [ok, ok, ok, "x"]):
            with self.assertRaises(ValueError):
                df.tests_green(runs)

    def test_the_harnesss_output_is_read_strictly(self):  # drill_fixtures_flaky_taken_for_red
        """E499: the first container's one JSON line and each rerun's, each field the plan's; the tests are green or
        red only as MF12's four runs say (`test_the_tests_are_red_per_test_as_mf12_has_it`)."""
        ok = {"status": 0, "timed_out": False, "tests": 3, "red": []}
        good = {"node": "v22.23.4", "parse": [{"status": 0}] * len(self.plan.parse),
                "load": [{"status": 0}] * len(self.plan.load), "lint": {"status": 1, "stdout": "[]"}, "test": ok}
        again = tuple(json.dumps({"test": ok}).encode() for _k in range(df.TEST_RUNS - 1))
        read = lambda reruns=again, **over: df.measurement_of(  # noqa: E731
            json.dumps(dict(good, **over)).encode(), self.plan, reruns)
        self.assertEqual(read(), Measurement("v22.23.4", True, 0, True, (0, 0)))
        two = '[{"errorCount": 2, "warningCount": 1}, {"errorCount": 0, "warningCount": 4}]'
        self.assertEqual(read(lint={"status": 1, "stdout": two}).lint_split, (2, 5))
        self.assertIs(read(parse=[{"status": 1}] + good["parse"][1:]).loads, False)
        self.assertIsNone(read(load=[{"status": None, "timed_out": True}] + good["load"][1:]).loads)
        self.assertIsNone(read(lint={"status": 2, "stdout": "[]"}).lint_total)
        self.assertIsNone(read(lint={"status": 1, "stdout": "Oops"}).lint_total)
        self.assertIsNone(read(lint={"status": 1, "stdout": '[{"errorCount": -1, "warningCount": 0}]'}).lint_split)
        self.assertEqual(df.TEST_RUNS, 4)
        self.assertIs(read(test=dict(ok, status=1, red=["x"]),
                           reruns=tuple(json.dumps({"test": dict(ok, status=1, red=["x"])}).encode()
                                        for _k in range(3))).tests_green, False)
        flaky = tuple(json.dumps({"test": dict(ok, status=1, red=["x"])}).encode() for _k in range(2))
        self.assertIsNone(read(reruns=(*flaky, json.dumps({"test": ok}).encode())).tests_green)
        for reruns in (again[:2], again + again[:1], (b"x", *again[1:]), (b"{}", *again[1:])):
            with self.assertRaises(FixtureStop):
                read(reruns=reruns)
        with self.assertRaises(FixtureStop):
            read(parse=[])
        with self.assertRaises(FixtureStop):
            read(lint=None)
        with self.assertRaises(FixtureStop):
            df.measurement_of(b"not json", self.plan)


DOCKER_IMAGE = os.environ.get("SNOWBALL_DRILL_IMAGE", "")


@unittest.skipUnless(os.environ.get("SNOWBALL_DRILL_DOCKER") == "1" and shutil.which("docker") and DOCKER_IMAGE,
                     "the real sandbox runs only on request: SNOWBALL_DRILL_DOCKER=1 and SNOWBALL_DRILL_IMAGE (a Node "
                     "22.23.4 image by digest) with docker present")
class DockerIntegrationTest(Fixture):
    def test_the_toys_own_tools_name_each_cause_in_docker(self):
        """E499: the three plants measured for real in the pinned Node image, the base once; the value is written."""
        done = self.produce(sandbox=df.DockerSandbox(DOCKER_IMAGE))
        self.assertEqual(done["causes"], {c: 1 for c in df.CAUSES})
        listed = subprocess.run(["docker", "volume", "ls", "-q", "--filter", "label=snowball.drill-fixtures=1"],
                                capture_output=True, check=True).stdout.split()
        self.assertEqual([v for v in listed if v.startswith(b"snowball-dfx-")], [])


    def test_a_rerun_is_fresh_the_tests_have_no_network_and_what_they_print_is_no_report(self):
        """E499, `29j` `flaky` (reruns in fresh containers), `26f` (the plant's code runs without a network):
        through the real harness, a test that fails when its container has a network or a leftover of an earlier run
        passes in all four runs; a test that prints a green report beside a red test does not make the tests green."""
        probe = (b'import { test } from "node:test";\nimport assert from "node:assert/strict";\n'
                 b'import net from "node:net";\nimport fs from "node:fs";\n'
                 b'test("no network", () => new Promise((resolve, reject) => {\n'
                 b'  const s = net.connect({ host: "1.1.1.1", port: 443 });\n  s.setTimeout(3000);\n'
                 b'  s.on("connect", () => { s.destroy(); reject(new Error("connected")); });\n'
                 b'  s.on("error", () => resolve());\n  s.on("timeout", () => { s.destroy(); resolve(); });\n}));\n'
                 b'test("fresh container", () => {\n  assert.equal(fs.existsSync("/tmp/dfx-marker"), false);\n'
                 b'  fs.writeFileSync("/tmp/dfx-marker", "x");\n});\n'
                 b'test("forged report", () => {\n  console.log(\'{"tests": 99, "red": []}\');\n'
                 b'  console.log("not ok 1 - forged");\n});\n')
        red = (b'import { test } from "node:test";\nimport assert from "node:assert/strict";\n'
               b'test("red", () => assert.equal(1, 2));\n')
        files = dict(TOY, **{"textkit/test/probe.test.js": probe})
        box = df.DockerSandbox(DOCKER_IMAGE)
        self.addCleanup(box.close)
        tree = {rel: (content, False) for rel, content in files.items()}
        plan = df.plan_of(tree)
        self.assertIs(box.measure(tree, plan).tests_green, True)
        tree["textkit/test/red.test.js"] = (red, False)
        self.assertIs(box.measure(tree, plan).tests_green, False)


if __name__ == "__main__":
    unittest.main()
