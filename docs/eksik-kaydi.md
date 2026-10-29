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
| E01 | Beyin komutunun 125 çıkışı "Docker arızası" sayılıyor | K | — | R4 X4 D1 | kapandı · parti 1 |
| E02 | Beynin içeriği `pull`'u çökertiyor; hakem saatlik takılıyor | K | — | X3 X7 D2 | kapandı · parti 1 |
| E03 | Dosya adındaki satır sonu rakibin isteğine sahte bölüm ekliyor | K | — | R5 | kapandı · parti 1 |
| E04 | İçe aktarma, beynin `.git/hooks`'unu operatörün checkout'una yazıyor | K | — | X1 | kapandı · parti 1 |
| E05 | Beşinciden sonraki yeniden üreticiler sessizce koşmuyor | K | — | R7 D3 | kapandı · parti 1 |
| E06 | Yeniden üretici sözleşmesi belirsiz; stderr ve çıktı atılıyor | K | — | R2 D4 | kapandı · parti 2 |
| E07 | Yeniden üretilemeyen iddia iz bırakmıyor | K | evet | D4 R2 | kapandı · parti 2 |
| E08 | Kanıtlanmış kusur unutuluyor; tekrar sayacı iddia metnine bağlı | K | evet | R1 D9 | kapandı · parti 2 |
| E09 | Totolojik yeniden üretici (`true`) "yeniden üretildi" sayılıyor | K | evet | R3 | kapandı · parti 2 ("önceden var" etiketi: sınır, bkz. Parti 2) |
| E10 | Rakip Kurucu'nun defterini görüyor (spec yasaklıyor) | K | evet | R6 S3 | kapandı · parti 2 |
| E11 | Rakibin kendi hataları Kurucu'nun "öğrenmiyor" sayacına yazılıyor | K | evet | R11 S11 D8 | kapandı · parti 2 |
| E12 | Kalıcı 4xx ve izolasyon hataları sonsuza dek kesinti diye yeniden deneniyor | K | evet | D6 | kapandı · parti 2 |
| E13 | Rakip harcaması bazı yollarda hiç yazılmıyor | K | — | R9 D5 W4 | kapandı · parti 2 (iptalde yükleme: E16 ile) |
| E14 | İmzalı durum kaybolursa hakem sessizce tohumdan yeniden başlıyor | K | evet | W1 D7 | spec yazıldı · kod açık |
| E15 | Eski imzalı durum geri yüklenebiliyor (zincir yok) | K | — | W2 | spec yazıldı · kod açık |
| E16 | `yaz`'daki "canlı" kill switch canlı değil; iptal `yaz`'ı durdurmuyor | K | evet | W3 | spec yazıldı · kod açık |
| E17 | İş akışında şablon enjeksiyonu; imza kimliği `main`'e sabit değil | K | — | W7 | kapandı · parti 1 |
| E18 | Testlerin toplam süresi sınırsız; yavaş test "ret" değil "kesinti" | K | — | W8 X5 D12 | açık |
| E19 | Kurucu kaynaklı hatalar altyapı arızası sınıflanıyor | K | — | D12 | açık |
| E20 | Çıkıştaki "bağımsız rakip denemesi" sayımı yanlış; yeniden deneme rakibi tekrar çağırıyor | K | evet | D10 D11 | kapandı · parti 2 |
| E21 | Donmuş spec yeniden dondurulabiliyor; her aşama dizini donuyor | K | evet | S1 D14 | spec yazıldı · kod açık |
| E22 | Tohumdaki Aşama 0 spec'i değiştirilmeden dondurulamıyor | K | — | S2 | spec yazıldı · kod açık |
| E23 | Çıkış kontrolü hakemin yapmadığı denetimleri sayıyor | K | evet | S4 | spec yazıldı · kod açık |
| E24 | Kurulum özeti, vektör, koltuk ve politika hash'leri denetlenmiyor | K | — | S5 | spec yazıldı · kod açık |
| E25 | Aşama 0'ın `llm.call` ve `agent.dispatch` sayfaları API anahtarı ve geçit varsayıyor | K | evet | S6 | kapandı · spec (Aşama 0 MF20/MF22 kodu Kurucu'nun) |
| E26 | Bu repoda CI yok | K | evet | W5 | onaylandı; repo açıldı (2026-10-29) · CI açık |
| E27 | İzolasyon hatası ancak tam koşudan sonra fark ediliyor | B | — | R8 | kapandı · parti 2 |
| E28 | Kapsayıcı çıktısı belleğe sınırsız alınıyor | B | — | X2 | açık |
| E29 | Operatörü uyaran hiçbir şey yok | B | evet | W6 | spec yazıldı · kod açık |
| E30 | Kablolama testleri izinleri, adım çıktılarını ve tetikleri denetlemiyor | K | — | W10 | açık |
| E31 | Action'lar eskimiş Node 20 sürümlerinde; her action'a izin var | B | — | W9 | açık |
| E32 | Zamanlayıcı hiç tetiklenmedi; açık repo güvenlik ayarları kapalı | K | evet | W12 | onaylandı; sır taraması ve itme koruması açıldı, beyin reposunda Actions kapatıldı (2026-10-29) · zamanlayıcı açık |
| E33 | CLI sürüm kayması ve koşu kökeni kaydedilmiyor | B | — | R12 W11 | kapandı · parti 2 |
| E34 | Bütçe bitince commit tüketiliyor; ay dönünce kendiliğinden açılmıyor | B | evet | S9 D13 | spec yazıldı · kod açık |
| E35 | Açık hakem reposu ile özel hedef birlikte olamaz; spec yazmıyor | B | evet | S7 | kapandı · spec |
| E36 | 09a aktarım yolunu açık repoda kapanmış sayıyor | K | — | S8 | kapandı · spec |
| E37 | Spec temizliği: tempo, aktarım betiği, çapraz referans, sağlayıcı, ret kuralları, okuyucu tablosu, iş sayısı, başlıklar | B | — | S10 S12–S20 R14 | kapandı · spec |
| E38 | Windows'ta model seçimli regex'in süre sınırı yok | S | evet | R13 | onaylandı · açık |
| E39 | Rakibe prompt injection kalıntı riski | S | evet | X6 | onaylandı · açık |
| E40 | Çalışma zamanı ve Sigstore pinlerinin yenileme yolu yok | B | — | W13 | açık |

| E41 | Bozuk çıkış isteği `decide`'ı çökertiyor; hakem saatlik takılıyor | K | — | T1 | kapandı · parti 1 |
| E42 | Bağımlılık yolu (`fetch-deps`, kapsayıcıda kurulum, lisans kapısı) hiçbir testte yok; e2e de kaybetti | K | — | T2 | açık |
| E43 | En yeni imzalı durumu seçen kod test edilmiyor | B | — | T3 | açık |
| E44 | Operatör ve durum zinciri yolları yalnız Linux'ta test ediliyor | B | — | T4 | açık |
| E45 | Mutasyon seti kapsayıcı, git, lisans, içe aktarma modüllerini hiç bozmuyor; `/vec` ve `/deps` salt okunurluğu denetlenmiyor | B | — | T5 | açık |
| E46 | Ağaç hash formülü ve `seed-hash` sabitlenmemiş; kayma Kurucu'ya yazılıyor | B | öneri | T6 | açık |
| E47 | `.gitattributes` yok; özet hash'leri hesaplanmıyor (E24 ile birlikte) | B | öneri | T7 | spec yazıldı · kod açık |
| E48 | Prova yargıcının beş dalını ne testler ne tohum vektörleri bağlıyor | B | öneri | T8 | kapandı · `gaps/drill` |
| E49 | Başarısız olamayan ya da yanlış nedenle geçen testler | S | — | T9 | açık |
| E50 | Ölü kod ve ölü çıktılar | S | — | T10 | açık |
| E51 | Testler üretimden farklı bir biçimi modelliyor | S | — | T11 | açık |
| E52 | Prova yargıcının ~20 kuralı yalnız referans yargıcın kendi testleriyle bağlı; Kurucu'nun yargıcını bağlayan vektör yok | B | — | E48 ajanı | açık |
| E53 | Açık bildirimi: Kurucu hakemde bulduğu açığı kullanmaz, kanıtıyla bildirir; hakem doğrular, düzeltme bağımsız kontrol ve operatör onayıyla girer; doğrulanmış bildirim Kurucu'ya artı sayılır | K | operatör yönü | operatör, 2026-10-29 | açık |

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

### E53 · Açık bildirimi · K · operatör yönü (2026-10-29)
- **Yön.** Operatör: Kurucu kötü niyetli değildir, yalan söylemez; amaç dünyanın en iyi sistemini
  birlikte ve sabırla kurmaktır. Hakemde bir açık bulursa onu kullanmaz, hakeme söyler; hakem
  doğruladıktan sonra kendini onarır.
- **Neden açıklar yine kapanır.** İyi niyetli Kurucu da hata yapar ve açık, hatayı içeri sızdırır (ikinci
  provada dürüstçe yazılmış referans beynin gerçek bir kusuru yanlış yazılmış bir yeniden üretici yüzünden
  kabul edildi). "Kabul" ile ödüllenen öğrenen bir sistem, niyet olmadan da kabul alan yola kayar.
- **Kurucu'nun görevleri (operatör, 2026-10-29).** Kurucu'nun hedefi yalnız kabul almak değildir:
  (a) işini doğru yapar, testten geçmek için değil; (b) açıkları kullanmaz; (c) hakemde, spec'te, testlerde
  ya da kendi kodunda gördüğü her eksikliği derhal bildirir; (d) bildirdiğinin düzeltilip düzeltilmediğini
  kendisi denetler: düzeltme gelince kendi testini yeni koda karşı yeniden koşturur, düzelmediyse kanıtıyla
  yeniden açar. Bildirimin yaşam döngüsü: açık → doğrulandı → düzeltildi → Kurucu teyit etti → kapandı.
- **Plan.** (1) `00a` anayasasına bu dört görev yazılır. (2) Bildirim beyin
  reposunda tipli bir dosyadır: hakemin bugünkü kodunda kırmızı olan bir test ve isteğe bağlı düzeltme
  önerisi. (3) Hakem doğrular: test bugünkü hakemde kırmızı, önerilen düzeltmeyle yeşil, hakemin diğer
  testleri ve mutantları yeşil. (4) Düzeltme hakeme yalnız bağımsız kontrol ve operatör onayıyla, aktarım
  yolundan girer (`01a`, `09a`): yargılanan kendi yargıcını tek başına değiştirmez. (5) Doğrulanmış
  bildirim Kurucu'ya artı sayılır (itibar ve ret hafızası dışı), açığı kullanmak hiçbir zaman ödüllenmez.
  Her doğrulanmış bildirim hakemde kalıcı bir test (ders) bırakır: kendini iyileştirmenin hakemdeki hâli.

### E27 – E40
Ayrıntıları özet tablodaki kaynak bulgulardadır; her biri ele alınırken bu bölüme kanıt, plan ve
test satırlarıyla eklenir.

## Kapanışlar

### Parti 1 (2026-10-29) · E01 E02 E03 E04 E05 E17 E41
- **E01.** `container.RUN`: komut `exec` edilmez, 125'i 1 olur. Kanıt: gerçek Docker'da `exit 125` → 1,
  `exit 3` → 3, stdin/stdout geçer, Docker'ın kendi hatası (eksik imaj) → 125; POSIX testi; mutant
  `command_can_claim_dockers_125`.
- **E02 / E41.** `pull` sınıflandırması `_pull_classify`'de; içerikten doğan her hata `pull_error`
  reddi (Kurucu'ya sayılmaz); manifestte aşama ve `done_mf` 1000 ile sınırlı, yalnız vekil karakter ve
  derin JSON `manifest_invalid`; çıkış isteği tip ve biçimle denetlenir; `decide` reddedilmiş isteğin
  SHA'sını okumaz. Testler: beş bozuk manifest, altı bozuk çıkış isteği, sınıflandırma çökmesi.
  Mutantlar: `pull_crash_wedges_the_referee`, `exit_request_types_unchecked`, `manifest_stage_unbounded`,
  `manifest_surrogate_allowed`, `pinned_sha_of_a_refused_request`, `pull_error_held_against_the_founder`.
- **E03 / E04 / X7.** `treehash.path_problem`: denetim karakteri, `.git` bileşeni (büyük-küçük harf
  duyarsız), `:` ve `\` → `pull`'da `unsafe_path` reddi, `tree_hash` ve `extract`'ta `TreeError`
  (içe aktarma önce hash'ler, kancaya hiç yazılmaz). Rakibin isteği koşu başına rastgele bir çitle
  bölünür, yollar JSON dizesi. Testler: altı ad tek tek; `.git/hooks` ağacı; sahte başlık. Mutantlar:
  `control_character_in_a_name`, `dot_git_component_allowed`, `unsafe_name_reaches_the_tree_hash`,
  `predictable_context_fence`.
- **E05.** `validate_verdict` 5'ten fazla yeniden üreticiyi reddeder (prompt sınırı söyler); `decide`
  her yeniden üreticinin sonucunu ister, yoksa `yeniden:incomplete` kesintisi. Mutantlar:
  `sixth_reproducer_accepted`, `unrun_reproducer_clears_a_push`.
- **E17.** `cek` ve `yaz` yalnız `refs/heads/main`'de koşar; Sigstore kimliği `${GITHUB_REPOSITORY}` ile
  `@refs/heads/main`'e sabit, `run:` içinde `${{ github.* }}` yok; durum artefaktı yalnız `main`
  koşularından seçilir. Testler: kablolama ve artefakt seçimi (en yeni, süresi dolmamış, `main`).
  Mutantlar: `artifacts_from_any_branch`, `state_verified_as_the_runs_own_ref`.
- **Kanıt özeti.** Windows 225 test OK (17 atlandı), Linux 242 OK (3 atlandı); mutasyon 77 mutant,
  ilk koşuda 75; hayatta kalan iki mutant testleri sıkılaştırdı (her ad ayrı commit'te; atlanan
  yeniden üretimin nedeni), yeniden koşuda öldü; e2e Docker'da `accepted`.

### Parti 2 (2026-10-29) · E06 E07 E08 E09 E10 E11 E12 E13 E20 E27 E33 · E141
Testler `tests/test_rival_memory.py`'de, sınıf adları kalem numarasıyla. Durum şeması 2'ye çıktı.
- **E06.** Rakibin protokolü ve `submit_verdict` sözleşmeyi söyler: gözlenen şey kusur yüzünden görülür, kod
  doğru olsaydı görülmez; traceback için `expect_stderr_contains` ya da `2>&1`; beklenti düz alt dizedir; en çok
  beş. `reproduce` stdout ve stderr'in son 2000 karakterini gizli taramasından geçirip saklar; zaman aşımına
  uğramış koşu hiçbir beklentiyi karşılamaz. Testler: yalnız stderr'deki traceback üretildi, kuyruklar sınırlı ve
  sırsız, zaman aşımı üç beklenti türünde de üretmez. Mutantlar: `protocol_without_the_contract`,
  `stderr_expectation_ignored`, `timed_out_run_reproduces`, `reproducer_tails_not_scanned`.
- **E09.** Gözleneni gösteren yeniden üretici aynı imaj ve ön adımla, kilit dosyası kurulmadan, boş (0755) bir
  kontrol ağacında da koşar; orada da gösteriyorsa `tautological`, sayılmaz; oradaki Docker hatası
  `runner_fault`. `true`/`expect_exit 0` ve yalnız çıkış koduna bakan yeniden üretici ("No module named" de 1
  ile çıkar) totolojiktir. "Önceden var" etiketi **sınır**: taban ağacı `yeniden`'e yeni bir artefakt olmadan
  gelmiyor; `29` bunu söylüyor. Mutantlar: `tautology_not_checked`, `control_tree_is_the_head`.
- **E07.** Yeniden üretilmeyen ya da yeniden üreticisiz çürütme durumda `open_claims` olarak kalır (en çok 10,
  en yenileri; iddia, ref'ler, yeniden üretici, gözlenen kuyruklar, ilk baş, `rewritten`). Sonraki rakibin
  isteğinde çitli bir bölümde kimliğiyle durur; rakip `open_claim` ile bir kez yeniden yazar. Açık iddialar her
  kod ve çıkış başında mekanik koşar, üretirse kanıtlanmış kusur olur; çıkış bloğu `open_claims`'i listeler.
  Mutantlar: `unreproduced_claim_forgotten`, `open_claims_not_shown_to_the_rival`, `claim_rewritten_twice`,
  `open_claim_never_rerun`.
- **E08.** Üretilmiş yeniden üretici `open_refutations`'ta kalır (en çok 20). `pull` her kod ve çıkış başında
  onları `state_repro` diye ister (çıktı `repro`), `yeniden` rakip `not_refuted` dese de koşturur; hâlâ
  üretiyorsa `refutation_still_reproduces`. İmza `refutation:` + `sha256(komut+beklentiler)`'in ilk 16 hanesi,
  yeni bulunanla aynı seri: iki ifadeyle üç push `not_learning`. Kayıt yalnız kabul edilen başta koşup
  üretmeyince ya da `control.json` `waived_refutations` (operatör feragati) ile kapanır. Mutantlar:
  `proven_defect_forgotten`, `state_reproducers_never_asked_for`, `still_reproducing_defect_accepted`,
  `refutation_signed_by_its_wording`, `proven_defect_never_closes`, `operator_waiver_ignored`,
  `reproduction_job_only_for_the_rival`.
- **E10.** `founder-ledger.jsonl` diff'ten (`:(exclude,glob)**/founder-ledger.jsonl`), istekteki değişen
  yollardan ve `ToolBox`'ın `read_file`, `grep`, `glob` ve satır sayımından çıkar; sınıflandırma onu yine görür.
  Mutantlar: `ledger_readable_by_the_rival`, `ledger_in_the_rivals_diff`, `ledger_named_in_the_request`.
- **E11.** Kurucu'ya sayılan: test, vektör, lisans, `pull`'un tipli retleri, yeniden üretilmiş ve hâlâ üreten
  çürütme, `prompt_too_large`, `max_turns`, `secret_in_prompt`. Rakip tarafı (`model_mismatch`,
  `malformed_verdict`, `no_verdict*`, `secret_in_verdict`, `refusal`, rakibin `budget`'ı, `request_rejected`,
  `rival_missing`), `budget`, `pull_error` ve altyapı serileri olduğu gibi bırakır. Üç ardışık rakip tarafı hata
  `warnings: rival_side_streak:3` ve `::warning::`. Mutantlar: `rival_side_failure_counts_against_the_founder`,
  `neutral_rejection_resets_the_streaks`, `rival_missing_held_against_the_founder`, `rival_side_streak_never_warns`.
  **K6** (kod denetçisi, 2026-10-29): `main`'de üç `secret_in_verdict` üst üste
  `{'rival_unresolved:secret_in_verdict:generic_assignment': 3}` ve `not_learning` veriyordu; sır rakibin yazdığı
  karardadır, rakip tarafıdır. `secret_in_prompt` Kurucu'nun diff'inden gelir, Kurucu tarafında kalır. Test: üç
  `secret_in_verdict` seriye dokunmaz, üç `secret_in_prompt` `not_learning`. Mutant:
  `secret_in_verdict_held_against_the_founder`.
- **E12.** 400/404/413/422 → `request_rejected:http_N`: değerlendirilir, Kurucu'ya sayılmaz, uyarır. Sayaç
  durumdadır (`outage_since`); park edilen baş 7 gün sonra `poll`'da kırmızı durur (`::error::`, çıkış 1).
  `isolation_*` → `outage_stop`: o baş zamanlayıcıyla denenmez, koşu kırmızıdır; operatör nedeni giderip
  `workflow_dispatch` ile bir kez denetir. Mutantlar: `permanent_4xx_retried_as_an_outage`,
  `isolation_fault_is_a_silent_outage`, `operator_stop_not_enforced`, `outage_retried_forever`,
  `outage_clock_restarts`, `dispatch_cannot_retry`.
- **E13.** Başlamış CLI'nin okunamayan maliyeti (sonuçsuz çıkış, bozuk sonuç, zaman aşımı, kesme)
  `min(kalan, koşu tavanı)` yazılır; hiç başlamayan ve `init`'te öldürülen koşu 0'dır. `rival` komutu
  `rival.json`'u `finally`'de yazar. `poll`, en yeni başarısız koşuda `cagir` başarılı, `yaz` başarısızsa,
  imzalı durum ondan eskiyse ve o koşunun `rival.json`'undaki baş aynıysa günde bir dener (`ghapi` koşu API'si,
  `actions: read`). Açık kalan: iptal ya da zaman aşımında `cagir`'ın paketleme ve yükleme adımları koşmaz;
  bu iş akışı değişikliği E16 (`!cancelled()`) ile. Mutantlar: `unparsed_cost_is_free`,
  `unreadable_cost_is_free`, `interrupted_run_leaves_no_record`, `unsigned_rival_run_reruns`,
  `unsigned_run_of_any_head_parks` (ve güncellenen `timeout_is_free`). **K7** (kod denetçisi): maliyet yalnız
  rakip "beklenirken" yazılıyordu, bu da yeşil bir `run.json` ister; `run.json` yoksa (`kos` başarısız, yükleme
  kaybı) `main`'de 4 000 000 mikro dolarlık harcama düşüyordu. Artık `rival.json` geldiyse maliyet her durumda
  yazılır (yeniden kullanılan sonuç hariç). Test: `run.json` yok, `kos=failure`, `cagir=success` → aylık ve aşama
  harcaması +4 000 000; kırmızı testli koşuda da yazılır. Mutant: `spend_of_an_unjudged_rival_dropped`.
- **E141** (K2, kod denetçisi; E01 sınıfı, vektörlerde). Vektör sonucu çıkış kodunu tutmuyordu ve `decide` 125'e
  yalnız testlerde bakıyordu: vektörler sırasında Docker'ın kendi hatası `vector_failed` oluyordu, yargılanıyor,
  hiç yeniden denenmiyor ve seriye yazılıyordu (`main`'de üç koşuda `not_learning:
  ['vector_failed:chain.V1.hash', ...]`). E01'den beri komutun kendi 125'i 1'e çevrildiği için 125 yalnız
  Docker'dır. Vektör sonucu `exit` ve son deneme 125 ile bittiyse `runner_fault` taşır; `decide` bunu 125 ile biten
  test gibi `infra kos:docker` kesintisi sayar. Test: her `docker run` 125 dönen koşucuyla üç push → kesinti,
  `last_evaluated_sha` değişmez, seriler aynı; Kurucu'nun kendi hatası (exit 1) `runner_fault` değildir.
  Mutantlar: `vector_docker_fault_judged`, `vector_exit_not_kept`.
- **E20.** `rival_artifacts` `{sha, outcome}` (`survived`, `refuted`; v1'den taşınan `unknown`); kayıt yalnız
  yeniden üreticiler tamamlanınca; çıkış yalnız `survived`'ı sayar. `yeniden` kesintisinde geçerli sonuç
  `pending_rival`'dır; aynı başın denemesinde `pull` rakibi çağırmaz (`reuse_rival`, bütçe engeli yok), maliyet
  ikinci kez yazılmaz, yalnız yeniden üreticiler koşar. Mutantlar: `any_reviewed_artifact_counts_at_exit`,
  `retry_calls_the_rival_again`, `reused_rival_booked_twice`, `artifact_recorded_before_its_reproducers_ran`.
- **E27.** CLI çıktısı akarken okunur; `init` olayı geldiği an önce izolasyon, sonra pinli sürüm, sonra model
  denetlenir, hata varsa süreç ağacı hemen öldürülür, maliyet 0. Kötü init basıp 60 s uyuyan sahte CLI 10 s
  altında döner (Windows'ta dört koşu ~2 s), MCP sunucusuna araç çağrısı ulaşmaz. Mutantlar:
  `init_checked_only_after_the_run`, `model_checked_before_isolation` (ve güncellenen `second_communicate_unbounded`).
- **E33.** `rival.json`: `cli_version`, `effort`, `prompt_sha256` (sistem + "\n" + istek), `tokens`, `duration_ms`,
  `head`. Pinden farklı sürüm `api_error:isolation_version` (init'te ve koşu sonunda), yani E12'nin operatör
  durdurması. Mutantlar: `version_drift_accepted`, `post_run_version_unchecked`, `provenance_not_recorded`.
- **Durum v2.** `state.migrate` v1'i taşır (bütçe, seriler, donmuş spec'ler, kabul edilen SHA aynen;
  `rival_artifacts`'ta yalnız son kabul `survived`); `fetch-state` silmek yerine taşır; bilinmeyen biçim yine
  durur ve `25`'i gösterir (E14'ün taşıma parçası). Mutantlar: `old_state_not_migrated`,
  `migration_trusts_unknown_artifacts`, `new_state_fields_unchecked`.
- **İş akışı.** Yalnız `yeniden`: `cek` çıktısı `repro`; koşul "rakibin yeniden üreticisi var ya da `repro` ve
  (spec ya da yeşil `kos`)"; `kos`'a bağımlılık; `rival` artefaktı yalnız `cagir` başarılıysa indirilip
  doğrulanır.
- **Spec.** `29` Rakibin kuralları: kontrol ağacı yalnız gözleneni gösteren yeniden üreticide ve kilitsiz;
  "önceden var" ölçülmez; sınırlar (20, 10), `open_claim`, feragat alanı, çıkışta da koşma, üreten açık iddia
  kanıtlanmış kusurdur. `29b` `yeniden` satırı aynı.
- **Kanıt özeti.** Kırmızı: yeni testlerin 53'ü eski kodda kırmızı (ikisi koruma testi); eski pakette denetim
  senaryoları: üç `model_mismatch` → `not_learning`, bütçe reddi seriyi siliyor; kanıtlanmış kusur aynı ağaçla
  `accepted`; aynı yeniden üretici iki ifadeyle iki imza; `true` ve zaman aşımı "üretildi"; çürütülmüş baş çıkışta
  sayılıyor; kötü init 60 s bekletiyor ve 12 300 mikro dolar yazıyor; dört kalıcı 4xx kesinti. Yeşil:
  Windows 284 test OK (21 atlandı: 18 POSIX, `claude` PATH'ten çıkarıldığı için 3 canlı CLI), Linux 305 OK
  (3 atlandı). K2, K6, K7 senaryoları `main`'de aynen tekrarlandı (yukarıda). Mutasyon 128 mutant (77 + 51
  yeni); K'lerden önceki 124'lük ilk koşuda 122: `toolbox_escapes_the_tree` (yeni defter
  denetimi `relative_to` ile ağaç dışını da reddedip korumayı ölçülmez kılmıştı; artık yalnız ad bakar) ve
  `reused_rival_booked_twice` (bekleyen sonuç maliyetsiz saklanıyordu; artık maliyetiyle saklanır, bir kez
  yazıldığı test edilir); son koşuda (Linux, dört parça) 128/128 öldü. Ayrıca kontrol ağacı `mkdtemp` ile 0700 açılıyordu;
  65534 kullanıcısı onu kopyalayamaz (kapsayıcıda denendi), 0755 yapıldı ve testle bağlandı.

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
