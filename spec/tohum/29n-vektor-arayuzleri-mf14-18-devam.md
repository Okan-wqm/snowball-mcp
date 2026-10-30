# Vektör Arayüzleri, Devam: `status`, `genesis`

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın MF16 ve MF18'ini yazarken; bu grupların komutu, girdisi ya da çıktısı değişirken
Çapa: `seed/bootstrap/vectors/vectors.json` (`status`, `genesis`) ve `vectors/<grup>/` fikstürleri

---

`29m`'nin devamıdır, kuralları onunkidir; beklenen değerler burada yok (`29a`). MF17'nin (`loop.yml`) grubu yoktur:
tohumun `wiring` denetimidir (`29d`).

## `status` (MF16, `status/block.py`)

`python -m status.block render <defter.jsonl> <imports.jsonl> <status.md>`; stdin `{"canary_cap_usd_micros": tamsayı}`
(aşama tavanı, çağıran mikroya çevirir). Defter hedefinkidir (`26`), bu devrin `status` satırından önce; imports
`setup/imports.jsonl` (`26c:37-38`); `status.md` `brain/state`'teki dosya, boş olabilir. Alanlar (test 42,
`asama-0/09:66`), `events` satırı `part: events` olandır: `cycle_id` son `cycle_start` satırının `payload.cycle_id`'si
(`01b:54` her devir başlangıç satırı yazar; tür adı seçim); `last_decision` son `decision` satırının
`payload.decision`'ı; `base_age_s` = ts(son `cycle_start`) − ts(ilk `genesis` satırı), saniye, ts
`YYYY-MM-DDTHH:MM:SSZ` (UTC); `07:12-13`'ün commit sayısını Aşama 0'da üreten yok (D1 `main`'i okumaz,
`asama-0/01:37`): vektörde yok. `brake` `{spent_usd_micros: her `part: cost` satırının `payload.usd_micros` toplamı,
cap_usd_micros, engaged: spent ≥ cap}`, `prompt`'un freni. `human_touches` `imports.jsonl` satır sayısı (`26c:38`,
`27:56`); `27:19`'un öbür dokunuşlarını (tohum dönemi, `stage-open`, dürüstlük anahtarı, sert duruş kalkışı) spec'in
adlandırdığı hiçbir dosya kaydetmez: sayılmaz. **Blok**, tam olarak `<!-- status.block -->` olan satırın LF'sinden
sonraki bayttan tam olarak `<!-- /status.block -->` olan sonraki satırın ilk baytına kadardır: işaret baytı yok, son
satırı LF'siyle; geri kalanı `docs.render`'ın (`15:42-43`). Açılış satırı yoksa `found_sha256` `null`; iki açılış ya da
kapanışsız açılış kullanılamaz. **Düzenleme** (`asama-0/14:43` yeniden üret ve `events`'e yaz der, tespiti söylemez;
seçim): her devir yazdığı bloğun `events {kind: status, payload: {block_sha256}}` satırını ekler; `recorded_sha256` son
`status` satırınınki ya da `null`; `edited` ⇔ `found_sha256 ≠ recorded_sha256` (ikisi `null`, ilk devir, düzenleme
değil; silinen blok düzenleme). `render` yazmaz: yeniden üretilen bloğu çağıran yazar, `ledger.append`'le
`status_edited` (varsa) ve yeni `status` satırını ekler. Bu türler `26`'ya girmelidir (`26:9-10`). Sert duruş yok:
`asama-0` yeniden üretir; `15:16` ve `01b:37` düzenlemeyi zincir kırığı ve ret sayar, karar sahibin. Defter ve imports
zincirini `render` doğrulamaz (`ledger.append`, `29i`). Çıktı: `cycle_id`, `last_decision`, `base_age_s` (eksikse
`null`), `brake`, `human_touches`, `edited`, `event` (`{kind: "status_edited", payload: {found_sha256,
recorded_sha256}}` ya da `null`); `block` ve `block_sha256` karşılaştırılmaz (görünüm Kurucu'nun, test 42). Çıkış: 0
düzenlenmemiş; 1 düzenlenmiş; 2 okunamayan dosya, JSON nesnesi olmayan satır, kullanılan satırda biçimsiz `ts`,
tamsayı `usd_micros`'u olmayan `cost` satırı, tamsayı olmayan tavan, işaret hatası (satır `{"edited": null}`).
Vakalar: `fields_from_ledger` alanlar yalnız defterden ve imports'tan; sonraki başka türden `events` satırı son kararı
değiştirmez, her devrin `cost`'u sayılır; blok kayıttakine eşit; `hand_edit_regenerated` blok içinde elle düzenleme
iki hash'le `status_edited` yazar; `edit_outside_block` iki işaret satırı arası bloktur, dışındaki düzenleme değil;
`deleted_block_is_edit` defter blok kaydederken silinmiş blok düzenlemedir; `brake_engaged` harcama tavana ulaşınca.

## `genesis` (MF18, `activate.py`)

`python -m activate genesis <api.json> <summary.json> <imports.jsonl> <policy.json> <güvenlik.jsonl> <tarif.json>`;
stdin `{"target": "<targets[].id>"}`. Kuru koşu: `api.json` kaydedilmiş GitHub REST'tir, `29i`'deki gibi (kaydı olan
çağrı gövdesini, başkası 404 alır); hiçbir şey yazılmaz, kesim MF9'undur (`refs`). Girdiler `setup/summary.json`
(`26c:31-35`), `26c:37-38` satırları, hakem politikası, `seed/security-ledger.jsonl` (`30e`), doğrulanmış tarif
(`26c:53-58`). Okunanlar, iki türde: `GET /app` (yazar App'i), `GET /installation/repositories`, `GET
/repos/{repo}/rules/branches/brain/state` ve `.../brain/integration`; `toy`'da `GET /repos/{repo}/git/ref/heads/main`
(oyuncak `main`'den kesilir, `25a:21`), `copy`'de `GET /repos/{repo}/actions/permissions` (`main`'i okunmaz).
`rules/branches` `01b:59`'un, öbür uçlar seçim. Nedenler (adlar seçim; her biri sert duruş, `28:37`): `app_scope`
(kurulum repolarının `full_name` kümesi `targets[].repo` kümesi değil); `state_rules_missing` (`deletion`,
`non_fast_forward` yok); `integration_rules_missing` (`deletion`, `non_fast_forward`, `pull_request`,
`required_status_checks`'ten biri yok, `25a:17`); `integration_check_not_writer` (bir `required_status_checks`
kuralında `strict_required_status_checks_policy` doğru değil, kontrol yok ya da `integration_id` `/app`'in `id`'si
değil; kural yoksa yalnız öncekisi); `copy_actions_enabled` (`enabled` `false` değil, `25a:20`);
`security_ledger_broken` (tohum güvenlik defteri boş ya da geçerli zincir değil). Yük, neden yoksa, on iki anahtar
(`10a:17`'nin bağladıkları; `26`'da genesis yükü yok, adlar seçim ve `26`'ya girmeli): `target`; `base_sha` (`toy`:
API'deki `main`'in `object.sha`'sı, özettekini okumaz, oyuncak kurulumda boştur, `25:26`, `25a:16`; `copy`:
`targets[].base_sha`); son imports satırından `referee_tree_sha256`, `result_sha256`; `import_line_sha256` (o satırın
LF'siz baytları, `26c:39`); `seed_epoch` (son `seed_epochs[]`); dosya baytlarının sha256'sı `policy_sha256`,
`summary_sha256`, `seed_security_ledger_sha256` (LF checkout'ta git blob'u, `25:64`); `seed_security_last_row_hash`
(`30e:67-69`); `recipe_sha256` (RFC 8785; evi `profile.json` `units[]`); `facts_sha256` (türün okuduğu GET'lerin
`{istek satırı: gövde}`'sinin RFC 8785'i). (A)'nın Rekor kimlikleri yok (onları taşıyan dosya spec'te yok); bypass
aktörleri, oyuncakta iş akışı yokluğu, mandal tabanı ve hazır adaylar bu grupta değil. Çıktı `ok`, `hard_stop`,
sıralı `reasons`, `payload` (sert duruşta `null`). Çıkış: 0 planlandı; 1 sert duruş; 2 hedef `targets[]`'ta yok,
okunamayan ya da biçimsiz dosya, imports satırı yok, gereken GET kayıtlı değil (satır `{"ok": false, "hard_stop":
true, "payload": null}`).
Vakalar: `toy_genesis_row` her ön koşul tutar; oyuncağın tabanı API'deki `main`, özettekinden farklı; satır her baytı
ve hash'i bağlar; `copy_genesis_row` kopyanın tabanı özettekidir, Actions izni olgu hash'ine girer;
`recipe_canonical` aynı tarif başka anahtar sırası ve girintiyle aynı yükü verir; `copy_actions_enabled` Actions açık
kopya sert duruş; `every_fault_named` dört olgu birden düşer, her biri adlanır, oyuncağın kayan `main`'i hata değil;
`security_ledger_broken` hash'ten sonra bir baytı düzenlenmiş tohum güvenlik defteri etkinleştirmeyi durdurur.
