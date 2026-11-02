# Değişiklik Günlüğü — Tohum

Tarih: 2026-10-29 · Sürüm: 2.2
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-02, E511, E517; sahibin kararı (2026-11-01): çit kaldırılmaz, kapısı öne çekilir, K6 Aşama 1 içinde
  canlı edilir; kandırma puanı düşürür): `03` `class_requires`: K6 düzeltmesinin önkoşulu hakemin son imzalı sonucunda
  `k6.status`'ün `live` olmasıdır (K6 sınavı güçlü, Güvenlik avcısı, bekçi testleri ve avcıdan farklı modelden test
  oracle'ı canlı) ve güvenlik yoluna dokunma aynı çıkışta; K5'in önceki PASS'i aranmaz, K6 hangi aşamada olursa olsun
  açılır, durumu hakem imzalar. `25a` 3: kopyanın `brain/integration`'ında ikinci zorunlu kontrol `snowball-fence`,
  hakemin kapı App'inin, dal korumasında (genesis'in okuduğu ruleset kuralları değişmez); `live` olmadıkça operatörün
  güvenlik yollarına dokunan baş kırmızıdır; `01a` ve `01b` buna bakar. Kurucu istemine açık kural: kandırma puanı
  düşürür, kaydı imzalı sonuçtadır. 80 satır sınırı için E411–E417 kaydı `CHANGELOG-4.md`'ye taşındı.
- 2.2 (2026-11-02, E507; Kurucu raporu): `26e`: bir modülün ilk adı Python'un standart kütüphanesinde bir modülün adı
  olamaz (`sys.stdlib_module_names`); hakem komutu `referee/` `sys.path`'te önde koşar ve o ad standart modülü gizler;
  böyle satırı olan tablo yüklenmez. Aşama 0'ın donmuş tablosundaki `profile` (MF4, MF6) kuraldan önce gelir, o tablo
  yeniden açılana kadar kalır. Yanıtlanan rapor: `spec-011-profile-shadows-stdlib` → `26e:33-37` (hakemin hiçbir
  komutu `cProfile`'ı çağırmaz; Aşama 0'ın yolu kalır). 80 satır sınırı için 2026-11-01 E421–E436 kaydı
  `CHANGELOG-4.md`'ye taşındı.
- 2.2 (2026-11-02, E506; sahibin kararı, boşluk D): `24a` "Kurucu": kapsülde defterin salt-okur dizini
  `/opt/founder/ledger_index.py` vardır (imajla gelir, beyne gelmez; tohumun ekleme aracı yine yoktur). 80 satır
  sınırı için 2026-11-01 E450 kaydı `CHANGELOG-4.md`'ye taşındı.
- 2.2 (2026-11-01, E490–E499; Kurucu raporu, E373'ün kalanları, act10 şüphecisinin bulgusu): `25a` 1: içe aktarma
  iki repodan yalnız `main`'i okur ve yalnız her itmenin göndereceğini git'in nesne denetiminden geçirir; 255 bayttan
  uzun tek ad ve boş repo adı durdurur. Yeni `29s` döngünün üç girdisini verir, hiçbiri
  operatör değişkeni değildir: beyin reposu `bootstrap.json` `brain_repo`'dur; bir koşu `targets[]`'ın her girdisine
  dizinin sırasıyla hizmet eder; Sigstore hakemin `bootstrap/requirements/sign.txt`'idir, onu koşturan işte kontrol
  adımının klonundan, lisans kapısından geçirilerek kurulur. Yeni `26e` Aşama 1'in parti tablolarıdır (P1 ve P2;
  modül yolları, parti adları; çıkış partisi Aşama 1 çıkışının yargısıyla gelir); P2 MF1'in testi `30d` "Profil
  testi", 53. `29b`: rakip freni açık aşamanınki, harcama kilitten sayılır; `18a`: `stage_budgets.asama_1.rival_usd`
  15 USD. `27`: `bootstrap.json`, özet ve `sign.txt`'in döngüdeki okuyucuları; `29p` `29s`'e bakar. Yanıtlanan rapor:
  `seed-041-loop-run-inputs-unnamed` → `29s:13-17` (beyin), `29s:19-24` (hedefler), `29s:26-47` (Sigstore);
  `seed-042-d4-canary-inputs-unnamed` → `29s:49-69` (CLI'nin pini kilittir, kurulum adımı, model `rival.model`);
  `seed-043-sentinel-end-row-unnamed` → `26f:12-22` (yeni `26f`: `events`/`sentinel`, geri alma, nöbetçinin bitişi);
  `seed-045-drill-live-inputs-unnamed` → `26f:24-36` (provanın satırları, iş ve sır; canlı fikstürler henüz yok, E499);
  declined: `seed-044-revert-facts-producers`: `29j:53-60` her olgunun ne olduğunu söyler (`build_ok` kodun kırmızı
  başta derlenip yüklenmesi, lint merge'ün ilk ebeveynindeki ve baştaki araç toplamı); üreticileri Kurucu'nun hakem
  kodudur (seed-023 ve seed-030 gibi).
  Dönem kesildikten sonra gelen rapor: `seed-046-pass-row-unnamed` → `26d:36-47` (PASS satırı, `part: events`, hakemin
  kendi satırı; ek alan serbest: `conditions`, `not_checked`), `26d:9` (yazarı döngü hakemi), `29s:19-24` (bir koşu her
  hedefe hizmet eder), `10a:44` (PASS koşulların makine denetimi: denetlenmeyen satır tutmuş sayılmaz), `26f:12-14` ve
  `10a:25` (`flaky` yeşil değildir), `10a:26` (her ekim), `26d:35` ve `10a:24` (`hunk_covered` merge yükünde, kapılamaz).
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
- 2.2 (2026-11-01, E390–E400, E404, E405, E411–E417, E421–E436, E450): Kurucu raporlarının yanıtları, npm
  workspaces kilidi, PASS satırı, `stage-open`, son kökün paketi ve `<state_root>`, fiziksel güvenlik ve kapsülün
  ajan/skill tanımları: `CHANGELOG-4.md`.
- 2.2 (2026-10-30 – 2026-10-31, E64, E65, E93, E249, E280–E301, E308, E317–E324, E333, E338, E339, E341, E342, E344):
  ders provasının aileleri ve sınav tarafı, sistem haritası, Aşama 0 çıkışının karar verilemeyen koşulları,
  `control`'ün döngü arayüzü, sınıf merdiveninin varsayılanlığı, yük altında performans, `main`'in salt okunur
  okunuşu, önyükleme hakeminin çıkıştan sonraki kuralı ve imzalı durumun arayüzü: `CHANGELOG-3.md`.
- 2.2 (2026-10-28 – 2026-10-30, E246–E247 ve öncesi): üçüncü inceleme, önyükleme hakeminin yazılışı ve sonraki kararlar: `CHANGELOG-2.md`.
- 2.1 ve öncesi (2026-10-28): `CHANGELOG-1.md`.
