# Record what the referee's vector judges sign on main, for a fixed set of runner answers.
# E533. Usage, from a checkout of the code to record: python -X utf8 record_judges.py seed/bootstrap OUT.json.gz LABEL
# (test_answers JudgeOutputBeforeThePinTest reads judges-main-4f58974.json.gz, recorded so on main 4f58974).
# Runner answers: the reference implementations (helpers.FakeRunner for the own judges, the reference brain run
# locally for the data groups), then deterministically disturbed by the input's sha256: kept, wrong, no answer,
# timed out, or the previous call's answer (a changed input answered like its case).
import gzip, hashlib, json, shlex, subprocess, sys, time
from pathlib import Path

boot = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(boot), str(boot / "tests")]
from snowball_bootstrap import stages, vectors  # noqa: E402
from snowball_bootstrap.container import RunResult  # noqa: E402
from helpers import FakeRunner  # noqa: E402

VEC = boot / "vectors"
BRAIN = boot / "local" / "reference_brain"
spec = json.loads((VEC / "vectors.json").read_text(encoding="utf-8"))
groups = [g for g in spec if isinstance(spec[g], dict) and g not in ("schema", "source")]
TABLE = stages.parse_table(json.dumps({"stage": 0, "mfs": [
    {"mf": 1, "tests": [13], "groups": groups, "module": "ledger/chain.py", "calls": []}]}), 0)
OWN = ("ledger.chain", "harness.stats", "harness.score", "harness.drill")


def local(cmd, stdin, timeout_s):
    argv = [sys.executable if p == "python" else VEC.as_posix() + p[len("/vec"):] if p.startswith("/vec/") else p
            for p in shlex.split(cmd)]
    proc = subprocess.run(argv, cwd=BRAIN / "referee", input=stdin, capture_output=True, timeout=60, check=False)
    return RunResult(proc.returncode, proc.stdout, proc.stderr, 1)


def disturb(line, mode):
    try:
        value = json.loads(line)
    except ValueError:
        return line
    if not isinstance(value, dict):
        return line

    def bend(v):
        if isinstance(v, bool):
            return not v
        if isinstance(v, int):
            return v + 1
        if isinstance(v, str):
            return v + "x"
        if isinstance(v, list):
            return v[:-1]
        if isinstance(v, dict):
            return {k: bend(x) for k, x in v.items()}
        return v
    keys = sorted(value)
    if mode == "wrong_one" and keys:
        value[keys[0]] = bend(value[keys[0]])
    elif mode == "wrong_all":
        value = {k: bend(v) for k, v in value.items()}
    elif mode == "drop_one" and keys:
        del value[keys[-1]]
    return json.dumps(value)


class Recorder:
    def __init__(self):
        self.fake = FakeRunner(VEC)
        self.tape = {}
        self.last = None

    def run(self, cmd, *, cwd=".", stdin=b"", timeout_s):
        key = vectors.input_key(cmd, stdin)
        if key in self.tape:
            t = self.tape[key]
            return RunResult(t["exit"], t["stdout"].encode(), t["stderr"].encode(), 1, timed_out=t["timed_out"])
        argv = shlex.split(cmd)
        res = self.fake.run(cmd, stdin=stdin, timeout_s=timeout_s) if argv[2:3] and argv[2] in OWN else \
            local(cmd, stdin, timeout_s)
        mode = ["keep", "keep", "keep", "wrong_one", "wrong_all", "drop_one", "none", "timeout", "previous"][
            hashlib.sha256(key.encode()).digest()[0] % 9]
        out, err, code, late = res.stdout.decode("utf-8", "replace"), res.stderr.decode("utf-8", "replace"), \
            res.exit_code, False
        lines = out.strip().splitlines()
        if mode.startswith(("wrong", "drop")) and lines:
            out = "\n".join(lines[:-1] + [disturb(lines[-1], mode)]) + "\n"
        elif mode == "none":
            out, err, code = "", "boom: no answer\n", 1
        elif mode == "timeout":
            out, err, code, late = "", "", 124, True
        elif mode == "previous" and self.last is not None:
            out, err, code = self.last
        self.tape[key] = {"exit": code, "stdout": out, "stderr": err[-300:], "timed_out": late, "mode": mode}
        if out.strip():
            self.last = (out, err[-300:], code)
        return RunResult(code, out.encode(), err[-300:].encode(), 1, timed_out=late)


rec = Recorder()
started = time.monotonic()
records = vectors.run_vectors(rec, VEC, (1,), table=TABLE)
doc = {"recorded_on": sys.argv[3] if len(sys.argv) > 3 else "", "groups": groups,
       "tape": rec.tape, "records": records}
with gzip.open(sys.argv[2], "wt", encoding="utf-8", compresslevel=9) as f:
    json.dump(doc, f, ensure_ascii=False, sort_keys=True, indent=0)
modes = {}
for t in rec.tape.values():
    modes[t["mode"]] = modes.get(t["mode"], 0) + 1
print(len(records), "records,", len(rec.tape), "inputs", modes, "fails", sum(1 for r in records if not r["ok"]),
      "passes with detail", sum(1 for r in records if r["ok"] and r["detail"]), f"{time.monotonic() - started:.0f}s")
