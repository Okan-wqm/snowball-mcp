# Politika Başlangıç Değerleri

Tarih: 2026-10-28 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: kurulumda `policy.json` yazılırken ve bir eşiğin ilk değeri aranırken
Çapa: beklemede: aşama 0 — hakem reposundaki policy.json; şema `26b`

---

`policy.json`'un her anahtarı burada bir başlangıç değeriyle durur; anahtarı olmayan eşik
yoktur. Anayasal değerleri operatör kurulumda yazar (`25`); bu tablo onun önerisidir. Performans
değerleri `18`'deki prosedürle değişir. Adlar `26b` şemasıyla aynıdır.

## Anayasal (`constitutional`)

| Anahtar | Başlangıç | Okuyan |
|---|---|---|
| `monthly_cap_usd` | Operatör yazar; öneri 300 USD | `06`, Gözcü (`28`) |
| `monthly_cap_ci_minutes` | 1.800 dk (Free özel repo kotası 2.000) | `01b`, `06`, `28` |
| `session_cap_usd` | Kurucu oturumu başına 20 USD | `24` |
| `shares` | Keşif ≤ %30, üretim ≤ %40, ölçüm ≤ %20, genel ≤ %10 | `06` |
| `class_floors.K0` | `{kind: census, misses: 0}`; clean'de FP 0 | `19`, aşama çıkışları |
| `class_floors.K1`, `K2`, `K4` | Kural sayımı, sıfır kaçırma (deterministik sarıcı, `19`) | `19` |
| `class_floors.K5`, `K6` | `recall_lb` ≥ 0,50 (`human_fix` katmanı, ≥ 25 vaka, ≥ 10 grup); `precision_lb` ≥ 0,60 | `19`, `asama-4/08` |
| `class_floors.K3`, `K7`, `K8` | Sınıfın aşama spec'i donmadan operatör yazar; yazılmadan aşama açılmaz | `02`, `lock.check` |
| `required_exit_rows` | `18`'deki yetenek tablosu | `spec.lint` (`02`) |
| `noninferiority_margin` | δ = 0,05 | `06`, `19` |
| `n_min_paired` | 45 | `06`, `19` |
| `mcnemar_min_discordant` | 8 | `12`, `17`, `19` |
| `confidence_level` | 0,90, tek yönlü | `19` |
| `look_budget` | Held-out havuzu başına 3 bakış; k. bakışta α/k | `19` |
| `survival_windows` | K0, K1, K2, K4: 72 saat; K3, K7, K8: 7 gün; K5, K6: 14 gün; yalnız uzar | `07`, `11` |
| `regression_freeze` | ≥ 50 merge varken 30 günde geri alma > %2; < 50 iken pencerede ≥ 2 geri alma | `20`, `28` |
| `cycle_caps` | Döngü başına PR ≤ 10, merge ≤ 5, CI ≤ 60 dk | `01b` |
| `daily_caps` | Gün başına PR ≤ 30, merge ≤ 15, CI ≤ 90 dk | `01b` |
| `security_keywords` | `14`'teki liste | `14`, `profile.derive` |
| `banned_phrases` | `23`'teki liste | `04a` 9, `spec.lint` |
| `stage_order` | 0 → 1 → 2 → 3 → 4 → 5 → 6 (`03`) | `lock.check` |
| `gate_rules.ratio_bootstrap_lb` | Değer / USD yolu: eşli bootstrap alt sınırı ≥ 1,2 | `12`, `17`, `19` |
| `gate_rules.membership_auc` | ε = 0,05; ≥ 200 aday; α = 0,10 | `19` (kendi-test 18) |
| `gate_rules.audit_sample` | Gizli tohumla %10 tekdüze denetim; bütçe ≥ 40 çözülmüş denetimden sonra | `19` |
| `gate_rules.promotion` | ≥ 4 repo hepsi lehte ya da ≥ 5; repo başına δ = 0,05; BH q = 0,10 | `21a` |
| `gate_rules.soft_freeze_limit` | Pencerede 2'den fazla yumuşak dondurma → sert duruş | `28` |
| `gate_rules.containment_freeze` | Aynı pencerede 2 kapsayıcılık ihlali → yumuşak dondurma | `08`, `28` |
| `gate_rules.gross_delete_cap` | Aday başına brüt silme ≤ 200 satır (K2 silmeleri hariç) | `04a` 9 |
| `stage_params.census_min_groups` | 45 modül grubu ya da mevcut olanın tamamı | `asama-0/04`, `exit.sample` |
| `stage_params.planted_max_cases` | Snapshot başına 5 vaka | `asama-0/06` |
| `stage_params.evidence_ref_max_lines` | Birincil ref ≤ 30 satır | `asama-0/07` |
| `stage_params.match_window_lines` | K3 ve üstü eşleme penceresi ±15 satır | `asama-0/08` |
| `stage_params.rival_min_attempts` | Aşama başına 5 ayrı artefakt, artefakt başına 1 deneme | `asama-0/10`, `29` |
| `stage_budgets` | Aşama sayfalarının bütçe tabloları; toplamdır, aylık tavan ayrıca bağlar | aşama bütçe sayfaları, Gözcü |

## Performans (`performance`)

| Anahtar | Başlangıç | Okuyan |
|---|---|---|
| `windows.measure` | Ölçüm penceresi 14 gün | `11`, `12`, `17`, `28` |
| `rules.recall_gate`, `rules.precision_gate` | `18`'deki örnek kurallar | `12`, kapı |
| `shadow_min_runs` | Pencere başına koşu sayısının yarısı, en az 3 | `12` |
| `shadow_max_windows` | 4 pencere; sonunda SHADOW → RETIRED | `12` |
| `ablation_margin` | Katkının %90 üst sınırı < 0,02 bileşik skor → emeklilik | `12` |
| `lambda` | 0,5 değer birimi / USD | `11` |
| `beta_prior` | Beta(1, 1) | `11` |
| `rules.reputation_half_life` | 30 gün; yalnız yeni karar varken işler | `11` |
| `shadow_discount` | 0,5 | `11`, `12` |
| `severity_map` | CRIT 10, HIGH 5, MED 2, LOW 1, lint 0,05 | `11`, `17`, `20` |
| `op_allow` | K0 `lint_fix`; K1 `lint_fix`, `change_type`; K2 `remove`; K5–K6 `doc_fix` dışı hepsi; K8 `doc_fix` | `04a` 8, `26` |
| `cheapest_model` | `claude-haiku-5-5`; yalnız panel faz 1–2 | `06`, `09` |
| `effort` | Kurucu `high`; rakip `medium`; panel koltuğu `low`; düzeltici `low` | `24`, `10a` |
| `rules.max_turns` | Rakip 30, avcı 60, panel koltuğu 12 | `24` |
| `rules.gap_rule` | gap ≥ 0,2 iki pencere üst üste ve havuz ≥ 20 vaka | `17` |
| `signal_thresholds` | `17`'deki tablonun eşik sütunu | `17` |
| `rules.drift_bound` | Bir eşiğin başlangıçtan net hareketi > %20 → Gözcü işareti | `18` |
| `rules.probe_cycle` | Sonda döngüsü başına 5 düzeltme; üst üste 2 temiz → kalkış | `28` |
| `rules.lesson_n_min` | Ders başına kol başına 250 koşu; altında UNMEASURABLE | `22` |
| `rules.seat_similarity` | Karar ve referans benzerliği > 0,8 → Gözcü işareti | `09a` |
| `rules.genesis_drafts` | Pencere başına ≤ 3 taslak; kuyruk derinliği ≤ 10 | `12`, `17` |
| `rules.lease_ttl` | Görev kirası 2 saat | `16` |
| `rules.bisect` | Adım ≤ 15 dk, en çok 12 adım; bisect açılınca okunur | `07` |
