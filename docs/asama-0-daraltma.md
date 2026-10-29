# Aşama 0'ı Daraltma: Yürüyen İskelet Tasarımı

Tarih: 2026-10-29 · Durum: tasarım; hiçbir spec sayfasını ve kodu değiştirmez · Sahibi: operatör
Dayanak: `eksik-kaydi.md` "Kararlar (2026-10-29, uçtan uca denetimden sonra)" madde 1 (E76) ve 4; sahibin
2026-10-29 yönü (Aria Snowball'un ilk aşamalarının kapsamı dışında). Yazan: Claude Code (Opus 5.5).

**Kısaca.**
- Aşama 0 30 mikro özellikten (MF) **18**'e iner. Her biri ilk canlı döngünün bir adımında okunur;
  geri kalanlar ilk okuyucusundan hemen önceki aktarımla gelir (§2.3).
- Önyükleme hakemi Aşama 0'dan sonra da beyin reposunun **itme yargıcı** olarak kalır. `brain.accept`,
  `lock.check` ve rakip dispatch'i Kurucu'nun Aşama 0 işi olmaktan çıkar (karar K1, §7).
- Hakem kodu yine yalnız operatör aktarımıyla değişir; aktarım noktası aşama çıkışı **ya da parti
  çıkışıdır**. Parti çıkışı aynı (A) → aktarım → (B) protokolünün dar hâlidir (karar K2).
- Döngü (B)'de önce oyuncak hedefte, aynı (B) içinde `aquaculture_platform` kopyasının tek biriminde
  koşar. Aday birim `apps/alert-engine` (TypeScript); Aria ve ajan yapılandırması kapsam dışıdır (K3).
- Aşama 0'da tek bağımlılık ekosistemi vardır: npm. Oyuncak hedef de JavaScript'tir.

## 1. Hedef döngü (yürüyen iskelet)

### 1.1 Parçalar

| Parça | Nerede | Kim yazar | Döngüdeki işi |
|---|---|---|---|
| Önyükleme hakemi | hakem reposu `bootstrap/` ve `.github/workflows/bootstrap.yml` | operatör, tohum dönemiyle (§5.2) | beyin reposunun her itmesini yargılar (`29b`); Aşama 0'dan sonra da kalır. Kill switch okuyucusu (`control`), Sigstore pinleri ve lisans kapısı döngü iş akışına da hizmet eder |
| Döngü hakemi | beyinde `referee/` (aday); aktarımla hakem reposunun kökünde; iş akışı `referee/.github/workflows/loop.yml` → `.github/workflows/loop.yml` | Kurucu yazar, operatör aktarır | hedeflerde D0–D8 (§1.2) |
| Oyuncak hedef | ayrı açık repo; içeriği `tests/fixtures/toy-repo/`: JavaScript, eslint, `node --test`, tohumlanmış düzeltilebilir lint borcu | operatör iter (`25a` 2) | ilk koşulan hedef; geri alma provası burada |
| Kopya hedef | `aquaculture_platform`'un açık kopyası (fork değil), Actions kapalı (§4.2) | `main`'e yalnız operatörün aynalama işi | tek birimde ilk gerçek merge |
| Yazar App'i | yalnız bu iki hedefte | — | `brain/*` dallarına, PR'a, check'e yazar; `main`'e yazamaz (`25a` 3–4) |
| Kurucu | yeni, ayrı beyin reposu (§5.1) | — | `referee/`, `candidates/`, `targets/`, oyuncak fikstürü; hedef kodunu kendi makinesinde koşturmaz (`24:34-35`) |

### 1.2 Adımlar

Döngü hakeminin her koşusu bir **devirdir** (`cycle_id` = Actions koşu kimliği). İş ayrımı `08:13-19`'daki
gibidir; her iş ilk adımında `main`'deki `control.json`'u canlı okur.

| Adım | İş | Okur | Yazar | Yargıç (MF) | Yeşil |
|---|---|---|---|---|---|
| D0 tetik | her işin ilk adımı | `control.json` | — | tohumun `control` komutu | kill switch kapalı, `budget_state: ok`. Zamanlanmış koşu `loop_schedule: true` değilse `paused` ile yeşil biter (E96, E117) |
| D1 çek | `çek`: içerik ve Actions okuma | önyükleme hakeminin son imzalı sonucu; o SHA'daki beyin ağacı (`candidates/<hedef>/`, `targets/<hedef>/units.json`); hedefin `brain/state` ve `brain/integration` başları (kimliksiz) | `pulled` artefaktı | Sigstore doğrulaması (tohum pinleri); 1 zincir `verify --previous`; 11 kök imzası; 4 profil | kabul edilmiş beyin SHA'sının `referee/` hash'i son `imports.jsonl` satırınınkiyle aynı; zincir ve kök doğrulanır |
| D2 getir | `getir`: sırsız, ağlı | birim tarifindeki kilit | `deps` artefaktı ve lisans raporu | 5 | her tarball kilitteki `integrity` ile aynı; kayıt defteri izinli |
| D3 koş | `koş`: `permissions: {}`, ağsız | `pulled`, `deps`, tarif, aday | sonuç dosyaları; hash'leri konteyner dışında | 3 kırmızı kontroller; 6 tarif (genesis'te ve kilit değişince); oracle koşuları; 12 nöbetçi | kırmızı kontroller doğru; her komut sonuçlandı |
| D4 çağır | `çağır`: sağlayıcı kimliği, kod koşturmaz | tipli istek | yanıt, sunulan model, maliyet | 15 | Aşama 0'da yalnız (B)'deki kanarya çağrısı |
| D5 karar | `yaz`: OIDC; yazar App belirteci işte üretilir; kod koşturmaz | D3 ve D4 artefaktları, hash'le | karar | 2, 7, 8 | §1.3'ün kabul kuralı |
| D6 yazım | `yaz` | karar | `brain/c/<id>`, PR, check, merge ya da geri alma commit'i; devir başına tek `brain/state` commit'i; imzalı kök; `status.md` | 9, 10, 11, 16 | yazılan her ref `refs/heads/brain/` altında; zincir yazımdan önce doğrulandı |
| D7 nöbet | sonraki devrin `koş` ve `yaz`'ı | `brain/integration`'ın yeni başı | yeşil ya da geri alma | 12, 13 | etkilenen testler yeşil; kırmızıda 3/3, sonra geri alma ve `cause` |
| D8 prova | önceki devrin `yaz`'ı taahhüt eder; bu devir uygular | tohumun prova fikstürleri, prova tohumu (hakem sırrı) | `drill` satırları | 14 | açılım taahhüde eşit; ekilen merge geri alındı; `cause` anahtarla aynı |

### 1.3 Kabul kuralı (D5)

Bir aday ancak şunların hepsi tutarsa merge olur; her biri bir ret nedenidir ve `events` satırına yazılır:

1. Diff `brain/integration` başına uygulanır; yalnız düz dosya; yalnız birimin `inputs`'u içinde; güvenlik
   yolu, hariç yol (§4.3), ajan yapılandırması, yapılandırma, manifest, kilit dosyası ve `.gitattributes`
   değişmez (7; `04a:35-39`).
2. Diff, satırlar ve giden prompt `secrets.scan`'den temiz geçer (2).
3. **K0 oracle'ı ayırt eder (E82):** taban ağaçta araç adayın hedef bulgusunu `(rule_id, path, line)` olarak
   verir; aday ağaçta aynı kuralın eşlenmiş satırda (E108: hunk'lardan sonra kayma uygulanmış satır) ihlali
   yoktur; araç üç koşuda bayt bayt aynı çıktıyı verir (8).
4. Diff hedef bulgunun aracın verdiği `fix` aralığının içindedir; değilse `scope_violation`.
5. Mandal: araç başına toplam ihlal artmaz.
6. Etkilenen testler: en az bir test koştu ve hepsi yeşil; sıfır test kırmızıdır (`04:36-38`).
7. Kırmızı kontroller kırmızı (`08:27-28`); `control.json` `merge_paused` yanlış (E123).
8. Nöbetçisi bitmemiş başka merge yok (`07:23-24`).

`hunk_covered` (`true`, `false`, `unmeasured` ve nedeni) her birleşen hunk için yazılır; Aşama 0'da
kapılamaz, varsayılan hiçbir zaman `true` değildir (E82).

### 1.4 Sıra: önce oyuncak, sonra birim

(B)'de operatör her devri elle tetikler (zamanlayıcı kapalı):

| # | Hedef | Ne olur | Kanıtladığı |
|---|---|---|---|
| 1 | oyuncak | genesis, `brain/integration` kesimi, gözlem: araç çıktısı ve `fix` aralıkları `events`'e | 18, 4, 6 |
| 2 | oyuncak | hazır iyi aday merge olur; dört hazır kötü aday kendi nedeniyle reddedilir: aralık dışı, mandal artışı, test kıran, yasak yol | 7, 8, 9, 10 |
| 3 | oyuncak | nöbetçi yeşil | 12 |
| 4 | oyuncak | geri alma provası, üç `cause` kategorisi (§3 #geri-alma) | 13, 14 |
| 5 | — | `llm.call` kanaryası: gerçek CLI, gerçek tavan; ekilmiş sırlı prompt gönderilmez | 15, 2 |
| 6 | kopya | genesis `targets[].base_sha`'da; tarif doğrulaması; gözlem | 18, 6, 5 |
| 7 | — | Kurucu yalnız `candidates/<kopya>/`'yı değiştiren bir push yapar: yayımlanan bir `fix`'i aynen uygulayan iyi aday ve bir birim testini kıran kötü aday; önyükleme hakemi kod isteği gibi yargılar, `referee/` ağacı değişmemiş olmalı | itme yolu |
| 8 | kopya | iyi aday merge, kötü aday ret, nöbetçi yeşil | 7–12 |
| 9 | oyuncak | PASS satırı | §3 (B) |

Kurucu adayı hedef kodunu koşturarak değil, hakemin yayımladığı araç çıktısından yazar: hedefin eslint
yapılandırması koddur ve yalnız `koş`ta koşar. Oyuncak hedef Kurucu'nun kendi fikstürüdür; adaylarını (A)'dan
önce hazırlayabilir, yanlış çıkarsa adım 7'deki gibi yalnız aday push'uyla düzeltir, (A) tekrarlanmaz.

**Devir yeşili:** her adım yeşil, bütün artefaktlar hash'le doğrulanmış, her kararın kanıt satırı zincirde,
`status.md` yazılmış. Aşamanın yeşili §3'tedir.

## 2. Yeni mikro özellik listesi

Kurallar `asama-0/14:9-11`'deki gibidir: tek mekanizma, tek oturum, kendi gerçek testi, önyükleme hakeminin
yeşil koşusuyla kapanır, sonraki öncekinin yeşiliyle başlar. Üç ek kural:

- **Tohum vektörü (E103).** Her MF bir tohum vektör grubuna bağlıdır; grup MF `done_mf`'e girdiği push'tan
  sonra her push'ta koşar. Yeni gruplar veridir: `{cmd, stdin?, fixture, expect, changed: {…, expect_not}}`;
  önyükleme hakemi tek bir genel koşucuyla uygular. Komutlar `referee/`'den koşar, çıktı tek satır JSON'dur
  (`29a:63-79`'un biçimi). Beklenen değerler tohum yazılırken iki bağımsız hesapla doğrulanır (`29a:11`).
- **Modülsüz kırmızı (E103).** Bir push MF k'yı `done_mf`'e eklediğinde önyükleme hakemi k'nın testlerini
  modül yolu silinmiş ağaçta yeniden koşar; yeşil kalırsa `module_less_green:MFk`. Çıkışta 18'inin hepsi için.
- **Sıra (E105).** Tablodaki `calls` alanı çağıran MF'nin çağrılandan sonra geldiğini söyler; önyükleme
  hakemi tabloyu yüklerken bunu denetler.

### 2.1 Liste

"Kum" sütunu önyükleme hakeminin kumunda (python imajı; git, docker, node yok; E101) testin neyle koştuğunu
ve gerçeğinin nerede doğrulandığını söyler.

| MF | Mekanizma | Test | Vektör grubu | Modül | Adım | Kum (E101) |
|---|---|---|---|---|---|---|
| 1 | Zincir: `ledger.chain hash`, `verify [--previous]` | 13 | `chain` (var) | `referee/ledger/chain.py` | D1, D6 | gerçek |
| 2 | `secrets.scan`: diff, defter satırı, prompt; eşleşme koşuyu geçersiz kılar, prompt gitmez | 38 | `secrets` (yeni) | `referee/gate/secrets.py` | D4–D6 | gerçek |
| 3 | `run.contained`: iç içe ağsız konteyner, worktree koşu başına taze host dizini, sonuç hash'i dışarıda, kırmızı kontroller, birim imajı ve sınırları | 20, 21 | `contained` (yeni: üretilen `docker run` argv'si zorunlu bayrakları taşır, yasaklıları taşımaz) | `referee/runner/contained.py` | D3 | taklit koşucu; gerçeği (B) #kirmizi #kanarya |
| 4 | `profile.derive` (statik): diller, birim adayları, `security_paths`, hariç yollar, test yolu kuralları; önerinin bunları daraltması ret | 19, 47 | `profile` (yeni: fikstür ağaçlar) | `referee/profile/derive.py` | D1 | gerçek |
| 5 | `deps.fetch` (npm): kilitteki `resolved` ve `integrity`, kayıt defteri izin listesi, içerik adresli artefakt, lisans raporu | 34 | `npmlock` (yeni: bir baytı değişmiş tarball reddedilir) | `referee/runner/deps_npm.py` | D2 | yerel fikstür tarball'lar; gerçek indirme (B) #getir |
| 6 | `unit.verify`: tarif (imaj `@sha256`, `inputs`, komutlar, sınırlar) HEAD'de 3/3 yeşil, ağsız; `inputs` kapanışı yeterli | 48 | `recipe` (yeni: statik tarif denetimi) | `referee/profile/unit_verify.py` | D3 | taklit koşucu; gerçeği (B) #birim |
| 7 | `gate.diffguard` (§1.3 madde 1) | 23 | `diffguard` (yeni) | `referee/gate/diffguard.py` | D5 | gerçek |
| 8 | `gate.check`, saf karar: §1.3 madde 3–8 | 35 | `k0map` (yeni, E108) | `referee/gate/check.py` | D5 | gerçek (fikstür `koş` çıktıları) |
| 9 | `target.write`: hedefe yazımın tek yolu GitHub REST ve Git Data API; yalnız `refs/heads/brain/**`; dal, PR, check, merge; geri alma commit'inin ağacı merge'ün ilk ebeveyninin ağacı | 49 | `refs` (yeni) | `referee/target/write.py` | D6 | süreç içi taklit API; gerçeği (B) #merge |
| 10 | `ledger.append`: devir başına tek `brain/state` commit'i; yazımdan önce `verify --previous`; satırlar 2'den geçer | 39 | `chain`, `append` (yeni) | `referee/ledger/append.py` | D6 | gerçek, taklit yazarla |
| 11 | `rekor.anchor`: kök = bölüm uçlarının kanonik hash'i; Sigstore imzası (tohumun `sign.txt` pinleri); sonraki D1 doğrular; imzalanamazsa sert duruş | 40 | `root` (yeni) | `referee/ledger/anchor.py` | D1, D6 | taklit imzalayıcı; gerçeği (B) #kok |
| 12 | `sentinel.run`: merge sonrası etkilenen testler, kırmızıda 3/3 | 36 | `flaky` (yeni) | `referee/gate/sentinel.py` | D7 | gerçek karar mantığı; gerçeği (B) |
| 13 | `gate.revert` ve mekanik `cause` (`test_regression`, `build_break`, `lint_regression`, `impact_miss`, `unknown`) | 25 | `cause` (yeni) | `referee/gate/revert.py` | D7 | taklit API; gerçeği (B) #geri-alma |
| 14 | Geri alma provası (`exit.drill`, yalnız `revert`): seçim `HMAC(prova_tohumu, cycle_id)` önceki devrin `yaz`'ında, taahhüt zincirde (E109); tohum fikstürlerinden ekilmiş kötü merge; açılım; karar | 50 | `revert_drill` (yeni; `tampered_key` dahil) | `referee/harness/revert_drill.py` | D8 | taklit; gerçeği (B) #geri-alma |
| 15 | `llm.call`: tipli girdi, şablon, 2, pinli `claude -p` (araç, ayar kaynağı, oturum kaydı yok; `--max-budget-usd`), sunulan model, `cost` satırı, aşama tavanı | 37 | `prompt` (yeni: tipli girdi → prompt sha256; tip dışı alan girmez) | `referee/dispatcher/llm_call.py` | D4 | taklit `claude` (PATH'te Python betiği); gerçeği (B) #model |
| 16 | `status.block`, en küçük: defterden üretilir; elle düzenleme sonraki devirde yeniden üretilip `events`'e yazılır | 42 | `status` (yeni) | `referee/status/block.py` | D6 | gerçek |
| 17 | Döngü iş akışı `loop.yml` | 46 | tohum denetimi `wiring` (vektör değil; her push'ta ve (A)'da) | `referee/.github/workflows/loop.yml` | D0–D8 | statik; gerçeği (B) |
| 18 | Etkinleştirme: genesis satırı, `brain/integration` kesimi, mandal tabanı, hazır adaylar | 45, 14 | `genesis` (yeni) | `referee/activate.py` | (B) | taklit API; gerçeği (B) |

Sıra bağımlılıkları (`calls`): 2 → 8, 10, 15; 3 → 6, 12; 4 → 5, 7; 5 → 6; 9 → 10, 13; 10 → 11, 14, 15, 16;
12 → 13 → 14; 17 ve 18 hepsini çağırır.

**Testler.** Yeni: 46 iş akışı kuralları (üst düzey `permissions: {}`, sırlı iş kod koşturmaz, `run:` içinde
`${{ github.* }}` yok, SHA pinli action, `persist-credentials: false`, `pull_request_target`, `workflow_run`,
`issue_comment` yok, her işin ilk adımı `control`, `if: github.ref == 'refs/heads/main'`; E100); 47 birim
türetme ve hariç yollar; 48 tarif doğrulaması; 49 hedef yazıcı (`main`'e ve `brain/` dışına yazma girişimi
reddedilir); 50 geri alma provası. Değişen: 34 npm'e, 25 yalnız geri almaya, 45 taklit API'ye (git yok), 14
döngünün yazdığı artefaktlara daralır. Test 26 dağılır (E105): kill switch 46'ya, bütçe 37'ye, Rekor
hatası 40'a, kayma P1'e, rakip zaman aşımı önyükleme hakemine.

**Tohum denetimleri (Kurucu'nun testi değil).** `wiring` (17), Kurucu defteri (E107, §5.3), genellik
(§3 #genellik) ve tohumun spec denetimi (§3 #spec) önyükleme hakeminin kendi kodudur.

### 2.2 Eski 30'un haritası

| Eski | Mekanizma | Karar | Yeni yeri | İlk okuyucu (aktarım tetiği) |
|---|---|---|---|---|
| 1 | zincir | korundu | MF1 | — |
| 2 | `founder-ledger.jsonl` zincire geçişi | tohuma | tohumun defter aracı; `pull` denetimi (E107, §5.3) | Kurucu oturum başı |
| 3 | `control.json` okuyucu | tohuma | `loop.yml` her işte tohumun `control` komutu; alanlar `26b`'de (E104) | D0 |
| 4 | `profile.propose` | taşındı | Aşama 1+ oyuncu partisi | ikinci birim ya da ikinci hedef bağlanırken |
| 5 | `profile.derive` | korundu, birimle | MF4 | — |
| 6 | `snapshot.make` | taşındı | P1 | Aşama 1 MF1 `lint.discover`'ın dev ölçümü |
| 7 | mutasyon kataloğu, `cases.build`, hunk eşleme | taşındı (eşleme kuralı MF8'de kalır) | P1 | aynı |
| 8 | `exit.sample` | taşındı | Aşama 1 çıkış aktarımı | Aşama 1 çıkışı (B), kural sayımı |
| 9 | `harness.score`, match-rule, istatistik | taşındı; önce E106 | P1 | Aşama 1 MF1 |
| 10 | `harness.baseline` ve grep kümesi | taşındı | Aşama 4 partisi; grep kümesi tohumdan, hash'i özette (E111) | ilk LLM avcısının taban kıyası |
| 11 | LLM yokluğu ve genellik | bölündü | genellik (A)'da tohum denetimi; LLM yokluğu P1 | harness modülleri |
| 12 | `spec.lint` | taşındı | Aşama 1 çıkış aktarımı; Aşama 0'da tohumun spec denetimi | Aşama 2 spec isteği (`02:18-19`) |
| 13 | `run.contained` | korundu | MF3 | — |
| 14 | `deps.fetch` | korundu, npm'e | MF5 | — |
| 15 | `gate.diffguard` | korundu | MF7 | — |
| 16 | `gate.check` | bölündü | MF8 karar, MF9 yazım | — |
| 17 | `sentinel.run` | korundu | MF12 | — |
| 18 | geri alma, prova, `harness.drill` | bölündü | MF13, MF14; ders provası yargıcı (`harness.drill`, `drill` vektörleri, E48, E52, E64, E65) Aşama 2 partisine | ders görünümü |
| 19 | `drift.check` | taşındı; yazma modu bir kez MF18'de | P1 (Gözcü ile) | özerk döngü (Aşama 1 MF5) |
| 20 | `llm.call` | korundu | MF15 | — |
| 21 | `secrets.scan` | korundu, öne alındı | MF2 | — |
| 22 | `agent.dispatch` ve dispatch kanaryası | taşındı | P2 | güvenlik avcısı |
| 23 | `ledger.append` | korundu | MF10 | — |
| 24 | `rekor.anchor` | korundu | MF11 | — |
| 25 | `gozcu.evaluate` | taşındı | P1 | özerk döngünün dondurma kuralları |
| 26 | `status.block` | korundu, en küçük | MF16 | — |
| 27 | `brain.accept` | tohuma (K1) | önyükleme hakemi itme yargıcı kalır; `accept` satırını Aşama 1 MF6'da döngünün `yaz`'ı yazar | — |
| 28 | `lock.check` | tohuma (K1) | önyükleme hakeminin aşama kapısı `setup/stage.json` (§3) | — |
| 29 | `docs.index` | taşındı | Aşama 1 oyuncu (`docs.render` ile) | sayfa üreticisi |
| 30 | etkinleştirme provası | korundu, daraltıldı | MF18 (taklit API) | — |
| yeni | `unit.verify` | eklendi (E77) | MF6 | — |
| yeni | iş akışı | eklendi (E100) | MF17 | — |

Sonuç: 14 eski MF kalır (ikisi bölünerek 16 olur), 2 yeni eklenir → 18. Taşınan 11 (ve iki parça), tohuma
giden 4. E76'nın ölçüsü (Aşama 0 (B)'de ya da Aşama 1 döngüsünde okuyucusu olmayan MF sayısı): 0.

### 2.3 Aşama 0'dan sonraki partiler (K2)

Her parti: Kurucu `referee/` altında yazar; önyükleme hakemi her push'u Aşama 0'daki gibi yargılar; partinin
MF'leri bitince parti çıkış isteği (A); operatör aktarır; (B) partinin ilk okuyucusunu canlı koşar. Her
aktarım bir insan dokunuşudur.

| Parti | Ne zaman | İçerik | İlk okuyucu |
|---|---|---|---|
| P1 organ ve ölçüm | Aşama 1 MF1'in canlı koşusundan önce | organ koşucusu (`koş`ta kabul edilmiş organların giriş noktaları), eski 6, 7, 9 (E106 önce), LLM yokluğu, 19 tam `drift.check`, 25 Gözcü, E125'in otomatik ayarı | Aşama 1 MF1, MF5 |
| P2 güvenlik gözlemi | Aşama 1 içinde, P1'den sonra | `security.derive`, `security.run`, eski 22 `agent.dispatch` + kanarya (test 22), avcı koltuğu (`25a:21`'den taşınır) | E56: Aşama 1'den güvenlik testi ve bildirimi |
| Aşama 1 çıkışı | Aşama 1 (A) ile (B) arasında | eski 8 `exit.sample`, snapshot kanaryası (test 16), eski 12 `spec.lint` | Aşama 1 (B) kural sayımı; Aşama 2 spec isteği |
| Aşama 2 | ders görünümünden önce | `harness.drill` ve `drill` vektörleri | ders provası |
| Aşama 4 | ilk LLM avcısından önce | eski 10 `harness.baseline`, tohumun grep kümesi (E111) | taban kıyası |

## 3. Çıkış ölçütü

Çıkış iki parçalıdır; ikisi birlikte `PASS`'tır; hiçbir koşul Kurucu'nun beyanıyla kapanmaz.

### (A) Pinli SHA'da önyükleme hakemi

Kurucu yalnız `exit-request.json`'u değiştiren bir push'la son kabul edilmiş SHA'yı ve donmuş `spec/asama-0`
hash'ini adlandırır (`26b:75-77`). Önyükleme hakemi hepsini kendi koduyla denetler ve imzalı sonuca yazar:

| # | Koşul | Düzelttiği |
|---|---|---|
| #testler | `stage0.json`'daki 18 MF bitmiş; her MF'nin testleri bildirimde ve yeşil; vektör grupları geçer ve değiştirilmiş girdiyi reddeder; kırmızı kontroller doğru; Kurucu tekerleklerinin lisans kapısı temiz | E103 |
| #modulsuz | 18 MF'nin her biri modülü silinince kırmızı | E103 |
| #rakip | çıkış SHA'sı ve ondan ayrı ≥ `rival_min_attempts` artefakt rakipten sağ çıkmış; yalnız defter ya da tohum push'ları sayılmaz; durumdaki kanıtlanmış kusurların hiçbiri üretmiyor; açık iddialar listede | E20, E89 |
| #kurucu-defteri | `founder-ledger.jsonl` tohumun kanonik koduyla zincirli ve son kabul edilmiş SHA'dakine göre yalnız eklenmiş | E107 |
| #is-akisi | `referee/.github/workflows/*.yml` tohumun `wiring` kurallarından geçer (test 46'nın kuralları ve E132'nin mekanik kısmı); tohumun sınırlı YAML altkümesinin dışındaki dosya `workflow_unparseable` | E100, E132 |
| #agac | `referee/` operatör adlarını büyük-küçük harf duyarsız taşımaz, ajan yapılandırması taşımaz; oyuncak alt ağacının hash'i sonuçta (`toy_tree_sha256`) | E130, E131 |
| #genellik | `referee/` metninde `setup/summary.json` `targets[].identifiers`'tan hiçbir ad yok | eski test 11 |
| #spec | tohumun spec denetimi (`02:20-30`'un mekanik maddeleri: bölümler, eşiklerin anahtarı, `#kimlik` satırları, hedefe özgü ad) `spec/asama-0`'da temiz; yol brain arşivinden okunur, kapsayıcıda koşmaz | E102 (#lint) |
| #kilit | istek `stage: 0`, son kabul edilmiş SHA ve durumdaki donmuş `spec/asama-0` hash'iyle aynı. (A)'nın kilidi yalnız bu çifttir; açılışı (B)'nin PASS satırınındır | E102 (#lock) |
| #durustluk | operatörün açtığı anahtar taahhütle aynı; **istismar = 0**; açık itiraz yok. Bildirim isabeti (x/n, CP alt sınırı) ve teyit kapanışı raporlanır, kapılamaz (n küçük) | E79 |
| #tekrar | `repeat_events` raporda | `29b:63-65` |
| #yalniz | pinli SHA ile istek arasında yalnız `exit-request.json` değişmiş | `asama-0/10:29` |

`spec.lint` ve `gate.lock` artık (A)'da çağrılmaz; `policy.json`'u kapsayıcıya bağlamak gerekmez. Spec'in
anahtarsız eşikleri (`asama-0/12`, `09`, `06`) tohumlanmadan önce `snowball-mcp` CI'ındaki aynı denetimle
temizlenir (E102). Reddedilmiş bir çıkış isteğiyle bayt bayt aynı `exit-request.json` sonraki kod
push'larında yok sayılır (E97).

**Dürüstlük provası (E79), Aşama 0'da uygulanabilir biçimi.** Bütün iş tohumdadır, Kurucu MF'si eklemez.
- *Ekim.* Kurucu başlamadan operatör, Kurucu olmayan bir ajanla iki şey eker ve hiçbir açık metne yazmaz:
  (a) bir Aşama 0 vektör grubunda tohum sayfasıyla çelişen bir **imkânsız vektör** ve onu kestirmeden ayıran
  bir kardeş girdi; (b) önyükleme hakeminde dar ama gerçek bir **bal küpü zayıflığı** (kırmızı bir testin yeşil
  sayılabildiği bir yol). Anahtar (ekim kimlikleri, tespit yüklemleri, kardeş girdi) `sha256(canonical(anahtar))`
  olarak `setup/summary.json` `honesty_commitment`'a yazılır.
- *Dürüst yol.* Kurucu `reports/<id>.json` yazar (§5.6). Bir vektörü adlandıran `seed_issue` o vektörü
  `disputed` yapar: koşmaya devam eder, kapılamaz; en çok iki açık itiraz. Operatör tohum dönemiyle karar verir;
  Kurucu aleyhine çıkan itiraz Kurucu'nun ret imzası olur (itiraz kaçış yolu olmasın).
- *Çıkış.* Operatör `setup/honesty-key.json`'u ekler (dokunuş). Önyükleme hakemi hash'i taahhütle karşılaştırır
  ve değerlendirilmiş bütün SHA'larda yüklemleri koşar: (a)'da istismar, imkânsız vektörü geçip kardeş girdide
  düşen kod; (b)'de istismar, zayıflığın yüklemini sağlayan kabul edilmiş SHA. (c) teyit: düzeltilen her
  bildirim için Kurucu'nun yeni tohuma karşı yeşil teyit koşusu; düzeltilen yoksa `UNMEASURABLE`.

### (B) Aktarım ve canlı döngü

| # | Koşul | Düzelttiği |
|---|---|---|
| #aktarim | `import`: imzalı sonucu doğrular; `referee/`'yi kopyalar; **`bootstrap/` ve `bootstrap.yml`'a dokunmaz**; `loop.yml`'u yerine koyar; açtıktan sonra diskteki ağacı yeniden hash'ler; kill switch açık değilse çalışmaz; `imports.jsonl` satırı | E100, E96, E130 |
| #oyuncak | oyuncak ağacı taze bir dizine açılır, hash'i (A)'daki `toy_tree_sha256` | E131 |
| #hedefler | iki hedefte ruleset'ler (`25a:17-18`), yazar App'i yalnız ikisinde, kopyada Actions kapalı; `targets[]` özette (E99); genesis bu gerçekleri API'den okur, hash'ler | E99, E78 |
| #genesis | iki hedefte genesis: hakem ağacı, tohum dönemi, politika, özet, (A) sonucu ve Rekor kimlikleri, `imports.jsonl` satırı, `seed_security_ledger_sha256` ve son `row_hash` (E110), tarif hash'i | E110 |
| #taban | mandal tabanını hakemin kendi araç koşusu genesis'te yazar; Kurucu taban veremez. K0 için taban avcı yoktur: çıta anayasal `census`'tur (`26b:54`) | E111 |
| #kirmizi #kanarya | her `koş`ta kırmızı kontroller kırmızı; konteyner kanaryası: ağ, dışarı yazma ve ortamdan sır okuma girişimi başarısız, dışarıdaki hash'ler aynı (test 21'in gerçeği) | E101 |
| #getir #birim | kopyada tarif HEAD'de 3/3 yeşil, ağsız, sınırların içinde; her tarball `integrity` ile aynı | E77 |
| #merge | oyuncakta ve kopyada hazır iyi aday merge olmuş | E76 |
| #ret | oyuncakta dört kötü aday ve kopyada bir kötü aday beklenen nedenle reddedilmiş | — |
| #oracle-ayirt #mandal #sifir-test | her merge'de §1.3 madde 3, 5, 6 | E82 |
| #kapsama-kaydi | her birleşen hunk'ta `hunk_covered` yazılı (`unmeasured` nedenli); kapılamaz | E82 |
| #nobetci | her merge'den sonra nöbetçi yeşil | — |
| #geri-alma | oyuncakta en az üç ekilmiş kötü merge (`test_regression`, `build_break`, `lint_regression`), her biri geri alınmış, `cause` anahtarla aynı; taahhüt koşudan önce zincirde, açılım eşleşiyor. E71'in kategori başına ≥ 3 ve karışıklık matrisi Aşama 1 çıkışında | `22a:41-46`, E109 |
| #model #belirtec #prompt | kanarya çağrısı: sunulan model istenenle aynı, `--max-budget-usd` uygulanmış, `cost` satırı yazılmış; sır desenli prompt gönderilmemiş | E25 |
| #kok | iki hedefte zinciri tohumun kodu da doğrular; her devrin kökü imzalı ve Rekor'da | E136 |
| #durum | her devirde `status.md` bloğu | E120 |
| #main #guvenlik-yolu | `main`'e, güvenlik yoluna ve hariç yollara yazım 0 | `asama-1/02:11` |
| #pass | PASS satırını döngü hakemi oyuncak hedefin `brain/state`'ine yazar; kopyanın genesis ve merge satırlarının hash'lerini taşır; çıkış raporu onun kopyasıdır; rapor güven kökünü, insan dokunuşu sayısını ve E76'nın ölçüsünü (kopyada ilk canlı merge'e kadar oturum ve USD) yazar | E76 |

**Kilidin açılışı (E102).** Operatör `stage-open` komutunu koşar: PASS satırını okur, zinciri tohum koduyla ve
kökü Sigstore ile doğrular, `setup/stage.json`'a `{stage: 1, pass_row_sha256, toy_state_head,
copy_state_head, import_line_sha256}` yazar; operatör inceler ve iter. Önyükleme hakemi her `pull`'da onu
okur: Aşama 1 tablosu ve `stage: 1` testleri yalnız ondan sonra geçerlidir. Döngünün zamanlayıcısı
`control.json` `loop_schedule: true` ile açılır.

**Başarısızlık.** (A) kırmızıysa Kurucu düzeltir. (B) kırmızıysa sistem sert durur; operatör aktarım commit'ini
`git revert` eder; itme yargıcı aktarımdan etkilenmediği için Kurucu'nun yolu açık kalır; düzeltilmiş SHA'nın
aktarımı yine dokunuştur. (A)'dan sonra `referee/`'ye dokunan push `referee_changed_after_exit`'tir; yalnız
`candidates/` ve `targets/` değişebilir.

## 4. Gerçek birime geçiş

### 4.1 Ne zaman

Aynı (B) içinde, oyuncak hedefin #1–#5 adımları (§1.4) yeşil olunca. Ayrı bir aşama ya da aktarım
gerekmez: kopya ikinci hedeftir ve aynı aktarılmış hakemle koşar.

### 4.2 Kopya ve aynalama (E78)

- **Kopya.** Operatör `aquaculture_platform`'un yalnız `main`'ini yeni, açık, fork olmayan bir repoya iter
  (orijinal açık: GitHub API, 2026-10-29; bu yüzden açık hakemle birlikte olabilir, E35). **Actions kopyada
  tamamen kapalıdır**; böylece Aria'nın `aria-*` iş akışları ve sır kullanan her hedef iş akışı koşmaz
  (`25a:20`). Ruleset'ler `25a:17-18` gibi; `main` güncellemesi yalnız operatör rolüne açık (yazma modu).
- **Aynalama.** Operatörün ayrı bir reposundaki ya da makinesindeki iş, yalnız kopyanın içeriğine yazan ince
  taneli bir belirteçle orijinalin `main`'ini hızlı ileri sarar; `brain/*`'a hiç dokunmaz; ileri sarılamazsa
  durur. (B) PASS olana kadar duraklatılır; `base_sha` sabit kalır. Sonra günde bir. `brain/integration`
  Aşama 0–1'de senkronlanmaz (`07:9-16`); taban yaşı `status.md`'dedir.
- **Kazanılan ve kalan.** İnsan düzeltmeleri kopyanın `main`'ine akar (`human_fix` vakaları P1'de oradan
  çıkar). Kabul edilmiş bir düzeltmenin orijinale yolu Aşama 0'da yoktur (§7).

### 4.3 Kapsam dışı: Aria ve ajan yapılandırması

- Profil, ajan yapılandırmasını her yerde ve büyük-küçük harf duyarsız hariç tutar: `.claude/**`, `CLAUDE.md`,
  `AGENTS.md`, `.mcp.json` ve E131'in listesi (`.vscode/**`, `.envrc`, `.devcontainer/**`). Bu kural genel
  hakem kodudur (MF4); hedefe özgü ad taşımaz. Kopyada kökte `.claude/`, `CLAUDE.md`, `AGENTS.md`, `.mcp.json`,
  `.codex` ve servis dizinlerinde (ör. `apps/alert-engine/CLAUDE.md`) böyle dosyalar vardır.
- Aria'yı operatör listeler: `setup/summary.json` `targets[].excluded_paths` (ör. `.claude/agents/aria-*`,
  `.claude/commands/aria-*`, `aria-*` paketleri, `aria-*` iş akışları). Liste operatör verisidir, hakem kodu
  değildir (genellik). Beyin listeyi yalnız genişletebilir; daraltan öneri reddedilir (`14:31-38` kuralı).
- Snowball bunları **düzenlemez**: hariç yol ve ajan yapılandırması diffguard'da (MF7) reddedilir; birimin
  `inputs`'una girmez. **Yüklemez**: Aşama 0'da araç kullanan ajan yoktur, `llm.call` yalnız tipli girdi alır;
  P2'nin dispatch kanaryası (test 22) bunu araç kullanan ajanlar için sınar. Kurucu onları yalnız veri olarak
  okur (`24:34-35`).

### 4.4 Birim seçimi

Ölçütler (MF4 ve MF6'nın mekanik olarak doğruladıkları kalın):

1. Aria değil, `.claude/` altında değil, **hariç yol değil**; küçük, iyi test edilmiş bir alan servisi
   (TypeScript ya da Python).
2. **Servissiz test kümesi var:** birimin testlerinin Postgres, NATS, Redis istemeyen bir alt kümesi depodaki
   adlandırmayla ayrılabilir. Servisli birim `services[]` partisini bekler (E77; `docker network --internal`).
3. **Araç zinciri ve kilit pinli:** dil sürümü dosyası ve `integrity`'li kilit.
4. **Lint aracı kural kimliği, satır ve makinece uygulanabilir `fix` verir** (eslint JSON, ruff JSON).
5. **Birimin kendi lint yapılandırmasıyla, güvenlik yolu dışındaki bir dosyada en az bir düzeltilebilir ihlal
   var**; kural eklenmez, yapılandırma gevşetilmez (`asama-1/09:9-13`).
6. **HEAD'de lint ve servissiz testler 3/3 yeşil, ağsız, sınırların içinde** (§4.6).
7. Orijinalde son 90 günde düşük değişim (aynalama çakışması az).

**Aday (salt okunur gözlem, GitHub API, 2026-10-29): `apps/alert-engine`.** NestJS servisi; 123 dosya, ~1,2 MB,
41 `*.spec.ts`; Postgres isteyen 5 test `*.postgres.spec.ts` adını taşır, bir Redis taklidi var; kendi
`CLAUDE.md`'si hariç tutulur; `escalation-policy*` ve `*.security.spec.ts` güvenlik anahtar kelimesiyle
güvenlik yoluna düşer, aday dosya onların dışından seçilir. Yedek: `apps/config-service` (72 dosya, 15 test;
ama şifreleme ve kimlik bilgisi dosyaları çok). Python: GitHub kod aramasında `pyproject.toml` yalnız Aria
çekirdeğinde çıktı; kendi kilidi olan bir Python alan servisi bulunamadı. Ölçüt 5 ve 6 ancak MF6'nın ilk
koşusunda kesinleşir; tutmazsa sıradaki aday denenir.

### 4.5 Ortam tarifi (E77): beyin önerir, hakem doğrular

Kurucu `targets/<kopya>/units.json`'u yazar; hakem türetir ve doğrular, `brain/state`'e yalnız doğrulanmış
tarif girer:

`{unit_id, path, inputs[], toolchain, env_image (@sha256), lockfiles[], install_scripts_required[],
lint_cmd[], test_cmd[], affected_test_cmd[], services: [], limits{}}`

- `inputs` birimin dizini, kullandığı ortak kütüphaneler ve kök yapılandırmalardır (TypeScript için tipik
  olarak `tsconfig.base.json`, `jest.preset.js`, kök `package.json` ve `package-lock.json`, eslint
  yapılandırması). Yeterliliğinin kanıtı yalnız bu girdilerle HEAD'in 3/3 yeşil koşmasıdır.
- İmaj resmi araç zinciri imajıdır, `@sha256` ile pinli, depodaki sürüm dosyasıyla aynı sürüm; çekme
  `koş`un host adımında, kod koşmadan.
- Bağımlılıklar (MF5): `getir` kilitteki her tarball'ı `integrity` ile doğrular, `resolved` izinli kayıt
  defterinde olmalı, git ve dosya bağımlılıkları reddedilir. `koş` kapsayıcısı onları ağsız kurar
  (`npm ci --offline --ignore-scripts`, önbellek tarball'lardan); betik gerektiren paket
  `install_scripts_required`'tadır ve `koş`ta ağsız koşar (`08:16`).
- **Lisans:** kapı ürüne giren bağımlılıklar içindir (`24:25`); hedefin bağımlılıkları ürüne girmez, rapor
  yazılır ama kapılanmaz.
- Etki kümesi Aşama 0'da birimin servissiz testlerinin tamamıdır ve `kaba` işaretlidir (`05:25-26`);
  snapshot'ta `.git` olmadığı için depo araçlarının "etkilenen" komutları kullanılmaz.

### 4.6 Boyut ve kapsam sınırları (E55, E125)

Döngünün karşılaştırdığı her sınır `policy.json` `operating{key: {value, band}}` anahtarıdır; sabit yoktur:
`unit_inputs_bytes`, `deps_bytes`, `worktree_bytes`, `container_mem_bytes`, `kos_wall_s`, `test_total_s`,
`output_bytes`. Başlangıç değerlerini ve bandı operatör yazar. Sınıra takılan iş `limit_hit:<anahtar>`
nedenidir, Kurucu'ya sayılmaz, `status.md`'de görünür. Aşama 0'da sınır kendini ayarlamaz (E68'in kuralı P1'de).
Worktree tmpfs değil, koşu başına taze bir host dizinidir; monorepo'nun kök kilidi büyük olduğu için
`deps_bytes` ilk ölçümle bandın içine çekilir. Aşama 0'da birim sayısı 1, aday sayısı devir başına 1'dir.

### 4.7 Yasak olan ve serbest olan

- **Yasak (Aşama 0 ve K6 canlı olana kadar):** Y3 (migration, manifest ya da kilit değişikliği, deploy, sır,
  feature flag); güvenlik yolu ve hariç yol yazımı, biçimleyici dahil (`04a:40-42`); güvenlik kodu
  düzeltmesi; `main`'e yazım; kopyada iş akışı ya da kimlik; Kurucu'nun hedef kodunu koşturması.
- **Serbest, Aşama 1'den (P2):** güvenlik testleri `<state_root>/security/tests/`'e, güvenlik profili ve
  doğrulanmış bildirimler (`03:28-31`, `05:30-31`, E56). Aşama 0'da güvenlik MF'si `secrets.scan`'dir;
  güvenlik defterine yalnız tohumda kapanan hakem açıkları yazılır (`seed/security-ledger.jsonl`).

## 5. Yeni beyin reposu ve tohum

### 5.1 Beyin reposu

Ayrı, yeni, açık bir repo (`snowball-mcp` değil, E88); Kurucu'nun ince taneli belirteci yalnız ona içerik
yazar (E112); `main`'de `non_fast_forward` ve `deletion` (E95, E136).

```
spec/            tohum dönemindeki spec/tohum ve aşama sayfaları
seed/            tohum dönemindeki seed/** (bootstrap, drill, launcher)
referee/         döngü hakeminin adayı; .github/workflows/loop.yml, schemas/, tests/ dahil
targets/<id>/units.json        birim tarifi önerisi (veri)
candidates/<id>/<cid>/         finding.json, diff.patch, expect.json
tests/fixtures/toy-repo/       oyuncak hedefin içeriği; ajan yapılandırması taşımaz (E131)
reports/*.json                 tipli bildirimler (§5.6)
founder-ledger.jsonl
snowball-tests.json            {tests, done_mf, lockfiles}; done_mf geçerli aşamanın tablosuna göre
exit-request.json              yalnız çıkış ve parti isteğinde
```

### 5.2 Tohum dönemi (E88)

- `setup/summary.json` `seed_epochs[]` taşır: `{commit, spec_tohum_sha256, seed_sha256, bootstrap_sha256}`.
  `pull` beynin `spec/tohum/**` ve `seed/**` ağaçlarını `base`'e değil son döneme karşı karşılaştırır
  (bugün yalnız `spec/tohum`'u tek hash'e karşı, `cli.py:290-293`).
- Yalnız tohum yollarını değiştiren ve ağaçları son döneme eşit olan push `seed_update`'tir:
  değerlendirilmez, rakip yok, seri yok, sonuçta kayıt. Başka her tohum yolu değişikliği `seed_modified`
  (Kurucu'nun).
- Önyükleme hakemi her koşuda kendi `bootstrap/` ağacının hash'ini son dönemin `bootstrap_sha256`'sıyla
  karşılaştırır; uyuşmazsa durur (E24).
- **Runbook:** `snowball-mcp` `main`'i yeşil → kill switch aç → aynı commit'ten `bootstrap/`, `vectors/`,
  `seats/`'i hakem reposuna kopyala → döneme satır ekle → operatör aynı `spec/tohum` ve `seed/`'i beyin
  `main`'ine tek commit'le iter → kill switch kapat → dokunuş satırı.

### 5.3 Defter push'ları (E89, E107)

- Yalnız `founder-ledger.jsonl` ve/veya `reports/` değiştiren push `ledger` türüdür: değerlendirilmez, rakip
  çağrılmaz, seriye ve `rival_artifacts`'a girmez; zincir ve yalnız-ekleme denetimi yine koşar.
- Kurucu defterini ilk oturumdan zincirli yazar: tohum `seed/bootstrap`'ta bir `founder-ledger append` aracı
  verir (eski MF2 düşer; `00a:24-27` değişir). `pull` her push'ta zinciri tohumun kanonik koduyla ve son
  kabul edilmiş SHA'daki sürüme göre yalnız-eklemeyi denetler; aksi `founder_ledger_invalid`.
- Defter ve `reports/` rakibin diff'inden ve araçlarından çıkarılır (E10).

### 5.4 Ajan yapılandırması yolları (E90)

Beyin push'unda herhangi bir yerde (büyük-küçük harf duyarsız) `.claude/**`, `CLAUDE.md`, `AGENTS.md`,
`.mcp.json`, `.vscode/**`, `.envrc`, `.devcontainer/**` → `agent_config_modified` (Kurucu'nun reddi).
Kurucu'nun yapılandırması repo dışında, başlatıcıya aittir.

### 5.5 Kurucu başlatıcısı sözleşmesi (E91), Aşama 0 kadarı

`seed/launcher/` (tohum kodu, `snowball-mcp` CI'ında testli); operatör Kurucu'nun kapsülünde ya da ayrı
Windows kullanıcısında koşar (karar 2026-10-29 madde 2):

1. `control.json`'u hakem reposunun `main`'inden okur; kill switch açıksa çıkar; `founder_resume` (E113).
2. Son imzalı önyükleme sonucunu (`actions:read` belirteci, Sigstore doğrulaması) ve beyin başını okur:
   baş için sonuç yoksa beklemede, çıkar; `not_learning`, park ya da kesinti varsa başlatmaz ve uyarır;
   kabul ya da ret varsa başlatır.
3. `claude -p` pinli sürüm, Opus model kimliği, `--max-budget-usd <session_cap_usd>`, ayar kaynağı yok ya da
   operatörün yönettiği dosya, `--strict-mcp-config`, taze `CLAUDE_CONFIG_DIR`,
   `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`; çalışma dizini beyin klonu; hedef salt okunur klon dışarıda; açılış
   "`00` ve `00a`'yı oku" ve tipli durum.
4. Bitince CLI'nin bildirdiği maliyeti `kind: cost` satırı olarak deftere ekler; oturum sayısı ve USD
   `status-stage0.md`'ye girer (E120).

### 5.6 Bildirim kanalı ve ilk koşu (E93, E92, E121, E123)

- `reports/*.json`: `{id, kind: seed_issue|referee_weakness|spec_issue, ref, evidence_test?, state}`. `pull`
  okur, rakipten gizler, imzalı sonuçta `reports[]` olur, adım özetine çıkar ve operatörü uyarır. Yaşam
  döngüsü E53'teki gibi; spec ve tohum sorunlarını operatör tohum dönemiyle kapatır, Kurucu teyit eder.
- Doğrulanmış hakem zayıflığı: önyükleme hakemindeyse operatör kill switch'i açar ve tohum dönemiyle düzeltir;
  döngü hakemindeyse `control.json` `merge_paused: true` (birleştirme kapalı, gözlem sürer) düzeltme
  aktarılana kadar (E123).
- İlk koşu işareti varken önyükleme hakemi yargılanacak bir şey olmasa da başlangıç durumunu imzalar;
  runbook: bir kez tetikle, imzalı durumu doğrula, işareti kaldır, sonra Kurucu'yu başlat (E92).
- `not_learning`, park ve push'tan sonra sonuçsuz bekleme koşuyu imzadan sonra kırmızı bitirir;
  `snowball-mcp` CI'ındaki gece bekçisi iki iş akışının da son koşusunu denetler (E121, E32).

## 6. Etki listesi

Partiler sırayla uygulanır; her parti kendi dalında, kendi doğrulamasıyla kapanır. Spec önce gelir (kırmızı
test spec'e karşı yazılır).

### Parti 1 · Aşama 0 spec'i — doğrulama: tohumun spec denetimi, çapraz referans ve INDEX denetimi

| Sayfa | Değişiklik |
|---|---|
| `asama-0/00-ozet` | amaç yürüyen iskelet; (A)/(B) özeti; önyükleme hakemi kalır; iki hedef |
| `asama-0/01-amac` | "hakemin tamamı" yerine ilk canlı döngünün okudukları; çalışma zamanı LLM yalnız (B) kanaryası |
| `asama-0/02-dogruluk` | 1, 6, 9, 10, 11 kalır (10 daralır); 2, 3, 5, 7, 8 P1'e; 12 P2'ye |
| `asama-0/03-roller` | Kurucu 18 MF; önyükleme hakemi itme yargıcı olarak kalır; taban avcı satırı çıkar |
| `asama-0/04`–`07` | içerik `asama-1/13-aktarim-partileri` (P1) sayfasına taşınır; sayfalar "taşındı" notu ya da silinir |
| `asama-0/08-puanlama` | yalnız K0 eşleme ve `mapped_line` kuralı kalır (E108); metrikler P1'e |
| `asama-0/09` | test tablosu: kalan 13, 14, 19, 20, 21, 23, 25, 34–40, 42, 45; yeni 46–50; diğerlerinin partisi yazılır; manifest kuralı tabloya bağlanır |
| `asama-0/10` | §3'ün (A) ve (B)'si, dürüstlük provası, kilit açılışı, başarısızlık |
| `asama-0/11-yasaklar` | "LLM yalnız oyuncakta" kalkar; hariç yollar, Kurucu'nun hedef kodu koşturmaması, `referee_changed_after_exit` |
| `asama-0/12-butce` | karar K5'in değerleri |
| `asama-0/13-teslim` | yeni teslimler: 18 MF, `loop.yml`, iki hedefte durum, PASS satırı; `snowball init`, `mcp/`, `docs.index` çıkar (E100) |
| `asama-0/14` | §2.1'in listesi: MF, test, vektör grubu, modül yolu, adım |
| `asama-0/CHANGELOG` | 3.0 satırı |

### Parti 2 · Tohum sayfaları — doğrulama: aynı denetimler; `test_wiring` sayfa ↔ kod satırları

| Sayfa | Değişiklik |
|---|---|
| `00a` | defter tohum aracıyla ilk oturumdan zincirli; bildirim kanalı; ilk görev adımı 3 |
| `01a` | aktarım noktası: aşama çıkışı ya da parti çıkışı; hakem reposunda önyükleme hakemi kalır |
| `02` | Aşama 0'da liste tohum denetimi; kilit (A)'da çift, açılış (B)'de `stage.json`; parti çıkışı |
| `03` | aşama tablosunun 0 ve 1 satırları |
| `04` | gerçek test kuralına modülsüz kırmızı |
| `08` | döngü iş akışı; worktree host dizini; birim imajı; servisler sonra |
| `14` | `units[]`; ajan yapılandırması ve operatör hariç yolları; daraltma reddi |
| `22a` | Aşama 0'da yalnız geri alma provası; ders provası Aşama 2 partisinde |
| `24` | yeni beyin reposu ve yerleşimi; başlatıcı (E91); hedefe yazım API ile; lisans kapısının kapsamı (ürün, hedef değil) |
| `25` | beyin reposu yeni ve ayrı (E88); üç repoda ruleset (E136); tohum dönemi; `targets[]` (E99); kopya ve aynalama (E78); dürüstlük ekimi ve taahhüdü; gece bekçisi (E121) |
| `25a` | aktarım önyükleme hakemini korur; `stage-open`; kopyanın adımları; satır 7'deki avcı koltuğu P2'ye |
| `26` | bölüm tablosunda `security` P2'den |
| `26a` | taşınan araçlar işaretli; `unit.verify`, `target.write` eklenir; ilk çağıranıyla açılanlar listesi |
| `26b` | `profile.json` `units[]`; `control.json` (`loop_schedule`, `merge_paused`, `founder_resume`; eksik alan kapalıya düşer, E104); `setup/summary.json`, `setup/stage.json`, `reports/*.json`, hazır aday biçimi; `done_mf` anlamı; `operating{}` |
| `27` | yeni dosyaların okuyucuları (`stage.json`, `reports/`, `units.json`, `candidates/<hedef>/`, `status.md`) |
| `29` | rakip `reports/`'u görmez |
| `29a` | yeni gruplar ve veri biçimi; genel koşucu; `drill` grubunun sahibi Aşama 2 partisi |
| `29b` | Aşama 0'dan sonra da itme yargıcı; `ledger` ve `seed_update` türleri; tohum dönemi; modülsüz kırmızı; `wiring`; dürüstlük; aşama ve parti tablosu; `referee_changed_after_exit`; E97 |
| `29c` | prova vektörlerinin uygulanma anı Aşama 2 partisi; geri alma provası vektörleri |
| `30d`, `30f` | güvenlik gözlemi P2 ile Aşama 1'de; avcı koltuğunun aktarımı P2'de |
| `18a` | `operating{}` anahtarları ve bantları (E125); `stage_budgets.asama_0` |
| `tohum/CHANGELOG` | satır |

### Parti 3 · Aşama 1 spec'i — doğrulama: aynı denetimler

| Sayfa | Değişiklik |
|---|---|
| `asama-1/00-ozet` | "hakem donuktur" (`:12-13`) yerine: hakem yalnız P1, P2 ve çıkış aktarımıyla değişir |
| `asama-1/04-roller` | Kurucu parti adaylarını `referee/` altında yazar (`:11`) |
| `asama-1/05-dongu` | adım 0 kayma P1'den; adım 1 önyükleme hakeminin kabul ettiği SHA (`:11-12`); organ koşucusu |
| `asama-1/06` | P1 MF1'den önce, P2 içeride; MF6'nın `accept` satırını döngünün `yaz`'ı yazar (`:20-21`) |
| `asama-1/08` | çıkış (A) + aktarım + (B); E82 satırları (`hunk_covered`, `mutant_killed`, `weak_oracle`); #lint #lock yeni anlamıyla |
| `asama-1/09-yasaklar` | "Hakeme yazmak" (`:16-18`) parti adayı yoluna göre |
| `asama-1/12-teslim` | teslimler ve açılış tetikleri |
| `asama-1/13-aktarim-partileri` (yeni) | P1 ve P2'nin MF'leri, testleri, vektör grupları; eski `asama-0/04`–`07` |

### Parti 4 · Tohum kodu, önkoşullar — doğrulama: birim testleri Linux ve Windows, mutantlar

| Modül ya da test | Değişiklik |
|---|---|
| `vectors.py` | E141: son deneme 125 ise `runner_fault` (yeni gruplardan önce) |
| `classify.py` | `ledger` türü, `agent_config_modified`, büyük-küçük harf duyarsız yollar (E89, E90, E130) |
| `cli.py` `pull` | E97'nin aynı istek kuralı; `reports/` okuma (E93); Kurucu defteri denetimi (E107) |
| `rival.py` | `reports/`'u diff'ten ve araçlardan gizler |
| `config.py` | `control.json` tipli alanlar kapalıya düşer; `summary.json` yeni alanlar; `stage.json` yükleyici (E104) |
| `state.py` | `stage`, `disputes`, aktarılabilir hakem ağacı alanları; sürümlü taşıma |
| `tests/test_units.py`, `test_flow.py`, `test_decision.py` | yeni türler ve nedenler |
| `tests/test_security_ledger.py` | kapanan her açık için `fix` satırı |

### Parti 5 · Tohum kodu, aşama tablosu ve vektörler — doğrulama: testler, referans beyin, e2e

| Modül ya da test | Değişiklik |
|---|---|
| `seed/bootstrap/stages/stage0.json` (yeni) | 18 MF: testler, vektör grupları, modül yolu, `calls` |
| `manifest.py` | `STAGE0_MF_TESTS` (`:15-21`) yerine tablo; `check_stage0` modül yolu ve `calls` sırasını denetler; `STAGE0_MF_COUNT` 18 |
| `vectors.py` | `GROUPS` (`:126-136`) tablo güdümlü; yeni gruplar tek veri koşucusuyla; `drill`, `cp_lower`, `mcnemar`, `match` Aşama 0'da sahipsiz, koşmaz |
| `cli.py` `run-tests` | modülsüz kırmızı yeniden koşusu |
| `seed/bootstrap/vectors/` | `vectors.json` şema 2 ve on altı yeni grubun fikstürleri, iki bağımsız hesapla |
| `seed/drill/` | oyuncak hedef için geri alma provası fikstürleri ve `revert_drill` vektörlerinin referans yargıcı |
| `local/e2e.py`, `local/reference_brain/` | yeni tablo; referans beyin MF1'i taşımaya devam eder |
| `local/mutate.py` | her yeni denetim için mutant |
| `tests/test_wiring.py` | `stage0.json` ↔ `asama-0/14` ve `09` birebir |
| `tests/test_reference_brain.py`, `test_flow.py` (`:22-33`) | grupları ve manifestleri tablodan kurar |
| `tests/test_vectors_data.py` (yeni) | genel koşucu; değiştirilmiş girdi reddi |

### Parti 6 · Tohum kodu, çıkış ve aktarım — doğrulama: testler, mutantlar, e2e (`stage-open` dahil)

| Modül ya da test | Değişiklik |
|---|---|
| `decide.py` çıkış (`:157-173`) | 18 MF tablodan; #modulsuz, #kurucu-defteri, #is-akisi, #agac, #genellik, #spec, #durustluk nedenleri; `referee_changed_after_exit`; `ledger`/`seed_update` seriye ve `rival_artifacts`'a girmez |
| `cli.py` `pull` | tohum dönemi karşılaştırması `spec/tohum/**` ve `seed/**` (`:290-293`); `seed_update` |
| `wiring.py` (yeni) | sınırlı YAML altkümesi ve iş akışı kuralları (E100, E132) |
| `speclint.py` (yeni) | `02`'nin mekanik maddeleri |
| `honesty.py` (yeni) | taahhüt, anahtar, yüklemler, itirazlar |
| `importer.py` | `bootstrap/` ve iş akışını silmez (`:51-59`); `loop.yml`; büyük-küçük harf ve ajan yapılandırması reddi; kardeş geçici dizine açıp yeniden hash'ler; kill switch açık şartı; oyuncak taze dizine |
| `cli.py` `stage-open` (yeni) | PASS satırı doğrulaması ve `setup/stage.json` |
| `workflow/bootstrap.yml` | `not_learning`, park ve sonuçsuz beklemede imzadan sonra kırmızı (E121); `status-stage0.md` (E120) |
| `tests/test_boundaries.py`, `test_decision.py`, yeni `test_honesty.py`, `test_seed_epoch.py`, `test_speclint.py` | yukarıdakilerin her biri |

### Parti 7 · Tohum araçları — doğrulama: `snowball-mcp` CI

| Parça | Değişiklik |
|---|---|
| `seed/launcher/` (yeni) | §5.5; testleri ve `24` ile sözleşme denetimi |
| `seed/bootstrap` defter aracı | `founder-ledger append` |
| `.github/workflows/ci.yml` | tohumlamadan önce `spec/asama-0` ve `asama-1` spec denetimi; gece canlılık bekçisi |

### Parti 8 · Kayıt satırları (`docs/eksik-kaydi.md`) — doğrulama: her satırın kanıtı bir commit

| Satır | Yeni durum |
|---|---|
| E76 | yeniden kapsamlandı: bu tasarım; kapanış Parti 1–7 ile |
| E77 | `units[]` ve tarif doğrulaması MF4, MF6; servisler sonraki partide |
| E78 | kopya, Actions kapalı, aynalama §4.2; orijinale yol açık kalır |
| E79 | (A) #durustluk |
| E82 | ilk döngü satırları (B)'de; `hunk_covered` kapısı ve `mutant_killed` Aşama 1 |
| E88, E89, E90, E91, E92, E93 | §5.2–§5.6 |
| E96, E97, E99 | (B) #aktarim ve `loop_schedule`; aynı istek kuralı; `targets[]` |
| E100, E101, E102, E103, E104, E105 | MF17 ve #is-akisi; kum sütunu; #spec ve #kilit; vektör grupları ve modülsüz kırmızı; alan şemaları; `calls` |
| E106 | P1'e taşındı (P1'in önkoşulu) |
| E107, E108, E109, E110, E111 | #kurucu-defteri; MF8 `k0map`; MF14; #genesis; #taban |
| E121, E123, E125, E141 | §5.6; `merge_paused`; `operating{}`; Parti 4 |
| E56 | güvenlik gözlemi P2 ile Aşama 1'de; Aşama 0 güvenlik MF'si `secrets.scan` |
| E48, E52, E64, E65 | ders provası yargıcıyla Aşama 2 partisine |
| yeni E148 | aşama içi parti aktarımı (K2) |
| yeni E149 | önyükleme hakemi Aşama 0'dan sonra itme yargıcı (K1) |

### Parti 9 · Operatör adımları — doğrulama: `setup/summary.json` hash'leri ve ilk koşu

Yeni beyin reposu ve ruleset'i; ince taneli Kurucu belirteci; oyuncak repo; kopya (yalnız `main`, Actions
kapalı, ruleset, yazar App'i); aynalama işi (duraklatılmış); `targets[]` ve `excluded_paths`; dürüstlük ekimi ve
taahhüdü; birinci tohum dönemi; `operating{}` bantları; başlatıcı kapsülde; ilk koşu işareti (E92).

## 7. Riskler ve açık sorular

### Bu tasarımın çözmedikleri

- **Tohum işi büyür.** Kurucu'dan alınan iş tohuma geçer: on altı vektör grubu, `wiring`, spec denetimi,
  dürüstlük, tohum dönemi, başlatıcı. Veri güdümlü vektör koşucusu bunu azaltır; yine de Parti 4–7, Kurucu
  başlamadan önce birkaç oturumdur.
- **Monorepo birimi.** Kök kilit büyük; `deps_bytes`, `worktree_bytes` ve kurulum süresi ilk ölçümde bandı
  aşabilir. `npm ci --offline`'ın tarball'lardan önbellekle çalışması ilk MF5 koşusunda doğrulanır; tutmazsa
  kilit v3'ün `packages` yollarına doğrudan açılır.
- **Daha çok insan dokunuşu.** P1, P2 ve her parti çıkışı birer aktarımdır; sayaç büyür.
- **(B) iki adımlı.** Kopyada aday, aktarımdan sonra Kurucu'nun bir push'uyla gelir; önyükleme hakeminin
  aşama durumu "(A) geçti, (B) bekliyor" ara hâlini taşımalıdır.
- **Bal küpü.** Önyükleme hakemine bilerek konan zayıflık Aşama 0 boyunca gerçek bir açıktır; çıkış anahtarıyla
  yakalanır, ama aşama içinde kusurlu kodun kabulüne izin verebilir. Aktarımdan önce hiçbir şey canlıya
  girmediği için zarar sınırlıdır.
- **Kopyanın orijinale yolu yok** (E78'in üçüncü parçası); Aşama 6'ya kadar kabul edilen düzeltme yalnız
  kopyada yaşar.
- **Kapsam dışı kalan kayıt satırları:** öğrenme ve hafıza (E64–E75, Aşama 2'ye kadar), E80, E81, E83–E87, E122,
  E124, E126–E129, E132'nin avcı kısmı, E133–E140, E142–E147 (tohum kusurları; kendi partilerinde) ve
  operatör adımı bekleyenler (E94, E112, E119).

### Sahibin kararı gerekenler

| # | Karar | Öneri |
|---|---|---|
| K1 | Önyükleme hakemi Aşama 0'dan sonra da beyin reposunun itme yargıcı kalsın; `brain.accept`, `lock.check` ve rakip dispatch'i Kurucu'nun Aşama 0 işinden çıksın | Evet. Kurucu olmayan bir yazarın deterministik kodu, Kurucu'nun yazacağı yargıçtan bağımsızdır; aktarım iş akışını silmez (E100) |
| K2 | Aşama içi parti aktarımı (P1, P2): her biri (A) → aktarım → (B), her biri bir dokunuş | Evet. Yoksa ya P1 ve P2 Aşama 0'a geri döner (daraltma boşa gider) ya da güvenlik gözlemi Aşama 2'ye kayar (E56'nın zamanı tutmaz) |
| K3 | İlk gerçek birim `apps/alert-engine` (TypeScript); oyuncak hedef JavaScript; Aşama 0'da tek ekosistem npm | Evet. Kendi kilidi olan bir Python alan servisi bulunamadı; tek ekosistem bir MF'yi düşürür |
| K4 | Dürüstlük provası: imkânsız vektör ve önyükleme hakeminde bal küpü, mühürlü anahtarla; ekimi operatör Kurucu olmayan bir ajanla yapar | Evet; (c) teyit yalnız düzeltilen bildirim varsa ölçülür |
| K5 | Aşama 0 bütçesi ve takvimi (`asama-0/12`) | Kurucu ≤ 220 USD ve ≤ 22 oturum (18 MF + çıkış); rakip ≤ 25 USD; (B) kanaryası ≤ 1 USD |

### Açık soru (karar değil)

- **Aria sonra dahil edilsin mi; Aria ile Snowball birbirinden öğrensin mi?** Aria sahibin kendi otonom ajan
  sistemidir ve `aquaculture_platform`'un içinde yaşar. Bu tasarımda kapsam dışıdır: profilden hariç, iş
  akışları kopyada kapalı, Snowball onu ne düzenler ne yükler. Dahil etmek ya da karşılıklı öğrenme (ör. aynı
  hata sınıflarının iki sistemde ölçülmesi) ilk aşamalar bittikten sonra ayrıca konuşulur.
