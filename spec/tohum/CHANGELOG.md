# Değişiklik Günlüğü — Tohum

Tarih: 2026-10-29 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-01, E478–E485; sekizinci şüphecinin bulgusu): `25a` 1–2: içe aktarma beyni git'in nesne
  denetimiyle getirir; `.git`, `.gitattributes` ve `.gitmodules`'ü her derinlikte, harf duyarsız ve HFS+ biçimiyle,
  Windows'un tutamadığı adı (`|?*"<>`, 260 karakterden uzun yol) her sistemde, oyuncakta `.github`'ı reddeder;
  hiçbir şey itilmeden git'in katı nesne denetimi koşar; iki itme okunan `main`'e kirayla (`--force-with-lease`)
  olur ve ret uzak `main`'i adlandırır; yerel yol çağıranın dizinindendir. `26d`: `stage-open` sayacı, özeti ve
  hakem ağacını klonun commit'inden okur, çalışma ağacından değil; profil düzenli dosyada tek JSON nesnesidir.
- 2.2 (2026-11-01, E470–E475; dördüncü şüphecinin bulgusu; sahibin yetkisiyle mimari karar): `25a` 1–2 içe aktarmayı
  git nesneleriyle anlatır: hakem reposu çıplak klonlanır, yeni `main` pinli `referee/` ağacı ile `main`'den tam adıyla
  alınan korunanlardan kurulur, her ad nesne yazılmadan denetlenir (`26c`, sonda nokta ya da boşluk, aygıt adı, `~` ve
  rakam, korunanın harf varyantı, harf duyarsız tek ad), sayaç satırı aynı commit'tedir, oyuncak ve hakem zorlamadan
  itilir; çalışma ağacı yoktur. `26d`: `stage-open` klonun commit'indeki hakem ağacını ve genesis'in ağaç ve sonuç
  hash'lerini aktarım satırına bağlar, kopyanın tabanı vardır, profil okunabilir olmalıdır, kaydın verisinin hash'i
  kökün kendisidir; `26a` `rekor.anchor` bunu söyler.
- 2.2 (2026-11-01, E411–E417; üçüncü şüphecinin bulgusu): `26d`'ye olgular: son kökün Sigstore paketi döngünündür ve
  kök satırının yanında, aynı `brain/state` commit'inde `<state_root>/chain/<kök>.sigstore.json`'dadır (`stage-open`
  oradan okur; `27a`); `<state_root>` `01a`'nın `.brain/`'idir, başka bir `state_root` tohum dönemi ister (E417, sahibin
  yetkisiyle operatör kararı); zincirli satırın kuralları (son satır da LF ile biter,
  CR yok, anahtar iki kez yok); kök Rekor v1 `hashedrekord`'dur (`sigstore` 4.5.0 `sign --rekor-version 1`; bayraksız en
  yüksek sürüm, v2). Genesis satırı `events`, `kind: genesis`, hakemin kendi satırı; (B)'nin koştuğu genesis defterin
  son genesis'idir ve kural yalnız ondan sonrakileri sayar: yeniden aktarım kilidi kapatmaz (`25a` "Başarısızlık").
  Öneri, `proposed_by`'ı boş olmayan dizgi olan satırdır. `00b`: `26c` ve `26d` üç görevde okunur. 80 satır sınırı için
  2026-10-31'in dört kaydı daha `CHANGELOG-3.md`'ye taşındı (`main`'le birleşince orada).
- 2.2 (2026-11-01, E404, E405; ikinci şüphecinin bulgusu): PASS satırı ve `stage-open`'ın kuralı yeni `26d`'de: `events`
  satırı, `payload` `{stage: 0, verdict: "PASS", import_line_sha256, copy_genesis_row_hash, copy_merge_row_hashes[],
  owner_exception?}`, hakemin kendi satırı (`trust` `verified` ya da `observed`); merge satırı `kind: merge`; önerilmiş
  kopyası sayılmaz; oyuncağın merge'ünden sonra gelir, son aktarımı adlandırır. Alanlar `26` ve `26b`–`26d`'de (`25a` 9).
- 2.2 (2026-11-01, E450; sahibin onayı): Kurucu kapsülü her oturumun başında beynin `agents/` ve `skills/` dizinlerindeki
  ajan ve skill tanımlarını denetleyip `brain` eklentisi olarak yükler, beynin başka hiçbir dosyasını yapılandırma olarak
  yüklemez; iki dizin beyin ağacında, biçim, düşürme kuralları ve yükleme kaydı `24a` "Ajan ve skill tanımları"nda. 80
  satır sınırı için 2026-10-31 E344 kaydı `CHANGELOG-3.md`'ye taşındı.
- 2.2 (2026-11-01, E421–E436; sahibin yetkisiyle operatör kararı (2026-11-01); sahip geri alabilir; Kurucu raporları;
  E150, E231, E260 kapandı): **Fiziksel güvenlik** (`05`, tek yer): fiziksel bir süreci süren, durduran, alarm veren ya
  da koruyan kod güvenlik yoludur; risk ağırlıklıdır, K6 kapısı olmadan biçimleyici dahil dokunulmaz; yolları sistem
  hedeften türetir, sahibin isteğe bağlı `targets[].safety_paths`'ı yalnız genişletir (`26c`, `25` 10a, `14`); K6 canlı
  olana kadar birim seçimi güvenlik yollarını dışlar, Aşama 1'in ilk birimi de; `03` ve `30` oraya bakar. **Görünmeyen
  tüketici** (`05`): tüketicilerini kapının sayamadığı değişiklik `blocked`'dır. **K0** ekosistemin kimlik ve konum veren
  ilk mekanik denetimidir, kural kimliği veren linter yoksa da (`03`). **Test gücü** (`04` 1): modülsüz kırmızı kalır;
  Aşama 1'in çıkışından Kurucu'nun kendi kodunun değişen satırlarında mutant öldürme tabanı; ölçü, içe aktarma ya da
  sözdizimi hatası olmayan kırmızıyla öldürülenlerin payı, değeri çıkıştan önce sahibin. **Kum havuzu** (`08` 2): hedefin
  test paketini koşan her kum havuzunda süreç ve CPU sınırı. **Sınav hatası** (`29e`, `29b` "Ret hafızası", `26c`
  `control.json`; E53): operatörün `exam_faults`'ta doğruladığı ret imzası, onu yargılayan sınav yürürlükteyken serilere
  sayılmaz, seri girdisi geri alınır, ret kalır. Yanıtlanan raporlar: `seed-001-seed-dir-missing` → `00a:24-27`,
  `24a:49`, `24a:55`, `26:18`, `27:61`, `25:28` (Kurucu satırı kendi koduyla `26`'nın zincir kuralına göre ekler, `cost`
  satırını başlatıcı yazar, beyne yalnız `spec/tohum` gelir); `referee-016-reproducer-polarity` → `29:30-52` (3a'dan beri
  yürürlükte; E260'ın bekleme etiketi `CHANGELOG-2.md:27`'den kalktı); `seed-027-root-choices` → `13:49-53`
  (g): beş bağ Aşama 1'den başlar, Aşama 0'ın satırı `29j`'ninkidir; `seed-030-cause-choices` → `29j:59-60` (girdiler
  Kurucu'nun hakem kodunda üretilir, vaat sözcüğü kalktı); `seed-023-run-record-producer` → declined: koşu kaydının ve
  `cause` girdilerinin üreticisi Kurucu'nun hakem kodudur (`29b:9`, `29j:59-60`; spec araç çıktısının biçimini vermez,
  `29h:27-28`); `spec-036-cycle-composition-unowned` → declined: devrin bileşimi MF17'nin, Kurucu'nun kodudur
  (`asama-0/14:44`, `:48`; `00a:13-14`); seed-029 (e) ve seed-030 (f) aynı yanıtı alır. 80 satır sınırı için
  2026-10-31'in dört kaydı (E341; E294, E308; E338, E339; E249) `CHANGELOG-3.md`'ye taşındı.
- 2.2 (2026-10-31 – 2026-11-01, E93, E333, E342, E390–E400): önyükleme hakeminin çıkıştan sonraki kuralı, imzalı
  durumun arayüzü, Kurucu raporlarının yanıtları ve npm workspaces kilidi: `CHANGELOG-4.md`.
- 2.2 (2026-10-30 – 2026-10-31, E64, E65, E249, E280–E301, E308, E317–E324, E338, E339, E341, E344): ders provasının
  aileleri ve sınav tarafı, sistem haritası, Aşama 0 çıkışının karar verilemeyen koşulları, `control`'ün döngü arayüzü,
  sınıf merdiveninin varsayılanlığı, yük altında performans ve `main`'in salt okunur okunuşu: `CHANGELOG-3.md`.
- 2.2 (2026-10-28 – 2026-10-30, E246–E247 ve öncesi): üçüncü inceleme, önyükleme hakeminin yazılışı ve sonraki kararlar: `CHANGELOG-2.md`.
- 2.1 ve öncesi (2026-10-28): `CHANGELOG-1.md`.
