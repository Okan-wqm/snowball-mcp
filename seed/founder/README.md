# Kurucu kapsülü ve pilot başlatıcısı

Kurucu (`spec/tohum/24a`) yalnız bu kapsülde çalışır: operatörün GitHub girişi ve Claude yapılandırması içeri
girmez. Kapsülün kökü salt okunur, yetkileri düşürülmüş; beyin her oturumda bellekte taze klonlanır, GitHub tek
evidir. Sınırlar `seed/bootstrap/tests/test_founder_capsule.py`'de sabitlidir.

**Araçlar** (E380, E508). Oturum CLI'ın varsayılan araçlarıyla koşar; yalnız altısı kapalıdır (`--disallowedTools
"RemoteTrigger,CronCreate,CronDelete,CronList,WebFetch,WebSearch"`): `RemoteTrigger` etkisi kapsülden sonra da
sürebilen tek varsayılan araçtır (bulutta bir rutin), Cron araçları süreçle ölür ve hiç kullanılmadı; `WebFetch` ve
`WebSearch` kapsülün ağının etrafından web'e ulaşır (arama dışarıda yapılır, parçacıkları herhangi bir açık repoyu
alıntılayabilir; E508). Başka hiçbir araç daraltılmaz (`--tools`, `--allowedTools` yok); `test_live_cli` girişin kendi
çağrısını sabitli CLI'a uydurma bir jetonla koşturur ve init olayında altısının olmadığını, kalanların durduğunu
denetler. İmaj yeniden kurulunca geçerli olur; talimat değişmez.

**Kapsülün ağı ve kaydı** (E508). `--egress open` (varsayılan) bugünkü gibidir: kapsül Docker'ın varsayılan
köprüsündedir. `--egress contained` kapsülü dışarıya yolu olmayan bir iç Docker ağına (`snowball_capsule`: `--internal`,
IPv6 kapalı, ağ geçidi `gateway_mode_ipv4=isolated`, yani köprüde Docker ana makinesinin adresi yok) koyar; ağın tek
öbür üyesi oturumun aktarıcısıdır (`egress.py`, yalnız stdlib; kapsülün sabitli Python tabanında, kendi kapsayıcısında,
kök salt okunur, yetkiler düşük, kodu ve jetonu salt okunur; yalnız kapsül ağındaki adresini dinler, köprüdeki başka bir
kapsayıcı ona ulaşamaz). Aktarıcı yalnız iki şey taşır: CLI'ın `HTTPS_PROXY`'si için modelin API'sine
(`api.anthropic.com:443`) `CONNECT` tüneli, ve `/git/` ile `/api/repos/` altında yalnız beyin reposunun git
smart-HTTP'si ile REST çağrıları; GitHub jetonunu kendisi ekler, kapsül jeton tutmaz (`https://github.com/` adresleri
`insteadOf` ile aktarıcıya döner). Yukarı akış ana bilgisayarı istekten değil yoldan gelir, yönlendirme izlenmez; ad
büyük-küçük harf ayırmadan, adın sonunda `/` ile eşleşir (izinli bir ad başka bir reponun önü olamaz); boş, `.` ya da
`..` kesimli, kodlanmış `/`, `\`, `.` ya da NUL taşıyan yol reddedilir. Her istek, izinli ya da reddedilmiş, oturumun
`relay/log/egress.jsonl`'ına bir JSON satırıdır (başlık ve gövde asla); reddedilenler okuma algılayıcısıdır, sayıları ve
ilkleri döngünün satırına ve `pilot-log.md`'ye girer. Aktarıcı kalkmazsa oturum açılmaz (kesinti). Var olan ama bunların
biri eksik bir `snowball_capsule` ağı (Docker'ın göstermediği alan da eksik sayılır) reddedilir, kullanılmaz,
değiştirilmez. Ölçüldü (2026-11-02, Docker 28.4): düz bir `--internal` ağdan kapsül, ağ geçidi adresinden Docker ana
makinesinin kendi ad alanında 0.0.0.0'ı dinleyen bir servise **bağlandı**; `isolated` ağ geçidiyle aynı bağlantı
reddedildi.

Döküm artık kapsülün dosyası değildir: giriş CLI'ın akışını kapsayıcının stdout'una yazar, başlatıcı onu kapsülün
bağlamadığı `logs/<damga>/session-<damga>.jsonl`'a yazar ve yanına `sha256sum` biçiminde `.sha256`'sını koyar (döngünün
satırında `transcript_sha256`). Kapsül `/work/logs` olarak yalnız `logs/<damga>/capsule/`'ı görür: akışın kendi kopyası
(`tee`), CLI'ın stderr'i, `brain-definitions.json`, `previous-session.json`. Ölçüldü: kapsülün `sed -i`'si kaydı
değiştiremez; ama kapsülün kullanıcısındaki bir süreç kapsayıcının stdout'una (`/proc/1/fd/N`) yazıp kayda satır
**ekleyebilir** (silemez, değiştiremez). CLI tek bir kapanış `result` olayı yazar; başka bir sayı (`transcript_results`)
raporda adıyla yazılır. Girişin değişmesi imajın yeniden kurulmasını gerektirir: kurulum girişin sha256'sını etikete
yazar (`snowball.entrypoint_sha256`) ve her başlangıç onu çalışma kopyasınınkiyle karşılaştırır; tutmazsa (`--no-build`
ile eski imaj) başlatıcı `RUNNING`'i silip durur.

`contained`'a geçiş operatörün (gizli değerler bu betikçe okunmaz): (1) `snowball-capsule.env`'e yalnız
`CLAUDE_CODE_OAUTH_TOKEN=...`, `snowball-relay.env`'e yalnız `GITHUB_TOKEN=...` (bugünkü beyin-yalnız jeton) yaz; kapsül
dosyasında `GITHUB_TOKEN` varsa giriş 64 ile durur; (2) başlatıcıyı `--egress contained` ile yeniden başlat (imaj
yeniden kurulur; ağ yoksa yukarıdaki gibi açılır; Docker 28'den eskisi `isolated`'ı bilmez ve ağ reddedilir).
`test_founder_capsule` `ContainmentProbeTest`'i (`SNOWBALL_EGRESS_PROBE=<ad öneki>`) başlatıcının kendi argv'siyle
gerçek Docker'da ölçer: 2026-11-02'de Docker 28.4'te 71 denemenin 69'u engellendi (DNS 7, TCP 11, UDP 1 ağ katmanında,
ana makinenin kendi servisi dahil; aktarıcıda 50 yasak hedef, hepsi kayıtta `deny`), ikisi geçti: modelin API'sine TLS
el sıkışması ve beynin git ucu (uydurma jetona GitHub 401); köprüdeki bir kapsayıcıdan aktarıcının iki adresi de yanıt
vermedi, ana makinenin servisi verdi (deneme kör değil). Aynı ölçüm düz `--internal` ağla kırmızıdır (servise bağlanır).
Sabitli CLI 2.1.293 uydurma bir jetonla aktarıcının arkasında yalnız `api.anthropic.com:443`'ü istedi. Bilinen sınırlar:
ağ katmanında düşen istekler (DNS, doğrudan adres) yol olmadığından kayda girmez; kapsülün kendi OAuth jetonuyla API'nin
sunucu tarafı araçları (web arama ve getirme) aktarıcının okuyamadığı tünelden çağrılabilir (TLS'i açmadan kapanmaz,
ölçülmedi); beyin reposunun fork ağındaki nesneler beyin yolundan okunabilir; paket kayıtları kapalıdır (kapsülde
`pip`/`npm install` çalışmaz).

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
altısından biri `tool_denied:`, başka ad `tool_not_allowed:` ile düşer; boyut ve sayı sınırları tek sabittir
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

**Klasör.** Pilotun her şeyi tek klasördedir (varsayılan `F:\snowball-work`); silinince pilot iz bırakmaz:

| Yol | Ne |
|---|---|
| `snowball-founder.env` | `--egress open`: `GITHUB_TOKEN` (yalnız beyin reposu, Contents: Read and write) ve `CLAUDE_CODE_OAUTH_TOKEN` (`claude setup-token`); operatör yazar, yalnız kapsül okur |
| `snowball-capsule.env` | `--egress contained` (E508): yalnız `CLAUDE_CODE_OAUTH_TOKEN`; kapsülün tek gizli değeri |
| `snowball-relay.env` | `--egress contained`: yalnız `GITHUB_TOKEN`; yalnız aktarıcının kapsayıcısına bağlanır |
| `aquaculture_platform/` | hedef klonu, kapsüle salt okunur |
| `referee/` | hakemin son imzalı sonucu (`result.json`), Kurucu okur |
| `vec/` | vektörlerin girdileri, kapsüle `/vec` olarak salt okunur (E244): `cases.json` (her veri vakasının `id`, `purpose`, `cmd`, `stdin`, `fixture` ve `changed` alanları) ve fikstürler; beklenen değer yok. Her oturumdan önce hakem reposunun `main`'indeki `vectors/`'ten, hakemin kendi `vectors.founder_inputs`'uyla yeniden kurulur |
| `logs/` | her oturumun klasörü `logs/<damga>/` (E508): `session-<damga>.jsonl` (döküm, `stream-json`, kapsülün stdout'undan) ve `.sha256`'sı; `capsule/`, kapsülün `/work/logs`'u (akışın kopyası, CLI'ın stderr'i, `brain-definitions.json`: beynin yüklenen ve düşen ajan ve skill tanımları, E450; `previous-session.json`); `relay/` (`contained`): aktarıcının o oturumda koşan kodu ve `log/egress.jsonl`'ı |
| `pilot-log.md` | operatörün raporu: her döngüde push, hakem kararı, yeni defter satırları ve bildirimler, maliyet satırının ne olduğu, beynin açık raporları ve yaşları |
| `pilot-metrics.jsonl` | her döngünün ölçümü: push, karar, nedenler ve **sahipleri** (hakemin kendi kuralıyla: Kurucu / rakip / hakem), rakibin kanıtlanmış bulguları, eski çürütmeler, yeni bildirimler, süre, maliyet, hakemin yeniden inceleme sayısı; sonucun neye bağlanacağı (E313): `prompt_sha256`, `image_id`, `model`, `cli_version` ve `model_served` (dökümün `init` olayı), `seed_commit`, `spec_tohum_tree`, `rival_config`, `target_sha`, `timed_out`. Her başlatıcı başlangıcı ayrı bir `kind: intervention` satırıdır (argümanlar, imaj, prompt hash'i). `prompt_sha256` imajın kendisinin: kurulum imajı içindeki prompt'un sha256'sıyla etiketler (`snowball.prompt_sha256`), `--no-build` eski imajı koşturur, etiketsiz imajda `null`; çalışma kopyasınınki `checkout_prompt_sha256` |
| `cost-pending.jsonl` | henüz yazılamamış maliyet satırları (aşağıda) |
| `reports-seen.json` | başlatıcının her beyin raporunu ilk gördüğü an: raporun yaşı |
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
