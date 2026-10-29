# Aşama 0 daraltması: `29` ve `29b` için bekleyen düzenlemeler

Tarih: 2026-10-29. Kaynak: `docs/asama-0-daraltma.md` §6 Parti 2 (`29`, `29b` satırları) ve sahibin K5 değişikliği
(bütçe yalnız kaçak frenidir; oturum ve USD ölçümdür; abonelik penceresi 429 kesintidir, ret değildir). Bu iki
sayfa başka bir dalda değiştiği için düzenlemeler burada bekler; o dal birleşince uygulanır. Satır numaraları
`gaps/stage0-spec` dalının tabanındaki (cb796bd) sayfalaradır. Diğer dal satır kaydırırsa bloklar metne göre
eşlenir: her bloğun eski ilk satırı alıntılanmıştır.

**Uygulama.** Her blok "satır X–Y'yi kaldır, yerine metni koy"dur; bloklar alttan üste uygulanırsa numaralar
kaymaz. `29b` 80 satır sınırında olduğu için durum, tohum dönemi, aşama tablosu, tohum denetimleri, bildirimler,
çıkış ve dürüstlük yeni `29e` sayfasına taşınır (tam metni §3). Uygulandıktan sonra: `29b` 79 satır, `29e` 64
satır, `29` 72 satır.

## 1. `spec/tohum/29-tohum-koltuklari.md`

### 29:16–18 → 4 satır

Rakip `reports/`'u görmez; Aşama 0'dan sonra da önyükleme hakemi çağırır. Eski ilk satır: "yoktur. Ayrı bağlamda artefaktı (son kabul edilmiş SHA'dan b…"

```text
yoktur. Ayrı bağlamda artefaktı (son kabul edilmiş SHA'dan bu yana tam diff), ilgili tohum sayfalarını ve
salt okunur araçlarla commit ağacını görür; `founder-ledger.jsonl` ve `reports/` diff'ten ve ağaçtan
çıkarılır, Kurucu'nun defterini, bildirimlerini ve gerekçesini görmez. Kurulumdan itibaren ve Aşama 0'dan
sonra da önyükleme hakemi çağırır (`29b`).
```

Başka değişiklik yok: `25` 3 ve `25a` 1 atıfları geçerli kalır (`25`'in madde numaraları korundu).

## 2. `spec/tohum/29b-onyukleme-hakemi.md`

### 29b:1 → 1 satır

Başlık: Aşama 0'dan sonra da itme yargıcı (K1). Eski ilk satır: "# Önyükleme Hakemi: Aşama 0'ın Yargıcı…"

```text
# Önyükleme Hakemi: Beyin Reposunun İtme Yargıcı
```

### 29b:4–5 → 2 satır

Okunma ve çapa: aşama tabloları. Eski ilk satır: "Okunma: kurulumda ve Aşama 0 boyunca…"

```text
Okunma: kurulumda, Aşama 0 boyunca ve sonra her push yargısında
Çapa: `seed/bootstrap/` (kod, iş akışı, aşama tabloları ve testleri); hakem reposundaki kopyası
```

### 29b:9–14 → 9 satır

Giriş: K1; `stages/`; tohum dönemi; aktarım her çıkışta `import` ve önyükleme hakemine dokunmaz; eski `asama-0/14` 30 atfı kalkar; `29e`'ye yönlendirme. Eski ilk satır: "Aşama 0'da Kurucu hakemi yazar; o hakem henüz yoktur, Kurucu…"

```text
Döngü hakemini Kurucu yazar; o hakem henüz yoktur, Kurucu da kendi yargıcı olamaz (Y6). Boşluğu tohumla
gelen, Kurucu'dan önce ve Kurucu olmayan bir yazarca yazılmış küçük, deterministik önyükleme hakemi
kapatır: beyin reposunun `seed/bootstrap/` dizininde `snowball_bootstrap` paketi (yalnız standart
kütüphane), `workflow/bootstrap.yml`, hash'e sabitli `requirements/` (Sigstore, `claude` CLI), `vectors/`,
`stages/` ve `tests/`. Operatör kurulumda hakem reposuna kurar (`25` 3); Kurucu ona yazamaz; yalnız tohum
dönemiyle değişir. **Aşama 0'dan sonra da beyin reposunun itme yargıcıdır:** push kabulü, aşama kilidi ve
rakip çağrısı Kurucu'nun işi değildir. Aşama ve parti çıkışlarındaki aktarım bu paketin `import`
komutudur (`25a` 1) ve önyükleme hakemine dokunmaz. Durum, aşama tablosu, tohum denetimleri ve çıkış
`29e`'dedir.
```

### 29b:23 → 1 satır

`çek`: tohum dönemi karşılaştırması, `reports/`, tohum denetimleri. Eski ilk satır: "| `çek` | Kimliksiz beyin okuma; Actions okuma | Önceki imza…"

```text
| `çek` | Kimliksiz beyin okuma; Actions okuma | Önceki imzalı durumu Sigstore ile doğrular; kendi `bootstrap/` hash'ini son tohum döneminin `bootstrap_sha256`'sıyla karşılaştırır, uyuşmazsa durur; SHA'yı çeker, sınıflandırır, ağacı blob blob kurar (`export-ignore` etkisizdir); `reports/`'u okur ve tohum denetimlerini uygular (`29e`) |
```

### 29b:25 → 1 satır

`koş`: geçerli aşama testleri, sahipli vektör grupları, modülsüz kırmızı. Eski ilk satır: "| `koş` | Yok | Tekerleklerin lisans kapısı (`24`; hakemin k…"

```text
| `koş` | Yok | Tekerleklerin lisans kapısı (`24`; hakemin kendi Sigstore tekerlekleri de kurulmadan önce geçer, kaydı `requirements/licenses.json`); kırmızı kontroller, `snowball-tests.json` bildirimindeki geçerli aşamanın testleri, sahibi bitmiş vektör grupları (`29a`, `29d`) ve bu push'la biten MF'nin modülsüz kırmızı yeniden koşusu, her biri `--network none --cap-drop ALL --read-only --user 65534` konteynerde |
```

### 29b:28 → 1 satır

`yaz`: `status-stage0.md`; `not_learning`, park ve sonuçsuz bekleme imzadan sonra kırmızı. Eski ilk satır: "| `yaz` | OIDC, içerik okuma | Kararı verir, sonucu Sigstore…"

```text
| `yaz` | OIDC, içerik okuma | Kararı verir, sonucu Sigstore ile imzalayıp Rekor'a bağlar, imzalı durumu ve `status-stage0.md`'yi yükler; `not_learning`, park ve push'tan sonra sonuçsuz bekleme koşuyu imzadan sonra kırmızı bitirir; kill switch açıksa kabul etmeyen, harcamayı yazan `stopped` sonucu imzalar; iptal edilen koşu hiçbir şey imzalamaz |
```

### 29b:30–35 → sil

**Durum** paragrafı ve ardındaki boş satır silinir; metin `29e`'ye taşınır (ilk koşu işareti kuralıyla). Eski ilk satır: "**Durum.** Bellek, önceki koşunun imzalı `bootstrap-state` a…"

### 29b:36–42 → 11 satır

Üç tür push → push türleri: `ledger`, `seed_update`, `seed_modified`, `agent_config_modified`, kökteki `.github/`. Eski ilk satır: "**Üç tür push.** Yalnız `spec/asama-*/` ve `spec/INDEX.md` d…"

```text
**Push türleri.** Yalnız `spec/asama-*/` ve `spec/INDEX.md` değiştiren push **spec isteğidir**: test
aranmaz, rakip çürütmeyi dener; kabul edilirse dizinin hash'i donar (`29e`). Yalnız `exit-request.json`
değiştiren push **çıkış ya da parti isteğidir** (`29e`). Yalnız `founder-ledger.jsonl` ve/veya `reports/`
değiştiren push **defter push'udur** (`ledger`): değerlendirilmez, rakip çağrılmaz, seriye ve
`rival_artifacts`'a girmez; zincir ve yalnız-ekleme denetimi yine koşar. Yalnız tohum yollarını
(`spec/tohum/**`, `seed/**`) değiştiren ve ağaçları son tohum dönemine eşit olan push `seed_update`'tir:
değerlendirilmez, rakip ve seri yok, sonuçta kayıt. Diğer her push **kod isteğidir**, `spec/asama-0`
donmadan kabul edilmez. Değişikliksiz push değerlendirilmez; spec ile kodu karıştıran, başka bir tohum yolu
değişikliği (`seed_modified`), başka `spec/` yolu ya da kökteki `.github/`'ı değiştiren, herhangi bir yerde
(büyük-küçük harf duyarsız) ajan yapılandırması taşıyan (`agent_config_modified`, `24a`) ve geçmişi
yeniden yazan push reddedilir.
```

### 29b:44–53 → 11 satır

Rakip: `reports/` gizli; kota = abonelik penceresi (429), kesinti ve uyarı, ret değil (K5). Eski ilk satır: "**Rakip çağrısı.** İç kullanımda API anahtarı yoktur (satışt…"

```text
**Rakip çağrısı.** İç kullanımda API anahtarı yoktur (satışta anahtara geçilir): rakip, operatörün
`CLAUDE_CODE_OAUTH_TOKEN`'ıyla koşan, `requirements/claude-cli/`'de sha512'yle pinli `claude` CLI'sidir;
yerleşik araç, ayar kaynağı, slash komutu ve oturum kaydı yoktur, tavan `--max-budget-usd`'dir. Artefaktı
(son kabul edilmiş SHA'dan bu yana tam diff) ve ilgili tohum sayfalarını görür, commit ağacını tek MCP
sunucusu `rival_mcp.py`'nin `read_file`, `grep`, `glob`'uyla salt okur, kararı `submit_verdict` ile verir
(`init` olayından kanıtlanır); `founder-ledger.jsonl` ve `reports/` diff'ten ve ağaçtan çıkarılır.
Sunulan model farklıysa, ret, tavan ya da tur sonu ve biçimsiz karar kabul değil `unresolved`'dır; yedek
model yoktur. Kimlik, kota (abonelik kullanım penceresi, HTTP 429), ağ, zaman aşımı ve 5xx kesintidir
(`api_error`), ret sayılmaz ve operatörü uyarır: aynı SHA üçüncüden sonra günde bir, en çok 7 gün
denenir, sonra görünür durur. 400/404/413/422 `request_rejected`'dır: değerlendirilmiş sayılır,
Kurucu'ya yazılmaz, operatörü uyarır. İzolasyon hatası operatör için durdurur.
```

### 29b:55–58 → 6 satır

Kabul: aşama tablosu, sahipli gruplar, modülsüz kırmızı, tohum denetimleri. Eski ilk satır: "**Kabul.** Kod SHA'sı: Aşama 0 testleri yeşil; vektörler geç…"

```text
**Kabul.** Kod SHA'sı: geçerli aşama tablosunda bitmiş her MF'nin testleri bildirimde ve yeşil; sahibi
bitmiş vektör grupları geçer ve değiştirilmiş girdiyi reddeder; bu push'la biten MF modülsüz kırmızıdır;
tohum denetimleri temiz; kırmızı kontroller doğru; rakip geçerli karar verdi; ne yeni bir çürütme ne
durumda tutulan kanıtlanmış kusur yeniden üretildi (`refutation_still_reproduces`, `29`). Testler
kırmızıysa rakip çağrılmaz. **Ret artefaktı** tiplidir: `{sha, kind, reasons: [{kind, test_id?, ref,
detail_sha256, detail?}]}`.
```

### 29b:60–65 → 7 satır

Ret hafızası: modülsüz yeşil sayılır; fren ve 429 serilere dokunmaz; `founder_resume`. Eski ilk satır: "**Ret hafızası.** Kurucu'nun düzeltebildiği her ret (test, v…"

```text
**Ret hafızası.** Kurucu'nun düzeltebildiği her ret (test, vektör, modülsüz yeşil, lisans, yeniden
üretilmiş çürütme, `prompt_too_large`, `max_turns`) nedenlerinin imzasıyla (`tür:test`, `tür:ref`;
çürütmede komut ve beklentinin hash'i) sayılır; kabul seriyi sıfırlar. Rakibin hataları (`model_mismatch`,
`malformed_verdict`, `no_verdict`, `refusal`, `rival_missing`), fren, abonelik penceresi ve altyapı arızası
serilere dokunmaz; rakip hata serisi operatörü uyarır. Sonuç `learning {repeated, not_learning,
repeat_events}` taşır; aynı imza ardışık `stage_params.repeat_reject_limit` rete ulaşınca `not_learning`
olur ve Kurucu oturumu durur (`22a`); devam `founder_resume` iledir (`24a`).
```

### 29b:67–74 → sil

**Çıkış isteği** paragrafı ("30 mikro özellik", `spec.lint`, `gate.lock`) ve ardındaki boş satır silinir; yeni hâli `29e`'de. Eski ilk satır: "**Çıkış isteği, Aşama 0 çıkışının (A) parçası.** `exit-reque…"

### 29b:75–80 → 8 satır

Asla yapmadıkları: bütçe kaçak frenidir (K5); oturum ve USD ölçümdür. Eski ilk satır: "**Asla yapmadıkları.** Hedefe, beyin ve hakem reposuna yazma…"

```text
**Asla yapmadıkları.** Hedefe, beyin ve hakem reposuna yazmaz; merge etmez; Kurucu'nun kodunu sırlı işte
koşturmaz; Actions önbelleği kullanmaz; kill switch açıksa iş başlatmaz. **Bütçe kaçak frenidir**
(`asama-0/12`): rakip freni dolunca yoklama uyarıyla geçer, commit tüketilmez; aynı baş ay dönünce ya da
politika değişince kendiliğinden yargılanır. Fren ret değildir; Kurucu'nun oturum sayısı ve USD'si
ölçümdür, kabulü etkilemez. Gözcü P1'le gelir; fren buradadır; `monthly_cap_ci_minutes` ölçülmez (fren
GitHub harcama sınırıdır, `25` 8). Politikadan okudukları: `monthly_cap_usd`,
`stage_budgets.asama_0.rival_usd`, `stage_params.{rival_min_attempts, repeat_reject_limit}`,
`license_allowlist`, `license_exceptions`.
```

## 3. Yeni sayfa `spec/tohum/29e-onyukleme-hakemi-devam.md` (tam metin)

INDEX: yeni satır `tohum/29e-onyukleme-hakemi-devam.md` | "Önyükleme Hakemi, Devam: Durum, Aşama Tablosu, Tohum
Denetimleri, Çıkış" | "kurulumda, her tohum döneminde ve her aşama ya da parti çıkışında". `29b` satırı: başlık
"Önyükleme Hakemi: Beyin Reposunun İtme Yargıcı", okunma "kurulumda, Aşama 0 boyunca ve sonra her push
yargısında".

````markdown
# Önyükleme Hakemi, Devam: Durum, Aşama Tablosu, Tohum Denetimleri, Çıkış

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: kurulumda, her tohum döneminde ve her aşama ya da parti çıkışında
Çapa: `seed/bootstrap/stages/`; imzalı `bootstrap-state`; hakem reposundaki `setup/stage.json`

---

`29b`'nin devamıdır; aynı kurallar geçerlidir.

**Durum.** Bellek, önceki koşunun imzalı `bootstrap-state` artefaktıdır (`result.json` ve Sigstore
paketi); her koşu onu kimlik doğrulamasıyla açar, doğrulanamaz ya da yoksa durur. Başlangıç durumunu (ilk
kabul edilmiş SHA son tohum döneminin commit'i) yalnız operatörün ilk koşu işareti kurar; işaret varken
yargılanacak bir şey olmasa da başlangıç durumu imzalanır (`25` 11); kurtarma `25`'tedir. Sonuç önceki
sonucun hash'ini taşır, koşu yalnız en yeni durumu okuduysa yazar (karşılaştır-ve-yaz). Boşta 7 günde bir,
kill switch'ten bağımsız bir adım durumu aynen yeniden yükler.

**Tohum dönemi.** `pull` beynin `spec/tohum/**` ve `seed/**` ağaçlarını `base`'e değil özetin son
`seed_epochs[]` satırına karşı karşılaştırır (`25` 10b, `26c`): yalnız tohum yolları değişmiş ve ağaçlar
döneme eşitse push `seed_update`'tir, değilse `seed_modified`. Tohumdan doğan nedenler Kurucu'nun değildir.

**Spec istekleri.** Yalnız sıradaki aşamanın dizini donabilir; donmuş dizine dokunan istek
`spec_already_frozen`'dır, açılması operatör kararıdır. Tohumdaki Aşama 0 spec'i düzeltme istemiyorsa
Kurucu incelemesini `spec/asama-0/CHANGELOG.md`'ye tarihli satır olarak ekleyip iter (`02` 1).

**Aşama ve parti tabloları.** `stages/stage0.json` `asama-0/14`'ün makine kopyasıdır (`26c`); partilerin
tabloları aynı dizindedir (`asama-1/13`). Hakem `done_mf`'in anlamını, bildirimde olması gereken testleri,
vektör gruplarının sahibini, modül yollarını ve `calls` sırasını buradan okur; çağıran MF çağrılandan
önce geliyorsa tabloyu yüklemez ve durur. Geçerli aşama `setup/stage.json`'dan okunur; dosya yoksa Aşama
0'dır. Aşama 1 tablosu ve `stage: 1` testleri yalnız `stage-open`'ın yazdığı `setup/stage.json`'dan sonra
geçerlidir (`asama-0/10a`); ayrı bir `lock.check` yoktur.

**Modülsüz kırmızı.** Bir push MF k'yı `done_mf`'e eklediğinde k'nın testleri tablodaki modül yolu silinmiş
ağaçta yeniden koşar; yeşil kalırsa ret `module_less_green:MFk`. Çıkışta tablodaki her MF için.

**Tohum denetimleri** (Kurucu'nun testi değil; `çek`te, beyin arşivinden okunur, kapsayıcıda koşmaz):
- `wiring`: `referee/.github/workflows/*.yml` sınırlı bir YAML altkümesiyle okunur, altkümenin dışındaki
  dosya `workflow_unparseable`'dır; kurallar `asama-0/09` test 46'nınkilerdir.
- Kurucu defteri: `founder-ledger.jsonl` tohumun kanonik koduyla zincirli ve son kabul edilmiş SHA'dakine
  göre yalnız eklenmiş; aksi `founder_ledger_invalid`.
- Genellik ve ağaç: `referee/` metninde `targets[].identifiers`'tan ad yok; `referee/` operatör adlarını ve
  ajan yapılandırmasını büyük-küçük harf duyarsız taşımaz.
- Spec: `02`'nin mekanik maddeleri (bölümler, eşiklerin anahtarı, `#kimlik` satırları, hedefe özgü ad,
  yeni dosyaların `27` ve `27a`'daki okuyucusu) donacak aşama dizininde.

**Bildirimler.** `reports/*.json` (`26c`) her `pull`'da okunur, rakipten gizlenir, imzalı sonuçta
`reports[]` ve adım özetinde olur, operatörü uyarır. Bir vektörü adlandıran `seed_issue` onu `disputed`
yapar: koşmaya devam eder, kapılamaz; en çok iki açık itiraz. Operatör tohum dönemiyle karar verir.

**Çıkış ve parti isteği.** `exit-request.json` son kabul edilmiş SHA'yı ve donmuş aşama dizininin hash'ini
(parti isteğinde `batch`'ı) adlandırır. Hakem `asama-0/10`'un (A) koşullarını kendi koduyla denetler:
tablodaki bütün MF'ler bitmiş ve modülsüz kırmızı; testler, vektörler ve kırmızı kontroller; tohum
denetimleri; rakip sayımı (çıkış SHA'sı ve ondan ayrı en az `stage_params.rival_min_attempts` artefakt
rakipten sağ çıkmış; defter ve tohum push'ları sayılmaz; aynı başın yeniden denemesi saklı rakip sonucunu
kullanır; durumdaki kanıtlanmış kusurlar artık üretmiyor; açık iddialar listede); kilit çifti (aşama ve
durumdaki donmuş spec hash'i); dürüstlük; `repeat_events`. Sonuç "aktarılabilir"dir; `referee/` ağaç
hash'ini, `toy_tree_sha256`'yı ve `repeat_events`'i taşır (`25a` 1). Reddedilmiş bir istekle bayt bayt
aynı `exit-request.json` sonraki kod push'larında yok sayılır. (A)'dan sonra `referee/`'ye dokunan push
`referee_changed_after_exit`'tir; yalnız `candidates/` ve `targets/` değişebilir.

**Dürüstlük provası** (`asama-0/10`). `honesty_commitment` kurulumda özete yazılır (`25` 10c); çıkışta
operatör `setup/honesty-key.json`'u ekler (dokunuş). Hakem anahtarın hash'ini taahhütle karşılaştırır ve
tespit yüklemlerini değerlendirilmiş bütün SHA'larda koşar: istismar 0 olmalıdır. Kurucu aleyhine çıkan
itiraz Kurucu'nun ret imzası olur; bildirim isabeti ve teyit raporlanır, kapılamaz.
````

## 4. Uygulandıktan sonra

- `25`'in "**Durum kaybolursa** (`29b`)" atfı `29e` yapılabilir (durum paragrafı oraya taşındı).
- `seed/` testleri bu iki sayfanın metnine bağlı değildir; `test_wiring` `25`'i okur, bu sayfaları değil.
- Dayanaklar: K1 (itme yargıcı kalır), K4 (dürüstlük), K5 (fren ve 429), E88 (tohum dönemi), E89 (`ledger`),
  E90 (ajan yapılandırması), E92 (ilk koşu), E93 (`reports/`), E97 (aynı istek), E100 (`wiring`), E103
  (modülsüz kırmızı, gruplar), E107 (Kurucu defteri), E120 (`status-stage0.md`), E121 (kırmızı bitiş).
