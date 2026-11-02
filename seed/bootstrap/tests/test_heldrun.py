"""The held runner (plan D5, register E510): held cases run only in the private exam repository, published as a
commitment.

Every fixture here is synthetic: a toy brain that adds two numbers and counts a fixture's lines, a held set that plants
a canary token in its commands, stdins and fixtures, and answers that appear nowhere else. The pipeline runs as the
template's jobs run it (`pack_inputs` for `hazir`, `run_held` for `kos`, `judge_held` for `yargi`, `sign_pending` for
`imza`), with the toy brain where the containers would be; `workflow/held.yml` is read the way a reviewer reads it.
"""

import datetime
import io
import json
import re
import shlex
import shutil
import tarfile
import tempfile
import unittest
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from snowball_bootstrap import canon, cli, heldrun, stages, vectors
from snowball_bootstrap.container import RunResult
from snowball_bootstrap.importer import ImportErrorStop
from snowball_bootstrap.treehash import extract

from helpers import BOOTSTRAP_YML, workflow_job
from test_wiring import run_blocks

BOOT = Path(__file__).resolve().parents[1]
HELD_YML = (BOOT / "workflow" / "held.yml").read_text(encoding="utf-8")
CANARY = "HELDCANARY-5e1d0b"
HEAD = "c" * 40
RESULT = json.dumps({"schema": "snowball-bootstrap-result/1", "head": HEAD, "kind": "code", "verdict": "accepted"})
TS = "2026-11-02T00:00:00Z"
TABLE = stages.parse_table(json.dumps({"stage": 0, "mfs": [
    {"mf": 1, "tests": [13], "groups": ["toyheld"], "module": "toy/add.py", "calls": []}]}), 0)
ADD = f"python -m toy.add --tag {CANARY}"
CASES = [
    {"id": "toyheld.add", "purpose": "adds two numbers", "cmd": ADD,
     "stdin": json.dumps({"a": 4000, "b": 242, "note": CANARY}), "fixture": [], "expect": {"value": 4242},
     "changed": {"description": "other numbers", "cmd": ADD, "stdin": json.dumps({"a": 1, "b": 2, "note": CANARY}),
                 "fixture": [], "expect_not": {"value": 4242}}},
    {"id": "toyheld.lines", "purpose": "counts a file's lines", "cmd": "python -m toy.lines /vec/fx/a.txt",
     "fixture": ["fx/a.txt"], "expect": {"value": 3},
     "changed": {"description": "another file", "cmd": "python -m toy.lines /vec/fx/b.txt", "fixture": ["fx/b.txt"],
                 "expect_not": {"value": 3}}},
]
FIXTURES = {"fx/a.txt": f"x\ny\n{CANARY}\n", "fx/b.txt": "only\n"}
MANIFEST = {"tests": [{"id": "T13", "cmd": "true", "stage": 0}], "done_mf": [1], "lockfiles": []}


def tar_of(files):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:", format=tarfile.PAX_FORMAT) as tar:
        for name, text in sorted(files.items()):
            data = text.encode("utf-8")
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode = len(data), 0, 0o644
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def brain_tar(done=(1,)):
    return tar_of({"snowball-tests.json": json.dumps(dict(MANIFEST, done_mf=list(done))),
                   "spec/toyheld.md": "# toyheld\n", "toy/add.py": "print('toy')\n"})


def write_held_set(folder, cases=CASES, fixtures=None, extra=None):
    folder.mkdir(parents=True, exist_ok=True)
    spec = {"toyheld": {"runner": "data", "interface": "spec/toyheld.md", "cases": cases}}
    (folder / "vectors.json").write_text(json.dumps(spec), encoding="utf-8")
    for rel, text in {**FIXTURES, **(fixtures or {}), **(extra or {})}.items():
        (folder / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / rel).write_text(text, encoding="utf-8")
    return folder


@dataclass
class ToyBrain:
    """The containers' stand-in: answers the toy interface from the inputs folder `/vec` stands for."""
    vec: Path
    mode: str = "right"  # right | constant | fault
    calls: list = field(default_factory=list)

    def run(self, cmd, *, cwd=".", stdin=b"", timeout_s):
        self.calls.append(cmd)
        if self.mode == "fault":
            return RunResult(125, b"", b"docker: error response from daemon", 1)
        argv = shlex.split(cmd)
        if argv[:3] == ["python", "-m", "toy.add"]:
            data = json.loads(stdin)
            value = data["a"] + data["b"]
        else:
            value = len((self.vec / argv[3].removeprefix("/vec/")).read_text(encoding="utf-8").splitlines())
        if self.mode == "constant":
            value = 7
        return RunResult(0, (json.dumps({"value": value}) + "\n").encode(), b"", 1)


class HeldCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def pipeline(self, mode="right", done=(1,), held=None, ledger=None):
        held = held or write_held_set(self.tmp / "exam" / "set")
        tar = brain_tar(done)
        held_in = self.tmp / f"held-in-{len(list(self.tmp.glob('held-in-*')))}"
        heldrun.pack_inputs(held_in, RESULT.encode(), held, tar, HEAD, heldrun.new_salt())
        src = held_in.parent / (held_in.name + "-src")
        extract(tar, src, 10 ** 8)
        brains = []

        def runner_for(inputs):
            brains.append(ToyBrain(inputs, mode))
            return brains[-1]
        trace = heldrun.run_held(held_in, TABLE, src, runner_for, 30)
        ledger = ledger or self.tmp / "ledger"
        ledger.mkdir(exist_ok=True)
        row = heldrun.judge_held(held_in, held, trace, ledger, TABLE, src, TS)
        return SimpleNamespace(held=held, held_in=held_in, trace=trace, ledger=ledger, row=row, brains=brains, src=src)


class CommitmentTest(unittest.TestCase):
    def test_a_fresh_salt_hides_the_same_counts(self):  # commitment_unsalted
        """E510: the statement's digest is public in Rekor. Without a salt in the commitment, n, pass and the bits of a
        held run are found by trying every outcome; with one, the same counts commit to unrelated values."""
        one, two = heldrun.new_salt(), heldrun.new_salt()
        commit = heldrun.commitment(one, 3, 2, "101")
        self.assertNotEqual(commit, heldrun.commitment(two, 3, 2, "101"))
        outcomes = [(n, f"{b:0{n}b}" if n else "") for n in range(5) for b in range(2 ** n)]
        tried = {canon.sha256_hex(canon.canonical({"bits": bits, "n": n, "pass": bits.count("1")}))
                 for n, bits in outcomes}
        self.assertNotIn(commit, tried)

    def test_a_commitment_opens_to_its_counts_alone(self):
        salt = heldrun.new_salt()
        commit = heldrun.commitment(salt, 3, 2, "101")
        self.assertEqual(commit, heldrun.commitment(salt, 3, 2, "101"))
        self.assertNotEqual(commit, heldrun.commitment(salt, 3, 2, "110"))
        for args in ((salt, 3, 1, "101"), (salt, 2, 2, "101"), (salt, 3, 2, "1a1"), (salt[:62], 3, 2, "101"),
                     (salt.upper(), 3, 2, "101"), (salt, True, 1, "1"), (salt, 1, -1, "0")):
            with self.assertRaises(heldrun.HeldError, msg=args):
                heldrun.commitment(*args)

    def test_salts_are_256_random_bits(self):
        salts = {heldrun.new_salt() for _ in range(50)}
        self.assertEqual(len(salts), 50)
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", s) for s in salts))


class StatementTest(HeldCase):
    def test_what_is_signed_names_the_run_and_no_count(self):  # counts_published held_salt_shared_with_trace_key
        """E510, critique A-5: no per-push aggregate is public. The statement `imza` signs carries the head, the signed
        result it ran, the held set and the commitment; the counts, the bits and the salt stay in the private ledger.
        The commitment's salt is `yargi`'s own: the trace's key sits in `kos`, beside brain code."""
        run = self.pipeline()
        data = heldrun.statement_path(run.ledger, run.row).read_bytes()
        stmt = json.loads(data)
        self.assertEqual(set(stmt), set(heldrun.STATEMENT_KEYS))
        self.assertEqual(stmt, {"schema": heldrun.STATEMENT_SCHEMA, "head": HEAD,
                                "result_sha256": canon.sha256_hex(RESULT.encode()),
                                "held_set_sha256": heldrun.tree_sha(run.held), "commitment": run.row["commitment"]})
        self.assertEqual(canon.sha256_hex(data), run.row["statement_sha256"])
        self.assertEqual((run.row["n"], run.row["pass"], run.row["bits"]), (4, 4, "1111"))
        for value in (run.row["salt"], run.row["bits"]):
            self.assertNotIn(value.encode(), data)
        key = cli.read_json(run.held_in / heldrun.RUN_FILE)["key"]
        self.assertNotEqual(run.row["salt"], key)
        self.assertNotEqual(run.row["commitment"], heldrun.commitment(key, 4, 4, "1111"))


class TraceTest(HeldCase):
    def test_the_trace_carries_no_held_input_nor_its_plain_name(self):  # held_inputs_in_trace_artifact
        """E510, red team A3: the trace leaves `kos`, the job beside brain code. It names each call by an HMAC under
        the run's key: no command, stdin or fixture of a held case, and not sha256 of one, which confirms a guess."""
        run = self.pipeline()
        data = canon.dump(run.trace).encode("utf-8")
        self.assertEqual(len(run.trace["tape"]), 4)
        needles = [CANARY, "toy.add", "toy.lines", "fx/a.txt", '"a": 4000']
        for case in CASES:
            for variant in (case, case["changed"]):
                needles.append(vectors.input_key(variant["cmd"], variant.get("stdin", "").encode("utf-8")))
        for needle in needles:
            self.assertNotIn(needle.encode("utf-8"), data, needle)

    def test_a_trace_under_another_key_or_of_another_head_is_refused(self):
        run = self.pipeline()
        with self.assertRaises(vectors.TapeError):
            heldrun.unkeyed(run.trace["tape"], heldrun.new_salt(), ["0" * 64])
        for trace in (dict(run.trace, head="d" * 40), dict(run.trace, tape=run.trace["tape"][1:])):
            with self.assertRaises((heldrun.HeldError, vectors.TapeError)):
                heldrun.judge_held(run.held_in, run.held, trace, run.ledger, TABLE, run.src, TS)
        self.assertEqual(len(heldrun.read_ledger(run.ledger)), 1)


class PipelineTest(HeldCase):
    def test_a_brain_that_computes_passes_every_held_case_and_one_that_does_not_fails(self):
        right = self.pipeline()
        wrong = self.pipeline("constant", ledger=right.ledger)
        self.assertEqual((wrong.row["n"], wrong.row["pass"], wrong.row["bits"]), (4, 2, "0101"))
        rows = heldrun.read_ledger(right.ledger)
        self.assertEqual([r["row_id"] for r in rows], ["h1", "h2"])
        self.assertEqual(rows[1]["prev_hash"], rows[0]["row_hash"])
        self.assertIsInstance(rows[0]["seconds"], int)

    def test_kos_gets_no_answer_and_no_file_the_cases_do_not_name(self):
        held = write_held_set(self.tmp / "exam" / "set", extra={"notes.txt": "ANSWERKEY 4242\n"})
        run = self.pipeline(held=held)
        files = {p.relative_to(run.held_in).as_posix(): p.read_bytes() for p in run.held_in.rglob("*") if p.is_file()}
        self.assertEqual(set(files), {"pulled/brain.tar", "pulled/meta.json", "run.json", "inputs/vectors.json",
                                      "inputs/fx/a.txt", "inputs/fx/b.txt"})
        for name, data in files.items():
            self.assertNotIn(b"4242", data, name)
            self.assertNotIn(b"ANSWERKEY", data, name)
        shown = json.loads(files["inputs/vectors.json"])["toyheld"]["cases"]
        self.assertEqual([(c["expect"], c["changed"]["expect_not"]) for c in shown], [({}, {}), ({}, {})])

    def test_a_held_fixture_that_carries_an_answer_or_is_missing_is_refused(self):
        answer = "sha256:" + "e" * 64
        cases = [dict(CASES[0], expect={"digest": answer}), CASES[1]]  # a.txt is the other case's: a lookup
        held = write_held_set(self.tmp / "a", cases=cases, fixtures={"fx/a.txt": answer + "\n"})
        with self.assertRaisesRegex(heldrun.HeldError, "carries an answer"):
            heldrun.pack_inputs(self.tmp / "in-a", RESULT.encode(), held, brain_tar(), HEAD, heldrun.new_salt())
        held = write_held_set(self.tmp / "b", cases=[dict(CASES[1], fixture=["fx/none.txt"])])
        with self.assertRaisesRegex(heldrun.HeldError, "not there"):
            heldrun.pack_inputs(self.tmp / "in-b", RESULT.encode(), held, brain_tar(), HEAD, heldrun.new_salt())
        held = write_held_set(self.tmp / "c", cases=[dict(CASES[1], fixture=["../a/fx/a.txt"])])
        with self.assertRaisesRegex(heldrun.HeldError, "relative path inside"):
            heldrun.pack_inputs(self.tmp / "in-c", RESULT.encode(), held, brain_tar(), HEAD, heldrun.new_salt())

    def test_only_data_groups_run_held(self):
        with self.assertRaisesRegex(heldrun.HeldError, "not a data group"):
            heldrun.blinded({"chain": {"rows": []}})

    def test_a_docker_failure_is_the_sandboxs_and_counts_nothing(self):
        run = self.pipeline("fault")
        self.assertEqual((run.row["n"], run.row["pass"], run.row["bits"], run.row["fault"]), (0, 0, "", "sandbox"))

    def test_a_micro_feature_not_done_runs_no_held_case(self):
        run = self.pipeline(done=())
        self.assertEqual(run.brains, [])
        self.assertEqual((run.trace["tape"], run.row["n"], run.row["bits"]), ([], 0, ""))

    def test_a_held_set_changed_after_hazir_is_refused(self):
        held = write_held_set(self.tmp / "exam" / "set")
        tar = brain_tar()
        heldrun.pack_inputs(self.tmp / "in", RESULT.encode(), held, tar, HEAD, heldrun.new_salt())
        extract(tar, self.tmp / "src", 10 ** 8)
        trace = heldrun.run_held(self.tmp / "in", TABLE, self.tmp / "src", lambda inputs: ToyBrain(inputs), 30)
        (held / "fx" / "b.txt").write_text("two\nlines\n", encoding="utf-8")
        (self.tmp / "ledger").mkdir()
        with self.assertRaisesRegex(heldrun.HeldError, "not the one"):
            heldrun.judge_held(self.tmp / "in", held, trace, self.tmp / "ledger", TABLE, self.tmp / "src", TS)


class LedgerTest(HeldCase):
    def rewrite(self, ledger, number, **fields):
        lines = (ledger / heldrun.LEDGER_FILE).read_text(encoding="utf-8").splitlines()
        row = json.loads(lines[number - 1])
        row.update(fields)
        row["row_hash"] = canon.row_hash({k: v for k, v in row.items() if k != "row_hash"})
        lines[number - 1] = canon.canonical(row).decode("utf-8")
        (ledger / heldrun.LEDGER_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_rows_chain_and_each_opens_its_commitment_and_statement(self):
        run = self.pipeline()
        self.pipeline("constant", ledger=run.ledger)
        good = (run.ledger / heldrun.LEDGER_FILE).read_bytes()
        for fields in ({"pass": 3, "bits": "1110"}, {"head": "d" * 40}, {"prev_hash": "1" * 64}, {"row_id": "h9"},
                       {"fault": "brain"}, {"seconds": -1}):
            self.rewrite(run.ledger, 1, **fields)
            with self.assertRaises(heldrun.HeldError, msg=fields):
                heldrun.read_ledger(run.ledger)
            (run.ledger / heldrun.LEDGER_FILE).write_bytes(good)
        lines = good.decode("utf-8").splitlines()
        (run.ledger / heldrun.LEDGER_FILE).write_text(lines[1] + "\n", encoding="utf-8")  # the first row dropped
        with self.assertRaises(heldrun.HeldError):
            heldrun.read_ledger(run.ledger)

    def test_each_statement_is_signed_once_and_only_as_its_row_names_it(self):
        run = self.pipeline()
        signed = []

        def signer(path, bundle):
            signed.append(path.name)
            bundle.write_text("{}", encoding="utf-8")
        self.assertEqual(heldrun.sign_pending(run.ledger, signer), ["h1"])
        self.pipeline("constant", ledger=run.ledger)
        self.assertEqual(heldrun.sign_pending(run.ledger, signer), ["h2"])
        self.assertEqual(heldrun.sign_pending(run.ledger, signer), [])
        self.assertEqual(signed, [f"{r['statement_sha256']}.json" for r in heldrun.read_ledger(run.ledger)])
        third = self.pipeline(ledger=run.ledger)
        heldrun.statement_path(run.ledger, third.row).write_text('{"n": 4}', encoding="utf-8")
        with self.assertRaisesRegex(heldrun.HeldError, "not the one its row names"):
            heldrun.sign_pending(run.ledger, signer)

    def test_the_reveal_opens_every_row_and_verifies_every_signed_one(self):
        run = self.pipeline()
        self.pipeline("constant", ledger=run.ledger)
        heldrun.bundle_path(run.ledger, run.row).parent.mkdir(parents=True)
        heldrun.bundle_path(run.ledger, run.row).write_text("{}", encoding="utf-8")
        seen = []
        opened = heldrun.reveal(run.ledger, lambda s, b: seen.append((s.name, b.name)))
        self.assertEqual([(r["row_id"], r["pass"], r["signed"]) for r in opened], [("h1", 4, True), ("h2", 2, False)])
        name = run.row["statement_sha256"]
        self.assertEqual(seen, [(f"{name}.json", f"{name}.cosign.json")])

        def bad(_s, _b):
            raise ImportErrorStop("signature verification failed")
        with self.assertRaises(ImportErrorStop):
            heldrun.reveal(run.ledger, bad)

    def test_statements_are_signed_by_the_epochs_key_never_by_an_identity(self):  # held_signed_keyless
        """E520 (verifier finding 9): a keyless Sigstore certificate names the exam repository and its workflow in a
        public log for good. The signer is cosign with the epoch's held key from the environment; without the key it
        signs nothing (cosign would fall back to keyless); `reveal` checks with the public half."""
        # held_key_not_required
        calls = []

        def ran(argv, **_kw):
            calls.append(argv)
            return SimpleNamespace(returncode=0, stderr="")
        stmt, bundle, pub = Path("s.json"), Path("b.json"), Path("held.pub")
        with mock.patch.object(heldrun.subprocess, "run", ran), \
                mock.patch.dict(heldrun.os.environ, {heldrun.SIGNING_KEY_ENV: "-----BEGIN ENCRYPTED KEY-----"}):
            heldrun.key_signer("/tmp/cosign")(stmt, bundle)
            heldrun.key_verifier("/tmp/cosign", pub)(stmt, bundle)
        self.assertEqual(calls, [["/tmp/cosign", "sign-blob", "--key", f"env://{heldrun.SIGNING_KEY_ENV}", "--bundle",
                                  "b.json", "--yes", "s.json"],
                                 ["/tmp/cosign", "verify-blob", "--key", "held.pub", "--bundle", "b.json", "s.json"]])
        with mock.patch.object(heldrun.subprocess, "run", ran), mock.patch.dict(heldrun.os.environ, {}, clear=True):
            with self.assertRaisesRegex(heldrun.HeldError, "held key"):
                heldrun.key_signer("/tmp/cosign")(stmt, bundle)
        self.assertEqual(len(calls), 2)  # nothing ran without the key
        self.assertFalse(hasattr(heldrun, "held_identity"))


class EligibilityTest(unittest.TestCase):
    def test_only_a_code_or_exit_head_runs_and_each_head_once(self):
        row = {"head": HEAD}
        for kind in ("code", "exit"):
            self.assertEqual(heldrun.eligible({"kind": kind, "head": HEAD}), HEAD)
        for result in ({"kind": "spec", "head": HEAD}, {"kind": "none", "head": HEAD}, {"kind": "code", "head": "x"},
                       {"kind": "code"}, None, []):
            self.assertIsNone(heldrun.eligible(result))
        self.assertEqual(heldrun.todo({"kind": "code", "head": HEAD}, []), HEAD)
        self.assertIsNone(heldrun.todo({"kind": "code", "head": HEAD}, [row]))
        self.assertEqual(heldrun.referee_identity("o/referee"),
                         "https://github.com/o/referee/.github/workflows/bootstrap.yml@refs/heads/main")

    def test_a_held_set_path_stays_inside_the_exam_repository(self):
        base = Path("exam")
        self.assertEqual(heldrun.inside(base, "k6/held"), base / "k6" / "held")
        for rel in ("", "/abs", "../up", "a/../b", "a\\b", "./a", "C:/x", "a//b"):
            with self.assertRaises(heldrun.HeldError, msg=rel):
                heldrun.inside(base, rel)


class PrepareTest(HeldCase):
    def test_nothing_is_fetched_before_the_signed_result_verifies(self):  # held_result_unverified
        """E510, `25a` 1: `hazir` takes a head only from a result Sigstore verified as the referee's main signed it; a
        result that does not verify fetches nothing and packs nothing."""
        signed = self.tmp / "signed"
        signed.mkdir()
        (signed / "result.json").write_text(RESULT, encoding="utf-8")
        (signed / "result.json.sigstore.json").write_text("{}", encoding="utf-8")
        referee = self.tmp / "referee"
        referee.mkdir()
        (referee / "bootstrap.json").write_text(json.dumps({
            "brain_repo": "owner/brain", "brain_branch": "main",
            "image": "docker.io/library/python:3.12-slim@sha256:" + "a" * 64,
            "rival": {"model": "claude-sonnet-5-5", "effort": "medium", "max_turns": 30,
                      "per_run_cap_usd_micros": 3_000_000},
            "limits": {"test_timeout_s": 600, "reproducer_timeout_s": 120, "max_prompt_chars": 600_000,
                       "max_tree_bytes": 50_000_000}}), encoding="utf-8")
        args = heldrun.build_parser().parse_args(
            ["prepare", "--referee", str(referee), "--referee-repo", "o/referee", "--signed", str(signed),
             "--exam", str(self.tmp / "exam"), "--held-set", "set", "--sigstore-python", "python3",
             "--work", str(self.tmp / "work"), "--out", str(self.tmp / "out")])
        fetched = RuntimeError("fetched")
        with mock.patch.object(heldrun, "verify_signature"), \
                mock.patch.object(heldrun.gitio, "fetch", side_effect=fetched) as fetch:
            with self.assertRaisesRegex(RuntimeError, "fetched"):  # a verified result is fetched
                args.func(args)
        self.assertEqual(fetch.call_args.args[1:], ("https://github.com/owner/brain.git", "main", HEAD))
        refused = ImportErrorStop("signature verification failed")
        with mock.patch.object(heldrun, "verify_signature", side_effect=refused) as verify, \
                mock.patch.object(heldrun.gitio, "fetch", side_effect=fetched) as fetch:
            with self.assertRaises(ImportErrorStop):
                args.func(args)
        self.assertEqual(verify.call_args.args[2], heldrun.referee_identity("o/referee"))
        fetch.assert_not_called()
        self.assertFalse((self.tmp / "out").exists())


class PollTest(HeldCase):
    """`poll` and `ledger-get` with GitHub's artifact calls stubbed: what is new, what is left to sign, what is carried,
    and a ledger taken only by the hash its job named."""

    def zipped(self, files):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for name, data in files.items():
                zf.writestr(name, data)
        return buf.getvalue()

    def ledger_zip(self, ledger):
        cli.pack_dir(ledger, self.tmp / "packed.tar")  # what `pack` uploads as the ledger artifact's one file
        return self.zipped({heldrun.LEDGER_TAR: (self.tmp / "packed.tar").read_bytes()})

    def poll(self, ledger_zip=None, age_days=0, result=RESULT):
        made = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=age_days)).isoformat()
        arts = {"o/referee": {"id": 1, "created_at": made},
                "o/exam": {"id": 2, "created_at": made} if ledger_zip else None}
        blobs = {1: self.zipped({"result.json": result, "result.json.sigstore.json": "{}"}), 2: ledger_zip}
        out = self.tmp / "github_output"
        out.write_text("", encoding="utf-8")
        env = {"GITHUB_REPOSITORY": "o/exam", "GH_TOKEN": "t", "REFEREE_TOKEN": "t", "GITHUB_OUTPUT": str(out)}
        with mock.patch.dict(heldrun.os.environ, env), \
                mock.patch.object(heldrun.ghapi, "latest_artifact", side_effect=lambda repo, name, token: arts[repo]), \
                mock.patch.object(heldrun.ghapi, "download_zip", side_effect=lambda repo, i, token: blobs[i]):
            argv = ["poll", "--referee-repo", "o/referee", "--out", str(self.tmp / "signed")]
            self.assertEqual(heldrun.main(argv), 0)
        return dict(line.split("=", 1) for line in out.read_text(encoding="utf-8").splitlines())

    def test_a_new_head_a_statement_to_sign_and_a_ledger_to_carry(self):
        self.assertEqual(self.poll(), {"new": "true", "carry": "false", "ledger": "none"})
        run = self.pipeline()
        blob = self.ledger_zip(run.ledger)
        sha = canon.sha256_hex(zipfile.ZipFile(io.BytesIO(blob)).read(heldrun.LEDGER_TAR))
        self.assertEqual(self.poll(blob), {"new": "false", "carry": "true", "ledger": f"2={sha}"})
        heldrun.sign_pending(run.ledger, lambda path, bundle: bundle.write_text("{}", encoding="utf-8"))
        signed = self.ledger_zip(run.ledger)
        self.assertEqual(self.poll(signed)["carry"], "false")
        self.assertEqual(self.poll(signed, age_days=heldrun.CARRY_DAYS)["carry"], "true")
        spec = json.dumps({"kind": "spec", "head": "d" * 40})
        self.assertEqual(self.poll(signed, result=spec)["new"], "false")
        other = json.dumps({"kind": "code", "head": "d" * 40})
        self.assertEqual(self.poll(signed, result=other)["new"], "true")

    def test_a_ledger_is_taken_only_by_the_hash_its_job_named(self):
        run = self.pipeline()
        blob = self.ledger_zip(run.ledger)
        sha = canon.sha256_hex(zipfile.ZipFile(io.BytesIO(blob)).read(heldrun.LEDGER_TAR))
        env = {"GITHUB_REPOSITORY": "o/exam", "GH_TOKEN": "t"}
        with mock.patch.dict(heldrun.os.environ, env), \
                mock.patch.object(heldrun.ghapi, "download_zip", return_value=blob):
            self.assertEqual(heldrun.main(["ledger-get", "--artifact", f"2={sha}", "--out", str(self.tmp / "a")]), 0)
            self.assertEqual(heldrun.read_ledger(self.tmp / "a"), heldrun.read_ledger(run.ledger))
            self.assertEqual(heldrun.main(["ledger-get", "--artifact", f"2={'0' * 64}", "--out", str(self.tmp / "b")]),
                             2)
            self.assertEqual(heldrun.read_ledger(self.tmp / "b"), [])
        self.assertEqual(heldrun.main(["ledger-get", "--artifact", "none", "--out", str(self.tmp / "c")]), 0)
        self.assertEqual(list((self.tmp / "c").iterdir()), [])


def held_job(name):
    return workflow_job(name, HELD_YML)


class HeldWorkflowTest(unittest.TestCase):
    JOBS = ("hazir", "imza", "kos", "yargi")

    def test_the_jobs_are_the_four_and_the_run_job_holds_nothing(self):  # run_job_has_permissions
        """E510, plan D5: `kos` runs brain code; it holds no token (`permissions: {}`), no secret and no environment,
        so a container escape there reaches the held inputs of one run and nothing else."""
        self.assertEqual(re.findall(r"(?m)^  ([a-z_]+):$", HELD_YML.split("\njobs:\n", 1)[1]), list(self.JOBS))
        self.assertIn("\npermissions: {}\n", HELD_YML)
        kos = held_job("kos")
        self.assertRegex(kos, r"(?m)^    permissions: \{\}  #")
        for word in ("secrets.", "environment:", "id-token", "contents:", "actions:", "github.token", "GH_TOKEN"):
            self.assertNotIn(word, kos)

    def test_brain_code_runs_only_where_no_token_is(self):
        """`tohum/08` 1: a job that holds a token or OIDC runs no brain code and starts no container."""
        for name in self.JOBS:
            job = held_job(name)
            runs_code = "heldrun run " in job or "docker" in job or "fetch-deps" in job
            self.assertEqual(runs_code, name == "kos", name)
            if name != "kos":
                self.assertRegex(job, r"(?m)^    permissions:\n(      [a-z-]+: (read|write)\n)+", name)

    def test_signed_at_a_runs_start_and_a_run_ends_before_the_next(self):  # held_sign_waits_for_the_run
        """E510: a statement's Rekor time is public. `imza` signs what an earlier run judged and waits for no job that
        runs brain code; every run ends long before the schedule starts the next, so the start of a run is the cron's,
        never the length of an earlier held run."""
        imza = held_job("imza")
        self.assertIn("    needs: hazir\n", imza)
        self.assertIn("      !cancelled() && needs.hazir.outputs.carry == 'true'\n", imza)  # past a failed `hazir` too
        self.assertNotIn("id-token", HELD_YML)  # E520: no certificate names this repository: held_job_has_oidc
        self.assertEqual([n for n in self.JOBS if "heldrun sign " in held_job(n)], ["imza"])
        self.assertNotIn("sigstore sign", HELD_YML)
        self.assertEqual([n for n in self.JOBS if "secrets.HELD_SIGNING" in held_job(n)], ["imza"])
        sign = imza.split("- name: Sign every statement left to sign", 1)[1].split("\n      - ", 1)[0]
        self.assertEqual(imza.count("secrets.HELD_SIGNING"), sign.count("secrets.HELD_SIGNING"))  # its step only
        self.assertIn('| sha256sum -c -', imza.split("cosign v2.4.1", 1)[1].split("\n      - ", 1)[0])
        cron = re.search(r'cron: "(\d+) \*/(\d+) \* \* \*"', HELD_YML)
        interval = int(cron.group(2)) * 60
        minutes = {n: int(re.search(r"timeout-minutes: (\d+)", held_job(n)).group(1)) for n in self.JOBS}
        longest = minutes["hazir"] + max(minutes["imza"], minutes["kos"]) + minutes["yargi"]
        self.assertLess(longest, interval)
        self.assertIn("cancel-in-progress: false", HELD_YML)
        self.assertLessEqual(vectors.BUDGET_S * 2, minutes["kos"] * 60)

    def test_every_artifact_is_read_by_the_hash_its_job_named(self):
        self.assertIn('echo "$IN_SHA  held-in.tar" | sha256sum -c -', held_job("kos"))
        yargi = held_job("yargi")
        for check in ('echo "$IN_SHA  held-in.tar" | sha256sum -c -', 'echo "$TRACE_SHA  trace.tar" | sha256sum -c -',
                      "IN_SHA: ${{ needs.hazir.outputs.in_sha }}", "TRACE_SHA: ${{ needs.kos.outputs.trace_sha }}"):
            self.assertIn(check, yargi)
        for name in ("imza", "yargi"):
            self.assertIn('heldrun ledger-get --artifact "$LEDGER"', held_job(name))
        retention = re.findall(r"name: ([a-z-]+)\n          path: [a-z.-]+\n          retention-days: (\d+)", HELD_YML)
        self.assertEqual(sorted(set(retention)), [("held-in", "1"), ("held-ledger", "8"), ("held-trace", "1")])
        self.assertLess(heldrun.CARRY_DAYS, 8)

    def test_every_command_parses_and_every_action_is_the_referees_pin(self):
        held_cmds = [shlex.split(re.sub(r"\$\{\{.*?\}\}", "X", m)) for line in run_blocks(HELD_YML)
                     for m in re.findall(r"-m snowball_bootstrap\.heldrun ([^|>]*)", line)]
        self.assertEqual(sorted({c[0] for c in held_cmds}), ["judge", "ledger-get", "poll", "prepare", "run", "sign"])
        for argv in held_cmds:
            heldrun.build_parser().parse_args(argv)
        referee_cmds = [shlex.split(m) for line in run_blocks(HELD_YML)
                        for m in re.findall(r"-m snowball_bootstrap ([^|>]*?)(?: \| | >> |$)", line)]
        self.assertEqual(sorted({c[0] for c in referee_cmds}), ["fetch-deps", "licenses", "pack"])
        for argv in referee_cmds:
            cli.build_parser().parse_args(argv)
        uses = set(re.findall(r"uses: (\S+)", HELD_YML))
        self.assertLessEqual(uses, set(re.findall(r"uses: (\S+)", BOOTSTRAP_YML)))
        self.assertTrue(all(re.fullmatch(r"[\w/-]+@[0-9a-f]{40}", u) for u in uses))

    def test_what_the_operator_sets_is_documented_and_no_exam_path_is_written(self):
        """The template is public; what it reads of the exam repository comes from the exam repository's own variables.
        Every variable and secret is named for the operator, and no context is pasted into a shell script (E17)."""
        names = set(re.findall(r"\$\{\{ (?:vars|secrets)\.([A-Z_]+)", HELD_YML))
        self.assertEqual(names, {"REFEREE_REPO", "HELD_SET", "REFEREE_READ_TOKEN", "HELD_SIGNING_KEY",
                                 "HELD_SIGNING_PASSWORD"})
        for name in names:
            self.assertIn(name, heldrun.__doc__)
            self.assertIn(name, HELD_YML.split("\nname:", 1)[0])
        for line in run_blocks(HELD_YML):
            self.assertNotIn("${{", line)
        self.assertEqual(re.findall(r"--held-set (\S+)", HELD_YML), ['"$HELD_SET"', '"$HELD_SET"'])
        self.assertNotIn("rehearsal", HELD_YML + heldrun.__doc__)


if __name__ == "__main__":
    unittest.main()
