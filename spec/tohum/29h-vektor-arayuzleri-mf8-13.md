# Vektör Arayüzleri: `k0map`, `refs`

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0'ın MF8 ve MF9'unu yazarken; bu grupların komutu, girdisi ya da çıktısı değişirken
Çapa: `seed/bootstrap/vectors/vectors.json` (`k0map`, `refs`) ve `vectors/<grup>/` fikstürleri

---

`29f` ve `29g`'nin devamıdır, kuralları onlarınki (`append`, `root`, `flaky`, `cause`: `29i`); beklenen değerler burada
yok (`29a`). Üretimde dış dünyaya dokunan mekanizma vektörde fikstür bir taklittir (`asama-0/14` Kum).

## `k0map` (MF8, `gate/check.py`)

`python -m gate.check map <diff.patch> <yol> <satır>` (stdin yok) ve `python -m gate.check decide <aday_dizini>
<taban.jsonl> <aday_koşu_dizini> <hashes.json>` (stdin tek JSON nesnesi). Diff `29g`'deki gibi okunur (`diff --git
a/A b/B` bloğu B'yi değiştirir); yalnız `<yol>`'un hunk'ları sayılır. **Eşlenmiş satır** (`asama-0/08`): hunk
`@@ -a,b +c,d @@` (sayı yoksa 1); taban aralığı bağlam dahil `[a, a+b-1]`, aday aralığı `[c, c+d-1]`. Bir taban
aralığındaki `L` o hunk'ın aday aralığının tamamına eşlenir (`d = 0` ise `[]`); başka her `L` `[m, m]`'ye,
`m = L + Σ(d−b)`, toplam taban aralığı `L`'den önce biten hunk'lar üzerinden (`b = 0` olan hunk `a < L` ise önce
biter). `map` → `mapped`: `[ilk, son]` ya da `[]`. `decide`: `<aday_dizini>` `finding.json` (`26c`) ve `diff.patch`
taşır; karar bulgudan yalnız `rule_id`, `path` ve `line`'ı okur: `fix` hakemin kendi taban koşusundandır,
`tool_output_sha256` okunmaz (`asama-0/08` 4, `26a`). `<taban.jsonl>` taban ağaçta, `<aday_koşu_dizini>/cand.jsonl`
aday ağaçta üç lint koşusudur, satır başına bir koşu; `<aday_koşu_dizini>/checks.json` `{tests: [{id, status:
pass|fail}], red_control: pass|fail}` (aday ağaçta etkilenen testler, aynı `koş`un bilinen-kötü adayı). Koşu satırı
normalleştirilmiş kayıttır (spec araç çıktısının biçimini vermez): `{tool, violations: [{rule_id, path, line, fix:
[ilk, son] | null}]}`, `fix` iki ucu dahil taban satırları. Üç satırı olmayan koşu dosyası kullanılamaz; koşu okuyan
her koşul dosyanın ilk satırını okur. `<hashes.json>` üç `koş` dosyasının baytlarının sha256'sı (`{"base.jsonl",
"cand.jsonl", "checks.json"}`, küçük onaltılık, kapsayıcı dışında alınır, `08`). stdin `{control: control.json
nesnesi, unfinished_sentinels: [merge sha]}`. **Nedenler, hepsi yazılır:** `artefact_hash_mismatch` (bir `koş`
dosyası yok ya da sha256'sı başka); `target_not_found` (`base.jsonl`'da bulgunun `rule_id`, `path` ve `line`'ı olan
ihlal yok; hedefsiz `not_distinguished` ve `scope_violation` değerlendirilmez); `not_distinguished` (`cand.jsonl`'da
hedefin `rule_id` ve `path`'i olan bir ihlal hedef satırın eşlenmiş aralığında); `tool_nondeterministic` (taban ya
da aday dosyanın üç satırı bayt bayt aynı değil); `scope_violation` (diff başka yola dokunur; silinen satırın taban
numarası hedefin taban `fix`'i `[s, e]` dışında; eklenen satırın taban konumu `p`, hunk'ında sıradaki taban satırı,
son taban satırından sonra `a+b`, `s ≤ p ≤ e+1` dışında; ya da hedefin `fix`'i `null`; bağlam satırına bakılmaz);
`ratchet_increase` (bir araç aday dosyada tabandakinden çok ihlal sayar; araç başına, kural başına değil; olmayan
araç 0); `zero_tests` (`tests` boş); `tests_red` (bir `fail`); `red_control_green` (`red_control` `pass`);
`merge_paused` (`control.merge_paused` `false` değil: `true`, yok ya da başka değer, `26c`); `sentinel_pending`
(`unfinished_sentinels` boş değil); `secret_in_diff` (`diff.patch` `secrets.scan diff`'ten temiz geçmez; MF8 MF2'yi
çağırır). Karar yalnız neden yoksa `merge`. Çıktı `decision` (`merge` | `reject`), sıralı ve tekil `reasons`.
Çıkış: `map` 0, kullanılamaz girdide 2 (ayrıştırılamayan diff, pozitif tamsayı olmayan satır); `decide` 0 merge, 1
ret, 2 diff, koşu dosyası, `checks.json` ya da stdin anlatıldığı gibi değilse (satır `{"decision": "reject"}`).
`asama-0/08` 1'in başa uygulama denetimi bu modülündür, saf karara girişi yazılana kadar vakasız; `secret_in_diff` de.
Vakalar: `map_shift` hunk dışındaki satır yolun, önünde biten hunk'larının net sayısı kadar kayar; `map_inside_hunk`
taban aralığındaki satır hunk'ın aday aralığının tamamına eşlenir, kaymış tek satıra ya da hunk içindeki konumuna
değil; `merge` madde 3–8 tutar (hedef eşlenmiş aralıktan gitmiş, aynı kuralın kaymış eski ihlali aralık dışında,
kural değişse de araç toplamı aynı, koşular aynı, diff `fix` içinde, testler yeşil, kontrol kırmızı, duraklatma ve
açık nöbetçi yok, hash'ler tutar); `artefact_hash_mismatch` hash'i tutmayan `koş` dosyasına güvenilmez;
`not_distinguished` bölünen satırda kalan ihlal aday aralığında, hedef satırın kendisi, kaymışı ve hunk içindeki
konumu onu kaçırır; `target_not_found` taban koşusunun vermediği satırı adlandıran bulguya güvenilmez;
`tool_nondeterministic` JSON değeri aynı, bir boşluk baytı farklı koşu; `scope_violation` diff `fix` dışındaki bir
satırı da yazar, `finding.json`'ın geniş `fix_range`'i sayılmaz; `ratchet_and_broken_test` mandal artışı ve düşen
test ikisi de yazılır; `red_control_green` bilinen-kötü kontrol yeşil; `fail_closed_controls` `merge_paused`'suz
`control`, bitmemiş nöbetçi ve sıfır test birlikte.

## `refs` (MF9, `target/write.py`)

`python -m target.write replay <api.json>`; stdin tek yazma isteği. `<api.json>` kaydedilmiş GitHub REST ve Git
Data API'sidir, `{"METHOD /yol": yanıt gövdesi}`, süreç içinde ağsız oynatılır: kaydı olan çağrı gövdesini, başka
her çağrı 404 alır; yazmalar yürütülmez, kayıttan yanıtlanır; kayıt yasak yazmaları da yanıtlar, onları yalnız modül
reddeder. İstek `{op, …}`; yollar `/repos/{repo}` altında: `branch {repo, ref, sha}` → `POST /git/refs {ref, sha}`;
`update {repo, ref, sha}` → `PATCH /git/refs/<ref, refs/ öneksiz> {sha, force: false}`; `pr {repo, head, base,
title}` → `POST /pulls`; `check {repo, sha, name, conclusion}` → `POST /check-runs`; `merge {repo, pr}` → `GET
/pulls/{pr}`, sonra `PUT /pulls/{pr}/merge`; `revert {repo, merge_sha, onto, ref}` → `GET /git/commits/{merge_sha}`,
`GET /git/commits/<ilk ebeveyni>`, `GET /git/ref/<onto, refs/ öneksiz>`, `POST /git/commits {message, tree: ilk
ebeveynin ağacı, parents: [onto'nun başı]}`, `POST /git/refs {ref, sha: yeni commit}`. **Ref kuralı:** yazılan her
ref `refs/heads/brain/` ile başlar, `refs/heads/`'den sonraki bileşenleri boş, `.` ya da `..` değil; büyük-küçük harf
duyarlı. Kural `branch`, `update` ve `revert`'ün `ref`'ine, `pr`'nin `head` ve `base`'ine, `merge`'ün yazdığı PR'nin
kayıttaki `head` ve `base`'ine uygulanır (merge base'i yazar); reddedilen istek yazma çağrısı yapmaz. Çıktılar
gönderilen isteklerdendir, kayıttaki yanıtlardan değil: `ok` (kuraldan geçti, her çağrı yanıtlandı); `refs` (oluşan
ya da güncellenen ref'ler, sıralı: `POST git/refs` gövdesinin `ref`'i, `PATCH git/refs` yolu `refs/<yol>`, merge
edilen PR'nin kayıttaki base'i `refs/heads/<base>`); `writes` (GET dışı her çağrının `METHOD /yol`'u, çağrı
sırasıyla; yol `/repos/` ile başlar); `commit` (`revert`'te `POST git/commits` gövdesinin `{tree, parents}`'ı, yoksa
`null`); retle `refs` ve `writes` `[]`. Çıkış: 0 yazıldı; 1 ref kuralıyla ret; 2 kullanılamaz istek ya da 404.
Vakalar: `revert_first_parent_tree` geri alma commit'inin ağacı merge'ün ilk ebeveyninin ağacı (Git Data API'sinden),
ne kendi ağacı ne ikinci ebeveyninki; ebeveyni `onto`'nun başı, yazılan tek ref `brain/` altındaki dal; `refuse_main`
kaydın kabul edeceği `refs/heads/main` güncellemesi yazmadan ret; `refuse_prefix_lookalike` metin olarak
`refs/heads/brain` ile başlayan, `refs/heads/brain/` altında olmayan ref ret; `refuse_dotdot` `..` bileşeniyle
`brain/`'den çıkan ref ret; `refuse_merge_into_main` istek ref adlandırmasa da kayıttaki base'i `main` olan PR'nin
merge'ü, PR okunduktan sonra yazmadan ret; `refuse_pr_into_main` `brain/`'den `main`'e PR ret. `check` vakasız.
