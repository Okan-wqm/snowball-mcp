# Kurulum, Birinci Bölüm: İnşadan Önce

Tarih: 2026-10-29 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ilk başlatmadan önce, bir kez
Çapa: hakem reposundaki `setup/summary.json`

---

Döngü içinde insan yoktur; döngüden önce iki kısa insan işi vardır. Hepsi listededir; listede
olmayan hiçbir şey sonradan insandan istenmez. Ön şart: tohumla gelen önyükleme hakeminin kodu
(`seed/bootstrap/`, `29b`) yazılmış ve kendi testlerinden geçmiş olmalıdır; yoksa kurulum başlamaz.

| # | İş | Neden |
|---|---|---|
| 0 | **Plan gerçeğini kaydet.** Hesap Free; özel repoda ruleset, dal koruması ve ortam sırrı yok, ayda ~2.000 Actions dakikası var; App izinleri kurulum genelinde. İç kullanımda (operatör kararı, 2026-10-29) beyin ve hakem repoları açıktır ve standart koşucu dakikası ücretsizdir; satışta ikisi özel olur. Hakem reposu açıkken koşu günlükleri ve artefaktları da açıktır: yalnız açık hedefler ve eğitim hedefi bağlanır; ilk özel hedeften ya da mühürlü depodan önce hakem reposu özel olur. Hakem reposuna hiçbir App yazmaz, hakem kodu yalnız operatör aktarımıyla değişir (`01a`) | Tasarımın dayandığı gerçek yazılı olsun; değişirse `drift.check` görür |
| 1 | Beyin reposunu aç (iç kullanımda açık). **Kurucu kimliği**: beyin reposunda içerik yazma, `workflows` yok; hakem reposunda yalnız okuma (içerik ve Actions sonuçları) | Oyuncu kendi iş akışını ve hakemini değiştiremesin |
| 2 | Hakem reposunu aç (iç kullanımda açık). Yazma izinli hiçbir App kurulmaz, ortak çalışan eklenmez; iş akışı varsayılan izni salt okunur | Hakemi yalnız operatör yazsın |
| 3 | Önyükleme hakemini kur: `seed/bootstrap/` → hakem reposunda `bootstrap/`, `seed/bootstrap/workflow/bootstrap.yml` → `.github/workflows/`, `seed/bootstrap/vectors/` → `vectors/`, `29` → `seats/`; `bootstrap.json`'u yaz (beyin reposu ve dalı, `@sha256` ile pinli imaj, rakip modeli, `effort`, tur sayısı ve çağrı başı USD tavanı, sınırlar); sır `CLAUDE_CODE_OAUTH_TOKEN` (operatörün `claude setup-token` çıktısı; bir yıl geçerlidir, son kullanma tarihi `control.json`'a `oauth_token_expires` olarak yazılır; dolunca rakip `api_error` verir: ret hafızasına işlenmez, aynı SHA'da üçüncüsünden sonra günde bir, en çok 7 gün yeniden denenir; iç kullanımda API anahtarı yoktur); hash'leri özete yaz | Aşama 0'ın yargıcı Kurucu'dan önce var olsun (Y6) |
| 4 | Hakem reposuna `control.json` (kill switch bayrağı, bütçe durumu, `oauth_token_expires`) ve `policy.json` anayasal bölümünü yaz: aylık USD ve Actions dakikası tavanları, paylar, sınıf tabanları, `required_exit_rows`, regresyon dondurma kuralı, döngü ve gün tavanları, güvenlik anahtar kelimeleri, yasaklı ifadeler, aşama sırası, bakış bütçesi, güven düzeyi, non-inferiority marjı, hayatta kalma pencereleri, prova kuralları, lisans izin listesi ve istisnaları (`18a`) | Operatörün tek döngü dışı kolu; hiçbir App yazamaz |
| 5 | **Okuyucu App'i, yalnız özel hedef gelince** (hakem reposu önce özel olur, madde 0): yalnız `contents:read`, `metadata:read`; özel hedeflere kur. Açık beyin ve açık hedef kimliksiz okunur; önyükleme hakeminde App yoktur | Hakem özel hedefi yazma yetkisi olmadan çeksin |
| 6 | **Yazar App'i**: `contents`, `pull_requests`, `checks` yazma, `administration:read`; `workflows` yok; yalnız hedef repolara kur, beyin ve hakem reposuna kurma | Hedefe tek yazar; oyuncunun ve hakemin reposuna yazmasın |
| 7 | Hakem reposunun sırları: yazar App anahtarı (özel hedef gelince okuyucu App anahtarı), sağlayıcı kimliği (tohum rakibi için `CLAUDE_CODE_OAUTH_TOKEN`), çıkış örneklemi ve prova gizli tohumları | Ajan konteynerine ve oyuncu kodu koşan işe hiçbiri girmez |
| 8 | Harcama tavanları: sağlayıcı harcama tavanı (tohum rakibi abonelik belirteciyle koşar: tavan planın kullanım sınırıdır, `06` bütçesi liste fiyatı tahminidir), GitHub Actions harcama sınırı (dakika aşımı ücretsiz durur; Aşama 0'da önyükleme hakemi dakikayı ölçmez, fren budur; etkinleştirmeden sonra Gözcü bunu bütçe dondurması sayar) | Bütçe sert olsun |
| 9 | Kill switch'in yolları: `control.json` bayrağı (her iş onu `main`'den canlı okur; açıkken iş başlamaz, koşan koşuda `yaz` kabul etmeyen, harcamayı yazan bir `stopped` sonucu imzalar), `gh run cancel` (iptal edilen koşu hiçbir şey imzalamaz), `gh workflow disable`, belirteç sırrını silmek, sağlayıcı tavanı ya da (App'ler kurulunca) App askıya alma. Her yolu bir kez dene | Durdurma hakkı |
| 10 | Oyuncak hedef: boş, herkese açık bir repo aç; içeriği Aşama 0 çıkışında aktarılır (`25a`) | Etkinleştirmenin canlı provası |
| 11 | Kurucu'yu başlat: Actions dışında, çalışma dizini beyin reposu, hedef salt okunur klon (`24`) | Aşama 0 inşası |

**Actions dakikası hesabı.** Açık repoda standart koşucu dakikası ücretsizdir; `monthly_cap_ci_minutes`
etkinleştirmeden sonra Gözcü'nün frenidir (`18a`), önyükleme hakemi onu ölçmez: Aşama 0'da fren GitHub
harcama sınırıdır (madde 8). Repo özel olursa (satışta) Free plan ayda ~2.000 dakika verir, tavan
1.800'dür ve her iş en az bir dakika faturalanır. Önyükleme hakeminin boştaki saatlik yoklaması tek iştir:
ayda ≈ 24 × 30 = 720 dakika. Değerlendirilen bir push beş ya da altı iştir, tipik olarak 15–30 dakika.
Açık repoda dakika bağlamaz; özel repoda kalan ~1.080 dakika ayda ~35–70 değerlendirme eder ve Aşama 0'a
yeter; mikro özellikler yine tek tek itilir (`asama-0/14`). Dakika biterse GitHub işleri durdurur (madde 8).
Tavanı genişletmek operatörün kararıdır ve plan gerçeğini (madde 0) değiştirir: Pro planı (3.000 dakika)
ya da her işten sonra sıfırlanan kendi koşucusu. Rakip bütçesi bitince hakem iş başlatmaz ve aynı baş ay
dönünce ya da politika değişince kendiliğinden yargılanır (`29b`).

**Açık repoda bir sınır.** GitHub, açık repoda 60 gün etkinlik olmazsa zamanlanmış iş akışını kapatır; hakem
uzun süre commit almazsa yoklama sessizce durur. Operatör iş akışını yeniden açar ya da bir commit atar.

**Operatörü ne uyarır.** Döngü operatöre bir şey sormaz ama onu uyarır: kırmızı bir hakem koşusu (kimlik
ya da kota kesintisi, 7 günü aşan kesinti, park edilmiş commit, `request_rejected`, rakip tarafı hata
serisi, durum yokluğu ya da ilk koşu) GitHub'ın başarısız koşu bildirimiyle gelir. `snowball-mcp`
CI'ındaki gecelik bekçi hakemin son koşusunu ve zamanlayıcının yaşadığını denetler; `control.json`'daki
`oauth_token_expires`'a 30 gün kala uyarır.

**Durum kaybolursa** (`29b`). İmzalı durum yoksa, doğrulanamıyorsa ya da koşunun okuduğu durum en yeni
değilse önyükleme hakemi durur ve koşu kırmızıdır; tohumdan kendiliğinden başlamaz. Kurtarma operatörün
işidir ve insan dokunuşu sayacına yazılır: (1) kill switch'i aç ve nedeni bul (silinmiş ya da süresi
dolmuş artefakt, doğrulanmayan imza, yarışan iki koşu); (2) yarış ya da geçici hataysa kill switch'i
kapatıp yeniden koştur, karşılaştır-ve-yaz en yeni durumu okur; (3) durum gerçekten yoksa
`setup/summary.json`'a ilk koşu işaretini koy: hakem tohum commit'inden başlar, donmuş spec'ler, bütçe
ve ret hafızası sıfırlanır, eski sonuçlar Rekor'da kanıt olarak kalır; (4) ilk koşudan sonra işareti
kaldır. Durum şeması değişirse artefakt silinmez, sürümlü taşınır.

Bu bölümün özeti (`setup/summary.json`: repo adları ve görünürlükleri, kurulu App'ler ve izinleri,
iş akışı varsayılan izni, vektör ve koltuk hash'leri, anayasal politika hash'i, `seed_commit`,
`python -m snowball_bootstrap seed-hash` ile hesaplanan `seed_tree_sha256` ve yalnız ilk koşuda ilk koşu
işareti) operatörce hakem reposuna yazılır. Önyükleme hakemi her imzalı sonuca `setup/summary.json`'un,
`vectors/`'ün, `seats/`'in ve anayasal `policy.json`'un hash'lerini yazar (böylece Rekor'a girerler);
vektör ya da koltuk hash'i özetle uyuşmazsa durur. Hash'ler git blob'ları üzerinden hesaplanır, satır
sonundan bağımsızdır. Aşama 0 bu özet olmadan başlamaz.
