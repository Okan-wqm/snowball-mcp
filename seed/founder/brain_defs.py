"""The brain's own agent and skill definitions, checked and turned into this session's plugin (register E450).

The capsule runs this once a session, after the brain is cloned and before `claude` starts (entrypoint.sh):

    python3 /opt/founder/brain_defs.py /work/brain "$CLAUDE_CONFIG_DIR/brain-plugin" /work/logs/brain-definitions.json

and the CLI loads the plugin with `--plugin-dir` (its setting sources stay off: no CLAUDE.md, settings, hooks, MCP
servers or output styles of any source). Agents and skills of a plugin are named `<plugin>:<name>`, here
`brain:<name>`: a brain definition never takes the place of one of the CLI's own.

What is read. Only the trees `agents/` and `skills/` of the clone's HEAD, and only from git's objects (`ls-tree`,
`cat-file`), never through the file system: no link can lead out of the brain. A symbolic link or a submodule is
not followed, it drops its definition.

The source formats (the brain):

    agents/<name>.md           ---
                               name: <name>
                               description: <one line>
                               tools: <Tool>, <Tool>     optional; without it the agent has the session's tools
                               model: <model>            optional; an alias (sonnet, opus, haiku, inherit) or an id
                               ---
                               <the agent's prompt>

    skills/<name>/SKILL.md     ---
                               name: <name>
                               description: <one line>
                               ---
                               <the skill's instructions>
    skills/<name>/<path>       the skill's own files (scripts, references), copied byte for byte

The front matter is the lines between a first line `---` and the next line `---`. Every line of it that is not
blank is `<key>: <value>`, the key at the start of the line; the value is the rest of the line without the
whitespace around it. A value in double quotes is read as a JSON string, one in single quotes with `''` for `'`;
any other value is taken as it is (a `#` or a `: ` in it is text). Only the keys above are taken; any other key (hooks, mcpServers, permissionMode, allowed-tools ...) drops the
definition. A name is lower-case letters and digits in words joined by single hyphens, at most `MAX_NAME_CHARS`, and
is the file's or the folder's own name. A description is one line, at most `MAX_DESCRIPTION_CHARS`, without control
characters. The text after the front matter must not be empty. Files are UTF-8; CRLF line ends are read as LF.

What is written. A plugin holding nothing but `.claude-plugin/plugin.json`, `agents/` and `skills/`; every agent file
and every SKILL.md is written anew from the checked fields (so the CLI reads exactly what was checked), a skill's own
files byte for byte. The load record (names, sha256 of the source blobs, and every skipped definition with its
reasons) goes to the session's log folder. A broken definition never stops the session: it is skipped and named
there; a failure of this script leaves no plugin, the record names the error, and the session starts without them.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path

SCHEMA = "snowball-brain-definitions/1"
PLUGIN = "brain"  # the CLI names the plugin's agents and skills `brain:<name>`
AGENTS_DIR, SKILLS_DIR, SKILL_FILE = "agents", "skills", "SKILL.md"
AGENT_KEYS = ("name", "description", "tools", "model")  # in the order they are written back
SKILL_KEYS = ("name", "description")
REQUIRED_KEYS = ("name", "description")

# The capsule's tool surface (entrypoint.sh, E380, E508). The six are what `--disallowedTools` removes; an agent naming
# one is dropped. WebFetch and WebSearch reach the web around the capsule's network (E508). ALLOWED_TOOLS is every other
# tool the capsule's session can have, as the pinned CLI 2.1.293 names it in its init event (signed out), `Agent`, the
# name the API and the documentation give the tool the init event calls `Task`, and `Glob` and `Grep`: on Linux, the
# capsule's platform, the session does not list them (its Bash searches), yet an agent that names them gets them.
# test_founder_capsule holds DENIED_TOOLS to the entrypoint's flag; test_live_cli holds ALLOWED_TOOLS to the CLI's init
# event and to the tools a brain agent's subagent is given.
DENIED_TOOLS = ("RemoteTrigger", "CronCreate", "CronDelete", "CronList", "WebFetch", "WebSearch")
ALLOWED_TOOLS = frozenset({
    "Agent", "Task", "Bash", "Edit", "EnterWorktree", "ExitWorktree", "Glob", "Grep", "ListAgents", "NotebookEdit",
    "Read", "ReportFindings", "ScheduleWakeup", "SendMessage", "Skill", "TaskStop", "ToolSearch", "Workflow", "Write"})

# The seed's agent configuration (`24a`; the referee's classify.AGENT_DIRS and AGENT_FILES, which test_founder_capsule
# holds these to): a path with such a component or last component is never loaded, whatever folder it is in.
AGENT_CONFIG_DIRS = frozenset({".claude", ".vscode", ".devcontainer"})
AGENT_CONFIG_FILES = frozenset({"claude.md", "agents.md", ".mcp.json", ".envrc"})


@dataclass(frozen=True)
class Limits:
    """Sizes and counts. A definition past one is skipped and named; the session starts all the same."""
    agents: int = 32  # agents loaded, in name order
    skills: int = 32  # skills loaded, in name order
    entries: int = 4096  # git entries read under agents/ and skills/ together
    definition_bytes: int = 64 * 1024  # an agent file, a SKILL.md
    skill_files: int = 64  # a skill's files, SKILL.md included
    skill_bytes: int = 1024 * 1024  # a skill's files together
    skill_depth: int = 6  # folders under the skill's own folder
    total_bytes: int = 4 * 1024 * 1024  # everything written to the plugin
    skipped_listed: int = 200  # skipped definitions named one by one in the record; the rest are counted


LIMITS = Limits()
MAX_NAME_CHARS = 64
MAX_DESCRIPTION_CHARS = 1024
NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
KEY_RE = re.compile(r"([A-Za-z][A-Za-z0-9_-]*):(?:[ \t]+(.*))?")
TOOL_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
MODEL_RE = re.compile(r"[a-z0-9][a-z0-9.-]{0,62}(?:\[[a-z0-9]+\])?")
COMPONENT_RE = re.compile(r"[A-Za-z0-9._-]+")  # one folder or file name in a skill's own files
GIT_TIMEOUT_S = 120
FILE_MODES = {"100644": 0o644, "100755": 0o755}


class Skip(Exception):
    """A definition that is not loaded; its reasons are stable identifiers the record names."""

    def __init__(self, *reasons: str) -> None:
        super().__init__(", ".join(reasons))
        self.reasons = list(reasons)


@dataclass(frozen=True)
class Entry:
    mode: str
    kind: str
    sha: str
    size: int
    path: str  # relative to the tree it was listed from


def git(brain: Path, *args: str, stdin: bytes | None = None) -> bytes:
    return subprocess.run(["git", "-C", str(brain), "--literal-pathspecs", *args], input=stdin, capture_output=True,
                          check=True, timeout=GIT_TIMEOUT_S).stdout


def ls_tree(brain: Path, treeish: str, *paths: str, recursive: bool = False) -> list[Entry]:
    out = []
    flags = ["-z", "--long"] + (["-r"] if recursive else [])
    for record in git(brain, "ls-tree", *flags, treeish, "--", *paths).split(b"\0"):
        if not record:
            continue
        meta, _, name = record.partition(b"\t")
        mode, kind, sha, size = meta.decode("ascii").split()
        out.append(Entry(mode, kind, sha, 0 if size == "-" else int(size), name.decode("utf-8", "surrogateescape")))
    return out


def read_blobs(brain: Path, shas: list[str]) -> dict[str, bytes]:
    """The blobs' bytes, in one `git cat-file --batch`."""
    wanted = sorted(set(shas))
    if not wanted:
        return {}
    out = git(brain, "cat-file", "--batch", stdin="".join(f"{sha}\n" for sha in wanted).encode("ascii"))
    blobs, at = {}, 0
    for sha in wanted:
        end = out.index(b"\n", at)
        head = out[at:end].split()
        if len(head) != 3 or head[0].decode("ascii") != sha or head[1] != b"blob":
            raise ValueError(f"git cat-file gave {out[at:end][:80]!r} for {sha}")
        size = int(head[2])
        blobs[sha] = out[end + 1:end + 1 + size]
        at = end + 2 + size
    return blobs


def is_agent_config(path: str) -> bool:
    parts = [part.casefold() for part in path.split("/") if part]
    return any(part in AGENT_CONFIG_DIRS for part in parts) or (bool(parts) and parts[-1] in AGENT_CONFIG_FILES)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def one_line(text: str) -> bool:
    return not any(unicodedata.category(c) in ("Cc", "Zl", "Zp") or c == "\ufeff" for c in text)


def unquote(value: str) -> str | None:
    """A double-quoted value is a JSON string, a single-quoted one has `''` for `'` (YAML's own rule for both on one
    line); any other value is taken as it is. None for a quoted value that does not read."""
    if value[:1] == '"':
        try:
            out = json.loads(value)
        except ValueError:
            return None
        return out if isinstance(out, str) else None
    if value[:1] == "'":
        inner = value[1:-1] if len(value) >= 2 and value[-1] == "'" else None
        return None if inner is None or "'" in inner.replace("''", "") else inner.replace("''", "'")
    return value


def parse(data: bytes, allowed: tuple[str, ...]) -> tuple[dict[str, str], str]:
    """(front matter, body) of a definition file in the format the module docstring states."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise Skip("not_utf8") from None
    lines = text.replace("\r\n", "\n").split("\n")
    if lines[0] != "---" or "---" not in lines[1:]:
        raise Skip("no_frontmatter")
    end = lines.index("---", 1)
    fields: dict[str, str] = {}
    reasons: list[str] = []
    for line in lines[1:end]:
        if not line.strip():
            continue
        match = KEY_RE.fullmatch(line.rstrip())
        if not match:
            reasons.append("bad_frontmatter_line")
            continue
        key, value = match.group(1), unquote((match.group(2) or "").strip())
        if value is None:
            reasons.append(f"bad_quotes:{key[:64]}")
        elif key not in allowed:
            reasons.append(f"key_not_allowed:{key}")
        elif key in fields:
            reasons.append(f"duplicate_key:{key}")
        else:
            fields[key] = value
    reasons += [f"missing:{key}" for key in REQUIRED_KEYS if key not in fields]
    body = "\n".join(lines[end + 1:])
    if not body.strip():
        reasons.append("empty_body")
    if reasons:
        raise Skip(*dict.fromkeys(reasons))
    return fields, body if body.endswith("\n") else body + "\n"


def check_fields(fields: dict[str, str], name: str) -> dict[str, object]:
    """The checked fields of a parsed definition, or Skip with every reason found."""
    reasons: list[str] = []
    if fields["name"] != name:
        reasons.append("name_mismatch")
    description = fields["description"]
    if not description or len(description) > MAX_DESCRIPTION_CHARS or not one_line(description):
        reasons.append("bad_description")
    out: dict[str, object] = {"name": name, "description": description}
    if "tools" in fields:
        tools = list(dict.fromkeys(part.strip() for part in fields["tools"].split(",")))
        if not tools or not all(tools):
            reasons.append("bad_tools")
        for tool in tools:
            if tool in DENIED_TOOLS:
                reasons.append(f"tool_denied:{tool}")
            elif tool and (not TOOL_RE.fullmatch(tool) or tool not in ALLOWED_TOOLS):
                reasons.append(f"tool_not_allowed:{tool[:64]}")
        out["tools"] = tools
    if "model" in fields:
        if not MODEL_RE.fullmatch(fields["model"]):
            reasons.append("bad_model")
        out["model"] = fields["model"]
    if reasons:
        raise Skip(*reasons)
    return out


def frontmatter(fields: dict[str, object], keys: tuple[str, ...]) -> str:
    """The front matter written back: one line a key, the description as a double-quoted scalar (a JSON string of one
    line is one), the tools as `A, B`."""
    lines = ["---"]
    for key in keys:
        if key not in fields:
            continue
        value = fields[key]
        if key == "description":
            value = json.dumps(value, ensure_ascii=False)
        elif key == "tools":
            value = ", ".join(value)  # type: ignore[arg-type]
        lines.append(f"{key}: {value}")
    return "\n".join(lines + ["---", ""])


def check_name(name: str) -> None:
    if len(name) > MAX_NAME_CHARS or not NAME_RE.fullmatch(name):
        raise Skip("bad_name")


@dataclass
class Load:
    brain: str | None = None
    agents: list[dict] = field(default_factory=list)
    skills: list[dict] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    skipped_total: int = 0
    written_bytes: int = 0
    error: str | None = None

    def skip(self, path: str, reasons: list[str]) -> None:
        self.skipped_total += 1
        if len(self.skipped) < LIMITS.skipped_listed:
            self.skipped.append({"path": path, "reasons": reasons})

    def record(self) -> dict:
        return {"schema": SCHEMA, "plugin": PLUGIN, "brain": self.brain, "error": self.error,
                "agents": self.agents, "skills": self.skills, "skipped": self.skipped,
                "skipped_total": self.skipped_total, "written_bytes": self.written_bytes, "limits": asdict(LIMITS),
                "denied_tools": list(DENIED_TOOLS), "allowed_tools": sorted(ALLOWED_TOOLS)}


def top_trees(brain: Path, load: Load) -> dict[str, list[Entry]]:
    """The entries under agents/ and skills/ (relative to each), at most LIMITS.entries together."""
    out: dict[str, list[Entry]] = {}
    budget = LIMITS.entries
    for top in ls_tree(brain, "HEAD", AGENTS_DIR, SKILLS_DIR):
        if top.path not in (AGENTS_DIR, SKILLS_DIR):
            continue
        if top.kind != "tree":
            load.skip(top.path, ["not_a_directory"])
            continue
        entries = ls_tree(brain, top.sha, recursive=True)
        if len(entries) > budget:  # the whole folder: a cut list would misname what it cut
            load.skip(top.path + "/", ["over_limit:entries"])
            continue
        budget -= len(entries)
        out[top.path] = entries
    return out


def file_problem(entry: Entry) -> str | None:
    if entry.mode == "120000":
        return "symlink"
    if entry.mode == "160000" or entry.kind == "commit":
        return "submodule"
    if entry.kind != "blob" or entry.mode not in FILE_MODES:
        return "not_a_file"
    return None


def load_agents(brain: Path, entries: list[Entry], out: Path, load: Load) -> None:
    candidates: dict[str, Entry] = {}
    folders: set[str] = set()
    for entry in entries:
        if "/" in entry.path:  # agents/ holds files only: a folder in it is not read, and is named once
            folders.add(f"{AGENTS_DIR}/{entry.path.split('/', 1)[0]}/")
        elif not entry.path.endswith(".md"):
            load.skip(f"{AGENTS_DIR}/{entry.path}", ["not_a_definition"])
        else:
            candidates[entry.path[:-3]] = entry
    for folder in sorted(folders):
        load.skip(folder, ["not_a_definition"])
    blobs = read_blobs(brain, [e.sha for e in candidates.values()
                               if file_problem(e) is None and e.size <= LIMITS.definition_bytes])
    for name in sorted(candidates):
        entry, path = candidates[name], f"{AGENTS_DIR}/{name}.md"
        try:
            check_name(name)
            if is_agent_config(path):
                raise Skip("agent_config")
            problem = file_problem(entry)
            if problem:
                raise Skip(problem)
            if entry.size > LIMITS.definition_bytes:
                raise Skip("over_limit:definition_bytes")
            data = blobs[entry.sha]
            parsed, body = parse(data, AGENT_KEYS)
            fields = check_fields(parsed, name)
            if len(load.agents) >= LIMITS.agents:
                raise Skip("over_limit:agents")
            text = (frontmatter(fields, AGENT_KEYS) + body).encode("utf-8")
            if load.written_bytes + len(text) > LIMITS.total_bytes:
                raise Skip("over_limit:total_bytes")
            (out / AGENTS_DIR).mkdir(exist_ok=True)
            (out / AGENTS_DIR / f"{name}.md").write_bytes(text)
            load.written_bytes += len(text)
            load.agents.append({"name": name, "loaded_as": f"{PLUGIN}:{name}", "path": path, "sha256": sha256(data),
                                "tools": fields.get("tools"), "model": fields.get("model")})
        except Skip as skip:
            load.skip(path, skip.reasons)
        except Exception as exc:  # a broken definition never stops the session: named, not swallowed
            load.skip(path, [f"error:{type(exc).__name__}"])


def skill_problems(name: str, files: list[Entry]) -> list[str]:
    reasons: list[str] = []
    skill_md = [f for f in files if f.path == SKILL_FILE]
    if not skill_md:
        reasons.append("no_skill_md")
    elif skill_md[0].size > LIMITS.definition_bytes:
        reasons.append("over_limit:definition_bytes")
    if len(files) > LIMITS.skill_files:
        reasons.append("over_limit:skill_files")
    if sum(f.size for f in files) > LIMITS.skill_bytes:
        reasons.append("over_limit:skill_bytes")
    for f in files:
        path = f"{SKILLS_DIR}/{name}/{f.path}"
        parts = f.path.split("/")
        problem = file_problem(f)
        if problem:
            reasons.append(f"{problem}:{path}")
        elif any(p in (".", "..") or p.casefold() == ".git" or not COMPONENT_RE.fullmatch(p) for p in parts):
            reasons.append(f"bad_path:{path.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')[:200]}")
        elif is_agent_config(path):
            reasons.append(f"agent_config:{path}")
        elif len(parts) - 1 > LIMITS.skill_depth:
            reasons.append(f"over_limit:skill_depth:{path}")
    return reasons


def load_skills(brain: Path, entries: list[Entry], out: Path, load: Load) -> None:
    groups: dict[str, list[Entry]] = {}
    for entry in entries:
        if "/" not in entry.path:
            load.skip(f"{SKILLS_DIR}/{entry.path}", ["not_a_definition"])
            continue
        folder, rest = entry.path.split("/", 1)
        groups.setdefault(folder, []).append(Entry(entry.mode, entry.kind, entry.sha, entry.size, rest))
    for name in sorted(groups):
        files, path = groups[name], f"{SKILLS_DIR}/{name}/{SKILL_FILE}"
        try:
            check_name(name)
            reasons = skill_problems(name, files)
            if reasons:
                raise Skip(*reasons)
            blobs = read_blobs(brain, [f.sha for f in files])
            source = blobs[next(f for f in files if f.path == SKILL_FILE).sha]
            parsed, body = parse(source, SKILL_KEYS)
            fields = check_fields(parsed, name)
            if len(load.skills) >= LIMITS.skills:
                raise Skip("over_limit:skills")
            skill_md = (frontmatter(fields, SKILL_KEYS) + body).encode("utf-8")
            size = len(skill_md) + sum(len(blobs[f.sha]) for f in files if f.path != SKILL_FILE)
            if load.written_bytes + size > LIMITS.total_bytes:
                raise Skip("over_limit:total_bytes")
            folder = out / SKILLS_DIR / name
            for f in sorted(files, key=lambda f: f.path):
                dest = folder.joinpath(*f.path.split("/"))
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(skill_md if f.path == SKILL_FILE else blobs[f.sha])
                os.chmod(dest, FILE_MODES[f.mode])
            load.written_bytes += size
            load.skills.append({"name": name, "loaded_as": f"{PLUGIN}:{name}", "path": path, "sha256": sha256(source),
                                "files": {f"{SKILLS_DIR}/{name}/{f.path}": sha256(blobs[f.sha])
                                          for f in sorted(files, key=lambda f: f.path)}})
        except Skip as skip:
            load.skip(f"{SKILLS_DIR}/{name}/", skip.reasons)
        except Exception as exc:  # a broken definition never stops the session: named, not swallowed
            shutil.rmtree(out / SKILLS_DIR / name, ignore_errors=True)
            load.skip(f"{SKILLS_DIR}/{name}/", [f"error:{type(exc).__name__}"])


def build(brain: Path, plugin: Path) -> Load:
    """Write the plugin at `plugin` (which must not exist yet) and return what was loaded and skipped."""
    load = Load()
    staging = plugin.with_name(plugin.name + ".partial")
    try:
        load.brain = git(brain, "rev-parse", "--verify", "--quiet", "HEAD^{commit}").decode("ascii").strip() or None
        shutil.rmtree(staging, ignore_errors=True)
        (staging / ".claude-plugin").mkdir(parents=True)
        (staging / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": PLUGIN}) + "\n", encoding="utf-8")
        trees = top_trees(brain, load)
        load_agents(brain, trees.get(AGENTS_DIR, []), staging, load)
        load_skills(brain, trees.get(SKILLS_DIR, []), staging, load)
        staging.rename(plugin)
    except Exception as exc:  # the session starts without the brain's definitions; the record says why
        shutil.rmtree(staging, ignore_errors=True)
        load.agents, load.skills = [], []
        load.error = f"{type(exc).__name__}: {str(exc)[:300]}"
    return load


def write_record(path: Path, record: dict) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(record, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: brain_defs.py <brain clone> <plugin folder to write> <record file>", file=sys.stderr)
        return 2
    brain, plugin, record = (Path(a) for a in argv)
    load = build(brain, plugin)
    write_record(record, load.record())
    if load.error:
        print(f"brain definitions not loaded: {load.error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
