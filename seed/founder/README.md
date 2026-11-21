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
`claude`'dan önce `brain_defs.py` beyin klonunun `HEAD`'indeki `agents/` ve `skills/` ağaçlarını git nesnelerinden
(`ls-tree`, `cat-file`; dosya sisteminden değil, hiçbir bağ beynin dışına götüremez) okur, denetler ve
`$CLAUDE_CONFIG_DIR/brain-plugin`'e bir eklenti yazar; CLI onu `--plugin-dir` ile yükler, ayar kaynakları kapalı kalır
(CLAUDE.md, ayarlar, hook'lar, MCP, çıktı stilleri hiçbir kaynaktan yüklenmez). Eklentinin ajanları ve skill'leri
`brain:<ad>` adını alır, CLI'ın kendi ajanlarının yerine geçemez. Eklentide yalnız `.claude-plugin/plugin.json`
(`{"name": "brain"}`), `agents/` ve `skills/` vardır; her ajan dosyası ve her `SKILL.md` denetlenen alanlardan yeniden
yazılır (CLI denetleneni okur), skill'in kendi dosyaları bayt bayt ve kipleriyle kopyalanır.

| Kaynak (beyin) | Biçim |
|---|---|
| `agents/<ad>.md` | ön bilgi `name`, `description`, isteğe bağlı `tools` (`Read, Grep` gibi virgüllü adlar) ve `model` (`sonnet`, `opus`, `haiku`, `inherit` ya da bir kimlik); gövde ajanın talimatı |
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
oturumun klasöründe `brain-definitions.json`'dır: beynin başı, yüklenen her tanımın adı, `loaded_as`'ı, kaynak blob'un
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
| `logs/` | oturum dökümleri (`stream-json`); her oturumun klasöründe `brain-definitions.json`, beynin yüklenen ve düşen ajan ve skill tanımları (E450), `targets.json`, hedeflerin `targets[]` sırasıyla `[{id, kind, base_sha, unit_candidates}]`'ı, adsız (E571, E577), ve `operating.json`, hakem reposundaki `policy.json`'un o oturum için okunan `operating`'i: `{operating: {…}}`, alan yoksa `{}`, okunamaz ya da `26c` biçiminde değilse (yalnız yedi anahtar, sayı `{value, band}`) dosya yok ve operatöre uyarı (E577), ve aynı okumadan `policy.json`, hakem reposundaki dosya bayt bayt: katı JSON nesnesi değilse, 256 KiB'tan büyükse, sır deseni ya da hedef adı taşıyorsa dosya yok ve operatöre yalnız sınıfı adlandıran uyarı (`29v`, E588), ve `loop-runs.jsonl`, hakem reposundaki `loop.yml`'un `main`'deki en yeni üç koşusu, işleri ve özet satırları, operatörün `gh` girişiyle okunur; okunamayan `null`, hiçbir zaman boş değil (`29y`, E596), ve `lessons.json`, oturumun açıldığı beyin başındaki defterin yürürlükteki `lesson` satırlarının en yeni 100'ünün `row_id`'si ve iddiası, dışarıda kalanların sayısıyla; başlatıcı yalnız okur, `recheck`'i koşturmaz, defter okunamazsa dosya yok ve operatöre uyarı (`26g`, E610), ve `mirror.json`, ölçüm aynası (`mirror.py`, sahip kararı 2026-11-19, E647): model sürümü başına oturum, push, karar, ret nedeni, Kurucu oturumlarının CLI'deki tahmini maliyeti (`cli_estimate`; hakem, rakip ve inceleme koşuları içinde değil) ve onun kabul başına payı, oturum süresinin ortancası; her aktarımın ardından döngü koşularının sonucu ve kırmızının işi ve nedeni; 14 günde birden çok satırda ya da koşuda görülen ret ve kırmızı sınıfları (satır ve koşu sınıf başına bir kez); aktarılmış hakem ağacının (bu döngünün `/vec` için indirilen arşivinden) ve spec'in boyutu; son 20 oturumun ajan çağrıları ve oturumlar arası bekleme; tohum dönemi Z'den (E677, `tohum/26h`) son 20 oturumun `session_time`'ı (`wall_s` metrik satırının dakikasından, transkriptten `api_s`, `blocked_on_own_checks_s` heartbeat yöntemiyle, çağrılar üzerinden toplam (eşzamanlı çağrılar ayrı sayılır, `wall_s`'i aşabilir; sonuç olayı olmayan oturumda `null`), kovaları adıyla kotanın başı ve sonu: `seven_day_overage_included`, `seven_day`, `five_hour`) ve ilk dilimin `path`'i (`path_mfs_left`: kabul edilmiş manifestin `done_mf`'inde olmayan P1 MF'leri; `organ_merges_copy` `null`, nedeni yazılı). Diskteki kayıtlar, o arşiv ve tohumun P1 tablosu okunur; tek ağ çağrısı başlatıcının kabul edilmiş SHA'daki `snowball-tests.json`'u `gh api` ile okumasıdır, başarısızsa `path`'in `null`'ı olur; her bölüm kaynağını ve penceresini söyler, hesaplanamayan `null` ve nedeni; yalnız olgu, öğüt yok. Ayna başarısızsa dosya yok ve operatöre yalnız sınıfı adlandıran uyarı; oturum yine başlar |
| `pilot-log.md` | operatörün raporu: her döngüde push, hakem kararı, yeni defter satırları ve bildirimler, maliyet satırının ne olduğu, beynin açık raporları ve yaşları; ayrı bir satırda **CEVAPSIZ (operatör)**: kimliği beynin tuttuğu tohumun hiçbir `spec/tohum/CHANGELOG*.md`'sinde geçmeyen açık raporlar, yaşlarıyla (operatör onları ne yanıtlamış ne reddetmiş, E527; tam kimlik eşleşmesi: `seed-040` `seed-0401`'le adlanmış sayılmaz; adlanmış ama dosyası onu adlandıran en son commit'ten beri değişmiş rapor da cevapsızdır, E552: başvuru brain'in git geçmişidir, commit zamanı değil; günlükler ya da geçmiş okunamazsa `okunamadı`, hiçbir zaman "cevapsız" değil); ayrı bir satırda **WIP dalları (operatör)**: beynin `wip/` dallarının bulguları, `wip_memory_off_main:<dal>` ve `wip_unmerged_behind:<dal>` (`15` 9, E592; hakemin nedeni değil), bir okuma başarısızsa `okunamadı`, hiçbir zaman "yok" değil. Yalnız operatörün: bu klasör kapsüle bağlanmaz, Kurucu'ya hiçbiri ulaşmaz |
| `pilot-metrics.jsonl` | her döngünün ölçümü: push, karar, nedenler ve **sahipleri** (hakemin kendi kuralıyla: Kurucu / rakip / hakem), rakibin kanıtlanmış bulguları, eski çürütmeler, yeni bildirimler, açık raporların ve cevapsızların sayısı (`reports_open`, `reports_unanswered`, E527; okunamayınca `null`), `wip` (WIP satırının bulguları, okunamayınca `null`, E592), süre, maliyet, hakemin yeniden inceleme sayısı; sonucun neye bağlanacağı (E313): `prompt_sha256`, `image_id`, `model`, `cli_version` ve `model_served` (dökümün `init` olayı), `seed_commit`, `spec_tohum_tree`, `rival_config`, `target_sha`, `timed_out`. Her başlatıcı başlangıcı ayrı bir `kind: intervention` satırıdır (argümanlar, imaj, prompt hash'i). `prompt_sha256` imajın kendisinin: kurulum imajı içindeki prompt'un sha256'sıyla etiketler (`snowball.prompt_sha256`), `--no-build` eski imajı koşturur, etiketsiz imajda `null`; çalışma kopyasınınki `checkout_prompt_sha256`; `context_sha256` imajın bütün kurulum dosyalarınınki (E506): kurulum imajı `snowball.context_sha256` ile de etiketler (`BUILD_FILES`'ın her dosyası, LF ile, sıralı `<yol>\0<sha256>\n` satırlarının sha256'sı), çalışma kopyasınınki `checkout_context_sha256`; ikisi farklıysa başlatıcı bunu söyler: yalnız prompt değil, değişmiş bir araç ya da yükleyici de görünür |
| `cost-pending.jsonl` | henüz yazılamamış maliyet satırları (aşağıda) |
| `reports-seen.json` | başlatıcının her beyin raporunu ilk gördüğü an: raporun yaşı |
| `epoch-delivery.json` | yalnız bir tohum teslimi sürerken: `deliver_epoch.py`'nin o teslimde yaptıkları (`S`, `STOP`'u kendisi mi koydu, `kill_switch` commit'leri, `D`, hakem commit'i, doğrulama koşusu); teslim bitince silinir, duran teslim onunla sürer (E526) |
| `STOP` | oluşturulursa başlatıcı o adımdan sonra durur |
| `launcher.lock` | çalışan başlatıcının özel işletim sistemi kilidi (E505): klasörde aynı anda tek başlatıcı. Süreç nasıl biterse bitsin (çökme, öldürme, yeniden açılış) işletim sistemi bırakır; elle silinmez |
| `RUNNING` | süren koşu (JSON, E505): seçenekleri (`--work`, `--cycles` ve `--resume` dışında), kalan döngü, push'suz oturum sayısı, başlangıç ve son güncelleme. Ön denetim geçince yazılır, her döngüden sonra güncellenir; koşu `STOP`'la, push'suz iki oturumla, zaman aşımıyla, girdiler yenilenemeyince, Ctrl+C ile ya da son döngüsüyle bitince silinir. Çökme, öldürme ya da yeniden açılış onu bırakır ve `--resume` o koşuyu sürdürür. Gizli bilgi yazılmaz |
| `scorecard/` | karnenin önbelleği ve özel kopyası (E310): `results/` hakemin imzalı sonuçları ve Sigstore paketleri (yalnız eklenir, özetiyle denetlenir), `manifests.jsonl`, `ledger-counts.jsonl` (her yargılanmış başta defterin satır sayısı: öz-tespitin (b) penceresi, E315), `karne.json` ve `karne.md` (maliyet ve keşif dahil). Kapsüle hiç bağlanmaz |

**Çalıştırma** (operatörün `gh` girişi ve Docker gerekir):

```
python seed/founder/launch.py --cycles 3
```

Her döngü: hakemin son sonucunu indir → vektör girdilerini yenile → bir Kurucu oturumu → beyin değiştiyse hakemi
tetikle ve bekle (zamanlayıcısı seyrek ve düzensiz çalışır, E32: beklemek güvenilmez) → maliyet satırı → `pilot-log.md`'ye yaz. Push'suz iki oturumda, zaman aşımında,
`STOP` dosyasında ya da girdiler yenilenemeyince (eski ya da eksik girdiyle oturum açılmaz) durur.
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
`--budget-usd` bütçe değil, kaçak frenidir. Döngülerin değerlendirmesi (ne buldu, ne kaçırdı, öğrendi mi) repoda
`docs/pilot-gunlugu.md`'dedir; her döngüden sonra güncellenir.

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
`RUNNING` kalır, görevin sonraki tetiklemesi yeniden dener); sonra saklı seçeneklerle kalan döngüleri koşturur ve
`pilot-log.md`'ye bir satır yazar: `başlatıcı yeniden başladı (çökme/yeniden açılış sonrası): kalan N döngü`.
Yargılanmamış bir push her başlangıçta olduğu gibi önce yargılanır (E168); Kurucu yarım işini kendi dallarından sürdürür
(E500). Ne yapmaz: `STOP`'u, push'suz iki oturumu, zaman aşımını, girdisizliği ya da Ctrl+C'yi geçersiz kılmaz; komut
satırındaki başka seçenekleri okumaz (koşunun seçenekleri `RUNNING`'dedir); `snowball-founder.env`'i okumaz. Pencereyi
kapatmak durdurma değildir, çökme sayılır ve sürdürülür: durdurmak için `STOP` ya da Ctrl+C. Elle başlatılan bir
başlatıcı koşarken görevin her tetiklemesi kilidi alamaz ve çıkar. Elle başlatma kesilmiş bir koşunun
yerine geçer, ön denetimi geçmese de: görev eski koşuyu onun arkasından diriltmez.

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

## Tohum teslimi (tohum dönemi, E88)

Canlı beyne yeni tohum (`spec/tohum/**`) yalnız bu yolla girer (`spec/tohum/25` madde 10b); beyne tohum kodu
(`seed/`) gitmez (E150, sahibin yetkisiyle operatör kararı, 2026-11-01). Hakemin imzalı durumu (donmuş spec'ler, ret serileri, açık iddialar, kanıtlanmış kusurlar, rakip artefaktları)
dönemden aynen geçer. Aşağıda `S` `snowball-mcp`'nin teslim edilen commit'i, `D` beyne giden teslim commit'idir.

**Tek komut** (E526). Aşağıdaki sekiz adımı `deliver_epoch.py` yapar; operatör yalnız `S`'yi seçer ve dönemin
günlük satırını (1. adım) `S`'ye koyar:

```
python seed/founder/deliver_epoch.py S --dry-run      # S'yi çözer, CI'ını okur, planı yazar; hiçbir şey yazmaz
python seed/founder/deliver_epoch.py S [--summary-edit edit.json] [--note "İçerik: ..."]
```

İlk uyuşmazlıkta durur (çıkış 2) ve neyin kaldığını söyler. Reddettikleri: `S` `main`'de değilse ya da `ci.yml`'ın
`S`'deki son push koşusu tamamlanmış ve yeşil değilse (1); başlatıcının kilidi (`launcher.lock`) `--wait` içinde
boşalmazsa, Kurucu'nun son push'unun (başlatıcının maliyet commit'leri ve önceki teslimler altta kalan) kararı yoksa
ya da reddi hiçbir oturumun okumadığı bir retse (E385: bir döngünün oturumu o başta başlamış olmalı,
`pilot-metrics.jsonl` `brain_before`) (2); `kill_switch` zaten açıksa ve onu bu araç açmadıysa (2); bir klonda
izlenmeyen ya da yok sayılan bir dosya varsa (2026-11-02'de hakem klonundaki bir `__pycache__` kopyayla sahnelendi),
sahnelenen bir girdi `S`'nin blob'u ve kipi değilse ya da sahnelenen diff'te bir CR baytı varsa (E242; baytlar `git
archive`'dan, `core.autocrlf=false` ile, her biri `ls-tree`'nin blob'una karşı) (3, 4); `D`'nin `spec/tohum` ağacı
`S`'ninki değilse ya da `D` başka bir yola dokunuyorsa (4); `seed-epoch` satırı `D`'yi adlandırmıyorsa,
`setup/summary.json` ya da `control.json` aracın yeniden yazdığı biçimde (girinti 2, tek satır sonu) değilse, ya da
`--summary-edit`'in bir alanı `from`'daki değerde değilse (5); imzalı sonuç `seed_update`/`noop`/`D` değilse (7).
`--summary-edit` `targets[]` girdilerinin alanlarını ve özetin üst düzey alanlarını değiştirir: `{"targets": {"copy":
{"unit_candidates": {"from": [...], "to": [...]}}}, "fields": {"spec_exception": {"from": null, "to": {...}}}}`; `from: null`
alanın henüz olmadığıdır, `to` null olamaz, `seed_epochs` ve `targets` `fields`'la değişmez (E564: sahibin istisnası ve
taahhüdü onları okuyan tohumun dönemiyle gelir, `26c`). Özette `drift` varsa 5. adım `drift.hashes.vectors_sha256` ve `seats_sha256`'yı sahnelenen `vectors/` ve `seats/`'ten, önyükleme hakeminin denetiminin kullandığı `treehash.dir_hash`'le yeniden hesaplar (3. adım ikisini de yeniden sahneler; eski değer kalsaydı sonraki koşu `vectors_hash_mismatch` ile dururdu, `25`, `01c`), `drift.hashes.constitutional_sha256`'yı da hakem klonunun o anki `policy.json`'undan `01c`'nin tarifiyle, önyükleme hakeminin RFC 8785 `canon.canonical`'ıyla (AA dönemi): anayasal bölümde bir kayan nokta varsa tarifin değeri yoktur ve teslim 5. adımda durur (`policy.json`'u `main`'de düzelt, aynı `S` ile yeniden koştur); eski ve yeni değer commit iletisinde, günlükte ve dokunuş satırındadır; `drift` yoksa özet ona dokunmaz. `seed-epoch` `S`'nin kendi `seed/bootstrap/`'ından (git nesnelerinden yazılır, bayt
kodu bırakılmaz) koşar. Her adım ya zaten yapılmışsa atlanır ya da uyuşmazlıkta durur: aracın yaptığı
`<work>/epoch-delivery.json`'dadır, duran bir teslim aynı `S` ile yeniden koşturulunca kaldığı yerden sürer (başka bir
`S` reddedilir). `kill_switch` açılmadan duran bir koşu klasörü bulduğu gibi bırakır (koyduğu `STOP` kalkar); sonra
duran koşu `STOP`'u ve `kill_switch`'i bırakır. `STOP`'u yalnız kendisi koyduysa kaldırır; başlatıcıyı başlatmaz.
`snowball-founder.env`'i okumaz. GitHub'a yazımlar operatörün `gh` girişiyle gider (başlatıcınınki gibi git'in `gh`
kimlik yardımcısı ve `gh workflow run`). Testler `tests/test_deliver_epoch.py`'dedir.

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
   `.github/workflows/bootstrap.yml`, `seed/security-ledger.jsonl` → `setup/security-ledger.jsonl` (genesis okur,
   `29o`; E541). Henüz itme. Baytlar git blob'larıyla aynı olmalı (E242): hakem ve beyin
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

**AA döneminin operatör işleri** (seed-082, seed-083, seed-084; tohum sayfası değil). Teslimden önce, hakem reposunun
`main`'inde, `deliver_epoch.py` koşmadan:
1. `policy.json`: `constitutional.confidence_level` `0.9` → `"0.900000"`, `constitutional.stage_params.fix_acceptance_min`
   `0.8` → `"0.800000"` (dosyada noktalı başka sayı kalmasın, `01c`); `18a`'nın Gözcü yaprakları
   (`constitutional.regression_freeze` `{min_merges: 50, window_days: 30, revert_rate: "0.020000", min_reverts: 2}`,
   `constitutional.gate_rules.soft_freeze_limit` 2, `containment_freeze` 2) ve `18b`'nin performans bölümü
   (`performance.windows.measure` 14 ve öbür satırları; kesirler altı ondalıklı dizgi). Aşama 1'in zorunlu yolları
   (`29v`) eksikse döngü temiz durur.
   Politikayı yeniden yazmak ve teslim aynı oturumda yapılır: arada koşan bir hakem işi yeni `policy.json`'u bayat
   `constitutional_sha256`'ya karşı okur.
2. `setup/summary.json` `drift`: `writer_app_permissions` bu teslimde **eklenmez** (beynin bugünkü sıkı biçimi onu
   "not a field of this shape" diye reddeder); `operator_checked_at` ile birlikte sonraki bir operatör dokunuşunda
   eklenir. `visibility` canlı tabanda zaten vardır. `constitutional_sha256`'yı teslimin 5. adımı yeni `policy.json`'dan
   yeniden hesaplar (hakemin `canonical`'ı); kayan nokta kaldıysa teslim kill switch'ten ve beyne `D`'den önce, `--dry-run`'da
   da durur. Teslim dışında elle, hakem reposunun kökünde, `snowball-mcp`'nin `seed/bootstrap`'ı `PYTHONPATH`'teyken
   (asla `json.dumps` ile değil):
   ```
   python -c "import json,hashlib; from snowball_bootstrap.canon import canonical; print(hashlib.sha256(canonical(json.load(open('policy.json', encoding='utf-8'))['constitutional'])).hexdigest())"
   ```
3. `operator_checked_at` sahibin kurulu App'ler denetimini bekler (E668).
4. Yazar App'inin etkinlik akışındaki login'i (`<slug>[bot]`) ilk canlı döngüden önce kopyanın akışında bir kez
   doğrulanır.

**Sert duruştan sonra yeniden başlatma** (seed-085 h, `26i`, `28a`). Operatör yeniden başlatma satırını elle yazmaz:
```
python seed/founder/restart_row.py <hakem checkout'u> --target <id> --hard-stop <row_hash> --stage <n> [--note "..."]
```
Satırı sayacın son `row_hash`'ine zincirler ve önyükleme hakeminin `canon.row_hash`'iyle hash'ler; kırık sayaçta hiçbir
şey yazmaz. Commit ve push operatöründür (insan dokunuşu).

## Etkinleştirme (Aşama 0 → Aşama 1)

Aşama 0 çıkışının (A) parçası kabul edilince yapılan aktarım ve kurulumun ikinci bölümü (`spec/tohum/25a`) bu pilot
için adım adım [ETKINLESTIRME.md](ETKINLESTIRME.md)'dedir: ön koşullar, kimin yaptığı ve neden, komutlar, her adımın
denetimi ve geri dönüşü, sahibin web arayüzü listesi (yazar App'i, ruleset'ler, sırlar). Henüz hiçbir adımı koşulmadı;
tutmayan ön koşullar sayfada ve kayıtta adıyla yazılı (E330).
