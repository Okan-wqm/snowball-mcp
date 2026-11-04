# Etkinleştirme: Aşama 0'dan Aşama 1'e (bu pilot)

`spec/tohum/25a`'nın ve dayandığı sayfaların (`25`, `01a`, `01b`, `07`, `14`, `26c`, `29o`, `29p`, `asama-0/08`,
`asama-0/10a`, `asama-1/00`, `asama-1/03`, `asama-1/13`) bu pilot için yürütülebilir hâli. Aşama 0 çıkışının (A)
parçası kabul edildiği an başlanır. Bu sayfa yazılırken hiçbir adımı koşulmadı (2026-10-31, kayıt E330); salt okunur
`gh` ve WSL komutları canlı repolarda denendi. Bugün tutmayan ön koşullar aşağıda adıyla yazılı. Sonraki aktarımlar
(P1, P2, Aşama 1 çıkışı) 1–4. adımlardır, oyuncak itilmeden ve `--toy` verilmeden (`25a` 1, `asama-1/13`; E378); her yeni yazma hedefi 5–7'yi
tekrarlar; mühürlü depo Aşama 4'tedir, burada yok.

**Kim.** *Operatör*: WSL'de git ve python, PowerShell'de `gh` (Okan-wqm girişi). *Sahip*: Okan-wqm hesabıyla GitHub
web arayüzü; App, ruleset ve sır işleri onundur ([sahip listesi](#sahip-listesi)). *Kurucu*: yalnız 8. adımda,
başlatıcıyla; ona bu sayfadan hiçbir şey söylenmez, ne yapacağını spec'ten okur (E304).

**Hedef ürün reposu dokunulmaz.** `Okan-wqm/aquaculture_platform`'a hiçbir şey itilmez, ayarı değişmez, App
kurulmaz; yalnız kimliksiz okunur. Yazma hedefleri oyuncak ve kopyadır (`25` 10, 10a).

| Ad | Repo |
|---|---|
| beyin | `Okan-wqm/snowball-rehearsal-brain` |
| hakem | `Okan-wqm/snowball-rehearsal-referee` (önyükleme hakemi `bootstrap.yml`; aktarımdan sonra `loop.yml` da) |
| hedef (salt okunur) | `Okan-wqm/aquaculture_platform` |
| oyuncak, `targets[].id` `toy` | `Okan-wqm/snowball-rehearsal-toy` (ad spec sessiz) |
| kopya, `targets[].id` `copy` | `Okan-wqm/snowball-rehearsal-copy` (ad spec sessiz) |

**Kabuklar.** `PS>` PowerShell; `WSL$` Ubuntu (`wsl -d Ubuntu`). İçe aktarma Windows'ta koşamaz: Sigstore'un pinli
kümesi yalnız Linux tekerleğidir (`requirements/sign.txt`, E116); WSL'nin ext4'ü harf duyarlıdır ve `core.autocrlf`
kapalıdır (E130, E242, E289). Her yeni pencerede önce:

```
PS> $H = 'Okan-wqm/snowball-rehearsal-referee'; $TS = 'Okan-wqm/snowball-rehearsal-toy', 'Okan-wqm/snowball-rehearsal-copy'
WSL$ E=~/etkinlestirme; SHA=<2. adımdaki brain_sha>; ID=https://github.com/Okan-wqm/snowball-rehearsal-referee/.github/workflows/bootstrap.yml@refs/heads/main
```

## Başlamadan önce doğru olması gerekenler

| # | Koşul | Bugün (2026-10-31) |
|---|---|---|
| Ö1 | (A) kabul: imzalı sonuç `kind: exit`, `verdict: accepted`, `exit.transferable: true` (`asama-0/10`); denetimi 2. adımda | beyinde `exit-request.json` yok |
| Ö2 | Kurulumun birinci bölümünden kalanlar: oyuncak ve kopya repoları, kopyada Actions kapalı, özette kopyanın `identifiers`'ını taşıyan `targets[]`, `control.json`'un eksik alanları, #durustluk için sahibin kararı ([Ek A](#ek-a-birinci-bölümden-eksik-kalanlar)) | hiçbiri yok (E284, E287, E294) |
| Ö3 | Hakemin `bootstrap/`'ındaki tohum araçları (yalnız tohum dönemiyle değişir) ve beynin döngüsü: K1 `import` `25a` 1–2'yi taşır; K2 `control` döngü arayüzünü taşır (`29p`); K3 `stage-open` var; K4 döngünün işleri her `targets[]` hedefinde bir devir koşar, girdileri `29s`'teki gibi (değişken yok). Denetimi 2. adımda; tutmayana el yaması yapılmaz | K1 ve K3 snowball-mcp `gaps/activation-tooling-3` dalında (E370–E372, ikinci tur E374–E379, E388–E389, üçüncü tur E402–E406, dördüncü E411–E417, beşinci E470–E475, altıncı E478–E485, yedinci E494, E496–E498 `gaps/stage1-ready`'de; E100, E275, E331 kapandı: içe aktarma çalışma ağacına hiç dokunmaz, yeni `main`'i git nesneleriyle kurar, git'in nesne denetiminden geçirir ve okuduğu `main`'e kirayla iter (E470, E479, E482), `stage-open` kökü `sha256:<kök>` özetiyle doğrular, klonları, aktarımı, istisnayı, hakemin satırını ve merge'leri bağlar, PASS satırının biçimi `26d`'de, P1'in (A)'sı ve aktarımı aynı tohumla olur, kilit yokken Aşama 0'ın yargısı değişmez), K2 snowball-mcp `main`'inde (`e7b3b24`, E282); üçü de hakemde yok, tohum dönemi bekliyor; K4 yok, beyin `8c57160` (E332) |
| Ö4 | Sahip 5. adım için ulaşılabilir (web arayüzü, yaklaşık yarım saat) | — |
| Ö5 | 0. adım bir kez yapılmış | yapılmadı |
| Ö6 | Oyuncağa ekilecek canlı prova fikstürleri (`22a`, `asama-0/01` D8; `26f`): onlarsız D8 canlı koşmaz, (B)'nin #geri-alma'sı ölçülemez, PASS yazılamaz | yok. Yeri, biçimi ve kuralları `26f`'te (E499): hakemin ikinci prova sırrı, o aktarım satırına bağlı; operatör aktarımdan sonra ve 7. adımdan önce tohumun `drill-fixtures` komutuyla üretir (6a), her aktarımda yeniden; komut snowball-mcp `tools/drill-fixtures` dalında, hakemin `bootstrap/`'ına bir tohum dönemiyle gelir |

## Adımlar

**0. WSL hazırlığı** (operatör, bir kez, istenen an · içe aktarma imzayı Sigstore ile doğrular, E116).

```
WSL$ sudo apt-get update && sudo apt-get install -y python3.12-venv
WSL$ git config --global credential.helper "/mnt/c/Program\ Files/Git/mingw64/bin/git-credential-manager.exe"
WSL$ git config --global user.name "<Windows'taki user.name>" && git config --global user.email "<Windows'taki user.email>"
WSL$ mkdir -p ~/etkinlestirme
```

*Denetim:* `python3 -m venv /tmp/v && rm -rf /tmp/v` hatasız. *Geri dönüş:* `rm -rf ~/etkinlestirme`;
`git config --global --unset credential.helper`.

**1. Durdur ve kill switch'i aç** (operatör · `25a` 1: aktarım kill switch açıkken yapılır).

```
PS> New-Item -ItemType File F:\snowball-work\STOP
PS> gh run list -R $H -L 5 --json workflowName,status,databaseId --jq '.[] | [.workflowName, .status, .databaseId] | @tsv'
```

Başlatıcı oturumu bitirip durana ve listedeki her satır `completed` olana kadar bekle. Sonra:

```
WSL$ cd $E && for r in referee brain toy; do git -c core.autocrlf=false clone -q https://github.com/Okan-wqm/snowball-rehearsal-$r.git $r; done
WSL$ python3 - $E/referee/control.json <<'EOF'
import json, sys
p = sys.argv[1]; d = json.load(open(p, encoding="utf-8")); d["kill_switch"] = True
open(p, "w", encoding="utf-8").write(json.dumps(d, indent=2) + "\n")
EOF
WSL$ git -C $E/referee commit -q -am "Kill switch: etkinleştirme (tohum/25a satır 1)" && git -C $E/referee push -q origin main
```

Oyuncak boş klonlanır (uyarı beklenir). *Denetim:* `PS> gh api "repos/$H/contents/control.json" -H "Accept: application/vnd.github.raw"`
`"kill_switch": true` gösterir. Bundan sonra `bootstrap.yml`'ın saatlik koşusu "Kill switch" adımında kırmızıdır:
beklenen (E117). *Geri dönüş:* aynı betikle `False`, it; `STOP`'u sil.

**2. (A)'nın sonucu ve kapı denetimi** (operatör · imzalı sonuç olmadan aktarım olmaz; araç `25a`'yı taşımıyorsa ya da
döngü bir devir koşamıyorsa aktarmak yalnız geri alınacak bir dokunuştur, `25a` "Başarısızlık"). `<RUN>` Kurucu'nun
çıkış isteğini yargılayan `bootstrap.yml` koşusudur (`pilot-log.md`; `gh run list -R $H --workflow bootstrap.yml -L 10`).
İndirme dizini yoksa yaratılır, varsa önce silinir.

```
PS> gh run download <RUN> -R $H -n bootstrap-state -D F:\snowball-work\etkinlestirme\a
WSL$ mkdir -p $E/a && cp /mnt/f/snowball-work/etkinlestirme/a/result.json /mnt/f/snowball-work/etkinlestirme/a/result.json.sigstore.json $E/a/
WSL$ python3 - $E/a/result.json <<'EOF'
import json, sys
r = json.load(open(sys.argv[1], encoding="utf-8")); e = r.get("exit") or {}
print(r["kind"], r["verdict"], e.get("transferable"))
for k in ("brain_sha", "referee_tree_sha256", "toy_tree_sha256", "owner_exception"): print(k, e.get(k))
EOF
```

Beklenen `exit accepted True`, 40 haneli `brain_sha`, iki 64 haneli hash; `owner_exception` ya `None` ya da sahibin
istisnasıdır (E294, insan dokunuşu, `27`). `brain_sha`'yı `SHA` yap, ikisini `pilot-log.md`'ye yaz. Sonra Sigstore
(`bootstrap.yml`'ın pinli kümesi, lisans kapısından geçer) ve araç, hakemin canlı `bootstrap/`'ının kopyasından:

```
WSL$ git -C $E/brain fetch -q origin && git -C $E/brain cat-file -e $SHA^{commit} && echo "SHA klonda"
WSL$ rm -rf $E/arac && cp -r $E/referee/bootstrap $E/arac && python3 -m venv $E/sig
WSL$ $E/sig/bin/pip download -q --require-hashes --only-binary=:all: --no-deps -d $E/sigw -r $E/arac/requirements/sign.txt
WSL$ cd $E/arac && python3 -m snowball_bootstrap licenses --root $E/referee --wheels $E/sigw
WSL$ $E/sig/bin/pip install -q --no-index --find-links $E/sigw --require-hashes --only-binary=:all: --no-deps -r $E/arac/requirements/sign.txt
```

Kapı denetimleri (`$E/arac`'ta; ilk dördü bugün `YOK` basar):

```
WSL$ python3 -m snowball_bootstrap control --help | grep -q -- --job && echo "K2 tamam" || echo "K2 YOK (E282)"
WSL$ python3 -m snowball_bootstrap stage-open --help >/dev/null 2>&1 && echo "K3 tamam" || echo "K3 YOK (E331)"
WSL$ git -C $E/brain grep -q 'reason="cycle_not_wired"' $SHA -- referee/loop/job.py && echo "K4 YOK (E332)" || echo "K4 tamam"
WSL$ git -C $E/brain grep -qE 'vars\.(BRAIN_REPO|LOOP_TARGET|CANARY_MODEL|CLAUDE_CLI_SHA512)\b' $SHA -- referee/.github/workflows/loop.yml && echo "K4 YOK (29s, E490)" || echo "K4: girdiler 29s'teki gibi"
WSL$ rm -rf $E/prova && mkdir $E/prova && git clone -q --bare $E/referee $E/prova/referee.git && git clone -q --bare $E/toy $E/prova/toy.git
WSL$ python3 -m snowball_bootstrap import --result $E/a/result.json --bundle $E/a/result.json.sigstore.json --identity "$ID" --sigstore-python $E/sig/bin/python --brain $E/brain --referee $E/prova/referee.git --toy $E/prova/toy.git
WSL$ git -C $E/prova/referee.git ls-tree -r --name-only main | grep -cE '^(bootstrap/|\.github/workflows/bootstrap\.yml$|control\.json$|setup/summary\.json$)'
WSL$ git -C $E/prova/referee.git show main:setup/imports.jsonl | tail -n 1 | python3 -c "import json,sys; print(sorted(json.load(sys.stdin)))"
WSL$ git -C $E/prova/referee.git show main:.github/workflows/loop.yml | grep -oE '(secrets|vars)\.[A-Za-z_][A-Za-z0-9_]*' | sort -u
```

K1'in ilk yarısı, prova: içe aktarma yerel iki çıplak kopyaya iter (GitHub'a değil) ve 0 ile biter; korunanlar
`main`'dedir (`bootstrap/`, `.github/workflows/bootstrap.yml`, `control.json`, `setup/summary.json`); son satırın
anahtarları `brain_sha, prev_hash, referee_tree_sha256, result_sha256, row_hash, stage, toy_tree_sha256, ts` (`26c:37`,
zincirli). Komut hiçbir çalışma ağacını okumaz ve yazmaz: hakem reposunu kendi geçici dizinine çıplak klonlar, beyin
commit'ini oraya git'in nesne denetimiyle getirir, yeni `main`'i git nesneleriyle kurar (E470; dört şüpheci turunda dosya
sistemi kopyası çürütüldü, E479). `referee/` ya da oyuncak ağacında `26c`'nin reddettiği bir ad, bir dosya sisteminin
başka ad okuduğu bir ad (sonda nokta ya da boşluk, aygıt adı, `~` ve rakam), Windows'un tutamadığı bir ad (`|?*"<>`, 260
karakterden uzun yol; E484), 255 bayttan uzun tek ad (E496), git'in kendi okuduğu bir ad (`.git`, `.gitattributes`, `.gitmodules`, harf duyarsız ve
HFS+ biçimiyle; E478, E479), oyuncakta `.github` (E480), korunan bir girdiyi harf duyarsız gösteren ya da harf duyarsız
tek ad olan iki ad, bağ ya da alt modül, hiçbir nesne yazılmadan `stop: …` ile durur; `main` bir korunan adı başka harfle taşıyorsa da
(`Bootstrap/`, `.GitHub/`). Son komut `loop.yml`'un adlandırdığı sırları ve değişkenleri basar; beyin `8c57160`'ta:
`secrets.CLAUDE_CODE_OAUTH_TOKEN`, `secrets.WRITER_APP_ID`, `secrets.WRITER_APP_PRIVATE_KEY`, `vars.TARGET_OWNER`.
Beyin `b099103`'te (2026-11-01) bunlara ek olarak `vars.BRAIN_REPO` ve `vars.LOOP_TARGET` (seed-041'in varsayımları) ile
`vars.CANARY_MODEL` ve `vars.CLAUDE_CLI_SHA512` (seed-042'nin varsayımları) vardır. `29s`'i taşıyan tohum döneminden sonra
`vars.BRAIN_REPO` ya da `vars.LOOP_TARGET` kaldıysa K4 tutmaz: döngünün beyni `bootstrap.json` `brain_repo`, hedefleri
özetin `targets[]`'ıdır ve bir koşu iki hedefe de hizmet eder; operatör bu iki değişkeni yazmaz (her devirde değişken
değiştirmek dokunuştur, E490). `CANARY_MODEL` ve `CLAUDE_CLI_SHA512` de yazılmaz (seed-042, E499): kanaryanın modeli
`bootstrap.json` `rival.model`, CLI'nin pini hakemin `bootstrap/requirements/claude-cli/` kilididir (`29s`). Başka bir ad varsa 3. adıma geçme, sahibe sor (spec sessiz). İkinci yarısı: kill switch kapalıyken aynı komut
durur (`25a` 1):

```
WSL$ rm -rf $E/prova && mkdir $E/prova && git clone -q --bare $E/referee $E/prova/referee.git && git clone -q --bare $E/toy $E/prova/toy.git
WSL$ git clone -q $E/prova/referee.git $E/prova/w && sed -i 's/"kill_switch": true/"kill_switch": false/' $E/prova/w/control.json && git -C $E/prova/w commit -qam "prova: kill switch kapalı" && git -C $E/prova/w push -q origin main
WSL$ python3 -m snowball_bootstrap import --result $E/a/result.json --bundle $E/a/result.json.sigstore.json --identity "$ID" --sigstore-python $E/sig/bin/python --brain $E/brain --referee $E/prova/referee.git --toy $E/prova/toy.git; echo "çıkış $?"
```

Beklenen `stop: …` ve `çıkış 2`. *Karar:* K1, K2 ve K4 tamamsa 3. adım; K3 yoksa 1–8 yapılır, 9 bekler. Biri eksikse
dur ve `pilot-log.md`'ye yaz. *Geri dönüş:* `rm -rf $E/prova`; beklenecekse 1. adımın geri dönüşü.

**3. İçe aktar** (operatör · `25a` 1–2: hakem kodu yalnız aktarımla değişir, `01a`; oyuncağın içeriği (A)'da
yargılanandır). Komut iki reponun `main`'ine zorlamadan, okuduğu `main`'e kirayla (`--force-with-lease`) iter: önce
oyuncak, sonra hakem (`25a` 1: her itmenin göndereceğini denetleyen git nesne denetimi dahil her denetim geçtikten sonra;
başka daldaki ya da `main`'in zaten tuttuğu eski bir nesne durdurmaz, E494; `main` arada ilerlediyse
ya da geri alındıysa itme reddedilir, hakemde hiçbir şey değişmez ve ret uzak `main`'in o anki başını adlandırır, E482).
`--toy ""` gibi boş bir repo adı durdurur (E498); `stage-open`'ın `--referee`'si checkout'un tepesidir (E497).

```
WSL$ cd $E/arac && python3 -m snowball_bootstrap import --result $E/a/result.json --bundle $E/a/result.json.sigstore.json --identity "$ID" --sigstore-python $E/sig/bin/python --brain $E/brain --referee https://github.com/$H.git --toy https://github.com/Okan-wqm/snowball-rehearsal-toy.git
PS> gh workflow disable loop.yml -R $H
WSL$ git -C $E/referee pull -q --ff-only && git -C $E/toy pull -q --ff-only && git -C $E/referee rev-parse HEAD && git -C $E/toy rev-parse HEAD
```

*Denetim* (iki `cmp` `AYNI`):

```
WSL$ git -C $E/brain -c core.quotePath=false ls-tree -r --format='%(objectname) %(path)' $SHA -- referee/ | sed 's# referee/# #' | sort > $E/a/hakem-beklenen
WSL$ git -C $E/referee -c core.quotePath=false ls-tree -r --format='%(objectname) %(path)' HEAD | grep -vE ' (bootstrap/|seats/|vectors/|setup/|policy\.json$|control\.json$|bootstrap\.json$|\.github/workflows/bootstrap\.yml$)' | sort > $E/a/hakem-gelen
WSL$ cmp $E/a/hakem-beklenen $E/a/hakem-gelen && echo AYNI
WSL$ git -C $E/brain -c core.quotePath=false ls-tree -r --format='%(objectname) %(path)' $SHA -- tests/fixtures/toy-repo/ | sed 's# tests/fixtures/toy-repo/# #' | sort > $E/a/oyuncak-beklenen
WSL$ git -C $E/toy -c core.quotePath=false ls-tree -r --format='%(objectname) %(path)' HEAD | sort > $E/a/oyuncak-gelen
WSL$ cmp $E/a/oyuncak-beklenen $E/a/oyuncak-gelen && echo AYNI
```

Hakemin her dosyası imzalı beyin commit'indeki `referee/` blob'udur (`loop.yml` `.github/workflows/`'a düşer), operatör
dosyaları önceki `main`'inkidir, yeni operatör satırı yalnız `setup/imports.jsonl`'dadır; oyuncak `tests/fixtures/toy-repo/`'nun
blob'larıdır (o ağacın hash'i `exit.toy_tree_sha256`). `gh workflow disable` itmenin hemen ardından: `loop.yml`
`main`'e girince saatlik zamanlayıcısı kayda geçer, kill switch açıkken her saat kırmızı koşardı; 7. adıma kadar
kapalıdır (spec sessiz; `25` 9'un yolu). Komut durursa (`stop: …`, çıkış 2) itilmiş hakem commit'i yoktur; mesajı ve
nedeni `pilot-log.md`'ye yaz. Oyuncak itilip hakem itmesi reddedildiyse mesaj oyuncağın commit'ini ve hakemin uzak
`main`'ini adlandırır; komutu yeniden koşmak ağacı zaten taşıyan oyuncağa dokunmaz.

**4. Kaydet, döngüyü kapalı tut** (operatör · `25a` 1–2).

İki SHA'yı (`AKTARIM`, `OYUNCAK_MAIN`) `pilot-log.md`'ye dokunuş satırı olarak yaz (aktarım insan dokunuşudur; sayaç
satırı `imports.jsonl`'dadır). *Denetim:*

```
PS> gh api "repos/$H/actions/workflows" --jq '.workflows[] | [.path, .state] | @tsv'
PS> gh api repos/Okan-wqm/snowball-rehearsal-toy/commits/main --jq .sha
```

`bootstrap.yml active`, `loop.yml disabled_manually`; oyuncağın `main`'i `OYUNCAK_MAIN`. *Geri dönüş:*
`git -C $E/referee revert --no-edit <AKTARIM> && git -C $E/referee push -q origin main` (spec'in tek yolu; geçmiş
yeniden yazılmaz). Oyuncağın `main`'i geri alınmaz; yeni aktarım üstüne yeni commit iter.

**5. Sahibin işi** (sahip · `25a` 3–4, `25` 6–7: yazar App'i, ruleset'ler ve sırlar operatörün elinde değildir).
Operatör sahibe 2. adımın provasındaki sır adlarını verir; sahip [sahip listesi](#sahip-listesi)'nin S4–S7'sini yapar, App ID'yi ve
App'in kurulum sayfasındaki repo listesini operatöre söyler (App ID gizli değildir). *Geri dönüş:* sahip kurulumu askıya
alır ya da kaldırır (Settings → Applications → Installed GitHub Apps → Configure → Suspend / Uninstall), özel anahtarı
App sayfasında siler, sırları ve ruleset'leri siler.

**6. Değişkeni yaz, sahibin işini doğrula** (operatör · hakem reposunun ayarı operatöründür, `01a`; `25a` 3–6: genesis
aynı olguları API'den okur ve tutmazsa sert durur, `29o`; bu okuma sert duruştan önce yakalar).

```
PS> gh variable set TARGET_OWNER -b Okan-wqm -R $H
PS> foreach ($T in $TS) { "== $T"; foreach ($B in 'brain/state', 'brain/integration', 'main', 'baska') { "-- $B"; gh api "repos/$T/rules/branches/$B" --jq '.[] | [.type, (.parameters // {} | tostring)] | @tsv' }; gh api "repos/$T/rulesets" --jq '.[].id' | ForEach-Object { gh api "repos/$T/rulesets/$_" --jq '[.name, .target, .enforcement, (.conditions | tostring), (.bypass_actors | tostring)] | @tsv' } }
PS> gh api repos/Okan-wqm/snowball-rehearsal-copy/actions/permissions --jq .enabled
PS> gh api repos/Okan-wqm/snowball-rehearsal-copy/actions/runs --jq .total_count
PS> gh api repos/Okan-wqm/snowball-rehearsal-toy/actions/workflows --jq .total_count
PS> gh secret list -R $H; gh variable list -R $H
PS> gh api "repos/$H/actions/permissions/workflow" --jq .default_workflow_permissions
```

Beklenen, iki hedefte de: `brain/state` yalnız `deletion`, `non_fast_forward`; `brain/integration` yalnız `deletion`,
`non_fast_forward`, `pull_request` (`required_approving_review_count` 0, `allowed_merge_methods` `["merge"]`),
`required_status_checks` (`strict_required_status_checks_policy` true, `do_not_enforce_on_create` true,
`[{"context":"snowball-gate","integration_id":<App ID>}]`); `main` yalnız `deletion`, `non_fast_forward`, `update`;
`baska` (`brain/` dışı herhangi bir dal) `creation`, `update`, `deletion`, `non_fast_forward`. Beş ruleset `active`:
`brain-state` ve `brain-integration`'ın bypass listesi `[]`; `main`, `brain-disi` ve `etiket`'inki (`target` `tag`)
yalnız `{"actor_id":5,"actor_type":"RepositoryRole","bypass_mode":"always"}` (Repository admin). Kopyada Actions
`false` ve koşu `0`, oyuncakta iş akışı `0`; sırlar 3. adımın adları; değişken `TARGET_OWNER Okan-wqm`; varsayılan
izin `read`. **App beyanı** (`25a` 5): operatör kurulumu API'den listeleyemez (`user/installations` App belirteci
ister); sahibin söylediği listeyi `pilot-log.md`'ye yaz ("kurulu App: snowball-rehearsal-writer; yalnız oyuncak ve
kopya"). Özete değil: alanı yok (`26c:31-35`, `29o`), bilinmeyen alan kapalıya düşer (`26c`); genesis aynı kümeyi
`app_scope` olarak denetler. Tutmayan satırı sahip düzeltir, 6 yeniden. *Geri dönüş:*
`gh variable delete TARGET_OWNER -R $H`; gerisi salt okuma.

**6a. Prova fikstürleri** (operatör · `25a` 7, `26f` "Canlı prova fikstürleri", E499: aktarımdan sonra, etkinleştirmeden
önce; her aktarım yeni bir küme alır, kırmızı bir (B)'de yanan küme yeniden kullanılmaz). Taslaklar operatörün özel
dosyasıdır, hiçbir repoda değil (komut repo içindeki taslağı da çıktıyı da reddeder): `[{"cause": …, "patch": …}]`;
her `patch` oyuncağın `main`'inde `git diff`'in yazdığı, var olan tek dosyayı yerinde değiştiren diff (dosya eklemez,
silmez, adını ya da kipini değiştirmez); üç nedenden (`build_break`, `lint_regression`, `test_regression`) eşit sayıda;
dosyası bir güvenlik yolunda (yolunda `policy.json`'un bir `security_keywords`'ü, ya da oyuncağın `safety_paths`'ı)
ve merge'ü beklenen bir adayın dosyası (beyin `candidates/toy/`'da `decision: merge`) değildir. Komut docker ister
(WSL'de Docker Desktop tümleşimi); Node imajı oyuncağın `.nvmrc`'sinin sürümü, özetiyle:

```
WSL$ git -C $E/brain fetch -q origin && git -C $E/toy fetch -q origin && git -C $E/referee pull -q --ff-only
WSL$ P=/mnt/f/snowball-work/private; V=$(cat $E/toy/textkit/.nvmrc); docker pull -q node:$V-bookworm-slim
WSL$ NODE=node:$V-bookworm-slim@$(docker image inspect node:$V-bookworm-slim --format '{{index .RepoDigests 0}}' | cut -d@ -f2)
WSL$ cd $E/arac && python3 -m snowball_bootstrap drill-fixtures --referee $E/referee --toy $E/toy --brain $E/brain --catalog $P/prova-taslak.json --out $P/prova-fiksturleri-<aktarım satırının row_hash'i>.b64 --node-image "$NODE"
```

Komut aktarım satırını hakem checkout'unun commit'inden okur ve ona bağlar (`stage-open`'ın bağı, E471); oyuncağın
`main`'i ve beynin `brain_sha`'daki oyuncak fikstürü o satırın `toy_tree_sha256`'sı olmalıdır. Her taslağı `26f`'in
kurallarıyla denetler, nedenini oyuncağın kendi araçlarıyla ölçer (temiz ağaç bir kez, sonra her ekim;
`npm ci --ignore-scripts` ağı olan tek adım, gerisi `--network none`), tutmayanı taslağın sırasıyla adlandırıp
reddeder ve hiçbir şey yazmaz; geçerse değeri yalnız `--out`'a (dosya yoksa) yazar, yalnız neden sayılarını, değerin
sha256'sını ve boyutunu basar. Değeri `loop.yml`'un adlandırdığı adla hakemin sırrı olarak yaz (3. adımın listesindeki fikstür sırrı;
ad spec'te değil, `loop.yml`'dadır), sha256'yı `pilot-log.md`'ye dokunuş satırı olarak yaz (kayda yalnız o girer):

```
PS> cmd /c "gh secret set <fikstür sırrının adı> -R $H < F:\snowball-work\private\prova-fiksturleri-<…>.b64"
PS> gh secret list -R $H
```

`cmd /c`'nin `<`'ü dosyanın baytlarını olduğu gibi verir (PowerShell 5.1'in borusu satır sonu ekler). *Denetim:* sır
listede, güncelleme anı şimdi; komutun bastığı `value_sha256` dosyanın sha256'sı (`sha256sum`). *Geri dönüş:*
`gh secret delete <ad> -R $H`; özel dosya kalır, hiçbir repoya girmez ve kırmızı bir (B)'den sonra kullanılmaz.

**7. Etkinleştir: oyuncağın devirleri, sonra kopyanın genesis'i** (operatör · `25a` 7, `asama-0/08` devir sırası
1–6; ilk durum ve canlı kanıt).

```
WSL$ git -C $E/referee pull -q --ff-only
WSL$ python3 - $E/referee/control.json <<'EOF'
import json, sys
p = sys.argv[1]; d = json.load(open(p, encoding="utf-8")); d.update(kill_switch=False, loop_schedule=False, merge_paused=False)
open(p, "w", encoding="utf-8").write(json.dumps(d, indent=2) + "\n")
EOF
WSL$ git -C $E/referee commit -q -am "Etkinleştirme: kill switch kapalı, zamanlayıcı kapalı, merge açık (tohum/25a satır 7)" && git -C $E/referee push -q origin main
PS> gh workflow enable loop.yml -R $H
```

`merge_paused: false` spec sessiz: `25a` 7 adlandırmaz, eksikse `true`'dur ve (B)'nin #merge'ü olmaz (`26c`). Zamanlanmış
koşu artık `paused` ile yeşil biter (`29p`). Her devir için tek tetik, bitene kadar bekle, denetle; `$R` tek bir sayı olmalı:

```
PS> $t0 = (Get-Date).ToUniversalTime().AddSeconds(-30).ToString('yyyy-MM-ddTHH:mm:ssZ'); gh workflow run loop.yml -R $H --ref main; Start-Sleep 15
PS> $R = gh run list -R $H --workflow loop.yml --event workflow_dispatch --created ">=$t0" --json databaseId --jq '.[0].databaseId'; gh run watch $R -R $H --exit-status
PS> foreach ($T in $TS) { "== $T"; gh api "repos/$T/commits/main" --jq .sha; gh api "repos/$T/git/matching-refs/heads/" --jq '.[] | [.ref, .object.sha] | @tsv' }
PS> $S = gh api repos/Okan-wqm/snowball-rehearsal-toy/git/ref/heads/brain/state --jq .object.sha; gh api "repos/Okan-wqm/snowball-rehearsal-toy/git/trees/$($S)?recursive=1" --jq '.tree[] | select(.type == "blob") | .path'
```

Sıra (`asama-0/08`): 1 oyuncakta genesis ve kesim; 2 iyi aday merge, dört kötü aday kendi nedeniyle ret; 3 nöbetçi
yeşil; 4 geri alma provası, üç `cause`; 5 `llm.call` kanaryası; oyuncağın 1–5'i yeşilse 6 kopyada genesis
`targets[].base_sha`'da. Hangi devrin koşacağını döngü seçer; operatör yalnız tetikler ve denetler. Her tetik özetin
`targets[]`'ındaki iki hedefte, dizinin sırasıyla birer devirdir (`29s`, E490): değişken ya da girdi yoktur; kopyanın devri
oyuncağın 1–5'i yeşil olana kadar hiçbir şey yazmaz ve koşuyu kırmızı yapmaz. *Denetim, her koşudan
sonra:* koşu yeşil; iki hedefin `main`'i değişmedi (`OYUNCAK_MAIN`, kopyanın `base_sha`'sı; #main); dallar yalnız `main`
ve `brain/` altında; 1'den sonra oyuncağın `brain/integration`'ı ilk merge'e kadar `OYUNCAK_MAIN`'de, `brain/state`
ağacında defter, kök zinciri ve `status.md` var; her devirde `status.md` yenilenmiş (#durum; okumak için ağaçtaki yolla
`gh api "repos/<T>/contents/<yol>?ref=brain/state" -H "Accept: application/vnd.github.raw"`); 6'dan sonra kopyanın
`brain/integration`'ı ilk merge'e kadar `base_sha`'da. Kırmızı koşu ya da `status.md`'de sert duruş: [Başarısızlık](#başarısızlık).
*Geri dönüş:* [Başarısızlık](#başarısızlık).

**8. Kopyanın adayları, merge'ler, PASS** (Kurucu, sonra operatör · `25a` 8, `asama-0/08` 7–9: kopyada ilk gerçek
merge). snowball-mcp `main` klonunun kökünden, `README`'deki gibi:

```
PS> Remove-Item F:\snowball-work\STOP
PS> C:\Python312\python.exe seed\founder\launch.py --cycles 3
```

Kurucu yalnız `candidates/<kopya>/`'yı değiştiren bir push yapar; başlatıcı önyükleme hakemini tetikler, sonuç `accepted`
olmalı (`pilot-log.md`). Olunca `STOP`'u yeniden koy; kopyanın devirlerinden önce operatör denetler (`asama-0/10a:41-42`;
E333'ü taşıyan tohum döneminden önce tohum bunu kendisi reddetmiyor, sonra da bu denetim ikinci göz olarak kalır):

```
WSL$ git -C $E/brain fetch -q origin && N=$(git -C $E/brain rev-parse origin/main)
WSL$ git -C $E/brain diff --quiet $SHA $N -- referee/ && echo "referee/ aynı" || echo "DUR: referee/ değişti"
WSL$ git -C $E/brain diff --name-only $SHA $N | grep -vE '^(candidates/|targets/|reports/|founder-ledger\.jsonl$|spec/tohum/|seed/)'
```

`referee/ aynı` ve ikinci komut hiçbir satır basmaz (Kurucu'nun kayıtları yargılanmaz, `classify.is_founder_record`;
`spec/tohum/` ve `seed/` yalnız tohum dönemiyle gelir, Kurucu'nun oradaki değişikliği zaten `seed_modified`'dır). Sonra
7. adımın tetik ve denetim komutlarıyla kopyanın devirlerini (iyi aday merge, kötü aday ret, nöbetçi yeşil) ve son devri
koştur: PASS satırı oyuncağın `brain/state` defterinde, kopyanın genesis ve merge satırlarının hash'leriyle (#pass).
`asama-1/00` ve `03` onu "iki hedefin `brain/state`'inde" ister; bu sayfa makine tanımı olan `asama-0/10a`'yı izler
(E334). *Geri dönüş:* push reddedildiyse Kurucu'nundur (olağan akış); `referee/` değiştiyse kopyanın devri tetiklenmez,
`pilot-log.md`'ye yazılır, Başarısızlık; kırmızı devir: [Başarısızlık](#başarısızlık).

**9. Kilidi aç** (operatör · `25a` 9, `asama-0/10a` "Kilidin açılışı": Aşama 1 ancak PASS'ten sonra; K3 gerekir).

`$E/arac` 2. adımdaki gibi hakemin canlı `bootstrap/`'ının kopyasıdır (K3'ü getiren tohum döneminden sonra yeniden
kopyala). Kopyanın `brain/state`'i küçük bir klondadır (yetim dal). Her hedefin son kökünü imzalayan Sigstore paketini
`stage-open` o hedefin `brain/state` başından okur: döngü onu kök satırının yanında tutar,
`.brain/chain/<kök>.sigstore.json` (`<state_root>` `01a`'nın `.brain/`'i: defter `.brain/ledger.jsonl`, kökler
`.brain/chain/root.jsonl`; başka bir `state_root` adlandıran profil durdurur; `26d`, E414, E417); operatör paket indirmez.
Kimlik döngünün iş akışınındır. Önce Aşama 1'in rakip freni politikaya girer (`asama-1/10`: 15 USD; `18a`, `26e`, E492):
önyükleme hakemi kilitten sonraki ilk push'ta `stage_budgets.asama_1.rival_usd`'yi okur ve onsuz durur; `stage-open` onu
`--referee` klonunun commit'indeki `policy.json`'dan okur ve onsuz kilidi açmaz. Anahtar zaten varsa bu iki satır atlanır:

```
WSL$ git -C $E/referee pull -q --ff-only && python3 -c "import json,sys; p=sys.argv[1]; d=json.load(open(p,encoding='utf-8')); d['constitutional']['stage_budgets'].setdefault('asama_1',{})['rival_usd']=15; open(p,'w',encoding='utf-8').write(json.dumps(d,indent=2)+'\n')" $E/referee/policy.json
WSL$ git -C $E/referee commit -q -am "Aşama 1'in rakip freni (asama-1/10, tohum/26e)" && git -C $E/referee push -q origin main
WSL$ git -C $E/referee pull -q --ff-only && git -C $E/toy fetch -q origin
WSL$ rm -rf $E/kopya-durum && git -c core.autocrlf=false clone -q --no-checkout --single-branch --branch brain/state https://github.com/Okan-wqm/snowball-rehearsal-copy.git $E/kopya-durum
WSL$ cd $E/arac && python3 -m snowball_bootstrap stage-open --referee $E/referee --toy $E/toy --copy $E/kopya-durum --identity "https://github.com/Okan-wqm/snowball-rehearsal-referee/.github/workflows/loop.yml@refs/heads/main" --sigstore-python $E/sig/bin/python
WSL$ cat $E/referee/setup/stage.json
WSL$ grep referee_tree_sha256 $E/referee/setup/imports.jsonl | tail -n 1 | tr -d '\n' | sha256sum
```

`--result` 3. adımda içe aktarılan imzalı (A) sonucudur (baytlarının sha256'sı son aktarım satırının
`result_sha256`'sı). `stage-open` 0 ile biter ya da `stop: …` ve `çıkış 2` ile durur, nedeni adıyla: Aşama 0'ın
aktarım satırı yok, `--result` o satırın sonucu değil, özet bir oyuncak ve bir kopya hedefi adlandırmıyor, bir klonun
ilk defter satırı o hedefin genesis satırı değil (`kind: genesis`, hakemin kendi `events` satırı, `payload.target`;
E416) ya da son genesis satırı o hedefin değil (kopyada `base_sha` da) veya son aktarım satırını adlandırmıyor (E376,
E377, E411), son genesis'ten sonra PASS satırı yok ya da iki tane (oyuncak defterinde öneri olmayan, `payload`'ı
`stage: 0`, `verdict: "PASS"` olan `events` satırı; önerilmiş bir kopyası sayılmaz, E405), hakemin kendi satırı değil
(`proposed_by` yok, `null` da değil; `trust` `verified` ya da `observed`, `derivation` ilk üçten; E388, E404, E416),
son genesis ile kendisi arasında oyuncağın merge satırı yok ya da sayacın son aktarım satırını adlandırmıyor
(`payload.import_line_sha256`, E405), kopyanın son genesis'ini ve ondan sonraki merge satırlarını adlandırmıyor
(`payload.copy_genesis_row_hash`, `payload.copy_merge_row_hashes`: her biri kopyanın bir `kind: merge` satırı; E376,
E405), sahip istisnasını imzalı sonuçtaki gibi taşımıyor (`payload.owner_exception`, E379), defter `.brain/` altında
yok ya da bir profil başka bir `state_root` adlandırıyor ya da düzenli dosyada tek bir JSON nesnesi değil (E417, E472,
E481), sayaç ya da özet `--referee` klonunun commit'inde yok (çalışma ağacı okunmaz: önce `main`'i çek; E478), o
commit'in `policy.json`'u `stage_budgets.asama_1.rival_usd`'yi adlandırmıyor (E492), bir zincir kırık, son kök
defterin uçları değil, kök paketi `brain/state`'te yok (E414), paket satırın Rekor girdisi değil ya da girdi kökü
kaydeden bir Rekor v1 `hashedrekord` değil (v2 gövdesi de; kök `sign --rekor-version 1` ile imzalanır, E406, E415),
Sigstore `sha256:<kök>`'ü reddetti (E375) ya da kilit zaten var (E371). Kural ve alanlar Kurucu'nun okuduğu `spec/tohum/26d`'dedir (E404). Durursa itme, `pilot-log.md`'ye yaz.

`setup/stage.json` tam olarak `{stage: 1, pass_row_sha256, toy_state_head, copy_state_head, import_line_sha256}`
(`26c:39`); iki baş `gh api repos/<T>/git/ref/heads/brain/state --jq .object.sha` ile, `import_line_sha256` son
komutla (LF'siz satır, `29o`) aynı. İncele ve it; sonra zamanlayıcıyı aç:

```
WSL$ git -C $E/referee add setup/stage.json && git -C $E/referee commit -q -m "Aşama 1 kilidi (stage-open, tohum/25a satır 9)" && git -C $E/referee push -q origin main
WSL$ python3 - $E/referee/control.json <<'EOF'
import json, sys
p = sys.argv[1]; d = json.load(open(p, encoding="utf-8")); d["loop_schedule"] = True
open(p, "w", encoding="utf-8").write(json.dumps(d, indent=2) + "\n")
EOF
WSL$ git -C $E/referee commit -q -am "Döngünün zamanlayıcısı açık (tohum/25a satır 9)" && git -C $E/referee push -q origin main
```

`pilot-log.md`'ye dokunuş satırı (`stage-open` insan dokunuşudur, `27`; satırın biçimi tanımsız, E277). Kopyanın
aynalaması açılır: günde bir `sh ~/etkinlestirme/aynala.sh` ([Ek A](#ek-a-birinci-bölümden-eksik-kalanlar); yer spec
sessiz, en dar seçim operatörün makinesi, kopyada Actions kapalı). Sonra `STOP`'u kaldır, başlatıcıyı başlat (Aşama 1).
*Denetim:* önyükleme hakeminin sonraki sonucu Aşama 1 tablosunu okur; `loop.yml`'ın zamanlanmış koşuları duraklamadan
geçer. *Geri dönüş:* `loop_schedule` `False`, it; `stage.json` commit'ini `git revert`; aynalamayı durdur.

## Başarısızlık

`25a` "Başarısızlık": 1., 7. ya da 8. satır kırmızıysa sistem sert durur. Operatör, sırası `25a`'nınki (arşiv, silme,
yeniden aktarım; E540):

1. `STOP` yerinde; kill switch açık (1. adımın betiği, it) ve `PS> gh workflow disable loop.yml -R $H`. Ruleset'lerin
   kapalı kaldığı pencere ancak bundan sonra açılır: yazar App'ini yalnız `loop.yml`'ın işleri kullanır;
2. **Arşiv.** İki hedefte her `refs/heads/brain/` dalının başı önce `pilot-log.md`'ye, sonra aynı hedef repoda
   `refs/tags/arsiv/$N/<dal>` etiketine (`<dal>` tam adıyla, ör. `brain/state`). `$N` başarısız aktarım satırının
   `row_hash`'idir: hakemin `main`'inde `setup/imports.jsonl`'un son aktarım satırı, geri almadan önce okunur (sıra
   numarası olmaz: geri alma satırı sayaçtan da çıkarır, sonraki aktarım aynı sıraya düşer). Etiketi `etiket`
   ruleset'inin bypass'ı olan Repository admin rolü iter (S7); yazar App'i etiket yazamaz (`29i` `refs`). Nesneler
   GitHub'da erişilebilir kalır, başarısız koşunun zinciri ve Rekor kökleri denetlenebilir; yerel arşiv de kalır;
3. **Silme.** Sahip S8'in ilk yarısını yapar, operatör her `brain/` dalını siler (`brain/state`, `brain/integration`,
   `brain/c/*`, `brain/drill/*`, `brain/revert/*`; genesis `brain/state`'i yetim dal olarak açar, `01a`, `24`, ve GitHub
   var olan ref'i yeniden yaratmaz, `POST git/refs`; kalan bir `brain/c/<cid>` kesimden sonra 422'dir), sahip S8'in
   ikinci yarısını yapar; operatör iki ruleset'in kurallarının geri geldiğini `rules/branches` ile denetler (kapalı
   kalan ruleset'i genesis `state_rules_missing` ya da `integration_rules_missing` ile durdurur, bypass aktörünü hiç
   okumaz: Bypass list'e kimse eklenmez). Yalnız oyuncak ve kopyada, yalnız `brain/` dalları;
4. `git -C $E/referee revert --no-edit <AKTARIM> && git -C $E/referee push -q origin main`: önyükleme hakemi
   etkilenmez, Kurucu'nun yolu açık kalır; sonra kill switch kapalı ve `control.json` `reverted_exits`'e (A)'nın
   `brain_sha`'sı eklenmiş, it (`26c`; E333'ü taşıyan tohum döneminden sonra: o olmadan `referee/`'ye dokunan her push
   `referee_changed_after_exit` kalır). Geri alma sayaç satırını da siler; insan dokunuşu sayacı bir eksik sayar (E546,
   sahibe açık): dokunuşu `pilot-log.md`'ye yaz;
5. nedeni `pilot-log.md`'ye; düzeltilmiş SHA (A)'dan yeniden geçer, aktarımı yine dokunuştur ([Adımlar](#adımlar)
   2–4); prova fikstürleri yeni aktarım satırı için yeniden üretilir ve sırrı yazılır (`26f`; yanmış küme yeniden
   kullanılmaz, Ö6). Sonra 7. adım: (B) iki hedefte yeni defterlerin ilk genesis'inden koşar.

```
WSL$ git -C $E/referee pull -q --ff-only && N=$(grep referee_tree_sha256 $E/referee/setup/imports.jsonl | tail -n 1 | python3 -c "import json,sys; print(json.load(sys.stdin)['row_hash'])") && AT=$(date -u +%Y%m%dT%H%M%SZ) && echo "$N"
PS> foreach ($T in $TS) { "== $T"; gh api "repos/$T/git/matching-refs/heads/brain/" --jq '.[] | [.ref, .object.sha] | @tsv' }
WSL$ git -C $E/toy fetch -q origin "refs/heads/brain/*:refs/arsiv/$AT/brain/*" && git -C $E/toy push -q origin "refs/arsiv/$AT/brain/*:refs/tags/arsiv/$N/brain/*"
WSL$ U=https://github.com/Okan-wqm/snowball-rehearsal-copy.git; git -C $E/kopya.git fetch -q $U "refs/heads/brain/*:refs/arsiv/$AT/brain/*" && git -C $E/kopya.git push -q $U "refs/arsiv/$AT/brain/*:refs/tags/arsiv/$N/brain/*"
PS> foreach ($T in $TS) { "== $T"; gh api "repos/$T/git/matching-refs/tags/arsiv/" --jq '.[] | [.ref, .object.sha] | @tsv' }
PS> foreach ($T in $TS) { gh api "repos/$T/git/matching-refs/heads/brain/" --jq '.[].ref' | ForEach-Object { gh api -X DELETE "repos/$T/git/$_" } }
PS> foreach ($T in $TS) { "== $T"; foreach ($B in 'brain/state', 'brain/integration') { gh api "repos/$T/rules/branches/$B" --jq '[.[].type] | unique | join(",")' } }
```

*Denetim:* etiketlerin SHA'ları ilk listedekilerdir; silmeden sonra `matching-refs/heads/brain/` boştur; son komut her
hedefte `deletion,non_fast_forward` ve `deletion,non_fast_forward,pull_request,required_status_checks` basar. Biri
eksikse S8'in ikinci yarısı yapılmamıştır: kill switch kapatılmaz, sahibe söylenir.

Hedef ürün reposu hiçbir durumda değişmez.

## Sahip listesi

Okan-wqm hesabıyla web arayüzü. Gizli değerler yalnız GitHub'ın kendi alanına ya da operatörün açtığı gizli isteme
yapıştırılır; sohbete, dosyaya ya da günlüğe yazılmaz.

- **S1 · İki boş açık repo** ((A)'dan önce, Ek A). github.com/new: Owner Okan-wqm; Repository name
  `snowball-rehearsal-toy`, sonra `snowball-rehearsal-copy`; Public; README, .gitignore, lisans ve şablon yok; çatal değil.
- **S2 · Kopyada Actions kapalı**, kopyaya içerik girmeden önce. snowball-rehearsal-copy → Settings → Actions →
  General → Actions permissions: Disable actions → Save.
- **S3 · Aynalama belirteci.** Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate
  new token: Token name `snowball-copy-mirror`; Resource owner Okan-wqm; Expiration 30 days; Repository access: Only
  select repositories → snowball-rehearsal-copy; Repository permissions: Contents Read and write, Workflows Read and
  write (Metadata Read-only kendiliğinden); başka izin yok → Generate token. Değeri Ek A 2'nin gizli istemine kendin
  yapıştır.
- **S4 · Yazar App'i** (5. adım). Settings → Developer settings → GitHub Apps → New GitHub App: GitHub App name
  `snowball-rehearsal-writer` (alınmışsa başka bir ad, operatöre söyle); Homepage URL
  `https://github.com/Okan-wqm/snowball-rehearsal-referee`; Callback URL boş; Request user authorization (OAuth) during
  installation kapalı; Enable Device Flow kapalı; Setup URL boş; Webhook Active kapalı. Repository permissions:
  Administration Read-only; Checks Read and write; Contents Read and write; Pull requests Read and write; Metadata
  Read-only; geri kalan her şey No access (Actions, Workflows, Secrets, Variables, Environments dahil). Organization ve
  Account permissions No access; Subscribe to events hiçbiri; Where can this GitHub App be installed: Only on this
  account → Create GitHub App. App ID'yi operatöre söyle; özel anahtar: App ayarlarında soldan Credentials → Key pairs → New key (.pem iner; GitHub'ın 2026 arayüzü, eski "Generate a private key" düğmesi yok).
- **S5 · App'i kur.** App sayfası → Install App → Okan-wqm → Only select repositories: snowball-rehearsal-toy,
  snowball-rehearsal-copy → Install. Başka repo yok (aquaculture_platform, beyin, hakem, snowball-mcp asla).
  Settings → Applications → Installed GitHub Apps'te yalnız bu App'in ve yalnız bu iki reponun göründüğünü operatöre söyle.
- **S6 · Hakemin sırları.** snowball-rehearsal-referee → Settings → Secrets and variables → Actions → Secrets → New
  repository secret (ortam sırrı değil): `WRITER_APP_ID` = App ID; `WRITER_APP_PRIVATE_KEY` = .pem dosyasının tamamı
  (BEGIN/END satırları dahil). Adlar 3. adımın listesindendir; listede başka bir sır varsa dur, operatörle konuş. Sonra
  .pem'i diskten sil, kopya tutma. `CLAUDE_CODE_OAUTH_TOKEN`'a dokunma.
- **S7 · Ruleset'ler, iki hedefte aynı** (S5'ten sonra). Settings → Rules → Rulesets → New ruleset (branch ya da tag);
  Enforcement status Active; "yok" Bypass list'in boş kalmasıdır; tabloda yazmayan kural işaretlenmez.

  | Ad (tür) | Hedef | Kurallar | Bypass |
  |---|---|---|---|
  | `brain-state` (branch) | Include by pattern `brain/state` | Restrict deletions; Block force pushes | yok |
  | `brain-integration` (branch) | Include by pattern `brain/integration` | Restrict deletions; Block force pushes; Require a pull request before merging (Required approvals 0, öbür seçenekler kapalı, Allowed merge methods yalnız Merge); Require status checks to pass (Require branches to be up to date before merging açık; Do not require status checks on creation açık; check `snowball-gate`, kaynak snowball-rehearsal-writer) | yok |
  | `main` (branch) | Include default branch | Restrict updates; Restrict deletions; Block force pushes | Repository admin, Always allow |
  | `brain-disi` (branch) | Include all branches; Exclude by pattern `brain/**` ve `main` | Restrict creations; Restrict updates; Restrict deletions; Block force pushes | Repository admin, Always allow |
  | `etiket` (tag) | Include all tags | Restrict creations; Restrict updates; Restrict deletions; Block force pushes | Repository admin, Always allow |

  Kontrolün kaynak listesinde App görünmezse (henüz hiç kontrol raporlamadı) `brain-integration`'ı Ek B'deki gövdeyle
  API'den yarat; "any source" seçilmez (genesis `integration_check_not_writer` ile durur).
- **S8 · Yalnız Başarısızlık 3'te.** İki hedefte `brain-state` ve `brain-integration` → Enforcement status Disabled →
  Save; operatör dalları silince ikisi yeniden Active, aynı ayarlarla. Bypass list'e kimse eklenmez; yalnız Enforcement
  status değişir (genesis bypass aktörünü okumaz, `29o`).

## Spec sessiz: seçilenler

Hepsi en dar seçimdir ve E330'dadır.

- Repo adları; hedef kimlikleri `toy`, `copy`. İçe aktarma WSL'de (E116; `25a` yer ve komut söylemez).
- K4 tutmuyorsa (A) kabul edilmiş olsa da aktarım yok: 7. satır kırmızı olur, sert duruş ve geri alma; aynı sonuç dokunuşsuz.
- `loop.yml` 4. ile 7. adım arası kapalı (`25` 9'un yolu). 7. adımda `merge_paused: false`.
- Kontrol adı `snowball-gate` (`25a` 3'ün adı; tohumun genesis vektörlerindeki ad). "Do not require status checks on creation" açık:
  yoksa `brain/integration`'ın `main`'den kesimi kontrolü olmayan commit'te reddedilir. Merge yöntemi yalnız Merge:
  geri alma merge'ün ilk ebeveynini okur (`asama-0/09` test 25, `29i`).
- Hedeflerin `main`'i `25a` 4'ün ikinci yoluyla: güncelleme kısıtı, bypass yalnız Repository admin (kopyanın aynalaması
  ve oyuncağın yeniden aktarımı bu roldedir; yazar App'i bu rolde değildir).
- `brain-disi` ve `etiket`: App izinleri dal bazında sınırlanamaz; yazar App'ini `brain/` dallarına bunlar hapseder.
- App beyanı özete değil `pilot-log.md`'ye (`25a` 5 Aşama 0'da yoktur, P1'le gelir; E545). `TARGET_OWNER`'ı
  operatör yazar.
- Sırlar repo düzeyinde (`loop.yml` ortam adlandırmaz); adları aktarılan `loop.yml`'dan. `25` 7'nin "prova gizli
  tohumu" bir döngü işi onu adlandırana kadar yaratılmaz.
- Aynalama belirtecinde Workflows izni (GitHub iş akışı dosyası taşıyan push'u onsuz reddeder; Actions kapalı, dosyalar
  koşmaz), 30 gün; aynalama operatörün makinesinde. `oauth_token_expires` ISO tarih.
- Arşiv etiketlerinin yeri ve adı (`refs/tags/arsiv/<row_hash>/<dal>`, hedefin kendi reposunda) `25a`'nındır (E540);
  komutlar burada.
- 8. adımda `referee/` denetimi elle (E333). PASS satırının yeri `asama-0/10a`'nınki, oyuncak (E334).
- `stage-open`'ın girdileri (E371): oyuncağın ve kopyanın `brain/state` klonları (`--ref` öntanımı
  `refs/remotes/origin/brain/state`; kök paketleri oradan, E414), döngünün `loop.yml` kimliği, imzalı (A) sonucu
  (`--result`, E379); PASS satırının ve kökün okunuşu E371, E375–E377, E379, E388, E404–E406 ve E411–E416'dadır,
  Kurucu'ya `26d`'de söylenir.
- Parti aktarımı (P1 ilk, E378): beyin parti isteğini yapar (`exit-request.json` `{stage: 1, sha, spec_sha256, batch:
  "P1"}`), önyükleme hakeminin aktarılabilir sonucu `exit.batch` taşır; 3. adımın komutu `--toy` olmadan koşulur,
  sayaç satırı `{ts, stage, batch, brain_sha, referee_tree_sha256, result_sha256}`'dir; açık parti dışındaki ya da
  ikinci kez aktarılan parti durur. İsteğin hangi biçimi taşıdığını kilit söyler, istek değil (E402): kilit yokken
  `batch` anahtarlı istek eskisi gibi `exit_request_malformed`'dır ve Aşama 0'ın her yargısı kilitsiz değişmez.
  P1'den sonra açık parti P2'dir (`stages/stage1-P2.json`, E491); aktarımı aynı komutla, `batch: "P2"`; P1 ve P2
  aktarılınca açık tablo boştur. Çıkış partisinin tablosu bu tohumda yoktur (E495). Parti tabloları Kurucu'ya `26e`'de.
- Aşama 1'in rakip freni `stage_budgets.asama_1.rival_usd` = 15 (`asama-1/10`'un başlangıç değeri; 9. adımda,
  `stage-open`'dan önce; E492). Değeri sahip ya da operatör yükseltebilir (olağan iş frene takılırsa, `asama-1/10`).
- Döngünün girdileri (E490): değişken yok; beyin `bootstrap.json` `brain_repo` (bugün `Okan-wqm/snowball-rehearsal-brain`),
  hedefler özetin `targets[]`'ı (`toy`, `copy`), Sigstore hakemin `bootstrap/requirements/sign.txt`'i (`29s`).
- Oyuncağın `identifiers`'ı `[]`, `unit_candidates`'i `["textkit"]` (`26c` ikisini kopya için tanımlar; tohumun genesis
  fikstürü oyuncağa da birim adayı verir). Parti aktarımında oyuncak itilmez (`26c` `toy_tree_sha256?`).

## Ek A: birinci bölümden eksik kalanlar

Bugün oyuncak ve kopya repoları yok; özette `targets[]` ve `honesty_commitment`, `control.json`'da `oauth_token_expires`,
`loop_schedule`, `merge_paused` yok. (A) bunlar olmadan kabul edilemez (`not_checked:genellik`, E284;
`not_checked:durustluk`, E287); sıra:

1. **Sahip** S1, S2, S3.
2. **Operatör: belirteç ve aynalama betiği** (bir kez; 0. adımdan sonra). Sahip belirteci gizli isteme yapıştırır,
   ekrana basılmaz:

   ```
   WSL$ mkdir -p ~/.config/snowball && chmod 700 ~/.config/snowball
   WSL$ read -rs T && (umask 077; printf '%s' "$T" > ~/.config/snowball/kopya-token) && unset T
   ```

   `~/etkinlestirme/aynala.sh` (kopyanın `main`'ini hedefin `main`'ine hızlı ileri sarar, `25` 10a; yalnız `main`,
   etiket ve başka dal yok; ileri sarılamazsa git reddeder ve durur):

   ```
   #!/bin/sh
   set -eu
   E=~/etkinlestirme
   [ -d $E/kopya.git ] || git init -q --bare $E/kopya.git
   git -C $E/kopya.git fetch -q --no-tags https://github.com/Okan-wqm/aquaculture_platform.git +refs/heads/main:refs/remotes/kaynak/main
   git -C $E/kopya.git -c credential.helper= \
     -c credential.helper='!f() { echo username=x-access-token; printf "password=%s\n" "$(cat ~/.config/snowball/kopya-token)"; }; f' \
     push https://github.com/Okan-wqm/snowball-rehearsal-copy.git refs/remotes/kaynak/main:refs/heads/main
   git -C $E/kopya.git rev-parse refs/remotes/kaynak/main
   ```

3. **Operatör: kopyanın ilk içeriği.** `sh ~/etkinlestirme/aynala.sh` bir kez; son satır `base_sha`'dır. Sonra (B)
   PASS olana kadar koşturulmaz (`base_sha` sabit). *Denetim:* `PS> gh api repos/Okan-wqm/snowball-rehearsal-copy/branches --jq '.[].name'`
   yalnız `main`; `gh api repos/Okan-wqm/snowball-rehearsal-copy/actions/runs --jq .total_count` 0.
4. **Operatör: `targets[]`.** Hakem klonunda `setup/summary.json`'a bir editörle ekle, tohumun kendi okuyucusuyla
   denetle, it; sonraki `bootstrap.yml` koşusu yeşil olmalı. Hakemin bugünkü `bootstrap/`'ı (tohum dönemi 3a) `targets[]`'ı
   okumaz; okuyan tohum snowball-mcp `main`'indedir (E284, E293), (A)'yı da onu getiren tohum dönemi yargılar:

   ```json
   "targets": [
     {"id": "toy", "repo": "Okan-wqm/snowball-rehearsal-toy", "kind": "toy", "base_sha": null,
      "identifiers": [], "excluded_paths": [], "unit_candidates": ["textkit"]},
     {"id": "copy", "repo": "Okan-wqm/snowball-rehearsal-copy", "kind": "copy", "base_sha": "<3'ün SHA'sı>",
      "identifiers": ["<operatör seçer>"], "excluded_paths": ["<operatör seçer>"], "unit_candidates": ["<operatör seçer>"]}
   ]
   ```

   ```
   WSL$ rm -rf $E/smcp && git -c core.autocrlf=false clone -q --depth 1 https://github.com/Okan-wqm/snowball-mcp.git $E/smcp
   WSL$ cd $E/smcp/seed/bootstrap && python3 -c "import sys; from pathlib import Path; from snowball_bootstrap import config; s = config.load_summary(Path(sys.argv[1])); print([(t.id, t.kind, t.base_sha, bool(t.identifiers)) for t in s.targets or ()]); print(config.start_missing(s) or 'tamam')" $E/referee
   ```

   Beklenen iki hedef, kopyanınki `True` ile; ikinci satır 6 yapılana kadar yalnız `honesty_commitment`'ı adlandırır.
   Kimlik `toy` beynin `candidates/toy/` ve `targets/toy/`'unu izler; oyuncak boştur, `base_sha` `null` (genesis
   `main`'i API'den okur). `identifiers` #genellik'in ad listesidir (oyuncağın boş listesi ad yok demektir, E291);
   kopyanınki en az hedefin ayırt edici adı. `excluded_paths` hedefin ajan ve otomasyon dizinleri ve kapsam dışı
   paketler (`14`, `25` 10a), `unit_candidates` `asama-0/08`'in ölçütleriyle sıralı birim yolları: üçü de operatör
   verisidir, bu sayfa seçmez. Yer tutucu bırakılarak itilmez.
5. **Operatör: `control.json`'un eksik alanları** (`25` 3–4), 4'le aynı commit'te: `oauth_token_expires` (`claude
   setup-token` gününe bir yıl; sır 2026-10-29'da yazıldı, günü operatör doğrular), `loop_schedule: false`,
   `merge_paused: true` (eksik alanın kapalı değerleri, `26c`; 7. adımda `merge_paused` açılır).
6. **Sahibin kararı: #durustluk** (`25` 10c, `02` "Sahip istisnası", E294). Ekim bu pilotta Kurucu başlamadan
   yapılmadı. Sahip istisnayı verirse özete `honesty_exception` `{"stage": 0, "carry_to": 1, "reason": "<neden, E287>"}`
   ve yanına Aşama 1'in ekiminin `honesty_commitment`'ı girer (Aşama 0 sürerken, Kurucu olmayan bir ajanla; anahtar
   hiçbir açık metne yazılmaz). Taahhüt olmadan istisna koşulu kaldırmaz (E297). Anahtarın ve tespit yüklemlerinin
   biçimi bugün tanımsız (E287): ekim tohum dönemini bekler.

## Ek B: `brain-integration` API ile

Sahip, `<APP_ID>`'yi yazıp `brain-integration.json` olarak kaydeder ve her hedef için bir kez koşar:
`PS> gh api -X POST repos/<hedef>/rulesets --input brain-integration.json`

```json
{"name": "brain-integration", "target": "branch", "enforcement": "active", "bypass_actors": [],
 "conditions": {"ref_name": {"include": ["refs/heads/brain/integration"], "exclude": []}},
 "rules": [{"type": "deletion"}, {"type": "non_fast_forward"},
  {"type": "pull_request", "parameters": {"required_approving_review_count": 0, "dismiss_stale_reviews_on_push": false,
   "require_code_owner_review": false, "require_last_push_approval": false, "required_review_thread_resolution": false,
   "allowed_merge_methods": ["merge"]}},
  {"type": "required_status_checks", "parameters": {"strict_required_status_checks_policy": true,
   "do_not_enforce_on_create": true, "required_status_checks": [{"context": "snowball-gate", "integration_id": <APP_ID>}]}}]}
```
