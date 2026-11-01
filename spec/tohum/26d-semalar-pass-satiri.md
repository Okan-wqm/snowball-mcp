# Şemalar, Devam: Aşama 0'ın PASS Satırı ve Kilidin Açılışı

Tarih: 2026-11-01 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın (B) devirlerini ve PASS satırını yazan kod yazılırken; kilidin açılışından önce
Çapa: beklemede: aşama 0 — oyuncağın `brain/state`'indeki PASS satırı; `setup/stage.json`

---

`26`, `26b` ve `26c`'nin devamıdır; aynı kurallar geçerlidir. PASS satırını döngü hakemi yazar (`asama-0/10a` #pass,
`asama-0/08` devir 9); operatörün `stage-open` komutu onu okur ve `setup/stage.json`'u yalnız aşağıdaki kural tutarsa
yazar (`25a` 9, `02` 5). Bu sayfa `asama-0/10a`'nın PASS satırını alan alan söyler; aşama sayfası tohumla çelişirse
tohum geçerlidir (`02` 1).

**PASS satırı.** Oyuncak hedefin `<state_root>/ledger.jsonl`'unda `26`'nın bir defter satırı, `part: events`; `kind`
serbesttir. `payload` bir nesnedir ve şu alanları taşır (başka alan da taşıyabilir):
- `stage`: tamsayı `0` (mantıksal değer değil); `verdict`: dizgi `"PASS"` (`19`).
- `import_line_sha256`: 64 küçük onaltılık; PASS yazıldığında `setup/imports.jsonl`'un son aktarım satırının
  (`referee_tree_sha256` taşıyan son satır, `29n`) LF'siz baytlarının sha256'sı; genesis yükündeki aynı adlı alanın
  kuralı (`29o`). Güven kökünün operatör aktarımıdır (`10a` #pass).
- `copy_genesis_row_hash`: 64 küçük onaltılık; kopya hedefin defterinin ilk satırının (genesis, `25a` 7) `row_hash`'i.
- `copy_merge_row_hashes`: dizgi dizisi, en az bir eleman, her biri bir kez; her eleman kopyanın defterinde genesis'ten
  sonra gelen bir merge satırının `row_hash`'i.
- `owner_exception`: (A) sonucunun `exit.owner_exception` nesnesi aynen, `{anchor, stage, carry_to, reason,
  carry_commitment, measured}` (`02` "Sahip istisnası"; `anchor` `#`'siz yazılır: `durustluk`). (A) sonucunda yoksa
  PASS satırında da yoktur.

**Hakemin kendi satırı.** `proposed_by` taşımaz; `trust` `verified` ya da `observed`'dır (`inferred` oyuncunun
önerisinin saklandığı değerdir, `26`); `derivation` `tool`, `static_analysis` ya da `test_verified`'dır (`26`: merge
kararına giren kanıtın üçü). PASS satırı ve merge satırları hakemin kendi satırlarıdır. **Merge satırı**: `part:
events`, `kind: merge` olan hakemin kendi satırı; `payload`'ı serbesttir.

**`stage-open`'ın kuralı.** Komut iki hedefin `brain/state` başını operatörün yerel klonunda okur, iki defterin ve iki
kök zincirinin her satırını tohumun koduyla doğrular (`26`) ve şunları denetler; biri tutmazsa nedeni adlandırıp
durur (çıkış 2) ve hiçbir şey yazmaz:
1. Sayacın son aktarım satırı Aşama 0'ındır; `--result` o satırın `result_sha256`'sının adlandırdığı imzalı (A)
   sonucudur.
2. Her hedef defterinin ilk satırı genesis'tir: `payload.target` `setup/summary.json` `targets[]`'taki o hedefin
   `id`'si (bir oyuncak, bir kopya), kopyada `payload.base_sha` o satırın `base_sha`'sı, ikisinde de
   `payload.import_line_sha256` sayacın son aktarım satırınınkidir (`29o`).
3. `proposed_by` taşıyan satırlar ayrıldıktan sonra oyuncak defterinde `payload.stage` 0 ve `payload.verdict` `"PASS"`
   olan tam bir `events` satırı vardır; oyuncunun önerdiği bir kopyası sayılmaz.
4. O satır hakemin kendi satırıdır ve oyuncak defterinde ondan önce en az bir merge satırı vardır (`asama-0/08`: merge
   devir 2, PASS devir 9).
5. PASS satırının `import_line_sha256`'sı sayacın son aktarım satırınınkidir. Sonra yazılmış, ya da geri alınıp yerine
   başkası gelmiş bir aktarım bu satırı değiştirir; PASS satırı başka bir aktarımı adlandırıyorsa kilit açılmaz.
6. `copy_genesis_row_hash` verilen kopya klonunun genesis'inin, `copy_merge_row_hashes` o defterin genesis'ten sonraki
   merge satırlarınındır.
7. `owner_exception` (A) sonucununkiyle RFC 8785 baytlarıyla aynıdır ya da ikisinde de yoktur.
8. Her hedefte son kök satırının `root`'u defterin uçlarının köküdür (`13`, `29j`) ve operatörün verdiği Sigstore
   paketi `--identity` ile `sha256:<kök>` özetini doğrular; paketin tek saydamlık kaydının yaprak hash'i satırın
   `rekor_uuid`'idir ve gövdesi `spec.data.hash`'i `{algorithm: sha256, value: <kök>}` olan bir `hashedrekord`'dur.
   Bu biçimde olmayan bir kayıt (başka bir tür ya da gövde biçimi) kilidi açmaz.

Hepsi tutarsa `setup/stage.json` `26c`'deki beş alanla yazılır: `pass_row_sha256` PASS satırının LF'siz baytlarının
sha256'sı, `toy_state_head` ve `copy_state_head` okunan başlar, `import_line_sha256` sayacın son aktarım satırınınki.
