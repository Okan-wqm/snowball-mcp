"""E532: the K6 fence keeps what decides the fenced code's build, not only its paths (independent verifier, finding 5).

A synthetic Cargo layout with the target's shape and none of its names (its paths stay off the seed, `test_fence`): a
virtual workspace root, a fenced library crate in it, a binary with its own workspace that depends on that crate by
path and holds fenced modules, a second member with a build script. Each test changes one file the way an edit could
change what the fenced files compile to without touching them, and an honest edit beside it that must stay open.
"""

import json
import unittest
from pathlib import Path

from snowball_bootstrap import buildfence as bf
from snowball_bootstrap import fence

OWNER = ["plant/src/failsafe*.rs", "crates/interlock-core/"]
BASE = {
    "Cargo.toml": """[workspace]
resolver = "2"
members = ["crates/interlock-core", "crates/telemetry"]
exclude = ["plant", "plant/fuzz"]

[workspace.package]
edition = "2021"

[workspace.dependencies]
serde = "1"
log = "0.4"
""",
    "Cargo.lock": """version = 4

[[package]]
name = "interlock-core"
version = "0.1.0"
dependencies = ["serde"]

[[package]]
name = "telemetry"
version = "0.1.0"
dependencies = ["log"]

[[package]]
name = "serde"
version = "1.0.1"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "aa"

[[package]]
name = "log"
version = "0.4.1"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "bb"
""",
    ".cargo/config.toml": "[build]\ntarget-dir = \"target\"\n",
    "rust-toolchain.toml": "[toolchain]\nchannel = \"1.88.0\"\n",
    "crates/interlock-core/Cargo.toml": """[package]
name = "interlock-core"
version = "0.1.0"
edition.workspace = true

[dev-dependencies]
serde = { workspace = true }
""",
    "crates/interlock-core/src/lib.rs": "pub mod trip;\n",
    "crates/interlock-core/src/trip.rs": "pub fn trip(x: f64) -> bool { x > 1.0 }\n",
    "crates/telemetry/Cargo.toml": """[package]
name = "telemetry"
version = "0.1.0"
edition.workspace = true

[dependencies]
log = { workspace = true }
""",
    "crates/telemetry/build.rs": "fn main() {}\n",
    "crates/telemetry/src/lib.rs": "pub fn emit() {}\n",
    "plant/Cargo.toml": """[package]
name = "plant-agent"
version = "0.1.0"
edition = "2021"

[workspace]
exclude = ["fuzz"]

[dependencies]
interlock-core = { path = "../crates/interlock-core", version = "0.1.0" }
serde = "1"
anyhow = "1"

[features]
default = []
strict = ["interlock-core/strict"]
verbose = []
""",
    "plant/Cargo.lock": """version = 4

[[package]]
name = "plant-agent"
version = "0.1.0"
dependencies = ["interlock-core", "serde", "anyhow"]

[[package]]
name = "interlock-core"
version = "0.1.0"

[[package]]
name = "serde"
version = "1.0.1"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "aa"

[[package]]
name = "anyhow"
version = "1.0.0"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "cc"
""",
    "plant/build.rs": "fn main() {}\n",
    "plant/src/main.rs": """#![cfg_attr(not(test), deny(warnings))]
// mod decoy; in a comment, "mod decoy;" in a string
mod config;
mod failsafe;
#[cfg(test)]
mod tests;

fn main() { config::load(); failsafe::enter(); }
""",
    "plant/src/config.rs": "pub fn load() {}\n",
    "plant/src/tests.rs": "#[test]\nfn t() {}\n",
    "plant/src/failsafe.rs": """mod limits;
const TABLE: &str = include_str!("failsafe_table.json");
pub fn enter() { limits::check(TABLE); }
""",
    "plant/src/failsafe/limits.rs": "pub fn check(_t: &str) {}\n",
    "plant/src/failsafe_table.json": "{}\n",
    "plant/fuzz/Cargo.toml": """[package]
name = "plant-fuzz"
version = "0.0.0"

[workspace]
members = ["."]

[dependencies]
plant-agent = { path = ".." }
""",
    "plant/fuzz/fuzz_targets/a.rs": "fn main() {}\n",
}


def tree(files):
    blobs = {p: v.encode() if isinstance(v, str) else v for p, v in files.items() if v is not None}
    return bf.Tree(tuple(sorted(blobs)), blobs.get)


def head(**edits):
    """BASE with ``edits``: a path (``/`` written ``__``, ``.`` as ``_dot_``, the crate ``interlock-core`` as
    ``interlock_core``) to new text or to a function of its old text, or to None to delete it."""
    files = dict(BASE)
    for name, text in edits.items():
        path = name.replace("interlock_core", "interlock-core").replace("__", "/").replace("_dot_", ".")
        if text is None:
            files.pop(path, None)
        else:
            files[path] = text(files.get(path, "")) if callable(text) else text
    return files


def fenced(files, owner=OWNER):
    changed = sorted(p for p in set(BASE) | set(files) if BASE.get(p) != files.get(p))
    return bf.fenced(changed, owner, tree(BASE), tree(files))


class ModuleChainTest(unittest.TestCase):
    """The files above a fenced module: what of them loads it, and nothing else of them."""

    def test_a_path_attribute_or_a_cfg_on_the_declaration_redirects_or_drops_the_fenced_module(self):
        # chain_view_ignored chain_parent_unfenced
        main = "plant/src/main.rs"
        for edit in ('#[path = "elsewhere.rs"]\nmod failsafe;', '#[cfg(any())]\nmod failsafe;',
                     '#[cfg_attr(unix, path = "elsewhere.rs")]\nmod failsafe;', "mod failsafe_v2;",
                     "mod failsafe {}"):
            with self.subTest(edit=edit):
                self.assertEqual(fenced(head(plant__src__main_dot_rs=lambda t: t.replace("mod failsafe;", edit))),
                                 [main])
        self.assertEqual(fenced(head(plant__src__main_dot_rs=lambda t: "macro_rules! guard { () => {} }\n" + t)),
                         [main])  # a module declared after a macro sees it
        self.assertEqual(fenced(head(plant__src__main_dot_rs=lambda t: "#![allow(unused)]\n" + t)), [main])
        self.assertEqual(fenced(head(plant__src__main_dot_rs=None)), [main])

    def test_an_honest_edit_of_the_crate_root_stays_open(self):  # chain_parent_fenced_whole
        """A new module, a new function, a comment: the crate root of a large binary is edited all the time."""
        for edit in (lambda t: t.replace("mod config;", "mod config;\nmod extra;"),
                     lambda t: t + "\nfn helper() -> u8 { 1 }\n", lambda t: "// a comment\n" + t,
                     lambda t: t.replace("mod config;", '#[path = "cfg.rs"]\nmod config;')):
            with self.subTest(edit=edit):
                self.assertEqual(fenced(head(plant__src__main_dot_rs=edit)), [])

    def test_everything_below_a_fenced_module_and_every_file_it_includes(self):  # module_children_unfenced
        self.assertEqual(fenced(head(plant__src__failsafe__limits_dot_rs="pub fn check(_t: &str) { todo!() }\n")),
                         ["plant/src/failsafe/limits.rs"])
        self.assertEqual(fenced(head(plant__src__failsafe_table_dot_json='{"x": 1}\n')),
                         ["plant/src/failsafe_table.json"])
        self.assertEqual(fenced(head(plant__src__config_dot_rs="pub fn load() { panic!() }\n")), [])

    def test_the_other_file_a_declaration_could_load(self):  # module_alternative_unfenced
        """`mod failsafe;` loads `failsafe.rs` or `failsafe/mod.rs`; the owner's pattern names one of them."""
        self.assertEqual(fenced(head(plant__src__failsafe__mod_dot_rs="pub fn enter() {}\n")),
                         ["plant/src/failsafe/mod.rs"])

    def test_the_whole_crate_of_a_fenced_directory(self):
        files = head()
        files["crates/interlock-core/src/new.rs"] = "pub fn n() {}\n"
        self.assertEqual(fence.touches_safety(["crates/interlock-core/src/new.rs"], OWNER),
                         ["crates/interlock-core/src/new.rs"])  # the owner's list itself


class ManifestTest(unittest.TestCase):
    """The manifests that point at the fenced crates, and the roots their builds run in."""

    def test_a_dependent_that_points_the_fenced_name_elsewhere(self):
        for edit in (lambda t: t.replace("../crates/interlock-core", "../crates/interlock-core-v2"),
                     lambda t: t.replace('interlock-core = { path = "../crates/interlock-core", version = "0.1.0" }',
                                         'interlock-core = { version = "0.1.0" }'),
                     lambda t: t.replace("interlock-core = {", 'interlock-core = { package = "other",'),
                     lambda t: t.replace('strict = ["interlock-core/strict"]', 'strict = []')):
            with self.subTest(edit=edit):
                self.assertEqual(fenced(head(plant__Cargo_dot_toml=edit)), ["plant/Cargo.toml"])

    def test_a_dependents_other_entries_stay_open_unless_it_is_fenced_itself(self):
        # dependent_view_entries_dropped fenced_manifest_partial
        """`plant-agent` holds fenced modules, so its own manifest is fenced whole; a dependent that holds none is
        fenced only where it names the fenced crate."""
        self.assertEqual(fenced(head(plant__Cargo_dot_toml=lambda t: t + 'regex = "1"\n')), ["plant/Cargo.toml"])
        owner = ["crates/interlock-core/"]
        self.assertEqual(fenced(head(plant__Cargo_dot_toml=lambda t: t.replace('anyhow = "1"', 'anyhow = "1.0.9"')),
                                owner), [])
        self.assertEqual(fenced(head(plant__Cargo_dot_toml=lambda t: t.replace("verbose = []", "verbose = [\"x\"]")),
                                owner), [])
        self.assertEqual(fenced(head(plant__Cargo_dot_toml=lambda t: t.replace("../crates/interlock-core", "../x")),
                                owner), ["plant/Cargo.toml"])

    def test_the_workspace_root_patches_profiles_and_inherited_fields(self):  # root_view_ignored
        for edit in (lambda t: t + '\n[patch.crates-io]\ninterlock-core = { path = "vendor/x" }\n',
                     lambda t: t + "\n[profile.release]\noverflow-checks = false\n",
                     lambda t: t.replace('edition = "2021"', 'edition = "2018"'),
                     lambda t: t.replace('resolver = "2"', 'resolver = "1"'),
                     lambda t: t + '\n[replace]\n"serde:1.0.1" = { path = "x" }\n'):
            with self.subTest(edit=edit):
                self.assertEqual(fenced(head(Cargo_dot_toml=edit)), ["Cargo.toml"])

    def test_an_honest_root_edit_stays_open(self):  # dev_dependencies_built
        for edit in (lambda t: t.replace('log = "0.4"', 'log = "0.4.2"'),  # a shared entry no fenced crate builds
                     lambda t: t.replace('serde = "1"', 'serde = "1.0.200"'),  # a fenced crate's dev-dependency
                     lambda t: t.replace('"crates/telemetry"]', '"crates/telemetry", "crates/new"]')):
            with self.subTest(edit=edit):
                self.assertEqual(fenced(head(Cargo_dot_toml=edit)), [])

    def test_a_package_that_takes_a_fenced_name(self):  # fenced_name_taken
        self.assertEqual(fenced(head(crates__fresh__Cargo_dot_toml='[package]\nname = "interlock_core"\n')),
                         ["crates/fresh/Cargo.toml"])
        self.assertEqual(fenced(head(crates__fresh__Cargo_dot_toml='[package]\nname = "fresh"\n',
                                     crates__fresh__src__lib_dot_rs="pub fn f() {}\n")), [])

    def test_the_workspace_root_a_fenced_crate_builds_in(self):  # workspace_root_moved_unfenced
        """Excluded from its workspace, the fenced crate builds as its own root: no patch or profile of the old root
        reaches it any more, and nothing in that root's view changed. A new root that captures it is a root too."""
        files = head(Cargo_dot_toml=lambda t: t.replace('exclude = ["plant",',
                                                        'exclude = ["crates/interlock-core", "plant",'))
        self.assertEqual(fenced(files), ["Cargo.toml"])
        files = head(crates__Cargo_dot_toml='[workspace]\nmembers = ["interlock-core"]\n')
        self.assertEqual(fenced(files), ["crates/Cargo.toml"])

    def test_a_manifest_that_does_not_parse(self):
        self.assertEqual(fenced(head(crates__telemetry__Cargo_dot_toml="[package\n")),
                         ["crates/telemetry/Cargo.toml"])


class BuildTest(unittest.TestCase):
    """What runs or is read while the fenced code builds: build scripts, proc-macros, cargo and rustup files."""

    def test_build_scripts_of_every_package_built_beside_the_fenced_ones(self):  # build_script_unfenced
        self.assertEqual(fenced(head(plant__build_dot_rs="fn main() { std::fs::write(\"x\", \"\").ok(); }\n")),
                         ["plant/build.rs"])
        self.assertEqual(fenced(head(crates__telemetry__build_dot_rs="fn main() { panic!() }\n")),
                         ["crates/telemetry/build.rs"])  # a member of the fenced crate's workspace
        self.assertEqual(fenced(head(crates__interlock_core__build_dot_rs=None)), [])  # never there
        added = head(crates__telemetry__src__lib_dot_rs="pub fn emit() { }\n")
        self.assertEqual(fenced(added), [])

    def test_a_new_member_with_a_build_script(self):  # member_build_script_unfenced
        files = head(Cargo_dot_toml=lambda t: t.replace('"crates/telemetry"]', '"crates/telemetry", "crates/new"]'),
                     crates__new__Cargo_dot_toml='[package]\nname = "new"\nversion = "0.1.0"\n',
                     crates__new__build_dot_rs="fn main() {}\n", crates__new__src__lib_dot_rs="")
        self.assertEqual(fenced(files), ["crates/new/build.rs"])

    def test_a_proc_macro_crate_built_beside_them(self):
        files = head(crates__telemetry__Cargo_dot_toml=lambda t: t + "\n[lib]\nproc-macro = true\n")
        self.assertEqual(fenced(files), ["crates/telemetry/Cargo.toml"])  # its code runs in the compiler from then on
        later = dict(files, **{"crates/telemetry/src/lib.rs": "pub fn emit() { /* now a macro */ }\n"})
        changed = ["crates/telemetry/src/lib.rs"]
        self.assertEqual(bf.fenced(changed, OWNER, tree(files), tree(later)), changed)

    def test_cargo_and_rustup_configuration_above_every_build(self):  # build_config_unfenced
        self.assertEqual(fenced(head(_dot_cargo__config_dot_toml=lambda t: t + '[env]\nLIMIT = "9"\n')),
                         [".cargo/config.toml"])
        for path in ("plant/.cargo/config.toml", "plant/.cargo/config", "crates/interlock-core/.cargo/config.toml",
                     "plant/rust-toolchain.toml", "rust-toolchain"):
            with self.subTest(path=path):
                files = head()
                files[path] = "[build]\nrustflags = [\"--cfg\", \"x\"]\n"
                self.assertEqual(fenced(files), [path])
        files = head()
        files["crates/telemetry/.cargo/config.toml"] = "[build]\n"
        self.assertEqual(fenced(files), [])  # read only by a build started there, which builds no fenced crate


class LockTest(unittest.TestCase):
    def test_a_lock_entry_the_fenced_build_compiles(self):  # lock_view_ignored lock_seeds_any_root
        """`plant/Cargo.lock` resolves the fenced binary's `serde`; the root lock's `serde` is a dev-dependency of
        the fenced library, and its `log` belongs to another member: neither is in what the fenced code compiles."""
        bump = lambda t: t.replace('version = "1.0.1"', 'version = "1.0.2"')  # noqa: E731
        self.assertEqual(fenced(head(plant__Cargo_dot_lock=bump)), ["plant/Cargo.lock"])
        self.assertEqual(fenced(head(Cargo_dot_lock=bump)), [])
        self.assertEqual(fenced(head(Cargo_dot_lock=lambda t: t.replace('"0.4.1"', '"0.4.2"'))), [])
        self.assertEqual(fenced(head(Cargo_dot_lock=lambda t: t.replace('name = "interlock-core"\nversion = "0.1.0"',
                                                                      'name = "interlock-core"\nversion = "0.2.0"'))),
                         ["Cargo.lock"])
        self.assertEqual(fenced(head(plant__Cargo_dot_lock="not toml [")), ["plant/Cargo.lock"])


class RustReadingTest(unittest.TestCase):
    """Declarations are read past comments, strings, raw strings, characters and lifetimes."""

    def test_only_real_declarations_count(self):  # rust_comment_read_as_code
        text = """
// mod line_comment;
/* mod block; /* nested */ mod still_comment; */
const S: &str = "mod in_string;";
const R: &str = r#"mod in_raw; "# ;
fn f<'a>(x: &'a str) -> char { let _ = x; '{' }
#[cfg_attr(feature = "x", path = "other.rs")]
pub(crate) mod real;
mod r#type;
mod inline { #[path = "deep.rs"] mod inner; mod nested; }
mod after;
"""
        read = bf.scan(text)
        self.assertEqual([(d.name, d.inline, d.paths) for d in read.decls],
                         [("real", (), ("other.rs",)), ("type", (), ()), ("inner", ("inline",), ("deep.rs",)),
                          ("nested", ("inline",), ()), ("after", (), ())])
        self.assertEqual(bf.scan('const T: &[u8] = include_bytes!("a/b.bin");').includes, ("a/b.bin",))

    def test_where_a_declaration_loads_from(self):
        decl = bf.Decl("m", (), (), "", False)
        self.assertEqual([o for o, _k in bf.options("p/src/main.rs", "root", decl)], ["p/src/m.rs", "p/src/m/mod.rs"])
        self.assertEqual([o for o, _k in bf.options("p/src/a.rs", "nonmodrs", decl)],
                         ["p/src/a/m.rs", "p/src/a/m/mod.rs"])
        inline = bf.Decl("m", ("i",), ("x.rs",), "", False)
        self.assertEqual([o for o, _k in bf.options("p/src/a.rs", "nonmodrs", inline)], ["p/src/a/i/x.rs"])
        self.assertEqual([o for o, _k in bf.options("p/src/a.rs", "nonmodrs", bf.Decl("m", (), ("../../q.rs",), "",
                                                                                         False))], ["q.rs"])
        self.assertEqual([o for o, _k in bf.options("src/a.rs", "root", bf.Decl("m", (), ("../../x.rs",), "",
                                                                                   False))], [None])

    def test_nothing_of_the_tree_runs(self):
        """No cargo, no rustc, no subprocess: `cargo metadata` would run a tree's `build.rustc`."""
        source = Path(bf.__file__).read_text(encoding="utf-8")
        for word in ("subprocess", "os.system", "import os", "exec(", "eval("):
            self.assertNotIn(word, source)


class TargetShapeTest(unittest.TestCase):
    def test_the_fixture_is_a_layout_cargo_would_read(self):
        """The fixture's manifests and locks parse, and its fenced packages and roots are the ones the docstring
        names, so the tests above measure the rules and not a broken fixture."""
        side = bf._side(bf.Graph.of(tree(BASE)), OWNER)
        self.assertEqual(sorted(p.directory for p in side.fenced), ["crates/interlock-core", "plant"])
        self.assertEqual(sorted(r.directory for r in side.roots), ["", "plant", "plant/fuzz"])
        json.dumps(sorted(side.whole))


if __name__ == "__main__":
    unittest.main()
