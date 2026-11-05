"""What decides the fenced code's build (E532): the files that choose which code is compiled and loaded as it.

The K6 fence (`fence`, E511) keeps the owner's safety paths. A path list alone leaves open every file that changes what
those paths compile to without touching them (independent verifier, finding 5): a ``#[path]`` in the crate root that
loads another file as the fenced module, a dependent's ``Cargo.toml`` that points the fenced crate's name at another
directory, a workspace ``[patch]``, a ``build.rs``, a ``.cargo/config.toml`` (paths overrides, rustflags, ``--cfg``,
``[env]``, a rustc wrapper), a toolchain file, a lock entry of the fenced crate's dependencies. This module derives
those files from the copy's own Cargo manifests and Rust module graph, at the head's base and at the head, and names
the changed ones. It reads; nothing of the tree runs (no cargo, no rustc: `cargo metadata` would run the tree's
``build.rustc``). Pure and stdlib-only, like `fence`; every doubt falls closed:

- the fenced packages: every Cargo package holding a fenced file. Its manifest, its build script and the build
  scripts and proc-macro crates of every package compiled beside it (the members of its workspace and their path
  dependencies) are fenced whole: a build script runs on the build machine and can write the fenced sources;
- in a fenced package, the module chain of each fenced Rust file: the files that declare it and every module above it
  up to the crate root (a ``mod`` line, its ``#[path]`` or ``#[cfg_attr(.., path)]``), the other file each declaration
  could load (``name.rs`` or ``name/mod.rs``), every module below it and every file it ``include!``s;
- the dependents: a manifest's entries that name a fenced crate (by name, by path, through ``workspace = true``), its
  features that reach one, and, at the workspace root of a fenced package or a dependent, ``[patch]``, ``[replace]``,
  ``[profile]``, the resolver, the inherited package fields and the shared dependency entries the fenced packages use;
  such a manifest is fenced when that part of it changes, and so is a manifest whose package takes a fenced name;
- the lock files: when a ``Cargo.lock``'s entries for the fenced crates and everything they depend on change;
- a package's workspace root: when it differs between base and head, both roots' manifests;
- the configuration cargo and rustup read from a build's directory and every directory above it: ``.cargo/config``,
  ``.cargo/config.toml``, ``rust-toolchain`` and ``rust-toolchain.toml``.

What a fenced module calls in another module or crate is its behaviour, not its build: that is the owner's list to name
(the K6 exam measures it). Paths compare as `fence` compares them: case-folded and composed.
"""

from __future__ import annotations

import functools
import posixpath
import re
import tomllib
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

from .fence import _fold, touches_safety

MANIFEST = "Cargo.toml"
LOCK = "Cargo.lock"
CONFIGS = (".cargo/config", ".cargo/config.toml", "rust-toolchain", "rust-toolchain.toml")
BUILT = ("dependencies", "build-dependencies", "build_dependencies")  # what a build compiles in (dev: tests only)
INCLUDES = frozenset({"include", "include_str", "include_bytes"})
MAX_RUST_BYTES = 4 << 20  # a module file read to find its declarations; a larger one is fenced with its package


@dataclass(frozen=True)
class Tree:
    """One commit of the copy as the fence reads it: every path, and a regular file's bytes (None for no regular file,
    or one that cannot be read)."""
    paths: tuple[str, ...]
    read: Callable[[str], bytes | None]


def _key(path: str) -> str:
    """A path as the fence compares it (`fence._fold`, one rule for both)."""
    return _fold(path).strip("/")


def _dir(path: str) -> str:
    return posixpath.dirname(path)


def _join(*parts: str) -> str | None:
    """The normalised path of ``parts`` below the top; None for one that leaves the tree or is absolute."""
    if any(p.startswith("/") or "\\" in p for p in parts if p):
        return None
    joined = posixpath.normpath(posixpath.join(*[p for p in parts if p])) if any(parts) else ""
    if joined == ".":
        return ""
    return None if joined == ".." or joined.startswith("../") else joined


def _ancestors(directory: str) -> list[str]:
    """``directory`` and every directory above it, the top (``""``) last."""
    out = []
    while True:
        out.append(directory)
        if not directory:
            return out
        directory = _dir(directory)


def _toml(data: bytes | None) -> dict[str, Any] | None:
    if data is None:
        return None
    try:
        return tomllib.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None


def _crate(name: Any) -> str:
    """A package name as cargo compares names across sources: case and ``-``/``_`` alike (fail closed)."""
    return str(name).lower().replace("-", "_")


@dataclass
class Package:
    directory: str
    data: dict[str, Any] | None  # None: a manifest that does not parse, read as wide as it can be
    name: str | None

    def table(self, key: str) -> dict[str, Any]:
        value = (self.data or {}).get(key)
        return value if isinstance(value, dict) else {}


def _dep_entries(data: dict[str, Any] | None) -> Iterable[tuple[str, str, Any]]:
    """``(where, key, spec)`` of every dependency entry a build of the package compiles in, target-specific ones
    too. Dev-dependencies build the package's tests alone, never what a dependent links."""
    data = data or {}
    tables = [("", data)] + [(f"target.{t}.", v) for t, v in (data.get("target") or {}).items() if isinstance(v, dict)]
    for prefix, holder in tables:
        for table in BUILT:
            entries = holder.get(table)
            for key, spec in (entries.items() if isinstance(entries, dict) else ()):
                yield f"{prefix}{table}", key, spec


@dataclass
class Graph:
    """One tree's Cargo packages, workspace roots and Rust modules, as far as the fence needs them."""
    tree: Tree
    files: dict[str, str] = field(default_factory=dict)  # folded key -> path as the tree holds it
    manifests: dict[str, Package] = field(default_factory=dict)  # folded directory -> package or workspace manifest

    @classmethod
    def of(cls, tree: Tree) -> "Graph":
        graph = cls(tree)
        for path in tree.paths:
            graph.files[_key(path)] = path
        for path in tree.paths:
            if posixpath.basename(path) == MANIFEST:
                data = _toml(tree.read(path))
                package = (data or {}).get("package")
                name = package.get("name") if isinstance(package, dict) else None
                graph.manifests[_key(_dir(path))] = Package(_dir(path), data, name if isinstance(name, str) else None)
        return graph

    def has(self, path: str) -> bool:
        return _key(path) in self.files

    def read(self, path: str) -> bytes | None:
        held = self.files.get(_key(path))
        return None if held is None else self.tree.read(held)

    def is_package(self, manifest: Package) -> bool:
        return manifest.data is None or "package" in manifest.data

    def package_of(self, path: str) -> Package | None:
        """The package whose directory holds ``path``: the nearest manifest above it that declares one."""
        for directory in _ancestors(_dir(path)):
            found = self.manifests.get(_key(directory))
            if found is not None and self.is_package(found):
                return found
        return None

    def root_of(self, package: Package) -> Package:
        """The workspace root a package builds in: its ``package.workspace``, else the nearest manifest at or above it
        with a ``[workspace]`` that does not exclude it; else itself."""
        explicit = package.table("package").get("workspace")
        if isinstance(explicit, str):
            target = _join(package.directory, explicit)
            found = self.manifests.get(_key(target)) if target is not None else None
            if found is not None:
                return found
        for directory in _ancestors(package.directory):
            found = self.manifests.get(_key(directory))
            if found is None or found.data is None or "workspace" not in found.data:
                continue
            return package if self._excludes(found, package.directory) else found  # excluded: its own root
        return package

    def _excludes(self, root: Package, directory: str) -> bool:
        excluded = root.table("workspace").get("exclude")
        rel = posixpath.relpath(directory, root.directory or ".") if directory != root.directory else ""
        for entry in excluded if isinstance(excluded, list) else []:
            entry = _join(str(entry))
            if entry is not None and (rel == entry or rel.startswith(entry + "/")):
                return True
        return False

    def members(self, root: Package) -> list[Package]:
        """The packages a build at ``root`` compiles from this tree: every package under it that builds in it (a
        package under a workspace root that is no member stops cargo), and the path dependencies of those, in turn."""
        found = [p for p in self.manifests.values() if self.is_package(p) and self.root_of(p) is root]
        seen = {_key(p.directory) for p in found}
        queue = list(found)
        while queue:
            for dep in self.path_deps(queue.pop()):
                if _key(dep.directory) not in seen:
                    seen.add(_key(dep.directory))
                    found.append(dep)
                    queue.append(dep)
        return found

    def path_deps(self, package: Package) -> list[Package]:
        out = []
        for _where, key, spec in _dep_entries(package.data):
            target = self._dep_dir(package, key, spec)
            found = self.manifests.get(_key(target)) if target is not None else None
            if found is not None and self.is_package(found):
                out.append(found)
        return out

    def _dep_dir(self, package: Package, key: str, spec: Any) -> str | None:
        if isinstance(spec, dict) and isinstance(spec.get("path"), str):
            return _join(package.directory, spec["path"])
        if isinstance(spec, dict) and spec.get("workspace") is True:
            root = self.root_of(package)
            shared = root.table("workspace").get("dependencies")
            inherited = shared.get(key) if isinstance(shared, dict) else None
            if isinstance(inherited, dict) and isinstance(inherited.get("path"), str):
                return _join(root.directory, inherited["path"])
        return None

    def names(self, package: Package, key: str, spec: Any) -> set[str]:
        """The crate names one dependency entry may resolve to: its key, its ``package``, its shared entry's."""
        out = {_crate(key)}
        if isinstance(spec, dict) and isinstance(spec.get("package"), str):
            out.add(_crate(spec["package"]))
        if isinstance(spec, dict) and spec.get("workspace") is True:
            shared = self.root_of(package).table("workspace").get("dependencies")
            inherited = shared.get(key) if isinstance(shared, dict) else None
            if isinstance(inherited, dict) and isinstance(inherited.get("package"), str):
                out.add(_crate(inherited["package"]))
        return out

    # ---- Rust modules ------------------------------------------------------------------------------------------

    def crate_roots(self, package: Package) -> list[str]:
        """Every file a target of ``package`` starts from: the library, the binaries (named or found) and the build
        script; an unread manifest gives the defaults."""
        base = package.directory
        roots = [_join(base, "src/lib.rs"), _join(base, "src/main.rs"), _join(base, "build.rs")]
        lib = package.table("lib")
        if isinstance(lib.get("path"), str):
            roots.append(_join(base, lib["path"]))
        build = package.table("package").get("build")
        if isinstance(build, str):
            roots.append(_join(base, build))
        bins = (package.data or {}).get("bin")
        for target in bins if isinstance(bins, list) else []:
            if isinstance(target, dict) and isinstance(target.get("path"), str):
                roots.append(_join(base, target["path"]))
        prefix = _key(_join(base, "src/bin") or "") + "/"
        for key, path in self.files.items():
            rest = key[len(prefix):] if key.startswith(prefix) else None
            if rest and (rest.count("/") == 0 and rest.endswith(".rs") or rest.count("/") == 1
                         and rest.endswith("/main.rs")):
                roots.append(path)
        return [r for r in roots if r is not None]

    def modules(self, package: Package) -> "Modules":
        mods = Modules()
        queue = [(r, "root") for r in self.crate_roots(package) if self.has(r)]
        seen = {_key(r) for r, _ in queue}
        while queue:
            path, kind = queue.pop()
            text = self.read(path)
            if text is None or len(text) > MAX_RUST_BYTES:
                mods.unread.add(_key(path))
                continue
            read = scan_bytes(text)
            for decl in read.decls:
                found = [(o, k) for o, k in options(path, kind, decl) if o is not None]
                group = {_key(o) for o, _k in found}
                for option, child_kind in found:
                    mods.alternatives.setdefault(_key(option), set()).update(group)
                    if not self.has(option):
                        continue
                    mods.parents.setdefault(_key(option), set()).add(_key(path))
                    mods.children.setdefault(_key(path), set()).add(_key(option))
                    mods.declared[(_key(path), _key(option))] = (decl.name, decl.inline)
                    if decl.macro_use:
                        mods.macro_use.setdefault(_key(path), set()).add(_key(option))
                    if _key(option) not in seen:
                        seen.add(_key(option))
                        queue.append((option, child_kind))
            for inc in read.includes:
                target = _join(_dir(path), inc)
                if target is not None:
                    mods.children.setdefault(_key(path), set()).add(_key(target))
        return mods


def options(path: str, kind: str, decl: "Decl") -> list[tuple[str | None, str]]:
    """Every file one out-of-line ``mod`` declaration in ``path`` (a ``kind`` of module file) may load, each with the
    kind of module file it is: by default ``name.rs`` or ``name/mod.rs`` in the module's directory (the file's own for
    a crate root or a ``mod.rs``, the file's stem below it for any other file; inline modules add theirs); a ``path``
    attribute is relative to the file's directory outside inline modules, to the module's inside them. A file a
    ``path`` attribute loads is read both ways."""
    here = _dir(path)
    stem = posixpath.splitext(posixpath.basename(path))[0]
    module_dirs = [here] if kind in ("root", "modrs") else [_join(here, stem)]
    if kind == "path":
        module_dirs = [here, _join(here, stem)]
    out: list[tuple[str | None, str]] = []
    for d in module_dirs:
        if decl.paths:
            out += [(_join(here, p) if not decl.inline else _join(d or "", *decl.inline, p), "path")
                    for p in decl.paths]
        else:
            out += [(_join(d or "", *decl.inline, f"{decl.name}.rs"), "nonmodrs"),
                    (_join(d or "", *decl.inline, decl.name, "mod.rs"), "modrs")]
    return out


@dataclass
class Modules:
    parents: dict[str, set[str]] = field(default_factory=dict)
    children: dict[str, set[str]] = field(default_factory=dict)  # declared modules and included files
    alternatives: dict[str, set[str]] = field(default_factory=dict)  # every file one declaration could load
    declared: dict[tuple[str, str], tuple[str, tuple[str, ...]]] = field(default_factory=dict)  # (file, child): decl
    macro_use: dict[str, set[str]] = field(default_factory=dict)  # a file's `#[macro_use]` modules
    unread: set[str] = field(default_factory=set)

    def below(self, keys: Iterable[str]) -> set[str]:
        out: set[str] = set()
        queue = list(keys)
        while queue:
            for child in self.children.get(queue.pop(), ()):
                if child not in out:
                    out.add(child)
                    queue.append(child)
        return out

    def around(self, key: str) -> tuple[set[str], dict[str, set[tuple[str, tuple[str, ...]]]]]:
        """What decides what ``key`` compiles to: (the files fenced whole: everything below it, the `#[macro_use]`
        modules of every file above it with what is below them, and every file each of those declarations could load;
        the files above it up to the crate root, each with the declarations in it that load the chain, fenced when
        those, its inner attributes or its macros change)."""
        chain: dict[str, set[tuple[str, tuple[str, ...]]]] = {}
        queue = [key]
        while queue:
            k = queue.pop()
            for parent in self.parents.get(k, ()):
                if parent not in chain:
                    queue.append(parent)
                chain.setdefault(parent, set()).add(self.declared[(parent, k)])
        used = {m for parent in chain for m in self.macro_use.get(parent, ())}
        whole = self.below([key]) | used | self.below(used)
        for k in list(whole) + [key] + [c for parent in chain for c in self.children.get(parent, ())
                                         if self.declared.get((parent, c)) in chain[parent]]:
            whole |= self.alternatives.get(k, set())
        return whole, chain


# ---- Reading Rust: declarations and includes, never meaning -------------------------------------------------------

# One token at a time, in the order Rust's lexer tries them: whitespace, comments, raw and plain string literals (byte
# and C strings too), character literals (a lone quote is a lifetime's), identifiers (raw ones too), punctuation.
_TOKEN = re.compile(r"""(?P<ws>\s+)|(?P<line>//[^\n]*)|(?P<block>/\*)|(?P<raw>[bc]?r(?P<hashes>\#*)")"""
                    r"""|(?P<str>[bc]?"(?:[^"\\]|\\.)*(?:"|\Z))"""
                    r"""|(?P<chr>'(?:\\(?:u\{[0-9A-Fa-f]{1,6}\}|x[0-9A-Fa-f]{2}|.)|[^\\'\n])')"""
                    r"""|(?P<id>(?:r\#)?[A-Za-z_][A-Za-z0-9_]*)|(?P<p>.)""", re.S)
_BLOCK = re.compile(r"/\*|\*/")
_ESCAPE = re.compile(r"\\(.)", re.S)
_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0"}
BRACKETS = {("p", "{"): ("{", "}"), ("p", "("): ("(", ")"), ("p", "["): ("[", "]")}


def tokens(text: str) -> list[tuple[str, str]]:
    """Rust source as ``(kind, value)``: ``id``, ``str`` (a string literal's value) and ``p`` (one punctuation
    character). Comments (nested ones too), character literals and whitespace are dropped."""
    out: list[tuple[str, str]] = []
    i, n = 0, len(text)
    while i < n:
        m = _TOKEN.match(text, i)
        kind = m.lastgroup if m.lastgroup != "hashes" else "raw"
        if kind == "block":
            depth, j = 0, i
            for b in _BLOCK.finditer(text, i):
                depth += 1 if b.group(0) == "/*" else -1
                j = b.end()
                if depth == 0:
                    break
            i = j if depth == 0 else n
            continue
        if kind == "raw":
            close = '"' + m.group("hashes")
            j = text.find(close, m.end())
            j = n if j < 0 else j
            out.append(("str", text[m.end():j]))
            i = j + len(close)
            continue
        i = m.end()
        if kind == "str":
            body = m.group(0)[m.group(0).index('"') + 1:]
            body = body[:-1] if body.endswith('"') else body
            out.append(("str", _ESCAPE.sub(lambda e: _ESCAPES.get(e.group(1), e.group(1)), body) if "\\" in body
                        else body))
        elif kind in ("id", "p"):
            out.append((kind, m.group(0)))
    return out


def _bracketed(toks: list[tuple[str, str]], start: int, open_: str, close: str) -> int:
    """The index just past the bracket that closes the one at ``start``."""
    depth = 0
    for j in range(start, len(toks)):
        if toks[j] == ("p", open_):
            depth += 1
        elif toks[j] == ("p", close):
            depth -= 1
            if depth == 0:
                return j + 1
    return len(toks)


@dataclass(frozen=True)
class Decl:
    name: str
    inline: tuple[str, ...]  # the inline modules it sits in
    paths: tuple[str, ...]  # its `path` attribute values (`cfg_attr` ones too: any may be the one that loads)
    attrs: str  # its outer attributes as tokens, the `cfg` that keeps or drops it among them
    macro_use: bool


@dataclass(frozen=True)
class Scan:
    decls: tuple[Decl, ...]
    includes: tuple[str, ...]
    inner: str  # the file's inner attributes (`#![...]`), as tokens
    macros: str  # its `macro_rules!` definitions, as tokens: a module declared after one sees it

    def view(self, loads: set[tuple[str, tuple[str, ...]]]) -> tuple[Any, ...]:
        """What of this file decides the modules ``loads`` names (``(name, inline)``): their declarations, the file's
        inner attributes, its macros and its `#[macro_use]` declarations."""
        return (tuple(sorted(repr(d) for d in self.decls if (d.name, d.inline) in loads or d.macro_use)), self.inner,
                self.macros)


def _text(toks: list[tuple[str, str]]) -> str:
    return " ".join(f"{k}:{v}" for k, v in toks)


@functools.lru_cache(maxsize=8192)
def scan_bytes(data: bytes) -> Scan:
    """``scan`` of a file's bytes; a file the base and the head share is read once."""
    return scan(data.decode("utf-8", "replace"))


def scan(text: str) -> Scan:
    """A Rust file's out-of-line module declarations, the literal paths it includes, its inner attributes and its
    macro definitions."""
    toks = tokens(text)
    decls: list[Decl] = []
    includes: list[str] = []
    inner: list[str] = []
    macros: list[str] = []
    pending: list[list[tuple[str, str]]] = []
    inline: list[tuple[str, int]] = []
    opening: str | None = None
    depth, i = 0, 0
    while i < len(toks):
        tok = toks[i]
        if tok == ("p", "#") and i + 1 < len(toks):
            j = i + 2 if toks[i + 1] == ("p", "!") else i + 1
            if j < len(toks) and toks[j] == ("p", "["):
                end = _bracketed(toks, j, "[", "]")
                if j == i + 1:  # an outer attribute: it belongs to the next item
                    pending.append(toks[j:end])
                else:
                    inner.append(_text(toks[j:end]))
                i = end
                continue
        if tok == ("id", "macro_rules") and toks[i + 1:i + 2] == [("p", "!")]:
            j = i + 3 if i + 2 < len(toks) and toks[i + 2][0] == "id" else i + 2
            pair = BRACKETS.get(toks[j]) if j < len(toks) else None
            end = _bracketed(toks, j, *pair) if pair else j
            macros.append(_text(toks[i:end]))
            i, pending = end, []
            continue
        if tok == ("id", "mod") and i + 1 < len(toks) and toks[i + 1][0] == "id":
            name = toks[i + 1][1].removeprefix("r#")
            nxt = toks[i + 2] if i + 2 < len(toks) else ("p", ";")
            if nxt == ("p", ";"):
                paths = tuple(a[k + 2][1] for a in pending for k in range(len(a) - 2)
                              if a[k] == ("id", "path") and a[k + 1] == ("p", "=") and a[k + 2][0] == "str")
                decls.append(Decl(name, tuple(n for n, _d in inline), paths, " | ".join(_text(a) for a in pending),
                                  any(("id", "macro_use") in a for a in pending)))
            elif nxt == ("p", "{"):
                opening = name
            pending = []
            i += 2
            continue
        if tok[0] == "id" and tok[1] in INCLUDES and toks[i + 1:i + 3] == [("p", "!"), ("p", "(")] \
                and i + 3 < len(toks) and toks[i + 3][0] == "str":
            includes.append(toks[i + 3][1])
        if tok == ("p", "{"):
            depth += 1
            if opening is not None:
                inline.append((opening, depth))
            opening = None
            pending = []
        elif tok == ("p", "}"):
            if inline and inline[-1][1] == depth:
                inline.pop()
            depth -= 1
            pending = []
        elif tok == ("p", ";"):
            pending, opening = [], None
        i += 1
    return Scan(tuple(decls), tuple(includes), " | ".join(inner), " | ".join(macros))


# ---- The fence's part ---------------------------------------------------------------------------------------------

def _fenced_files(graph: Graph, owner: Sequence[str]) -> list[str]:
    return touches_safety(graph.tree.paths, owner)


@dataclass
class Side:
    """What one tree fences: whole files, the packages that hold fenced files, their names and dependents."""
    graph: Graph
    whole: set[str] = field(default_factory=set)
    fenced: list[Package] = field(default_factory=list)
    names: set[str] = field(default_factory=set)
    dirs: set[str] = field(default_factory=set)
    roots: list[Package] = field(default_factory=list)
    chain: dict[str, set[tuple[str, tuple[str, ...]]]] = field(default_factory=dict)  # file above a fenced module


def _side(graph: Graph, owner: Sequence[str]) -> Side:
    side = Side(graph)
    fenced_files = _fenced_files(graph, owner)
    by_dir: dict[str, Package] = {}
    for path in fenced_files:
        package = graph.package_of(path)
        if package is not None:
            by_dir.setdefault(_key(package.directory), package)
    side.fenced = list(by_dir.values())
    side.dirs = set(by_dir)
    side.names = {_crate(p.name) for p in side.fenced if p.name}
    for package in side.fenced:
        side.whole.add(_key(_join(package.directory, MANIFEST) or MANIFEST))
        mods = graph.modules(package)
        if mods.unread:  # a module file too large or unreadable to follow: its whole package is fenced
            inside = _key(package.directory) + "/"
            side.whole |= {k for k in graph.files if not package.directory or k.startswith(inside)}
        for path in fenced_files:
            if graph.package_of(path) is package:
                whole, chain = mods.around(_key(path))
                side.whole |= whole
                for parent, loads in chain.items():
                    side.chain.setdefault(parent, set()).update(loads)
    dependents = _dependents(graph, side)
    builds = {_key(p.directory): p for p in side.fenced + dependents}
    roots = {_key(graph.root_of(p).directory): graph.root_of(p) for p in builds.values()}
    side.roots = list(roots.values())
    for root in side.roots:
        for member in graph.members(root):
            for script in (_join(member.directory, "build.rs"), _build_script(member)):
                if script is not None:
                    side.whole.add(_key(script))
            if member.table("lib").get("proc-macro") is True or member.table("lib").get("proc_macro") is True:
                side.whole |= {k for k in graph.files if k.startswith(_key(member.directory) + "/")}
    for directory in {d for p in list(builds.values()) + side.roots for d in _ancestors(p.directory)}:
        side.whole |= {_key(_join(directory, c) or c) for c in CONFIGS}
    return side


def _build_script(package: Package) -> str | None:
    build = package.table("package").get("build")
    return _join(package.directory, build) if isinstance(build, str) else None


def _refers(graph: Graph, package: Package, key: str, spec: Any, names: set[str], dirs: set[str]) -> bool:
    target = graph._dep_dir(package, key, spec)
    return bool(graph.names(package, key, spec) & names) or (target is not None and _key(target) in dirs)


def _dependents(graph: Graph, side: Side) -> list[Package]:
    """Every package that builds a fenced package: depends on one, or on a package that does."""
    names, dirs = set(side.names), set(side.dirs)
    found: dict[str, Package] = {}
    changed = True
    while changed:
        changed = False
        for key, package in graph.manifests.items():
            if key in dirs or key in found or not graph.is_package(package):
                continue
            if any(_refers(graph, package, k, s, names, dirs) for _w, k, s in _dep_entries(package.data)):
                found[key] = package
                dirs.add(key)
                if package.name:
                    names.add(_crate(package.name))
                changed = True
    return list(found.values())


def _manifest_view(graph: Graph, package: Package, side: Side, root_keys: set[str]) -> dict[str, Any]:
    """The part of one parsed manifest that decides what the fenced packages build from: its entries that name one,
    its features that reach one, its package name if it takes a fenced one; at a workspace root, also what every
    member inherits or is patched with. Empty (``_relevant`` False) for a manifest the fence has no part in."""
    data = package.data or {}
    entries = sorted((w, k, repr(s)) for w, k, s in _dep_entries(data)
                     if _refers(graph, package, k, s, side.names, side.dirs))
    keys = {k for w, k, s in _dep_entries(data) if _refers(graph, package, k, s, side.names, side.dirs)}
    features = data.get("features") if isinstance(data.get("features"), dict) else {}
    reach = sorted((f, repr(v)) for f, v in features.items()
                   if any(isinstance(x, str) and re.split(r"[/:?]", x.removeprefix("dep:"))[0] in keys
                          for x in (v if isinstance(v, list) else [])))
    view: dict[str, Any] = {"entries": entries, "features": reach,
                            "name": package.name if package.name and _crate(package.name) in side.names else None}
    if _key(package.directory) in root_keys:
        workspace = package.table("workspace")
        used = {k for p in side.fenced for _w, k, s in _dep_entries(p.data)
                if isinstance(s, dict) and s.get("workspace") is True}
        shared = workspace.get("dependencies") if isinstance(workspace.get("dependencies"), dict) else {}
        view.update({"patch": repr(data.get("patch")), "replace": repr(data.get("replace")),
                     "profile": repr(data.get("profile")), "resolver": repr(workspace.get("resolver")),
                     "package_resolver": repr(package.table("package").get("resolver")),
                     "inherited": repr(workspace.get("package")),
                     "shared": sorted((k, repr(v)) for k, v in shared.items()
                                      if k in used or _crate(k) in side.names
                                      or isinstance(v, dict) and _crate(v.get("package", "")) in side.names)})
    return view


def _relevant(view: dict[str, Any]) -> bool:
    return any(view.values())


def _lock_view(data: bytes | None, names: set[str], built: set[str]) -> Any:
    """A lock's entries for the fenced crates (``names``) and for what they compile in (``built``: their non-dev
    dependencies' names) with everything those depend on, in turn; None for a lock that does not parse. A fenced
    crate's own entry is not followed: as a member its dependency list holds its dev-dependencies too."""
    lock = _toml(data)
    if lock is None:
        return None if data is not None else ()
    listed = lock.get("package")
    entries = [p for p in listed if isinstance(p, dict)] if isinstance(listed, list) else []
    by_name: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        by_name.setdefault(_crate(entry.get("name", "")), []).append(entry)
    seen, queue = {n for n in names if n in by_name}, [n for n in built - names if n in by_name]
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        for entry in by_name.get(name, []):
            deps = entry.get("dependencies")
            queue += [_crate(str(d).split(" ")[0]) for d in (deps if isinstance(deps, list) else [])]
    return tuple(sorted(repr(sorted(e.items())) for n in seen for e in by_name.get(n, [])))


def _lock_seeds(side: Side, directory: str) -> tuple[set[str], set[str]]:
    """Whose entries a lock in ``directory`` holds for the fence: the fenced packages a build rooted there compiles
    (every fenced package, when no manifest roots a build there), their names and their non-dev dependencies'."""
    root = side.graph.manifests.get(directory)
    held = side.fenced if root is None else [p for p in side.graph.members(root) if _key(p.directory) in side.dirs]
    built = {n for p in held for _w, k, spec in _dep_entries(p.data) for n in side.graph.names(p, k, spec)}
    return {_crate(p.name) for p in held if p.name}, built


def fenced(changed: Iterable[str], owner: Sequence[str], base: Tree, head: Tree) -> list[str]:
    """The paths of ``changed`` (the copy head's diff from its base) that decide what the owner's fenced files compile
    to or which code is loaded as them, at the base or at the head: sorted, each once. The owner's own paths are
    `fence.touches_safety`'s; this names what a path list cannot."""
    sides = [_side(Graph.of(base), owner), _side(Graph.of(head), owner)]
    names = set().union(*(s.names for s in sides))
    whole = set().union(*(s.whole for s in sides))
    root_keys = {_key(r.directory) for s in sides for r in s.roots}
    for side in sides:  # a package that builds under another workspace root at the head: both roots decide
        side.names, side.dirs = names, set().union(*(s.dirs for s in sides))
    chain: dict[str, set[tuple[str, tuple[str, ...]]]] = {}
    for side in sides:
        for parent, loads in side.chain.items():
            chain.setdefault(parent, set()).update(loads)
    out = set()
    for path in changed:
        if _key(path) in whole:
            out.add(path)
        elif _key(path) in chain:  # a file above a fenced module: what of it loads the chain
            texts = [s.graph.read(path) for s in sides]
            views = [None if t is None or len(t) > MAX_RUST_BYTES else scan_bytes(t).view(
                chain[_key(path)]) for t in texts]
            if views[0] != views[1] or None in views:
                out.add(path)
        elif posixpath.basename(path) == LOCK:
            seeds = [_lock_seeds(s, _key(_dir(path))) for s in sides]
            crates, built = seeds[0][0] | seeds[1][0], seeds[0][1] | seeds[1][1]
            views = [_lock_view(s.graph.read(path), crates, built) for s in sides]
            if views[0] != views[1] or None in views:
                out.add(path)
        elif posixpath.basename(path) == MANIFEST:
            seen: list[Any] = []
            for s in sides:
                package = s.graph.manifests.get(_key(_dir(path)))
                seen.append("absent" if package is None else "unparsed" if package.data is None
                            else _manifest_view(s.graph, package, s, root_keys))
            if "unparsed" in seen or seen[0] != seen[1] and any(isinstance(v, dict) and _relevant(v) for v in seen):
                out.add(path)
    for package_key in set().union(*(s.dirs for s in sides)):  # the workspace root each fenced package builds in
        roots = []
        for s in sides:
            package = s.graph.manifests.get(package_key)
            roots.append(None if package is None else _key(s.graph.root_of(package).directory))
        if roots[0] is not None and roots[1] is not None and roots[0] != roots[1]:
            for root in roots:
                out |= {p for p in changed if _key(p) == _key(_join(root, MANIFEST) or MANIFEST)}
    return sorted(out)

