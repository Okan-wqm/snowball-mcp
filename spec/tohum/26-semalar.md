# Şemalar, Araç İmzaları, Kanonik Biçimler

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 inşasında ve her şema değişikliğinde
Çapa: beyin reposundaki schemas/ dizini; harness kendi-testi 'şema'

---

Kurucu'nun tutarsız icat etmemesi için sabitlenen biçimler. Hepsi JSON Schema olarak beyin
reposunda `schemas/` altında durur ve harness'in kendi-testleri her artefaktı şemaya karşı
doğrular. Alan adları İngilizcedir.

**finding** (agent format, `findings.jsonl`): `finding_id`, `fingerprint`, `class_level`
(K0–K8), `property`, `tool`, `rule_id` (K0–K2 için zorunlu), `claim`, `evidence_refs`
`[{path, line_start, line_end}]`, `required_change` `{file, symbol, op}` (`op` kapalı küme:
`add_guard`, `remove`, `rename`, `change_type`, `move`, `add_test`, `other`), `severity`,
`confidence`, `derivation`, `trust`. İnsan formatı `docs/findings/<fingerprint>.md`
(`15-dokumantasyon.md`).

**case** (`cases.jsonl`): `case_id`, `class_level`, `property`, `provenance`
(`human_fix` | `mutation` | `system_tp` | `system_regression`), `base_sha`, `fix_sha?`,
`mutation_id?`, `touched_paths` `[{path, hunks:[{start,end}], symbol?}]`, `rule_id?`,
`severity`, `validity_evidence` `{kind, ref, output_sha256}`, `split` (`dev` | `heldout`),
`group` (modül ya da mutasyon operatörü).

**run_meta**: `run_id`, `organ_id`, `role`, `model_requested`, `model_served`, `effort`,
`prompt_sha256`, `rung`, `snapshot_id`, `tokens_in`, `tokens_out`, `cost_usd`, `wall_clock_s`,
`files_read`, `lessons_read`, `previous_run_ref` (boş), `containment` `{paths_written[],
commands[], network_attempts[], declared_exits[]}`.

**ledger row** (her defter): `row_id`, `ts`, `kind`, `payload`, `derivation`, `trust`,
`snapshot_id`, `cause?`, `derived_from?`, `prev_hash`, `row_hash`. Kanonikleştirme RFC 8785;
hash SHA-256; `row_hash = sha256(canonical(row − row_hash) ‖ prev_hash)`.

**organ registry row**: `organ_id` (hash), `kind`, `state`, `born_from` `{signal, measurement}`,
`definition_sha256`, `model`, `tools[]`, `derived_from?`, `transition_evidence`.

**reputation row**: `organ_id`, `window`, `class_level`, `weighted_value`, `usd`, `n_decided`,
`beta_lower_bound`, `rank_in_class?`.

**heldout.seal.json**: `seal_id`, `hmac_sha256` (CI sırrıyla), `case_count`, `created_at`,
`looks_used`, `rotation_due`; vaka listesi bu dosyada değil, mühürlü depodadır.

**profile.json**: `languages{}`, `toolchains{lang: {lint[], typecheck[], test[], format[],
build[]}}`, `affected_test_cmd`, `graph_cmd`, `ci_system`, `runner`, `security_paths[]`,
`excluded_dirs[]`, `state_root`, `dependency_cache`, `bootstrap_done{}`, `readers{file: [organ]}`.

**MCP araç imzaları** (`24-calisma-modeli.md` listesi): her araç `{input_schema, output_schema,
side_effects[], allowed_callers[]}` ile tanımlanır; `allowed_callers` boş olan araç yoktur.
`harness.score` held-out için `allowed_callers = ["ci:exit"]`.

**status.md şablonu (aşama başına büyür):** başlık ve döngü kimliği; son döngü sonucu ve
maliyeti; `blocked` listesi ve nedenleri; kapsama oranı; zincir durumu; Aşama 1'den itibaren lig
tablosu ve değer / USD; Aşama 2'den itibaren eğilimler ve "geçen yıl bugün".

**Mutasyon kataloğu (K0)** ve **taban avcının grep kümesi** harness reposunda sürümlü dosyalar
olarak durur; her ikisi de hedef repoya özgü değil, araç başınadır.
