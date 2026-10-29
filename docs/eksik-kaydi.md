# Eksik Kaydı: Büyütmeden Önce

Tarih: 2026-10-29 · Sahibi: operatör · Kapsam: Kurucu'yu çalıştırmak ve MCP sunucusunu yazmak dışındaki her şey

Bu kayıt, Kurucu başlamadan ve sistem büyümeden önce kapatılması gereken eksiklerin tek listesidir.
Her satır bir kanıta dayanır; her düzeltme önce kırmızı bir testle, sonra kodla, sonra bir mutantla
kapanır ve satırın durumu commit ile güncellenir. Satır silinmez; kapanınca durumu değişir.

**Nasıl bulundu (2026-10-29).** Altı uzman denetçi, birbirinden bağımsız ve salt okunur çalıştı:
karar ve durum makinesi (D), rakip ve yeniden üretme (R), iş akışı ve operasyon (W), spec ile kod
tutarlılığı (S), test ve doğrulama araçları (T), güvenlik (X). Her bulgu dosya:satır alıntısı ya da
gerçekten koşulmuş bir komutla geldi; aynı kusuru birden çok denetçi bulduysa kaynak sütununda
hepsi yazılıdır. Bulguları birleştiren ve doğrulayan: Claude Code (Opus 5.5).

**Önem.** `K` = Kurucu'dan önce kapanmalı. `B` = büyütmeden (Aşama 1'den ya da ilk gerçek hedeften)
önce. `S` = sonra; bilinen sınır olarak kayıtlı.
**Durum.** `açık` · `karar bekliyor` · `kapandı <commit>` · `sınır` (bilerek kabul edildi, gerekçesi yazılı).

## Özet

| No | Eksik | Önem | Karar | Kaynak | Durum |
|---|---|---|---|---|---|
| E01 | Beyin komutunun 125 çıkışı "Docker arızası" sayılıyor | K | — | R4 X4 D1 | açık |
| E02 | Beynin içeriği `pull`'u çökertiyor; hakem saatlik takılıyor | K | — | X3 X7 D2 | açık |
| E03 | Dosya adındaki satır sonu rakibin isteğine sahte bölüm ekliyor | K | — | R5 | açık |
| E04 | İçe aktarma, beynin `.git/hooks`'unu operatörün checkout'una yazıyor | K | — | X1 | açık |
| E05 | Beşinciden sonraki yeniden üreticiler sessizce koşmuyor | K | — | R7 D3 | açık |
| E06 | Yeniden üretici sözleşmesi belirsiz; stderr ve çıktı atılıyor | K | — | R2 D4 | açık |
| E07 | Yeniden üretilemeyen iddia iz bırakmıyor | K | evet | D4 R2 | onaylandı · açık |
| E08 | Kanıtlanmış kusur unutuluyor; tekrar sayacı iddia metnine bağlı | K | evet | R1 D9 | onaylandı · açık |
| E09 | Totolojik yeniden üretici (`true`) "yeniden üretildi" sayılıyor | K | evet | R3 | onaylandı · açık |
| E10 | Rakip Kurucu'nun defterini görüyor (spec yasaklıyor) | K | evet | R6 S3 | onaylandı · açık |
| E11 | Rakibin kendi hataları Kurucu'nun "öğrenmiyor" sayacına yazılıyor | K | evet | R11 S11 D8 | onaylandı · açık |
| E12 | Kalıcı 4xx ve izolasyon hataları sonsuza dek kesinti diye yeniden deneniyor | K | evet | D6 | onaylandı · açık |
| E13 | Rakip harcaması bazı yollarda hiç yazılmıyor | K | — | R9 D5 W4 | açık |
| E14 | İmzalı durum kaybolursa hakem sessizce tohumdan yeniden başlıyor | K | evet | W1 D7 | onaylandı · açık |
| E15 | Eski imzalı durum geri yüklenebiliyor (zincir yok) | K | — | W2 | açık |
| E16 | `yaz`'daki "canlı" kill switch canlı değil; iptal `yaz`'ı durdurmuyor | K | evet | W3 | onaylandı · açık |
| E17 | İş akışında şablon enjeksiyonu; imza kimliği `main`'e sabit değil | K | — | W7 | açık |
| E18 | Testlerin toplam süresi sınırsız; yavaş test "ret" değil "kesinti" | K | — | W8 X5 D12 | açık |
| E19 | Kurucu kaynaklı hatalar altyapı arızası sınıflanıyor | K | — | D12 | açık |
| E20 | Çıkıştaki "bağımsız rakip denemesi" sayımı yanlış; yeniden deneme rakibi tekrar çağırıyor | K | evet | D10 D11 | onaylandı · açık |
| E21 | Donmuş spec yeniden dondurulabiliyor; her aşama dizini donuyor | K | evet | S1 D14 | onaylandı · açık |
| E22 | Tohumdaki Aşama 0 spec'i değiştirilmeden dondurulamıyor | K | — | S2 | açık |
| E23 | Çıkış kontrolü hakemin yapmadığı denetimleri sayıyor | K | evet | S4 | onaylandı · açık |
| E24 | Kurulum özeti, vektör, koltuk ve politika hash'leri denetlenmiyor | K | — | S5 | açık |
| E25 | Aşama 0'ın `llm.call` ve `agent.dispatch` sayfaları API anahtarı ve geçit varsayıyor | K | evet | S6 | onaylandı · açık |
| E26 | Bu repoda CI yok | K | evet | W5 | onaylandı; repo açıldı (2026-10-29) · CI açık |
| E27 | İzolasyon hatası ancak tam koşudan sonra fark ediliyor | B | — | R8 | açık |
| E28 | Kapsayıcı çıktısı belleğe sınırsız alınıyor | B | — | X2 | açık |
| E29 | Operatörü uyaran hiçbir şey yok | B | evet | W6 | onaylandı · açık |
| E30 | Kablolama testleri izinleri, adım çıktılarını ve tetikleri denetlemiyor | K | — | W10 | açık |
| E31 | Action'lar eskimiş Node 20 sürümlerinde; her action'a izin var | B | — | W9 | açık |
| E32 | Zamanlayıcı hiç tetiklenmedi; açık repo güvenlik ayarları kapalı | K | evet | W12 | onaylandı; sır taraması ve itme koruması açıldı, beyin reposunda Actions kapatıldı (2026-10-29) · zamanlayıcı açık |
| E33 | CLI sürüm kayması ve koşu kökeni kaydedilmiyor | B | — | R12 W11 | açık |
| E34 | Bütçe bitince commit tüketiliyor; ay dönünce kendiliğinden açılmıyor | B | evet | S9 D13 | onaylandı · açık |
| E35 | Açık hakem reposu ile özel hedef birlikte olamaz; spec yazmıyor | B | evet | S7 | onaylandı · açık |
| E36 | 09a aktarım yolunu açık repoda kapanmış sayıyor | K | — | S8 | açık |
| E37 | Spec temizliği: tempo, aktarım betiği, çapraz referans, sağlayıcı, ret kuralları, okuyucu tablosu, iş sayısı, başlıklar | B | — | S10 S12–S20 R14 | açık |
| E38 | Windows'ta model seçimli regex'in süre sınırı yok | S | evet | R13 | onaylandı · açık |
| E39 | Rakibe prompt injection kalıntı riski | S | evet | X6 | onaylandı · açık |
| E40 | Çalışma zamanı ve Sigstore pinlerinin yenileme yolu yok | B | — | W13 | açık |

| E41 | Bozuk çıkış isteği `decide`'ı çökertiyor; hakem saatlik takılıyor | K | — | T1 | açık |
| E42 | Bağımlılık yolu (`fetch-deps`, kapsayıcıda kurulum, lisans kapısı) hiçbir testte yok; e2e de kaybetti | K | — | T2 | açık |
| E43 | En yeni imzalı durumu seçen kod test edilmiyor | B | — | T3 | açık |
| E44 | Operatör ve durum zinciri yolları yalnız Linux'ta test ediliyor | B | — | T4 | açık |
| E45 | Mutasyon seti kapsayıcı, git, lisans, içe aktarma modüllerini hiç bozmuyor; `/vec` ve `/deps` salt okunurluğu denetlenmiyor | B | — | T5 | açık |
| E46 | Ağaç hash formülü ve `seed-hash` sabitlenmemiş; kayma Kurucu'ya yazılıyor | B | öneri | T6 | açık |
| E47 | `.gitattributes` yok; özet hash'leri hesaplanmıyor (E24 ile birlikte) | B | öneri | T7 | açık |
| E48 | Prova yargıcının beş dalını ne testler ne tohum vektörleri bağlıyor | B | öneri | T8 | açık |
| E49 | Başarısız olamayan ya da yanlış nedenle geçen testler | S | — | T9 | açık |
| E50 | Ölü kod ve ölü çıktılar | S | — | T10 | açık |
| E51 | Testler üretimden farklı bir biçimi modelliyor | S | — | T11 | açık |

**Kararlar (2026-10-29).** Operatör, "karar" sütunu `evet` olan 19 kalemin hepsinde aşağıdaki
önerileri onayladı ve `snowball-mcp`'nin de açık olmasını istedi. E46–E48 test denetçisinden sonra
geldi; önerilen yol uygulanır ve operatöre ayrıca bildirilir.

## Ayrıntı

### E01 · Beyin komutunun 125 çıkışı "Docker arızası" sayılıyor · K
- **Kanıt.** `container.py:28` komutu `exec sh -c "$SNOWBALL_CMD"` ile koşar; komutun çıkış kodu
  kapsayıcınınki olur. `reproduce.py:31` 125'i `runner_fault`, `decide.py:101` ve `:136` kesinti
  sayar. D1'in denemesi: yeniden üretilmiş kusur → `infra yeniden:docker`, aynı SHA'da yeni rakip
  kusuru kaçırınca `accepted`; 125 ile çıkan testler ret hafızasına hiç girmiyor.
- **Neden.** Kurucu (bilerek ya da değil) "iç hata → exit 125" yazarsa her kanıtlanmış kusur kesintiye
  döner ve rakip, kaçırana kadar yeniden çağrılır. 125'i kesinti sayma kuralını önceki turda bu oturum
  eklemişti; açık bu turda kapanmalı.
- **Plan.** PRELUDE komutu `exec` etmez; komutun 125'ini 1'e çevirir, böylece 125 yalnız Docker'dan
  gelebilir. Test: `SNOWBALL_CMD="exit 125"` → çıkış 125 değil; decide birim testi; Linux'ta gerçek
  `DockerRunner` ile `exit 125`. Mutant: eşleme kaldırılır.

### E02 · Beynin içeriği `pull`'u çökertiyor · K
- **Kanıt.** D2 ve X3 denemeleri: manifestte dev tamsayı, yalnız vekil karakter, derin iç içe JSON,
  çıkış isteğinde ondalık `stage` → `CanonicalError`/`RecursionError`; `cli.py:547` yalnız dört
  hata türünü yakalar. X7: adında `:` geçen bir dosya `TreeError` ile işi durdurur. `cek` başarısız
  olunca `yaz` koşmaz, imzalı durum yazılmaz, park mekanizması hiç devreye girmez: hakem her saat aynı
  SHA'da çöker.
- **Plan.** Manifest ve çıkış isteği tip ve aralıkla denetlenir; ayrıştırma hataları adlandırılmış
  ret nedenidir (`manifest_invalid`, `exit_request_malformed`, `unsafe_path`); `head` bilindikten sonra
  `pull`'daki her beklenmedik hata `pull_error:<tür>` reddine döner. Test: altı girdinin her biri
  `pull` 0 döner ve nedeni yazar.

### E03 · Dosya adındaki satır sonu rakibin isteğine sahte bölüm ekliyor · K
- **Kanıt.** `treehash.py:37` `_clean` satır sonunu reddetmez; `rival.py:608` değişen yolları ham
  birleştirir. R5'in denemesi: sahte bir `=== Seed page spec/tohum/29b… ===` bölümü gerçek sayfadan
  önce isteğe girdi.
- **Plan.** `pull`'da denetim karakterli yol reddedilir (`control_char_in_path`); istek içinde yollar
  JSON ile gösterilir, diff ve sayfalar koşu başına rastgele bir sınırla çitlenir. Test: satır sonlu
  yol → `pull` reddi; `build_context` sahte başlık üretmez.

### E04 · İçe aktarma, beynin `.git/hooks`'unu operatörün checkout'una yazıyor · K
- **Kanıt.** `importer.py:20` `.git`'i korur ama `extract` `referee/.git/...` üyesini yazar;
  `tree_hash` `.git` bileşenini reddetmez. X1 kurgusu: `referee/.git/hooks/pre-commit` → operatör
  `git commit` dediğinde kendi makinesinde kod çalışır.
- **Plan.** `tree_hash` ve `extract` herhangi bir yol bileşeni `.git` olan (büyük-küçük harf
  duyarsız) üyeyi reddeder; içe aktarma önce geçici dizine açar. Test: böyle bir ağaç `TreeError`,
  `run_import` reddeder.

### E05 · Beşinciden sonraki yeniden üreticiler sessizce koşmuyor · K
- **Kanıt.** `rival.py:40` 10 deneme, `reproduce.py:19` ilk 5'i koşar; D3'ün denemesi: gerçek kusur
  6. denemedeydi → `accepted`. `decide` her yeniden üreticinin sonucu olup olmadığına bakmıyor.
- **Plan.** `validate_verdict` 5'ten fazla yeniden üreticiyi reddeder (model düzeltir); `decide`
  sonuçların tam olmasını ister, yoksa `yeniden:incomplete`. Sınır prompta yazılır.

### E06 · Yeniden üretici sözleşmesi belirsiz; stderr ve çıktı atılıyor · K
- **Kanıt.** Koltuk metni "beklenen çıktı" diyor (`29:21`); doğru davranışın mı kusurun mu beklendiği
  yazmıyor. `reproduce.py:24-27` yalnız çıkış kodu ve stdout'a bakar, çıktıyı saklamaz. İkinci provada
  rakip doğru bir kusur buldu, beklentiyi ters yazdı, `2>/dev/null` ile traceback'i attı.
- **Plan.** Sözleşme: gözlenen şey kusur yüzünden olmalı, kod doğru olsaydı olmamalı; `2>&1`;
  alt dize eşleşmesi. `expect_stderr_contains` eklenir; sonuçta gizli taranmış stdout/stderr kuyruğu
  saklanır. Test: yalnız stderr'de görünen traceback beklentiyle yeniden üretilir.

### E07 · Yeniden üretilemeyen iddia iz bırakmıyor · K · karar
- **Kanıt.** `29:30` "kayda geçer ama kabulü durdurmaz"; kayıt yalnız o koşunun 90 günlük artefaktı.
  Durumda iddia yok; sonraki rakip görmez (`rival.py:603-613`).
- **Seçenekler.** (a) yalnız kayıt (çıktı kuyruğuyla); (b) açık iddialar durumda tutulur ve sonraki
  rakibe verilir; (c) ayrıca her yeni başta mekanik olarak yeniden koşulur ve çıkışta listelenir.
- **Öneri.** (b) şimdi, (c) Aşama 0 çıkışından önce. Rakibe bir kez düzeltilmiş yeniden üretici yazma
  hakkı (R2-ii) da (b)'nin parçası olur.

### E08 · Kanıtlanmış kusur unutuluyor; tekrar sayacı iddia metnine bağlı · K · karar
- **Kanıt.** Durum yeniden üretilmiş yeniden üreticiyi tutmuyor (`state.py:26-28`); aynı ağaç yeni
  bir commit olarak gelince yalnız yeni rakip bakar (R1 senaryosu: kabul). İmza `sha256(iddia)`;
  aynı kusur iki ifadeyle iki imza (R1, D9).
- **Öneri.** Yeniden üretilmiş yeniden üreticiler (sınırlı sayıda) durumda tutulur, her yeni kod
  push'unda yeniden koşar; hâlâ üretiyorsa `refutation_still_reproduces`, imza
  `sha256(komut+beklenti)`. Kayıt yalnız kabul edilen başta artık üretmeyince ya da operatör
  feragatiyle kapanır. E09 olmadan açılmaz.

### E09 · Totolojik yeniden üretici "yeniden üretildi" sayılıyor · K · karar
- **Kanıt.** `{"cmd":"true","expect_exit":0}` → reproduced; zaman aşımına uğramış koşu stdout'u
  eşleşirse sayılıyor (R3).
- **Öneri.** Her yeniden üretici aynı imajda boş bir kontrol ağacında da koşar; gözlenen şey orada da
  çıkıyorsa `tautological`, sayılmaz. Taban ağaçta da üretiyorsa reddeder ama "önceden var" etiketi
  alır. Zaman aşımı hiçbir zaman "üretildi" değildir.

### E10 · Rakip Kurucu'nun defterini görüyor · K · karar
- **Kanıt.** `29:16` "Kurucu'nun defterini ve gerekçesini görmez"; diff ve `ToolBox` hiçbir yolu
  dışlamıyor (`rival.py:185-208`, `gitio.diff_text`); 29b ise tüm ağacı okuttuğunu yazıyor.
- **Öneri.** `founder-ledger.jsonl` diff'ten ve araçlardan gizlenir; 29 ve 29b aynı cümleye çekilir.

### E11 · Rakibin kendi hataları "öğrenmiyor" sayacına yazılıyor · K · karar
- **Kanıt.** D8 denemeleri: rakibin `budget`, `model_mismatch`, `max_turns`, `refusal`,
  `malformed_verdict` sonuçları üç kez üst üste → `not_learning`. `NOT_THE_FOUNDERS` yalnız `pull`'un
  bütçe nedenini kapsıyor; bütçe reddi mevcut ret serisini siliyor.
- **Öneri.** İki küme: Kurucu'nun düzeltebildikleri (testler, vektörler, lisans, yeniden üretilmiş
  çürütme, `prompt_too_large`, `max_turns`) sayılır; rakip tarafı (`model_mismatch`,
  `malformed_verdict`, `no_verdict`, `refusal`, `rival_missing`) ve bütçe seriye dokunmaz, kendi
  serisi operatöre uyarı olur. 29b:65 buna göre yazılır.

### E12 · Kalıcı 4xx ve izolasyon hataları sonsuz kesinti · K · karar
- **Kanıt.** `rival.py:556-558` her HTTP hatasını `api_error` yapar; D6 denemesi: beş `http_400`
  denemesi 14,5 USD ve değerlendirme yok. 29b:55 kesintiyi kimlik, kota, ağ ve zaman aşımıyla sınırlar.
- **Öneri.** 400/404/413/422 → `request_rejected` (değerlendirilmiş, Kurucu'ya sayılmaz, operatöre
  uyarı); izolasyon hatası operatör için durdurur; aynı SHA'da en fazla N=7 günlük yeniden deneme,
  sonra görünür durma.

### E13 · Rakip harcaması bazı yollarda hiç yazılmıyor · K
- **Kanıt.** Sonuçsuz CLI çıkışı 0 yazar (`rival.py:524-526`); iptalde `rival.json` yazılmaz; `yaz`
  imzalayamazsa durum yazılmaz ve tam boru hattı her saat yeniden koşar (W4: günde 24 × çağrı tavanı).
- **Plan.** CLI başlamış ve maliyet okunamamışsa çağrı tavanı yazılır, `rival.json` `finally`'de
  yazılır; `poll`, aynı başta `cagir` başarılı ama `yaz` başarısız bir koşu görürse park eder ve
  bildirir. Test: init verip çıkan sahte CLI → maliyet = tavan.

### E14 · İmzalı durum kaybolursa hakem sessizce tohumdan başlıyor · K · karar
- **Kanıt.** `cli.py:198-200` artefakt yoksa başlangıç durumu kurar; tazeleme adımı kill switch'ten
  sonra (`bootstrap.yml:74,124`); 90 günlük saklama. Donmuş spec'ler, bütçe, ret hafızası sıfırlanır.
- **Öneri.** Başlangıç yalnız operatör işaretiyle (`setup/summary.json` içinde ilk koşuya izin) olur;
  aksi halde "durum yok, kurtarma bkz." diye durur. Tazeleme kill switch'ten önce, ayrı bir adımda
  koşar (dosya kopyalamak yargı değildir). Kurtarma yolu `25`'e yazılır. Şema değişikliğinde "artefaktı
  sil" yerine sürümlü taşıma.

### E15 · Eski imzalı durum geri yüklenebiliyor · K
- **Kanıt.** `ghapi.py:36-38` en yeni artefaktı seçer; rehearsal'da aynı anda dört geçerli imzalı durum
  var; durum önceki sonucun hash'ini taşımıyor.
- **Plan.** Durum `prev_result_sha256` taşır; `yaz` yüklemeden önce en yeni artefaktın `cek`'in
  okuduğu olduğunu doğrular (karşılaştır-ve-yaz). Test: en yeni silinmiş ve eski koşu yeniden
  koşturulmuş iki durum → durur.

### E16 · Kill switch `yaz`'da canlı değil; iptal `yaz`'ı durdurmuyor · K · karar
- **Kanıt.** `yaz` checkout'u koşunun başındaki SHA'yı okur (rehearsal günlüğü); `if: always()`
  iptalde de koşar. Yol 2 (sırrı silmek) ve 3 (sağlayıcı tavanı) hiç denenmedi.
- **Öneri.** Her iş, ilk adımında `main`'deki `control.json`'u canlı okur; kill switch açıksa `yaz`
  kabul etmeyen, harcamayı yazan bir `stopped` sonucu imzalar. `always()` yerine `!cancelled()`.
  `25` madde 9'a `gh run cancel` ve `gh workflow disable` eklenir; yol 2 ve 3 denenir.

### E17 · Şablon enjeksiyonu; imza kimliği `main`'e sabit değil · K
- **Kanıt.** `bootstrap.yml:100` `${{ github.ref }}` doğrudan bash'e girer; `workflow_dispatch` her
  dalı kabul eder; kimlik koşunun kendi ref'ini izler.
- **Plan.** Her iş `if: github.ref == 'refs/heads/main'`; kimlik `env:` ile gelir ve
  `@refs/heads/main` ile bitmesi doğrulanır; artefaktlar `main` koşularına süzülür. Test: `run:`
  içinde `${{ github.* }}` yok.

### E18 · Testlerin toplam süresi sınırsız · K
- **Kanıt.** `kos` 60 dk; 200 test × 600 s; yavaş test işi öldürür → `infra kos` → park; Kurucu hangi
  testin takıldığını öğrenmez. `yeniden` için de aynı (W8, X5).
- **Plan.** `run-tests` ve `reproduce` toplam süre bütçesiyle koşar; aşınca kalan testler
  `not_run:time_budget` olur ve ret tipli yazılır. `test_timeout_s` ve `reproducer_timeout_s`
  `config.py`'de tavanlanır; kablolama testi iş zaman aşımlarıyla karşılaştırır.

### E19 · Kurucu kaynaklı hatalar altyapı arızası sınıflanıyor · K
- **Kanıt.** İndirilemeyen bir kilit pini `getir` başarısızlığı → `infra` (D12); kırmızı kontroller
  Kurucu'nun kilit dosyalarıyla koşuyor, kurulum hatası `infra kos:exit_zero` oluyor.
- **Plan.** `getir` tipli `deps.json` yazar (ağ hatası ile "böyle dağıtım yok/hash uyuşmuyor" ayrılır);
  kontroller kilitsiz koşar, ayrı bir kurulum yoklaması Kurucu reddine döner.

### E20 · Çıkıştaki rakip deneme sayımı ve "artefakt başına tek deneme" · K · karar
- **Kanıt.** `rival_artifacts` reddedilmiş ve yeniden üreticisi koşmamış SHA'ları da sayıyor (D10);
  `yeniden` kesintisinden sonra yeniden deneme rakibi tekrar çağırıyor (D11), `29:32` ile çelişiyor.
- **Öneri.** Liste `{sha, outcome}` tutar; çıkışta yalnız rakipten "sağ çıkmış" artefaktlar sayılır.
  Geçerli rakip sonucu durumda bekletilir; aynı başın yeniden denemesi rakibi değil yalnız yeniden
  üreticileri koşturur.

### E21 · Donmuş spec yeniden dondurulabiliyor · K · karar
- **Kanıt.** `cli.py:317-322` her `spec/asama-N`'i hash'ler, `decide.py:192-193` üzerine yazar;
  `02:43-44` "yalnız bir sonraki aşamanın spec'i donar".
- **Öneri.** Donmuş bir dizine dokunan spec isteği `spec_already_frozen`; yalnız sıradaki aşama
  dizini dondurulabilir; donmuş spec yalnız operatör kararıyla açılır.

### E22 · Tohumdaki Aşama 0 spec'i değiştirilmeden dondurulamıyor · K
- **Kanıt.** Değişikliksiz push değerlendirilmez (`classify.py:22-23`); `frozen_specs` boş başlar;
  her kod push'u `spec_not_frozen`. e2e bunu `00-ozet.md`'yi düzenleyerek atlatıyor.
- **Plan.** `00a` adım 2 ve `29b`: düzeltme gerekmezse inceleme `spec/asama-0/CHANGELOG.md`'ye tarihli
  satır olarak eklenir ve yalnız o dizini değiştiren push yapılır. Test: yalnız CHANGELOG değişen push
  donar.

### E23 · Çıkış kontrolü hakemin yapmadığı denetimleri sayıyor · K · karar
- **Kanıt.** `asama-0/10:13-27` `#lint`, `#lock`, `#okuyucu` ve etkinleştirme provasını hakemin makine
  doğrulaması sayıyor; `decide.py:152-167` bunları yapmıyor.
- **Öneri.** `29a` arayüzüne `spec.lint` ve `lock.check` komutları eklenir, hakem çıkışta koşar;
  diğerleri Kurucu'nun testi olarak yeniden yazılır.

### E24 · Kurulum özeti ve hash'ler denetlenmiyor · K
- **Kanıt.** `25:40-44` ve `asama-0/13:31` özet hash'inin Rekor'a girdiğini yazar; `config.load_summary`
  yalnız iki alanı okur, `result.json` hiçbir kurulum hash'i taşımaz.
- **Plan.** `result.json`'a `setup{summary, vectors, seats, policy}` hash'leri; `control`, vektör ya da
  koltuk hash'i özetle uyuşmazsa durur. Test: kurcalanmış `vectors.json` → `control` durur.

### E25 · `llm.call` ve `agent.dispatch` API anahtarı varsayıyor · K · karar
- **Kanıt.** `24:56-57` "tek Messages çağrısı", `24:52-54` ve `08:32-36` koşuya bağlı belirteçli geçit;
  bunlar Aşama 0'ın 20. ve 22. mikro özellikleri. Tek gerçek model yolu `rival.py` (anahtar yok).
- **Öneri.** İç kullanımda geçit yoktur: model çağrısı ve araç kullanan ajan, tohum rakibi deseniyle
  `çağır` işinde pinli `claude` CLI'siyle ve yalnız hakemin MCP araçlarıyla koşar; geçit satışta API
  anahtarıyla açılır. 24, 08, 06, 26a ve aşama sayfaları buna göre.

### E26 · Bu repoda CI yok · K · karar
- **Kanıt.** `.github/` yok; repo özel (Free planda ~2.000 dk); 16 test yalnız Linux'ta koşuyor;
  hakem kopyası elle eşitleniyor.
- **Öneri.** `snowball-mcp` de açık yapılır (operatör 2026-10-29'da "snowball mcp, beyin, hakem açık
  olabilir" demişti; dakika ücretsiz olur). CI: her push'ta Linux birim + drill; Windows birim;
  haftalık ve ilgili değişiklikte mutasyon parçaları, beyin mutantları, e2e (rakipsiz), CLI sözleşmesi;
  `actionlint`.

### E27 – E40
Ayrıntıları özet tablodaki kaynak bulgulardadır; her biri ele alınırken bu bölüme kanıt, plan ve
test satırlarıyla eklenir.

## Doğrulanmış sağlam taraflar
Kapsayıcı bayrakları ve kırmızı kontroller; host'ta kabuk enjeksiyonu yok; `$GITHUB_OUTPUT`'a serbest
metin girmiyor; tek sır yalnız rakip adımında; rakibin ortamı ve init doğrulaması; ağaç kurulurken
kancalar ve filtreler etkisiz; işler arası artefakt hash'leri; imzalı durumun kimlik doğrulaması;
spec'te 80 satırı aşan sayfa, kırık çapraz referans ya da INDEX uyumsuzluğu yok; vektörler ve mikro
özellik→test haritası spec ile birebir.

## Sıra
Her parti kendi dalında kapanır, testleri ve mutantlarıyla `main`'e merge edilir, kayıttaki satırlar
o commit ile `kapandı` olur.

1. **Güvenlik, çökme ve takılma:** E01, E02, E41, E03, E04, E05, E17.
2. **Rakip ve yeniden üretme:** E06, E07, E08, E09, E10, E11, E12, E13, E20, E27, E33.
3. **Durum ve iş akışı:** E14, E15, E16, E18, E19, E29, E30, E31, E32, E34, E26 (CI).
4. **Spec:** E21, E22, E23, E24, E47, E25, E35, E36, E37.
5. **Doğrulama araçları:** E42, E43, E44, E45, E46, E48, E49, E50, E51, E38, E39, E40.
