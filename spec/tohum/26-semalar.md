# Şemalar ve Kanonik Biçimler

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 inşasında ve her şema değişikliğinde
Çapa: beklemede: aşama 0 — hakem reposundaki schemas/

---

Hepsi JSON Schema olarak hakem reposunda `schemas/` altındadır; harness her artefaktı şemaya karşı
doğrular. Alan adları İngilizce. Araç imzaları `26a`'da.

**finding**: `finding_id`, `fingerprint`, `state` (`open`|`fixed`|`verified`|`reopened`|`withdrawn`),
`class_level` (K0–K8), `property`, `file`, `symbol?`, `tool?`, `rule_id?`, `claim`, `evidence_refs`
`[{path, line_start, line_end}]`, `required_change` `[{file, symbol?, op}]` (`op`: `lint_fix`,
`add_guard`, `remove`, `rename`, `change_type`, `move`, `add_test`, `other`; sınıf başına izinli küme
`policy.json`'da), `severity_hint`, `confidence`, `derivation`, `trust`, `snapshot_id`.
`confidence`'in okuyucusu panelin faz sıralamasıdır.

**case**: `case_id`, `class_level`, `property`, `provenance` (`human_fix`|`mutation`|`system_tp`|
`system_regression`), `base_sha`, `fix_sha?`, `mutation_id?`, `touched_paths`
`[{path, hunks:[{start,end}], symbol?}]`, `rule_id?`, `validity_evidence` `{kind, ref, output_sha256}`,
`split`, `group`.

**run_meta**: `run_id`, `subject_run_id?`, `organ_id`, `role`, `model_requested`, `model_served`,
`effort`, `prompt_sha256`, `rung`, `snapshot_id`, `tokens_in`, `tokens_out`, `cost_usd`,
`wall_clock_s`, `files_read`, `lessons_injected`, `previous_run_ref` (boş), `containment`
`{paths_written[], commands[], network_attempts[], declared_exits[]}`. Model ve ders alanlarını
dispatcher yazar.

**ledger row** (tüm bölümler): `row_id`, `ts`, `part` (`events`|`cost`|`containment`|`founder`|
`genesis`|`freeze`|`map`|`coverage`|`lessons`), `kind`, `payload`, `derivation`
(`tool`|`static_analysis`|`test_verified`|`llm_inference`|`name_similarity`), `trust`
(`verified`|`observed`|`inferred`), `snapshot_id`, `evidence_refs`, `cause?`, `derived_from?`,
`prev_hash`, `row_hash`. Kanonik biçim RFC 8785; `row_hash = sha256(canonical(row − row_hash) ‖
prev_hash)`, küçük harf onaltılık; ilk satırın `prev_hash`'i 64 sıfır.

**cause** (kapalı küme): `test_regression`, `contract_counterpart`, `build_break`,
`lint_regression`, `flaky_dependency`, `conflict_with_main`, `scope_violation`, `unknown`.

**lesson**: `lesson_id`, `claim`, `cause`, `scope` `{class_level, property, path_glob}`,
`evidence_refs`, `origin_event`, `hit`, `miss`, `withheld_hit`, `withheld_miss`, `superseded_at?`,
`derived_from?`.

**map edge**: `edge_id`, `layer` (a|b|c|d), `from`, `to`, `kind`, `evidence_refs`, `derivation`,
`trust`, `snapshot_id`, `stale`. **coverage**: `path`, `fate` (`seen`|`unseen`|`coarse`|
`excluded`), `by_rungs[]`, `snapshot_id`.

**organ registry**: `organ_id`, `kind`, `state`, `born_from` `{signal, measurement}`,
`definition_sha256`, `model`, `tools[]`, `derived_from?`, `transition_evidence`.
**reputation**: `organ_id`, `window`, `class_level`, `rung`, `weighted_value`, `usd`, `n_decided`,
`beta_lower_bound`, `rank_in_class?`.

**harness report**: `run_id`, `snapshot_id`, `spec_version`, `match_rule_version`, `hunter_id`,
`prompt_sha256`, `rung`, `n`, `n_groups`, `recall`, `recall_lb`, `precision`, `precision_lb`,
`clean_findings`, `unresolved`, `cost_usd`, `value_per_usd`, `verdict`.

**profile.json**: `languages{}`, `toolchains{lang: {lint[], typecheck[], test[], format[], build[],
coverage[]}}`, `affected_test_cmd`, `graph_cmd`, `graph_granularity`, `test_path_rules[]`,
`banned_constructs{lang: []}`, `rule_property_map{tool: {rule_id: property}}`, `finding_id_patterns[]`, `security_paths[]`, `excluded_dirs[]`,
`registry_egress[]`, `ci_system`, `runner`, `state_root`, `dependency_cache`,
`readers{file: [organ|role]}`.

**policy.json**: `constitutional{monthly_cap_usd, shares, class_floors{K0..K8:{recall, precision}},
regression_freeze, cycle_caps, daily_caps, security_keywords[], banned_phrases[], stage_order,
look_budget, confidence_level}`, `performance{rules{name: expr}, windows{}, lambda, beta_prior,
shadow_discount, survival_windows{}, severity_map{}, op_allow{}, cheapest_model, effort{}}`.

**contract**: `contract_id`, `producer`, `consumer`, `schema_ref`, `state` (`proposed`|`frozen`),
`tests[]`.

**heldout.seal.json**: `seal_id`, `hmac_sha256`, `case_count`, `created_at`, `looks_used`,
`rotation_due`, `cutoff_ts`; vaka listesi mühürlü depodadır.
