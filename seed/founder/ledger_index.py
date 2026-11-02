"""A read-only index of the Founder's ledger, in the capsule (register E506; the owner's decision on gap D, 2026-11-02).

    python3 -I /opt/founder/ledger_index.py <command> [options] [--ledger PATH]

Every call reads the ledger's bytes once and answers from them; nothing is written or kept anywhere, so there is no
cache to go stale and no copy to plant. Every answer's first line says which bytes it read (size, sha256, readable rows,
the last readable row) and that it judged no chain: links, row hashes and the meaning rules are the referee's and the
Founder's own check. Stdlib only, and nothing of the seed's code is imported.

Two tiers. The exact tier answers by field value, and what it finds is what a scan of every line by the same rule finds
(`seed/bootstrap/tests/test_ledger_index.py` holds it to an independent oracle). The text tier matches literal strings
in the free text and gives candidates only.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import re
import sys

TOOL = "ledger_index/1"
DEFAULT_LEDGER = "/work/brain/founder-ledger.jsonl"
LIMIT, LIMIT_MAX = 40, 200
BUDGET = 24_000  # UTF-8 bytes of one answer, header included: the CLI shows only a preview of a larger output
HEAD = 200  # characters of a summary, and of any other string, in a compact row
UNREADABLE_LISTED = 20
FIELDS = {"kind": "kind", "part": "part", "derivation": "derivation", "trust": "trust", "row": "row_id",
          "hash": "row_hash", "supersedes": "supersedes"}
KEYS = (*FIELDS, "commit", "day", "path", "report", "tag")
NOT_A_PATH = re.compile(r"[a-z_]+:(?![0-9])")
TAG = re.compile(r"([a-z_]+):(?![0-9])(.+)\Z", re.DOTALL)
SPAN = re.compile(r":[0-9]+(?:-[0-9]+)?\Z")
REPORT = re.compile(r"reports/([^/]+)\.json\Z", re.DOTALL)
HEX_PREFIX = re.compile(r"[0-9a-f]{7,}\Z")
ROW_ID = re.compile(r"f[0-9]+\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
WORD = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
CLOSING_RULE = "structural: the closer's own validity is not judged"


class Unreadable(ValueError):
    """Why one line is not read as a row; the message is the rule's name."""


def _unique(pairs: list) -> dict:
    found: dict = {}
    for key, value in pairs:
        if key in found:
            raise Unreadable("duplicate_key")  # a later key never hides an earlier one
        found[key] = value
    return found


def _constant(_name: str):
    raise Unreadable("noncanonical")  # NaN, Infinity, -Infinity


def read_line(raw: bytes) -> dict:
    """One line as a row, or Unreadable with the rule's name. Nothing else is judged here."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise Unreadable("not_utf8") from None
    try:
        row = json.loads(text, object_pairs_hook=_unique, parse_constant=_constant)
    except Unreadable:
        raise
    except RecursionError:
        raise Unreadable("too_deep") from None
    except json.JSONDecodeError:
        raise Unreadable("not_json") from None
    except ValueError:  # an integer longer than Python reads
        raise Unreadable("noncanonical") from None
    if not isinstance(row, dict):
        raise Unreadable("not_json")
    return row


class Ledger:
    """The bytes read, split on LF; each line read once. Line numbers count from 1 and are the identity throughout."""

    def __init__(self, path: str, data: bytes) -> None:
        self.path, self.size = path, len(data)
        self.sha256 = hashlib.sha256(data).hexdigest()
        self.lines = data.split(b"\n")
        partial = self.lines.pop()  # empty when the last line ends with its newline
        self.rows: list[tuple[int, dict]] = []
        self.unreadable: list[dict] = []
        for number, raw in enumerate(self.lines, start=1):
            try:
                self.rows.append((number, read_line(raw)))
            except Unreadable as exc:
                self.unreadable.append({"line": number, "rule": str(exc)})
        if partial:  # not appended yet: a row ends with its newline
            self.lines.append(partial)
            self.unreadable.append({"line": len(self.lines), "rule": "unterminated"})
        self.by_line = dict(self.rows)
        self._index: dict[str, dict[str, list[tuple[int, str]]]] = {}

    def index(self, key: str) -> dict[str, list[tuple[int, str]]]:
        """One exact key's index, built from every readable row the first time it is asked for: each value, in the
        order first seen, with the (line, field) pairs that hold it in line order. A row holding a value twice is
        there twice; the readers count lines."""
        if key not in self._index:
            postings: dict[str, list[tuple[int, str]]] = {}
            for line, row in self.rows:
                for value, where in values(row, key):
                    postings.setdefault(value, []).append((line, where))
            self._index[key] = postings
        return self._index[key]

    def tip(self) -> dict | None:
        if not self.rows:
            return None
        line, row = self.rows[-1]
        return {"line": line, "row_id": _text(row.get("row_id")), "row_hash": _text(row.get("row_hash"))}

    def header(self) -> dict:
        return {"tool": TOOL, "ledger": self.path, "bytes": self.size, "sha256": self.sha256, "rows": len(self.rows),
                "tip": self.tip(), "verified": False, "complete": not self.unreadable,
                "unreadable": self.unreadable[:UNREADABLE_LISTED], "unreadable_count": len(self.unreadable)}


# ---- what a row holds, by exact key -----------------------------------------------------------------------------
def _text(value):
    return value if isinstance(value, str) else None


def _clip(value):
    return value[:HEAD] if isinstance(value, str) else None


def summary(row: dict) -> str | None:
    payload = row.get("payload")
    return _text(payload.get("summary")) if isinstance(payload, dict) else None


def refs(row: dict) -> list[str]:
    payload = row.get("payload")
    found = payload.get("refs") if isinstance(payload, dict) else None
    return [ref for ref in found if isinstance(ref, str)] if isinstance(found, list) else []


def paths(row: dict) -> list[tuple[str, str]]:
    """(path, where) for every path the row names: a ref that is no `word:` tag, its `:n` or `:n-m` cut off, and each
    evidence_refs[].path. Compared byte for byte; no case folding."""
    out = []
    for ref in refs(row):
        if not NOT_A_PATH.match(ref):
            path = SPAN.sub("", ref)
            if path:
                out.append((path, "refs"))
    evidence = row.get("evidence_refs")
    for item in evidence if isinstance(evidence, list) else ():
        path = item.get("path") if isinstance(item, dict) else None
        if isinstance(path, str) and path:
            out.append((path, "evidence_refs"))
    return out


def tags(row: dict) -> list[tuple[str, str]]:
    """(tag, value) of every ref `<tag>:<value>` whose value does not start with a digit. No tag has a meaning here."""
    return [(m.group(1), m.group(2)) for m in map(TAG.match, refs(row)) if m]


def values(row: dict, key: str) -> list[tuple[str, str]]:
    """(value, the field it came from) of one exact key."""
    if key in FIELDS:
        value = _text(row.get(FIELDS[key]))
        return [(value, FIELDS[key])] if value is not None else []
    if key == "commit":
        value = _text(row.get("snapshot_id"))
        return [(value, "snapshot_id")] if value is not None else []
    if key == "day":
        value = _text(row.get("ts"))
        return [(value[:10], "ts")] if value is not None else []
    if key == "path":
        return paths(row)
    if key == "report":
        return [(m.group(1), where) for path, where in paths(row) for m in [REPORT.match(path)] if m]
    if key == "tag":
        return [(f"{tag}:{value}", "refs") for tag, value in tags(row)]
    raise ValueError(key)


def matches(how: str, value: str, query: str) -> bool:
    if how == "commit" and HEX_PREFIX.match(query):
        return value.startswith(query)
    if how == "under":
        return value.startswith(query)
    if how == "report":
        return value == query or value.startswith(query + "-")
    return value == query


def lookup(ledger: Ledger, how: str, query) -> dict[int, set[str]]:
    """The lines one (how, query) matches, each with the fields that held the match. An equality query is one
    lookup in the key's index; a prefix query reads the key's distinct values, never the rows again."""
    if how == "line":
        return {query: {"line"}} if query in ledger.by_line else {}
    index = ledger.index("path" if how == "under" else how)
    prefixed = how in ("commit", "under", "report")  # these may match more values than the query itself
    names = [value for value in index if matches(how, value, query)] if prefixed else [query]
    found: dict[int, set[str]] = {}
    for value in names:
        for line, where in index.get(value, ()):
            found.setdefault(line, set()).add(where)
    return found


def find(ledger: Ledger, groups: list[list[tuple[str, object]]]) -> list[tuple[int, dict, list[str]]]:
    """The rows every group matches (AND), in line order, once each; a group is (how, query) pairs, any one of which
    may match (OR); `how` is a key, `line` or `under`. With no group every readable row matches."""
    hits: dict[int, set[str]] | None = None
    for group in groups:
        found: dict[int, set[str]] = {}
        for how, query in group:
            for line, where in lookup(ledger, how, query).items():
                found.setdefault(line, set()).update(where)
        hits = found if hits is None else {line: hits[line] | found[line] for line in hits if line in found}
    if hits is None:
        return [(line, row, []) for line, row in ledger.rows]
    return [(line, ledger.by_line[line], sorted(hits[line])) for line in sorted(hits)]


# ---- the text tier ------------------------------------------------------------------------------------------------
def texts(row: dict) -> list[tuple[str, str]]:
    out = [(text, "summary") for text in [summary(row)] if text is not None]
    out += [(ref, "refs") for ref in refs(row)]
    out += [(text, "snapshot_id") for text in [_text(row.get("snapshot_id"))] if text is not None]
    return out


def contains(hay: str, term: str, fold: bool, token: bool) -> bool:
    """Whether the literal term is in hay: no pattern language, so no term can make it slow or match by accident."""
    if fold:
        hay, term = hay.casefold(), term.casefold()
    at = hay.find(term)
    while at != -1:
        end = at + len(term)
        if not token or ((at == 0 or hay[at - 1] not in WORD) and (end == len(hay) or hay[end] not in WORD)):
            return True
        at = hay.find(term, at + 1)
    return False


def text_hits(ledger: Ledger, terms: list[str], fold: bool, token: bool, only=None) -> list[tuple[int, dict, list]]:
    out = []
    for line, row in ledger.rows:
        via = sorted({where for text, where in texts(row) if (only is None or where in only)
                      and any(contains(text, term, fold, token) for term in terms)})
        if via:
            out.append((line, row, via))
    return out


# ---- folds --------------------------------------------------------------------------------------------------------
def brief(line: int, row: dict) -> dict:
    return {"line": line, "row_id": _clip(row.get("row_id")), "kind": _clip(row.get("kind"))}


def compact(line: int, row: dict, via: list | None = None) -> dict:
    head = summary(row)
    out = {"line": line, "row_id": _clip(row.get("row_id")), "kind": _clip(row.get("kind")), "ts": _clip(row.get("ts")),
           "head": head[:HEAD] if head is not None else None}
    if via is not None:
        out["via"] = via
    return out


def unclosed(ledger: Ledger, tag: str, kinds: list[str], everything: bool) -> list[tuple[int, dict]]:
    """Each row of a kind in `kinds` with what names it by `<tag>:<its row_id>`: a later namer closes it, an earlier
    one never does. The closer's own validity is not judged."""
    named, ids = ledger.index("tag"), ledger.index("row")
    out = []
    for line, row in ledger.rows:
        rid = row.get("row_id")
        if row.get("kind") not in kinds or not isinstance(rid, str):
            continue
        namers = list(dict.fromkeys(at for at, _where in named.get(f"{tag}:{rid}", ())))  # a row naming it twice: once
        closers = [brief(at, ledger.by_line[at]) for at in namers if at > line]
        if closers and not everything:
            continue
        item = compact(line, row)
        item.update(closed_by=closers, early=[brief(at, ledger.by_line[at]) for at in namers if at <= line],
                    ambiguous=len(ids[rid]) > 1)
        out.append((line, item))
    return out


def sessions(ledger: Ledger) -> list[dict]:
    """session_start and session_end rows paired in line order: a start with no end before the next start or the
    file's end is unfinished; an end with no open start is an orphan."""
    out: list[dict] = []
    current: dict | None = None
    for line, row in ledger.rows:
        kind = row.get("kind")
        if kind == "session_start":
            if current is not None:
                out.append(current)  # unfinished
            current = {"line": line, "state": "unfinished", "start": compact(line, row), "end": None}
        elif kind == "session_end":
            if current is None:
                out.append({"line": line, "state": "orphan_end", "start": None, "end": compact(line, row)})
            else:
                current.update(state="finished", end=compact(line, row))
                out.append(current)
                current = None
    if current is not None:
        out.append(current)
    return out


# ---- answers ------------------------------------------------------------------------------------------------------
def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def size(text: str) -> int:
    return len(text.encode("utf-8", "backslashreplace")) + 1


def paged(head: dict, items: list[tuple[int, dict]], args, default: str) -> list[str]:
    """Header and items, one JSON line each: `count` is every match; a page ends at --limit or at BUDGET bytes, and
    `next` is the exact --before/--after argument for the rest (null when nothing is left)."""
    order = args.order or default
    rest = [(line, item) for line, item in items
            if (args.before is None or line < args.before) and (args.after is None or line > args.after)]
    if order == "newest":
        rest.reverse()
    head.update(count=len(items), shown=0, order=order, next="--before " + "9" * 15)
    room = BUDGET - size(dumps(head))
    shown: list[str] = []
    for line, item in rest[:args.limit]:
        text = dumps(item)
        if shown and size(text) > room:
            break
        shown.append(text)
        room -= size(text)
    last = rest[len(shown) - 1][0] if shown else None
    more = len(rest) > len(shown)
    cursor = f"--before {last}" if order == "newest" else f"--after {last}"
    head.update(shown=len(shown), next=cursor if more else None)
    return [dumps(head), *shown]


def text_also(ledger: Ledger, terms: list[str]) -> dict:
    return {"tier": "text", "guarantee": "none", "terms": terms,
            "count": len(text_hits(ledger, terms, False, False, only=("summary",)))}


def cmd_find(ledger: Ledger, args, groups=None, query=None, default="newest") -> list[str]:
    if groups is None:
        query = {key: getattr(args, key) for key in (*KEYS, "line", "under") if getattr(args, key)}
        groups = [[(key, q) for q in query[key]] for key in (*KEYS, "line") if key in query and key != "path"]
        path = [("path", q) for q in query.get("path", [])] + [("under", q) for q in query.get("under", [])]
        groups += [path] if path else []
    head = {**ledger.header(), "query": query, "tier": "exact"}
    terms = [q for key in ("commit", "path", "under", "report") for q in query.get(key, [])]
    if terms:  # a commit, a path or a report named only in prose is in the text tier alone
        head["text_also"] = text_also(ledger, terms)
    return paged(head, [(line, compact(line, row, via)) for line, row, via in find(ledger, groups)], args, default)


def cmd_history(ledger: Ledger, args) -> list[str]:
    if not args.path and not args.under:
        raise Usage("history needs a PATH or --under DIR/")
    query = {"path": [args.path]} if args.path else {}
    query.update({"under": args.under} if args.under else {})
    groups = [[("path", q) for q in query.get("path", [])] + [("under", q) for q in query.get("under", [])]]
    return cmd_find(ledger, args, groups, query, default="oldest")


def cmd_named(ledger: Ledger, args) -> list[str]:
    target = args.target
    if ROW_ID.match(target):
        ids = {target} | {row["row_hash"] for _l, row in ledger.rows
                          if row.get("row_id") == target and isinstance(row.get("row_hash"), str)}
    elif HASH.match(target):
        ids = {target} | {row["row_id"] for _l, row in ledger.rows
                          if row.get("row_hash") == target and isinstance(row.get("row_id"), str)}
    else:
        raise Usage("named takes fN or a 64-hex row_hash")
    via: dict[int, set[str]] = {}
    for value, holders in ledger.index("tag").items():
        tag, _colon, name = value.partition(":")
        for line, _where in holders if name in ids else ():
            via.setdefault(line, set()).add(f"refs:{tag}")
    for name in ids:
        for line, _where in ledger.index("supersedes").get(name, ()):
            via.setdefault(line, set()).add("supersedes")
    items = [(line, compact(line, ledger.by_line[line], sorted(via[line]))) for line in sorted(via)]
    head = {**ledger.header(), "query": {"named": target, "names": sorted(ids)}, "tier": "exact"}
    return paged(head, items, args, "newest")


def cmd_unclosed(ledger: Ledger, args) -> list[str]:
    if not re.fullmatch(r"[a-z_]+", args.tag):
        raise Usage("--tag is the word before ':' in a ref, [a-z_]+")
    kinds = [k for k in args.kinds.split(",") if k]
    head = {**ledger.header(), "query": {"tag": args.tag, "kinds": kinds, "all": args.all}, "tier": "exact",
            "rule": CLOSING_RULE}
    return paged(head, unclosed(ledger, args.tag, kinds, args.all), args, "newest")


def cmd_sessions(ledger: Ledger, args) -> list[str]:
    found = sessions(ledger)
    head = {**ledger.header(), "tier": "exact", "sessions": sum(1 for s in found if s["start"]),
            "finished": sum(1 for s in found if s["state"] == "finished"),
            "unfinished": [s["line"] for s in found if s["state"] == "unfinished"],
            "orphan_end": [s["line"] for s in found if s["state"] == "orphan_end"]}
    if args.last is None:
        head["query"] = {"sessions": True}
        return paged(head, [(s["line"], s) for s in found], args, "newest")
    starts = [s["line"] for s in found if s["start"]]
    since = starts[-args.last] if args.last <= len(starts) else (starts[0] if starts else None)
    head["query"] = {"last": args.last, "from_line": since}
    rows = [(line, compact(line, row)) for line, row in ledger.rows if since is not None and line >= since]
    return paged(head, rows, args, "oldest")


def cmd_tail(ledger: Ledger, args) -> list[str]:
    above = [(line, row) for line, row in ledger.rows if args.before is None or line < args.before]
    picked = above[-args.n:]
    head = {**ledger.header(), "query": {"tail": args.n, "before": args.before}, "tier": "exact",
            "count": len(picked), "shown": 0, "next": "--before " + "9" * 15}
    room = BUDGET - size(dumps(head))
    shown: list[tuple[int, str]] = []
    for line, row in reversed(picked):  # the newest that fit, printed in file order
        text = dumps(compact(line, row))
        if shown and size(text) > room:
            break
        shown.append((line, text))
        room -= size(text)
    shown.reverse()
    more = len(shown) < len(above)  # older rows than the page holds: --before continues
    head.update(shown=len(shown), next=f"--before {shown[0][0]}" if shown and more else None)
    return [dumps(head), *(text for _line, text in shown)]


def cmd_keys(ledger: Ledger, args) -> list[str]:
    found = []
    for value, holders in ledger.index(args.key).items():
        lines = list(dict.fromkeys(line for line, _where in holders))
        found.append({"value": value, "rows": len(lines), "first": lines[0], "last": lines[-1]})
    ranked = sorted(found, key=lambda e: (-e["rows"], e["first"]))
    head = {**ledger.header(), "query": {"key": args.key}, "tier": "exact", "count": len(ranked), "shown": 0,
            "next": "--skip " + "9" * 15}
    room = BUDGET - size(dumps(head))
    shown: list[str] = []
    for entry in ranked[args.skip:args.skip + args.top]:
        text = dumps(entry)
        if shown and size(text) > room:
            break
        shown.append(text)
        room -= size(text)
    end = args.skip + len(shown)
    head.update(shown=len(shown), next=f"--skip {end}" if end < len(ranked) else None)
    return [dumps(head), *shown]


def cmd_text(ledger: Ledger, args) -> list[str]:
    if any(term == "" for term in args.terms):
        raise Usage("an empty term matches everything")
    hits = text_hits(ledger, args.terms, args.i, args.token)
    head = {**ledger.header(), "query": {"text": args.terms, "casefold": args.i, "token": args.token},
            "tier": "text", "guarantee": "none"}
    return paged(head, [(line, compact(line, row, via)) for line, row, via in hits], args, "newest")


def cmd_show(ledger: Ledger, args) -> list[str]:
    lines, missing = [], []
    for sel in args.selectors:
        if re.fullmatch(r"[0-9]+", sel):
            found = [int(sel)] if 1 <= int(sel) <= len(ledger.lines) else []
        elif ROW_ID.match(sel):
            found = [line for line, row in ledger.rows if row.get("row_id") == sel]
        elif HASH.match(sel):
            found = [line for line, row in ledger.rows if row.get("row_hash") == sel]
        else:
            raise Usage(f"show takes a line number, fN or a 64-hex row_hash, not {sel!r}")
        missing += [] if found else [sel]
        lines += [line for line in found if line not in lines]
    if args.start and len(lines) != 1:
        raise Usage("--from needs exactly one line")
    head = {**ledger.header(), "query": {"show": args.selectors}, "tier": "exact", "count": len(lines), "shown": 0,
            "missing": missing, "next": " ".join(map(str, lines)) + " --from " + "9" * 15}
    room = BUDGET - size(dumps(head))
    shown: list[str] = []
    cut = None
    for line in lines:
        text = ledger.lines[line - 1].decode("utf-8", "backslashreplace")
        item = dumps({"line": line, "text": text})
        if args.start or (not shown and size(item) > room):  # one line alone over the budget: a window of it
            start, width = min(args.start, len(text)), room
            while True:
                end = min(len(text), start + width)
                item = dumps({"line": line, "text": text[start:end], "from": start, "to": end, "chars": len(text)})
                if size(item) <= room or width <= 1:
                    break
                width = max(1, width * room // size(item) - 1)
            cut = end if end < len(text) else None
            shown.append(item)
            break
        if shown and size(item) > room:
            break
        shown.append(item)
        room -= size(item)
    rest = lines[len(shown):]
    head["shown"] = len(shown)
    head["next"] = (f"{lines[0]} --from {cut}" if cut is not None else " ".join(map(str, rest)) if rest else None)
    return [dumps(head), *shown]


# ---- the command line ---------------------------------------------------------------------------------------------
class Usage(Exception):
    """A query the tool cannot answer as asked: exit 2."""


HELP = """\
Exact tier (find, history, named, unclosed, sessions, tail, keys, show): what it finds is what a scan of every
line by the same rule finds. Text tier (text): literal strings in payload.summary, payload.refs and snapshot_id;
candidates only ("guarantee":"none").

Exact keys of a row (a field of the wrong type gives no key; the row is still read):
  kind part derivation trust      the field's string, equal
  row hash supersedes             row_id, row_hash, supersedes, equal
  line                            the line number (1 = first line); the identity in every answer
  commit                          snapshot_id: a lowercase hex query of 7 or more characters is a prefix, else equal
  day                             ts[:10] (YYYY-MM-DD); there is no time range: ts is not in line order
  path                            each payload.refs[i] that is not '<word>:<non-digit>...', a final :n or :n-m cut
                                  off, and each evidence_refs[j].path; byte for byte; --under is a prefix
  report                          the stem of a path reports/<stem>.json; Q matches stem Q and stems Q-...
  tag                             each ref '<word>:<value>' whose value does not start with a digit, as word:value

Every answer is JSON Lines: line 1 the header (bytes, sha256, rows, tip = the last readable row, "verified": false,
complete, unreadable lines and their rule, query, tier, count = every match, shown, next), then one line per match.
A page ends at --limit or at about 24 KB; "next" holds the arguments that continue it, added to the same command
(show: the selectors left). The chain (prev_hash, row_hash) and the meaning of rows are not judged. Exit 0 ok; 1 a
line could not be read (the answers cover the readable lines, which are listed); 2 a usage error or no ledger."""


def _limit(text: str) -> int:
    value = int(text)
    if not 1 <= value <= LIMIT_MAX:
        raise argparse.ArgumentTypeError(f"between 1 and {LIMIT_MAX}")
    return value


def _count(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("0 or more")
    return value


@functools.cache
def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="ledger_index.py", description="A read-only index of founder-ledger.jsonl.",
                                  epilog=HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--ledger", default=DEFAULT_LEDGER, help=f"the ledger file (default {DEFAULT_LEDGER})")
    pages = argparse.ArgumentParser(add_help=False)
    pages.add_argument("--limit", type=_limit, default=LIMIT,
                       help=f"matches per page (default {LIMIT}, max {LIMIT_MAX})")
    pages.add_argument("--order", choices=("newest", "oldest"), help="newest first or oldest first")
    cursor = pages.add_mutually_exclusive_group()
    cursor.add_argument("--before", type=int, metavar="LINE", help="only matches above this line")
    cursor.add_argument("--after", type=int, metavar="LINE", help="only matches below this line")
    sub = top.add_subparsers(dest="command", required=True, metavar="command")
    find_p = sub.add_parser("find", parents=[common, pages], help="rows by exact key (newest first)",
                            description="Repeat a key for OR; different keys are ANDed. No key: every row.")
    for key in KEYS:
        find_p.add_argument(f"--{key}", action="append", metavar=key.upper())
    find_p.add_argument("--line", action="append", type=int, metavar="N")
    find_p.add_argument("--under", action="append", metavar="DIR/", help="paths starting with this prefix")
    hist = sub.add_parser("history", parents=[common, pages], help="rows naming a path (oldest first)")
    hist.add_argument("path", nargs="?")
    hist.add_argument("--under", action="append", metavar="DIR/")
    named = sub.add_parser("named", parents=[common, pages], help="rows naming fN or a row_hash by a tag ref or "
                           "supersedes (fN also by its row_hash, and the reverse)")
    named.add_argument("target", metavar="fN|HASH")
    unc = sub.add_parser("unclosed", parents=[common, pages], help="rows of KINDS no later row names by TAG:<row_id>")
    unc.add_argument("--tag", required=True, help="the ref's word before ':'")
    unc.add_argument("--kinds", default="seed_issue,blocked", help="comma-separated (default seed_issue,blocked)")
    unc.add_argument("--all", action="store_true", help="every row of KINDS, closed ones too, with closed_by")
    ses = sub.add_parser("sessions", parents=[common, pages], help="session_start/session_end pairs; --last K: the "
                         "rows from the K-th last session's start to the end")
    ses.add_argument("--last", type=_limit, metavar="K")
    tail = sub.add_parser("tail", parents=[common], help="the last N rows, compact (default 12), in file order")
    tail.add_argument("n", type=_limit, nargs="?", default=12, metavar="N")
    tail.add_argument("--before", type=int, metavar="LINE", help="the last N rows above this line")
    keys = sub.add_parser("keys", parents=[common], help="distinct values of one exact key, with their row counts")
    keys.add_argument("key", choices=KEYS)
    keys.add_argument("--top", type=_limit, default=LIMIT, metavar="N")
    keys.add_argument("--skip", type=_count, default=0, metavar="M")
    text = sub.add_parser("text", parents=[common, pages], help="literal terms (OR) in summary, refs, snapshot_id; "
                          "candidates only")
    text.add_argument("terms", nargs="+", metavar="TERM")
    text.add_argument("-i", action="store_true", help="casefold both sides")
    text.add_argument("--token", action="store_true", help="no [A-Za-z0-9_-] right before or after the match")
    show = sub.add_parser("show", parents=[common], help="lines verbatim, by line number, fN or row_hash")
    show.add_argument("selectors", nargs="+", metavar="LINE|fN|HASH")
    show.add_argument("--from", dest="start", type=_count, default=0, metavar="C",
                      help="one long line from character C")
    return top


COMMANDS = {"find": cmd_find, "history": cmd_history, "named": cmd_named, "unclosed": cmd_unclosed,
            "sessions": cmd_sessions, "tail": cmd_tail, "keys": cmd_keys, "text": cmd_text, "show": cmd_show}


def answer(argv: list[str]) -> tuple[int, str]:
    """(exit code, the answer's text). A malformed command line exits 2 from argparse, as --help exits 0."""
    args = parser().parse_args(argv)
    try:
        with open(args.ledger, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        return 2, dumps({"tool": TOOL, "ledger": args.ledger, "error": f"no ledger: {type(exc).__name__}"}) + "\n"
    ledger = Ledger(args.ledger, data)
    try:
        lines = COMMANDS[args.command](ledger, args)
    except Usage as exc:
        return 2, dumps({"tool": TOOL, "ledger": args.ledger, "error": str(exc)}) + "\n"
    return (1 if ledger.unreadable else 0), "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    code, text = answer(sys.argv[1:] if argv is None else argv)
    try:
        sys.stdout.buffer.write(text.encode("utf-8", "backslashreplace"))
        sys.stdout.flush()
    except BrokenPipeError:
        pass
    return code


if __name__ == "__main__":
    sys.exit(main())
