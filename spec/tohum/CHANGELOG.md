# Değişiklik Günlüğü — Tohum

Tarih: 2026-10-29 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-01, E411–E417; üçüncü şüphecinin bulgusu): `26d`'ye olgular: son kökün Sigstore paketi döngünündür ve
  kök satırının yanında, aynı `brain/state` commit'inde `chain/<kök>.sigstore.json`'dadır (`stage-open` oradan okur;
  `27a`); `<state_root>` `stage-open` için o commit'in tepesidir; zincirli satırın kuralları (son satır da LF ile biter,
  CR yok, anahtar iki kez yok); kök Rekor v1 `hashedrekord`'dur (`sigstore` 4.5.0 `sign --rekor-version 1`; bayraksız en
  yüksek sürüm, v2). Genesis satırı `events`, `kind: genesis`, hakemin kendi satırı; (B)'nin koştuğu genesis defterin
  son genesis'idir ve kural yalnız ondan sonrakileri sayar: yeniden aktarım kilidi kapatmaz (`25a` "Başarısızlık").
  Öneri, `proposed_by`'ı boş olmayan dizgi olan satırdır. `00b`: `26c` ve `26d` üç görevde okunur. 80 satır sınırı için
  2026-10-30 kayıtları `CHANGELOG-3.md`'ye taşındı.
- 2.2 (2026-11-01, E404, E405; ikinci şüphecinin bulgusu): PASS satırı ve `stage-open`'ın kuralı yeni `26d`'de: `events`
  satırı, `payload` `{stage: 0, verdict: "PASS", import_line_sha256, copy_genesis_row_hash, copy_merge_row_hashes[],
  owner_exception?}`, hakemin kendi satırı (`trust` `verified` ya da `observed`); merge satırı `kind: merge`; önerilmiş
  kopyası sayılmaz; oyuncağın merge'ünden sonra gelir, son aktarımı adlandırır. Alanlar `26` ve `26b`–`26d`'de (`25a` 9).
- 2.2 (2026-11-01, E400; Kurucu raporu spec-015 -> `29g`, `29d`, `24`, `30c`): npm workspaces kilidi. Kök, çalışma alanı bağı (`link` doğru, `resolved` depo içi göreli yol) ve böyle bir bağın adlandırdığı çalışma alanı dizini getirilmez ve denetlenmez; iç içe `<çalışma alanı>/node_modules/<paket>` dahil başka her girdi pakettir, getirilir ve denetlenir (`29g`; vakalar `workspaces_lock`, `workspace_folder_needs_its_link`, `nested_registry_not_allowed`). Hangi girdinin getirilip denetlendiği yalnız `29g`'dedir; `29d`, `24` ve `30c` oraya bakar.
- 2.2 (2026-10-31, E333; uzman tartışması ve hakem, ikinci tur 2026-11-01): önyükleme hakemi `asama-0/10a`'nın kuralını
  uygular: kabul edilmiş çıkıştan ((A)) sonra spec, kod ya da çıkış push'unda Kurucu kayıtları dışında yalnız `candidates/`
  ve `targets/` değişebilir: `referee/` `referee_changed_after_exit`, başka yol `changed_after_exit:<yol>` (`29b` "Çıkıştan
  sonra"). Dondurma Aşama 0'ındır: kilit sonraki aşamayı açınca ya da (B) kırmızıyken operatör aktarımı geri alıp başı
  `control.json` `reverted_exits`'e yazınca biter (`26c`, `25a` "Başarısızlık"). İmzalı durum çıkışın başını taşır
  (`snowball-bootstrap-state/4`; `/3` aynen taşınır, taşıdığı sonuç aktarılabilir bir çıkışsa onun başıyla).
- 2.2 (2026-10-31, E344; uzman tartışması ve hakem): başlatıcı oturumun CLI'nin bildirdiği maliyetini `kind: cost`
  satırı olarak `26`'nın zincir kuralıyla yazar (`24a` 4); andığı "tohumun defter aracı" tohumda yoktur (E150).
- 2.2 (2026-10-31, E342, E93; Kurucu raporu seed-040, uzman tartışması ve hakem): önyükleme hakeminin imzalı durumunun
  arayüzü `29b` "Durum"dadır: artefakt, hakem reposunun `main`'indeki koşuların süresi dolmamış en yeni `bootstrap-state`'i
  (iki dosya); açılışı `sigstore verify identity` (`bootstrap.yml`'in `main` kimliği, GitHub OIDC yayıncısı), doğrulanamazsa
  ya da yoksa çıkış 2; son kabul `state.last_accepted_sha`. `26c` `referee_tree_sha256`'nın kuralını, kodun her retini
  (arşivin her yerindeki bağ, özel dosya ve güvensiz ad dahil) ve bilinen cevaplı örneğini (`/vec/treehash/three-files.tar`;
  vektör vakası değil) verir; D1'in nasıl kurulacağı Kurucu'nundur. Raporların okuyucusu (E93): `pull` beynin
  `reports/*.json`'unu okur; imzalı sonuç `reports[]` `{id, kind, ref, state, sha256}` ve açık rapor varsa `reports_open:<n>`
  uyarısını taşır; rakibin isteği `reports/`'u yine dışarıda tutar (`26c`); `disputed` kuralı E53'te kalır. Her dönemin
  günlük satırı yanıtladığı ya da reddettiği rapor kimliklerini adlandırır; bu dönem: `seed-040-d1-bootstrap-state-read` →
  `29b:30-34`, `26c:39-45`.
- 2.2 (2026-10-31, E341; sahibin kararı): "Performanslı" hedefi beklenen yük altında da geçerlidir; gecikme, hata ve kaynak
  hedefleri yük altında ölçülür, yalnız yalıtılmış kopyada ve sentetik veriyle (`01`); K7 bu hedefe bağlıdır (`03`).
- 2.2 (2026-10-31, E294, E308; sahibin kararı): ekim üretilemediyse taşınan #durustluk'un taahhüdü, aşama başlamadan
  kaydedilmiş değişmez ve mühürlü bir ölçüm planının hash'idir (`02` "Sahip istisnası", `25` 10c); plan çıkışta
  `setup/honesty-key.json` olarak açılır, değerlendiricinin çıktısı `setup/honesty-result.json`'dır (`26c`); gizli artefakt yoktur.
- 2.2 (2026-10-31, E338, E339; sahibin onayı, uzman tartışması ve hakem): sınıf merdiveni varsayılandır. Aşama 1'den
  sonra hangi sınıf grubunun açılacağını Kurucu'nun aşama spec'i, önkoşulları kapanmış sınıflar arasından seçer; aşama
  tablosu ve Savunma'nın zorunlu alternatifi varsayılan satırdır ve yan yana koşmaz (`10`); sapma tek sınıf getirir,
  hakemin aşama açılmadan yazdığı değer / USD alt sınırına dayanır ve çıkışta seçilen sınıfın gerçek harcamasıyla o
  sınıra karşı denetlenir; ıska, `UNMEASURABLE` tahmin ya da `UNMEASURABLE` çıkış varsayılanı geri getirir (`03`, `18`
  Varsayılandan sapma). Sınıf önkoşulları `class_requires`: prosedür yalnız ekler, operatör siler; "aynı çıkışta" en
  geç sınıfın kendi çıkışıdır (`03`, `18`, `18a`, `26b`); `stage_order` sayaçtır, kök 0 → 1, 6 son. Oracle'ı hazır
  olmayan sınıf yalnız rapor eder; geçen aşama ya da açık sınıf sayısı puana girmez. Çapa aşama numarasını değil
  `02`'nin listesindeki olayı bekler (`02`, `15`): `04a`, `07a`, `10a`, `11`, `12a`, `21a`, `22`, `30e`, `31a`, `31b`,
  `31d`, `31h`; sınıf sırasına bağlı metin koşulları da (`01a`, `06`, `08`, `17`, `19`, `24`, `25a`, `26a`, `27`,
  `27a`, `29`, `30`, `30a`, `30f`). `18`'in "merdiven sırası" maliyet merdiveninin basamak sırasıdır. Satırdaki `18`
  atıflı yetenek seçimle o aşamadan düşmez: ders provası Aşama 2'nin ilk işi kalır (E317). `asama-4` K5'in hedef
  taslağıdır, ön koşulu `03`'ün tablosudur. Kapının kodu Aşama 2 spec isteğiyle gelir (E339).
- 2.2 (2026-10-31, E249; sahibin sorusu, uzman tartışması): `main`'i salt okunur okumak dokunmak değildir; taban yaşının
  commit sayısı ve eskimiş bulgu oranı senkrondan önce de bu okumayla ölçülür (`07`). `07`'nin andığı eskimiş bulgu oranı
  sinyali `17`'de satırdır: eşik pencerede > %20, doğan şey organ değil Aşama 2'deki senkron izin kararıdır.
- 2.2 (2026-10-31, E317, E321–E324; ders provası tartışmasının hakem kararı): gerçek beyinde ders provası ders
  görünümünü getiren aşamanın (Aşama 2) ilk işidir ve sahibin MVP sınavıdır; erken ders partisi yok (`03`, `22b`,
  E317). `#ders-dogru` zorunlu çıkış satırı (`18`, E322). Aşama özeti `03` satırında `18` atfıyla geçen her yeteneği
  listeler, Kurucu'nun taslağı tohumun hedefini düşüremez (`02`). Havuz o aşamanın spec isteğinden önce taahhüt
  edilir, açık sayfada ya da vektörde geçen aile havuza girmez, kalibrasyon ders okuyabilecek her koltuğun modeliyle
  (`22b`, E324). Etki çiftinin iki koşusu bütçe ve ders bloğu dışındaki prompt hash'iyle de eşit, kaydı eksik çift
  FAIL (E321); `i`'nci deneme p < 0,10 · 2^-i ile (E323); yeni `22c`; `18a`, `22a`, `29c`, `29q`.
- 2.2 (2026-10-30, E64, E65, E280–E319): ders provası, sistem haritası ve Aşama 0 çıkışının kuralları: `CHANGELOG-3.md`.
- 2.2 (2026-10-28 – 2026-10-30, E246–E247 ve öncesi): üçüncü inceleme, önyükleme hakeminin yazılışı ve sonraki kararlar: `CHANGELOG-2.md`.
- 2.1 ve öncesi (2026-10-28): `CHANGELOG-1.md`.
