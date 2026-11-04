# Kurucu kapsülü ve pilot başlatıcısı

Kurucu (`spec/tohum/24a`) yalnız bu kapsülde çalışır: operatörün GitHub girişi ve Claude yapılandırması içeri
girmez. Kapsülün kökü salt okunur, yetkileri düşürülmüş; beyin her oturumda bellekte taze klonlanır, GitHub tek
evidir. Sınırlar `seed/bootstrap/tests/test_founder_capsule.py`'de sabitlidir.

**Araçlar** (E380). Oturum CLI'ın varsayılan araçlarıyla koşar; yalnız dördü kapalıdır (`--disallowedTools
"RemoteTrigger,CronCreate,CronDelete,CronList"`): `RemoteTrigger` etkisi kapsülden sonra da sürebilen tek varsayılan
araçtır (bulutta bir rutin), Cron araçları süreçle ölür ve hiç kullanılmadı. Başka hiçbir araç daraltılmaz (`--tools`,
`--allowedTools` yok); `test_live_cli` girişin kendi çağrısını sabitli CLI'a uydurma bir jetonla koşturur ve init
olayında dördünün olmadığını, kalanların durduğunu denetler. İmaj yeniden kurulunca geçerli olur; talimat değişmez.

**Beynin ajan ve skill tanımları** (E450, sahibin onayı 2026-11-01). Her oturumda, klon kesildikten sonra ve
`claude`'dan önce `brain_defs.py` hakemin beyinde son kabul ettiği commit'in (E531; aşağıda) `agents/` ve `skills/`
ağaçlarını git nesnelerinden
(`ls-tree`, `cat-file`; dosya sisteminden değil, hiçbir bağ beynin dışına götüremez) okur, denetler ve
`$CLAUDE_CONFIG_DIR/brain-plugin`'e bir eklenti yazar; CLI onu `--plugin-dir` ile yükler, ayar kaynakları kapalı kalır
(CLAUDE.md, ayarlar, hook'lar, MCP, çıktı stilleri hiçbir kaynaktan yüklenmez). Eklentinin ajanları ve skill'leri
`brain:<ad>` adını alır, CLI'ın kendi ajanlarının yerine geçemez. Eklentide yalnız `.claude-plugin/plugin.json`
(`{"name": "brain"}`), `agents/` ve `skills/` vardır; her ajan dosyası ve her `SKILL.md` denetlenen alanlardan yeniden
yazılır (CLI denetleneni okur), skill'in kendi dosyaları bayt bayt ve kipleriyle kopyalanır.

**Yalnız kabul edilmiş commit'ten** (E531, sahibin kararı 2026-11-03). Okunan commit klonun `HEAD`'i değil, hakemin
imzalı sonucunun `state.last_accepted_sha`'sıdır: başlatıcı sonucu `referee/`'ye indirir (`fetch_result`), kapsül onu
`/work/referee/result.json` olarak salt okunur görür ve giriş yükleyiciye dördüncü argüman olarak verir. Hakemin
reddettiği ya da henüz yargılamadığı bir push'un tanımı yüklenmez; kabul edilince sonraki oturumda yüklenir. Sonuç
yoksa, okunmuyorsa, `snowball-bootstrap-result/1` değilse ya da klonda olmayan bir commit adlandırıyorsa hiçbir tanım
yüklenmez, kayıt nedenini (`NotAccepted: ...`) yazar, oturum tanımsız başlar. Ajanın `model`'i sahibin model kuralıdır
(2026-11-01: claude-opus ya da claude-sonnet, en son sürüm): `inherit` (oturumunki), `claude-opus-5-5` ya da
`claude-sonnet-5-5` (`ALLOWED_MODELS`); takma ad (ne adlandırdığı CLI'ın seçimi), haiku, eski sürüm ya da büyük bağlam
penceresi `model_not_allowed:` ile düşer. Model sürümü değişince küme de değişir (operatörün işi); test başlatıcının ve
girişin varsayılan modelini kümeye bağlar. Sınır: yükleyici sonucun Sigstore paketini yeniden doğrulamaz; sonucu
başlatıcının `gh` girişi hakem reposunun `main` koşularından indirir, Kurucu'nun ona yazma yolu yoktur (bağ salt okunur,
jeton yalnız beyin).

| Kaynak (beyin) | Biçim |
|---|---|
| `agents/<ad>.md` | ön bilgi `name`, `description`, isteğe bağlı `tools` (`Read, Grep` gibi virgüllü adlar) ve `model` (`inherit`, `claude-opus-5-5` ya da `claude-sonnet-5-5`; E531); gövde ajanın talimatı |
| `skills/<ad>/SKILL.md` | ön bilgi `name`, `description`; gövde skill'in yönergesi; dizinin başka dosyaları skill'in kendi dosyalarıdır |

Ön bilgi ilk satırı `---` olan ve bir sonraki `---` satırında biten satırlardır; boş olmayan her satırı satır başında
`<anahtar>: <değer>`'dir, çift tırnaklı değer JSON dizgesi, tek tırnaklıda `''` bir `'`'tir, başka değer olduğu gibi
alınır. Ad küçük harf ve rakamlardan, tek tirelerle (en çok 64), dosyanın ya da dizinin adıdır; açıklama tek satır
(en çok 1024, kontrol karakteri yok); gövde boş olmaz; UTF-8, CRLF LF okunur. Korkuluklar, her biri
`test_founder_capsule` `BrainDefinitionsTest`'te: yalnız iki dizin okunur, başka hiçbir yol yapılandırma olmaz; başka
anahtar (`hooks`, `mcpServers`, `permissionMode`, `allowed-tools` ...) tanımı düşürür (`key_not_allowed:`); ajanın
`tools`'u kapsülün araçlarının (`ALLOWED_TOOLS`; `test_live_cli` onu CLI'ın init olayına bağlar) alt kümesidir, kapalı
dördünden biri `tool_denied:`, başka ad `tool_not_allowed:` ile düşer; boyut ve sayı sınırları tek sabittir
(`LIMITS`: 32 ajan, 32 skill, tanım başına 64 KiB, skill başına 64 dosya ve 1 MiB, 6 dizin derinliği, toplam 4 MiB,
4096 git girdisi); ad kuralı, adın dosyayla eşleşmesi, sembolik bağ, alt modül, güvensiz dosya adı ve hakemin ajan
yapılandırması saydığı yol (`classify.AGENT_DIRS`, `AGENT_FILES`; `agents/claude.md` dahil) tanımı düşürür. Kayıt
oturumun klasöründe `brain-definitions.json`'dır (`snowball-brain-definitions/2`): tanımların okunduğu kabul
edilmiş commit (`brain`) ve klonun başı (`head`), yüklenen her tanımın adı, `loaded_as`'ı, kaynak blob'un
sha256'sı (skill'in her dosyasınınki de), düşen her tanım ve nedenleri, sınırlar ve araç kümeleri. Kullanım dökümden
ölçülür: `Agent` çağrısının `subagent_type`'ı ve `Skill` çağrısının `skill`'i `brain:<ad>`'dır. Kırık bir tanım
oturumu durdurmaz, atlanır ve kayda girer; yükleyicinin kendi hatası eklenti bırakmaz, kayıt hatayı adlandırır, oturum
tanımsız başlar (girişte `||`). `test_live_cli` sabitli CLI 2.1.293'te uydurma jetonla init olayının `brain:` ajanını ve
skill'ini listelediğini, kapalı araçlı ajanın listelenmediğini ve 127.0.0.1'e giden ilk istekte açıklamaların ve
araçların kayıttaki gibi, klonun `CLAUDE.md`'sinin hiç görünmediğini denetler. Talimat yalnız bunun bir gözlem
cümlesini taşır (`prompt.md` "Beynin tanımları"); tanım yazıp yazmamak Kurucu'nundur. İmaj yeniden kurulunca geçerli
olur.

**Defterin salt-okur dizini** (E506, sahibin kararı 2026-11-02, boşluk D). İmajda `/opt/founder/ledger_index.py`
vardır; Kurucu onu isterse `python3 -I /opt/founder/ledger_index.py <komut>` ile koşturur (`-I`: `/work/brain`'deki ya
da `PYTHONPATH`'teki bir modül araçtan önce yüklenmez). Talimat bunu bir cümleyle söyler (`prompt.md` 2. madde); hiçbir
görev, etiket ya da soru adlandırmaz. Araç her çağrıda defterin baytlarını bir kez okur ve hiçbir şey yazmaz ya da
saklamaz (önbellek yok, beyne dizin dosyası yok); her yanıtın ilk satırı okuduğu baytları (`bytes`, `sha256`, `rows`)
ve ucu (`tip`: son okunabilir satır) yazar, `"verified": false` der: zinciri, satır hash'lerini ve anlam kurallarını
yargılamaz (hakemin ve Kurucu'nun kendi denetiminin işi; hakemin kodu kapsüle girmez). Kesin katman alan değerine göre
bulur (`kind`, `part`, `derivation`, `trust`, `row_id`, `row_hash`, `supersedes`, satır numarası, `snapshot_id` öneki,
`ts` günü, yol, rapor, `<etiket>:<değer>` ref'i); bulduğu, defterin her satırını aynı kuralla taramanın bulduğudur
(`tests/test_ledger_index.py`: 300 rastgele defterde ve gerçek defterin `4423ff3` kopyasında bağımsız kâhinle).
Katlamalar: `unclosed --tag T` (sonraki bir satırın `T:<row_id>` ref'iyle adlanmayan satırlar; kapatanın geçerliliği
yargılanmaz), `sessions`, `named`, `history`, `tail`, `keys`, `show` (satırlar olduğu gibi). `text` katmanı serbest
metinde düz dizgi arar ve yalnız aday verir (`"guarantee": "none"`). Bir sayfa `--limit`'te ya da 24.000 baytta biter,
`next` devamının tam argümanıdır (CLI 30 KB'yi aşan çıktının yalnız 2 KB'lik önizlemesini gösterir). Çıkış 0; okunamayan
satır varsa 1 (yanıtlar okunanları kapsar, okunamayanlar adlarıyla listelenir); kullanım hatası ya da defter yoksa 2.
"Yürürlükteki kararlar" ve "açık raporlar" izdüşümü yoktur: kararı geri çekmenin yapısal biçimi yok (bugün 225/225
karar "yürürlükte" görünürdü), sahibin kararını bekler. İmaj yeniden kurulunca geçerli olur.

**Klasör.** Pilotun her şeyi tek klasördedir (varsayılan `F:\snowball-work`); silinince pilot iz bırakmaz:

| Yol | Ne |
|---|---|
| `snowball-founder.env` | `GITHUB_TOKEN` (yalnız beyin reposu, Contents: Read and write) ve `CLAUDE_CODE_OAUTH_TOKEN` (`claude setup-token`); operatör yazar, yalnız kapsül okur |
| `aquaculture_platform/` | hedef klonu, kapsüle salt okunur |
| `referee/` | hakemin son imzalı sonucu (`result.json`), Kurucu okur |
| `vec/` | vektörlerin girdileri, kapsüle `/vec` olarak salt okunur (E244): `cases.json` (her veri vakasının `id`, `purpose`, `cmd`, `stdin`, `fixture` ve `changed` alanları) ve fikstürler; beklenen değer yok. Her oturumdan önce hakem reposunun `main`'indeki `vectors/`'ten, hakemin kendi `vectors.founder_inputs`'uyla yeniden kurulur |
| `logs/` | oturum dökümleri (`stream-json`); her oturumun klasöründe `brain-definitions.json`, beynin yüklenen ve düşen ajan ve skill tanımları (E450) |
| `pilot-log.md` | operatörün raporu: her döngüde push, hakem kararı, yeni defter satırları ve bildirimler, maliyet satırının ne olduğu, beynin açık raporları ve yaşları |
| `pilot-metrics.jsonl` | her döngünün ölçümü: push, karar, nedenler ve **sahipleri** (hakemin kendi kuralıyla: Kurucu / rakip / hakem), rakibin kanıtlanmış bulguları, eski çürütmeler, yeni bildirimler, süre, maliyet, hakemin yeniden inceleme sayısı; sonucun neye bağlanacağı (E313): `prompt_sha256`, `image_id`, `model`, `cli_version` ve `model_served` (dökümün `init` olayı), `seed_commit`, `spec_tohum_tree`, `rival_config`, `target_sha`, `timed_out`, `budget_usd` (oturumun freni) ve `stage` (açık aşama; E530). Her başlatıcı başlangıcı ayrı bir `kind: intervention` satırıdır (argümanlar, imaj, prompt hash'i). `prompt_sha256` imajın kendisinin: kurulum imajı içindeki prompt'un sha256'sıyla etiketler (`snowball.prompt_sha256`), `--no-build` eski imajı koşturur, etiketsiz imajda `null`; çalışma kopyasınınki `checkout_prompt_sha256`; `context_sha256` imajın bütün kurulum dosyalarınınki (E506): kurulum imajı `snowball.context_sha256` ile de etiketler (`BUILD_FILES`'ın her dosyası, LF ile, sıralı `<yol>\0<sha256>\n` satırlarının sha256'sı), çalışma kopyasınınki `checkout_context_sha256`; ikisi farklıysa başlatıcı bunu söyler: yalnız prompt değil, değişmiş bir araç ya da yükleyici de görünür |
| `cost-pending.jsonl` | henüz yazılamamış maliyet satırları (aşağıda) |
| `reports-seen.json` | başlatıcının her beyin raporunu ilk gördüğü an: raporun yaşı |
| `STOP` | oluşturulursa başlatıcı o adımdan sonra durur |
| `launcher.lock` | çalışan başlatıcının özel işletim sistemi kilidi (E505): klasörde aynı anda tek başlatıcı. Süreç nasıl biterse bitsin (çökme, öldürme, yeniden açılış) işletim sistemi bırakır; elle silinmez |
| `RUNNING` | süren koşu (JSON, E505, E528): seçenekleri (`--work`, `--cycles` ve `--resume` dışında), kalan döngü, sayaçları (Kurucu'nun push'suz bitirdiği oturumlar `idle`, art arda başarısızlıklar `failures`, art arda kullanım sınırları `limit_waits`, son biten döngüden bu yana sürdürmeler `resumes`), başlangıç ve son güncelleme. Ön denetim geçince yazılır, her döngüden sonra güncellenir; yalnız koşu kasıtlı bitince silinir: `STOP`, Kurucu'nun push'suz bitirdiği iki oturum, Ctrl+C ya da son döngü. Çökme, öldürme, yeniden açılış ve HALT onu bırakır ve `--resume` o koşuyu sürdürür. Gizli bilgi yazılmaz |
| `HALT` | koşu operatörü bekliyor (JSON, E528: neden, ne zaman, kalan döngü): art arda beşinci başarısızlık, bu klasörün durmayan bir kapsülü, yenilenemeyen vektör girdileri, okunamayan bütçe (E530) ya da arada hiçbir döngü bitmeden dördüncü sürdürme. `RUNNING` kalır (başarısızlık ve sürdürme sayaçları sıfırlanmış); `HALT` varken `--resume` hiçbir şey yapmaz. Operatör onu silince görev koşuyu sürdürür; elle başlatma onu siler ve koşunun yerine geçer |
| `scorecard/` | karnenin önbelleği ve özel kopyası (E310): `results/` hakemin imzalı sonuçları ve Sigstore paketleri (yalnız eklenir, özetiyle denetlenir), `manifests.jsonl`, `ledger-counts.jsonl` (her yargılanmış başta defterin satır sayısı: öz-tespitin (b) penceresi, E315), `karne.json` ve `karne.md` (maliyet ve keşif dahil). Kapsüle hiç bağlanmaz |
| `gunluk-rapor/` | operatörün günlük gözlemci raporu (E537): `<tarih>.md`, on satır, `daily_report.py` üretir, elle yazılmaz. Kapsüle hiç bağlanmaz |

**Çalıştırma** (operatörün `gh` girişi ve Docker gerekir):

```
python seed/founder/launch.py --cycles 3
```

Her döngü: hakemin son sonucunu indir → vektör girdilerini yenile → bir Kurucu oturumu → beyin değiştiyse hakemi
tetikle ve bekle (zamanlayıcısı seyrek ve düzensiz çalışır, E32: beklemek güvenilmez) → maliyet satırı →
`pilot-log.md`'ye yaz.
**Bitiş durumları** (E528). Her oturumun nasıl bittiği adlandırılır (`pilot-log.md`'de `bitiş`, metrikte `end`):
`usage_limit` (hesabın kullanım sınırı, E243), `exit` (CLI bitti, kapsül 0 ile çıktı), `timeout` (duvar saati sınırında
öldürüldü), `brake` (CLI'nin tur ya da bütçe freni: `error_max_turns`, `error_max_budget_usd`) ya da `error` (başka her
çıkış: Docker kapsülü koşturamadı, kapsül öldürüldü, CLI hata verdi). Koşu yalnız kasıtlı biter ve yalnız o zaman
`RUNNING` silinir: `STOP`, Kurucu'nun push'suz bitirdiği (`exit`) iki oturum ya da son döngü. Kullanım sınırı CLI'nin
adlandırdığı sıfırlanmaya kadar beklenir (adlandırmazsa art arda sınırlara göre 30 dk, 1 sa, sonra 6 sa); push'suz böyle
bir oturum döngü harcamaz ve hiçbir sayacı değiştirmez. `timeout`, `brake` ve `error` başarısızlıktır, push'suz oturum
sayılmaz: art arda 1.'den 4.'ye 5 dk, 15 dk, 45 dk, sonra 3 sa beklenir, 5.'si HALT'tır. GitHub kesintisi, hakemin
yargılamadan bıraktığı bir push ya da kapsülleri listeleyemeyen bir Docker (oturum hiç açılmaz) da koşunun
başarısızlığıdır: döngü harcamaz, aynı bekleyişle beklenir. Push her iki sayacı sıfırlar. Yenilenemeyen vektör girdileri
(eski ya da eksik girdiyle oturum açılmaz) beklemekle düzelmez: HALT. Her alt süreç (her `docker` ve `gh` çağrısı) bir
sınırla çalışır. Her oturumdan önce bu çalışma klasörünün hâlâ koşan kapsülleri (`snowball_founder_<damga>` adlı ve
`logs/<damga>` klasörü burada olan) durdurulur: kilit bu başlatıcıda olduğuna göre her biri ölmüş bir başlatıcının ya da
durmayan bir oturumun kapsülüdür ve sonrakinin yanında push edebilir; durmayan biri HALT'tır, beyinde iki yazan olmaz.
Başka klasörün ya da başka adın kapsülüne dokunulmaz.
Sayfasıyla çelişen bir vektör kırmızı kalır ve operatör tohum dönemiyle yanıt verene kadar kabulü engeller; Kurucu
onu kanıtıyla `seed_issue` olarak bildirir, etrafından dolaşmaz.
**Maliyet satırı** (`spec/tohum/24a` 4, E344): her oturumdan sonra başlatıcı CLI'nin bildirdiğini çıplak gerçek olarak
beynin `founder-ledger.jsonl`'ına bir `kind: cost` Kurucu satırı yazar (`session <damga>: exit, dakika, tur, cost_usd_micros,
CLI sonucu`; bilinmeyen `unknown`), `26`'nın zincir kuralıyla (`canon.row_hash`), hakemin defter denetiminden geçtiği
sınanarak, kendi kimliğiyle (`Snowball launcher`) ve operatörün `gh` girişiyle `main`'e iter. Yalnız son kabul edilmiş
commit'ten bu yana başın değiştirdiği her yol Kurucu'nun hafızası ya da son tohum döneminin teslimiyse yazar: hakem
o commit'i yalnız hafıza (`none`, test yok, rakip yok, `noop`) okur. Kabul edilmemiş iş taşıyan başta yazmaz (hakem o işi
yeniden yargılar, reddi iki kez sayardı): satır `cost-pending.jsonl`'da bekler ve ilk uygun döngüde önce o gider.
Zaman aşımına uğrayan oturumun satırı da yazılır. Başlatıcının commit'i Kurucu push'u sayılmaz (push'suz iki oturum) ve
sonraki oturumdan önce başlatıcıca yargılatılmaz; hakemin zamanlayıcısı onu yine de yargılayabilir: yalnız başlatıcının
commit'lerini ekleyen bir başın `none` sonucu bulunursa `<work>/referee/`'ye bir önceki sonuç girer, Kurucu kendi push'unun
kararını okur (durum ikisinde de aynıdır). Her git çağrısının sınırı vardır (ağ 300 sn); zaman aşımı satırı bekletir, bir oturumun satırı
bir kez yazılır.
Döngülerin değerlendirmesi (ne buldu, ne kaçırdı, öğrendi mi) repoda `docs/pilot-gunlugu.md`'dedir; her döngüden
sonra güncellenir.
**Bütçe** (E530, sahibin kararı 2026-11-03). Her oturumdan önce başlatıcı hakem reposunun `main`'indeki `policy.json`'u
hakemin kendi ayrıştırıcısıyla (`config.policy_of`) okur. Oturumun freni (`--max-budget-usd`) `--budget-usd` ile
`session_cap_usd`'nin küçüğüdür: seçenek freni yalnız düşürür. Son 24 saatte başlamış oturumların harcaması artı bu fren
`day_cap_usd`'yi aşabilecekse oturum açılmaz: başlatıcı en eski oturumlar pencereden yeterince çıkana kadar bekler,
döngü harcamaz, sayaç değiştirmez ve ops reposuna tek bir uyarı açar (`alert:budget`, başlığı `[budget:day-cap]`;
açıkken yenisi açılmaz). Açık aşamanın (hakemin `setup/stage.json` kilidi, yoksa 0) Kurucu toplamı
`stage_budgets.asama_<k>.founder_usd`'ye ulaşırsa yalnız uyarı gider, oturum açılır. Harcama `pilot-metrics.jsonl`'dan
okunur: CLI'nin bildirmediği oturum kendi freniyle (`budget_usd`; E530'dan önceki satırlar 50 USD), okunamayan bir satır
(kesik, iki satır birleşmiş) 50 USD'lik bir oturum sayılır; okunamayan bir şey harcamayı hiç düşürmez. Kapalı kalır:
iki tavanı birden adlandırmayan ya da ayrıştırılamayan politika, aşama taşımayan bir kilit ya da okunamayan metrik
dosyası koşuyu uyarıyla HALT'a alır; GitHub'a ulaşılamaması kesintidir (bekleyişle). Hakemin `policy.json`'u
`session_cap_usd` ve `day_cap_usd`'yi yazmadan başlatıcı oturum açmaz (canlı politikada ikisi de yok; bir kez,
E492'nin `ETKINLESTIRME` 9. adımı gibi: `d['constitutional'].update(session_cap_usd=15, day_cap_usd=100)`).
Uyarıları `seed/founder/alert.py` operatörün `gh` girişiyle `--ops` reposuna (varsayılan `Okan-wqm/snowball-ops`,
özel) issue olarak açar; ön denetim o girişin repoyu okuyabildiğini sınar, okuyamazsa ya da ad `OWNER/NAME` değilse
koşu başlamaz: hiçbir uyarı boşa gitmez. Uyarının `gh` çağrıları başlatıcının kendi `run`'ından geçer (sınırı aynı);
deneme kipinde (`dry_run`) `gh`'ye hiç gitmez, testler onu ya da sahte bir `run`'ı kullanır, gerçek issue açmaz.

**Çökme ve yeniden açılış** (E505). Başlatıcı bir çökmeden ya da bilgisayarın yeniden açılışından sonra kendiliğinden
sürer; kasıtlı bir durdurmayı hiçbir zaman geçersiz kılmaz. Bir kez, `snowball-mcp` klasöründen, yönetici gerekmeden:

```
C:\Python312\python.exe seed/founder/launch.py --install-service --work F:\snowball-work
```

Geçerli kullanıcıya bir Zamanlanmış Görev (`Snowball Founder launcher`) kaydeder: oturum açılışında ve her 15 dakikada
`<python> -u <snowball-mcp>\seed\founder\launch.py --resume --work <work>`'ü `snowball-mcp` klasöründe çalıştırır;
aynı anda tek örnek, süre sınırı yok (zamanlayıcının üç günlük varsayılanı uzun bir koşuyu öldürürdü), pilde de. Yalnız
kullanıcının oturumu açıkken koşar (Docker ve `gh` girişi onundur); her tetiklemede kısa bir konsol penceresi açılır.
Kaydı görmek: `schtasks /Query /TN "Snowball Founder launcher" /V /FO LIST`; kaldırmak: `--uninstall-service`.

`--resume` ne yapar: kilidi alır, alamazsa başka bir başlatıcı yaşıyordur ve hiçbir şey yapmaz; `RUNNING` yoksa ya da
`STOP` varsa sessizce çıkar (`STOP` varken o koşunun `RUNNING`'i silinir: `STOP` sonra kaldırılsa da eski koşu
dirilmez); Docker ve `gh` yanıt verene kadar en çok 10 dakika bekler (bu arada da `STOP`'a bakar; yanıt gelmezse
`RUNNING` kalır, görevin sonraki tetiklemesi yeniden dener); `HALT` varsa hiçbir şey yapmaz, `RUNNING` kalır (E528);
sonra saklı seçeneklerle ve sayaçlarla kalan döngüleri koşturur ve `pilot-log.md`'ye bir satır yazar:
`başlatıcı yeniden başladı (çökme/yeniden açılış sonrası): kalan N döngü`. Her sürdürme ön denetimden sonra kendini
`RUNNING`'de sayar, biten her döngü sayacı sıfırlar; arada döngü bitmeden üç sürdürmeden sonraki dördüncüsü hiçbir
döngü koşturmadan HALT yazar (E528: her sürdürmede dönen bir çökme, bu olmasa her 15 dakikada ücretli bir oturum
açardı). Ön denetimde kalan sürdürme (Docker, `gh` ya da hakemin özeti yanıt vermiyor) sayılmaz: oturum açmaz, görev
yeniden dener.
Yargılanmamış bir push her başlangıçta olduğu gibi önce yargılanır (E168); Kurucu yarım işini kendi dallarından sürdürür
(E500). Ne yapmaz: `STOP`'u, Kurucu'nun push'suz bitirdiği iki oturumu, HALT'ı ya da Ctrl+C'yi geçersiz kılmaz; komut
satırındaki başka seçenekleri okumaz (koşunun seçenekleri `RUNNING`'dedir); `snowball-founder.env`'i okumaz. Pencereyi
kapatmak durdurma değildir, çökme sayılır ve sürdürülür: durdurmak için `STOP` ya da Ctrl+C. Elle başlatılan bir
başlatıcı koşarken görevin her tetiklemesi kilidi alamaz ve çıkar. Elle başlatma kesilmiş ya da HALT'ta bekleyen bir
koşunun yerine geçer (`HALT`'ı da siler), ön denetimi geçmese de: görev eski koşuyu onun arkasından diriltmez.

**Karne** (E310): kendini geliştirmenin ölçüsü, elle yazılmaz. Başlatıcının döngüsüne bağlı değildir (bir `gh`
takılması döngüyü durdurmasın, yeniden başlatma gerekmesin); her döngüden sonra, başlatıcı çalışırken ayrı bir
kabukta:

```
python seed/founder/scorecard.py --work F:\snowball-work --public docs/karne
```

Yalnız GET ile okur: hakemin `bootstrap-state` artefaktları (zip'i GitHub'ın verdiği özetle denetlenir, özetsiz
artefakt karneyi reddeder; hakemin Sigstore imzası önbelleğe alınır ama karnede doğrulanmaz, `python -m sigstore
verify` doğrular), beynin defteri hakemin son sonucunun başında (tek kayıt noktası; zinciri tohumun `canon.row_hash`'iyle
doğrulanır, kırık zincir karneyi reddeder) ve her yargılanan başta `snowball-tests.json`. `scorecard/self-found-replays.jsonl` (varsa; operatörün, öz-tespiti kapatan testi H'de ve kapanış başında kapsül imajında `--network none` ile çevrimdışı koşusu: `{row_id, h, closing_head, test, red_at_h, green_at_close}`, E315), `pilot-metrics.jsonl` ve `fikir-olcutu.md` salt okunur açılır, yalnız özel karneye girer.
Yazdığı yerler yalnız `scorecard/` ve `--public` ile verilen `docs/karne.json` ile `docs/karne.md`'dir; açık karne
yalnız açık imzalı girdilerden sayılardır. Operatör iki dosyayı commit'ler; `CommittedCardTest` sayfanın json'dan
üretildiğini ve tanımların koddakiyle aynı olduğunu denetler. Düzeltilmiş sütunun dışarıda bıraktıkları
`scorecard_exclusions.json`'dadır, her biri kayıttaki satırıyla; hakemin kuralıyla sütun hep yanındadır.

**Günlük gözlemci raporu** (E537, otonomi planı §6): operatörün izlediği on satır, betikten çıkar, elle yazılmaz;
başlatıcının döngüsüne bağlı değildir:

```
python seed/founder/daily_report.py --work F:\snowball-work [--at 2026-11-04T18:00:00Z] [--offline] [--out F]
```

Pencere `--at`'a kadarki 24 saattir (başlatıcının gün tavanınınki) ve rapor `--at` anındaki kayıttır: ondan sonraki
metrik satırı, günlük döngüsü ve zamanlı satır hiçbir sayıya girmez (dünün raporu bugün de aynı çıkar); `HALT`,
`reports-seen.json`, karne ve boş disk şimdiki hâlleriyle okunur. Salt okunur açar: `pilot-metrics.jsonl`,
`pilot-log.md`, `HALT`, `reports-seen.json`, `scorecard/karne.json` ve penceredeki her oturumun yükleyici kaydı
`logs/<damga>/brain-definitions.json`; `--offline` değilse operatörün `gh` girişiyle iki GET: hakemin
`policy.json`'u (tavanlar, hakemin `policy_of`'uyla) ve `setup/stage.json` (açık aşama). Yazdığı tek dosya
`gunluk-rapor/<tarih>.md` (ya da `--out`). Sayılar başlatıcının kendi kurallarıdır, kopya değil: harcama
`session_spend` (bildirilmeyen maliyet oturumun freniyle), bitiş satırın `end`'i (E528 öncesi satır alanlarından
`session_end` ile; orada fren çıkıştan ayrılamaz), rapor yaşı `report_ages`, "kanıtlandı" karnenin `proved`'u (yalnız
geçen kontrollü sınav). Satırlar planın sırasıyla: oturumlar ve bitişleri, HALT ve kayıt uzlaşması; harcama ve
tavanlar; hedef; büyüme; tahmin; tuzak alarmı; açık raporlar; olaylar; kapsama; kanıt. Sahibin iki ölçüsü
(`sabah-sorulari` 2026-11-03) satır eklemeden girer, ikisi de bu haftanın 7 günü ile önceki 7 gün: büyüme satırında
aynı türden işin emeği (kabul edilen kod push'unun medyan maliyeti, süresi, turu; kayıt daha ince bir iş türü
adlandırmaz), olaylar satırında insan dokunuşu (elle başlatma, `--resume` değil, ve operatörün günlüğe yazdığı dokunuş
başlığı ya da `(insan dokunuşu` işaretli zamanlı satırı; kaydın biçimi tanımsızdır, E277, zamansız başlık
"zamanı okunamayan" diye sayılır). Henüz kurulmamış bir düzenek
(E529 nabız, E532 kanarya ve dışa çıkış, E534 tahmin, E535 iş/geliştirme ayrımı, E536 organlar) kayıt numarasıyla
"ölçülmedi" der, hiçbir zaman 0 demez. Rapor sayı, kimlik ve zaman taşır; Kurucu'nun metnini taşımaz.

**Kayıt uzlaşması.** Günlüğün her `## Döngü <n> — <damga>` bölümü damgasıyla bir metrik satırına eşlenir. Fark
yalnız kayıtlar nedenini söylüyorsa açıklanmış sayılır: metrik dosyasının ilk satırından önce günlüğe yazılmış oturum
(dosya döngü 9'da başladı) ya da kararını kendisi düzelten satır (`corrected_by`, E241). Başka her fark (günlükte
olmayan satır, satırı olmayan oturum, iki kez yazılmış damga, ayrışan karar ya da push, okunamayan satır)
açıklanmamıştır: satır `UZLAŞMADI` der ve o sayılarla kural kurulmaz. Canlı kayıtta (2026-11-05) günlük 123
döngü, metrik 114 döngü satırı; fark 9 metrik öncesi oturum ve 1 düzeltilmiş satırdır, açıklanmayan 0. Planın "7'ye
karşı 12 ret" farkı bunlardır: günlükteki 12 reddin 5'i metrik dosyasından önceki oturumlardadır; "99'a karşı 100"
ise metriğin 8 başlatıcı satırını da döngü sayıyordu (`--at 2026-11-03T03:41:00Z`: günlük 100, metrik 91 döngü
satırı, fark yine 9).

## Tohum teslimi (tohum dönemi, E88)

Canlı beyne yeni tohum (`spec/tohum/**`) yalnız bu yolla girer (`spec/tohum/25` madde 10b); beyne tohum kodu
(`seed/`) gitmez (E150, sahibin yetkisiyle operatör kararı, 2026-11-01). Hakemin imzalı durumu (donmuş spec'ler, ret serileri, açık iddialar, kanıtlanmış kusurlar, rakip artefaktları)
dönemden aynen geçer. Aşağıda `S` `snowball-mcp`'nin teslim edilen commit'i, `D` beyne giden teslim commit'idir.

1. **Kaynak.** `snowball-mcp` `main`'inde CI'ı yeşil bir commit seç (`S`). Dönemin tohum günlüğü satırı
   (`spec/tohum/CHANGELOG.md`) yanıtladığı ya da reddettiği Kurucu raporlarının kimliklerini adlandırır:
   `<rapor kimliği> → <sayfa:satır>` ya da `declined: <neden>` (E342; rapor yanıtsız kalmasın).
2. **Durdur.** Başlatıcı klasörüne `STOP` koy, oturumun bitmesini bekle. Hakem reposunda `control.json`'da
   `"kill_switch": true` yap ve `main`'e it: dönem boyunca hiçbir hakem koşusu başlamaz. Teslimi yalnız Kurucu'nun
   son push'u yargılanmışken yap: ya kabul edilmiştir ya da reddi bir oturuma ulaşmıştır (E385; `seed_update`
   sonucunda ret bloğu yoktur, dönemden hemen önce yargılanan bir ret sonraki oturuma yalnız seri imzası olarak
   ulaşır).
3. **Hakem kopyası** (`25` madde 3): `S`'deki `seed/bootstrap/` → `bootstrap/`, `seed/bootstrap/vectors/` →
   `vectors/`, `spec/tohum/29-tohum-koltuklari.md` → `seats/`, `seed/bootstrap/workflow/bootstrap.yml` →
   `.github/workflows/bootstrap.yml`. Henüz itme. Baytlar git blob'larıyla aynı olmalı (E242): hakem ve beyin
   klonlarını `git -c core.autocrlf=false clone` ile al, her `archive`'ı `git -c core.autocrlf=false` ile koştur
   (`core.autocrlf=true` olan Windows'ta `git archive` LF'yi CRLF'ye çevirir); itmeden önce
   `git diff --cached | tr -cd '\r' | wc -c` 0 olmalı.
4. **Beyne teslim.** Beynin güncel `main`'inin taze klonunda `spec/tohum/`'u `S`'deki ile birebir değiştir, silinen
   dosyalar dahil; başka hiçbir yola dokunma (`spec/INDEX.md` ve `spec/asama-*` teslimle değişemez, E180). Tek
   commit, `main`'e hızlı ileri:
   ```
   git rm -r -q spec/tohum
   git -C <snowball-mcp> -c core.autocrlf=false archive S spec/tohum | tar -x -f -
   git add -A spec/tohum
   git commit -m "Tohum dönemi: snowball-mcp S" && git push origin main
   ```
   Push reddedilirse Kurucu araya girmiştir: yeniden çek, yeniden kur, yeniden it. `D` bu commit'tir; üstünde ikinci bir teslim commit'i olmaz.
5. **Dönem satırı.** `S`'nin `seed/bootstrap/` dizininden:
   ```
   python -m snowball_bootstrap seed-epoch --brain <beyin klonu> --commit D --source <snowball-mcp> --source-commit S
   ```
   Yazılan JSON nesnesini hakem reposunun `setup/summary.json`'ında `seed_epochs` dizisinin sonuna ekle (ilk
   teslimde diziyi aç). `seed_commit` ve `seed_tree_sha256` kurulum tohumudur, dokunma. Beyinde `seed/`
   olmadığından satırın `seed_sha256`'sı `null`'dır. Elle yazma: hash'ler git blob'larından hesaplanır, satır sonundan
   bağımsızdır.
6. **Aç.** 3. ve 5. adımı hakem reposunun `main`'ine it; sonra `"kill_switch": false`, it.
7. **Doğrula.** `gh workflow run bootstrap.yml -R <hakem reposu>`. İmzalı sonuç `kind: seed_update`,
   `verdict: noop`, `head: D` olmalı. Koşu `stop: setup/summary.json: the last seed epoch ...` ile kırmızı biterse
   satır `D`'ninki değildir (yanlış commit, yanlış hash ya da push edilmemiş `D`): düzelt ve yeniden tetikle. Bu
   durma Kurucu'ya hiçbir şey yazmaz.
8. **Devam.** `STOP`'u kaldır, başlatıcıyı başlat; `pilot-log.md`'ye dokunuş satırı yaz (tohum dönemi insan
   dokunuşudur, `27`).

**Hakem ne yapar.** `D` başken teslimin kendisidir: yargılanmaz (`seed_update`, `noop`), altındaki Kurucu commit'i
onun adıyla yeniden yargılanmaz, seri ve rakip artefaktı değişmez. Sonraki Kurucu push'unun son kabul edilmiş
SHA'dan diff'i teslimi taşır; başın `spec/tohum/` ve `seed/` ağaçları son satırdakine eşitken bu yollar Kurucu'nun
değişikliği sayılmaz ve rakibin diff'ine girmez, push kendi türüne göre yargılanır. Kurucu'nun `spec/tohum/` ya da
`seed/`'deki her değişikliği (ekleme ve silme dahil) `seed_modified` ve `seed_tree_mismatch` ile reddedilir. Durum
kaybolursa hakem son dönemin commit'inden başlar (`25` "Durum kaybolursa"). Yeni `bootstrap/` durumun şemasını
değiştiriyorsa önceki şemayı taşıyabilmelidir (`state.migrate`); taşıyamıyorsa teslim yapılmaz. Hakem
`bootstrap_sha256`'yı biçim olarak okur, kendi `bootstrap/` kopyasıyla henüz karşılaştırmaz (E24).

## Etkinleştirme (Aşama 0 → Aşama 1)

Aşama 0 çıkışının (A) parçası kabul edilince yapılan aktarım ve kurulumun ikinci bölümü (`spec/tohum/25a`) bu pilot
için adım adım [ETKINLESTIRME.md](ETKINLESTIRME.md)'dedir: ön koşullar, kimin yaptığı ve neden, komutlar, her adımın
denetimi ve geri dönüşü, sahibin web arayüzü listesi (yazar App'i, ruleset'ler, sırlar). Henüz hiçbir adımı koşulmadı;
tutmayan ön koşullar sayfada ve kayıtta adıyla yazılı (E330).
