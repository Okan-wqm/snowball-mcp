"""The loop workflow's wiring rules (`asama-0/10` #is-akisi, `asama-0/09` test 46, `asama-0/14` MF17; `tohum/08`,
`01a`; E100, E162, E281-E283).

`referee/.github/workflows/` holds one file, `loop.yml` (`tohum/08` 1: the loop referee's jobs are in one workflow;
`13`). It is read with the seed's restricted YAML subset and held to test 46's rules. Only bytes are read; nothing of
the Founder's runs. `pull` checks it on every code push once the micro-feature that owns the workflow is finished, and
at the exit (`asama-0/14` MF17: "her push'ta ve (A)'da").

**The subset** (E281: no spec page defines it; the aim is that GitHub's parser and this one can never read the same
bytes differently, so anything that could be read two ways is refused). UTF-8 without a byte order mark, carriage
return, tab or other control character, and without the characters YAML 1.1 takes for line breaks (U+0085, U+2028,
U+2029). Block mappings whose keys match ``[A-Za-z_][A-Za-z0-9_-]*`` followed by ``:`` and a space or the end of the
line, no key twice; block sequences indented under their key; plain scalars on one line, without ``: `` or `` #`` and
not ending in ``:``; single-quoted scalars (``''`` is a quote) and double-quoted ones (``\\"`` and ``\\\\`` the only
escapes), each on one line with nothing after the closing quote; ``|`` literal blocks (clip: one final newline);
``{}`` and ``[]``; whole-line comments outside a literal block. Refused: anchors, aliases, tags, merge keys, document
markers and directives, folded and chomped blocks, non-empty flow collections, multi-line plain scalars, quoted or
complex keys, indentation that does not nest, nesting deeper than ``MAX_DEPTH``, files over ``MAX_BYTES``. Every
scalar is a string; ``persist-credentials: false`` is the string ``false``.

**The rules** (test 46). Top-level ``permissions`` is ``{}``. No ``pull_request_target``, ``workflow_run`` or
``issue_comment`` trigger, in the string, list or mapping form of ``on``. The jobs are `tohum/08`'s five and each has
``if: github.ref == 'refs/heads/main'`` exactly. No ``${{ }}`` expression in a ``run:`` names the ``github`` context
(E17: through ``env:`` it is data, not script). Every ``uses:`` is ``owner/repo[/path]@<40 hex>``. Every
``actions/checkout`` step sets ``persist-credentials: false``. "No secret-bearing job runs code" cannot be decided by
reading the file (E283); the decidable reading is `tohum/08` and `01a`'s table of which job does what: the jobs that
run code (`getir`, `koş`) have ``permissions: {}`` and no secret; secrets, ``id-token`` and write scopes appear only in
`çağır` and `yaz`; nothing enumerates or inherits the secrets.

**Not decided here** (E282): "every job's first step is the seed's `control` command and stops the job while the kill
switch is on". The seed's `control` command has no interface for the loop yet (`asama-0/01` D0, `asama-1/13`), so no
file can be held to it; `decide.EXIT_NOT_CHECKED` keeps the exit closed on it by name.
"""

from __future__ import annotations

import re
from typing import Any

from . import stages

WORKFLOW_DIR = "referee/.github/workflows"
WORKFLOW_FILE = "loop.yml"
MODULE = ".github/workflows/loop.yml"  # the module of the stage table's loop workflow micro-feature (MF17)
JOBS = ("cek", "getir", "kos", "cagir", "yaz")
CODE_JOBS = ("getir", "kos")
SECRET_JOBS = ("cagir", "yaz")
MAIN_ONLY = "github.ref == 'refs/heads/main'"
FORBIDDEN_EVENTS = ("pull_request_target", "workflow_run", "issue_comment")
MAX_BYTES = 256 * 1024
MAX_DEPTH = 32
MAX_REASONS = 40

KEY_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*):(?: +|\Z)")
PINNED_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_./-]+)?@[0-9a-f]{40}\Z")
EXPRESSION_RE = re.compile(r"\$\{\{(.*?)(?:\}\}|\Z)", re.S)
INDICATORS = set("&*!|>%@`,?#[]{}")
LINE_BREAKS = (chr(0x85), chr(0x2028), chr(0x2029))  # line breaks to YAML 1.1, ordinary text to YAML 1.2
BOM = chr(0xFEFF)


class Unparseable(ValueError):
    """The bytes are outside the subset. ``line`` is 1-based (0: the file as a whole); ``why`` a short word."""

    def __init__(self, line: int, why: str):
        super().__init__(f"line {line}: {why}")
        self.line, self.why = line, why


def _printable(ch: str) -> bool:
    code = ord(ch)
    if ch == "\n" or 0x20 <= code <= 0x7E:
        return True
    return code >= 0xA0 and ch not in LINE_BREAKS and ch != BOM and code not in (0xFFFE, 0xFFFF)


def _scalar(text: str, line: int) -> Any:
    """One scalar written on one line (already stripped of the spaces around it)."""
    if text in ("{}", "[]"):
        return {} if text == "{}" else []
    head = text[0]
    if head == "'":
        out, k = [], 1
        while True:
            q = text.find("'", k)
            if q < 0:
                raise Unparseable(line, "unterminated_quote")
            out.append(text[k:q])
            if text[q + 1:q + 2] == "'":
                out.append("'")
                k = q + 2
                continue
            if text[q + 1:]:
                raise Unparseable(line, "text_after_quote")
            return "".join(out)
    if head == '"':
        out, k = [], 1
        while k < len(text):
            ch = text[k]
            if ch == "\\":
                if text[k + 1:k + 2] not in ('"', "\\"):
                    raise Unparseable(line, "escape")
                out.append(text[k + 1])
                k += 2
            elif ch == '"':
                if text[k + 1:]:
                    raise Unparseable(line, "text_after_quote")
                return "".join(out)
            else:
                out.append(ch)
                k += 1
        raise Unparseable(line, "unterminated_quote")
    if head in INDICATORS or text in ("-", ":") or text.startswith(("- ", ": ")):
        raise Unparseable(line, "indicator")
    if ": " in text or text.endswith(":") or " #" in text:
        raise Unparseable(line, "plain_scalar")
    return text


class _Reader:
    def __init__(self, lines: list[str]):
        self.lines = lines
        self.inner: dict[int, tuple[int, str]] = {}  # a sequence entry's content, read as a line of its own

    def at(self, i: int) -> tuple[int, str]:
        if i in self.inner:
            return self.inner[i]
        raw = self.lines[i]
        text = raw.lstrip(" ")
        return len(raw) - len(text), text.rstrip(" ")

    def next(self, i: int) -> int:
        """The first line from ``i`` that is neither blank nor a whole-line comment."""
        while i < len(self.lines):
            indent, text = self.at(i)
            if text and not text.startswith("#"):
                if indent == 0 and text.startswith(("---", "...", "%")):
                    raise Unparseable(i + 1, "document_marker")
                return i
            i += 1
        return i

    def document(self) -> Any:
        i = self.next(0)
        if i >= len(self.lines):
            raise Unparseable(0, "empty")
        if self.at(i)[0] != 0:
            raise Unparseable(i + 1, "indentation")
        value, i = self.node(i, 0, 1)
        i = self.next(i)
        if i < len(self.lines):
            raise Unparseable(i + 1, "indentation")
        return value

    def node(self, i: int, indent: int, depth: int) -> tuple[Any, int]:
        if depth > MAX_DEPTH:
            raise Unparseable(i + 1, "too_deep")
        text = self.at(i)[1]
        if text == "-" or text.startswith("- "):
            return self.sequence(i, indent, depth)
        return self.mapping(i, indent, depth)

    def nested(self, i: int, indent: int, depth: int) -> tuple[Any, int]:
        """The block under a key or a bare ``-`` on line ``i - 1``: more indented, or nothing (null)."""
        j = self.next(i)
        if j < len(self.lines) and self.at(j)[0] > indent:
            return self.node(j, self.at(j)[0], depth + 1)
        return None, i

    def literal(self, i: int, indent: int) -> tuple[str, int]:
        """A ``|`` block: its lines are more indented than ``indent``, the first one sets the block's indentation."""
        if i >= len(self.lines) or not self.lines[i].strip(" ") or self.at(i)[0] <= indent:
            raise Unparseable(i, "empty_literal")
        block, out = self.at(i)[0], []
        while i < len(self.lines):
            raw = self.lines[i]
            if raw == "":
                out.append("")
            elif not raw.strip(" "):
                raise Unparseable(i + 1, "blank_line_with_spaces")
            elif len(raw) - len(raw.lstrip(" ")) >= block:
                out.append(raw[block:])
            else:
                break
            i += 1
        while out and out[-1] == "":
            out.pop()
            i -= 1
        return "\n".join(out) + "\n", i

    def mapping(self, i: int, indent: int, depth: int) -> tuple[dict[str, Any], int]:
        out: dict[str, Any] = {}
        while True:
            i = self.next(i)
            if i >= len(self.lines):
                return out, i
            at, text = self.at(i)
            if at < indent:
                return out, i
            if at > indent:
                raise Unparseable(i + 1, "indentation")
            match = KEY_RE.match(text)
            if not match:
                raise Unparseable(i + 1, "not_a_key")
            key, rest = match.group(1), text[match.end():]
            if key in out:
                raise Unparseable(i + 1, "duplicate_key")
            if rest == "":
                out[key], i = self.nested(i + 1, indent, depth)
            elif rest == "|":
                out[key], i = self.literal(i + 1, indent)
            else:  # a line more indented than its key after it is a multi-line scalar: refused as indentation
                out[key], i = _scalar(rest, i + 1), i + 1

    def sequence(self, i: int, indent: int, depth: int) -> tuple[list[Any], int]:
        out: list[Any] = []
        while True:
            i = self.next(i)
            if i >= len(self.lines):
                return out, i
            at, text = self.at(i)
            if at < indent:
                return out, i
            if at > indent:
                raise Unparseable(i + 1, "indentation")
            if text == "-":
                value, i = self.nested(i + 1, indent, depth)
            elif text.startswith("- "):
                body = text[2:].lstrip(" ")
                column = at + len(text) - len(body)
                if KEY_RE.match(body) or body == "-" or body.startswith("- "):
                    self.inner[i] = (column, body)
                    value, i = self.node(i, column, depth + 1)
                else:
                    value, i = _scalar(body, i + 1), i + 1
            else:
                raise Unparseable(i + 1, "not_an_entry")
            out.append(value)


def parse(data: bytes) -> Any:
    """Read a workflow in the subset; Unparseable for anything outside it."""
    if len(data) > MAX_BYTES:
        raise Unparseable(0, "too_large")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise Unparseable(0, "not_utf8") from None
    for number, line in enumerate(text.split("\n"), start=1):
        bad = next((ch for ch in line if not _printable(ch)), None)
        if bad is not None:
            why = {"\r": "carriage_return", "\t": "tab", BOM: "byte_order_mark"}.get(bad, "control_character")
            raise Unparseable(number, why)
    lines = text.split("\n")
    if lines[-1] == "":
        lines.pop()
    return _Reader(lines).document()


def _expressions(text: str) -> list[str]:
    return [m.group(1) for m in EXPRESSION_RE.finditer(text)]


def _names(expression: str, context: str) -> list[re.Match[str]]:
    """Where an expression names a context (case-insensitively, as GitHub reads contexts)."""
    return list(re.finditer(rf"(?<![\w.-]){context}(?![\w-])", expression, re.I))


def _strings(node: Any, key: str = "") -> list[tuple[str, str]]:
    """Every string under ``node`` with the key it is the value of (a sequence item has its parent's key)."""
    if isinstance(node, dict):
        return [found for k, v in node.items() for found in _strings(v, k)]
    if isinstance(node, list):
        return [found for v in node for found in _strings(v, key)]
    return [(key, node)] if isinstance(node, str) else []


def _expressions_in(node: Any) -> list[str]:
    """The expressions under ``node``: every ``${{ }}``, and the whole of an ``if:`` (an expression without them)."""
    found: list[str] = []
    for key, text in _strings(node):
        found += _expressions(text)
        if key == "if":
            found.append(text)
    return found


def _uses_secrets(node: Any) -> bool:
    return (isinstance(node, dict) and "secrets" in node) or any(_names(e, "secrets") for e in _expressions_in(node))


def _enumerates_secrets(node: Any) -> bool:
    """``secrets: inherit``, ``toJSON(secrets)``, ``secrets[...]`` or the bare context: every secret at once."""
    if isinstance(node, dict) and node.get("secrets") == "inherit":
        return True
    for expression in _expressions_in(node):
        for match in _names(expression, "secrets"):
            if not re.match(r"\s*\.\s*[A-Za-z_]", expression[match.end():]):
                return True
    return False


def _grants(permissions: Any) -> bool:
    """Whether a job's permissions give more than reading: a write scope, an OIDC token, or anything unknown."""
    if permissions is None:
        return False  # inherited from the top level, which must be {}
    if isinstance(permissions, str):
        return permissions != "read-all"
    if not isinstance(permissions, dict):
        return True
    return any(value not in ("read", "none") or (scope == "id-token" and value != "none")
               for scope, value in permissions.items())


def _rules(doc: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if doc.get("permissions") != {}:
        reasons.append("workflow_top_permissions")
    on = doc.get("on")
    if isinstance(on, str):
        events = [on]
    elif isinstance(on, list) and all(isinstance(e, str) for e in on):
        events = on
    elif isinstance(on, dict):
        events = list(on)
    else:
        events = []
        reasons.append("workflow_trigger:none" if on is None else "workflow_trigger:unreadable")
    reasons += [f"workflow_trigger:{e}" for e in events if e.casefold() in FORBIDDEN_EVENTS]
    outside = {k: v for k, v in doc.items() if k != "jobs"}
    if _uses_secrets(outside):
        reasons.append("workflow_secret_job:workflow")  # the top-level env reaches every job, code jobs too
    if _enumerates_secrets(outside):
        reasons.append("workflow_secrets_enumerated:workflow")
    jobs = doc.get("jobs")
    if not isinstance(jobs, dict):
        return reasons + ["workflow_shape:jobs"]
    reasons += [f"workflow_unknown_job:{name}" for name in jobs if name not in JOBS]
    reasons += [f"workflow_missing_job:{name}" for name in JOBS if name not in jobs]
    for name, job in jobs.items():
        if not isinstance(job, dict):
            reasons.append(f"workflow_shape:{name}")
            continue
        if job.get("if") != MAIN_ONLY:
            reasons.append(f"workflow_job_not_main_only:{name}")
        if "uses" in job and not (isinstance(job["uses"], str) and PINNED_RE.match(job["uses"])):
            reasons.append(f"workflow_action_not_pinned:{name}:job")
        steps = job.get("steps", [])
        if not isinstance(steps, list):
            reasons.append(f"workflow_shape:{name}")
            steps = []
        for number, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                reasons.append(f"workflow_shape:{name}:{number}")
                continue
            run = step.get("run")
            if run is not None and (not isinstance(run, str) or any(_names(e, "github") for e in _expressions(run))):
                reasons.append(f"workflow_github_in_run:{name}:{number}")
            uses = step.get("uses")
            if uses is None:
                continue
            if not isinstance(uses, str) or not PINNED_RE.match(uses):
                reasons.append(f"workflow_action_not_pinned:{name}:{number}")
            elif uses.split("@", 1)[0].casefold() == "actions/checkout":
                options = step.get("with")
                if not isinstance(options, dict) or options.get("persist-credentials") != "false":
                    reasons.append(f"workflow_persist_credentials:{name}:{number}")
        secret = _uses_secrets(job)
        if name in CODE_JOBS:
            if job.get("permissions") != {}:
                reasons.append(f"workflow_code_job_permissions:{name}")
            if secret:
                reasons.append(f"workflow_secret_in_code_job:{name}")
        elif name not in SECRET_JOBS and (secret or _grants(job.get("permissions"))):
            reasons.append(f"workflow_secret_job:{name}")
        if _enumerates_secrets(job):
            reasons.append(f"workflow_secrets_enumerated:{name}")
    return reasons


def check(files: dict[str, bytes]) -> list[str]:
    """Why the files of ``referee/.github/workflows/`` (keyed by their path inside it) break the wiring rules."""
    reasons = [f"workflow_extra_file:{name}" for name in sorted(files) if name != WORKFLOW_FILE]
    if WORKFLOW_FILE not in files:
        return reasons + [f"workflow_missing:{WORKFLOW_FILE}"]
    try:
        doc = parse(files[WORKFLOW_FILE])
    except Unparseable as exc:
        return reasons + [f"workflow_unparseable:{WORKFLOW_FILE}:L{exc.line}:{exc.why}"]
    if not isinstance(doc, dict):
        return reasons + [f"workflow_unparseable:{WORKFLOW_FILE}:L1:not_a_mapping"]
    return (reasons + _rules(doc))[:MAX_REASONS]


def files_in(referee: dict[str, bytes]) -> dict[str, bytes]:
    """The workflow directory's files among ``referee/``'s, keyed by their path inside the directory."""
    prefix = WORKFLOW_DIR + "/"
    return {path[len(prefix):]: content for path, content in referee.items() if path.startswith(prefix)}


def due(table: stages.StageTable, done: tuple[int, ...] | list[int]) -> bool:
    """Whether a code push is held to the rules: the micro-feature whose module is the loop workflow is finished."""
    return any(f.module == MODULE and f.mf in set(done) for f in table.mfs)
