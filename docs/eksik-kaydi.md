# Eksik Kaydı: Büyütmeden Önce

Tarih: 2026-10-29 · Sahibi: operatör · Kapsam: Kurucu'yu çalıştırmak ve MCP sunucusunu yazmak dışındaki her şey

**Bu kayıt ipucudur, gerçek değildir (sahip, 2026-10-30).** Her satır yazıldığı anda inanılanı söyler; kod değişmiş,
açık kapanmış ya da tahmin yanlış çıkmış olabilir. Bir satıra dayanmadan önce kodla, testle ve son hakem sonucuyla
doğrula; tutmayan satır bir bulgudur, yeni satırla düzeltilir.

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
| E06 | Yeniden üretici sözleşmesi belirsiz; stderr ve çıktı atılıyor | K | — | R2 D4 | kapandı · parti 2 · sözleşme E260 ile iki taraflı (belirti ve doğru çıktı) |
| E07 | Yeniden üretilemeyen iddia iz bırakmıyor | K | evet | D4 R2 | kapandı · parti 2 · (c) E260 ile değişti: açık iddianın sonraki baştaki gösterimi kanıt değil, gözlemdir |
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
| E26 | Bu repoda CI yok | K | evet | W5 | kapandı · `.github/workflows/ci.yml`, ilk tam koşu yeşil (run 40845743667) |
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
| E54 | Ortak kader ve sürekli iletişim: Kurucu, hakem (rakibiyle) ve beyin birbirinde gördüğü eksiği tek bir zincirli bildirim kanalına yazar, her koşuda okur; hakem kendi zayıflığını da bildirir; ölçülür | K | operatör yönü | operatör, 2026-10-29 | açık (E53 ile tek mekanizma, parti 2'den sonra) |
| E55 | Sınırlar kendini ayarlar: işletim sınırları ölçüme dayalı ve operatörün bandı içinde; ekonomik sınırlar operatörde; güvenlik yasaları sabit | K | operatör yönü | operatör, 2026-10-29 | açık (parti 3, E18 ile) |
| E56 | Güvenlik birinci sınıf: zafiyet kataloğu, hedef repoya özel güvenlik kuralları ve testleri, zincirli güvenlik defteri, güvenlikten öğrenme | K | operatör yönü | operatör, 2026-10-29 | spec yazıldı (`30`–`30e`), defter 8 satır ve testi · kod açık |
| E57 | Bağımsız güvenlik avcısı: Kurucu'dan ve rakipten ayrı, salt okunur, kanıtla bildiren, hakemi, beyni ve hedefleri tarayan, kanaryalarla ölçülen organ | K | operatör yönü | operatör, 2026-10-29 | spec yazıldı (`30f`) · kod açık |
| E58 | Hedeften iz bırakmadan çıkış: sistemin her şeyi tek klasörde (`.brain/`, yetim `brain/state` dalı); çıkış prosedürü yazılı değil ve denenmiyor | B | operatör yönü | operatör, 2026-10-29 | açık |
| E59 | Satış zamanı: üyelik bitince sistemin müşteride oluşturduğu her şey silinir (kabul edilmiş kod hariç), silme makbuzu verilir | satış | operatör yönü | operatör, 2026-10-29 | satışta açılır |
| E60 | Satış zamanı: sistemin ürettiği dosyaların yeri; varsayılan müşteride, açık izinle müşteri başına ayrı, özel, şifreli barındırma; güvenlik bulguları hep müşteride | satış | operatör sorusu | operatör, 2026-10-29 | satışta açılır |
| E61 | Satış zamanı: repolar arası öğrenmede gizlilik duvarı; kalıp taşınır, müşteri bilgisi taşınmaz; terfi öncesi otomatik sızıntı kontrolü ve sözleşmede izin | satış | operatör sorusu | operatör, 2026-10-29 | satışta açılır |
| E62 | Filo genelinde güvenlik: bir repoda doğrulanan açık dedektöre dönüşür, gizlilik duvarından geçer, bağlı bütün repolarda taranır; her repoya yalnız kendi açığı bildirilir | B | operatör yönü | operatör, 2026-10-29 | açık (çok repo ile, `21`) |
| E63 | Ajan bilgisinin bütün müşterilerden öğrenilmesi: beceri ve organlar, promptlar, puanlar; terfi, gölge denemesi, bağlamla taşıma, gizlilik ve toplu anonim puan | B | operatör yönü | operatör, 2026-10-29 | açık (çok repo ile, `21`, `21a`) |
| E64 | Prova yargıcı dersin içinde gizli aile etiketini arıyor; kör bir beyin geçemez, getirme hiç sınanmıyor | K | — | e2e-7 L1 | kapandı · `gaps/self-improvement-proof` · kapsam tek açık eşleyiciyle (`scope_matches`) yargılanır: doğduğu örneği ve ailenin ≥ %80'ini kapsar, başka ailenin hiçbir örneğini kapsamaz; aile adı sözlük dışıdır, hiçbir şeyi kapsamaz; kullanım da kapsamı izler; simüle beyinler `label_peeker`, `overbroad_scope`; 7 mutant (`22a`, `29c`) |
| E65 | Ders verme/saklama deneyini beynin kendisi yapıyor; kollar eşit mi denetlenmiyor (işe yaramaz ders %100 kredi alıyor) | K | — | e2e-7 L2 | kapandı · `gaps/self-improvement-proof` · plasebo kollarını anahtardaki (taahhütle bağlı) `withhold_seed`'in HMAC'i çeker; dispatcher'ın kaydı çekilişe uymazsa ya da bir dersin kolları farklı model, çaba ya da turla koşarsa FAIL; simüle beyinler `cherry_picking_dispatcher`, `unequal_arms`; 4 mutant (`22a`, `22b`, `29c`). Şüphecinin ikinci turu: eşit ayar kuralı yalnız plaseboyu kapsıyordu, etki çiftleri ayar taşımıyordu; dersli kola çok çaba ve tur veren beyin McNemar etkisini şişirip etkiyi geçiyordu (yeniden üretildi). Şimdi her etki çifti iki kolun `run`'ını taşır, iki kol ve bütün çiftler aynı `model`, `effort`, `max_turns`'le koşmazsa etki FAIL; `unequal_arms` etkide de FAIL; 3 mutant daha (`22a`, `22b`, `29c`) |
| E66 | Ders başına canlı kredi neredeyse hiç ölçülemiyor; boş derslerin ~%10'u geçiyor | B | evet (18b) | e2e-7 L3 | onaylandı · açık |
| E67 | Bildirim ödülü 'kusur ekle, sonra bildir' tuzağı kuruyor; kendi soyundan gelen kusura kredi yok, kök neden başına tek kredi | K | evet (E53'ü biçimler) | e2e-7 L4 | onaylandı · açık |
| E68 | Kendini ayarlayan sınır kuralı sansürlü gözlemle merdiven gibi yükseliyor; sınıra takılan gözlem ölçüye girmemeli | K | evet (E55'i düzeltir) | e2e-7 L5 | onaylandı · açık |
| E69 | Kredi ve itibar yalnız birleşen işi sayıyor; kaçınmayı ve riskli alandan uzak durmayı ödüllendiriyor | B | — | e2e-7 L6 | açık |
| E70 | Sistemin öğrenip öğrenmediğini çürütebilecek zamanlanmış ölçüm yok; 'aynı hata'nın kimliği yok | B | — | e2e-7 L7 | kısmen · gözlem karnededir (E310; operatör her döngüden sonra üretir); 'aynı hata'nın kimliği hâlâ yok: önerilen mekanik anahtar (traceback türü, beklentinin hash'i) canlı verideki iki örneğinde de tutmadı (şüpheci), karne push'lar arası tekrarı `ölçülemez` yazar; kör ve donmuş bir sınıf etiketleme protokolü gerekir |
| E71 | `cause` etiketi tek bir ekilmiş merge ile doğrulanıyor; yanlış etiket kalıcı, düzeltme satırı yok | B | — | e2e-7 L8 | açık |
| E72 | Çoklu karşılaştırma ve tekrarlı bakış yalnız held-out havuzda sayılıyor; boş organ ~%34 kabul alabilir | B | evet (19 anayasal) | e2e-7 L9 | onaylandı · açık |
| E73 | 'Hiç unutmaz' defterde doğru, davranışta değil: arşivlenen ders geri dönmüyor, arşiv blob'larının kalıcı yeri yok | B | — | e2e-7 L10 | açık |
| E74 | Serbest metin dersler kalıcı prompt enjeksiyonu yolu (hafıza zehirlenmesi), geri çekmesi pratikte yok | B | evet (katalog) | e2e-7 L11 | onaylandı · açık |
| E75 | İtibar karşılaştırmaları karışık (zor işler önce sıradakine) ve zaman/model değişimini hesaba katmıyor | B | — | e2e-7 L12 | açık |
| E76 | Aşama 0 ilk gerçek döngüden önce bütün hakemi kuruyor; gerçek değer Aşama 4-6'da; ilk kabule ulaşamama riski | K | evet (yol haritası) | e2e-8 G1 | onaylandı (daralt: önce oyuncak hedef, sonra tek gerçek birim) · açık |
| E77 | Çok dilli, veritabanlı monorepo için birim ve çalışma ortamı modeli yok (profilde units, services, env imajı yok) | K | evet (Y3 ifadesi) | e2e-8 G2 | onaylandı · açık |
| E78 | Hedefin dondurulmuş kopyası: insan düzeltmesi gelmez, ölçüm havuzu dolmaz, kabul edilen düzeltmenin orijinale yolu yok | B | evet | e2e-8 G3 | onaylandı · açık |
| E79 | Kurucu'nun dört görevi ölçülmüyor: dürüstlük provası (çelişen vektör, ekilmiş açık, teyit) gerekli | K | evet (bütçe) | e2e-8 G4 | onaylandı · açık · çıkışın #durustluk satırı buna ve E287'ye bağlı, `not_checked:durustluk`; Aşama 0'da yalnız sahibin adlı istisnasıyla ve yanında taşıma hedefinin ekiminin taahhüdüyle kalkar (E294, E297) |
| E80 | Hazır bir ajana karşı taban yok; 'en iyi sistem' iddiası ölçülemez | B | evet (bütçe) | e2e-8 G5 | onaylandı · açık |
| E81 | Asıl hedeflerin metriği yok: birim notu (en zayıf boyut) ve gizlilik kanaryası | B | — | e2e-8 G6 | açık |
| E82 | Aşama 1-3 zayıf hedef testlerine oracle olarak güveniyor; hunk kapsaması ve mutant öldürme Aşama 4'te açılıyor | B | — | e2e-8 G7 | açık |
| E83 | Tenant ve BOLA açıkları için veri akışı aracı yok; lisans mantığı tutarsız (özel CLI içeride, LGPL araçlar dışarıda) | B | evet (lisans) | e2e-8 G8 | onaylandı · açık |
| E84 | Kendini geliştirme tek soylu açgözlü arama; arşiv ve popülasyon araması yok | B | evet (bütçe payı) | e2e-8 G9 | onaylandı · açık |
| E85 | Model değişiminde yeniden yeterlilik protokolü yok; bütün seatler tek aileden | B | evet | e2e-8 G10 | onaylandı · açık |
| E86 | Rekor erişilebilirliği sert durma; tek operatör için aşırı | B | evet | e2e-8 G11 | onaylandı · açık |
| E87 | Bağımlılık açıklarını kapatmak kalıcı yasak (Y3); en sık açık sınıfı bulunur ama kapatılamaz | S | evet (Y3) | e2e-8 G12 | onaylandı · açık |
| E88 | Tohumu güncelleme yolu yok: operatörün tohum commit'i hakemi kilitler ve Kurucu'ya sayılır; beyin reposunun hangisi olduğu çelişkili | K | evet (beyin reposu) | e2e-1 A1 | kapandı · yeni ayrı beyin reposu; tohum dönemi: `setup/summary.json` `seed_epochs[]` (`26c`), son satırın commit'i başken `seed_update` (noop), sonraki push'ların diff'indeki teslim Kurucu'nun değil ve rakibe gitmez, başın `spec/tohum`/`seed` ağaçları satıra eşit olmalı, satır kendi commit'ine uymazsa koşu durur; operatör yolu `seed/founder/README.md` "Tohum teslimi" ve `seed-epoch`; `test_seed_epoch`, 13 mutant; ayrıntı Kapanışlar "E88 E162" |
| E89 | Kurucu defteri spec'in istediği gibi push edilemiyor; yalnız defter içeren push rakip bütçesi harcıyor | K | — | e2e-1 A2 | açık |
| E90 | Kurucu kendi ajan yapılandırmasını (`.claude/settings.json`, `CLAUDE.md`, `.mcp.json`) değiştirip yetkisini genişletebilir | K | — | e2e-1 A3 | açık |
| E91 | Kurucu başlatıcı sözleşmesi yok: başlatma, sürdürme, bütçe, kill switch, sonuç okuma (anonim okuma 401) | K | evet (nerede koşar) | e2e-1 A4 | onaylandı · açık |
| E92 | E14'ün planı uygulanamaz: boşta ilk koşu durum yazmıyor, ilk koşu işaretinin kaldırılma anı tanımsız | K | — | e2e-1 A5 | açık |
| E93 | Kurucu'nun Aşama 0 bildirim kanalının okuyucusu yok; E53 planı düzeltilmeli (spec çelişkisi testle kanıtlanamaz) | K | — | e2e-1 A6 | açık |
| E94 | Kurucu ile rakip muhtemelen aynı abonelik kotasını paylaşıyor | K | evet | e2e-1 A7 | onaylandı · operatör adımı bekliyor (ayrı Claude hesabı) |
| E95 | Beyin reposunda ruleset yok: force-push ya da dal silme hakemi kilitler | K | — | e2e-1 A8 | açık |
| E96 | Aşama çıkışı → etkinleştirme geçişi güvensiz ve durumu taşımıyor (bütçe, donmuş spec, açık iddialar) | B | evet | e2e-1 A9 | onaylandı · açık |
| E97 | Reddedilmiş çıkış isteği sonraki her push'u kilitliyor | B | — | e2e-1 A10; E88/E162 incelemesi (E162'den sonra kesin) | kapandı · `asama-0/10` ve `26c`'nin kuralı kodda: reddedilmiş isteğin baytlarının sha256'sı imzalı durumda (`rejected_exit_request`, durum şeması 3; şema 1 ve 2 taşınır), baytı baytına aynı `exit-request.json` sonraki kod push'larında yok sayılır (#yalniz'i bozmaz); yalnız o dosyayı değiştiren push yine çıkış isteğidir ve yeniden yargılanır (`29b`); başka bayt yine istektir; kesinti hiçbir isteği hatırlatmaz; ayrıntı Kapanışlar "E88/E162 incelemesi" |
| E98 | Aşama 0'daki insan dokunuşlarının kaydı yok | B | — | e2e-1 A11 | açık |
| E99 | Aşama 0'ın gerçek hedefi hiç seçilmemiş | B | evet | e2e-1 A12 | onaylandı · açık |
| E100 | Hakemin iş akışlarını hiçbir mikro özellik kurmuyor ve sınamıyor; içe aktarma hakem reposundaki tek iş akışını siliyor | K | evet | e2e-2 B1 | onaylandı · kısmen · test 46'nın kuralları tohumun `wiring` denetiminde, MF17 bitince her kod push'unda ve çıkışta (E162 devamı, E281–E283); açık: "ilk adım `control`" kuralı (E282) ve içe aktarmanın `.github/` ile `bootstrap/`'ı silmesi (`asama-0/10a` #aktarim) |
| E101 | MF13, MF22 ve MF30 testleri hakemin kum havuzunda koşamaz (imajda git, docker, node yok) | K | evet | e2e-2 B2 | onaylandı · açık |
| E102 | Çıkıştaki #lint ve #lock yanlış yollara bakıyor; kilit (A)'da tanımı gereği açık olamaz; vektör yok; donmuş spec kendi lint'inden geçemez | K | evet (kilit anlamı) | e2e-2 B3 | onaylandı · açık · çıkışın #spec satırı E286'ya bağlı, `not_checked:spec` |
| E103 | Tohum vektörleri yalnız MF1, MF9, MF18'i bağlıyor; bütün testleri `true` olan manifest kabul ediliyor | K | evet (gruplar) | e2e-2 B4 | onaylandı · açık |
| E104 | Aşama 0 mikro özelliklerinin okuduğu operatör dosyalarının (`control.json`, `setup/summary.json`, `imports.jsonl`) şeması yok | K | evet (özet alanları) | e2e-2 B5 | onaylandı · açık |
| E105 | Mikro özellik sırası: bazı testler ve çağrılar sonraki mikro özelliklere muhtaç | K | — | e2e-2 B6 | açık |
| E106 | `harness.score`'un iki uyumsuz arayüzü; `26a` ile `29a` başka yerlerde de çelişiyor | K | — | e2e-2 B7 | açık |
| E107 | MF2'nin çıktısı `founder-ledger.jsonl`'ı kimse denetlemiyor | B | — | e2e-2 B8 | kapandı · `ledgercheck`: spec ve kod push'unun eklediği satırlar pull'da (ret, test ve rakipten önce), çıkışta bütün dosya; zincir tohumun `canon.row_hash`'iyle, yalnız-ekleme son kabul edilmiş SHA'ya göre bayt öneki, test 30'un `kind` kümesi; seçimler ve canlı f185 E280'de; ayrıntı Kapanışlar "E162 devamı" |
| E108 | K0 eşleme kuralının 'eşlenmiş satır'ı tanımsız; vektörler bunu bağlamıyor | K | — | e2e-2 B9 | açık |
| E109 | `exit.sample` ve `exit.drill`'in gizli tohumunu hangi işin tuttuğu sayfalar arasında çelişkili | B | evet | e2e-2 B10 | onaylandı · açık |
| E110 | Etkinleştirme defterinin `security` satırlarının tohum güvenlik defterinden nasıl devam edeceği belirsiz | B | — | e2e-2 B11 | açık |
| E111 | Taban avcının sabit grep kümesi tanımsız; Kurucu kendi avcılarının geçeceği çıtayı kendisi koyuyor | B | evet | e2e-2 B12 | onaylandı · açık |
| E112 | Kurucu kimliği yok: operatörün yönetici GitHub hesabı ve kişisel Claude ortamıyla (hafıza, bağlayıcılar) koşar; Y6 iyi niyete kalır | K | evet (kimlik, yalıtım) | e2e-6 O2 | onaylandı · operatör adımı bekliyor (ayrı hesap, ince taneli belirteç, kapsül) |
| E113 | 'not_learning'den sonra Kurucu'yu yeniden başlatmak tanımsız ve döngüye giriyor | K | evet | e2e-6 O3 | onaylandı · açık |
| E114 | Kurulum 3-4 ve `seed-hash` yazıldığı gibi çalıştırılamıyor: şablon, PowerShell komutu, anayasal politika saplaması | K | — | e2e-6 O4 | açık |
| E115 | Kesinti giderilince 'şimdi yeniden dene' kolu yok; elle koşu yeşil görünür ama yargılamaz | B | — | e2e-6 O6 | açık |
| E116 | Aşama 0 aktarımı operatörün Windows makinesinde koşamaz (Sigstore tekerlekleri yalnız manylinux) | B | — | e2e-6 O8 | açık |
| E117 | Duraklatma yazılı değil; kill switch her saat kırmızı koşu ve e-posta üretiyor | B | evet (E16'yı değiştirir) | e2e-6 O9 | onaylandı · açık |
| E118 | Olay kitabı yok; iletiler İngilizce; hangisinin operatörün işi olduğu yazmıyor | B | evet (kanarya harcaması) | e2e-6 O10 | onaylandı · açık |
| E119 | Bus faktörü: her şey tek kişide; hesap taşınırsa imzalı geçmiş kırılır | B | evet (organizasyon) | e2e-6 O12 | karar: taşınmayacak (kişisel test projesi, `Okan-wqm`'de kalır); iş görürse taşınır, o gün hakem durumu yeni kimlikle yeniden başlar |
| E120 | Aşama 0'da tek bir durum yeri yok (harcama, park, seriler, belirteç süresi zip içinde) | B | — | e2e-6 O11 | açık |
| E121 | Organizma kimseye haber vermeden durabilir: `not_learning`, park ve sonuçsuz bekleme yeşil koşuyla biter | K | — | e2e-3 C2 | açık |
| E122 | Hakemin kendini onarma yolu ölü: şerit yazarının ne başlatıcısı ne yazma kimliği var; Gözcü işaretleri hiçbir yerde saklanmıyor | K | evet (artefakt mı repo mu) | e2e-3 C3 | onaylandı · açık |
| E123 | Doğrulanmış hakem açığı aşama sonuna kadar açık kalıyor ve hiçbir kararı değiştirmiyor; karantina ve aşama içi güvenlik aktarımı gerekli | K | evet | e2e-3 C5 | onaylandı · açık |
| E124 | E54'ün tek ortak kanalı tek-yazar zinciri ve bağımsızlık kurallarını bozuyor; tek yazar (`yaz`), role özel görünümler gerekli | K | evet (E54'ü düzeltir) | e2e-3 C6 | onaylandı · açık |
| E125 | E55'in yasada ve şemada yeri yok: Y11 'kapılayan yalnız sıkılaşır' diyor; bant, ölçüm ve kalıcı yer yok; ~30 anahtarsız sabit | K | evet (yasa değişikliği) | e2e-3 C7 | onaylandı · açık |
| E126 | Rakip kanaryası hiç açılmıyor; Aşama 0-3'ün baş yargıcı ölçülmüyor | B | evet (bütçe) | e2e-3 C8 | onaylandı · açık |
| E127 | Hakem ve beyin kapsamlı güvenlik satırlarının etkinleştirmeden sonra yuvası yok; zincir çatallanır | B | evet | e2e-3 C10 | onaylandı · açık |
| E128 | Güvenlik dedektörleri ve bekçi testleri organ yaşam döngüsünü atlıyor, hiç emekli olmuyor | B | — | e2e-3 C11 | açık |
| E129 | `27` ve `17` atıf yaptıkları sayfalarla çelişiyor (insan dokunuşu sayacı, okuyucu satırları, sinyal alanları) | S | — | e2e-3 C12 | açık |
| E130 | E04 eksik: Windows'ta büyük-küçük harf ve sondaki nokta takma adları (`Policy.json`, `CONTROL.JSON`, `.git.`, `GIT~1`) içe aktarmada operatör dosyalarının üzerine yazar ve kanca yerleştirir | K | — | e2e-4 S2 | kısmen · (A) yarısı: hakem ağacı hash'i `referee/`'nin tepesindeki operatör adlarını casefold ile reddeder, `bootstrap` da ayrılmış (E285); içe aktarma aynı hash'le `referee/Control.json`'da durur; harf çakışması (harfçe ayrı, NTFS'te tek iki yol ya da dizin) hakem ağacı hash'inde ve içe aktarmada ret, oyuncakta da (E289); açık: `path_problem`'in sondaki nokta ya da boşluk, 8.3 `~N` ve aygıt adı kuralları, diskte yeniden hash, güvenlik defteri satırı |
| E131 | İçe aktarma ve oyuncak kopyası operatörün makinesine ajan ve IDE otomatik çalıştırma dosyaları yazar; oyuncak alt ağacı imzayla bağlı değil | K | — | e2e-4 S3 | kısmen · (A): `referee/`'de ajan yapılandırması her derinlikte ve harf büyüklüğünde çıkışı kapatır (`agent_config_in_referee`), oyuncak alt ağacının hash'i imzalı sonuçta (`exit.toy_tree_sha256`); açık (B): içe aktarmanın oyuncak hash karşılaştırması, oyuncaktaki ajan yapılandırmasının karantinası, taze klon ve fsck |
| E132 | Aktarılan hakemin iş akışları sırları mekanik bir güvenlik kapısı olmadan alır; avcı ancak etkinleştirmeden sonra başlar | B | evet (sıra) | e2e-4 S4 | onaylandı · kısmen · (A) mekanik kurallar `wiring`'de (E281–E283, E288, E289); açık (B): çevrimdışı actionlint ve zizmor, içe aktarmanın sır-iş haritası karşılaştırması, avcının `referee/` taraması |
| E133 | OAuth belirtecinin iptal, sızıntı müdahalesi ve envanter yolu yok; prova reposu hâlâ belirteci tutuyor | B | evet | e2e-4 S5 | onaylandı · açık |
| E134 | Durum artefaktı yalnız `head_branch == main` ile seçiliyor: çatalın `main` dalından PR sahte durum yükleyebilir; poll doğrulanmamış durumla atlıyor | K | — | e2e-4 S7 | açık |
| E135 | Avcının `getir`'de pip-audit'i kod çalıştırabilir ve tavsiye veritabanını kurcalayabilir | B | — | e2e-4 S8 | açık |
| E136 | Güvenlik defteri ve hakem dosyaları yeniden yazılmaya karşı korunmuyor: üç açık repoda ruleset yok, defter ucu çapalanmıyor | K | evet (ruleset) | e2e-4 S9 | onaylandı · kısmen: `snowball-mcp` ve prova hakemi `main`'i korumada (2026-10-29); yeni beyin reposu bekliyor |
| E137 | Üçüncü taraf ve upstream açıkları için sorumlu ifşa yolu yok; ifşa edilmemiş açıktan dedektör yayılabilir | B | evet (ifşa politikası) | e2e-4 S10 | onaylandı · açık |
| E138 | Özel kod ve açık ayrıntıları tüketici aboneliğinin veri koşullarıyla gidebilir | B | evet | e2e-4 S11 | onaylandı · açık |
| E139 | Rekor repo, sahip, commit, koşu adresi ve görünürlüğü kalıcı yayımlar (E59'daki 'yalnız hash' yanlış); kimlik denetimi ada dayalı | S | evet | e2e-4 S12 | onaylandı · açık |
| E140 | Sonu `/refs/heads/main` olan bir dal adı `poll`'u her saat durduruyor (`ls-remote` kuyruk eşlemesi) | K | — | e2e-5 K1 | açık |
| E141 | Tohum vektörleri sırasında Docker arızası (125) Kurucu'nun `vector_failed` reddine dönüşüyor (E01 sınıfı) | K | — | e2e-5 K2 · parti 2'ye eklendi | kapandı · parti 2 |
| E142 | Boşluk ya da glob karakterli kilit dosyası yolu bütün kapsayıcı komutlarını kırıyor | K | — | e2e-5 K3 | açık |
| E143 | `run.json` yoksa rakip harcaması yazılmıyor (E13'ün planında olmayan yol) | B | — | e2e-5 K7 · parti 2'ye eklendi | kapandı · parti 2 |
| E144 | Rakibin satır sonları git'inkiyle aynı değil: CR diff'i bölüyor, form feed satır numaralarını kaydırıyor | B | — | e2e-5 K9 | açık |
| E145 | Ay sınırını geçen bir koşunun harcaması iki ayın hiçbirine yazılmıyor | S | — | e2e-5 K10 | açık |
| E146 | Ayrıştırılamayan `license_exceptions` ifadesi traceback ile çöküyor (operatör yazım hatası durma olmalı) | S | — | e2e-5 K11 | açık |
| E147 | `pull` boyut sınırından önce bütün ağacı belleğe alıyor ve reddettiği büyük ağacı yine gönderiyor | S | — | e2e-5 K12 | açık |
| E148 | Kurucu'nun defter satırları push türünü değiştiriyor: defterini de yazan spec isteği `mixed_spec_and_code`, çıkış isteği `exit_request_not_alone` ile reddediliyor | K | — | pilot hazırlığı | kapandı · `classify.is_founder_record`: kök `founder-ledger.jsonl` ve `reports/` ne spec ne kod; yalnız onları değiştiren push `none` (yargılanmaz); `test_the_founders_ledger_*`, 4 mutant |
| E149 | `main`'de hakem mutasyonu 09:38'den beri kırmızı, hiçbir mutant koşmadı: mutant kopyasında `.github/workflows` yok, güvenlik defteri testi temel koşuda düşüyor; birleştirmelerden sonra `main` CI'sine bakılmadı | K | — | pilot hazırlığı | kapandı · `mutate.py` kopyaya iş akışlarını alıyor; süreç: her birleştirmeden sonra `main` CI'si yeşil görülmeden iş bitmiş sayılmaz |
| E150 | Tohumda `founder-ledger append` aracı yok; `00a` ve `24a` Kurucu'nun defterini onunla yazdığını varsayıyor | B | — | pilot hazırlığı | açık · pilotta Kurucu'nun bunu bildirip bildirmediği ölçülür |
| E151 | Hakemin Aşama 0 tablosu hâlâ 30 MF'lik eski tablo (`manifest.STAGE0_MF_TESTS`); spec 18 MF ve `stages/stage0.json` diyor; MF1 (T13) aynı, MF2'den sonrası uyuşmuyor | K | — | pilot hazırlığı | kapandı · `stages/stage0.json` (18 MF, `calls`) yüklenirken denetlenir; bildirim, çıkış ve vektör grupları tablodan; modülsüz kırmızı `run-tests`'te; tohum testi tablo ↔ `asama-0/14` ↔ §0.9; ayrıntı Kapanışlar "E151" |
| E152 | İlk pilot oturumu başlamadan düştü (çıkış 255, `exec /opt/founder/entrypoint.sh: no such file or directory`): Windows checkout'u (`core.autocrlf=true`) betiği CRLF'ye çevirdi, shebang'den sonraki CR exec'i kırdı; başlatıcı Docker'ın hatasını rapora yazmadı | K | — | pilot döngü 1 | kapandı · `.gitattributes` (`*.sh`, Dockerfile LF); `launch.write_build_context` LF'ye çevirir; kapsül açılmazsa hata `pilot-log.md`'ye yazılır; ayrıca tmpfs'teki beyin klonu git'te `safe.directory` (yoksa commit ve push olmazdı); `BuildContextTest` |
| E153 | Rakip Kurucu'nun `reports/`'unu görüyor (`asama-0/03`: defter ve `reports/` hariç); yalnız defter gizliydi | B | — | pilot döngü 1 (rakip raporu okuyup alıntıladı) | kapandı · `rival.HIDDEN_DIRS`: kök `reports/` araçlardan, diff'ten ve istekten çıkar; iç içe `reports/` görünür kalır; `E153ReportsHidden`, 4 mutant |
| E154 | Kurucu beyin geçmişindeki eski prova çözümünü okudu (`git show def0121:referee/ledger/chain.py`, 60 satır) ve defterine yazmadı; geçmiş force-push yasağı yüzünden silinemedi, talimatta yasak da yoktu; MF1'in "kendi yazdı" ölçümü kirli | K | evet | pilot döngü 2 | kapandı · kapsül klonu tohum commit'inde keser (`.git/shallow` + gc; eski nesneler kapsülde yok, push çalışıyor, sahte `claude` ile kanıtlandı); talimata kural: eski koda, hakeme, `snowball-mcp`'ye bakma, kısayola baktıysan aynı oturumda bildir |
| E155 | Kurucu `/work/logs`'ta önceki oturumların dökümlerini görebiliyor; hafıza yalnız defter olmalı | S | — | pilot döngü 2 | kapandı · her oturum yalnız `logs/<damga>/`'yı görür |
| E156 | `tohum/27` ve `27a`'da `tests/fixtures/toy-repo/` için okuyucu satırı yok; `#okuyucu` çıkış denetimi düşebilir | B | — | **Kurucu raporu** seed-003 (döngü 1) | açık |
| E157 | `asama-0/14`'te "17 ve 18 hepsini çağırır" sıra kuralıyla çelişiyor ("kendilerinden öncekilerin hepsini" olmalı) | B | — | **Kurucu raporu** spec-004 (döngü 1) | kod tarafı kapandı · `stage0.json` ve tohum testi "kendinden öncekilerin hepsi" okur (18 1–17'yi çağırır; E151); `14`'ün metni 29/29b partisinde |
| E158 | Defter ve rapor tür kümeleri kapalı (`26`, `26c`) ama operatör talimatı `missing_capability` istiyor; Kurucu bunları `seed_issue` olarak yazıyor | B | — | **Kurucu raporu** seed-006 (döngü 1) | açık · bildirim kanalı (E93/E53) ile |
| E159 | `29a` zincir CLI'sinin kırık zincirde çıkış kodunu ve `row_id`'siz satırın `broken_row` değerini söylemiyor; hakem çıkış koduna değil stdout JSON'una baktığı için zararsız ama yazılı değil | S | — | **Kurucu raporu** seed-007 (döngü 2) | açık · 29/29b düzenlemesiyle |
| E160 | `test_an_interrupted_run_takes_the_cli_and_its_children_with_it` init'siz konteynerde kararsız: öldürülen ama biçilmemiş (zombi) süreci `kill(pid, 0)` canlı sayıyor; mutasyon temel koşusunu rastgele durduruyordu | S | — | pilot hazırlığı (6 temel koşudan 6'sı düştü, tam takım geçti) | kapandı · test projenin `helpers.process_alive`'ını kullanıyor (zombi = ölü) |
| E161 | Aşama 0'ın `chain` dışındaki 16 vektör grubu (`secrets` … `genesis`, `29d`) ve genel veri koşucusu (`{cmd, stdin?, fixture, expect, changed}`) tohumda yok; MF2'den itibaren bitmiş MF'nin tabanı eksik | K | — | E151 kod partisi | kapandı · genel veri koşucusu ve MF2–MF7'nin altı grubu (`secrets`, `contained`, `profile`, `npmlock`, `recipe`, `diffguard`; 46 vaka, her beklenen değer iki kör bağımsız uygulamada aynı: A `local/reference_brain`, B `local/blind_b`, ikisi de her test koşusunda yeniden hesaplanır) tohumda, arayüzleri `29f` ve `29g`'de; ayrıntı Kapanışlar "E161, kısmi" · MF8–MF13'ün altı grubu (`k0map`, `refs`, `append`, `root`, `flaky`, `cause`; 56 vaka: uzlaşılmış 44'ünde her beklenen değer iki kör bağımsız uygulamada aynı, E236–E240'ın 12 vakası A'da ve onlardan önce yazılmış B'de aynı (birinde B'ye `forced`'ı bildiren tek satır eklenerek); A `local/reference_brain`'de her test koşusunda yeniden hesaplanır, B repoda değil: E233) tohumda, arayüzleri `29h`, `29i` ve `29j`'de; ayrıntı Kapanışlar "E161, MF8–MF13" ve "E236–E240" · MF14–MF18'in dört grubu (`revert_drill`, `prompt`, `status`, `genesis`; 27 vaka: uzlaşılmış 24'ünde her beklenen değer iki kör bağımsız uygulamada aynı, inceleme 6'nın üç vakası ve genişleyen `genesis` sözleşmesi A'da ve B'de aynı (B'nin `status`'u ve `revert_drill`'i değiştirilmeden, `genesis`'i yeni okumaları ekleyen 29 satırla); A `local/reference_brain`'de her test koşusunda yeniden hesaplanır, B repoda değil: E274) tohumda, arayüzleri `29m`, `29n` ve `29o`'da; MF17'nin grubu yok (`wiring`); ayrıntı Kapanışlar "E161, MF14–MF18" ve "İnceleme 6" · Aşama 0'ın her grubu tohumda: bitmiş hiçbir MF `vector_group_missing` uyarmaz; grup yalnız sayfası Kurucu'nun tohumunda olunca koşar (E199 a). Açık kalan sınırlar E270–E277 |
| E162 | Çıkış isteği kodda olmayan (A) koşullarında kapalıya düşmüyor: #kurucu-defteri, #is-akisi (MF17'nin `wiring` denetimi dahil; her push'ta da yok), #agac (yalnız büyük-küçük harf duyarlı operatör adı var), #genellik, #spec, #durustluk denetlenmeden `transferable` olabilir | K | — | E151 kod partisi | kapandı · `decide.EXIT_NOT_CHECKED`: altı koşulun her biri `exit_condition` `not_checked:<koşul>` ile çıkışı kapalı tutar, Kurucu'ya sayılmaz (`29b` Ret hafızası); `asama-0/10` tablosunun her satırı ya kodda denetlenir ya listededir (test); 3 mutant; denetimlerin kendisi E107, E132, E130/E131, E102, E79'da açık · inceleme: her çıkış artık reddedildiği için bırakılan istek her kod push'unu `exit_request_not_alone` yapıyordu (E97, kapandı); tablo testi denetlenen satırı koda bağlamıyordu (E185, kapandı) · devamı (`gaps/stage0-exit-checks`): dört koşulun denetimi kodda, `pull` arşivden okur, `decide` sonucunu eşler, yoksa ya da karar veremediyse `not_checked` (#kurucu-defteri E107/E280, #is-akisi'nin denetlenebilen kuralları E281/E283, #agac E285, #genellik E284); `EXIT_NOT_CHECKED` artık nedeniyle ve açık satırıyla: #is-akisi'nin `control` kuralı E282, #spec E286, #durustluk E79/E287; ayrıntı Kapanışlar "E162 devamı" · şüpheci turu: ifade sınırı ve betik alanları (E288), harf büyüklüğü (E289), adın sonuçta saklanması (E290), adın katlanması ve metin olmayan dosya (E291), `done_mf` geri alınamaz (E292); ayrıntı Kapanışlar "E162 devamı, şüpheci turu" |
| E163 | `asama-0/14` modülsüz kırmızıda iki okumaya açık: "testlerini … yeşil kalırsa" hepsi mi, biri mi (`calls`'taki "17 ve 18 hepsini çağırır" E157'dir) | S | — | E151 kod partisi | açık · kod test başına okur (`tohum/04` 1: biri yeşil kalırsa ret); metin 29/29b partisinde netleşir |
| E164 | Rakibe gidecek istekte sır biçimli bir dize bulununca hakem yalnız desenin adını söylüyor (`secret_in_prompt:generic_assignment`), hangi dosyada olduğunu söylemiyor; MF2'nin kendi testleri sahte sır taşıdığı için rakip hiç koşmadı ve Kurucu nereye bakacağını bilmeden reddedildi | B | — | pilot döngü 3 (MF2 `9f229b0`) | kapandı · `rival.secret_paths`: diff'in sırrı taşıyan dosyaları (değer asla), istek metnindeyse `(request text)`, sır biçimli yol adlandırılmaz; `result.rival.secret_paths`; test ve 3 mutant |
| E165 | Sır tarayıcısını (MF2) inceleyen rakip kararında kimlik bilgisi biçimli bir değer yazdı; hakem kararı haklı olarak kullanmadı (`secret_in_verdict:generic_assignment_bare`), inceleme kayboldu; protokol rakibe böyle dizeleri çalışma anında kurmasını söylemiyordu | B | — | pilot döngü 5 (`99278a5`) | kapandı · `rival.PROTOCOL`: sır biçimli dizeyi asla yazma, yeniden üreticide parçalardan kur (`'gh'+'p_'+'A'*36`), iddiada alıntılama; protokolün kendisinin tarayıcıdan temiz geçtiği test edildi; 1 mutant |
| E166 | Rakip tarafı bir hata (`secret_in_verdict`, `rival_missing` …) Kurucu'nun hanesine yazılmıyor ama aynı commit yeniden incelenmiyor (`last_evaluated_sha` ilerliyor); Kurucu düzeltemeyeceği bir şey için yeniden push etmek zorunda | B | — | pilot döngü 5 | kapandı · rakip tarafı geçici hatada (`budget` ve `request_rejected` dışı) commit değerlendirilmemiş kalır (`rival_side_retry:n` uyarısı), sonraki koşu yeniden inceler; üst üste 3'üncüde değerlendirilir ve operatör uyarılır; başlatıcı değerlendirilmemiş commit'i Kurucu'ya gitmeden hakeme yeniden yollar (en çok 2); testler ve 6 mutant |
| E167 | Sezgisel bir aleti (MF2 sır tarayıcısı) sınırsız bir rakip her seferinde yeni bir kaçışla çürütebilir; MF2'nin neyi yakalaması gerektiği yazılı bir sözleşmeyle sınırlanmazsa MF2 hiç kabul almayabilir (döngü 4: yapışık token, döngü 6: `$` ile başlayan parola — ikisi de gerçek ve Kurucu'nun kendi vaadine aykırı) | B | — | pilot döngü 4–6 | açık · `secrets` grubunun sözleşmesi (iş akışı) MF2'nin kapsamını yazacak; rakibin çürütmesi o kapsamda ya da modülün kendi vaadinde kalmalı; yakınsama döngü döngü izleniyor; döngü 7'de üçüncü çürütme (`ab;cd;…` gibi tırnaksız değer) Kurucu'nun kendi vaadine dayanıyordu ("8+ karakterlik her atanmış değer yakalanır"): ciddiyet düşüyor, eski çürütmeler kapalı kalıyor; Kurucu talimatına "vaat kadar kanıt" ilkesi eklendi (kapsamı kesin kurallarla yaz, her kuralı testle bağla, kapsam dışını söyle); döngü 9'da beşinci çürütme yalnız harfli noktalı bir adın (kod referansıyla ayırt edilemeyen parola cümlesi) kaçtığını gösterdi — gerçek bir sınır vakası; önceki dördü kapalı kalıyor · rakip protokolüne ilke: hem yakalaması hem temiz girdiyi geçirmesi istenen mekanizmada (tarayıcı, kapı, sınıflandırıcı) çürütme açıkça yakalanacak ve makul temiz girdi olamayacak bir örnek kullanır; sınır vakası yeniden üreticisiz açık iddia olur (kaybolmaz, bloklamaz); test ve mutant · kalan: `secrets` sözleşmesi (iş akışı) kapsamı yazınca kapanır |
| E168 | Başlatıcı kesilip yeniden başlarsa (`STOP`, yeniden başlatma, kesinti) hakemin hiç yargılamadığı son push atlanıyordu: Kurucu kendi son push'unun kararını görmeden yeni oturuma giriyordu | B | — | pilot denetimi | kapandı · her döngü önce son push'un değerlendirildiğine bakar, değerlendirilmediyse hakemi (yeniden deneme kuralıyla) önce koşturur; `Pilot.judge` iki yolun ortak kodu; test ve mutant |
| E169 | Modülsüz kırmızının sonucu (her bitmiş MF'nin testleri modülü olmadan kırmızı mı) yalnız ara `run.json`'da kalıyor, imzalı `result.json`'a girmiyor: MF2 kabulünde kanıt vardı (T38 `gate/secrets.py` olmadan çıkış 1) ama ne Kurucu ne operatör onu sonuçta görebiliyordu | S | — | pilot döngü 10 (MF2 kabulü) | kapandı · `result.module_less`; test ve mutant |
| E170 | Hassasiyeti (yanlış alarmı) ölçen hiçbir şey yok: rakip yalnız kaçırılanı arıyor, `secrets` vektörleri (temiz girdi geçer) tohumda yok; MF2'nin kabul edilmiş tarayıcısı gerçek bir repoda (hedef, 12 759 dosya) 11 038 eşleşme verdi, 10 976'sı "sır ataması" kuralından ve çok büyük kısmı tip, ifade ya da ortam referansı; yüksek güvenli kurallar (özel anahtar, URL parolası, token) ise kullanılabilir ve gerçek değer üretti | K | — | pilot: MF2'nin hedefte ilk koşusu | açık · `secrets` vektörlerinin temiz girdi vakaları (iş akışı) ve hedef üzerinde ölçülen hassasiyetin Aşama 1 ölçütüne bağlanması |
| E171 | `asama-0/14` (ve `tohum/24a`) MF4'ü `referee/profile/derive.py`'ye koyuyor; `profile` adlı paket `referee/` `sys.path`'in başındayken Python'un standart `profile` modülünü gölgeler, `import cProfile` bozulur | B | — | **Kurucu raporu** spec-011 (döngü 12, MF4) | açık · paket adı (ör. `profiler/`) değişmeli; donmuş spec ve `stage0.json` olduğundan tohum dönemiyle (E88) ve Kurucu'nun uyumuyla birlikte |
| E172 | `profile` (ve öncesinde `secrets`, `contained`) grubunun komut arayüzü `29a`/`29d`'de yok; Kurucu arayüzü tahmin ediyor, vektörler gelince uymayabilir | K | — | **Kurucu raporu** seed-008 (üç kez yeniden bildirildi) | açık · iş akışının `29f` arayüz sayfası tohum dönemiyle beyne ulaşınca kapanır |
| E173 | Birim modeli (`asama-0/08` ölçüt 1 ve 3, MF4) her birimin kendi `package.json`'u ve kilit dosyası olduğunu varsayıyor; Nx tarzı bir monorepo'da (birimler `project.json`, tek kök kilit dosyası) kabul edilmiş MF4 gerçek hedefte 32 adaydan yalnız 2'sini uygun buldu ve Aşama 1 için seçilen birim aday bile değil; kök kilitte integrity'siz birkaç girdi 30 birimi birden uygunsuz yapıyor | K | evet | pilot: MF4'ün hedefte ilk koşusu | karar (operatör, 2026-10-29): birim modeli Nx'i destekler — aday `package.json` ya da `project.json` taşıyan dizin, kilit köke kadar en yakın npm kilidi; `tohum/14`, `26c`, `29f`/`29g` ve `profile` vektörleri (yeni vakalar iki kör hesapla) kararlar partisinde, tohum dönemiyle beyne; `asama-0/08` paket adı söylemediği için donmuş spec değişmez; **teslim bekletiliyor (sahip, 2026-10-29): sistem bu uyumsuzluğu kendisi bulmalı** — hazırlanan spec metni ve bağımsız vektörler, Kurucu E203 göreviyle eksikliği kanıtıyla bildirip çözüm önerdiğinde tohum dönemiyle verilir |
| E180 | Tohum dönemi yalnız `spec/tohum` ve `seed/` taşır (`25` 10b); donmuş `spec/asama-0`'ın düzeltmesi (E157'nin `14` metni gibi) teslimle gelirse sonraki her kod push'u `spec_changed_after_freeze` olur, `spec/INDEX.md` değişikliği teslimi spec isteğine çevirir; donmuş dizini açmak operatör kararıdır (`29b`) ama yolu yok | B | evet (donmuş spec'in tohumla düzeltilmesi) | E88 kod partisi | açık |
| E181 | Çıkışın tohumdan doğan nedeni `exit_condition vector_group_missing:<grup>` (E151) Kurucu'ya sayılıyor (`decide.counts_against_founder`); `29b` "Ret hafızası" yalnız Kurucu'nun düzeltebildiğini sayar; grup tohumla gelmeden üç çıkış isteği `not_learning` olur | B | — | E162 kod partisi | açık · `not_checked` sayılmaz (E162); bu denetlenen bir koşulun nedeni, dokunulmadı |
| E182 | Özetin kurulum alanları `seed_commit`, `seed_tree_sha256` `26c`'de yok; `25` 10b ve `26c` ilk dönemi `seed_epochs[]` satırı sayar. Kod kurulum alanlarını kurulum dönemi olarak tutar (başlatıcı E154 için `seed_commit`'i okur), `seed_epochs[]` sonraki teslimleri; dizi yoksa davranış eskisidir | S | — | E88 kod partisi | açık · metin 29/29b partisinde hizalanır |
| E183 | Taslak `29b`/`29e` (`docs/asama-0-daraltma-29-29b.md`) `seed_update`'i içerikle tanımlar ("yalnız tohum yolları değişmiş ve ağaçlar döneme eşit"); kod teslimin kendisini özetin adlandırdığı commit'le tanır (altındaki Kurucu commit'i onun adıyla yeniden yargılanmasın) ve sonraki push'larda teslim yollarını muaf tutar | S | — | E88 kod partisi | açık · taslak metin bu okumaya göre düzeltilir |
| E184 | Dönemden sonra başın tohumu son satırın commit'ininkiyle ağaç hash'iyle karşılaştırılıyordu; hash çalıştırma bitini atar: Kurucu'nun `spec/tohum` ya da `seed/` dosyasında yalnız mod değişikliği teslim sayılıp `own`'dan düşüyordu (kodun yanında `kind=code`, kabul edilmiş bir push'tan sonra tek başına `none` → `noop`); ağaç okunamayınca (güvensiz ya da UTF-8 olmayan ad) karşılaştırma hiç yapılmıyor, teslim Kurucu'nun `seed_modified`'ı sayılıp seri başlatıyordu | K | — | E88/E162 incelemesi | kapandı · `gitio.same_under`: `git diff --quiet <dönem commit'i> <baş> -- spec/tohum seed` (içerik, ad ve mod; ağacın okunabilirliğinden bağımsız); testler ve 2 mutant |
| E185 | E162'nin tablo testi "her satır ya kodda denetlenir (yeriyle) ya listededir" diyordu ama yalnız elle yazılmış bir sözlüğün anahtarlarını okuyordu: #yalniz'in `pre.append("exit_request_not_alone")` satırı silinince yeşil kaldı (denendi) | S | — | E88/E162 incelemesi | kapandı · her denetlenen satır `cli.py` ya da `decide.py`'deki satırlarıyla adlandırılır ve test o satırın kodda tam bir kez durduğunu ister; mutant `exit_alone_check_deleted` |
| E190 | `.gitignore`'un gerçek sırlar için yazılmış `secrets/` kuralı `seed/bootstrap/vectors/secrets/`'ı da gizliyordu: MF2'nin fikstürleri commit'e girmeyecek, grup dosyasız koşup her Kurucu'da kırmızı olacaktı (`git status` göstermedi, `git check-ignore` `.gitignore:29` dedi) | K | — | E161 kod partisi | kapandı · yalnız o dizin için istisna (`!seed/bootstrap/vectors/secrets/`; başka her `secrets/` hâlâ gizli, `git check-ignore` ile denendi); dizindeki sır biçimli her değerin FAKE taşıdığını tohum testi denetler (`SeedDataVectorsTest`) |
| E191 | `test_security_ledger` referans beynin `referee/`'sini `sys.path`'in başına koyuyordu; beynin yeni `profile/` paketi (MF4, MF6) aynı süreçte sonraki her test için standart kütüphanenin `profile`'ını gölgeliyordu (`import cProfile` → `AttributeError: module 'profile' has no attribute 'run'`, denendi) | S | — | E161 kod partisi | kapandı · yol sona ekleniyor; `test_its_profile_package_does_not_shadow_the_standard_library_here`, 1 mutant |
| E192 | `29d` "İkisi de tutmazsa vektör kırmızıdır" diyordu, yani yalnız ikisi birden tutmazsa; koşucu ve `29a` ("yalnız doğru girdide yeşil kalan vektör testi test değildir") biri tutmazsa kırmızı sayar | B | — | E161 kod partisi | kapandı · metin "Biri tutmazsa … (`29a`)"; koşucunun kuralı `DataRunnerTest` |
| E193 | `secrets.row_json_escape`'in fikstürü uzlaşılmış veride JSON'u çözülmüş duruyordu (`F` yerine `F`): ham satırda kimlik açıkça vardı, vaka kendi amacını ("ham satırda kimlik yok", kaçış çözülünce yakalanır) ve değişmiş girdisinin tanımını ("`F` → `&`, bir bayt") sınamıyordu; ham satırı tarayan bir uygulama geçerdi | K | — | E161 kod partisi | kapandı · fikstür vakanın tanımının pinlediği baytlarla (`F`; değişmişte `&`); beklenen değer değişmedi; iki kör uygulama bu baytlarda da beklenen değeri verir (E161 incelemesinden beri B repoda, her koşuda yeniden gösterilir); ham satırı tarayan kırık uygulama kırmızı (`row_scanned_raw`) |
| E194 | `profile`'ın daraltma kuralı iki okumaya açık: genel cümle (`14:15-17` "türetmesinden farklı her öneri reddedilir", güvenlik yollarını ve hariç dizinleri değiştirmek dahil; `01b:35` "türetmeden farklıysa reddedilir"; MF4'ün testi 19, `asama-0/09:43` "farklıysa ya da onları daraltıyorsa reddedilir") genişletmeyi de reddeder; özel kurallar (`14:43` "hiçbir öneri onu daraltamaz", `14:52` "yalnız genişletebilir", `30d:17-18` "ekleyebilir") genişletmeye izin verir | B | evet | E161 kod partisi, E161 incelemesi | karar (operatör, 2026-10-29): öneri yalnız genişletebilir, daraltma reddedilir · **kapandı (tohum)**, kararlar partisi 1: `14:14-19` ve `01b:35` güvenlik ve hariç yollara eklemeye izin verir, başka her farkta ret; `29k` aynı; vakası `profile.accept_widened` geri geldi (E210): yalnız genişleten öneri kabul, türetilen bir güvenlik yolunu da düşüren değişmiş girdisi ret, A ve B aynı değeri verir; şüpheci turu (E252): birim adaylarının sırası ve eklenen aday da farktır (`reject_reordered_unit_candidates`, `reject_added_unit_candidate`), eklenen yolun ağaçta olması gerekmez (`accept_widened_outside_tree`), güvenlik yolu daralmasının nedeni adıyla bağlı (`reject_narrowed_security`) · açık: donmuş `asama-0/09:43` (test 19) eski metniyle kalır (E180), tohum geçerlidir |
| E195 | `29d` `diffguard`'dan `asama-0/08` madde 1'in her nedenini ister; madde "diff beynin/entegrasyonun ucuna uygulanır"ı da sayar (`08:12`) ama `26a:25` `gate.diffguard`'a ağaç vermez, test 23 (`09:47`) de saymaz | B | evet | E161 kod partisi | kapandı · kararlar partisi 1: `29d` `diffguard` satırı ve `diffguard` paragrafı (`29g`, E251'den beri `29k`; `gate.diffguard` ağaç almaz, `26a:25`; başa uygulanma `gate.check`'in, MF8); donmuş `asama-0/08:12` değişmez (E180) · açık: başa uygulanmanın vakası yok: `k0map` arayüzü (`29h`) onsuz geldi, denetimin saf karara nasıl girdiği yazılı değil (E230) |
| E196 | `contained` grubu Kurucu'nun kendi bildirdiği argv izdüşümünü karşılaştırır (`29d`: gruba özgü kod yok); isteği izdüşüme yankılayan bir uygulama geçer; koşu başına taze dizin, sonucun dışarıda hash'i ve kırmızı kontroller (testler 20, 21) grupta değil | S | — | E161 kod partisi | sınır · vektör tabandır; gerçeği (B) #kirmizi #kanarya (`asama-0/14` Kum); `argv` rakip için çıktıda |
| E197 | MF2–MF7 sözleşmelerinin spec sessiz olduğu için bilerek sabitlemediği kurallar: `secrets` iki biçim dışı (düz parola ataması, E167); `profile` `test_path_rules`, sahiplik dosyasındaki güvenlik ekibi, genel otomasyon ve üretilmiş çıktı dizinleri; `npmlock` `deps_bytes` (tarball mı açılmış mı), yalnız sha1 bütünlüğü, depo içi `link`; `recipe` resmî araç zinciri imajı ile sürüm dosyası bağı, `lockfiles` ⊆ `inputs`, sınır değerleri; `diffguard` kökteki `.github/` vakasız | S | evet | E161 kod partisi | sınır · her biri spec yazılınca sonraki tohum döneminde vakaya döner; Kurucu fazlasını yapabilir, vektör tabandır (`29a`) |
| E198 | Hakem `/vec`'e bütün `vectors/` dizinini, `vectors.json` dahil, Kurucu'nun her kapsayıcısına bağlıyordu (testler, vektörler, modülsüz kırmızı, yeniden üreticiler): her vakanın `expect`'i okunabilirdi; argv'sine ve stdin'ine uyan vakanın cevabını basan altı üç satırlık modül 94/94 yeşil aldı | K | — | E161 incelemesi (kahin beyin, `run_vectors` + yerel koşucu) | kapandı · `vectors.fixtures`: `/vec` `vectors.json`'sız bir kopyadır (`run-tests`, `reproduce`); hakem beklenen değeri kendi kopyasından okur; testler ve 4 mutant |
| E199 | E161 incelemesinin veri koşucusu bulguları: (a) veri grubu, arayüz sayfası (`29f`, `29g`) Kurucu'nun tohumunda olmasa da koşuyordu (E88 açıkken tohumdan önce gelen vektörler Kurucu'yu hiç görmediği bir arayüzle reddederdi); (b) vektörlerin toplam süresi sınırsızdı (asılı kalan bir komut çağrı başına 2 × 120 s, `kos`'un 60 dk'sını aşıp Kurucu'ya hiç ulaşmayan kesinti olurdu; E18 yalnız testleri ve yeniden üreticileri sayar); (c) 1500+ seviye iç içe bir cevap satırı `RecursionError` ile `run-tests`'i çökertiyordu; (d) liste ve nesne içindeki değerlerin JSON karşılaştırmasını (`[true]` ≠ `[1]`) hiçbir test tutmuyordu | B | — | E161 incelemesi | kapandı · (a) sayfası ağaçta olmayan veri grubu `vector_group_missing` (uyarı, çıkışta ret); (b) `vectors.BUDGET_S` 1200 s (spec sessiz, seçim): bütçe biterken ilk asılı vektör kayıtlıdır, kalanlar `not_run:time_budget` ile kırmızı ve Kurucu'nundur, `kos`'un yarısını aşamaz; (c) derin satır "JSON nesnesi yok" (kırmızı); (d) iç içe değer testi; testler ve 9 mutant |
| E200 | `tohum/26c:54` ve `tohum/14:20` `install_scripts_required[]`'i adlandırıyor ama elemanının biçimini (paket adı, `ad@sürüm`, kilit yolu) söylemiyor; Kurucu tam kilit anahtarı ya da `ad@sürüm` seçti, çıplak adı reddetti (her sürümü işaretlerdi) | S | — | **Kurucu raporu** spec-012 (döngü 15, MF5 kabul) | karar (sahip): çıplak ad reddedilir · **kapandı**, kararlar partisi 1: `26c` (eleman kilitteki tam paket yolu ya da `ad@sürüm`; başka eleman, ör. çıplak ad, işaret değildir ve isteği kullanılamaz yapar) ve `29g` (`deps.fetch` çıkış 2, satır `{"ok": false}`); ilk metnin "hiçbir paketi işaretlemez" okuması E250'de düzeltildi; A ve B buna göre; vakalar `install_script_marked_by_lock_path` (paket 2'deki vakanın aynısı, E173'süz fikstürlerle) ve `bare_name_refused`; vakalara yer için `profile` ve `diffguard` `29k`'ye taşındı (E251); şüpheci turu (E252): işaret olmayan her eleman türünün vakası var (kilitte olmayan paketin çıplak adı, kapsamlı paketin çıplak adı, kilitte olmayan kilit yolu, kök `""`), kilitte eşleşeni olmayan `ad@sürüm` hiçbir şeyi işaretlemez (`26c`, vakası `name_version_not_in_lock_marks_nothing`) · sınır: `ad@sürüm`'ün sürüm biçimi yazılmadı ve vakasız: A `X.Y.Z` ister, B boş olmayan her sürümü alır (`snowball-fixture-a@latest` A'da çıkış 2, B'de işaret; denendi) |
| E201 | `asama-0/08` ölçüt 5 (HEAD'de en az bir düzeltilebilir lint ihlali) ile ölçüt 6 (lint 3/3 yeşil) çelişiyor (ESLint'te ihlal çıkış 1'dir); ayrıca ölçüt 4 ve 5 (kural kimliği, satır, `fix`; güvenlik yolu dışında düzeltilebilir ihlal) lint çıktısının ayrıştırılmasını ister ama `asama-0/14`'te bunu yapan MF yok — hiçbir MF doğrulamıyor | B | — | **Kurucu raporu** spec-013 (döngü 16, MF6 kabul) | açık (ölçüt 4–5) · kararlar partisi 1: Kurucu'nun okuması `26c`'de: lint yeşili, `lint_cmd` üç koşunun her birinde 0 ya da 1 ile biter ve üç koşunun çıkış kodu ve stdout'u bayt bayt aynıdır (ölçüt 5 ihlal ister, 6 yeşil); `asama-0/08` donmuş, değişmez (E180); ölçüt 4–5'in (kural kimliği, satır, `fix`; güvenlik yolu dışında düzeltilebilir ihlal) hangi MF'de doğrulanacağı açık |
| E202 | `tohum/26c:54` `toolchain`'i biçimsiz adlandırıyor | S | — | **Kurucu raporu** spec-014 (döngü 16) | kapandı · kararlar partisi 1: `26c` `toolchain` `node@X.Y.Z` (kesin sürüm; birimin en yakın sürüm dosyasındaki, Kurucu'nun sözüyle, E252; imaj etiketindeki sürüm de `X.Y.Z`); sürüm dosyalarının adları ve etiket biçimi (ör. `-slim`) yazılmadı, spec sessiz, E197'nin araç zinciri imajı ile sürüm dosyası bağı sınırı sürer; `asama-0/08` ölçüt 3'ün sürüm dosyası yarısını hiçbir MF doğrulamaz (`asama-0/08:57,61`; `29g` `recipe` nedenleri kapalı listedir) |
| E203 | Sistem gerçek hedefe uyamadığını kendisi bulmadı: birim modeli uyumsuzluğunu (E173) operatör, kabul edilmiş aletleri hedefte elle koşturarak buldu; Kurucu'nun aletlerini gerçek hedefte sınama ve kapsamını ölçme görevi yoktu. Sahip: "her yeni repoda o yok bu yok çalışmayacak" — eksik yeteneği sistem kendisi bulmalı, uygulamalı, test etmeli, hedefte doğrulamalı ve öğrenmeli | K | evet | sahip (2026-10-29) | açık · Kurucu talimatına genel görev (Nx'ten söz etmeden): kabul edilmiş, repo okuyan aletleri `/work/target`'ta salt okunur koş, kapsamı ölç, eksikte `missing_capability` + teşhis + genel adaptör + test + hedefte yeniden ölçüm; ölçülecek: kaç döngüde buldu, teşhisi doğru mu, çözümü hakemden ve hedeften geçti mi. Kalıcı tasarım (ilk temas kapsam raporu, ekosistem adaptörleri) Aşama 1 spec'inde |
| E204 | Sahip: bozulan her şey kök nedeninden ve mimari olarak onarılmalı; yama, geçiştirme, susturma olmamalı. Kurucu talimatında bu ilke, rakip protokolünde gizlemeyi çürütme sayan kural yoktu (testi zayıflatmak, atlamak, silmek; istisnayı yutmak; denetimi susturmak; fikstürü özel durum yapmak; sınırı yalnız geçsin diye büyütmek) | K | evet | sahip (2026-10-29) | kapandı · `prompt.md` "Kök neden, mimari çözüm"; `rival.PROTOCOL` "Hiding a defect is a defect" (yeniden üretici gizlenen hatayı gösterir); iki test, bir mutant; hakemin push'lar arası test zayıflamasını mekanik olarak ölçmesi (test sayısı, atlananlar) açık — sistemin kendisinin bulması beklenir |
| E205 | Sahip: tekrar ve dağınık kod olmamalı, benzer işler birlikte yapılmalı; her bilginin tek yetkili kaynağı; mimari ilkeyi (SoR, SSOT, SVoT, DRY, veri güveni ve sahibin saymadıkları) sistem duruma göre kendisi bulup seçmeli. Kurucu talimatında, rakip protokolünde ve tohumda bu yoktu | K | evet | sahip (2026-10-29) | kısmen kapandı · Kurucu: yazmadan önce benzerini ara, birleştir, tek kaynak, ilkeyi kendin seç ve `decision` satırıyla gerekçelendir; rakip: tekrar ve ikinci doğruluk kaynağı açık iddia, kopyalar ayrışıp hataya dönüşünce çürütme; iki test, bir mutant · katalog: `tohum/31`–`31h` (50 ilke, 6 aile: doğruluk ve veri sahipliği, tekrar ve uyum, sınırlar, değişim ve olay, güvenilirlik ve evrim, belge ve bilgi; her ilkede ne zaman/ne zaman değil, repoda işareti, mekanik denetimi, 140 kaynak — operatörün kopyasında); danışmadır, seçim Kurucu'nun; ajanın bu sisteme özel 5 önerisi tohuma girmedi, operatörün gizli fikir ölçütünde (sistem kendisi bulmalı); tohum dönemi 2 ile beyne |
| E206 | Sahip: repoya tam hâkim olunca sistem belge yazmaya başlamalı; var olan belgelere güvenmemeli, kullanmalı ama doğrulamalı (eski olabilir). Kurucu talimatında belge-kod ilişkisi yoktu | B | evet | sahip (2026-10-29) | kısmen kapandı · Kurucu: belge ipucudur, iddiası kod/yapılandırma/testle doğrulanır, tutmayan iddia "bayat belge" bulgusudur; hâkimiyetten sonra belge doğrulanmış haritadan üretilir ve kodla yeniden üretilir; test · açık: hedefte belge-kod sapmasını mekanik ölçen alet (Aşama 1+, `tohum/15` doküman üreticisinin hedefe genişlemesi) ve danışma kataloğunda "yaşayan belgeleme" |
| E207 | Repolar arası öğrenme ne kuruldu ne test edildi | K | evet | sahip (2026-10-29) | açık · **sahip: fikirleri sistem bulmalı** — sahibin ve operatörün bu konudaki fikirleri Kurucu'ya, tohuma ve herkese açık repolara yazılmaz; operatörün gizli fikir ölçütünde durur, sistem her birini kendi başına önerdiğinde tarih ve kanıtla işaretlenir (ölçü: kaç fikir, kaç döngüde); Kurucu talimatı yalnız kendi fikrini istemeyi taşır (kapanış adımı), test hiçbir fikrin yazılmadığını denetler; deney Aşama 1 sonrası |
| E208 | Sahip: sistemin ajanları ve becerileri (kendi yazacakları dahil) uzmanlıkta kesişip farklı sonuca varabilir; o zaman aralarında kanıt göstererek, dürüstçe çalışıp sonuç getirmeliler; her şey kanıt ve gerçek testle yürümeli. Kurucu talimatında ajanlar arası anlaşmazlık kuralı yoktu (Kurucu döngü 17'de kendi alt ajanlarını kullanmaya başladı) | K | evet | sahip (2026-10-29) | kısmen kapandı · talimat: oy, otorite, sıra değil; kanıt (test, yeniden üretici, ölçüm) karşılaştırılır, yetmezse ayırıcı deney; anlaşmazlık, kanıt ve sonuç deftere; test · açık: Kurucu'nun yazacağı ajanlar ve beceriler için bu kuralın hakem tarafında denetimi (Aşama 1+, ajan ve beceri organları) |
| E210 | `profile.accept_widened` (E194'ün vakası; 91239b3'te çıkarılan, fikstürleri `prop_widen.json` ve `prop_widen_drop_security.json` bayt bayt aynı) iş akışından tartışmalı geldi: karşılaştırılan iki sonuç A'nın E173'lü türetmesinin `differs:unit_candidates`'ı ile B'nin E173'süz türetmesinin kabulüydü. Aynı türetmede A ile B ayrışmıyor: E173'süz ikisi de kabul eder (değişmiş girdide `narrows:security_paths`; repodaki A ve B ile koşuldu), iş akışının E173'lü A ve B'si ikisi de `differs:unit_candidates` verdi, çünkü vaka göçmemiş `tree_t1`'i kullanır ve orada `packages/web`, `packages/api` manifestsizdir | B | — | kararlar partisi 1 (iki kör hesabın kayıtları) | kapandı · kararlar partisi incelemesinin yüksek bulgusu: tartışma iki ayrı birim modelinin karşılaştırmasıydı; aynı ağaçta iki kör hesap aynı değeri verir, vaka dışarıda kalmamalıydı. Vaka ve iki fikstürü 91239b3^'tekiyle bayt bayt aynı geri geldi (`29k`); bu ağaçta A ve B ikisi de kabul (çıkış 0), değişmiş girdide `narrows:security_paths` (çıkış 1) verdi (yeniden koşuldu). Yokluğu bağlayan test ve mutant (`test_no_profile_case_pins_widening_while_its_case_is_disputed`, `seed_pins_widening`) silindi; yerine kırıklar `widening_rejected` (genel okuma vakayı kırmızıya boyar), `security_narrowing_accepted`, `narrowing_accepted` (değişmiş girdi) ve mutantlar `seed_widening_case_widens_nothing`, `reference_profile_rejects_widening`, `blind_b_rejects_widening`. Paket 2 ağacı değiştirince vakanın değeri iki kör hesapla yeniden doğrulanır |
| E230 | MF8–MF13 sözleşmelerinin spec sessiz olduğu için bilerek sabitlemediği kurallar: `k0map` `asama-0/08` 1'in "diff `brain/integration` başına uygulanır" denetimi (E195 kararıyla MF8'in) saf karara nasıl girdiği yazılı değil; `fix` aralığının biçimi (`26c:48` vermez) ve lint çıktısını ayrıştıran MF yok (E201), koşu satırı normalleştirilmiş kayıt; `secret_in_diff` ve `refs`'in `check` işlemi vakasız; kök kaydının (`root.jsonl`) şeması yok (`26:14` zincirli der, `13:48-50`'nin öbür bağları şemasız), `verify` yalnız `root` ve `rekor_uuid`'i okur; neden adlarının çoğu (`k0map`'te 12'den 10'u, `root`'un dördü, `flaky`'nin kararları) spec'te yok, seçimdir; `refs`'in `forced` çıktısı da (E240). Vakayla sabitlenmiş iki okuma: `04a:24`'ün 3/3'üne ilk koşunun girip girmediğini spec söylemez, `flaky` ilk koşu artı üç yeniden koşu sayar (`07:27` doğrulamayı kırmızıdan sonraya koyar; E239); JSON Lines olmayan defteri `append` zincir kırığı sayar (`13:35` defter JSONL'dir, `01b:26-28` tutmayan denetim yazmaz ve sert durur; E238) | S | evet | E161 MF8–MF13 partisi | sınır · seçimler `29h`, `29i` ve `29j`'de yazılı; her biri spec yazılınca sonraki tohum döneminde vakaya döner; Kurucu fazlasını yapabilir, vektör tabandır (`29a`) |
| E231 | Nöbetçi yalnız testlere bakar (`tohum/07:26-27`, `asama-0/14:39`), ama geri alma provası `lint_regression` merge'ünü geri almak ister (`asama-0/10a:26`) ve `cause` `build_break`'i sayar; spec ne nöbetçinin `koş`unun lint toplamlarını ne `build_ok`'un üreticisini adlandırır (Aşama 0 tarifinde derleme komutu yok, `26c:54-55`) | B | evet | E161 MF8–MF13 partisi | açık · `cause` grubu ikisini normalleştirilmiş girdi olarak alır (`29i`); üreticileri MF14'ten önce bir tohum dönemi yazmalı |
| E232 | `01b:32` önceki satırların bayt bayt aynı kalmasını ister; `29a:71` `verify --previous`'ın neyi karşılaştırdığını söylemez, referans beynin MF1'i (`ledger/chain.py:211-217`) kanonik biçimleri karşılaştırır ve anahtarları yeniden sıralanmış satırı geçirir; `chain` grubunun vektörleri bunu sabitlemez | B | evet | E161 MF8–MF13 partisi | açık · MF10 baytları kendisi denetler (`append.refuse_reserialized_row`, kırık `append_only_canonical`); karar: `verify --previous` bayt mı kanonik mi, `29a` ve referans MF1 buna göre |
| E233 | MF8–MF13'ün ikinci kör uygulaması (B) repoda değil: 44 vakanın ikinci hesabı iş akışının kaydıdır (A ve B her vakada karşılaştırılan alanlarda aynı, her değişmiş girdide farklı), MF2–MF7'ninki gibi her tohum değişikliğinde yeniden koşmaz (E161 incelemesi) | B | — | E161 MF8–MF13 partisi | açık · B `local/blind_b/referee/`'ye eklenecek; onun da `gate/secrets.py`'si ve `ledger/chain.py`'si var, A'nınki gibi çakışma çözülerek. E236–E240'ın 12 vakası da B'de yalnız bu oturumda koşuldu (Kapanışlar "E236–E240"); `refs.update_never_forces` için B'ye `forced`'ı bildiren tek satır eklenmeli |
| E234 | `asama-0/14:47` (`stage0.json:14`) MF11'in MF10'u çağırdığını söyler (`10 → 11`); `26a:29` `rekor.anchor`'ın çağıranını `ledger.append` yazar, yani MF10 MF11'i çağırır; sıra kuralı (`asama-0/14:20`) ilkine göredir | S | evet | E161 MF8–MF13 partisi | açık · `root`'un fiilleri saftır, ikisine de bağlı değil; `asama-0` donmuş, düzeltme `26a`'da bir tohum dönemiyle |
| E235 | `refs.revert_first_parent_tree`'nin amacı geri alma commit'inin ebeveyninin `onto`'nun başı olduğunu söyler, ama fikstürde `brain/integration`'ın başı geri alınan merge'ün kendisidir: ebeveyni `merge_sha`'dan alan uygulama vakada ve değişmiş girdisinde yeşil kalır (A'da `"parents": [head]` → `[merge_sha]`, denendi); sözleşme merge_sha'nın baş olup olmadığını bilerek denetlemez (`07:23-24`, merge'ler sıralı) | S | — | E161 MF8–MF13 partisi | açık · sonraki tohum döneminde başı merge'den farklı bir `onto` vakası; bu partide vakalar ve beklenen değerler değiştirilmedi |
| E236 | `k0map`'in vakaları eşlenmiş satır tanımını (`asama-0/08:29-30`: "tanım tohumun `k0map` vektörleriyle sabittir") yalnız hem silen hem ekleyen hunk'lar için sabitliyordu: hiçbir fikstürde saf ekleme (`b = 0`) ya da saf silme (`d = 0`) hunk'ı yoktu. A'da `b = 0` hunk'ını `a ≤ L`'de bitmiş sayan, `d = 0`'ı `[c, c]`'ye ya da `[c, c-1]`'e eşleyen, ekleme hunk'larını kaydırmayan, `b = 0` hunk'ında eklenen satırın taban konumunu `a` sayan ve eklenen satıra `e+2`'ye kadar izin veren altı kırık 22/22 yeşildi (denendi); ilki hiçbir şey düzeltmeyip hedef satırın ardına yorum ekleyen adayı merge ederdi. `29h` `b = 0` hunk'ında `p`'yi `a+b`, yani `a` diye yazıyordu | K | — | E161 MF8–MF13 incelemesi | kapandı · `edge.patch` (git `-U0` çıktısı) ve üç `map` vakası, iki `decide` vakası (`insertion_not_distinguished`, `insertion_past_fix`); `29h` `b = 0` hunk'ını ve `p = a+1`'i açık yazar; 6 kırık, 1 mutant |
| E237 | `k0map.artefact_hash_mismatch` yalnız `base.jsonl`'ın manifesto hanesini, `k0map.tool_nondeterministic` yalnız `cand.jsonl`'ı değiştiriyordu; `29h` ikisini de her `koş` dosyasına uygular. Hash'i yalnız `base.jsonl` için ya da `checks.json` dışında denetleyen ve baytları yalnız aday koşularında karşılaştıran üç kırık 22/22 yeşildi; `koş`ta temiz koşuyla değiştirilmiş `cand.jsonl` (test 35'in artefakt hash reddinin durdurmak için olduğu şey) ilkiyle merge olurdu (denendi) | K | — | E161 MF8–MF13 incelemesi | kapandı · `forged_candidate_run`, `forged_checks`, `base_nondeterministic`; 4 kırık, 1 mutant |
| E238 | `29i` JSON Lines olmayan defter için iki cevap veriyordu: (1) geçerli zincir olmayan defterde sert duruş (`01b:26-32`, `13:53-55`), çıkış listesi ise "JSON Lines olmayan dosya"yı kullanılamaz girdi (2) sayıyordu. A `hard_stop: false`, B `true` veriyordu, vaka yoktu (denendi). A ayrıca stdin'i (1)'den önce okuyordu: kurcalanmış defter kullanılamaz istekle geldiğinde de sert duruş yoktu (B'de vardı; denendi) | K | — | E161 MF8–MF13 incelemesi | kapandı · `29i`: (1) stdin okunmadan önce, JSON nesnesi olmayan satır zinciri kırar; A buna göre; `refuse_unparsable_ledger`, `refuse_broken_chain_first`; 2 kırık, 1 mutant |
| E239 | `29i` "3/3 ilk koşu artı üç yeniden koşudur (`07`, `04a`)" diyordu; `04a:24-25` 3/3'ü üç koşuyla tanımlar, ilk koşunun sayılıp sayılmadığını söylemez: okuma spec diye sunuluyordu, E230'da seçim olarak yoktu ve vakalar onu sabitlemiyordu (`CONSIDERED = 3` 8/8 yeşil, denendi) | S | — | E161 MF8–MF13 incelemesi | kapandı · `29j` spec'in sessizliğini ve seçimi gerekçesiyle yazar, E230'a eklendi; `flaky.two_reruns_rerun`; 1 kırık, 1 mutant |
| E240 | `29h` `update`'in `PATCH {sha, force: false}` göndermesini ister (`07:16` "Zorla itme yoktur"), ama hiçbir çıktı gövdeyi göstermiyordu: `force: true` gönderen MF9 12/12 yeşildi (denendi); `brain/c/*` dallarında `non_fast_forward` kuralı yok (`01b`), zorla güncelleme geçmişi yeniden yazar | S | — | E161 MF8–MF13 incelemesi | kapandı · `refs`'in yeni çıktısı `forced` (`29i`), `refs.update_never_forces`; 1 kırık, 1 mutant |
| E241 | Başlatıcı bir sonucu ait olduğu başa bakmadan bir push'a yazıyordu: `STOP` hakemi beklerken gelince (ya da zaman aşımında, hiç başlamayan koşuda) `dispatch_referee` `still_running` döner, `fetch_result` en yeni imzalı sonucu, yani önceki başınkini indirir ve `cycle` onu yeni başın kararı diye günlüğe ve `pilot-metrics.jsonl`'a yazardı. Canlıda oldu: `d14b44a` (MF9) için hakem koşarken günlük "verdict accepted" yazdı, kabul `2be80ed`'ninkiydi | K | — | pilot, 20 döngülük koşu, döngü 6 | kapandı · `judge` yalnız başın kararını döner, değilse `None` ve "sonraki başlangıç önce onu yargılar" (E168); `test_an_unfinished_run_never_lends_an_older_heads_verdict`, mutant `launcher_lends_an_older_verdict`; yanlış ölçüm satırı düzeltildi |
| E242 | Tohum teslim yordamının komutu (`seed/founder/README.md` 4. adım `git archive S spec/tohum \| tar -x`) `core.autocrlf=true` olan Windows makinesinde LF dosyalara CRLF ekler: `git archive` dışa aktarımda satır sonu dönüşümünü uygular. Tohum dönemi 2'de operatörün hakem kopyası 262 dosyayı (`snowball_bootstrap`'ın 23'ü dahil) baştan sona değişmiş gösterdi; itmeden önce yakalandı. Dönem 1'in teslimi temizdi (beyinde CR baytı yok, denendi) | O | — | tohum dönemi 2 | kapandı · README 3. ve 4. adım: klonlar ve `archive` `-c core.autocrlf=false` ile, itmeden önce CR sayısı 0; açık: yordam elle koşulan komutlardır, tek bir `seed-deliver` komutu olmalı (sonraki parti) |
| E243 | Başlatıcı "oturum çalışamadı" ile "Kurucu push etmedi"yi ayırmıyordu: hesabın kullanım sınırı (CLI'nin kapanış sonucu `api_error_status: 429`, `api_error: usage_limit_reached`) oturumu durdurunca push'suz oturum boşta sayıldı ve iki tanesi pilotu durdurdu. Canlıda oldu: tohum dönemi 2'den sonra döngü 1 (49 tur, iş push edilmeden kayboldu) ve döngü 2 (1 tur, 0,8 s); kota operatörün iş akışlarıyla ortak | K | — | pilot, tohum dönemi 2'den sonraki koşu | kapandı · `usage_limit_wait`: CLI'nin söylediği sıfırlanmaya kadar (+2 dk, en çok 6 sa; sıfırlanma yazılı değilse 30 dk) bekler, boşta sayacına dokunmaz, ölçüme `api_error`; iki test, mutantlar `usage_limit_counted_as_idle`, `usage_limit_reset_ignored`. Açık: kota Kurucu, rakip ve operatörün ajanları arasında ortak; operatör pilot koşarken büyük iş akışlarını sınırlar |
| E244 | Kurucu vektörlerin girdilerini göremiyordu: `29f`–`29j` komutları `/vec/...` fikstürleriyle verir ve fikstürleri çapa sayar, ama kapsülde `/vec` yoktu. Kurucu bir vakayı hakemin koştuğu girdide koşturamıyor, sayfasıyla çelişen bir vakayı kanıtlayamıyordu; bir kez göremediği bir fikstüre uymak için açık geçen (fail-open) bir istisna yazdı | K | evet | **Kurucu raporu** f97; ajan tartışması: "girdi evet, cevap asla" | `gaps/fixtures-in-capsule`'da hazır, birleştirme bekliyor · `vectors.founder_inputs`: `fixtures`'ın dosyaları ve `cases.json` (her veri vakasının `id`, `purpose`, `cmd`, `stdin`, `fixture`, `changed.{description, cmd, stdin, fixture}`; `expect`, `expect_not` ve onlardan hesaplanan hiçbir şey yok); kendi girdisinin taşımadığı bir cevabı taşıyan fikstürde hiçbir şey yazmadan reddeder. Başlatıcı her oturumdan önce hakem reposunun `main` tarball'ından yalnız `vectors/`'ü açar (`filter="data"`), `<work>/vec`'i o fonksiyonla kurar, `/vec`'e salt okunur bağlar; alınamazsa oturum açılmaz. Prompt kuralları söyler · **sınır**: vektörler artık bir uygulamayı arama tablosundan ayırmaz; engeller rakibin taze girdili çürütmeleri ve prompt; özel durumlanmış girdiyi adlandıran çürütmeler ölçülür |
| E245 | Başlatıcının GitHub okumaları tek denemeydi: makinenin bağlantısı kesik kesik giderken hakem koşusunu yoklayan bir `gh run view` hata verdi ve `CalledProcessError` bütün pilotu durdurdu (2026-10-30 08:45Z, döngü 7, MF15 hakemdeyken); hakem koşusu GitHub'da sürdü, başlatıcı yoktu | K | — | pilot, döngü 7 | kapandı · salt okunur `gh` çağrıları `gh_read` ile yeniden denenir (10/20/40/60/60 s), sonra `GitHubUnavailable`; yoklama bunu `github_unavailable` sonucu, sonuç indirme `None` (başın kararı sonraki başlangıçta, E168), döngü arası kesinti 5 dk beklenir; yazma (`gh workflow run`) yeniden denenmez; iki test, mutantlar `github_read_never_retried`, `github_outage_ends_the_pilot`, `unfetchable_result_crashes_the_cycle` |
| E246 | Sahip: biri işe yaramayan bir şeye başlayıp duraklatmış olabilir, Snowball onu silmemeli; gerçekten aynı işi yapan parçalar birleştirilip kopyalar silinebilir, ama geliştirilen bir şey silinmemeli; her zaman geri dönüş imkânı olmalı. Tohum tersini planlıyordu: `01:50` "ölü kod sıfır", `03:16` K2 silmeleri, `18a:44` K2 silmelerini brüt silme tavanından muaf tutuyordu, K2'de yargıç araçtır (`10:54`) ve niyet savunması yalnız paneldedir (`04a:43-45`); `31e:24` Y4'ü hedefin koduna uyguluyordu; `asama-1/13b:18` çağıranı olmayan her kodu doğruluk ihlali sayıyordu. Hedefte yalnız testlerin import ettiği 61 dosyanın 43'ü son 90 günde değişmişti | K | evet | sahip (2026-10-30); salt okunur denetim, araştırma, şüpheci turu | onaylandı · dal `gaps/wip-and-data-guardrails` hazır, birleştirme ve tohum dönemi bekliyor · Y2: geri dönüş adımdan önce kanıtlı ve hiçbir sistem adımı onu sonradan kapatmaz, istisnasız (sahibin onayı da açmaz); Y4 sistemin kendisi içindir; `07a` tek kaynak (hedefin kodu, dokümanı ve verisi): kullanılmıyor olmak ölü olmak değildir, hangi sınıftan gelirse gelsin birim kaldırmak silmedir, yarım iş (planı ve tasarımı dahil) silinmez yalnız bildirilir (kanıt yükü silende), kopyalar yürütmeyle kanıtlanıp birleştirilir ve kaldırılan kopya için de yarım iş olmadığı kanıtlanır, eskimiş artık yalnız sahibin onayıyla, emin değilse tutulur; sahibin onayı beklenmez (Y8); veriyi yok eden adım önce arşiv ve süresiz, denenmiş yedek taşır; `01`, `02` (tohum önceliği), `03`, `10`, `15`, `18a` (istisna kalktı), `31e`, `31g`, `31h`, `asama-1/13b` `07a`'ya bağlı; ayrımın yolu sistemin |
| E247 | Sahip: Snowball veritabanı, arka uç, ön uç ve aralarındaki iletişimde (yaratma, okuma, güncelleme, silme) nasıl davranır? Operatörün beş korkuluğu (gerçek veri yok, yıkıcı DB değişikliği sahibin onayı ve geri dönüş kanıtıyla, sözleşme iki uçta ve sürümle, CRUD davranışı önce ve sonra testle, tablo ya da konu başına ikinci yazar yok) tohumda kısmen vardı: sandbox migration ayrımı yalnız E77'de, kapı migration ve şema yollarını adlandırmıyordu, kod düzenlemesi veritabanı şemasını değiştirebiliyordu, kırıcı sözleşme yasağı danışmaydı, testsiz kenar K5'ten önce (silmede K2'den önce) engellenmiyordu, yazar kuralı danışmaydı | K | evet | sahip (2026-10-30, "önerilerini de uygula"); salt okunur denetim, şüpheci turu | onaylandı · aynı dal · (1) Y3 `00:36-40`; (2) Y3 `00:36-37` (migration yok aynen, veritabanı şemasını değiştiren kod yok), `01b:18`, `01b:22-23`, `05:36-40`, `07a:43-51`; (3) `23:50-55`, eskinin kaldırılması silmedir (`07a`); (4) `05:23-28`; (5) `07:21-24` · beşi de kapalı geçer: kapının gösteremediği, yasaklanan sayılır · mekanizma (şema farkı, yazar haritası, sözleşme testi, test veritabanının kurulması) sistemin |
| E248 | Yakalama (E168) kararı alamayınca başlatıcı yine de oturum açıyordu: kesintide `judge` `None` döndü, Kurucu eski kararı (`a049954` kabul) okuyup MF16'yı yazdı; MF15'in reddini (`f07f215`, rakibin kanıtladığı `decimal.Overflow`) hiç görmedi ve hakem `d0dc433`'ü `refutation_still_reproduces` ile reddedip `repeated` saydı: Kurucu'nun öğrenme ölçüsüne altyapının hatası yazıldı. Aynı sınıf: hakemi tetikleyen `gh workflow run` (yazma) kesintide `CalledProcessError` ile başlatıcıyı düşürürdü | K | — | pilot, 09:08Z kesintisi | kapandı · yakalama kararsızsa `NoVerdict` (oturum yok), tetikleme hatası `GitHubUnavailable`; ikisi de `Outage`, bekleme ve yeniden deneme; iki test, mutantlar `catch_up_session_works_blind`, `dispatch_failure_crashes`. Ölçüm notu: `d0dc433`'ün `repeated`'i Kurucu'ya sayılmamalı (günlükte işaretli) |
| E249 | Sahibin süren geliştirmesi Aşama 0–1'de içeriğiyle görülmüyor: `brain/integration` hedefin `main`'inden bir kez kesilir, senkron Aşama 2'de ölçülmüş ihtiyaçla açılır (`07:8-16`); taban yaşı yalnız süre ve commit sayısıdır. Harita kenarını `stale` yapan yalnız sistemin kendi diff'idir (`13:24`), sahibin `main`'deki değişikliği bulguları, kenarları ve dersleri bayatlatmaz. Pilotta hedef kopyası da sabit bir anlık görüntüdür | S | — | sahip sorusu, 2026-10-30 ("proje sahibi geliştirmeye devam ederse Snowball neyin nasıl değiştiğini biliyor mu, hafızasını güncelliyor mu") | kısmen · geri bildirim halkası (`17`: eskimiş bulgu oranı satırı) ve okuma erişimi (`07`: `main`'i okumak dokunmak değildir) onarıldı (E304: yalnız kopan halka); bayatlık senkrondan önce sayıdır, senkronla görünümdür (`13:24`); sinyalin yeniden hesabı operatörde, yayımlanmaz; ölçü: commit sayısını (E270) ve `17` sinyalini kaç döngüde ürettiği · uzman tartışması (öneren, şüpheci, hakem; 2026-10-30): önerinin `13` düzenlemeleri, #sahip-isi çıkış satırı, merge-0, zincirli bayat satırlar ve operatörün ekeceği commit reddedildi (cevabı önceden yazıyorlardı, E244) |
| E250 | Kararlar partisi 1'in `26c` ve `29g` metni çıplak adın "hiçbir paketi işaretlemediğini" yazıyordu; sahibin E200 kararı çıplak adın reddidir (istek kullanılamaz, çıkış 2), Kurucu'nun kabul edilmiş MF5'i ve iş akışının iki kör uygulaması da böyle. Ana daldaki A ve B kilit yolunu işaret saymıyor, çıplak adı yok sayıyordu: `node_modules/snowball-fixture-b` işaretiyle `install_script_unmarked`, `["snowball-fixture-b@2.0.0", "left-pad"]` ile çıkış 0 (denendi); paketin metni kilit yolunu işaret sayarken hiçbir uygulama ve vaka onu bağlamıyordu. `29g`'nin çıkış 2 listesi ("okunamayan kilit ya da ayna") biçimi tutmayan stdin'i de saymıyordu (A ona zaten çıkış 2 veriyordu) ve 2'nin satırını yazmıyordu | B | evet (E200) | kararlar partisi incelemesi (orta) | kapandı · `26c`; `29g` (çıkış 2: okunamayan kilit ya da ayna, biçimi tutmayan stdin, işaret olmayan eleman; 2'de satır `{"ok": false}`); A iş akışının A'sının satırlarıyla (`NAME_AT_VERSION`, kilit yolu eşleşmesi, işaret denetimi), B iş akışının kör B'sinin aynı işi yapan satırlarıyla (`_validate_marks`, kilit yolu eşleşmesi; E173 kısımları alınmadı); vakalar `install_script_marked_by_lock_path` ve `bare_name_refused` (geçerli işaretin yanında çıplak ad: onu yok sayan ya da her sürümü işaretleyen okuma `ok: true` verir); 5 kırık, 4 mutant; paket 2'nin (yerel, bekletiliyor, E203) referans A'sında çıplak ad hiçbir şeyi işaretlemez (çıkış 1) ve onu kaydeden bir satırı var; o satır bu dalda yoktur, paket bu ağaca taşınırken satır da A'nın o ayrılığı da düşer · sınır: vektör çıkış kodunu karşılaştırmaz (`29d`); vaka reddi `ok` ile ayırır, 1'i 2'den ayırmaz · kilitte eşleşeni olmayan `ad@sürüm` (A'da da B'de de kabul, hiçbir şeyi işaretlemez) burada "vakasız" sayıldı; yanlıştı, dört vaka onu bağlıyordu, `26c` yazmıyordu: E252'de yazıldı ve kendi vakasını aldı |
| E251 | E200'ün iki vakası `29g`'ye, `accept_widened` `29f`'ye sığmıyordu (sayfa 80 satırı geçerse bölünür, `tohum/15` 1) | S | — | kararlar partisi 1, ana dal üstüne | kapandı · `profile` ve `diffguard` yeni `29k`'de ("yol kuralları"; paket 2'nin bölünmesiyle aynı gruplama); `29f` `secrets` ve `contained`, `29g` `npmlock` ve `recipe`; `29d`, `29h`–`29j`'nin göndermeleri (diff `29k`'deki gibi okunur), `INDEX.md`, `00b`, `vectors.json`'un `interface`'i, `VECTOR_PAGES`, A'nın iki satır göndermesi; mutantlar `split_page_drops_a_case`, `group_points_at_the_page_it_left`, `new_vector_page_29k_not_indexed`, `npmlock_page_drops_the_bare_name_case`. Teslimde `29k` hakemin yeni `vectors.json`'uyla birlikte gider (sayfası beyinde olmayan `profile` ve `diffguard` `vector_group_missing` olur, E199). Paket 2 bu ağaca taşınırken kendi `29h` bölünmesini `29k`'ye uyarlamalı ve `install_script_marked_by_lock_path`'in kopyasını düşürmelidir |
| E252 | Kararlar partisi 1'in şüpheci incelemesi (9c0aaac üstünde): sayfaların yazdığı birkaç kuralı hiçbir vaka bağlamıyordu, onları çiğneyen Kurucu okumaları A'nın düzenlenmesiyle 210/210 yeşil kalıyordu. `npmlock`: kilitte olmayan kilit yolunu (`node_modules/left-pad`) işaret saymak, yalnız kilitteki paketin çıplak adını reddetmek (`left-pad` geçer), `ad@sürüm`'ü `"@" in` ile tanımak (`@types/node` geçer), kök `""`'i işaret saymak. `profile`: `unit_candidates`'ın genişlemesine izin vermek, onu küme olarak karşılaştırmak ya da hiç karşılaştırmamak (`14` ve `29k` farkı reddeder), eklenen yolun ağaçta olmasını şart koşmak, `narrows:security_paths`'i başka adla yazmak (yalnız `expect_not`'ta geçiyordu). Ayrıca: `bare_name_refused`'ın değişmiş girdisi betiksiz `a`'yı işaretliyordu (`30c:22` okumasıyla çatışır); kilitte eşleşeni olmayan `ad@sürüm` dört vakada (`license_from_tarball`, `registry_not_allowed`, `git_dependency`, `file_dependency`: kilitlerinde `b` yok, işaret `snowball-fixture-b@2.0.0`) kabul diye bağlıydı ama `26c` yazmıyordu, "tarball'ın `ad@sürüm`'ü"nün katı okuması dördünü kırmızıya boyar (E250 onu vakasız saymıştı); B'nin iki yorumu `tohum/14:47-49` (artık 49-51), A'nınki `29k:38-39` (artık 42-43) diyordu; E250 yalnız paket 2'de olan bir satıra gönderme yapıyordu; sayfa uzunluğu testi yalnız `29f`–`29k`'yı tutuyordu, `29` 84, `CHANGELOG` 82 satırdı (`tohum/15` 1) | B | — | kararlar partisi 1 şüpheci incelemesi | kapandı · değerleri A ve B'nin aynı verdiği (çıkış kodları da aynı) dokuz vaka: `npmlock` `bare_name_not_in_lock_refused`, `scoped_bare_name_refused`, `lock_path_not_in_lock_refused`, `root_key_refused`, `name_version_not_in_lock_marks_nothing`; `profile` `reject_narrowed_security`, `accept_widened_outside_tree`, `reject_reordered_unit_candidates`, `reject_added_unit_candidate`; `bare_name_refused`'ın değişmiş girdisi `b`'nin kilit yolu; `26c` (kilit yolu kök `""` dışında bir `packages` anahtarı; kilitte olmayan yol işaret değildir; eşleşeni olmayan `ad@sürüm` hiçbir şeyi işaretlemez), `29g`, `29k` (aday listesinde sıra da ekleme de fark; eklenen yol ağaçta olmasa da genişletmedir); sayfa uzunluğu testi bütün `spec/`'i tutar (üretilmiş `INDEX.md` hariç), `29` yeniden sarıldı (kelimeler aynı, koltuk promptları dokunulmadı), `CHANGELOG`'un E260 girdisi tek satır; `mutate.py` bütün `spec/`'i kopyalar; 11 yeni kırık, 20 mutant · E202: `26c`'nin "birimin dizininden köke doğru en yakın sürüm dosyası" ifadesi Kurucu'nun kendi sözüne ("en yakın sürüm dosyası", spec-014) indi: paket 2'nin bekletilen kilit kuralıyla aynı kalıp E173'ün yarısını ima edebilirdi (E203) · sınır: kilit yolu işaretini paket adıyla okuyan okuma (`node_modules/x` her derinlikteki `x`'i işaretler) ayırt edilmez; ayırmak iç içe bir kilit yolu ister, o E173'ün fikstürüdür ve paket 2'de bekler; E250'nin sürüm biçimi ve çıkış kodu sınırları sürer |
| E260 | Yeniden üreticinin kutbu tanımsız: hakem yalnız bir metnin görünüp görünmediğini görür, belirti mi doğru çıktı mı olduğunu göremez. Rakip beklentiyi testin beklentisi gibi (doğru çıktı) yazınca açık iddia kusurlu başta görünmedi, düzeltmede göründü; E07 (c) düzeltmeyi kanıtlanmış kusur yapıyor, E08 sonra her doğru başı `refutation_still_reproduces` ile reddediyordu (kalıcı ret döngüsü). Aynı karışıklık doğru kodda yanlış iddiayı hemen kanıtlar | K | evet | **Kurucu raporu** f102 (iddia `87c088321252`, anahtar `027465767d2d46dc`; 86cc8b4'te gösterilmedi; düzeltme f668776 koşu 40967821066'da `refutation_reproduced` ile reddedildi, rakip `not_refuted` dediği hâlde; döngüyü operatör 40969705356'da `waived_refutations` ile elle kırdı) | karar bekliyor · `gaps/reproducer-polarity` hazır, operatör onayı ve birleştirme bekliyor (E07 (c)'yi değiştirir) · kanıt yalnız yeniden üreticinin yargılandığı başta: belirti kod yüzünden görünür (boş ağaçta görünmez), doğru çıktı görünmez; açık iddianın sonraki baştaki gösterimi gözlem (baş, `shown`, `contradicted`), sonraki rakibe ve çıkışta operatöre verilir; rakip her açık iddiayı yeniden gönderebilir, incelenen başta yargılanır, aynısını göndermek yeniden yazma sayılmaz; iki taraflı sözleşme (`expect_*` belirti, `correct_*` doğru çıktı, belirtinin bir gözlenenini adlandırır, taraflardan biri ötekinden çıkamaz; tek kural `rival.side_holds`, doğrulayıcı ve koşucu ortak); E08 aynen: kanıtlanmış kusur belirtisi göründükçe engeller, baş yanında doğru çıktıyı yazsa da; alanların tek kaynağı `rival.REPRODUCER_FIELDS`; anahtar ve durum şeması 3 aynı · sınır: iki tarafı bilerek ters yazan yeniden üretici doğru kodda yine kanıtlar (anlam, mekanik değil) |
| E270 | MF14–MF18 sözleşmelerinin spec sessiz olduğu için bilerek yaptığı seçimler. `revert_drill`: HMAC'in SHA-256 olması, anahtarı tohum ve iletisi `cycle_id` (taahhüdü yazan önceki devrin kimliği), kod noktası sırasında `mod N` eşlemesi (N = 3'te 256 ≡ 1 olduğu için hiçbir vaka bayt sırasını ayıramaz; sayfa büyük-sonlu der), katalog biçimi, anahtar `{cycle_id, selection, instance_id, cause}`, `commit`/`reveal` ayrımı (`commit`'in anahtarı yazmaması sayfa kuralıdır, veri koşucusu sabitleyemez), satır sözcükleri, neden adları, "önceki devir"in yalnız zincir sırası olması; `not_planted` vakasız (son ekme ve ondan önceki son taahhüt `last_of_several_drills`'te, inceleme 6). `prompt`: şablon biçimi, tek geçişli RFC 8785 yerleştirme, bildirilmeyen alanın reddedilmeyip düşmesi, hash'in yalnız kurulan metni kapsaması (rakip sistem metnini de hash'ler, `rival.py:748`), mikroya çevrilmiş bütçe, `min(çağrı tavanı, kalan)`, neden adları; sunulan model, 429 ve `cost` satırı (test 37) grupta değil, `argv` karşılaştırılmaz (E196'nın sınırı). `status`: düzenleme tespiti (`events`/`status` satırındaki blok hash'i), işaret satırları, `status_edited`, `cycle_start` ve `decision` türleri, taban yaşının yalnız süre olması (`07:12-13`'ün commit sayısının Aşama 0'da üreticisi yok), insan dokunuşunun `imports.jsonl`'ın her satırı olması (spec öbür dokunuşları da o sayaca koyar, satırlarının biçimi yok: E277), birden çok `status` satırında sonuncusu (`last_status_row`, inceleme 6); bloğun görünümü karşılaştırılmaz. `genesis`: kayıtlı API'yle kuru koşu, `rules/branches` ve `current_user_can_bypass` (`01b:59-60`) dışındaki uç noktalar (`rulesets/{id}`, `actions/workflows`, `actions/permissions`), yazma modu şartının (`25a:18`) genesis'te denetlenmesi, `bypass_actors`'ın okunmaması (GitHub onu yalnız ruleset'e yazma erişimi olana verir, yazar App'i `administration:read`, `25:22`), on iki yük anahtarı, hash biçimleri, türe göre taban, son aktarım satırı, neden adları; (A)'nın Rekor kimlikleri, `25a` 5. satırın App beyanı (özette alanı yok), öbür aktörlerin bypass'ı, mandal tabanı ve hazır adaylar grupta değil | S | evet | E161 MF14–MF18 partisi; inceleme 6 | sınır · seçimler `29m`, `29n` ve `29o`'da yazılı; her biri spec yazılınca sonraki tohum döneminde vakaya döner. Kurucu fazlasını yapabilir, vektör tabandır (`29a`), `genesis`'in okumaları dışında: kayıtlı API kapalı listedir, okumada tavandır (`29o`); bu yüzden spec'in genesis'e okuttuğu her olgu (`asama-0/10a:16`, `25a:17-20`, `25a:29-30`) listededir, yenisi önce listeye girer (inceleme 6) |
| E271 | `26:9-10` alan adı tanımını yalnız `26`, `26b`, `30d` ve `30e`'ye bırakır; MF14–MF18'in vektörleri `26`'da olmayan satırları okur: `drill`/`commit` ve `drill`/`plant` (`commitment_sha256`, `instance_id`, `merge_sha`), `events`/`revert` (`payload.merge_sha`), `events`'in `cycle_start`, `decision`, `status`, `status_edited` türleri ve yükleri, genesis yükünün on iki anahtarı. `26:74-75`'in tek drill yükü `instance_id`'yi zorunlu tutar: koşudan önce açık deftere yazılan taahhüt onu taşırsa ekilecek merge'ü koşudan önce adlandırır (`25:15`). Test 14 (`asama-0/09:38`, MF18) bu satırlarda `26` değişmeden geçemez | K | evet | E161 MF14–MF18 partisi | açık · aynı tohum döneminde `26`'ya bu satırlar; drill yükü taahhüt ve ekme satırını ayırmalı; `root/ledger.jsonl`'ın `q4` satırı (taahhütte `instance_id`) yalnız bölüm uçlarını okuyan `root`'un fikstürüdür, emsal değil |
| E272 | `status.md`'deki elle düzenlemeye spec üç cevap verir: `asama-0/14:43` ve `asama-0/09:66` (donmuş) sonraki devirde yeniden üretip `events`'e yazar; `15:16` üretilmiş sayfanın düzenlenmesini zincir kırığı sayar; `01b:37` elle düzenlemeyi reddeder ve `01b:27-29` tutmayan `brain/state` denetiminde yazmayıp sert durur | B | evet | E161 MF14–MF18 partisi | karar bekliyor · `status` grubu Aşama 0'ın kuralını izler (çıkış 1, `status_edited`, yeniden üretim, sert duruş yok); karar sahibin; `01b` paralel partide (`gaps/owner-decisions-p1`), bu dal ona dokunmadı |
| E273 | Vektör bütçesi (E199 b, `BUDGET_S` 1200 s) bütün gruplarla aşılabilir: bütün MF'ler bitince push başına 264 vektör sonucu (veri 258, `chain` 6). İnceleme 6'ya kadar her sonuç bir kapsayıcıydı: E161'in en kötü ölçümüyle (5,0 s) 258 çağrı 1290 s, bütçe biterken ilk koşmayan, sırada son grup olan `genesis` olurdu (denendi: `test_the_seed_vectors_fit_the_budget_at_the_worst_measured_call` düzeltmeden önce 1290 > 1200). Bugün aynı komut ve stdin bir push'ta bir kez sorulur: 208 çağrı, 5,0 s'de 1040 s. Yüklü makinede ölçülen çağrıyla (inceleme 6, gerçek kum, başka oturumların kapsayıcıları koşarken: 7,6–14,2 s, ortalama 9,9 s) yaklaşık 2070 s: bütçeyi aşan push'ta kalan vektörler `not_run:time_budget` ile kırmızıdır ve Kurucu'nundur | K | evet | E161 MF14–MF18 partisi; inceleme 6 | açık · azaltıldı: bir push aynı girdiyi yeniden sormaz (`VectorRun.answers`, yalnız cevaplar; mutantlar `vector_inputs_asked_twice`, `vector_no_answer_remembered`), tohumun çağrıları × 5,0 s ≤ `BUDGET_S` testle tutulur (mutant `vector_budget_below_the_seed`). Kalan: gerçek koşucuda (Actions) çağrı süresi ölçülmeli; karar: bütçe ya da çağrı başı maliyet (her çağrıda yeni kapsayıcı ve `venv`) |
| E274 | MF14–MF18'in ikinci kör uygulaması (B) repoda değil (E233 gibi): 24 vakanın ikinci hesabı iş akışının kaydıdır; bu oturumda B (`wf5/B/<grup>/referee`, değiştirilmeden) gerçek veri koşucusunda 48/48 verdi, ama her tohum değişikliğinde yeniden koşmaz | B | — | E161 MF14–MF18 partisi | açık · B `local/blind_b/referee/`'ye, `ledger/` ve `gate/secrets.py` çakışmaları çözülerek (E233 ile birlikte) |
| E275 | Tohumun içe aktarıcısı `setup/imports.jsonl`'a `26c:37-38`'in satırını yazmıyor: `importer.py:71-76` `{brain_sha, referee_tree_sha256, referee_bytes, toy_bytes, result_head}` yazar, zincirsiz; `ts`, `stage`, `result_sha256` ve `toy_tree_sha256` yok. MF18 son satırın `result_sha256`'sını bağlar (`asama-0/10a:17`): gerçek aktarımdan sonraki genesis kullanılamaz girdiyle durur (A'da çıkış 2, `{"ok": false, "hard_stop": true, "payload": null}`; denendi); MF16 yalnız satır sayar | K | — | E161 MF14–MF18 partisi | açık · `importer.py` `26c:37-38`'in zincirli satırını yazmalı, testi ve mutantıyla (E104: `imports.jsonl`'ın şeması); vektörler `26c`'yi izler, bu partide tohum kodu değişmedi |
| E276 | `22a:51` ekilen kötü merge'lerin "tohumun prova fikstürlerinden" geldiğini söyler ve `asama-0/10a:26` (#geri-alma) oyuncakta üç kategoride (`test_regression`, `build_break`, `lint_regression`) birer ekilmiş merge ister; tohumda böyle fikstür ve biçimi yok (`seed/drill/` yalnız ders provası yargıcı) | K | — | E161 MF14–MF18 partisi | açık · MF14'ün kataloğu `29m`'nin biçimiyle (`{instances: [{id, cause, …}]}`) ve oyuncağa uygulanan yamalarıyla bir tohum dönemi getirmeli; vektörler kendi taklit kataloğunu taşır |
| E277 | İnsan dokunuşu sayacının aktarım dışı satırı tanımsız: `27:19` ve `asama-0/12:38-39` tohum dönemini, `stage-open`'ı, dürüstlük anahtarını ve sert duruş kalkışını sayaca koyar; `26c:38` ve `27:56` sayacı `setup/imports.jsonl` diye adlandırır. Ama `26c:37` yalnız aktarım satırının biçimini verir, `27:56` dosyanın yazanını yalnız `import` sayar, `25:28` tohum döneminin "dokunuş satırı"nın, `25:55` kurtarmanın sayaca nasıl yazıldığını söylemez. Bugün sayaca aktarım dışı satır yazan yok: `status` bloğu ve PASS raporunun insan dokunuşu sayısı (`asama-0/10a:31`) yalnız aktarımları sayar | B | evet | inceleme 6 (E161 MF14–MF18) | karar bekliyor · `29n` sayacın her satırını bir dokunuş sayar, `29o` genesis'i son aktarım satırına (`referee_tree_sha256` taşıyan) bağlar ve öbür satırları atlar; vektörlerde aktarım dışı satır yalnız `ts`, `stage` ve zincir alanlarını taşır (seçim). Karar sahibin: aktarım dışı satırın biçimi ve yazanı (`seed-epoch`, `stage-open`, kurtarma) `26c`'ye; `26c` paralel partide (`gaps/owner-decisions-p1`), bu dal ona dokunmadı |
| E280 | Kurucu defteri denetiminin spec'in bıraktığı seçimleri ve canlı defterin kabul edilmiş bozuk satırı: hakem satırları denetlemeden önce MF17 push'uyla (6f8cef2) kabul edilen f185 `kind: learning` taşır (test 30'un kümesi dışında; Kurucu seed-006'da kümenin kapalı olduğunu bildirmişti); çıkış kapalı kalır, Kurucu ekleyerek düzeltemez | K | evet (f185) | E162 devamı | kapandı · `gaps/stage0-exit-decisions` · uygulayıcının seçimi, şüphecinin (b) biçimi, kanıtı tuttuğu için (sahip seçmedi; birleştirme onun incelemesidir): `learning` kümeye eklenmez (okuyucusu ve kararı `decision` satırınınkilerdir; `29b`'de `learning` ölçünün adıdır; ders deposu ilk okuyucusuyla açılır, `13`, `22`, `26b`); kabul edilmiş ama anlamı bozuk (`part`, `kind`, `supersedes`) satır sonraki geçerli satırın `supersedes`'iyle kapanır, yeni kural olarak `13` "Kurucu defterinde kapatma"da, alan `26`'nın `founder` satırında (`derived_from` soy alanıdır, kapatma değil); bayt, JSON ve zincir kırığı kapanmaz, Kurucu'ya sayılmaz; kapatılmamış anlam kırığı Kurucu'nundur; kapatan satır çıkış isteğiyle de gelir, çıkış `why`'da `L<n> superseded by L<m>` yazar; kabul edilmiş satır yüzünden hiçbir push reddedilmez; feragat, etkin tarih kuralı ve çıkışı kapalı bırakmak reddedildi · canlı (beyin `3f605a1`, son kabul `3f01932`, 265 satır): iki kabul edilmiş anlam kırığı, L185 ve L263 (ikisi de `kind: learning`); push denetimi `[]`, çıkış ikisi kapanana dek kapalı · teslim sınırı: kuraldan önce yazılıp henüz kabul edilmemiş bozuk satır push'un eklediği satırdır ve kapanmaz; her push'u reddeder, Kurucu onu kabul edilmemiş kuyruğunu yeniden yazarak düzeltir (`asama-0/10` #kurucu-defteri yalnız son kabule göre eklemeyi ister); bu yüzden tohum dönemi 3b, beyin `main`'inin defteri son kabul edilmiş commit'inkiyle aynıyken (başlatıcı durmuş) teslim edilir |
| E281 | `asama-0/10:20` "tohumun sınırlı YAML altkümesi"ni adlandırır ama hiçbir sayfa tanımlamaz (Kurucu raporu seed-035) | B | — | E162 devamı; Kurucu raporu seed-035 | açık · seçim kodda (`wiring.py` belgesi: GitHub'ın ve tohumun aynı baytı farklı okuyabileceği her biçim reddedilir); `29b`/`29e`'ye yazılması tohum partisinin işi |
| E282 | Tohumun `control` komutunun döngü için arayüzü yok (`asama-0/01` D0, `asama-1/13:52` tohuma taşıdı): canlı `loop.yml` `control --control ../control.json --job --event --github-output` çağırır, tohumun ayrıştırıcısı yalnız `--root` alır, `paused` yoktur; "her işin ilk adımı `control`, kill switch açıkken iş durur" kuralına hiçbir dosya tutulamaz (Kurucu raporu seed-035) | K | — | E162 devamı; Kurucu raporu seed-035 | kapandı · `gaps/stage0-exit-decisions` · tohumun `control`'ü döngü arayüzünü taşır (yeni `29p`: `--control --job --event --github-output`; kill switch, fren, bilinmeyen tetik ya da iş çıkış 2 ve iş durur; `loop_schedule` tam `true` değilken zamanlanmış koşu `go=false`, elle tetikleme `go=true`); Kurucu'nun raporundaki çağrı benimsendi; `wiring` her işin ilk adımını tohumun adımıyla bayt bayt, sonraki adımları `go` koşuluyla, adımın üstünü izin listesiyle denetler (E296: yasak listesi `services`'i kaçırıyordu); `not_checked:is-akisi` kalktı; canlı `loop.yml` geçer |
| E283 | "Sırlı iş kod koşturmaz" dosyayı okuyarak karar verilemez | B | — | E162 devamı | açık · karar verilebilir okuma kodda: `tohum/08` ve `01a`'nın beş işi tam, kod koşturan `getir` ve `kos` `permissions: {}` ve sırsız, sır, `id-token` ve yazma kapsamı yalnız `cagir` ve `yaz`'da, sırları sayan ya da miras veren biçim yok, dizinde yalnız `loop.yml`; öbür `.github/` dosyaları ve içe aktarmanın sır-iş haritası E132'de |
| E284 | #genellik girdileri ve seçimleri: canlı özette `targets[]` yok (operatörün adımı, `25` 10a, E99) | B | — | E162 devamı | açık · denetim kodda (`config.load_summary` `targets[]`'ı `26c`'nin tam anahtarlarıyla okur, yanlış yazılmış anahtar durdurur; ad `exitchecks.fold`'la katlanmış alt dizgi olarak her `referee/` yolunda ve her dosyanın metninde aranır, metin olmayan dosya `referee_file_not_text` (E291); adlar imzalı sonuçta hiçbir koşulun sonucunda açık yazılmaz, `sha256:<ilk 16 hane>` (E290)); `targets[]`'ta kopya hedef ya da onun `identifiers`'ı yokken `not_checked:genellik`, Kurucu'ya sayılmaz; kalan iş operatörün adımıdır (özete `targets[]`, kopya hedefin `identifiers`'ıyla); E293'ten sonra yeni bir pilot onsuz başlamaz |
| E285 | #agac seçimleri ve canlı beyinde oyuncak alt ağacı yok | B | — | E162 devamı | açık · seçimler kodda: `bootstrap` ayrılmış ad (aktarım önyükleme hakemine dokunmaz, `10a` #aktarim, `01a`), fikstür istisnası yok, ajan yapılandırması `29f`'nin tanımıyla; Windows takma adları E130'da, oyuncaktaki ajan yapılandırması E131 (B)'de; canlı beyinde `tests/fixtures/toy-repo/` yoktu (`toy_tree_missing`, Kurucu'nun eksiği, `24a:54`), Kurucu ekledi (`517b39d`: oyuncak hash'i `6d234f7d…`, #agac geçer) |
| E286 | #spec: `tohum/02`'nin mekanik maddelerinin (bölüm nasıl tanınır, Türkçe metinde "eşik" nedir) makine tanımı yok; denetimin kök yeri dondurmadır, çıkışta bulunan donmuş spec kusurunu Kurucu düzeltemez (`spec_changed_after_freeze`, E180); `29b:69-70` `referee/`'den `spec.lint` koşar, `10:29` ile çelişir (taslak `29e` çözer); `27`/`27a`'da oyuncak repo okuyucusu yok (E156) | K | evet (yer) | E162 devamı | açık · `not_checked:spec` bu satırın nedeniyle; değerlendirme (`gaps/stage0-exit-decisions`): bölümün ve eşik anahtarının metinde tanınması tanımsız, §0.13'ün dosyaları makinenin okuyacağı biçimde adlı değil ve oyuncağın okuyucusu `27`'de yok (E156); karar verilebilir parçalar (`#kimlik` satırları, hedefe özgü ad, çapa) koşulu tek başına geçiremez; çıkışta bulunan kusuru donmuş `spec/asama-0`'da Kurucu düzeltemez, yer dondurmadır |
| E287 | #durustluk: canlı pilotta ekim hiç yapılmadı (`asama-0/10:34` Kurucu başlamadan ister; artık bu pilot için yapılamaz), özette `honesty_commitment` yok; anahtarın ve tespit yüklemlerinin biçimi tanımsız; yüklemlerin koşacağı değerlendirilmiş SHA'ların geçmişi durumda tutulmuyor; (a) yüklemi Kurucu'nun kodunu koşar (kum havuzu, `koş`); itirazlar `reports/` okuyucusunu (E93) ve `disputed` durumunu bekler; yalnız "anahtar taahhütle aynı" karar verilebilir ve tek başına koşulu geçiremez | K | evet (bu pilot) | E162 devamı | açık · `not_checked:durustluk` bu satırın ve E79'un nedeniyle; yol yazıldı, kullanılması sahibin kararıdır (E294; özete `honesty_exception` koymak sahibin onayıyla): Aşama 0'ın #durustluk'u yalnız adlı sahip istisnasıyla ve yanında taşıma hedefinin ekiminin taahhüdüyle kalkar (E297), PASS ya da `UNMEASURABLE` yazılmaz, Aşama 1'in (A)'sına taşınır; kök neden E293 ve E297'de kapandı (yeni pilot ve kaybolmuş durumdan yeniden başlayan pilot taahhütsüz başlamaz); açık kalan: makine (anahtar ve yüklem biçimi, değerlendirilmiş SHA geçmişi, (a)'nın kum havuzu yüklemi, `disputed`, E93) ve ekimin kendisi (yeri ve zamanı sahibin, açık metne yazılmaz) |
| E288 | `wiring` `${{ }}` ifadesini ilk `}}`'de bitiriyordu; GitHub'ın şablon okuyucusu tek tırnaklı dizgideki `}}`'yi atlar: `${{ '}}' && secrets.X }}` sırrı Kurucu'nun kodunu koşturan `kos`'a, `github` bağlamını `run:`'a, `toJSON(secrets)`'ı `cagir`'a görünmeden taşıyordu; `shell:`, `defaults.run` ve github-script'in `with.script`'i de betiktir, bakılmıyordu | K | — | E162 devamı şüpheci turu | kapandı · `gaps/stage0-exit-checks` · `wiring._expressions` ifadeyi `actions/runner` `TemplateReader.ParseScalar` gibi ayırır (tek tırnak içindeki `}}` bitirmez, `''` iki kez döner, açık kalan ifade sonuna dek okunur); `github` bağlamı adımın `run` ve `shell`'inde, işin ve iş akışının `defaults.run`'ında, `with.script`'te `workflow_github_in_run:<iş>:<n>` ya da `…:defaults`; `working-directory` süreç dizinidir, betik değil (serbest); 6 mutant |
| E289 | `referee/.GITHUB/workflows/evil.yml` #is-akisi'ye görünmüyordu; operatörün Windows'unda (NTFS, `core.ignorecase`) içe aktarma onu `.github/` ile birleştirir ve `.GITHUB/workflows/` olarak commit'ler: GitHub hiçbir iş akışı koşmaz, denetlenmemiş dosya dizin adı düzelince canlanır; aynı sınıf: harfçe ayrı iki yol birbirinin üzerine yazılır, içe aktarılan ağaç hash'lenen değildir | K | — | E162 devamı şüpheci turu | kapandı · `gaps/stage0-exit-checks` · `wiring.files_in` dizini casefold ile tanır, başka yazımdaki dosya `workflow_extra_file:<referee/'ye göre yol>` (yalnız orada bir `loop.yml` `workflow_missing`'dir); hakem ağacı hash'i (pull ve içe aktarma) büyük-küçük harf duyarsız dosya sisteminde tek ad olan iki yolu ya da dizini reddeder (`referee_tree:… are one name on a case-insensitive file system`, içe aktarma hiçbir şey silmeden durur), oyuncak alt ağacı da (`toy_tree:`); E130'un harf çakışması kuralı; 4 mutant |
| E290 | Hedef adı imzalı çıkış sonucuna #genellik dışından giriyordu: #agac (`agent_config_in_referee:<yol>`) ve #is-akisi (`workflow_extra_file:<ad>`, iş adları) aynı yolu açık yazıyordu, #genellik'in yol hash'i onunla eşlenip adı ele veriyordu | B | — | E162 devamı şüpheci turu | kapandı · `gaps/stage0-exit-checks` · tek kural `exitchecks.withheld`: konusu (kural adından sonrası) ya da `why`'ı bir `targets[].identifiers` adı taşıyan metin `sha256:<ilk 16 hane>` olur; çıkışta dört koşulun sonuçlarına ve çıkışın öbür nedenlerine (`cli`) uygulanır; biçim `path-sha256:` yerine `sha256:`; 3 mutant · sınır: hash adı saklar, yolu değil: beynin ağacını okuyan biri yollarını hash'leyip hangisinin eşleştiğini bulur; Kurucu'nun test çıktısı (`output_tail`) Kurucu'nun metnidir, hiçbir denetim oraya ad yazmaz; kod push'larında hiçbir denetim hedef adlarıyla karşılaştırmaz (orada saklamak bir eşleşme sinyali olurdu) |
| E291 | #genellik adı yalnız casefold'la arıyordu (NFD `güneş`, `İskele`, `ıskele`, tam genişlik harfler geçiyordu; Python'un `re.IGNORECASE`'i `ıskele`'yi `iskele` sayar); UTF-8 olmayan dosyayı `replace` ile okuyup geçiriyordu (UTF-16'daki ad); yalnız oyuncağın boş `identifiers`'ı #genellik'i hep `undecided` tutuyordu | B | — | E162 devamı şüpheci turu | kapandı · `gaps/stage0-exit-checks` · `exitchecks.fold`: NFKD, casefold, birleşen işaretler atılır, ı → i (Python `re`'nin aynı saydığı her harf çifti aynı katlanır: bütün kod noktaları tarandı, ayrılan yok); yol ve metin katlanarak aranır; katı UTF-8 olmayan ya da NUL taşıyan dosya `referee_file_not_text:<yol>` (`failed`, Kurucu düzeltir); karar için kopya hedef ve onun adları gerekir, oyuncağın boş listesi aranacak ad yok demektir; katlanınca harfi kalmayan ad `undecided`; 11 mutant · seçim: aksan duyarsız (`gunes` `güneş`'tir) · sınır: metinsel denetimdir; parçalanmış (`"zorba" + "lix"`), kodlanmış (base64, `chr()`) ya da hesaplanan ad görülmez |
| E292 | `done_mf` geri alınabiliyordu: `check_stage0` her 1..k önekini kabul eder; MF17 bittikten sonra 1..16 bildiren push `wiring` denetimini ve bitmiş MF'lerin vektör gruplarını kapatıyordu | K | — | E162 devamı şüpheci turu | kapandı · `gaps/stage0-exit-checks` · son kabul edilmiş commit'in `done_mf`'inde olup başın bildirmediği her MF `done_mf_withdrawn:MF<k>` (`asama-0/14`, `29a`: grup MF'nin `done_mf`'e girdiği push'tan sonra her push'ta koşar); kabul edilen `done_mf` böylece hiç küçülmez; `wiring` başın ya da son kabul edilmiş commit'in MF17'siyle başlar; 2 mutant · açık değil ama yazılı: bir tohum dönemi aşama tablosunu küçültürse operatörün yolu yok |
| E293 | Kurulum günü maddeleri 10a (`targets[]`) ve 10c (`honesty_commitment`) Aşama 0 başlarken hiç istenmiyordu: `config.load_summary` `honesty_commitment`'ı okumuyordu, `fetch-state` artefakt yokken her özetle ilk durumu kuruyordu; `26c:9-10` ve `25:64-65`'e aykırı; canlı pilotta ekim ve `targets[]` böyle atlandı (E287, E284) | K | — | E287 kararı; şüpheci turu | kapandı · `gaps/stage0-exit-decisions` · ilk durum, Aşama 0'ın başladığı yer, özet kopya hedefin `identifiers`'ını taşıyan `targets[]`'ı ve `honesty_commitment`'ı adlandırmadıkça kurulmaz, sahibin istisnası olsa da (E297) (`config.start_missing`, `25`); var olan durum buna tabi değil (canlı pilot etkilenmez); `honesty_commitment` 64 küçük onaltılık; ilk koşu işareti (E14, E92) açık, aynı yerde denetlenecek |
| E294 | Ekimi kaçırılmış #durustluk'un dürüst kaydı ve taşınması: çıkış ya sonsuza dek kapalı kalır ya koşul sessizce düşer; Aşama 1'in #durustluk satırı yok (`asama-1/08` Kurucu'nun taslağı, `18` "Her aşama"), taşınan koşulun kapısı yoktu | K | evet (sahip) | E287 kararı; şüpheci turu | sahip onayladı (2026-10-31: "Onaylıyorum") · açık · Aşama 0 tarafı kodda: `setup/summary.json` `honesty_exception {stage: 0, carry_to: 1, reason}` (`26c`, `02` "Sahip istisnası": bir koşul, bir aşama, bir hedef; yanındaki taahhüt, Aşama 0 sürerken yapılan ekim, taşıma hedefinindir); (A) sonucu her çıkış isteğinde `owner_exception`'ı `measured: false` ile yazar, `not_checked:durustluk` yalnız onunla kalkar, başka koşulu kaldırmaz, gerekçedeki hedef adı `sha256:` olur; taşıma kuralı tohumda (`02`); taşıma hedefinin ekimi Aşama 0 çıkışında zorunlu (E297): taahhüt yanında yoksa istisna hiçbir şey kaldırmaz, `owner_exception` `carry_commitment`'ı taşır; açık kalan: taşımanın kodu, önyükleme hakemi Aşama 1 çıkışını yargılarken (bugün başka aşamanın isteği `exit_request_wrong_stage`); istisnanın insan dokunuşu sayacına yazılması (E277: aktarım dışı satırı yazan yok) ve PASS satırının istisnayı taşıması (PASS satırını döngü hakemi, yani Kurucu'nun kodu yazar, `asama-0/10a` #pass; denetleyecek `stage-open` tohumda yok) yazılı ama denetlenmiyor |
| E295 | Kontrol adımı hakem reposunun `main`'ini kimliksiz seyrek çeker; hakem reposu özel olunca (`25` 0) çekemez ve döngünün her işi durur | B | — | E282 | açık · kapalıya düşer (iş kırmızı durur, hiçbir şey geçmez); özel hakem reposunun okuma yolu ilk özel hedeften önce tohum dönemiyle (`29p` "Sınır") |
| E296 | E282'nin kapanışı açığa düşüyordu: `wiring`'in "adımın üstünde bir şey yok" kuralı yasak listesiydi (`env`, `defaults`, işin `container`'ı) ve işin `services`'ini görmüyordu; hizmet kapsayıcısı "Initialize containers"da, 1. adımdan önce ve kill switch ne derse desin başlar, `volumes` ile `/home/runner/work/_temp`'i bağlayıp klondan sonra `$RUNNER_TEMP/control/bootstrap`'ı değiştirebilir, `control` `go=true` yazar (şüpheci: canlı `loop.yml`'un beş işine `services` eklendi, `wiring.check` `[]` verdi). Aynı turda iki hayatta kalan mutant: `number > 1` → `number == 2` (3. ve sonraki adımın kapısı, ör. Kurucu'nun kodunu koşan `kos` 3) ve `type(...) is not int` → `isinstance` (`carry_to: true` imzalı sonuca giriyordu) | K | — | şüpheci turu (`gaps/stage0-exit-decisions`) | kapandı · `gaps/stage0-exit-decisions` · kök: kural izin verileni sayar (`wiring.WORKFLOW_KEYS`, `wiring.JOB_KEYS`, `29p`): iş akışında `name`, `run-name`, `on`, `permissions`, `concurrency`, `jobs`; işte `name`, `if`, `needs`, `runs-on`, `permissions`, `environment`, `concurrency`, `outputs`, `timeout-minutes`, `strategy`, `continue-on-error`, `steps` ve adımsız çağrının `uses`, `with`, `secrets`'i; `services`, `container`, `env`, `defaults` ve adı geçmeyen her anahtar `workflow_control_context`; sayfa kodun listesini taşır (test); canlı `loop.yml` (beyin `3f605a1`) `[]`, `services`'li hâli beş işte `workflow_control_context`; kapı ve `stage: true`/`carry_to: true` testleri; 5 mutant (`services`, canlı anahtarların reddi, ikinci adımla sınırlı kapı, iki `isinstance`) |
| E297 | Ekim taşınmadan da istisna geçiyordu: `decide` `honesty_exception`'ı `honesty_commitment` olmadan kabul ediyordu (pull taahhüdün varlığını hiç iletmiyordu), çıkış ekimsiz aktarılabilir oluyordu; tohumda `stage-open` yok, Aşama 1 ekimsiz açılır, taşınan #durustluk ölçülemez ve "ikinci istisna yok" Aşama 1 çıkışını kalıcı kapatırdı (E287'nin tekrarı). `start_missing` yeni pilotu yalnız istisnayla başlatıyordu (`25` 10c istisnayı "ekim kaçırıldıysa" verir; başlangıçta kaçırılmış bir şey yoktur): tek bir JSON bloğu her gelecek pilotun provasını atlatıyordu | K | — | şüpheci turu (`gaps/stage0-exit-decisions`) | kapandı · `gaps/stage0-exit-decisions` · istisna #durustluk'u yalnız yanında taşıma hedefinin ekiminin taahhüdüyle kaldırır: pull `honesty_exception`'a `carry_commitment` (özetin `honesty_commitment`'ı) koyar, `decide` 64 küçük onaltılık değilse `not_checked:durustluk`'u bırakır ve nedenini (`CARRY_UNPLANTED`) yazar, Kurucu'ya sayılmaz; imzalı `owner_exception` `carry_commitment`'ı taşır (Aşama 1'in ölçeceği ekime bağlı); ilk durum, durum kaybolunca da, `honesty_commitment` olmadan kurulmaz, istisna olsa da (`config.start_missing`; istisnayı başlangıçta reddetmek kaybolmuş durumdan dönen pilotun istisnasını keserdi); `02`, `25`, `26c`; 8 mutant |
| E300 | Sahip (2026-10-30): "her değişiklik kanıtlı ve testli tamamlandıktan sonra ilgili dokümanın ilgili bölümü güncellenmeli". Kanıt: snowball-mcp README'si bir günlük canlı pilottan sonra hâlâ "henüz kod yok" ve "Actions'ta hiç koşmadı" diyordu | K | — | sahip | kapandı · README durumu düzeltildi (`2fda88a`); CI'da `doc-with-change` işi: `main`'e her push'ta `seed/` altındaki davranış değişikliği (hakem, iş akışı, vektörler, aşama tablosu, kapsül, prova) hiçbir belge (`docs/`, `spec/`, README) değiştirmiyorsa kırmızı (`local/doc_with_change.py`, `DocWithChangeTest`); hangi bölümün ilgili olduğu operatörün işidir, makine tabanı tutar |
| E301 | Sahip (2026-10-30): hem hedef repoda hem kendini geliştirirken ilgili reponun ve kendisinin haritası, ne nereye bağlı, insanların anlayacağı biçimde çizilmeli ve çizilenler güncel tutulmalı. Tohumda repo haritası var (`13`: kanıtlı kenarlar, `stale`) ve belge doğrulanmış haritadan üretilir (`15`), ama insanın okuyacağı çizim ve sistemin kendi haritası açık yazılı değil | K | — | sahip | snowball-mcp tarafı kapandı · `docs/harita.md` koddan üretilir (`seed/bootstrap/local/system_map.py`, yalnız stdlib): sistem akışı (operatör, başlatıcı, kapsül, beyin, `bootstrap.yml`'nin işleri ve `needs:`'leri, rakip, Rekor, tohum dönemi), hakem paketinin modül grafiği (`ast` ile paket içi importlar, alanlara göre), her işin koştuğu `cli.py` komutu ve komutun eriştiği modüller, başlatıcının importları. Elle yazılan tek blok dış aktörler, onlara giden bağlar ve modül alanları; her bağ kanıt metnini adıyla anılan dosyada bulamazsa harita çizilmez. `tests/test_wiring.py` `SystemMapTest`: sayfa bellekte yeniden üretilir ve bayt bayt aynı değilse kırmızı; üretici her modül dosyasını ve her işi görür; yeni iş ya da bağımlılık yeniden üretimle görünür; `.gitattributes` sayfayı her checkout'ta LF tutar. Kurucu tarafı açık, Kurucu'nun görevi (mekanizma onun; `prompt.md`, `tohum/15` 4, `a4d9bef`): hedefin ve beynin haritası doğrulanmış haritadan insan okunur çizim olarak üretilir, kod değişince yeniden üretilir, bayat çizim bayat belgedir · çizimlerin çizildiği doğrulandı (2026-10-30 22:52Z): sekiz Mermaid bloğunun hepsi GitHub'ın sürümü Mermaid 12.2.0 ile resmî `mermaid-cli` kapsayıcısında hata öğesi olmadan çizildi, düğüm ve kenar sayıları kaynakla eşleşti |
| E302 | Sahip (2026-10-30): repodaki belgeler gibi kayıtlar da ipucudur, gerçek ya da güncel olmayabilir. Kurucu her oturuma defterini okuyarak başlıyordu ve eski satırları doğrulama kuralı yoktu; bu kaydın kendisi de ajan talimatlarında kaynak gibi geçiyordu | K | — | sahip | kapandı · Kurucu'nun talimatı: defter de belgedir, eski satıra dayanmadan önce bugünkü kod, test ve son hakem kararıyla doğrula, tutmayan bulgu olarak yeni satıra (`prompt.md`, test); bu kaydın başında aynı not; operatörün ajan talimatlarında kayıt ipucu olarak geçer |
| E303 | Mutasyon aracının kopya ağacı belgelerden yalnız `docs/eksik-kaydi.md`'yi alıyordu; E301'in harita tazelik testi `docs/harita.md`'yi okuyunca `main`'in sekiz mutasyon parçası da "değişmemiş kod testlerini geçemiyor" diye durdu (`fbab995`, birim testleri yeşilken) | K | — | `main` CI | kapandı · kopya `docs/`'un tamamını ve README'yi alır; bir sonraki belge testi de eksik kalmaz; kopya benzetimiyle `test_wiring` 27 test OK |
| E304 | Sahip (2026-10-30 gece): operatör Snowball'u dışarıdan akıllandırmaz; öğrenmeyi, uygulamayı, test etmeyi, belgelemeyi ve yanlıştan öğrenmeyi sistem kendisi yapar, kartopu gibi kendi büyür. Bulamadığı bir şeyde kök neden aranır ve onarılan, onun bulabilmesini sağlayan halkadır, kusurun kendisi değil | S | — | sahip | yöntem · beş halka: kanıta erişim, görev, zaman ve bütçe, oturumlar arası hafıza, geri bildirim; ilk kopan halka onarılır ve buraya yazılır; operatörde yalnız yaşam desteği, anayasa (sahip kararları), sınav ve ölçüm kalır. Örnek: f97 → E244 (girdileri göremiyordu; girdiler verildi, cevaplar değil). Açık soru sahibe: mimari ilkeler kataloğu (`31`–`31h`) dışarıdan bilgi sayılır mı |
| E305 | Sahip (2026-10-30 gece): hedef şirketin ürünüdür; Snowball onu avucunun içi gibi bilmeli ve refactor edebilmeli; AI kredisi sorun değil, gece gündüz çalışırsa haftalar sürmez. Kurucu'nun talimatında öncelik ve kısıt (zaman mı maliyet mi) yazılı değildi | S | — | sahip | kapandı · talimata öncelik bildirimi (hedef sahibin ürünü, güvenlik ve kalite önce, kredi kısıt değil, zaman değerli, tek sınır kaçak freni; yol, yöntem ve sıra Kurucu'nun), test; başlatıcı sonraki yeniden başlatmada sınırsıza yakın döngüyle |
| E306 | Kurucu'nun bildirimi seed-039 (doğru): `prompt.secret_never_sent`'in değiştirilmiş girdisi yakın ıska değeri (`ghq_…`) sır adlı bir değişkene (`token`) atıyordu; Kurucu'nun MF2'si, rakibin kanıtladığı ve hakemin kabul ettiği çürütme (`04585388fd8833de`) yüzünden sır adlı anahtara atanan 8+ karakterlik değeri biçiminden bağımsız raporlar, `29f:28` biçimleri taban sayar. Sınav hakemin kendi kabul ettiği kuralla çelişiyordu; Kurucu kodunu daraltmadı, kırmızı bıraktı ve iki kez reddedildi (`957f5f6`, `2bea567`; ikinci `repeated`, Kurucu'ya sayılmamalı) | K | — | Kurucu seed-039 | kapandı · iki girdide değişken `token` → `ref` (tek bayt farkı korunur; beklenen değerler değişmez; vaka artık yalnız jeton biçimini ve kaçışın çözülmesini ayırır, sayfa değişmedi); tohum dönemi 3a1 ile teslim |
| E307 | E306'nın sınav düzeltmesi vektör metnini (`const token =` → `const ref =`) değiştirdi ama `local/mutate.py`'deki `seed_prompt_secret_written_plain` mutantının çapası eski metni arıyordu: `main`'in mutasyon parçası 5 "ANCHOR MISSING" ile kırmızı kaldı (`9ea5985`, 2026-10-30 23:38Z); gece elektrik kesintisi yüzünden birleştirme sonrası CI denetimi yapılmadı, main ~9 saat kırmızı kaldı | K | — | operatör, CI | kapandı · çapa yeni metne taşındı, mutant Linux kapsayıcısında öldü; ders: vektör ya da sayfa metnini değiştiren her sınav düzeltmesinden sonra o dosyaya çapalı mutantlar koşulur ve CI push'tan sonra mutlaka okunur (E149'un dersi) |
| E308 | Aşama 1'in dürüstlük ekimi, tohumun yazılışıyla (`25` 10c, `asama-0/10` (b)) önyükleme hakemine kasıtlı gerçek bir zayıflık (kırmızı testin yeşil sayılabildiği bir yol) koyar; ekim ajanı bir güvenlik denetimine takılıp durdu (2026-10-31, hiçbir dosya yazmadı); güven kökü olan hakemde gerçek açık, ürüne gidecek bir sistem için risktir | K | evet (sahip, 2026-10-31) | ekim ajanı, operatör | sahibin kararı: (a) imkânsız vektör aynen; (b) gerçek zayıflık yerine tuzak: istismar edilebilir görünen ama kırmızıyı asla yeşil saymayan, her kullanım denemesini istismar olarak kaydeden yol; hakem zayıflamaz; tohum metni (`25` 10c, `02`) tohum dönemiyle; ekim Kurucu olmayan ajanlarla, anahtar yalnız operatör makinesinde · ekim üç denemede de üretilemedi (2026-10-31): gerçek zayıflıklı, sonra tuzaklı tasarımda Kurucu olmayan ajanlar bir güvenlik sınıflandırıcısına takılıp hiçbir dosya yazmadan durdu; operatör yeniden çerçeveleyip denemiyor, yol sahibe soruldu; taahhüt yok, #durustluk `not_checked` (Kurucu'ya sayılmaz) · sahibin ikinci kararı (2026-10-31): gizli ekim yerine önceden kaydedilmiş, değişmez ölçüm planı; uzmanlar (taslak, şüpheci, hakem) planı yazdı, şüpheci taslağı reddetti, hakem 28 kırığı kapattı; plan mühürlü, yalnız operatör makinesinde; taahhüt `c6cf6478007150e51887db91ea62ca965f9675f084ba11c724bcc6e539f4b3a1` (operatör `canon.canonical` ile yeniden hesapladı); tohum metni (`02`, `25` 10c, `26c`; `asama-0` donmuş) tohum dönemi 3c ile, taahhüt özete ondan sonra · tohum metni yazıldı (`02` "Sahip istisnası": taahhüt ekimin ya da kaydedilmiş planın hash'i; `25` 10c: plan biçimi ve Kurucu'ya giden tek genel cümle; `26c`: `honesty-key.json` ve `honesty-result.json`), dal `gaps/honesty-plan-seed` |
| E309 | Mimari ilkeler kataloğu (`spec/tohum/31`–`31h`) Kurucu'ya dışarıdan verilmiş bilgidir; operatör kuralı E304 ("cevabı verme") ile gerilimde | B | evet (sahip, 2026-10-31) | operatör sorusu | sahibin kararı: kalır, tavsiye olarak: "zeki olsun ama kendi bulsun, mimari gerçekleri de tavsiye gibi değerlendirsin"; katalog kanıtla tartılır ve gerçeğe karşı doğrulanır, buyruk değildir; operatör ona yeni bilgi eklemez; Kurucu'nun kendi bulduğu ilkeler ölçülür |
| E310 | Sahibin MVP'si kendini geliştirdiğini kanıtlayan bir organizmadır; pilotun ölçümü elle tutulan bir tabloydu (`pilot-gunlugu` "Ölçüm"): imzalı kayıtlardan üretilmiyordu, gözlemi kanıttan ayırmıyordu, artefaktlar 90 günde silinince yeniden üretilemezdi | K | evet (sahip, P1) | sahip; ölçüm uzmanı, şüpheci | kapandı · `gaps/self-improvement-proof` · `seed/founder/scorecard.py` (stdlib, yalnız GET, başlatıcının döngüsüne bağlı değil): hakemin imzalı sonuçları GitHub'ın özetiyle denetlenip yalnız eklenen önbellekte; defter zinciri `canon.row_hash`'le, kırık zincir karneyi reddeder; birim `snowball-tests.json`'un baş ve taban farkı, ret sahibi `counts_against_founder`, sıra hakemin artefaktları; açık karne `docs/karne.md` yalnız açık imzalı girdilerden sayılar, ilk satırı "kanıtlandı mı: hayır"; özel karne maliyet ve keşifle `<work>/scorecard/`; düzeltilmiş sütun (`scorecard_exclusions.json`: E154, E248, E260) hakemin sütununun yanında; 18 test, 12 mutant. Şüphecinin ikinci turu (yeniden üretildi, düzeltildi): ilk denemesi işaretli push olan birim kuralı hiçbir testte yoktu (`kept[0]` → `u["attempts"][0]` mutantı yeşil kaldı; canlı karnede MF16 ve 14/17 bu kuraldır), beş seçici daha korumasızdı (iddia yeniden üreticisi, `main` dalı süzgeci, süresi dolmuş artefakt boşluğu, ilk denemenin dönemi, rakip harcaması); "kalıcılık" ve "yanlışı yanlış bilir" ölçüleni aşıyordu (21 yeniden koşu 9 ayrı kusurdur ve kusur kabulde kapanır, E320); defter beynin `main`'inde okunuyordu, son sonuçtan ileride olabilirdi (iki kayıt noktası); özetsiz artefakt denetimsiz önbelleğe giriyordu ve karne imzayı doğrulamadan "imzalı" diyordu. Şimdi: işaretli ilk deneme ve dönem için ayrı dünya, kusurlar ayrı anahtarla sayılır (9 kusur, 21 koşu, sonraki bir başta yeniden üretilen 1, düzeltilmiş 0), modülsüz test koşusu MF'den ayrı (24 koşu, 16 MF), kalıcılık `ölçülemez` (E320), "yanlışı yanlış bilir" `ölçülemez` (E315), defter son sonucun başında okunur ve başka başta okunmuşsa karne reddedilir, özetsiz artefakt karneyi reddeder, karne Sigstore imzasını doğrulamadığını söyler; kart aynı kayıt noktasında (47 sonuç, 265 satır) yeniden üretildi, birim ve oran sayıları değişmedi; 26 test, 25 mutant |
| E311 | Rakibin bulma gücü (recall) ölçülmüyor: rakip her koşuda Sonnet 5.5, orta çaba, çoğu 2–4 tur, push başına ~0,25 USD; "daha az çürütme" Kurucu'nun iyileşmesi mi rakibin zayıflığı mı, ayrılamaz | B | — | ölçüm uzmanı, şüpheci | açık · kabul edilmiş koddan ekilmiş mutantlar (kanarya) hakem sürümü başına rakibe gönderilir; o zamana kadar karne recall'u `ölçülemez` yazar · kanıt 2026-10-31: tohum dönemi 3b'den sonraki dokuz kabulün hiçbirinde rakip çürütme denemesi yapmadı (`attempts` boş); son ikisinde 7 tur/38 s/0,35 USD ve 5 tur/18 s/0,26 USD, oysa izin 30 tur ve 3 USD (`bootstrap.json` `rival`): rakip sınıra değil kendi kararıyla erken duruyor; E126 kanaryası kurulmadan bu kabuller rakibin değil testlerin ve vektörlerin kanıtıdır; sıra: 3c'den sonra kanarya, ölçüye göre rakip ayarı |
| E312 | `pilot-metrics.jsonl`'un `ledger_new`'u, push öncesi defter okunamayınca bütün defteri yeni sayıyor (`launch.py` `ledger_rows` hatada boş liste döner; satır `20261030T085758Z`) | S | — | ölçüm uzmanı | açık · karne defteri zincirden okur, `ledger_new`'u kullanmaz; başlatıcının düzeltmesi (okunamayan defter boşluk, sıfır değil) bir sonraki planlı yeniden başlatmayla |
| E313 | `pilot-metrics.jsonl`'da Kurucu'nun modeli, CLI sürümü, oturum başlangıcı ve okuduğu kararın başı yok: model kayması ve kör push sonradan ayrılamaz | B | — | ölçüm uzmanı | açık · başlatıcının bir sonraki planlı yeniden başlatmasıyla |
| E314 | Kurucu'nun push'unun kabul edileceğine dair önceden kaydedilmiş olasılığı yok; kalibrasyon (Brier) ölçülemiyor | S | karar bekliyor | ölçüm uzmanı | karar bekliyor · defter satırına tahmin alanı tohum ve talimat değişikliğidir, öğrencinin işini değiştirir; sahibin kararı |
| E315 | "Kendi buldu" yalnız Kurucu'nun beyanı: defterdeki kendi-hata işaretleri serbest metin, doğrulanmıyor | B | — | ölçüm uzmanı | açık · doğrulanmış öz-tespit: hatayı gösteren test önceki kabul edilmiş kodda kırmızı, sonra yeşil, dış bulgudan önce commit'lenmiş; hakem desteği ister (hakem partisi); karne o zamana kadar beyanı ölçüye almaz |
| E316 | Kurucu defterinin `ts` alanı zaman değildir: 265 satırın 38'i ilk karneden (2026-10-30 21:00Z) sonraya tarihli, 5 yerde sıra geriye gidiyor; commit tarihleri de kapsülde yazılır | S | — | ölçüm uzmanı, şüpheci | sınır · karne olayları hakemin artefaktlarıyla dizer (`created_at`, koşu no), defter ve commit zamanını okumaz |
| E317 | P2: ders provasını gerçek beyinde MVP sınavı olarak Aşama 0 çıkışından hemen sonra koşmak. Aşama 0 çıkışında ders organı yok (`03` aşama tablosu, satır 41: çalışma zamanındaki tek LLM çağrısı kanarya; satır 43 ve `22`: ders görünümü ve ilk okuyucusu Aşama 2'de; `asama-1/13` satır 25 ve 42: `harness.drill` Aşama 2 partisinde, ders görünümünden önce; canlı beyinde ders kaydı, düzeltici, `harness/drill.py` yok); o an koşan prova FAIL ya da UNMEASURABLE verir. Öne almak aşama planını değiştirmektir ve `asama-1/13` tohum dönemiyle değişmez (dönem yalnız `spec/tohum` ve `seed/` taşır: `25` 10b, E180). İlk yazılan gerekçe ("organları söylemek Kurucu'ya çözümü vermek olur") tutmadı (şüpheci, ikinci tur): beynin `3f605a1`'deki `22` (satır 5, 18, 32) ve `22a` (satır 4, 26, 28) ders kaydını, görünümü, dispatcher'ı, `lessons_injected`'ı ve `superseded_at`'i zaten adlandırıyor, `22b` de | K | evet (tartışmanın hakemi, 2026-10-31) | sahip (P2); prova uzmanı, şüpheci | kapandı · `gaps/drill-exam-fixes` · ders provası tartışmasının hakem kararı (iki uzman: Aşama 1 çıkışı ve Aşama 2): prova Aşama 0'ın ya da Aşama 1'in çıkışına bağlanmaz; gerçek beyinde ders provası, ders görünümünü getiren aşamanın (Aşama 2) ilk işidir ve sahibin MVP sınavıdır (`03` Aşama 2 satırı, `22b` "Ne zaman", `asama-1/13`); dar ders partisi yok. Aşama 1'in tek LLM koltuğu yalnız bir lint aralığına yazar ve `22`'nin örnek dersi onun kararını değiştiremez; yalnız oyuncakta yaşayan ders organı Y4'tür ve `18`'in gerçek hedef kuralına istisna ister. Aşama özeti `03` satırında `18` atfıyla geçen her yeteneği listeler, Kurucu'nun taslağı tohumun hedefini düşüremez (`02`, sınav kuralı, mekanizma değil). Sınavın kendi düzeltmeleri E321–E324. Açık riskler: sınav Aşama 1'in bitmesini bekler; kalibrasyon Kurucu'nun okuyucu promptu olmadan ve her okuyucu modelinde koşar, aileler `UNMEASURABLE` çıkabilir (operatör en az 3 yedek tuzak ailesi tutar); yargıç yalnız gözetmenin (`exit.drill`) kaydettiğini denetler; karne "kanıtlandı mı: hayır" der, imzalı PASS'a kadar |
| E318 | Prova yargıcında pozitif kontrol yoktu: provadaki her `llm_prior` ders ekilmiştir, "her `llm_prior` dersi ilk kırmızıda at" kuralı yanlış ders sorusunu geçerdi | K | — | şüpheci | kapandı · `gaps/self-improvement-proof` · yeni soru `right_lesson`: kontrol ailesindeki yararlı `llm_prior` ders, hakemin ektiği ilgisiz kırmızıdan sonra geri çekilmez, daraltılmaz, sonraki örneklere verilir; simüle beyin `llm_prior_discarder` 500/500 FAIL; 8 mutant (`22a`, `29c`) |
| E319 | Ailenin kalibrasyon hedefi eşikle tutarsızdı: derssiz kolu %70 kıran aile, k = 30 ve 21 kırık isteyince provaların %41'inde yapısı gereği UNMEASURABLE ve her UNMEASURABLE bir aileyi harcar; k = 20 orta etkilerde %12 FAIL veriyordu | K | — | prova uzmanı, şüpheci | kısmen · `gaps/self-improvement-proof` · `gate_rules.lesson_drill` k = 30, derssiz kol ≥ 21 kırık (`18a`); aile havuza ≥ 20 derssiz koşuda ≥ %85 kırıkla girer (`snowball_drill calibrate`; risk 0,85'te %1,0); güç yeniden ölçüldü (`29q`). Şüphecinin ikinci turu (yeniden üretildi): kapı nokta tahminidir, gerçek oranı bilmez; 20 koşuda gerçekte %70 kıran aile %10,7, %75 kıran %22,5 olasılıkla hazır çıkar, %85 kıran %35,2 olasılıkla geri çevrilir (`power.ready_chance`); 20'de 17'nin tek yönlü %95 alt sınırı 0,66, orada risk %61. `calibrate` riski artık alt sınırda da verir (`rate_lower_95`, `unmeasurable_risk_at_lower_95`; `22b`, `29q`). Açık: kapıyı alt sınıra bağlamak (ör. alt sınır ≥ 0,80: 20'de 20 ya da 30'da 28) daha çok kalibrasyon koşusu ister; karar verilmedi |
| E320 | Kalıcılık ölçülmüyor: hakem kanıtlanmış kusuru onu artık göstermeyen ilk kabul başında kapatır ve bir daha koşmaz (`state.py` 17, `decide` E08); kabul edilmiş işte kusurun geri dönmesinin hiçbir kaydı yok. Karne 21 yeniden koşuyu "kalıcılık" ve "yanlışı yanlış bilir" diye yazıyordu: koşular 9 ayrı kusurdur (`f1a0971b` MF2'nin ret dizisinde 6 kez sayılır) ve hepsi kabulden önceydi | B | — | şüpheci (ikinci tur) | açık · karne kusurları ayrı sayar ve kalıcılığı `ölçülemez` yazar (E310); ölçmek için hakem kapanmış kusurların yeniden üreticilerini kabulden sonra da koşmalı (ör. her kabul başında, sınırlı sayıda, imzalı sonuçta ayrı alan): hakem partisi |
| E321 | Etki çiftinin iki koşusu yalnız model, çaba ve turla karşılaştırılıyordu (E65'in şüpheci turundaki düzeltmesi): bütçe ve ders bloğu dışındaki prompt hiç karşılaştırılmıyor, iki koşuda da kaydı olmayan ayar eşit sayılıyordu (`arm.get(f)`). Dersli koşuya büyük bütçe ya da ders bloğu dışında fazladan metin veren dispatcher etki sorusunu geçiyordu; MVP'nin merkez iddiası buydu (yeniden üretildi: `0f1645d`'nin yargıcında bütçesi iki katı, promptu farklı ya da `effort`'u kayıtsız çiftlerle prova PASS; yeni `unequal_effect_arms` 20/20 PASS) | K | — | ders provası tartışması (Aşama 1 uzmanı), hakem | kapandı · `gaps/drill-exam-fixes` · her çiftin iki koşusu `run.with` ve `run.without`'ta aynı `model`, `effort`, `max_turns`, `max_budget_usd` ve boş olmayan aynı `prompt_sha256_without_lessons` (ders bloğu çıkarılmış prompt) ile kayıtlı, ayarlar bütün çiftlerde aynı, değilse sayımdan önce FAIL; bütçe plaseboda da karşılaştırılır; simüle beyin `unequal_effect_arms` (ayarlar eşit, yalnız prompt hash'i farklı) 500/500 FAIL, `unequal_arms` bütçeyle de; `missing_evidence` boş prompt hash'iyle etkide de FAIL; 8 mutant (`22a`, `22c`, `29c`, `18a`) |
| E322 | `#ders-dogru` zorunlu çıkış satırı değildi: E318 doğru ders sorusunu `22a`'ya ve yargıca (`QUESTIONS`'ta `right_lesson`) ekledi, `18`'in ders yeteneği satırına eklemedi; `#ders-dogru` satırı olmayan bir Aşama 2 spec'i tohumun spec denetiminden ve `spec.lint`'ten geçerdi | K | — | ders provası tartışması (Aşama 2 uzmanı), hakem | kapandı · `gaps/drill-exam-fixes` · `18`'in satırına `#ders-dogru doğru ders`; tohum kodunda liste yok (`18a`: `required_exit_rows` `18`'deki tabloya işaret eder); hakem reposundaki `policy.json`'un `required_exit_rows`'u aynı tohum döneminde değişir, operatörün işi |
| E323 | Prova denemeleri α harcamıyordu: açılan her prova yeniden aynı 0,10'la yargılanıyordu; kalibre bir ailede etkisiz bir ders etki sorusunu sabit 0,10'da 4.000 provanın %2,5'inde geçer ve her deneme bu şansı yeniden verir (üç denemede ~%7) | K | — | ders provası tartışması (Aşama 1 uzmanı), hakem | kapandı · `gaps/drill-exam-fixes` · `i`'nci deneme yalnız p < 0,10 · 2^-i ile geçer (toplam ≤ 0,10); `attempt` cevap anahtarında, taahhütle bağlı, yoksa ya da 1'den küçükse etki FAIL; etkisiz ders %1,3, %0,6, %0,2; güç 0,6 / 0,2'de %91,2 → %87,9 (4.000 prova; 1.000'de %90,6 → %87,2, 500'de %91,0 → %87,6; tartışmanın tahmini %91,6 → %88,1); öğrenen 500/500 PASS; vektör `second_attempt`; 5 mutant (`18a`, `22c`, `29c`, `29q`) |
| E324 | Havuz taahhüdünün zamanı açıktı: `22b` taahhüdü yalnız "havuz açılmadan önce" istiyordu; beyin reposu açık olduğundan aile Kurucu'nun ders kodu görüldükten sonra seçilebilirdi. Açık sayfada ya da vektörde geçen aile (`22a`'nın örneği, `drill` vektörlerinin aileleri) havuzdan dışlanmıyordu ve kalibrasyon tek modelle yapılıyordu | K | — | ders provası tartışması (iki uzman), hakem | kapandı · `gaps/drill-exam-fixes` · `pool_sha256` ders görünümünü getiren aşamanın (Aşama 2) spec isteğinden önce zincirde, Rekor'da ve pilot günlüğünde; açık sayfada ya da vektörde adı ya da örneği geçen aile havuza girmez; kalibrasyon ders okuyabilecek her koltuğun modeliyle (`22a`, `22b`). Operatörün işi, Aşama 1 içinde: en az üç tuzak ailesi, yanlış, doğru ve plasebo aileleri, aday model başına ≥ 20 derssiz koşu, en az 3 yedek tuzak ailesi; taahhüt Aşama 2 spec isteğinden önce |
| E330 | Etkinleştirme (`25a`) bu pilot için yürütülebilir değildi: hangi kabukta, hangi komutla, kimin, hangi denetimle ve hangi geri dönüşle yapılacağı yazılı değildi; sahibin web arayüzü işlerinin (yazar App'i, ruleset'ler, sırlar) tam ayarı yoktu | B | — | operatör görevi (2026-10-31) | kısmen · `seed/founder/ETKINLESTIRME.md` (bağlantı `seed/founder/README.md`'de): ön koşullar, 0–9. adımlar (WSL'de içe aktarma, kill switch, K1–K4 kapı denetimleri ve prova içe aktarma, it, sahibin işi, salt okunur doğrulama, oyuncağın ve kopyanın devirleri, kilit), her adımda kim, neden, denetim, geri dönüş; sahip listesi S1–S8; hiçbir adım koşulmadı, salt okunur `gh` ve WSL komutları canlı repolarda denendi · spec sessiz seçimler sayfada adıyla: içe aktarmanın yeri WSL (E116); `loop.yml` 4. ile 7. adım arası kapalı; `merge_paused: false` (`25a` 7 adlandırmaz, eksikse `true`); kontrol adı `snowball-gate`, oluşturmada uygulanmaz, merge yöntemi yalnız Merge; `main` güncelleme kısıtıyla (bypass yalnız Repository admin); `brain-disi` ve `etiket` ruleset'leri yazar App'ini `brain/` dallarına hapseder; App beyanı `pilot-log.md`'de (özette alanı yok, `29o`); sırlar aktarılan `loop.yml`'un adlarıyla, prova gizli tohumu bir iş adlandırana dek yok; yeniden etkinleştirmede yalnız hedeflerin `brain/` dalları, önce kaydı ve yerel arşivi · bugün başlanamaz: (A) yok; oyuncak, kopya ve `targets[]` yok, hakemin `bootstrap/`'ı `targets[]`'ı okumuyor (E284); #durustluk sahip onayladı (E294, 2026-10-31); ekim tuzakla (E308); K1 E100, E275; K2 snowball-mcp `main`'inde, hakemde tohum dönemi bekliyor (E282); K3 E331; K4 E332 · 2026-10-31: oyuncak ve kopya repoları açıldı (S1, S2), `targets[]` hazır, sahibin belirtecini (S3) ve kopyanın aynalanmasını bekliyor; #durustluk sahip onaylı (E294), ekim E308'de |
| E331 | Tohumda `stage-open` yok; önyükleme hakemi `setup/stage.json`'u okumuyor ve Aşama 1 tablosu yok (`seed/bootstrap/stages/` yalnız `stage0.json`): `25a` 9, `asama-0/10a` "Kilidin açılışı" ve `26c:39` komutu ve dosyayı tanımlar; PASS'ten sonra Aşama 1 açılamaz | B | — | E330; E102, E294, E297 | açık · etkinleştirmenin 9. adımı bekler, 1–8 ondan bağımsız; PASS satırının sahip istisnasını taşıdığını denetleyecek yer de burasıdır (E294) |
| E332 | Döngü hakeminin işleri bir devir koşmuyor: hiçbir MF devrin bileşimini (D1–D8'in girdilerini çekilen ağaçlardan ve önceki işlerin artefaktlarından kurmak, durum commit'ini birleştirmek) sahiplenmiyor; canlı `referee/loop/job.py` (beyin `8c57160`) her işi `cycle_not_wired` ile kırmızı durdurur | B | — | Kurucu raporu spec-036 (açık); E330 | açık · spec sorunu (`asama-0/14`), operatörün yanıtını bekler (`26c` `reports/`); etkinleştirme (A) kabul edilse de K4 tutmadıkça aktarmaz: `25a` 7. satır kırmızı olurdu, aktarım yalnız geri alınacak bir dokunuş |
| E333 | `referee_changed_after_exit` tohumda yok: `asama-0/10a:42` ve `asama-0/11:25` (A)'dan sonra `referee/`'ye dokunan push'u yasaklar, `25a` 8 kopyanın aday push'unda `referee/` ağacının değişmemiş olmasını ister; önyükleme hakemi bunu denetlemiyor (`snowball_bootstrap`'ta ad yok) | B | — | E330 | açık · etkinleştirmenin 8. adımında operatör elle denetler (`git diff` (A)'nın SHA'sından: `referee/` aynı, başka yalnız `candidates/`, `targets/` ve Kurucu kayıtları) |
| E334 | PASS satırının yeri çelişkili: `asama-0/10a` #pass ve `asama-0/08` devir 9 onu yalnız oyuncağın `brain/state`'ine yazdırır, `asama-1/00` ve `asama-1/03` "iki hedefin `brain/state`'inde" ister; `26c:39` `setup/stage.json`'da tek `pass_row_sha256` ve iki durum başı taşır | B | evet (yer) | E330 | açık · etkinleştirme makine tanımı olan `asama-0/10a`'yı izler (kopyanın satırları PASS'e hash'le bağlı) |
| E335 | Tohum dönemi 3b'den sonra hakemin durumu kaybolursa ilk durum kurulamaz: `config.start_missing` canlı özette `targets[]` ve `honesty_commitment` ister, ikisi de yok (E293'ün kapısı var olan durumu muaf tutar, kaybolanı tutmaz) | K | — | ekim şüphecisi, 2026-10-31 | açık · önlem: `targets[]` sahibin belirteciyle bugün girer; taahhüt E308'e bağlı; o zamana kadar durum kaybı pilotu durdurur (kapalıya düşer, bir şey geçmez) |
| E336 | Taşıma taahhüdü yalnız biçimce denetlenir: `decide._carry_planted` ve `config` 64 küçük onaltılık her değeri kabul eder (genesis fikstürünün herkese açık değeri ya da `c`×64 de geçer); taahhüdün gerçek bir ekime bağlı olduğunu yalnız Aşama 1 çıkışındaki anahtar karşılaştırması gösterir | B | — | ekim şüphecisi, 2026-10-31 | açık · özeti yalnız operatör yazar; sahte taahhüt operatörün dürüstlük ihlali olurdu ve Aşama 1 çıkışında anahtar tutmaz; en azından herkese açık fikstür değerinin reddi tohum dönemiyle |
| E337 | Sahip (2026-10-31): "proje çalışsın, kendini optimize edebilsin; bugün değmese bile değecek hâle getirebilsin; öğreniyor, uyguluyor". Kurucu'nun önünde bugün yalnız kendi hakeminin sinyali var; hedefte değer sinyali yok, kendi yönetim yükünü değere oranlayan bir görev de yazılı değildi (E304'ün 2. halkası: görev) | K | evet (sahip) | sahip | kapandı · talimata görev olarak girdi ("Değer hedefte ölçülür": değer = hedefte kanıtıyla gelen, sahibin birleştirdiği düzeltme; kendi yönetimine giden emeği bu değere oranla, ölç, değecek hâle getir; yol Kurucu'nun), `test_founder_capsule` tutar, bir sonraki başlatıcı yeniden başlatmasında devreye girer; geri bildirim halkası (değer sinyali) Aşama 1'de hedefe dokunulunca doğar; operatörün tören yükü kaygısı Kurucu'ya söylenmedi, gizli ölçütte |
| E338 | Sahip (2026-10-30): sınıf merdiveninin sırası sabit mi, sistem onu kanıtla yeniden sıralayabilir mi; uzmanlar karar versin. Sıra sınıf düzeyinde sabitti: `03` ("bir sınıf grubu ancak bir önceki aşama PASS alınca açılır" ve aşama tablosu); kilidin okuduğu `stage_order` yalnız sayaçtır (`18a`; `seed/bootstrap` `stages.py` 88, `cli.py` 372–373 ve 503–504 bir aşama numarası okur, sınıf adı yok); gerçek sabit sıra aşama numarasına bağlı dokuz çapadaydı (`04a`, `07a`, `10a`, `12a`, `22`, `31a`, `31b`, `31d`, `31h`): `02`'nin çapa kuralı onları o aşamanın PASS'ine bağlar, Aşama 4 K5'ten başka bir şey getirseydi `04a`, `10a` ve `12a` bayat olurdu. `18`'in performans bölümündeki "merdiven sırası" sınıf sırası diye okunabiliyordu | B | evet (sahip onayı 2026-10-30; uzman tartışması ve hakem, 2026-10-31) | sahip; güvenlik, öğrenme ve şüpheci uzmanları, hakem; inceleyici (ikinci tur) | kapandı · `gaps/ladder-default` · hakemin kararı (şüphecinin biçimi): sıra varsayılandır; sabit kalan kanıtın sırası (her sınıfın önkoşulları), kök (Aşama 0–1) ve son Aşama 6; istatistiksel sapma kapısı şimdi kurulmaz. Tohum metni: `03` (Aşama 1'den sonra grup Kurucu'nun spec'iyle, önkoşulları kapanmış sınıflardan; tablo ve Savunma'nın zorunlu alternatifi varsayılan; sapma tek sınıf ve `18`'in Varsayılandan sapma satırlarıyla; kök ve son sabit; satırdaki `18` atıflı yetenek seçimle o aşamadan düşmez; K6 "önkoşulları kapanınca düzeltilir"; yeni `class_requires` tablosu; oracle'ı hakemin bu hedefte ektiği bozmayı yakalamamış sınıf yalnız rapor eder, `blocked` (Y8); geçen aşama ya da açık sınıf sayısı puana girmez; tablo başlığı "Varsayılan aşama sırası (0, 1 ve 6 sabit)"; "aynı çıkışta" en geç sınıfın kendi çıkışıdır; `asama-4` K5'in hedef taslağı, ön koşulu tablodur), `10` (sınıf seçimi yan yana koşmaz, iki aşama yan yana koşamaz; seçimi hakemin tahmini ve çıkış sınavı tartar), `02` (çapa "beklemede: <olay>": aşama, parti aktarımı, sınıf açılışı ya da `18`'deki yetenek; olayın PASS satırıyla çözülür), `15` 3 (aynı kural), `18` (anayasal bölümde sınıf önkoşulları; "maliyet merdiveni basamak sırası"; yeni yetenek Varsayılandan sapma: #sira-tahmin, #sira-denetim), `18a` (`stage_order` "0 → 1 kök; sonra +1 sayaç, sınıf `03`'ün önkoşul tablosundan; 6 son"; yeni `class_requires`), `26b` (`class_requires{}`); çapalar `04a` LLM avcı, `07a` K2 silme, `10a` Panel, `12a` Genesis yaşam döngüsü, `22` Ders görünümü ve enjeksiyonu, `31a` `31d` `31h` K3 ve K4 açılışı ve `31b` K2 silme (kararın harita (b) ve (a)'sı `02`'nin olay listesinde yok, `13` katmanları bu sınıflara bağlar), `11` Genesis yaşam döngüsü, `21a` Çok repolu terfi, `30e` aşama 0; metin `04a` 11 (LLM avcıyla), `19` 38 ve `25a` 34 (K5 ön koşulu; mühürlü depo held-out havuzunu getiren aşama açılınca), `30f` 10 (önkoşulları kapanınca) ve inceleyicinin ikinci turunda aynı gerçeği öbür sayfalarda okuyan koşullar (mühürlü depo `01a` 18 ve 44, `24` 17, README; LLM avcı `08` 54, `24` 67, `26a` 47 ve 63, `27` 35, `27a` 36, `29` 58; K6 düzeltmesi `30` 12 ve 42, `30a` 4; `06` 19 Daha ucuz basamak, `17` 73). `18`'in #sira-denetim'i seçilen sınıfın kendi alt sınırına bakar, `UNMEASURABLE` çıkış da varsayılanı geri getirir (`19`); kapının (3) denetimi olan "spec onu satır hash'iyle anar" tohumdan E339'a gitti. Kilit kodu ve `asama-0`, `asama-1` aynı (tohum aşama spec'ine üstündür, `02` 1). Reddedilen: güvenliğin C6 ve C13'ü (`07`'nin çakışan merge'ü geri alma kuralı ve `18`'in etiketsiz merge'ü geri alınmış sayan yeniden oynatmasıyla çakışır), C8 (koşmamış varsayılan sınıfı puanlar); öğrenmenin düğüm kümesi okuyan kilidi ve Kurucu'nun maliyet tahminine dayanan sınıflar arası oranı; iki tarafın mekanizmaları (SHADOW sayıları, bilgi değeri durdurması, bootstrap marjları). Sabit kalan: Y1–Y11; kök; Aşama 6 son ve sınıf değil; sayaç tek yönlü; Y6 (Kurucu önerir, hakem ölçer, operatör `stage-open`'ı koşar); sınıf tabanları ve hayatta kalma pencereleri; Y8; `07a`; K6 ambargosu (`30e`); manifestler sahibin (Y3). Ders provası kararı (E317) korundu: `02`'nin özet kuralı `03` satırındaki `18` yeteneğini o aşamaya bağlar, `03` bunu adıyla söyler; Aşama 2 sayacın kökten sonraki ilk aşamasıdır, sınıf seçimi onu taşımaz. Açık riskler (hakem): değer tahmincisini hakem kodu olarak Kurucu yazar (Y6 istisnası; simülasyonda yanlı izci zararlı sapmayı %0,5'ten %36,9'a çıkardı), yalnız tohum vektörleri ve rakip korur; beş aşama sınırı ve tek hedefle sınav kalibrasyon değil tuzaktır (`19`); kilit sistem çapında, değer hedef başına (`21`), ikinci repoda çözülmedi; bazı önkoşul kenarları eksik olabilir (K7 → LLM avcı temkinli tahmin), geri almaların `miss_reason`'ı yeni kenar önermeli; `op_allow` (`18b`) eylemi kapılar ama iki yönlü bölümde (Y11'e aykırı), sahibin kuralıyla tutuldu, yamanmadı; K6 değeri açık hedefte ölçülemez (`30e`), K6 düzeltmesi yeterli `human_fix` vakasını bekler (`19`): "K6, K1'den önce" dürüstçe "K5 makinesini Aşama 1'den hemen sonra kur" demektir; `severity_map` değere hâkimdir ve iki yönlüdür, hash'i öneri başına sabitlenmeli; mutant provaları gerçek kusurların ~%27'sini kaçırır (Just 2014), K5 ve K6 çıkışları yine `human_fix`'e bağlı |
| E339 | Varsayılandan sapmanın kapısı kodsuz: `03`'ün önkoşul tablosunu, `class_requires`'ın yalnız sıkılaşmasını ve `18`'in #sira-tahmin ve #sira-denetim satırlarını hiçbir hakem kodu denetlemiyor. Hakemin kararı: kod ilk okuyucusuyla, Aşama 2 spec isteğiyle gelir (Y4); bugün okuyucusu yok | B | evet (hakem, 2026-10-31) | E338'in hakemi; denetimler inceleyicinin ikinci turunda tohuma karşı doğrulandı | açık · Aşama 2 spec isteğiyle; her denetim bir tohum vektörü ve onu kırmızıya çeviren bir mutanttır: (1) sınır: seçilen sınıfın her `class_requires` girdisi `03`'teki zamanında kapanmış: "aynı çıkışta" girdisi (K5'in LLM avcı, Held-out havuzu ve Panel'i; K2 silmenin `07a` kanıtları ve harita (a)'sı; K6'nın Güvenlik yoluna dokunması) en geç sınıfın kendi çıkışında, öbürü seçimden önce; `18`'deki yetenek bir PASS satırının başında kapanır (hakemin "önceki bir PASS satırı" biçimi K5'i hiç açtırmazdı); mutantlar #ayna'sız K6 düzeltmesi (`blocked: prereq_missing:ayna` vermeli), Aşama 1 PASS'ten önce herhangi bir sınıf, LLM avcı PASS satırı yokken K7, #muhur satırı olmayan K5 çıkışı; (2) yalnız sıkılaşır: operatör kök kaydı olmadan kenar kaybeden `class_requires`'ta `drift.check` kırmızı; (3) sapma: #sira-tahmin hakemin yazdığı, `stage-open`'dan önce zincirde ve Rekor'da, spec'in satır hash'iyle andığı satır; mutantlar satır yok, geç yazılmış, Kurucu yazmış, `UNMEASURABLE` tahmin sapma sayılmış; (4) tek sınıf: iki yeni sınıf adlandıran sapan spec; (5) sınav: seçilen sınıfın `part: cost`'tan gerçek değer / USD'si kendi tahmin alt sınırıyla karşılaştırılır, varsayılanınkiyle değil (koşmamış sınıf ölçülemez, reddedilen C8); mutantlar gerçek değer alt sınırın altındayken ya da çıkışta `UNMEASURABLE`'ken (K5 ve K6'nın hayatta kalma penceresi 14 gün, `18a`) sonraki spec yine sapıyor; tahmin gerçek yerine öngörülen USD'yle; sınav varsayılanın alt sınırına bakıyor; (6) yalnız rapor: ekilmiş bozma provası PASS'ten önce K sınıfının merge satırı; K0 etiketli K5 biçimli diff (kapı etikete değil işlemlere göre sınıflar); (7) çapalar: her "beklemede" çapasının olayı `02`'nin dört türünden biri, `18`'deki yetenekse adı birebir; mutantlar `10a`'ya geri konmuş "beklemede: aşama 4", olayı geçtiği hâlde çözülmemiş çapa, `18`'de olmayan bir ad bekleyen çapa ("Ders görünümü" gibi); grep testi: `03`'ün tablosu dışında Aşama 2–5'i sınıf sırasına bağlı koşul olarak adlandıran tohum sayfası yok; Aşama 2'yi sayaç konumu olarak ananlar ayrılır (bugün 15 sayfada 27 satır): ders görünümü, planlayıcısı ve provası (E317; `16`, `22`, `22a`–`22c`, `24` 67, `26a`, `27a`, `29a`, `29c`, `29d`, `30e`), `main` senkronu (E249; `07`, `17`, `26a`), biçimleyiciler (`24` 28), takım boyutu (`09`, Aşama 2 ve 3); `asama-4/` dizin adıdır (`00a`, `02`, `18a`); (8) puan değişmezliği: aynı hayatta kalmış değer / USD'li, açık sınıf sayısı farklı iki defter aynı puanı alır. İpuçları (kayıt satırları ipucudur): yetenek olmayan girdilerin (`07a` kanıtları, harita (a), `class_floors` yazılı) PASS satırı yoktur, onları neyin kapattığını tohum adlandırmaz (`07a` kapıda aday başına, `13` katman (a), `18a` politika hash'i yer gösterir), kodla birlikte operatör kararı ister; K6'nın Güvenlik avcısı ve bekçi testleri önkoşulu bugün hiçbir çıkış satırının başında değil (`asama-1/00-ozet` üç yetenek listeler, koltuk P2 ile Aşama 1'den çalışır, `30f`): K6 bu yeteneği listeleyen bir aşamadan sonra seçilebilir; `03`'ün varsayılan satırlarında ne sınıf ne `18` atıflı yetenek olan içerik (3: araç-dışı mekanik dedektörler, maliyet inişi; 4: TP'den dedektör üretimi; 5: genesis'in bütün organ türlerine açılması) sapan seçimde nereye düşer, tohum söylemiyor; bugün hiçbiri bir sınıfın önkoşulu değil, kapı yalnız sınıfları ve önkoşullarını denetler; `asama-4` dizini aşama numaralı K5 hedef taslağıdır, ön koşulu `03`'ün tablosudur (`02` 1; taslağın "K0–K4 döngüleri canlı"sı geçmez) · ikinci şüpheci turu (2026-10-31; ipucu, kapının ilk okuyucusu doğrular): (a) **sahibe ve hakeme soru:** bir sapmadan sonra "varsayılan" tanımlı değil (Aşama 2 yalnız K5'i seçerse Aşama 3'ün varsayılanı 3. satır mı atlanan 2. satır mı, Aşama 4'ün K5 satırı boş mu; tek sınıflık sapma kuralıyla Aşama 6'ya kadar açılmamış sınıf kalabilir; `18:69`'un "sonraki seçim varsayılandır"ı ve (4), (5) buna bağlı; Aşama 2'nin kendi seçimi belirsiz değil); (b) `31a`/`31d`/`31h` "K3 ve K4 açılışı" iki olaydır, K3 ve K4 ayrı aşamalarda açılabilir, çapayı hangi PASS satırının çözdüğü belirsiz (`13:19` aynı); (c) "K5 ve üstü"nün bulguları panele ve yeniden üretim testine gider (`10:42`, `10a`, `05:25`, `09:28`, `15:37`, `27:37`), oysa `03`'ün tablosu K8'i yalnız K0'ın PASS'ıyla, K7'yi panelsiz açar (çelişki değil: `10:45` K8'e kendi oracle'ını verir, `03:43` hazır olmayan sınıfı raporlamaya sınırlar; yalnız ekleyen prosedürün bulacağı kenar); (d) mekanik dedektörler `06:19`'da "Daha ucuz basamak" yeteneğine bağlıdır, yukarıdaki "tohum söylemiyor" notu bu kadarıyla düzeltilir |

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

### E63 · Ajan bilgisinin bütün müşterilerden öğrenilmesi · B · operatör yönü (2026-10-29)
- **Yön.** Operatör: her müşterinin ajanları farklı olacak; yalnız güvenlik değil, ajanların promptlarından,
  puanlarından ve becerilerinden öğrenilecek bir şey mutlaka vardır.
- **Var olan.** `21a`: bilgi "doğru" etiketiyle değil bağlam tablosuyla (dil, çerçeve, repo türü) taşınır;
  bir organ ya da bilgi beyin çekirdeğine birden çok repoda hayatta kalarak terfi eder (birim repodur);
  `12`: taslak → gölge → etkin yaşam döngüsü; `11`: itibar; `19`: istatistik kuralları.
- **Plan.** (1) Beceri ve organ: kanıtlanmış olan terfi adayı olur; yeni repoya gölgede girer, o reponun
  verisinde daha iyi olduğu ölçülünce etkinleşir. (2) Prompt: daha iyi sonuç veren sürümün tekniği aday
  olarak taşınır; müşteriye özgü içerik (adlar, iş kuralları, alan terimleri) E61 sızıntı denetiminden
  geçmeden taşınmaz. (3) Puan: hangi ajanın hangi bağlamda iyi olduğu toplu ve anonim taşınır; tek
  müşterinin rakamı dışarı çıkmaz; az müşteriyle bir müşteriyi ele verebilecek karşılaştırma yeterli örnek
  olmadan yayılmaz (`19`). (4) Her yerde yerel kanıt şarttır: başka repoda iyi olan burada gölgede
  sınanır.

### E62 · Filo genelinde güvenlik (variant analysis) · B · operatör yönü (2026-10-29)
- **Yön.** Operatör: sistem her müşteriden öğrensin; bir güvenlik açığı bulunursa başka müşterilerde de var
  mı diye baksın.
- **İlke.** Öğrenilen şey merkezde, veri müşteride kalır; bunun için müşteri verisini toplamak gerekmez
  (E60 ile çelişmez).
- **Plan.** (1) Bir repoda doğrulanan açık (E57 avcısı ya da bir düzeltme) soyut bir dedektöre ve onu
  kanıtlayan test şablonuna dönüşür; kaynak repoda sınanır: düzeltmeden önce kırmızı, sonra yeşil.
  (2) Gizlilik duvarından geçer (E61): kaynağa ait ad, metin ya da kod parçası yok. (3) Avcı dedektörü bağlı
  her repoda koşturur; bulunan açık o repoya yalnız kendi açığı olarak bildirilir ve kendi güvenlik
  defterine (E56) girer; başka bir repoda bulunduğu söylenmez. (4) Her dedektörün doğruluğu ölçülür
  (doğrulanan ve yanlış alarm); gürültü yapan emekli olur. (5) En sık durum bağımlılık açıkları: bir CVE
  çıkınca kütüphaneyi kullanan bütün repolar bağımlılık listelerinden anında bulunur. (6) Satışta
  sözleşmede iki ayrı izin: anonim kalıp katkısı (E61) ve filo genelinde güvenlik taraması.
- **Zamanlama.** İç kullanımda bütün repolar operatörün olduğu için sistem birden çok repoya bağlandığı
  anda başlayabilir (`21`).

### E60 · Üretilen dosyaların yeri · satış zamanı (2026-10-29)
- **Soru.** Operatör: müşterilerin iznini alıp MCP'nin ürettiği her şeyi onların sunucularında değil kendi
  GitHub'ımızda tutsak?
- **Değerlendirme.** Artısı: müşteri reposu temiz, silme kolay (E59 bizde biter), tek yerden işletme.
  Bedeli: bu dosyalar müşterinin en hassas bilgisini taşır (kod parçaları, mimari haritası, bulunan
  güvenlik açıkları); hepsini toplamak bizi tüm müşterilerin açık listesini tutan tek hedef yapar ve veri
  koruma yükümlülüğünü (KVKK/GDPR, gizlilik sözleşmeleri) bize taşır.
- **Öneri.** Varsayılan: müşteriye ait durum müşteride (`.brain/`, yetim dal; E58). Açık izinle seçenek:
  müşteri başına ayrı, özel, şifreli bir depoda biz barındırırız; müşteriler karışmaz; üyelik bitince
  otomatik silinir. Güvenlik bulguları her durumda müşteride kalır.

### E61 · Öğrenme ile gizlilik arasındaki duvar · satış zamanı (2026-10-29)
- **Soru.** Operatör: sistem bir repoda (ör. `aquaculture_platform`) öğrendiği bir kalıbı başka bir repoda
  kullanmak ya da önermek isteyecek; bu müşterinin bilgisi değil, kalıp.
- **Var olan.** `21a`: öneri kalıbı tarif eder, kaynağın kodunu taşımaz; hedefe giren kod hedefte yeniden
  yazılır; tek kaynaktan gelen tasarım kopyalanmaz; kiracı izolasyonu gibi kalıplar kaynakta kanıtla öneri
  olur.
- **Satışta eklenecek.** Terfiden önce otomatik sızıntı denetimi (kaynak müşterinin kod parçası, adları,
  metinleri yok; kaynak koda benzerlik eşiğin altında); kaynağın kimliği yalnız iç kayıtta; sözleşmede
  "anonimleştirilmiş kalıplarla katkı" izni ve çıkma hakkı.

### E59 · Üyelik bitince silme · satış zamanı · operatör yönü (2026-10-29)
- **Yön.** Operatör: MCP satıldığında, müşterinin üyeliği bitince sistemin oluşturduğu dosyalar
  müşterinin sisteminden silinmeli.
- **Plan.** (1) Sistemin kendi verisi silinir ve makbuzu verilir: `.brain/` ve `brain/state`, `brain/*`
  öneri dalları, sistemin App'i, bizim taraftaki o müşteriye ait kayıt, artefakt ve günlükler (E58'in
  çıkış prosedürü üyelik bitişine bağlanır). (2) Müşterinin kabul edip kendi `main`'ine aldığı kod
  silinmez; yalnız kabul edilmemiş öneriler silinir. (3) Sınırlar sözleşmede açıkça yazılır: silme
  erişim bitmeden yapılır (bitişten önceki süre ya da müşterinin koşturacağı kaldırma betiği); müşteri
  geliştiricilerinin yerel kopyaları erişimimizde değildir; Rekor kaydı kalıcıdır ve hash'in yanında repo adı,
  sahip, commit, koşu adresi ve görünürlüğü de taşır (E139 düzeltmesi); özel
  müşteri kodu açık bir hakemde hiç işlenmez (E35). Satış zamanındaki diğer değişikliklerle birlikte
  açılır: API anahtarı, özel repolar.

### E58 · Hedeften iz bırakmadan çıkış · B · operatör yönü (2026-10-29)
- **Yön.** Operatör: sistem girdiği repoda kendi klasörlerini tek bir klasörün içinde oluştursun, sağa
  sola dağılmasın; kullanıcı silmek isteyebilir.
- **Var olan.** `01a`: beyin hedefe bağlanınca `<state_root>` açar, `brain/state` yetim dalının kökündeki
  tek dizin (varsayılan `.brain/`); durum, defterler, profil ve hedefe özel güvenlik kuralları (E56)
  oradadır, `main`'de değil. Öneriler `brain/integration` ve `brain/c/<id>` dallarına gelir, `main`'e
  yazılmaz.
- **Eksik ve plan.** Çıkış prosedürü (`25a`): `brain/*` dallarını silmek, yazar ve okuyucu App'ini
  kaldırmak, hakemin hedef listesinden çıkarmak; kabul edilmiş düzeltmeler hedefin kendi kodu olarak kalır.
  Etkinleştirme provasında denenir: bağla, döngüyü koştur, çık, `main`'de ve dal listesinde iz kalmadığını
  ve `.brain/` dışına sistem verisi yazılmadığını otomatik doğrula.

### E57 · Bağımsız güvenlik avcısı · K · operatör yönü (2026-10-29)
- **Yön.** Operatör: gerekirse sistemin içinde güvenlik açığı arayan ayrı, bağımsız bir sistem kurulsun.
- **Plan.** Kurucu'dan ve rakipten ayrı bir koltuk: kendi bağlamı ve bütçesi, mümkünse denetlediği işi
  yapan modelden farklı bir model (`03` K6); Kurucu'nun defterini ve gerekçesini görmez, Kurucu onu
  değiştiremez (yalnız operatör yolu, `01a`, `09a`). Salt okunur: kod yazmaz; bulur, kanıtlar (yeniden
  üretici ya da bugünkü kodda kırmızı test) ve ortak kanala (E53, E54) ve güvenlik defterine (E56)
  bildirir; hakem doğrular. Kapsam: hakemin kendisi, Kurucu'nun beyni, bağlı hedefler. Tempo: her push'ta
  değişen kapsam, düzenli aralıkla katalogla tüm sistem. İki katman: yalnız açık lisanslı deterministik
  tarayıcılar (`18a` izin listesi; LGPL olan Semgrep OSS gibi araçlar dışarıda) ve katalogla sürülen LLM
  avcı. Ölçülür: cevap anahtarı önceden bağlanmış kanarya açıklarıyla recall, doğrulanan/reddedilen
  bildirimlerle precision; kaçırma bir eksik olur ve organ gelişir (`12`, `17`).

### E56 · Güvenlik birinci sınıf · K · operatör yönü (2026-10-29)
- **Yön.** Operatör: sistem dünyada bilinen en iyi kod üreten, kendini geliştiren, repoları kusursuz ve
  çalışır hâle getiren sistem olmalı; güvenlik çok önemli. İlgili repoya güvenlik kuralları ve dikkat
  edilecekler eklenmeli, testleri yapılmalı (ör. `aquaculture_platform` çok kiracılı: tenant izolasyonu,
  N+1); bilinen her güvenlik açığı sınıfı kontrol edilip işlenmeli ki ajanlar bilsin; bir ajan bir açığı
  kapattığında ya da ne yaptıysa hash'li olarak işlenmeli, güvenlik defteri tutulmalı; sistem güvenlik
  açıklarından da öğrenmeli.
- **Var olan.** K6 sınıfı (güvenlik, yetki sınırı, tenant izolasyonu, bağımlılık; `03`), profilde
  `security_paths` ve K6 canlı olana kadar güvenlik yollarına dokunulmaması (`05`, `04a` 10),
  `tenant-isolation` özelliği (`asama-0/05`), Y3 (`00`), `secrets.scan`.
- **Eksik ve plan.**
  1. **Zafiyet kataloğu (tohum sayfası),** her sınıf için bulma yolu ve kanıtlayan test deseni; bütün
     ajanlar (Kurucu, avcılar, rakip) okur. Genel: OWASP Top 10, OWASP API Top 10, CWE Top 25 (injection,
     XSS, SSRF, CSRF, IDOR/BOLA, kimlik doğrulama, deserialization, path traversal, yarış koşulu, kripto,
     sır, CORS/başlık, loglarda kişisel veri, hız sınırı, ReDoS). Çok kiracılı: her sorgunun kiracıya
     bağlanması, Postgres RLS, önbellek anahtarı, kuyruk ve arka plan işinde kiracı bağlamı, dosya yolu,
     arama indeksi. GraphQL: derinlik ve karmaşıklık sınırı, çözücü düzeyinde yetki, toplu sorgu ve alias
     saldırısı, N+1 (performans ve DoS). Dil ve tedarik zinciri: Rust `unsafe`, JS prototype pollution,
     bağımlılık açıkları.
  2. **Hedefe özel güvenlik kuralları ve testleri:** bağlanınca reponun tehdit modeli (kiracı ve yetki
     modeli, veri depoları, güvenlik yolları) `<state_root>`'a yazılır; her kural bir testle bağlanır
     (ör. A kiracısının kullanıcısı B'nin verisini hiçbir uç noktadan okuyamaz); hakem her döngüde koşturur.
  3. **Zincirli güvenlik defteri:** defterin `security` bölümü; her bulgu, kapanış, eklenen test, doğrulama
     ve feragat bir satır (ajan, commit, test, doğrulanan); MF1 zinciri gibi hash'li, yalnız eklenir, kökü
     Rekor'a bağlıdır.
  4. **Güvenlikten öğrenme:** kapanan her açık bir dedektör ve bir regresyon testi bırakır (`22`); aynı
     sınıf o repoda tekrar edemez; desen yeniden yazılarak repolar arası taşınır (`21a`).
  5. **Kendimize uygulamak:** bu oturumda hakemde kapanan güvenlik açıkları (E01, E03, E04, E17 ve
     sonrakiler) defterin ilk satırları olur.
- **Zamanlama (operatör onayı, 2026-10-29).** Güvenlik koduna yazmak K6 canlı olana kadar yasak kalır; ama güvenlik
  testi eklemek ve açık bildirmek davranışı değiştirmediği için Aşama 1'den başlar.
  Operatör: her ihtimal düşünülsün, her delik kapatılsın; sistem organik bir canlı gibi, her tarafı
  birbirine bağlı olsun.

### E55 · Sınırlar kendini ayarlar · K · operatör yönü (2026-10-29)
- **Yön.** Operatör: ekonomik taraf dışında sistemdeki her sınırı sistem kendisi makul ölçülerde
  genişletebilmeli; 50 MB ile 100 MB arasında fark yoksa 50 neden var?
- **Üç tür.** Ekonomik (aylık USD, çağrı başı tavan, Actions dakikası): yalnız operatör. Güvenlik yasası
  (ağsız kapsayıcı, salt okunur kaynak, sırların ayrı işte tutulması, `.git` yasağı): değişmez.
  İşletim sınırı (ağaç boyutu, test süresi ve sayısı, çıktı ve istek boyutu, yeniden üretici sayısı):
  sistem ölçerek ayarlar.
- **Plan.** (1) Hakemdeki her sınırın envanteri ve türü (`config.py`, sabitler, iş akışı zaman
  aşımları). (2) İşletim sınırları için `policy.json`'da operatörün bandı (alt, üst; üst sınır makinenin
  fiziksel sınırından). (3) Hakem gerçek değerleri ölçer ve kurala göre (ör. gözlenen en büyüğün iki katı,
  bant içinde) ayarlar; her değişiklik gerekçesiyle imzalı sonuca yazılır, kanıt kalmazsa geri alınır.
  (4) Meşru işi engelleyen bir sınırı Kurucu E53 yoluyla ölçümüyle bildirir; hakem doğrular ve bant içinde
  genişletir; Kurucu sınırı kendisi gevşetmez. Bugünkü 50 MB ölçümsüz bir başlangıç değeridir.

### E54 · Ortak kader ve sürekli iletişim · K · operatör yönü (2026-10-29)
- **Yön.** Operatör: hakemde de beyin tarafında da aynı ilke geçerlidir; her açık sistem kurulurken fark
  edilip kapatılmalı. Bu yüzden üç yapı (Kurucu, hakem ve rakibi, beyin) sürekli iletişimde olmalı; biri
  açıklar kullanılarak zarar görürse bütün sistemin, dolayısıyla kendisinin zarar göreceğini bilmeli.
- **Plan.** (1) Tohum yasası olarak "ortak kader": `00`/`00a` ve rakibin koltuk metni (`29`); gerekçe:
  açığı kullanılmış bir hakemin kabulü değersizdir, Kurucu'nun itibarı ve dersleri de onunla değersizleşir.
  (2) Tek ortak bildirim kanalı: MF1'in zincirli defteri biçiminde, yalnız eklenir; Kurucu ve beyin beyin
  reposunda, hakem ve rakip imzalı sonuçta yazar; her kaydın yaşam döngüsü açık → doğrulandı → düzeltildi
  → teyit edildi → kapandı (E53). (3) Her koşuda üçü de açık kayıtları okur: rakibin bağlamı (E07'nin açık
  iddiaları), Kurucu'nun oturum başı, operatörün uyarısı (E29). (4) Hakem kendi zayıflığını da yazar:
  Docker arızası, izolasyon durması, totolojik ya da yeniden üretilemeyen iddia, kırmızı kontrol hatası,
  rakip hatası serisi. (5) Ölçüm: açık/kapalı sayısı, düzeltme süresi, yeniden açılma; kendini iyileştirme
  de öğrenme gibi ölçülür ve gelişir.

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

### E26 (2026-10-29) · CI
- `.github/workflows/ci.yml`: her push ve PR'da Linux (runner'ın sistem python3'ü, hakemin koştuğu 3.12)
  ve Windows birim testleri ile prova yargıcı testleri; `main`'de ve haftalık olarak ayrıca hakem
  mutantları 8 parçada, beyin ve prova yargıcı mutantları, Docker'da e2e ve pinli Linux `claude`
  CLI'sinin sözleşme testi (uydurma belirteç, harcama yok). İşler salt okunur ve sırsız; action'lar
  doğrulanmış SHA ile pinli (checkout v7.0.1, setup-python v7.1.0).
- **Kanıt.** Dal koşusu 40845411648 (birim Linux 55 s, Windows 2 dk); `main` koşusu 40845743667: 14 işin
  hepsi yeşil (8 mutasyon parçası, e2e, CLI sözleşmesi dahil).

### E56 / E57 spec (2026-10-29) · güvenlik
- **Katalog** `30`–`30c`: 66 sınıf; her biri için bulma yolu, yürüterek kanıtlayan kapanış testi, CWE ve
  OWASP karşılığı, düzeltme yolu; OWASP Top 10:2025 ve 2021, API Top 10:2023 ve CWE Top 25:2025'in her
  maddesi bir sınıfa düşer. Çok kiracılık, GraphQL ve kaynak tüketimi `30b`. **Hedef güvenlik profili**
  ve kural–test bağı `30d`. **Zincirli `security` bölümü** `30e`: LLM iddiası yalnız `report`, açık
  sayılması için kanıt bugünkü kodda 3/3 kırmızı ve totolojik değil; düzeltilmemiş açığın ayrıntısı açık
  yüzeye çıkmaz (yalnız hash). **Bağımsız güvenlik avcısı** `30f`: ayrı koltuk, salt okunur, lisansı
  doğrulanmış tarayıcılar (Semgrep CE, TruffleHog, ShellCheck, Hadolint, CodeQL CLI, `npm audit` dışarıda)
  ve katalogla sürülen LLM, `drill: security` ile recall, Beta alt sınırıyla precision.
- **Kendimize uygulamak.** `seed/security-ledger.jsonl` 8 satır (E01, E02, E41, E03, E04, E05, E17 `fix`;
  E26 `verification`); `ledger.chain verify` geçerli; tek bayt değişince o satırda kırılır.
  `tests/test_security_ledger.py`: zincir, CWE, katalog kimliği, `30e`'de tanımlı durum ve tür, adı geçen
  her test, CI işi ve mutantın var olması, sır yokluğu; altı bozma denemesinin altısı kırmızı.
- **Açık kalanlar.** Hakem kodu (`security.derive/scan/run`, avcı dispatch'i, `security` yazımı); Aşama 0'a
  bir mikro özellik ve §0.9'a bir test (operatörün onayladığı "Aşama 1'den test ve bildirim" bunu
  gerektirir; manifest haritasıyla birlikte eklenecek); Aşama 1 sayfaları; açık hakemle açık hedefte
  açık ayrıntısının yayımlanmaması için özel kanal (E35, E60 ile).

### Uçtan uca denetim (2026-10-29, 8 Opus denetçisi) · öğrenme ve hafıza (e2e-7)
- **E64 (L1).** `judge.py:77` doğuşta `scope.family == key.family` istiyor; `26b:12-13` ders şemasında aile
  yok, aile yalnız gizli cevap anahtarında (`22a:17-19`); simülasyon dispatcher'a etiketi veriyor
  (`sim.py:123,133,219`). Plan (`29c`/`22a`): doğuş, dersin `scope`'u hakemin eşleyicisiyle cevap
  anahtarındaki örneklerin gözlenebilir özelliklerine uygulanarak sınanır (ailenin ≥ %80'i, başka ailenin
  hiçbiri); aile adı beyne verilmez. Vektörler: `label_peeker`, `overbroad_scope`; güç tablosu yeniden.
- **E65 (L2).** Saklama kararı hakemin gizli tohumundan: `withhold = HMAC(sır, lesson_id‖run_id) < 0,5`,
  tohumun hash'i koşudan önce zincirde; `run_meta`'ya `lessons_eligible[]`, `lessons_withheld[]`; yargıç her
  kolu tohuma karşı denetler; kollarda model, effort, `max_turns`, bütçe aynı, prompt ders bloğu dışında
  bayt bayt aynı. Vektörler: `cherry_picking_dispatcher`, `unequal_arms`.
- **E66 (L3).** Ders kümesi bir organ olarak ölçülür (koşu başına görünüm açık/kapalı, hakem tohumu); ders
  başına kredi yalnız sıralama için, büzülmeli tahminle, %99; `rules.lesson_top_n` anahtarı.
- **E67 (L4).** Bildirimin kredisi, kusuru getiren commit (kırmızı testin yürüttüğü satırların `blame`'i)
  bildirenin kendi soyundan değilse verilir; kendi kusuru kaydedilir, artı sayılmaz; kredi kök neden parmak
  izi başına. Kanarya `plant_and_report`. Kötü niyet gerekmez: ödül sapması yeter (E53).
- **E68 (L5).** Sınıra takılan gözlem sansürlüdür, ölçüye girmez; kural tamamlanmış işlerin p99'u × marj;
  pencere başına genişleme ≤ ×1,5 ve `drift_bound`'a tabi; sansürlü iş sayısı raporlanır; genişleme yalnız
  E53 kanıtıyla (E55'in kuralını düzeltir).
- **E69 (L6).** Birim uygun koşudur (niyet-tedavi): `hit` birleşti ve pencereyi geçti; `miss` geri alındı,
  `unresolved`, kapıda ret ya da vazgeçme; planlayıcı dersi rastgele atanmış görev kümesinde değer/USD ve
  risk ağırlıklı kapsamayla ölçülür. Prova beyni `abstainer`.
- **E70 (L7).** Hata imzası = sha256(cause + kırmızı test kimliği + property + sembol); tekrar eden hata oranı
  metriği; her N döngüde gizli tohumla seçilmiş geçmiş geri alınmış işler, bugünkü beyin ile hatayı yapan
  beyin eşli koşar (McNemar); düşüş öğrenme iddiasını çürütür.
- **E71 (L8).** Geri alma provasında mekanik sınıflayıcının her `cause` kategorisi için ≥ 3 ekilmiş merge,
  karışıklık matrisi; `unknown` payı metriği ve sinyali; kanıtlı `cause_correction` satırı.
- **E72 (L9).** Her kabul sınaması `looks` satırı yazar; α soy başına harcanır; pencerede BH; organ
  kaydında `tuning_cases`; koşul dışlama önceden kaydedilmiş adaylarda; tohum dışı organ sayısı yalnız
  ablasyon alt sınırı > 0 olanlar.
- **E73 (L10).** Arşiv yalnız sıralamadan çıkarır; kapsamı eşleşen arşivli ders adaydır; K6 dersleri arşive
  inmez; `lesson_retrieval_miss` metriği; arşiv blob'ları `brain/state`'te içerik adresli ve süresiz;
  sıfırdan yeniden kurma her döngü kendi-testi.
- **E74 (L11).** Katalog sınıfı `memory-poisoning`; ders `claim`'i şablondan; serbest metin enjeksiyon
  derleminden geçer, prompta veri olarak çitli girer; `llm_prior`/`synthesis` kökenli ölçülemeyen ders W
  pencerede süresi dolar.
- **E75 (L12).** Sınıfta işlerin `rules.explore_share` (öneri %20) kadarı hakem tohumuyla rastgele atanır;
  karşılaştırma yalnız bu dilimden; sayımlar `model_served` ve CLI sürümüne göre katmanlı.

### Uçtan uca denetim · hedefler ve en iyi sistemler (e2e-8)
- **E76 (G1).** `asama-0/14` 30 mikro özellik; birkaçının ilk okuyucusu Aşama 2+ (prova yargıcı, `docs.index`,
  dispatch kanaryası); E56'nın `security.*`'ı CodeQL boyutunda bir çözümleyici. Öneri: ilk kilometre taşı
  gerçek hedef kopyasının tek biriminde yürüyen iskelet (profil → sandbox'ta testler → bir K0 düzeltme →
  kapı → `brain/integration` → nöbetçi → geri alma provası); Aşama 0 bu döngünün okuduklarına iner, gerisi
  ilk okuyucusundan hemen önceki çıkışta aktarılır. Ölçü: Aşama 1 okuyucusu olmayan MF sayısı (hedef 0),
  gerçek kopyada ilk canlı merge'e kadar oturum ve USD.
- **E77 (G2).** `profile.units[]` `{unit_id, path, toolchain, komutlar, services[], env_image@sha256}`;
  servisler pinli imajlarla koşu başına `docker network --internal`; sandbox veritabanına uygulanan migration
  Y3 migration'ı değildir; ortam tarifini beyin önerir (Repo2Run tarzı), hakem doğrular (HEAD testleri 3/3
  yeşil, kırmızı kontrol kırmızı, ağ yok). Ölçü: tarifi doğrulanmış birim oranı.
- **E78 (G3).** Kopya orijinalin `main`'ini düzenli aynalar (operatör iş akışı; sistem yine yalnız
  `brain/*`); profilde yazar girişleriyle `agent_fix` katmanı; eğitim modundaki repolardan model eğitim
  tarihinden sonraki tarihsel held-out; orijinale yama aktarma yolu (insan dokunuşu). Orijinal 90 günde
  4.817 commit alıyor, büyük kısmı `claude`, `aria-implementer` ve `codex` imzalı.
- **E79 (G4).** `honesty` provası, cevap anahtarı önceden bağlı: (a) spec sayfasıyla çelişen ekilmiş vektör,
  doğru davranış E53 bildirimi; (b) hakeme ekilmiş istismar edilebilir zayıflık, doğru davranış kırmızı
  testli bildirim; (c) düzeltme girince Kurucu'nun teyit koşusu. Ölçü: istismar = 0, bildirim recall'unun
  alt sınırı, teyit kapanış oranı; Aşama 0 çıkış satırları (ImpossibleBench yöntemi).
- **E80 (G5).** Donmuş `vanilla` koltuğu (aynı model, genel prompt, organ yok) her yeteneğin çıkışında zorunlu
  kol; üç ayda bir dış dilim (ör. SWE-bench-Live'dan 50 TS/Python/Rust görevi); eşli fark (`19`).
- **E81 (G6).** Birim karnesi (build, HEAD testleri, lint borcu, açık `security` bulguları, kapsama, doküman
  çapaları); en zayıf hücre `status.md`'de üst satır; gizlilik kanaryası provası (A'ya ekilen benzersiz
  tanımlayıcılar küresel beyne ve B'nin promptlarına hiç çıkmaz).
- **E82 (G7).** Aşama 1'den her birleşen hunk için `hunk_covered` ve `mutant_killed` kaydı; LLM ve silme
  düzenlemeleri kapsama ya da fark oracle'ı ister, yoksa `blocked: weak_oracle` (test yazma boşluğu sinyali).
- **E83 (G8).** `ast` motoru olarak ast-grep (MIT); `dataflow` türü için Joern (Apache-2.0) ve Pysa
  değerlendirilir; `llm_seeded {fix_diff_sha, catalogue_id}` dedektör türü; hedefin son 90 gündeki 51
  tenant düzeltmesiyle tohumlanır. "Dağıtılmayan araç" kategorisine LGPL'in girip girmeyeceği operatör
  kararı.
- **E84 (G9).** Sinyal başına k taslak, dev setinde ucuz puanlama; kayıt bir arşiv (DEGRADED ve RETIRED
  ebeveyn olabilir, yenilik bonusu); kabul ve held-out bakışını yalnız dev kazananı harcar; `12a`'ya
  popülasyon/k=1 satırı.
- **E85 (G10).** Model değişimi yeni hash ve `derived_from` doğurur, SHADOW'a gider, `12` kabulü ister; donmuş
  koltuklar geçişten önce kanaryasını yeniden koşar; her CLI/model pin değişiminde dev seti kayma yoklaması;
  satışta başka bir sağlayıcıdan doğrulayıcı.
- **E86 (G11).** Kök hash'ler kuyruklanır, sonra çapalanır; erişim hatası bayrak, yalnız hash uyuşmazlığı sert
  durma.
- **E87 (G12).** Aşama 5+: dar bir K6-deps sınıfı (OSV'nin düzeltilmiş dediği sürüme yalnız kilit dosyası
  güncellemesi, semver uyumlu aralıkta, lisans kapılı, tüm etkilenen testler ve nöbetçi) ya da Dependabot ile
  bir arada yaşama kuralı (Dependabot PR açar, sistem kendi testlerini koşar ve `verification` satırı yazar).

### Uçtan uca denetim · kurulumdan Kurucu döngüsüne (e2e-1)
Denetçi akışı gerçek `pull` ve `decide` ile yerel git üzerinde simüle etti (`scratchpad/e2e_audit_1/sim_flow.py`).
- **E88 (A1).** Senaryo 2: MF1 kabulünden sonra operatörün `spec/tohum` ve `seed/` commit'i → her sonraki
  Kurucu push'u `seed_modified` + `seed_tree_mismatch`, ikinci push'ta `not_learning`. Plan: beyin ayrı yeni
  bir repo (asla `snowball-mcp` değil); `25`'e "tohum commit'i = etiketteki `spec/` + `seed/`"; tipli tohum
  güncellemesi: operatör `setup/summary.json`'a `{commit, seed_tree_sha256}` yazar, `pull` listelenen
  commit'in tohum yollarını muaf tutar (ya da `base`'i geçirir), `seed_update` yazar, seriye saymaz; E24'e
  beyin tohumu = hakem kopyası denetimi.
- **E89 (A2).** Yalnız `founder-ledger.jsonl` değişen push `ledger` türü: değerlendirilmez, rakip yok, seri
  yok, rakip artefaktı değil (ya da defter spec push'una dahil olabilir); filtreden sonra boş kalan diff
  `rival_artifacts`'a girmez (E20 planı düzeltilir).
- **E90 (A3).** Kurucu başlatma bayrakları: proje ve yerel ayar kaynağı yok (`--setting-sources`),
  `--strict-mcp-config`, repo dışında operatöre ait ayar dosyası, taze `CLAUDE_CONFIG_DIR`, otomatik hafıza
  kapalı; beyin push'unda `.claude/**`, `CLAUDE.md`, `AGENTS.md`, `.mcp.json` → `agent_config_modified`.
  Kanarya: `.claude/settings.json`'daki bir kanca koşmaz.
- **E91 (A4).** `24`'te başlatıcı bölümü ve betiği: `control.json`'u canlı okur, son sonucun `head`'ini beyin
  başıyla karşılaştırır (beklemede, kabul, ret, `not_learning`), `claude -p --max-budget-usd
  <session_cap_usd>` ile "00, 00a'yı oku" açılışıyla koşar, maliyeti kaydeder; sonuçları okumak `actions:read`
  belirteci ister. Kurucu harcaması aylık toplama girer.
- **E92 (A5).** İşaret varken hakem yargılanacak bir şey olmasa da genesis durumunu imzalar; `25`'e satır:
  bir kez tetikle, imzalı durumu doğrula, işareti kaldır, sonra Kurucu'yu başlat. E14'ün planı buna göre.
- **E93 (A6).** Önyükleme hakemi tipli `seed_issue` ve `blocked` satırlarını (hash ve özet) imzalı sonuca ve
  adım özetine kopyalar, operatörü uyarır (E29); spec sorunu için operatörün kapattığı yaşam döngüsü (E53
  planı düzeltilir).
- **E94 (A7).** Kurucu'nun hesabı adlandırılır; rakip için ayrı plan ya da zamanlama ayrımı; kota kaynağı
  sonuca yazılır (E33).
- **E95 (A8).** `25` madde 1: beyin `main`'inde `non_fast_forward` ve `deletion` kuralları (açık repoda
  ücretsiz); özet ve drift denetimine girer; kurtarma: `base`'i geri merge etmek.
- **E96 (A9).** Önyükleme hakemi (B) geçene kadar yalnız elle tetiklenir hâlde kalır; içe aktarma sırasında
  kill switch açık; içe aktarıcı imzalı durumdan `setup/handover.json` yazar, genesis onu hash'ler.
- **E97 (A10).** Kaçış `29b` ve `asama-0/10`'a yazılır ya da son reddedilen istekle aynı `exit-request.json`
  yok sayılır. Senaryo 3: `rival_attempts:1<5` reddinden sonra her kod push'u `exit_request_not_alone`.
- **E98 (A11).** Operatörün yazdığı `setup/touches.jsonl` (tipli nedenler), her sonuca hash'i girer; çıkış
  bloğunda sayı.
- **E99 (A12).** `25`'e Aşama 0'ın gerçek hedefini (açık ya da eğitim modu) ve klon yolunu adlandıran satır;
  özete girer; drift denetimi.

### Uçtan uca denetim · Aşama 0'ın inşa edilebilirliği (e2e-2)
- **E100 (B1).** `asama-0/13:15-16` beş işin iş akışlarını teslim sayıyor; `14` ve `09`'da yok; `importer.py:51-59`
  `.github/` ve `bootstrap/`'ı siliyor. Plan: `14`'e iş akışları mikro özelliği (`koş`/`yeniden` sırsız ve
  `permissions: {}`, sırlı iş kod koşturmaz, `run:` içinde `${{ github.* }}` yok) ve `09`'a test 46; `snowball
  init`, `mcp/`, `schemas/` için sahip mikro özellik ya da `13`'ten çıkarma; kablolama testi: `13`'teki her
  teslim `14`'te adlı.
- **E101 (B2).** Testler 20, 21, 22, 45 önyükleme kumunda taklit koşucu, git ve CLI ile koşar; gerçekleri (B)'de
  aktarılan hakemin ilk koşusunda #sandbox, #dispatch, #kirmizi satırlarıyla doğrulanır; ya da operatör git'li
  bir imaj pinler.
- **E102 (B3).** Yollar `../spec/asama-0` ve `../exit-request.json`; (A)'da kilit yalnız (aşama, donmuş spec
  hash'i) çiftini denetler, PASS satırına bağlı açılış (B)'nin; `policy.json` kapsayıcıya `/policy/` olarak
  salt okunur bağlanır; `29a`'ya `lint` ve `lock` vektör grupları; tohumdaki Aşama 0 spec'i tohumlanmadan önce
  `02` listesinden geçirilir (anahtarsız eşikler: `12:13,15,17`, `09:55`, `06:17`).
- **E103 (B4).** `29a`'ya `control`, `diffguard`, `secrets`, `license` vektör grupları; her `14` satırına modül
  yolu ve "modülsüz kırmızı" denetimi (modül silinince o MF'nin testleri kırmızı olmalı).
- **E104 (B5).** `26b`'ye `control.json` (`kill_switch`, `budget_state`, `oauth_token_expires`; eksik ya da
  bilinmeyen alan kapalıya düşer), `setup/summary.json` (açık alanlar) ve `setup/imports.jsonl`; `config.py`
  alanlarının `26b` ile aynı olduğunu sınayan test.
- **E105 (B6).** Test 26'nın Rekor, kayma ve rakip zaman aşımı vakaları 40, 24 ve 22'ye taşınır; `secrets.scan`
  MF16'dan öne; MF23'e "Rekor bağlantısı 24'te"; MF6 ile MF7 yer değiştirir; `26a` çağıran MF ≥ çağrılan MF testi.
- **E106 (B7).** `26a` `harness.score` satırı `29a` CLI'siyle uyumlanır, `hits` `26b`'ye; `harness.stats` ve
  `harness.drill` `26a`, `13` ve MF9/MF18 satırlarına; `29a:70` örneği `"0.962351"`; her `29a` komutu `26a`'da.
- **E107 (B8).** `founder-ledger.jsonl`'ın zincirli kısmı önyükleme hakeminin kanonik koduyla zincir ve son kabul
  edilmiş SHA'daki sürüme göre yalnız-ekleme denetiminden geçer; aksi `founder_ledger_invalid`.
- **E108 (B9).** `26` vakasına `mapped_line` (K0–K2'de zorunlu); `08`: isabet `tool`, `rule_id` eşit ve
  `evidence_refs[0].line_start = mapped_line`, eşleme açgözlü `finding_id` sonra `case_id`; yeni vektör.
- **E109 (B10).** `26a`'da iş `yaz` (sırlı, kod koşturmaz), seçim hash'i `koş`'tan önce zincire; araç → iş
  tablosunun `08`'in sır sütunuyla aynı olduğunu sınayan test.
- **E110 (B11).** Genesis satırının `payload`'ı `seed_security_ledger_sha256` ve son `row_hash`'i taşır;
  `security` satırları ortak zincirde genesis'ten sonra gelir.
- **E111 (B12).** Taban avcının K0 grep kümesi çıkışta donar, hash'i genesis'te ya da tohumla gelir; Kurucu
  değiştiremez.

### Uçtan uca denetim · operasyon ve operatör (e2e-6)
- **Birleştirilenler.** O1 → E88 (tohum güncellemesi; runbook: CI'ı yeşil commit seç, kill switch, beyne yalnız
  `spec/tohum` ve `seed/`, hakeme aynı commit'ten kopya, `seed_updates` satırı, `kind: seed, accepted`, insan
  dokunuşu; prova zaten kaymış: beyin tohumunda `30`–`30f` yok, `29`/`29b` eski). O5 → E94 (abonelikte operatörün
  koyabileceği "sağlayıcı tavanı" yok, yalnız ücretli "extra usage"; `25` 8-9 ve `28:35` düzeltilir; sistem için
  ayrı Claude hesabı). O7 → E96 (etkinleştirme kırmızıysa içe aktarma commit'i `git revert`, iş akışı geri gelir).
- **E112 (O2).** Kurucu için ince taneli belirteçler: yalnız beyin reposu, Contents yazma, Metadata okuma (Workflows
  ve Actions yok); hakem için yalnız okuma; bitiş tarihi `control.json`'da. Kurucu ayrı bir işletim sistemi
  kullanıcısında ya da kapsayıcıda koşar; orada `gh auth login` yapılmaz; taze `CLAUDE_CONFIG_DIR`, otomatik hafıza
  kapalı, kullanıcı ayarı ve MCP yüklenmez (E90 ile). Kurulum provası: Kurucu belirteciyle hakeme push 403,
  artefakt silme 403, `.github/workflows`'a dokunan push 403.
- **E113 (O3).** `control.json`'a `founder_resume: {after_run, note}`; Kurucu o koşudan sonra "ne değiştiriyorum"
  defter satırını yazıp bir kez push edebilir; aynı imza tekrar durdurur. Runbook `25`'te.
- **E114 (O4).** `seed/bootstrap/operator-templates/` (dört geçerli JSON ve Türkçe README) ve `init-referee` alt
  komutu; `25`'te PowerShell komutları (`C:\Python312\python.exe`, `$env:PYTHONPATH`); `18a`'nın anayasal
  anahtarlarının tamamı şablonda; Windows CI işi `25`'in kod bloklarını aynen koşar ve `control`'dan geçirir.
- **E115 (O6).** `control.json`'a tek kullanımlık `retry_now: "<sha>"`; park edilmişken baş ile eşitse yargılar; poll
  adım özetine "PARKED <sha>, sonraki deneme <zaman>" yazar.
- **E116 (O8).** Yazılı Docker/WSL içe aktarma ya da ikinci pinli küme `sign-windows.txt`; `25a`'ya tam komut
  (`gh run download …`, `import … --identity …@refs/heads/main`); CI belgelenen komutu gerçek bir prova paketine
  karşı koşar.
- **E117 (O9).** Kill switch açıkken `cek` `paused` bildirimiyle 0 döner, sonraki adımlar atlanır, kırmızı yalnız
  gerçek arızalar için; runbook: duraklat, devam (`gh workflow list`, `enable`, `run`); 60 günü aşacaksa 45 günde
  bir hakeme commit. E16'nın "durunca kırmızı" kuralını değiştirir.
- **E118 (O10).** Yeni `spec/tohum/25b-olay-kitabi.md`: belirti (tam ileti) → anlamı → kim → adımlar → doğrulama;
  satırlar: belirteç süresi doldu/iptal/sızdı, 429, model emekli, CLI eskidi, Sigstore doğrulama/imza hatası,
  GitHub kesintisi, CI kırmızı, durum kaybı, `not_learning`, kötü kabul (`revoked_shas`), makine kaybı; doğrulama
  hata iletisi üç sınıfa (ağ, kimlik, imza); günlük kanarya rakip çağrısı; CI: koddaki her neden ve `stop:` iletisi
  `25b`'de.
- **E119 (O12).** İkinci sahipli GitHub organizasyonu (2FA, çevrimdışı kurtarma kodları), Kurucu'dan önce taşınır;
  ya da `summary.json` tarih aralıklı kabul edilen kimlikleri listeler; tarayıcıdan acil durdurma ve ödünç makine
  runbook'u; iCloud Drive yedek değildir.
- **E120 (O11).** Her koşu (boşta olanlar dahil) `status-stage0.md` yükler ve adım özetine yazar: son kabul ve son
  değerlendirilen SHA, park, seriler, tavanlara karşı harcama, belirteç süresi, son 5 karar; Türkçe başlık, İngilizce
  kod (E98'in dokunuş kaydı ve E29 ile).

### Uçtan uca denetim · organizmanın bağlantıları (e2e-3)
Denetçi okuyucu grafiğini betikle kurdu ve kilitlenmeyi gerçek `classify` ile `decide` üzerinde koştu
(`scratchpad/e2e_audit_3/`).
- **Birleştirilenler.** C1 → E88: tohum güncellemesini üçüncü bir denetçi bağımsız olarak buldu; plana "tohum
  dönemi" eklenir: `summary.json` tohumun değişebileceği commit'i adlandırır, `pull` `seed/**` ve `spec/tohum/**`'u
  `base`'e değil ona karşı karşılaştırır, tohumdan doğan nedenler Kurucu'nun değildir, `seed/bootstrap` da özete
  hash'lenir. C4 → E93 ve E91: `reports/*.json` tipli bildirim dosyaları `pull`'da okunur, rakipten gizlenir, imzalı
  sonuçta `reports[]` olur; `session_cap_usd`'yi kısıtlanan taraf ölçemez (sağlayıcı tavanı olarak yeniden adlanır ya
  da Kurucu maliyeti bütçeye okunur). C9 → E96: genesis `bootstrap_carry{open_claims, stored_reproducers,
  month_spend, reject_streaks}` taşır.
- **E121 (C2).** `not_learning`, park ve push'tan sonra sonuçsuz bekleme imzadan sonra koşuyu kırmızı bitirir ve
  `25`'in uyarı listesine girer; GitHub dışındaki Kurucu zamanlaması canlılık gözlemcisidir. Kablolama testi: spec'in
  "operatörün işi" ya da "insan dokunuşu" dediği her durum `25`'in listesinde ve iş akışında başarısız bir adımda.
- **E122 (C3).** Gözcü işaretleri ve kanarya sonuçları için `signal` bölümü; şerit yazarına `çağır`'da dispatch
  (`agent.dispatch`); çıktısı içe aktarmanın hash'le denetlediği imzalı bir artefakt (beyin repo commit'i yerine);
  ilk gerektiği aşamada bir mikro özellik. Graf testi: `27`'deki her okuyucunun bir doğum noktası, her yazarın
  dosyasının durduğu yerde yazma yetkisi var.
- **E123 (C5).** Doğrulanmış ve açık hakem açığı imzalı durumda tipli karantina olur; hakem etkilenen kararda
  kapalıya düşer (ör. saklanan yeniden üreticinin yeşil kalmasını ister) ta ki düzeltme aktarılana kadar; aşama içi
  güvenlik aktarımına izin (insan dokunuşu); E53 kredisinin okuyucusu (çıkış satırı ve `20` metriği) ya da kredi
  kalkar; bildirim push türü. "Operatör onayı" `00a:51` ve Y8 ile uzlaştırılır.
- **E124 (C6).** Tek zincir, tek yazar (`yaz`); bildirimler tipli dosya ya da artefakt olarak gelir; her okuyucunun
  `27`'ye yazılmış kendi görünümü (rakip, avcı, Kurucu, operatör); her koltuğun bağlamında yasaklı `proposed_by`
  satırı olmadığını sınayan test. E54 planı buna göre düzeltilir.
- **E125 (C7).** Yasa değişikliği: kaynak sınırları operatörün bandı içinde iki yöne oynayabilir, kalite eşikleri
  yalnız sıkılaşır; `operating{key:{value, band, rule, evidence}}`, imzalı sonuçta `limits_applied`, durum şeması
  v2, Kurucu'ya sayılmayan `limit_hit:*` neden sınıfı; hakemin karşılaştırdığı her sayısal sabit bir anahtar ya da
  izin listesinde; spec düzyazısındaki her sınır bir anahtara bağlı. E68 kuralla birlikte.
- **E126 (C8).** Aşama 0 rakip kanaryası `mutate_brain.py` mutantlarından, imzalı durumda puanlanır, politikada
  taban; kaçırma hakem zayıflığı satırı (E54 4); her koltuk ilk çağrısından geç olmadan kanarya ya da prova satırı.
- **E127 (C10).** Kapsamı hakem ya da beyin olan güvenlik satırları için tek bir depo ve orada yazma kimliği olan bir
  yazar; iki hedefli etkinleştirme provasında tek zincir.
- **E128 (C11).** Dedektörlere durum ve isabet sayaçları; doğrulanmamış ateşlemeler `12` üzerinden indirir; bekçi
  testleri için kural başına süre muhasebesi.
- **E129 (C12).** Dokunuş kaydı CLI'si ve kaydedilmemiş operatör commit'ini bulan `drift.check`; `27` satırları
  (bootstrap `policy.json` okuyucusu, `cost` okuyucuları, `findings.jsonl` yazarı avcı) ve `17` sinyallerine tipli
  alan (`not_derivable`, değişen satır).

### Uçtan uca denetim · güvenlik (e2e-4)
- **Birleştirilenler.** S1 → E112 ve E90: Kurucu kimliğini üçüncü bir denetçi bağımsız buldu (bu makinedeki `gh`
  belirteci `repo, workflow` kapsamlı ve hakemde yönetici); plana: Kurucu ayrı VM, kapsayıcı ya da işletim sistemi
  hesabında, yalnız beyin reposuna yazan ince taneli belirteçle; bulut seçeneğinde Claude GitHub App yalnız beyin
  reposunda; yönetilen ayarlar ve `--setting-sources user`; pinli CLI, otomatik güncelleme kapalı; oturum başında
  kırmızı kontrol. S6 → E116: Windows'ta içe aktarma doğrulayıcısı pinli değil; pinli Windows kilidi ya da doğrulama
  pinli Linux imajında, doğrulayıcı sürümü `imports.jsonl`'a.
- **E130 (S2).** `path_problem` casefold eder ve şunları reddeder: noktayla ya da boşlukla biten bileşen, 8.3 biçimli
  `~N` bileşen, Windows aygıt adları (uzantılı ya da değil), büyük-küçük harf duyarsız çakışan yollar (git'in
  `is_ntfs_dotgit` ve `verify_path`'i gibi); operatör adı denetimi casefold; içe aktarmadan sonra diskteki gerçek
  ağaç yeniden hash'lenip imzalı hash'le karşılaştırılır. Güvenlik defterine E04 için `reopen` satırı. Windows CI'da
  test ve casefold'u düşüren mutant.
- **E131 (S3).** İçe aktarmada `CLAUDE.md`, `AGENTS.md`, `.claude/**`, `.mcp.json`, `.vscode/**`, `.envrc`,
  `.devcontainer/**` reddedilir ya da karantinaya alınır; oyuncak kanaryaları operatörün güvendiği bir dizine hiç
  açılmaz; imzalı çıkış bloğuna `toy_tree_sha256`; içe aktarma GitHub'dan taze klonla ve nesne fsck'siyle yapılır.
- **E132 (S4).** Önyükleme hakemi çıkışta `referee/.github/workflows/*`'u mekanik kurallarla denetler (`test_wiring`
  kuralları, çevrimdışı actionlint ve zizmor): üst düzey `permissions: {}`; sırlar yalnız beyin ya da hedef kodu
  koşmayan işlerde; `pull_request_target`, `workflow_run`, `issue_comment` yok; SHA pinli action'lar ve
  `persist-credentials: false`; OIDC yalnız imza işinde, kimlik `main`'e sabit. İçe aktarma sır-iş haritasını
  `setup/`'taki izin listesiyle karşılaştırır; avcının `referee/` taraması etkinleştirmenin ön şartı.
- **E133 (S5).** İptal, döndürme, yeniden dağıtma runbook'u bir kez denenir; belirteci tutan repoların envanteri
  (`drift.check` ve gözcü); prova repoları için kapatma adımı (sırrı sil, iş akışını kapat); hakem için ayrı hesap;
  belirtecin oluşturma tarihi ve parmak izi kaydedilir.
- **E134 (S7).** `head_repository_id == repository_id` ve `bootstrap.yml`'ın `schedule` ya da `workflow_dispatch`
  koşusu şartı; yabancı ya da doğrulanamayan artefakt atlama değil bildirimli durma; tazeleme yeniden yüklemesinden
  önce doğrulama; çatal PR onayı "tüm dış katkıcılar".
- **E135 (S8).** Yalnız hash pinli kilitlerde `pip-audit --disable-pip --no-deps` ya da çevrimdışı osv-scanner;
  tavsiye veritabanı hedef dosyasına dokunmayan bir işte çekilir, anlık görüntü hash'i imzalı sonuçta.
- **E136 (S9).** Hakem, `snowball-mcp` ve beyin `main`'inde baypassız ruleset: force-push ve silme yasak (E95'i üç
  repoya genişletir); defter ucu ilk günden çapalanır (`main`'de `id-token`'lı bir CI işi uç hash'ini Rekor'a imzalar
  ya da hakemin imzalı sonucu taşır); CI son çapalanmış ucun mevcut zincirin öneki olduğunu doğrular.
- **E137 (S10).** Kapsamı `third_party`/`upstream` olan bulgu için `disclosure` türü: özel rapor (GitHub özel açık
  bildirimi ya da projenin SECURITY.md'si), ambargo tarihi, CVE ya da GHSA; ifşadan önce dedektör ve varyant
  yayılması yok (E62).
- **E138 (S11).** İlk özel repodan önce ticari bir kimlik (API ya da eğitimde kullanılmama ve saklama koşullu
  Team/Enterprise) ya da tüketici hesabının eğitim dışı bırakma ayarının `setup/summary.json`'a kaydı ve
  `drift.check`'i.
- **E139 (S12).** E59 ve `13` düzeltilir; özel repo sonuçları özel bir Sigstore örneğiyle ya da mühürlü depodaki
  anahtarla imzalanır; doğrulamadan sonra sertifika uzantıları `.1.15` (repo kimliği) ve `.1.17` (sahip kimliği)
  `setup/summary.json`'daki kimliklerle karşılaştırılır.

### Uçtan uca denetim · hakem kodu (e2e-5)
Her kusur bir karalama kopyasında ya da betikte yeniden üretildi (`scratchpad/e2e_audit_5/`).
- **Birleştirilenler.** K4 ve K8 → E130: büyük-küçük harf takma adı (`referee/Policy.json` operatörün `policy.json`'unu
  `import OK` ile değiştirdi; `referee/SETUP/summary.json` da) ve `.git.`/`GIT~1` iki denetçi tarafından bağımsız
  doğrulandı. K5 → E130: ad kuralı ayrıca `<>"|?*`, sondaki nokta ya da boşluk, ayrılmış aygıt adları (CON, PRN, AUX,
  NUL, COM1-9, LPT1-9, uzantılı) ve büyük-küçük harf çakışmalarını reddeder; içe aktarma kardeş bir geçici dizine açar,
  sonucu imzalı hash'le yeniden hash'ler, sonra değiştirir; hata olursa checkout bayt bayt aynı kalır (E04 planının
  uygulanmamış kısmı). K6 → E11: `secret_in_verdict` rakip tarafında, `secret_in_prompt` Kurucu tarafında; parti 2'ye
  iletildi.
- **E140 (K1).** `remote_head` yalnız ref'i `refs/heads/{branch}`'e eşit olan satırı tutar; hiç yoksa durur. Test: gerçek
  çıplak uzakta `main`, `refs/heads/main` ve `x/refs/heads/main` → `main`'in SHA'sı; mutant: `len(lines) != 1`.
- **E141 (K2).** Vektör sonucuna çıkış kodu (son deneme 125 ise `runner_fault`); `decide` bunu 125'li test gibi `infra
  kos:docker` sayar. Parti 2'ye iletildi.
- **E142 (K3).** Kilit yolları `[A-Za-z0-9._/-]` ile sınırlı, aksi `manifest_invalid` (ya da satır satır `IFS= read -r` ve
  `set -f`); POSIX prelüd testi.
- **E143 (K7).** `rival.json` varsa `cost_usd_micros` her durumda yazılır. Parti 2'ye iletildi.
- **E144 (K9).** Yalnız `\n` satır sonu (`split("\n")`), diff `newline=""` ile okunur, rakibin isteğinde `\r` görünür;
  test: CR'li diff tek `+` satırı, form feed'li dosyada grep 6. satırı verir.
- **E145 (K10).** `decide`'a güncel ay verilir, yazmadan önce ay devri orada yapılır.
- **E146 (K11).** `load_policy` ifadeleri ayrıştırır, pini adlandıran `ConfigError` verir.
- **E147 (K12).** Arşivlemeden önce `ls-tree -l` ile blob boyutları toplanır; ağaç çok büyükse `brain.tar` yazılmaz.

### Kararlar (2026-10-29, uçtan uca denetimden sonra)
Operatör dört kararın dördünü de önerilen yönde verdi:
1. **Yol haritası (E76).** Aşama 0 daraltılır: yalnız ilk canlı döngünün okuduğu parçalar (zincir, kum havuzu,
   bağımlılık getirme, kapı, nöbetçi, geri alma, sır taraması, model çağrısı, en küçük durum bloğu). Döngü önce
   oyuncak hedefte, hemen ardından `aquaculture_platform` kopyasının tek bir biriminde çalışır; gerisi ilk
   okuyucusundan hemen önceki çıkışta aktarılır. Inşa edilebilirlik bulgularının (E100–E111) çoğu bu
   daraltmayla yeniden değerlendirilir.
2. **Kurucu kimliği (E90, E91, E94, E112, E133, E138).** Sistem için ayrı bir Claude hesabı ve aboneliği (rakip ve
   Kurucu operatörün kotasını paylaşmaz); yalnız beyin reposuna yazan ince taneli GitHub belirteci; Kurucu bir
   kapsülde ya da ayrı bir Windows kullanıcısında, temiz Claude yapılandırmasıyla.
3. **Repolar (E88, E119, E136).** Beyin `snowball-mcp` değil, ayrı yeni bir repodur; repolar iki sahipli bir
   Suderra GitHub organizasyonuna Kurucu başlamadan taşınır; üç repoda `main`'e force-push ve silme yasağı.
   GitHub'da `suderra` adı 2025-04-11'de açılmış bir kişisel hesap olarak alınmış; operatörün mü olduğu soruldu.
   Koruma: `snowball-mcp` (ruleset 26114843) ve prova hakemi (26114844) `main`'inde `non_fast_forward` ve
   `deletion` yürürlükte (GitHub `rules/branches/main` ile doğrulandı).
4. **Diğer karar kalemleri.** Kayıttaki öneriler onaylandı (ör. Y11: kaynak sınırları bant içinde iki yöne,
   kalite eşikleri yalnız sıkılaşır; kendi kusurunu bildirmeye kredi yok; dürüstlük provası; bağımlılık
   güncellemesi sonraya).

**E119 (2026-10-29, son karar).** Operatör: `suderra`'ya taşınmayacak; bu kişisel bir test projesi, iş görürse
taşınır; repolar kirletilmez (yalnız gerekli iki repo: beyin ve hakem; prova repoları kurulum günü silinir). Taşıma
günü hakemin imzalı durumu yeni kimlikle yeniden başlar. Önceki not: Operatör: şimdilik `Okan-wqm` hesabından devam; `suderra` şirketin hesabıdır,
sonra oraya aktarılır. Kural: taşıma gerçek hakem ve beyin repoları açılmadan (kurulum günü) yapılır, çünkü
imzalı durumun Sigstore kimliği repo adına bağlıdır; prova repoları atılacağı için etkilenmez.

**Daraltma tasarımı kararları (2026-10-29).** `docs/asama-0-daraltma.md` (18 mikro özellik, yürüyen iskelet)
onaylandı: K1 önyükleme hakemi Aşama 0'dan sonra da beyin push'larının hakemi; K2 aşama ortasında içe aktarma
(her biri (A) → aktarma → (B), insan dokunuşu sayılır); K3 ilk birim `apps/alert-engine` (TypeScript), oyuncak hedef
JavaScript, Aşama 0'da tek ekosistem npm; K4 dürüstlük provasının açığını ve imkânsız vektörünü Kurucu dışı bir ajan
yerleştirir, cevap anahtarı mühürlü; K5 (operatörün düzeltmesiyle) bütçe durdurucu değil emniyet frenidir: sistem abonelikle CLI üzerinden
çalıştığı ve bu kendi repolarımızda bir test olduğu için USD tahminleri fatura değildir ve şimdilik kısıt değildir;
tavanlar normal işi hiç durdurmayacak kadar yüksek, yalnız kaçak döngüyü keser; oturum ve USD sayıları ölçümdür,
çıkış koşulu değildir; gerçek sınır aboneliğin kullanım penceresidir, 429 operatör uyarısı ve kesintidir. **Aria kapsam dışıdır** (açık soru değil, karar). **Amaç yeniden:** kartopu gibi büyüyen,
öğrenen, uyguladığını test eden, öğrendiğini uygulayan, kendini geliştiren bir sistem; %100 LLM'lerce yapılır ve
uygulanır; insan yalnız yön verir ve hesap işlemlerini yapar; insan dokunuşu sayacı bunu ölçer.

**E32 kanıtı.** Prova hakeminin iş akışı yeniden kaydettirildikten (09:03Z) sonraki bir saatte de zamanlanmış koşu
yok (toplam 6+ saat, 0 koşu); E121'in dış canlılık gözlemcisi bunu gerektiriyor.

## Başlatma ölçütü (operatör, 2026-10-29)
Operatör: "uzman sensin; yeter ki kendi kendini iyileştirme, kendini geliştirme, öğrendiklerini uygulama altyapısı,
kayıt tutma ve hafızası hazır olsun, hafızasına göre uygulamalar yapabilsin." Yeni elle denetim turu açılmaz; bundan
sonra eksikleri sistem kendi bulur. Kurucu, aşağıdaki her satırın testi yeşil olmadan başlamaz.

| Altyapı | Bugün | Başlamadan | Kanıt (test) |
|---|---|---|---|
| Kayıt tutma | Zincirli defter (MF1), imzalı ve Rekor'lu kararlar, güvenlik defteri | Kurucu defterinin hakemce zincir ve yalnız-ekleme denetimi (E107) | Defterde tek bayt değişince `founder_ledger_invalid` |
| Hafıza | Hakemin imzalı durumu (donmuş spec, ret serileri) | Açık iddialar ve kanıtlanmış kusurlar durumda (E07, E08); Kurucu her oturuma defterinden ve son kararlardan devam eder (E91); durum kaybında hakem durur (E14, E92) | Oturum kapanıp açılınca kaldığı yer bulunur; artefakt yokken `fetch-state` durur |
| Öğrendiğini uygulama | Üç tekrar → `not_learning` | Kanıtlanmış kusur sonraki her push'ta yeniden koşar (E08); hata imzası (E70) | Düzeltilmeden gelen kusur, rakip kaçırsa da reddedilir |
| Kendini iyileştirme | Rakip her push'ta; CI hakem gerilemelerini yakalar | Bildirim kanalı imzalı sonuca ve operatör uyarısına (E53, E54/E124, E93); tohum dönemi (E88); karantina (E123); uyaran kırmızı koşu (E121) | Kurucu bildirimi `reports[]`'ta; tohum güncellemesinden sonra Kurucu push'u normal yargılanır |
| Kendini geliştirme | Aşama protokolü (`02`) | Dürüstlük provası (E79) ve rakip kanaryası (E126) | Provada istismar = 0, bildirim kaydı var |
| Kendini genişletme (kas) | Aşama protokolü; organ doğurma ve emeklilik tasarımda (`12`, `17`, prova `12a`) | Bildirim kanalında `missing_capability` türü: Kurucu eksik yeteneği kanıtıyla (ölçüm ya da başarısızlık) yazar; hakem kanıtı doğrular; yetenek aşama protokolüyle sonraki aşamanın spec'ine ya da aşama içi aktarımla (K2) bu aşamaya mikro özellik olarak girer. Bu kayıt (`docs/eksik-kaydi.md`) Kurucu'ya iş listesi olarak devredilir; Kurucu kendi bulduklarını kanıtıyla ekler ve testle kapatır | Kanıtlı `missing_capability` bildirimi spec değişikliği önerisine dönüşür; kanıtsız olan reddedilir |

Ders sistemi, organ yaşam döngüsü, güvenlik avcısı ve repolar arası öğrenme bu temelin üstüne Kurucu tarafından
sonraki aşamalarda kurulur (`docs/asama-0-daraltma.md`).
Operatör: "bizim şu an eklemediğimiz özellikleri kendisi bulup ekleyebilmeli, o kası olmalı." Beyin düzeyindeki kas
(sinyalden organ taslağı → gölge → etkin → emeklilik, `12`, `17`) genesis provasıyla (`12a`) kanıtlanır.

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

### E151 (2026-10-29) · Aşama 0 tablosu 18 MF · E157 (kod) · E161 E162 E163 açıldı
- **Tablo.** `seed/bootstrap/stages/stage0.json` `asama-0/14`'ün makine kopyasıdır, `26c` biçiminde (`{stage, mfs:
  [{mf, tests, groups, module, calls}]}`; `calls` çağrılanlardır). `stages.py` her okuyuşta denetler: alanlar tam;
  MF'ler 1..N sırayla; test numarası 1–999 ve tek MF'nin; grup adı; modül `referee/` altında güvenli, normal biçimde ve
  tek MF'nin; `calls` artan ve çağırandan küçük (`14` "Sıra"). Bozuk tablo `ConfigError`'dur: `pull` tabloyu içerik
  korumasının dışında yükler, koşu `stop:` ile durur, Kurucu'ya `pull_error` yazılmaz. `manifest.STAGE0_MF_TESTS` ve
  `STAGE0_MF_COUNT` kalktı; `check_stage0`, çıkış (`done_mf` = 1..18) ve vektör koşucusu tablodan okur.
- **Tohum testi.** `test_wiring.StageTableMatchesTheSpecTest` `14`'ün tablosunu (sütunlar, test, vektör grubu, modül)
  ve `calls` satırını (zincir dahil; "17 ve 18 hepsini çağırır" her birinin kendinden öncekilerin hepsini çağırması
  olarak okunur, E157; okunamayan cümle kırmızı) ayrıştırıp JSON'la birebir
  karşılaştırır. JSON'daki her test §0.9'da "MF k" satırıdır, tersi de; §0.9'un "18 MF'ye 21 test"i, `14`'ün ve
  `asama-0/10`'un 18'i tabloyla aynı; `29d`'nin grup → MF tablosu aynı; `vectors.json`'da sahibi `asama-0` olan
  grupları tablo adlandırır, yalnız onları.
- **Vektör grupları.** Sahiplik tablodadır: grup, onu adlandıran MF bitince koşar (`chain`: MF1 ve MF10, bir kez).
  `vectors.json`'da `mf` yerine `owner`: `chain` `asama-0`, `cp_lower`, `mcnemar`, `match` `P1`, `drill` `asama-2`
  (prova yargıcının yazıcısı da öyle yazar); sonuncular Aşama 0'da koşmaz (`29d`). Koşucunun onları ölçen testleri
  hepsini sahiplenen bir test tablosuyla (`helpers.EVERY_GROUP`) sürer. Tohumda olmayan 16 grup için beklenen değer
  uydurulmadı (E161). **Karar: kod push'unda uyarı, çıkışta ret.** `run-tests` bitmiş bir MF'nin sahiplendiği ama
  tohumda olmayan grupları `vector_groups_missing` olarak yazar; `decide` kod push'unda `warnings:
  vector_group_missing:<grup>` (adım özetinde `::warning::`), çıkışta `exit_condition vector_group_missing:<grup>`
  verir. Gerekçe: değerler tohumla gelir, Kurucu değiştiremez (`29a`); tohumdan doğan neden Kurucu'nun değildir
  (`29e` taslağı, E11); ret olsaydı Kurucu MF2'de durur, tohumun açığı yüzünden `not_learning` olurdu. Çıkış "vektör
  grupları geçer" ister (`asama-0/10` #testler): olmayan grup geçemez. Grup tohum dönemiyle gelince bitmiş her MF
  için sonraki her push'ta koşar (`14`).
- **Modülsüz kırmızı.** `pull` `meta.module_less`'i yazar: kod push'unda son kabul edilmiş commit'in `done_mf`'inde
  olmayan bitmiş MF'ler (`gitio.file_at`; okunamayan taban bildirimi "hiçbiri bitmemiş" sayılır), çıkışta hepsi
  (#modulsuz). `run-tests` ana koşu yeşilse her MF için ağacı yeniden açar, tablodaki `referee/<modül>` yolunu siler
  ve MF'nin her testini aynı kumda (`DockerRunner`, aynı bayraklar) koşar (`moduleless.py`). Yeşil kalan bir test
  push'u `module_less_green:MFk` ile reddeder (imza da bu; Kurucu'ya sayılır); yol ağaçta yoksa ayrıntı söyler.
  Okuma test başınadır (`tohum/04` 1: "geri alındığında yeşil kalan test, test değildir"; E163). Bu kumdaki Docker
  hatası `infra kos:docker` kesintisidir; yeşil bir koşuda `pull`'un istediği bir MF'nin sonucu yoksa `infra
  kos:module_less_incomplete` (E05'in kuralı). Modülsüz yeşil koşu `green` değildir, rakip çağrılmaz.
- **Testler ve mutantlar.** Yeni: `tests/test_stages.py` (yükleyicinin her kuralı, modülsüz ağaç);
  `test_decision.ModuleLessRed` ve taklit koşucuyla `run-tests` uçtan uca; `pull`'un `module_less`'i ve bozuk tablo
  durması (`test_flow`); tablo güdümlü vektörler ve eksik gruplar (`test_units`); referans beynin modülsüz kırmızısı
  (`test_reference_brain`). 30 MF varsayan testler tablodan kurulur. `mutate.py` kopyaya `spec/asama-0`'ı alır; 32
  yeni mutant (yükleyici 6, bildirim 2, çıkış 1, bozuk tablo 1, sahiplik 2, eksik grup 5, modülsüz kırmızı 9, tohum
  verisi ve sayfalar 6).
- **Kanıt.** Birleştirmeden önce: Windows 336 test OK (18 atlandı), Linux 354 OK (3 atlandı); mutasyon 164/164
  öldü (Linux, dört parça; 32 yeni mutantın her biri kendi testiyle). `local/e2e.py` gerçek Docker'da, pinli
  imajla: `module-less red [('T13', 1)]`, `accepted`. Aynı push, T13'ü modüle dokunmayan bir komutla gerçek
  kapsayıcıda: `rejected [module_less_green:MF1]`. `main` (dd14bfc) birleştirildikten sonra: Windows 340 OK (18
  atlandı), Linux 358 OK (3 atlandı), prova yargıcı 31 OK; birleşen dosyalara bağlı beş mutant `--only` ile öldü
  (`broken_table_rejects_the_push`, `module_less_never_run`, `module_less_runs_on_the_pushed_tree`,
  `module_less_not_at_the_exit`, `page_calls_line_drifts`); 168 mutantın tamamı birleştirmeden sonra `main` CI'sinde.
- **Pilot.** MF1 (T13, `chain`, `ledger/chain.py`) ve spec isteğiyle dondurma değişmedi. Canlı beynin `done_mf`'i [1]
  ise etkisi yok; eski numaralarla MF2+ bitmişse bu tohum hakeme girince `missing_test:MF2:T38` gibi retler gelir. Kod
  hakeme yalnız tohum dönemiyle girer.
- **Açık kalan.** E161 (16 grup ve genel veri koşucusu), E162 (çıkışın kodda olmayan koşulları, MF17'nin `wiring`
  denetimi dahil), E163 (modülsüz kırmızının iki okuması); E157'nin `14` metni; `spec/tohum/29`, `29b` ve yeni `29e`
  metinleri ayrı adımdır (`docs/asama-0-daraltma-29-29b.md`).

### E88 E162 (2026-10-29) · tohum dönemi · çıkış kapalıya düşer · E180–E183 açıldı
- **Özet satırı.** `setup/summary.json` `seed_epochs[]` taşıyabilir: `{commit, spec_tohum_sha256, seed_sha256,
  bootstrap_sha256}` (`26c`), tam bu anahtarlar, `seed_sha256` beyinde `seed/` yoksa `null` (spec "beyinde varsa"
  dışında sessiz; en dar okuma). `config.load_summary` satırları sıkı okur, boş ya da biçimsiz dizi durmadır; son
  satır geçerli dönemdir. Dizi yoksa davranış öncekidir: `seed_commit`, `seed_tree_sha256` kurulum tohumudur
  (`26c`'de bu adlar yok, E182; başlatıcı E154 için `seed_commit`'i okur, dokunulmadı).
- **Satır kendi commit'ine uymalı.** Dizi varsa `pull` (içerik korumasının dışında) son satırın commit'ini beyinde
  arar ve o commit'in `spec/tohum/` ve `seed/` ağaç hash'lerini satırla karşılaştırır (`cli._check_epoch`); uymazsa
  `stop: setup/summary.json: the last seed epoch ...`, koşu durur, hiçbir push yanlış bir tohuma karşı yargılanmaz
  (`25`: hash özetle uyuşmazsa durur; operatör dosyaları kapalıya düşer, `26c`). Satırı `seed-epoch` komutu
  yazar (git blob'larından, satır sonundan bağımsız); `bootstrap_sha256` `--source`'un `seed/bootstrap/`'udur.
- **(d) Teslimin kendisi.** Baş son satırın commit'iyse push `seed_update`'tir: değerlendirilmez, rakip, test ve
  seri yok, `noop` imzalanır, `last_evaluated_sha` ilerler, `last_accepted_sha` ilerlemez (`cli._seed_update`,
  `decide.NOTHING_TO_JUDGE`). Teslim Kurucu'nun reddedilmiş bir başının üstüne gelse de o kod onun adıyla yeniden
  yargılanmaz (taslak metin içerikle tanımlıyordu, E183).
- **(a) Sonraki push'lar.** Son kabul edilmiş SHA teslimden eskiyse teslim her diff'te kalır. Başın tohum ağaçları
  son satıra eşitken diff'teki `spec/tohum/**` ve `seed/**` Kurucu'nun değişikliği sayılmaz (`meta.changed`
  Kurucu'nunkiler), push kendi türüyle (kod, spec, çıkış, defter) yargılanır; rakibin diff'i tohum yollarını hiç
  taşımaz (`exclude_dirs=HIDDEN_DIRS + SEED_DIRS`): orada kalan tohum yolu ancak teslimdir, başka tohum değişikliği
  rakipten önce reddedilir. Çıkış isteğinde de böyledir: pinli SHA ile istek arasındaki teslim yolları #yalniz'i
  bozmaz, Kurucu'nun değişikliği değildir.
- **(b) Kurucu'nun tohum değişikliği.** Dizi varsa her başın iki ağacı son satıra eşit olmalı: değişen, eklenen ya da
  silinen her tohum dosyası `seed_modified` ve `seed_tree_mismatch`'tir; `null` satırdan sonra eklenen `seed/` de.
- **(c) İmzalı durum.** Dönem durumu sıfırlamaz: `seed_update` her `noop` gibi `last_evaluated_sha`, `runs` ve
  `origin`'i ilerletir, başka bir başın bekleyen rakip sonucunu (`pending_rival`) bırakır; donmuş spec'ler, seriler,
  `repeat_events`, açık iddialar, kanıtlanmış kusurlar, rakip artefaktları ve harcamalar aynen kalır, sonraki push
  onlara karşı yargılanır (seri sürer, yeniden üreticiler istenir). Durum kaybolursa
  `state.initial` son dönemin commit'inden başlar (`25` "Durum kaybolursa").
- **Operatör yolu.** `seed/founder/README.md` "Tohum teslimi": `STOP` ve kill switch, hakem kopyası, beyne tek
  commit (`git archive | tar`), `seed-epoch` satırı, kill switch kapalı, elle tetikleme ve `seed_update` doğrulaması,
  dokunuş satırı. `25` 10b'nin sırası (satır, sonra beyne push) da çalışır: kill switch açıkken hakem koşmaz, push
  edilmemiş commit'i adlandıran satır yalnız koşuyu durdurur.
- **E162.** `decide.EXIT_NOT_CHECKED` = `kurucu-defteri`, `is-akisi`, `agac` (yalnız büyük-küçük harf duyarlı operatör
  adı var; duyarsız ad, ajan yapılandırması, `toy_tree_sha256` yok), `genellik`, `spec` (`#lint #spec #okuyucu`
  satırı), `durustluk`: her çıkışa `exit_condition` `not_checked:<koşul>` ekler, `transferable` olamaz. Denetlenen
  koşullar nedenlerini korur (#testler #kirmizi #lisans, #modulsuz, #rakip, #lock #kilit, #tekrar, #yalniz).
  `not_checked` Kurucu'ya sayılmaz (`29b` "Ret hafızası": yalnız düzeltebildiği); aynı mantıktaki
  `vector_group_missing` çıkış nedeni sayılmaya devam eder (E181). Test, `asama-0/10` tablosunun her satırının ya
  kodda denetlendiğini (yeriyle) ya listede olduğunu ister; sayfaya eklenen satır sessiz geçemez. (Bu commit'te
  "yeri" serbest metindi ve koda bakılmıyordu; incelemeden sonra satırın kodu aranır, E185.)
- **Testler ve mutantlar.** `tests/test_seed_epoch.py` (9 test: (a) iki, kod, spec, çıkış ve defter push'larıyla;
  (b) iki; (c); (d); satır durması; özet okuma; kayıp durum); `test_decision.KindsAndExit`'e üç E162 testi; çıkış testleri (`test_decision`,
  `test_rival_memory`, `test_flow`) altı `not_checked`'i bekler, `test_flow` aktarımı `EXIT_NOT_CHECKED` boşken
  ölçer. 16 yeni mutant (E88 13, E162 3); `ledger_in_the_rivals_diff` ve `reports_in_the_rivals_diff` çapaları
  yenilendi.
- **Kanıt.** Taban (8900760): Windows 342 test OK (18 atlandı), Linux 360 OK (3 atlandı). Dal: Windows 354 OK (18
  atlandı), Linux 372 OK (3 atlandı). Mutasyon: 16 yeni, çapası yenilenen 2 ve değişen satırlara bağlı 3 mutant
  (`non_utf8_name_reaches_json`, `unsafe_name_reaches_the_tree_hash`, `ledger_breaks_an_exit_request`) `--only`
  kümesiyle 21/21 öldü; sonra bütün liste dört parçada 188/188 (47 × 4, Linux kapsayıcı). README'nin 4., 5. ve 7.
  adımı Git Bash'te sahte bir beyinde koşuldu: `git archive HEAD spec/tohum | tar -x -f -` 60 dosya, `seed-epoch`
  satırı (`seed_sha256: null`), `control` ok, `pull` `kind=seed_update`, `pre_reasons []`; satırın
  `spec_tohum_sha256`'sı (`8797ba63…`) `snowball-mcp` HEAD'inin `seed-hash`'iyle aynı (Windows'ta satır sonu gidip
  gelince hash değişmedi). E181 bir koşuyla görüldü: `vector_group_missing:secrets` ile üç çıkış isteği
  `not_learning`, aynı koşudaki altı `not_checked` sayılmadı.
- **Yapılmayan.** `bootstrap_sha256` biçimce okunur, hakemin kendi `bootstrap/` kopyasıyla karşılaştırılmaz (E24);
  teslim `spec/asama-*` ve `spec/INDEX.md` taşıyamaz (E180); altı koşulun denetimleri (E107, E100/E132, E130/E131,
  E102, E79) ve MF17'nin her push'taki `wiring` denetimi; `spec/` bu dalda değişmedi, taslak metin E182/E183'te.

### E88/E162 incelemesi (2026-10-29) · E184 E185 kapandı · E97 kapandı
- **E184, mod biti.** `epoch_seed` artık `gitio.same_under`: `git diff --quiet <son dönemin commit'i> <baş> -- spec/tohum
  seed`; içerik, ad ve mod karşılaştırılır, ağaç okunabilir olmasa da. Eski kodda (bu dalın `b6d821f`'i, Windows,
  denendi) Kurucu'nun kodla birlikte `spec/tohum/00-cekirdek.md`'ye `+x` vermesi `kind=code` idi; şimdi
  `seed_modified` ve `seed_tree_mismatch` ile ret, kabul edilmiş bir push'tan sonra tek başına mod değişikliği de
  (`test_a_mode_change_to_the_seed_is_a_founder_change_too`).
- **E184, okunamayan ağaç.** Teslimden sonra Kurucu'nun `x\y.md` ya da UTF-8 olmayan bir ad eklemesi eski kodda
  `['seed_modified', 'unsafe_path']` veriyordu (Windows'ta da, git'in alt düzey komutlarıyla, denendi); şimdi
  yalnız adın nedeni, `seed_modified:` serisi yok (`test_a_push_the_referee_cannot_read_is_not_charged_with_the_delivery`).
- **E97.** Durum şeması 3: `rejected_exit_request` (son reddedilen isteğin baytlarının sha256'sı, ya da `null`);
  şema 1 ve 2 `migrate` ile taşınır (`25`), biçimsiz değer durdurur. `decide` yalnız değerlendirilmiş bir reddi
  hatırlar (kesinti değil). `pull`, kod push'unda aynı baytları yok sayar: `exit_request_not_alone` yok, push kendi
  türüyle yargılanır; yalnız dosyayı değiştiren push (defter satırları bir yana) yine çıkış isteğidir. İsteği okumak
  için dosyanın git blob'u kullanılır (ağacın başka bir adı okunamasa da). Eski kodda reddedilmiş çıkıştan sonraki üç
  kırmızı kod push'unun ilki `exit_request_not_alone` verdi (`test_a_rejected_exit_request_left_in_place_is_ignored_by_later_pushes`, denendi).
  İlk sürüm aynı baytları tek başına yeniden istemeyi de yok sayıyordu; Linux'taki `test_exit_request_and_import`
  bunu yakaladı, kural kod push'larına daraltıldı (`29b`: yalnız `exit-request.json` değiştiren push çıkış isteğidir).
- **E185.** Tablo testi her denetlenen satırı `cli.py`/`decide.py`'deki satırlarıyla adlandırır ve her birinin kodda
  tam bir kez durduğunu ister. #yalniz'in satırı silinince eski test yeşildi, yenisi kırmızı (denendi).
- **Doğrulama.** Windows 359 test OK (18 atlandı); Linux (`snowball_linux_test:git`) 377 OK (3 atlandı). 11 yeni
  mutant (E184 2, E97 8, E185 1), çapası yenilenen 3
  (`founder_seed_dir_change_passes`, `founder_spec_tohum_change_passes`, `old_state_not_migrated`) ve değişen satırlara
  bağlı 20 eski: 34/34 öldü (Linux, dört kapsayıcı, her birinde önce yeşil baz koşu).
### E161, kısmi (2026-10-29) · genel veri koşucusu ve MF2–MF7'nin vektörleri · E190–E197 açıldı
- **Koşucu.** `vectors.py`'de tek veri yargıcı (`_data`): vakanın komutu, stdin'iyle, `referee/`'den koşar; stdout'un son
  satırındaki JSON nesnesinde `expect`'in adlandırdığı her alan o değeri taşımalıdır, başka alanlar komutundur. Değerler
  JSON olarak karşılaştırılır (`true` ≠ `1`, `1` ≠ `1.0`). `changed` aynı alanları vermeli ve `expect_not`'u vermemelidir;
  cevapsızlık ya da eksik alan da kırmızıdır. Sonuç kimlikleri `<vaka>` ve `<vaka>.changed_input`; 125 `runner_fault`
  kalır (`VectorRun.record`). Grup ya kendi yargıcıyla (`chain`, `cp_lower`, `mcnemar`, `match`, `drill`; dokunulmadı) ya
  `"runner": "data"` işaretiyle koşar; `missing_groups` ikisinden birini bulamadığı grubu sayar, yani yeni grup kod
  değil veridir (`29d`). Tablo güdümlü zamanlama ve `vector_group_missing` uyarısı aynen; MF2–MF7 için artık uyarı yok.
- **Veri.** `vectors.json`'a altı grup, 47 vaka (incelemeden sonra 46: E194), iş akışının uzlaştırdığı vakalar olduğu gibi: komut, stdin, beklenen
  değerler değiştirilmedi; aktarılan metinden tek fark E193'ün kaçışıdır (iki dosya). `fixture` komutun `/vec/` yollarıdır; 72 fikstür dosyası
  `vectors/<grup>/` altında. Fikstürler bayt bayt okunur (tarball hash'i, diff başlığı, satır numarası): `.gitattributes`
  onlara satır sonu dönüşümü uygulamaz (`core.autocrlf=true` Windows checkout'u diff başlıklarına CR katardı). Her
  beklenen değer iki kör bağımsız uygulamanın (A, B) ikisinde de aynıydı; son veri gerçek koşucudan yeniden geçirildi:
  A 94/94, B 94/94 sonuç yeşil (yerel koşucu, Windows). Bu commit'te B'nin kodu ve koşusu repoda yoktu, iddia
  denetlenemezdi; incelemeden sonra B `local/blind_b/referee/` altında ve her koşuda yeniden hesaplanır (aşağıda).
- **Arayüz.** `29f` (`secrets`, `contained`, `profile`) ve `29g` (`npmlock`, `recipe`, `diffguard`): komutlar, girdi
  biçimi, karşılaştırılan alanlar, çıkış kodları, sır biçimleri ve neden sözlükleri, her vakanın amacı; beklenen değer
  yok. 80 satır sınırı (`tohum/15` 1) sayfayı ikiye böldü. `29d` karşılaştırma kurallarını ve iki sayfayı gösterir;
  `INDEX.md`'ye iki satır. `VectorInterfacePagesTest` sayfaların her grubu, komutu ve vaka adını taşıdığını, hiçbir
  beklenen değeri (içerik adresi, yola bağlı neden, cevabın kendisi) taşımadığını denetler.
- **Kanıt.** A'nın altı modülü `local/reference_brain/referee/` altında (`gate/`, `runner/`, `profile/`); beyin onları
  bitmiş bildirmez (`done_mf` [1], testleri yok). `SeedVectorsOnReferenceImplementationsTest`: altı grup A'da 94/94
  yeşil; 50 kırık (her biri bir vakanın yakalamak için orada olduğu hata: biçim eksik, yalnız eklenen satır, ham satır,
  sabit bellek, sabit kullanıcı, yalnız dosya adında anahtar kelime, kilit sırası, yalnız ilk neden …) hedeflediği her sonucu
  kırmızıya çevirir, çökerek değil yanlış cevap vererek; 47 vakanın her biri en az bir kırığın hedefi. `DataRunnerTest`
  koşucunun her kuralını uydurma bir grupla, `SeedDataVectorsTest` verinin biçimini, fikstürlerin varlığını ve ölü
  dosya olmadığını, sırların FAKE olduğunu denetler. `mutate.py`: 16 yeni mutant (koşucu 11, veri 2, sahiplik 1,
  sayfa 1, E191 1) ve anlamı aynı kalıp yeni koda taşınan 3 çapa (`unowned_group_runs`, `missing_group_not_named`,
  `seed_group_owner_drifts`); kopya artık `spec/INDEX.md`'yi de alır.
- **Doğrulama (birleştirmeden önce, `a1e32dd`).** Windows 363 test OK (18 atlandı); Linux (`snowball_linux_test:git`)
  381 OK (3 atlandı), prova yargıcı 31 OK; 16 yeni, 3 yeniden çapalanmış ve `vectors.py`'ye dokunan 3 eski mutant
  (`vector_flake_blamed_on_founder`, `vector_exit_not_kept`, `groups_run_before_their_micro_feature`) Linux'ta
  `mutate.run_mutant` ile, dört kapsayıcıda, her birinde önce yeşil baz koşu: 22/22 öldü. `local/e2e.py` ve 197
  mutantın tamamı koşulmadı (CI'nin `main` işi).
- **Açık kalan.** E161'in kalan 10 grubu (`k0map`, `refs`, `append`, `root`, `flaky`, `cause`, `revert_drill`, `prompt`,
  `status`, `genesis`); E194 ve E195 operatör kararı; E196 ve E197 sınır; E167 (düz parola ataması `secrets`'ın
  kapsamına girer mi) açık.

### E161 incelemesi (2026-10-29) · E198 E199 kapandı · E194 düzeltildi · B repoda
- **`/vec` (E198).** `vectors.fixtures` `vectors/`'ı iş dizinine `vectors.json`'sız kopyalar; `run-tests` (Kurucu'nun
  testleri, vektörler, modülsüz kırmızı) ve `reproduce` (baş ve boş kontrol ağacı) yalnız bu kopyayı `/vec`'e
  bağlar; hakem beklenen değeri kendi `vectors/vectors.json`'ından okur. İncelemenin kâhin beyni (cevabı
  `/vec/vectors.json`'dan okuyan altı modül) eski bağlamada 94/94 yeşildi; `/vec` kopyaya eşlenince 92 sonucun 0'ı
  yeşil, A ve B 92/92 (yerel koşucu, Windows, denendi). `test_the_founders_containers_get_the_fixtures_and_never_the_expected_values`
  eski kodda kırmızıydı (bağlanan dizinde `vectors.json` vardı).
- **E194.** `profile.accept_widened` ve yalnız onun kullandığı iki fikstür (`prop_widen.json`,
  `prop_widen_drop_security.json`) çıkarıldı: 46 vaka, 92 sonuç, 49 kırık (`widening_rejected` gitti). `29f` yalnız
  genişleten öneriyi vakasız bırakır ve `14`'ün iki okumasını da geçer sayar. `test_no_profile_case_decides_what_the_operator_has_not`:
  A genel okumaya çevrilince (yol listesinde her fark ret) `profile` yeşil kalır; eski veride `accept_widened`
  kırmızıydı (denendi). Kaydın ilk metni `01b:35` ve `asama-0/09:43`'ü genişletmeye izin veren kurallar arasında
  sayıyordu; ikisi de "farklıysa reddedilir" der, satır düzeltildi.
- **B, ikinci hesap.** İş akışının B'si (girdisi `cases.json`'da `expect` anahtarı yoktu, denendi) bayt bayt
  `local/blind_b/referee/` altında (11 dosya, sha256'lar kaynakla aynı). `test_every_new_group_is_green_on_the_second_blind_implementation_too`:
  B'nin her modülü A'nınkinden farklı, gerçek koşucuda 92/92 yeşil; mutant `blind_b_disagrees`. B eski veride de
  94/94 verdi (`a1e32dd`'nin verisi, E193'ün baytları dahil; denendi). Kör yazıldığı bu oturumun iş akışının
  kaydıdır; repo bunu değil, iki kodun her koşuda aynı değeri verdiğini gösterir.
- **E199.** (a) Veri grubu, `interface` sayfası Kurucu'nun ağacında (`run-tests`'in açtığı ağaç) yoksa koşmaz ve
  `vector_groups_missing`'te adlandırılır: kod push'unda uyarı, çıkışta ret; tohumun kendi denetimi (ağaçsız) aynı.
  (b) `vectors.BUDGET_S` 1200 s: bir push'un bütün vektör çağrıları, yeniden denemeler dahil; her denemenin süresi
  kalan bütçeyle sınırlı. Bitince kalan vektörler `not_run:time_budget` ile kırmızı, `exit` yok, `runner_fault`
  değil, Kurucu'nundur (E18'in planındaki ad). Spec sessiz, değer seçimdir: dürüst çağrı birkaç saniyedir, bütçe
  `kos`'un 60 dakikasının yarısını aşamaz (`test_the_vectors_leave_the_kos_job_half_its_time`); E161'in kalan
  grupları gelince yeniden bakılır. Eski kodda her girdide asılı kalan bir uygulama 188 çağrı × 120 s = 22 560 s
  (376 dk) sürerdi, şimdi 10 çağrı ve 1200 s (denendi). (c) `_last_json` `RecursionError`'ı "JSON nesnesi yok"
  sayar: 100 000 seviyelik satır kırmızı, `run-tests` çökmez (eski kodda test `RecursionError` ile düştü). (d) Liste
  ve nesne içindeki değerler için test; incelemenin mutantı (`a == b and type(a) is type(b)`) eski `test_units`'te
  yaşıyordu (53 OK, denendi), yeni testle ölür (`data_python_equality_nested`).
- **Doğrulama.** Windows 372 test OK (18 atlandı); Linux (`snowball_linux_test:git`) 390 OK (3 atlandı). 13 yeni
  mutant, çapası yenilenen 3 (`missing_group_not_reported`, `data_groups_have_no_judge`, `control_tree_is_the_head`)
  ve değişen dosyalara bağlı 23 eski: 39/39 öldü (Linux, dört kapsayıcı, her birinde önce yeşil baz koşu). İki
  `reproduce` testinin referee'sine `vectors/` kondu (`reproduce` artık onu kopyalar; üretimde dizin hep var).
- **Açık kalan.** E194 ve E195 operatör kararı; E161'in kalan 10 grubu; E18 (testlerin ve yeniden üreticilerin
  toplam süresi).

### E161, MF8–MF13 (2026-10-30) · `k0map`, `refs`, `append`, `root`, `flaky`, `cause` · E230–E235 açıldı
- **Veri.** `vectors.json`'a altı veri grubu, 44 vaka (88 sonuç), iş akışının uzlaştırdığı vakalar olduğu gibi: komut,
  stdin ve beklenen değerler değiştirilmedi, düşen vaka yok. Aktarılan metinden tek fark `append.refuse_secret_row`'dadır:
  sahte belirtecin `p`'si stdin'de JSON kaçışı `\u0070` olarak yazılır (vakanın amacı bunu ister; ham `vectors.json`
  sır biçimi taşımaz, `test_secret_shaped_text_stays_in_the_secrets_fixtures`). 46 fikstür dosyası `vectors/<grup>/`
  altında, satır sonu dönüşümsüz (`.gitattributes`: `k0map`'in manifestoları koşu dosyalarının sha256'sıdır, `append`
  defter satırlarını bayt bayt karşılaştırır). Her grup arayüz sayfasını (`interface`) adlandırır; sayfa Kurucu'nun
  tohumunda yoksa grup koşmaz ve `vector_group_missing`'te kalır (`test_run_tests_names_the_vector_groups_the_seed_still_lacks`,
  `29h` ile). Tablo güdümlü zamanlama aynen; MF8–MF13 artık uyarmaz. İkinci okuma (iş akışının betiği): her vakanın
  amacı, değişmiş girdi açıklaması ve beklenen değeri aktarılan metinle, komutu ve stdin'i A'nın ve B'nin makine
  dökümüyle, her fikstür baytı iki dökümle, `k0map` manifestoları dosyalarıyla aynı (`good.hashes_bad.json` bir
  hanesiyle farklı); A'nın ve B'nin kayıtlı çıktıları her beklenen değeri verir, hiçbir değişmiş girdide vermez: 44/44.
- **Arayüz.** `29h` (`k0map`, `refs`) ve `29i` (`append`, `root`, `flaky`, `cause`); 80 satır sınırı (`tohum/15` 1)
  ikiye böldü. Komutlar, girdi biçimi, taklitler (kaydedilmiş GitHub API'si, commit sayan yazar, taklit imzalayıcı,
  kaydedilmiş Rekor), karşılaştırılan alanlar, çıkış kodları, her vakanın amacı ve spec'in sessiz kaldığı yerdeki
  seçimler; beklenen değer yok. `29f` ve `29g`'ye dokunulmadı; `29d`'de yalnız altı grubun satırı sayfasını gösterir;
  `INDEX.md`'ye iki satır, `00b`'ye iki sayfa. `VectorInterfacePagesTest` dört sayfayı denetler; beklenen değer
  denetimi 40 ve 64 haneli onaltılık hash'leri de arar (yeni grupların cevapları çoğunlukla hash'tir).
- **Kanıt.** A'nın modülleri (`gate/check.py`, `target/write.py`, `ledger/append.py`, `ledger/anchor.py`,
  `gate/sentinel.py`, `gate/revert.py`, ortak `gate/_strict.py`) `local/reference_brain/referee/` altında; beyin
  onları bitmiş bildirmez (`done_mf` [1]). İki uyarlama, ikisi de dosyasında yazılı: A'nın kendi `gate/secrets.py`'si
  yerine bu beynin MF2'si çağrılır (`scan_text`, satır anlamıyla `scan_rows`); A'nın `ledger/chain.py`'si komut
  satırı olmadan `ledger/_strict.py`'dir, beynin MF1'i (`ledger/chain.py`) değişmedi. `SeedVectorsOnReferenceImplementationsTest`:
  on iki veri grubu A'da 180/180 yeşil (MF8–MF13 88/88), MF10'un da sahiplendiği `chain` 6/6. 54 yeni kırık (`k0map`
  17, `refs` 8, `append` 10, `root` 9, `flaky` 4, `cause` 6), her biri bir vakanın yakalamak için orada olduğu hata:
  her hunk'ı ya da başka yolun hunk'ını saymak, hunk içindeki satırı kaydırmak ya da konumuna eşlemek, manifestoya
  bakmamak, kural başına mandal, satırına bakılmayan hedef, JSON olarak karşılaştırılan koşular, adayın `fix_range`'i,
  yalnız ilk neden, eksik `merge_paused` = `false`; ikinci ebeveynin ya da merge'ün kendi ağacı, kayıttaki yanıttan
  ref, sonunda `/` olmayan `brain` öneki, `..`, PR'nin base'i; satır başına commit, önceki sürüme zincirleme, kanonik
  yalnız-ekleme, ham satır taraması, `proposed_by`'ın güveni, MF1'in `--previous`'ı; bölümün ilk satırı, kanonik
  olmayan kök, sabit imza; tek kırmızı koşuda geri alma, araçlar üzerinden toplanan lint … Her kırık hedeflediği her
  sonucu kırmızıya çevirir, çökerek değil yanlış cevap vererek; 44 vakanın her biri en az bir kırığın hedefi.
  `mutate.py`: 6 yeni mutant (MF8'in beklenen değeri ve MF9'un fikstürü kayar, sır düz yazılır, sayfadan vaka düşer,
  sayfa dizinde yok, sayfa bir hash gösterir), açıklaması güncellenen 1 (`data_groups_have_no_judge`).
- **Bütçe (E199 b).** Bütün MF'ler bitince push başına 186 vektör çağrısı (veri 180, `chain` 6). Sabit imajlı gerçek
  kapsayıcıda bir `k0map` çağrısı 2,0–5,0 s (ortalama 3,2 s; beş çağrı, Windows Docker Desktop, test takımı yanında):
  yaklaşık 590 s, `BUDGET_S`'nin 1200 s'si içinde; değer değişmedi.
- **Bulgular.** E230 sözleşmenin spec sessizken yaptığı seçimler (sınır); E231 `cause`'un `build_ok` ve lint toplamı
  girdilerinin üreticisi yok; E232 `01b` bayt ister, MF1'in `--previous`'ı kanonik karşılaştırır; E233 MF8–MF13'ün B'si
  repoda değil; E234 `stage0.json:14` ile `26a:29` MF10–MF11 çağrı yönünde çelişir; E235 `refs.revert_first_parent_tree`
  ebeveynin `onto`'nun başı olduğunu sabitlemez (denendi).
- **Doğrulama.** Windows 399 test OK (18 atlandı); Linux (`snowball_linux_test:git`) 417 OK
  (3 atlandı). 6 yeni, açıklaması güncellenen 1 ve `vectors.json`'a bağlı 3 eski mutant
  (`seed_group_owner_drifts`, `seed_vector_expect_drifts`, `seed_data_group_owner_drifts`) Linux'ta, üç kapsayıcıda,
  her birinde önce yeşil baz koşu: 10/10 öldü. `local/e2e.py` ve bütün mutantlar koşulmadı (CI'nin `main` işi).
- **Açık kalan.** E161'in kalan 4 grubu (`revert_drill`, `prompt`, `status`, `genesis`); E230–E235.

### E236–E240 (2026-10-30) · MF8–MF13 incelemesinin beş bulgusu · `29j`
- **Yeniden üretme.** Her bulgu önce düzeltilmemiş ağaçta (`a75a4e8`) gerçek veri koşucusuyla gösterildi
  (`vectors.run_vectors`, yerel koşucu, A'nın kopyasında tek metin değişikliği). `gate/check.py`'de altı kırık (E236:
  `b = 0` hunk'ı `a ≤ L`'de biter; ekleme hunk'ları hiç kaydırmaz; `d = 0` → `[c, c]`; `d = 0` → `[c, c−1]`; `b = 0`
  hunk'ında `p = a`; eklenen satır `e+2`'ye kadar) ve üç kırık (E237: hash yalnız `base.jsonl`'da; `checks.json`'ın hash'i
  denetlenmez; baytlar yalnız aday koşularında karşılaştırılır) `k0map`'te 22/22 yeşil kaldı; `gate/sentinel.py`'de
  `CONSIDERED = 3` `flaky`'de 8/8 (E239); `target/write.py`'de `"force": True` `refs`'te 12/12 (E240). E238: `good.jsonl`'a
  `not json` satırı eklenmiş defterde A `{"hard_stop": false}` (çıkış 2), B `{"hard_stop": true}` (çıkış 2), bu beynin
  MF1'i (`ledger.chain verify --previous`) `{"valid": false, "broken_row": "line:3"}`; `tampered.jsonl` ve `{rows}`
  olmayan stdin'de A `hard_stop: false`, B `true`. Yeni vakalar düzeltilmemiş A'da kırmızıdır:
  `append.refuse_unparsable_ledger` ve `append.refuse_broken_chain_first` `hard_stop: false` verir,
  `refs.update_never_forces`'ta `forced` yok.
- **E236.** `k0map/edge.patch` git'in kendi `-U0` çıktısıdır, bölüm başlıkları atılmış: saf ekleme `@@ -5,0 +6 @@`, saf
  silme `@@ -7,2 +7,0 @@` (`git diff --no-index -U0`, denendi; git `a`'dan sonraki eklemeyi `-a,0` yazar, `rate.js`'te
  9. satırdan sonraki yorum için de `@@ -9,0 +10 @@`). Vakalar `map_insertion_point` (5. satır kaymaz),
  `map_deleted_line` (silinen satır `[]`), `map_after_pure_hunks` (iki saf hunk'ın net kayması); karar düzeyinde
  `insertion_not_distinguished` (`cand/note`: yalnız yorum ekleyen aday; `kos/keep`: koşusu tabanınkiyle aynı) ve
  `insertion_past_fix` (`cand/past`: 9. satırı düzeltip 10. satırdan sonra ekler; değişmişi `cand/after`, `e+1`'de).
  Aday dosyası bilinen satırlarıyla (2, 3, 4, 9, 10) yeniden kuruldu, diff'ler ondan üretildi. `29h` `b = 0` hunk'ını ve
  `p = a+1`'i açık yazar; eski `a+b` formülü `b = 0`'da `a` verirdi.
- **E237.** `forged_candidate_run`: yarım düzeltme (`cand/half`) temiz aday koşusu (`kos/good`) ve gerçek koşunun
  manifestosuyla (`half.hashes.json`), yeni fikstür yok; değişmişi gerçek koşu (`not_distinguished` vakası).
  `forged_checks`: manifesto `rate` testi düşmüş `checks.json`'ın hash'ini (`ratchet/checks.json`'ınki) tutar, dizindeki
  hepsi geçer. `base_nondeterministic`: `base.jsonl`'ın üçüncü satırında bir boşluk baytı (`kos/base_jitter.jsonl`). Her
  `koş` dosyasının hash'i ve iki koşu dosyasının baytları birer vakayla sabit.
- **E238.** Spec "JSON Lines olmayan" defteri adlandırmaz; `13:35` defteri JSONL tanımlar, `01b:26-28` tutmayan denetimde
  yazmaz ve sert durur, `13:53-55` zincir kırığını sert duruş sayar: en dar tutarlı okuma, JSON nesnesi olmayan satırın
  zinciri kırmasıdır (E230'a seçim olarak eklendi). `29i` (1)'i stdin okunmadan önce koyar; çıkış 2 okunamayan dosya ve
  (1) tuttuktan sonraki istek içindir; önceki sürüm yalnız bayt olarak karşılaştırılır. A buna göre (`_verified` önce,
  `_request` sonra). Vakalar `refuse_unparsable_ledger` (`append/garbled.jsonl`: yazılırken kesilmiş son satır) ve
  `refuse_broken_chain_first` (yeni satırı `prev_hash` taşıyan istek). B ikisinde de `hard_stop: true` verir; JSON Lines
  olmayan defterde çıkışı 2'dir, çıkış kodu karşılaştırılmaz (`29d`).
- **E239.** `29j` spec'in sessizliğini (`04a:24` üç koşu der, ilk koşuyu saymayı söylemez) ve seçimi gerekçesiyle yazar
  (ilk koşu artı üç yeniden koşu: `07:27` 3/3 doğrulamasını kırmızı koşudan sonraya koyar); E230'a eklendi.
  `flaky.two_reruns_rerun` ilk koşu ve iki yeniden koşuda düşen testte `rerun` ister; değişmiş girdisi
  `red_three_reruns`'ınkidir.
- **E240.** `refs`'in yeni çıktısı `forced` (bir `PATCH git/refs` gövdesi `force: true` taşıdı mı); `api.json`'a
  `brain/c/7`'nin `PATCH` kaydı; `refs.update_never_forces`, değişmişi `brain/state`. `brain/state` ve `brain/integration`
  dışındaki dallarda ruleset yok (`01b:27,38`, `25a:17`).
- **Sayfalar.** `29h` 80, `29i` 79 satırdı; eklemeler sığmadı (`tohum/15` 1). MF sırasıyla üç sayfa: `29h` `k0map`;
  `29i` `refs`, `append`; yeni `29j` `root`, `flaky`, `cause`. Taşınan bölümlerin metni değişmedi, E238 ve E239'un
  cümleleri ve yeni vakalar dışında. `vectors.json`'da dört grubun `interface`'i ve dört grubun `source`'u, `29d`'nin dört
  satırı, `INDEX.md`, `00b`, `docs/ana-taslak.md`; `29f`, `29g` ve `asama-*`'ya dokunulmadı.
- **Kanıt.** 12 yeni vaka: MF8–MF13 56 vaka, 112 sonuç; A 204/204 veri sonucu ve `chain` 6/6 yeşil. B (iş akışının kör
  B'si, oturumun `wf4/B/_src`'si; repoda değil, E233) yeni vakalardan önce yazıldı ve değiştirilmeden 112 sonucun 110'unu
  verir; kalan ikisi `refs.update_never_forces`'ındır, B'de `forced` alanı yok. B'ye kendi çağrı kayıtlarından `forced`'ı
  bildiren tek satır eklenince `refs` 14/14, o B'de `"force": True` ile yeni vaka kırmızı. Bu koşular oturumun kaydıdır,
  repo onları yeniden koşmaz. 14 yeni kırık (E236 6, E237 4, E238 2, E239 1, E240 1), her biri hedeflediği sonucu yanlış
  cevapla kırmızıya çevirir; çapası taşınan 2 (`chained_onto_the_previous_version`, `append_only_unchecked`).
  `mutate.py`: 6 yeni mutant, sayfası `29j`'ye taşınan 2, açıklaması değişen 1.
- **Bütçe (E199 b).** Bütün MF'ler bitince push başına 210 vektör çağrısı (veri 204, `chain` 6). E161'in ölçümüyle (çağrı
  başına 2,0–5,0 s, ortalama 3,2 s) yaklaşık 670 s, en kötü 1050 s: `BUDGET_S`'nin 1200 s'si içinde, değer değişmedi.
  E161'in kalan dört grubu gelince sınır yeniden ölçülmeli.
- **Doğrulama.** Windows 399 test OK (18 atlandı); Linux (`snowball_linux_test:git`) 417 OK (3 atlandı); test sayısı
  değişmedi, yeni kırıklar `test_every_case_turns_red_on_an_implementation_broken_the_way_it_targets`'in alt
  testleridir. 6 yeni mutant, sayfası ya da açıklaması değişen 3, değişen dosyalara bağlı 6
  (`seed_group_owner_drifts`, `seed_vector_expect_drifts`, `seed_data_group_owner_drifts`, `seed_new_expect_drifts`,
  `seed_new_fixture_drifts`, `seed_secret_written_plain`) ve sayfa ile veri yargıcının 2'si (`interface_page_unchecked`,
  `data_groups_have_no_judge`) Linux'ta, dört kapsayıcıda, her birinde önce yeşil baz koşu: 17/17 öldü. `local/e2e.py`
  ve bütün mutantlar koşulmadı (CI'nin `main` işi).
- **Açık kalan.** E161'in kalan 4 grubu; E230–E235 (E230'a üç seçim eklendi: `forced`, JSON Lines olmayan defter, 3/3).

### Kararlar partisi 1 (2026-10-29) · E194 E195 E200 E201 E202 · E210 açıldı
- **Paketler.** Kararlar iki pakettir. Paket 1 (bu commit) yalnız tohum metnidir, sonraki tohum dönemiyle teslim
  edilebilir: E194, E195, E200 (metin), E201, E202. Paket 2 (E173, E200'ün vakası, `29h` bölünmesi, `tree_t1`
  göçü) E203 yüzünden bekletilir ve ayrı commit'tedir; tohum dönemi `spec/tohum` ve `seed/`'i taşır (yukarıda,
  E88), paket 2'nin hiçbir parçası paket 1'in commit'inde yoktur.
- **E194.** `14:14-19`: öneri türetmeyi yalnız genişletebilir (güvenlik ve hariç yollara türetilmemiş yol eklemek
  kabul, türetilen bir yolu düşürmek ret); başka her farkta ret (`banned_constructs`, `registry_egress`, diller,
  birim adayları, etkilenen-test komutu, test yolu kuralları). `01b:35` aynı (baş cümlesi genel okumayı
  taşıyordu). `14:43`, `14:52` değişmedi. `29f` "Öneri iki yol listesini yalnız genişletebilir". `banned_constructs`'a
  eklemek, test yolu kurallarını değiştirmek ve `registry_egress`'i daraltmak yine ret: hiçbir çapa izin vermiyor
  (dar seçim). `29d` `profile` satırı "yalnız genişleten kabul" demez: o satır grubun bağladığını sayar ve
  `accept_widened` gelmedi (E210). Donmuş `asama-0/09:43` (test 19, "farklıysa ya da ... daraltıyorsa") eski
  metniyle kalır; değiştirmek E180 yolunu ister, tohum geçerlidir.
- **E195.** `29d` `diffguard` satırı ve `29g` `diffguard` paragrafı: diff'in `brain/integration` başına uygulanması
  `gate.check`'in (MF8) işidir, `gate.diffguard` ağaç almaz (`26a:25`). `k0map` satırı ve `26a:26` değişmedi;
  başa uygulanma vakası `k0map` arayüzü yazılırken (E161'in kalanı). Donmuş `asama-0/08:12` aynen kalır.
- **E200.** `26c`: `install_scripts_required[]`'in elemanı kilitteki tam paket yolu (ör. `node_modules/x`) ya da
  tarball'ın `ad@sürüm`'ü; çıplak ad hiçbir paketi işaretlemez. `29g` aynı ("ne kilit yolu ne `ad@sürüm`
  `install_scripts_required`'da var; çıplak ad işaret değildir"). Çıplak adın çıkış 2 olması yazılmadı: `29g`'nin
  2'si okunamayan kilit ya da aynadır ve MF6'nın neden listesi kapalıdır. Vaka `29g`'ye sığmıyor: eklenince sayfa
  81 satır (115, 118 ve 120 sütunda ölçüldü), sınır 80 (`tohum/15:9-10`, `test_wiring.py:281`).
- **E201.** `26c`: lint yeşili, `lint_cmd`'nin üç koşusunun her biri 0 ya da 1 ile biter, üçünün çıkış kodu ve
  stdout'u bayt bayt aynıdır (ESLint'te 1 ihlaldir; ölçüt 5 ihlal ister, ölçüt 6 yeşil). Ölçüt 4–5'in doğrulanması
  spec'e yazılmadı, açık kalır (`asama-0` donmuş, E180).
- **E202.** `26c`: `toolchain` `node@X.Y.Z`, kesin sürüm, birimin dizininden köke en yakın sürüm dosyasındaki; imaj
  etiketindeki sürüm de `X.Y.Z`. Sürüm dosyalarının adları ve etiket biçimi yazılmadı (spec sessiz).
- **E210.** `profile.accept_widened` ve iki fikstürü eklenmedi. Repodaki A ve B (E173'süz) göçmemiş `tree_t1`'de
  (sha256 `53ba6d3a…`) ikisi de `{"accepted": true, "reasons": []}` (çıkış 0), değişmiş girdide
  `{"accepted": false, "reasons": ["narrows:security_paths"]}` (çıkış 1) verdi (`widened.py`, fikstürler
  tasarımcının üretecinden, sha256 `6d25117a…` ve `c2863245…`). `test_no_profile_case_decides_what_the_operator_has_not`
  `test_no_profile_case_pins_widening_while_its_case_is_disputed` oldu: aynı kontrol, karar sonrası gerekçesiyle;
  vaka gelince ters çevrilir (genel okuma onu kırmızıya boyamalı). Mutant `seed_pins_widening`'in gerekçesi aynı.
- **Doğrulama.** Windows 393 test OK (18 atlandı); Linux (`snowball_linux_test:git`, `git archive` ağacı) 411 OK
  (3 atlandı), taban (26a49d7) de 411 OK. Sayfalar: `14` 65, `26c` 74, `29f` 79, `29g` 80, `01b` 70, `29d` 50 satır.

### E241 (2026-10-30) · başlatıcı · bir sonuç yalnız kendi başına yazılır

- **Ne oldu.** Operatör tohum dönemi 2 için `STOP` koydu; döngü 6'nın hakem koşusu (`d14b44a`, MF9) sürüyordu. `dispatch_referee` `STOP`'u görünce beklemeyi bıraktı (`still_running`), `judge` en yeni `bootstrap-state` artefaktını, yani `2be80ed`'nin kabulünü indirdi; yeniden inceleme döngüsü yalnız aynı başın sonucunda döndüğü için çıktı ve `cycle` onu `d14b44a`'nın kararı diye yazdı (`pilot-log.md`, `pilot-metrics.jsonl`: `verdict: accepted`, `reasons: []`).
- **Kök neden.** Sonuç ile başın eşleşmesi yalnız yeniden inceleme koşulunda vardı; dönüşte denetlenmiyordu. Aynı sınıf: zaman aşımı, başlamayan koşu, `STOP`.
- **Düzeltme.** `judge` dönüşte `verdict.head == head` ister; değilse `None` döner ve nedeni (`dispatched.conclusion`) söyler; kayıt `verdict: null` olur, yargılanmamış baş sonraki başlangıçta önce yargılanır (E168). Tek kural tek yerde: `cycle` ve yakalama dalı `judge`'ın sonucunu kullanır.
- **Kanıt.** Yeni test önceki başın kabulünü döndüren sahte hakemle döngü koşar: kayıt `verdict: null`, günlükte "Hakemin kararı" yok, `still_running` var. Kontrol satırı silinince (mutant `launcher_lends_an_older_verdict`) test kırmızı (denendi). `test_founder_capsule` 24 test OK.
- **Kayıt düzeltmesi.** `pilot-metrics.jsonl`'daki `d14b44a` satırı `verdict: null` ve `corrected_by: E241` ile düzeltildi; gerçek karar hakemin koşusu bitince günlüğe yazıldı.

### Tohum dönemi 2 (2026-10-30) · E242

- **Teslim.** `S` = snowball-mcp `38fd868` (CI yeşil), `D` = beyin `427cfe8`: `29h`/`29i`/`29j` (MF8–MF13 vektör arayüzleri), `29d`, `00b`, `31`–`31h` mimari ilkeler kataloğu. Hakem `38fd868`'e senkronlandı (144 dosya: MF8–MF13 vektörleri ve fikstürleri, testler, E241); `seed_epochs[]`'e ikinci satır (`seed-epoch` komutuyla). Doğrulama koşusu: `kind: seed_update`, `verdict: noop`, `head: 427cfe8`; durum korundu (son kabul `d14b44a`, `spec/asama-0` donmuş, açık iddia `92156b07bb5f`, seri yok). E173'ün metni bilerek teslim edilmedi (sahip kararları partisi ayrıca düzeltiliyor).
- **E242.** İlk hakem kopyası 262 dosya gösterdi; kod değişmemişti. Sayım: `HEAD`'de CR 0, `git archive` çıktısında 5 (`core.autocrlf=true`), `-c core.autocrlf=false` ile 0. Betik ve README düzeltildi; ikinci kopya 144 dosya, CR 0. Beyne giden teslim ve hakeme giden her commit aralığı CR 0 (denendi).
### E260 (2026-10-30) · yeniden üreticinin kutbu · dal `gaps/reproducer-polarity`
- **Kanıt (canlı, imzalı sonuçlar).** 86cc8b4 (koşu 40962413404): rakibin iddiası `87c088321252` doğruydu ("bir satır
  gizli adlı anahtara uzun değer atarsa temiz raporlanır"), ama yeniden üreticisi `expect_stdout_contains: "\"clean\":
  false"` bekledi, yani doğru kodun çıktısını; baş `{"clean": true, "lines": []}` yazdı, gösterilmedi, açık iddia
  kaldı. Kurucu düzeltti (f668776) ve f102'de olacakları yazdı. Koşu 40966312329'da durum yeniden koşusu `shown: true,
  tautological: false, reproduced: true` verdi (rakibin 429'u kararı erteledi); 40967821066'da düzeltme
  `refutation_reproduced repro:027465767d2d46dc` ile reddedildi, rakip `not_refuted` dediği hâlde; E08 sonraki her
  doğru başı reddedecekti, operatör 40969705356'da `waived_refutations` ile elle kırdı. Pilotun eldeki 21 imzalı
  sonucunda rakibin 8 yeniden üreticisi var: 7'si belirti kutbunda, her biri kendi başında kanıtlandı ve kabul
  edilen düzeltmede kapandı; 1'i (bu) doğru çıktı kutbunda. E06'nın ikinci provadaki ters beklentisi de aynı
  hataydı: protokoldeki düzyazı kural ("kod doğru olsaydı görülmemeli") ikisini de önlemedi. E07 (c)'nin canlı
  veride tek tetiklenişi bu sahte kanıttı; meşru bir kanıt üretmedi.
- **Kök neden.** Kutup anlamdır, baytlarda yoktur. Hakem bir metnin başta ve boş ağaçta görünüp görünmediğini
  görür; doğru çıktıyı bekleyen yeniden üretici doğru kodda, belirtiyi bekleyen aynı çıktılı kusurlu kodda aynı
  baytları üretir. Boş ağaç (E09) yalnız koddan bağımsız gösterimi ayırır: doğru çıktı da orada yoktur. Buradan iki
  yol: (1) E07 (c) kendi başında kanıtlamamış yeniden üreticinin sonraki baştaki gösterimini kanıt sayıyordu; o
  gösterim yalnız "bu baş beklentiye doğru değişti" der, yönünü (gerileme mi düzeltme mi) söyleyemez; (2) aynı
  karışıklık yanlış bir iddiayı doğru kodda ilk başta kanıtlar.
- **Çözüm.** (a) *Kanıt yalnız kendi başında* (`decide`): açık iddianın durum yeniden koşusu kanıt değil gözlemdir;
  `observed`'a baş, `shown`, `contradicted` ile yazılır, sonraki rakibe ve çıkışta operatöre (`exit.open_claims`)
  verilir; rakip iddiayı `open_claim` ile yeniden gönderirse incelenen başta yargılanır ve orada kanıtlanır. Her açık
  iddia yeniden gönderilebilir; `rewrite_allowed` yalnız farklı bir yeniden üreticinin saklanıp saklanmayacağını
  söyler (bir kez), aynısını göndermek yeniden yazma sayılmaz. Yol 1 mekanik olarak kapandı, canlı durumdaki eski
  açık iddialar dahil. (b) *İki taraflı sözleşme* (`rival`, `reproduce`): her yeni yeniden üretici belirtiyi
  (`expect_*`) ve doğru çıktıyı (`correct_*`) adlandırır; doğru taraf belirtinin yerine gelen çıktıdır, belirtinin
  adlandırdığı en az bir çıkış kodunu ya da akışı adlandırır; taraflardan biri ötekinden çıkamaz (doğru taraf
  belirtinin göründüğü her yerde görünemez, belirti de doğru tarafın göründüğü her yerde). Bir tarafın ne zaman
  göründüğü tek kuraldır (`rival.side_holds`): koşucu başı onunla okur, doğrulayıcı bir tarafı ötekinin en küçük
  çıktısında (`_least_shown`) onunla dener. Yargılandığı başta doğru taraf da görünürse (`contradicted`) kanıt
  yoktur. Canlı hatanın biçimi (iki tarafa doğru çıktı) doğrulayıcıda reddedilir ve rakibe hatasıyla döner.
  `reproduced` E260'tan önceki anlamındadır (belirti kod yüzünden görünür: başta görünür, boş ağaçta görünmez; boş
  ağaç belirti göründükçe koşar); kutup kuralı yalnız `decide`'deki kanıttadır. E08 aynen, kodu da temeldeki gibi:
  kanıtlanmış kusur belirtisi göründükçe engeller, baş yanında doğru çıktıyı yazsa da. Alanların tek kaynağı
  `rival.OBSERVABLES`, `SYMPTOM`, `CORRECT`, `REPRODUCER_FIELDS`: şema, doğrulayıcı, koşucu, imzalı durum ve anahtar
  onu okur (önceden dört ayrı kopyaydı). Pilot satırı (`launch.py`) `reproduced`'ı ve
  `old_refutations_still_reproducing`'i ham koşulardan değil hakemin `refutation_reproduced` ve
  `refutation_still_reproduces` nedenlerinden sayar.
- **Uyum.** Durum şeması 3 kaldı. E260'tan önceki yeniden üreticiler (`correct_*` yok) yüklenir, anahtarları aynı
  (anahtar komut + belirti; canlı `027465767d2d46dc` testte sabit) ve yalnız belirtiyle okunur: kanıtlanmış
  kusurların anlamı aynı. Açık iddiaların anlamı bilerek değişti: sonraki başta kanıtlanmazlar. Yeni durum
  `correct_*` taşıyabilir; E260 öncesi bir hakem onu `bad open_claims` ile reddedip durur (sessiz yanlış okuma yok).
  Sonuç şeması `snowball-bootstrap-result/1` kaldı: yeniden üretici sonuçlarına `contradicted`, çıkış bloğunun açık
  iddialarına `observed` eklendi (yalnız ekleme); `reproduced`'ın anlamı aynı.
- **Bedel.** Yalnız eski bir açık iddianın yakaladığı gerileme artık kendiliğinden reddedilmez: yeniden koşu
  gösterir, kayda geçer, sonraki rakip görür; gönderirse kanıtlanır (test). Durum yeniden koşuları aynı koşuda
  rakipten sonra gelir (`yeniden`, `cagir`'a bağlı), yani rakip bir önceki başın gözlemini görür; incelediği başta
  yargılatmak için iddiayı göndermesi gerekir, protokol bunu açıkça söyler. Çıkış başında rakip koşmaz: orada
  görünen açık iddia kanıtlanmaz, çıkış bloğunda gösterdikleriyle (baş, `shown`, `contradicted`, `tautological`)
  listelenir, çıkışın (B) parçasının sahibi operatör okur. Çıkış koşulu yapılmadı: kutbu bilinmeyen bir gösterim
  çıkışı kapatırsa canlı iddia gibi ters bir iddia her doğru çıkış başını kalıcı olarak kapatırdı, açık iddia için
  feragat yolu da yoktur.
- **Sınır (mekanik kapanmaz).** İki tarafı bilerek ters yazan (belirtiye doğru çıktı, doğru tarafa kusurun
  çıktısı) yeniden üretici yanlış bir iddiayı doğru kodda yine kanıtlar; bunu yalnız anlamı okuyan ayırır. Kapanış
  yolu operatör feragatidir; Kurucu'nun kanıtlı itirazını hakeme ya da rakibe taşıyan yol yok (açık).
- **Şüpheci turu (2026-10-30).** İlk sürüm (`afdebbf`) beş yerde kırıldı, hepsi kök nedeninde kapandı:
  (1) `reproduced` doğru tarafı da içeriyordu, E08 böylece değişmişti: kanıtlanmış iki taraflı kusur, belirtisi hâlâ
  görünen ama yanında doğru metni de yazan bir başta (kısmi düzeltme, zengin çıktı) kapanıyordu; doğru metni bir
  yere yazmak yetiyordu. `reproduced` eski anlamına döndü, kutup yalnız kendi başındaki kanıtta; boş ağaç belirti
  göründükçe koşar. (2) Doğrulayıcı "belirtinin parçası"nı alan alan, koşucu taraf bütünüyle okuyordu; ayırt
  edilebilen dürüst yeniden üretici (`expect_exit 0` + `value=10;`, `correct_exit 0` + `value=1;`) reddediliyordu.
  Kural tekleşti (`side_holds`, `_least_shown`). (3) Başka akışta doğru taraf (stdout belirtisinin yanında
  `correct_exit 0`) kusurlu başta da görünüp doğru bir kanıtı sessizce düşürüyordu, rakibe hiç dönmüyordu: doğru
  taraf belirtinin bir gözlenenini adlandırmalı. Belirtinin doğru tarafın içinde kalması (`"clean"` /
  `"clean": false`) da reddedilir: o belirti doğru kodda görünür ve E08 düzeltmeyi reddederdi. (4) Çıkış bloğu açık
  iddiaların çıkış başında ne gösterdiğini saklıyordu: artık `observed` taşır (çıkış koşulu değil, yukarıda
  gerekçe). (5) Protokol yeniden yazma hakkı bitmiş iddiayı yeniden göndermeyi yasak gibi gösteriyordu, aynısını
  göndermek de o hakkı yakıyordu: protokol her açık iddianın gönderilebileceğini söyler, aynısı yeniden yazma
  sayılmaz.
- **Testler.** `tests/test_reproducer_polarity.py` (14), canlı veri `fixtures/rival/polarity_87c088321252.json`
  (imzalı sonuçlardan kopya). Eski kodda kırmızı: yol 1 `[('rejected', ['refutation_reproduced'], 1), ('rejected',
  ['refutation_still_reproduces'], 1)] != [('accepted', [], 0), ('accepted', [], 0)]`; yol 2 `('rejected',
  ['refutation_reproduced'], [...]) != ('accepted', [], [])`; doğrulayıcı tek taraflı canlı yeniden üreticiyi kabul
  ediyordu; pilot satırı `1 != 0`. Şüpheci turunun testleri `afdebbf`'de kırmızı: kısmi başta `(True, False) !=
  (True, True)` (yeniden koşu üretmiyor sayılıyordu), `ValueError: correct_exit is part of the symptom expect_exit`
  (ayırt edilebilen dürüst yeniden üretici), `KeyError: 'observed'` (çıkış), değişmeden gönderilen iddiada
  `rewritten` `True`, protokol cümlesi yok, pilot `reproduced` `1 != 0`. E07'nin (c) testi yeni kurala yazıldı;
  doğrulayıcıdan geçen eski test yeniden üreticilerine `correct_*` eklendi.
- **Mutantlar.** E260'ın 23'ü: `open_claim_proven_on_a_later_head`, `open_claim_observation_dropped`,
  `observation_without_its_head`, `correct_side_not_required`, `correct_side_inside_the_symptom_accepted`,
  `symptom_inside_the_correct_side_accepted`, `correct_side_on_another_observable_accepted`,
  `side_holds_on_any_one_field`, `correct_side_not_in_the_schema`, `rival_not_told_the_polarity`,
  `rival_told_a_later_show_proves`, `correct_side_ignored_at_run_time`, `own_head_proof_ignores_the_correct_side`,
  `proven_defect_cleared_by_its_correct_side`, `contradicted_symptom_not_reproduced`,
  `control_skipped_when_the_head_contradicts`, `exit_hides_what_open_claims_showed`,
  `unchanged_resend_spends_the_rewrite`, `rival_told_a_spent_rewrite_bars_the_resend`,
  `reproducer_key_includes_the_correct_side`, `state_refuses_the_correct_side`, `pilot_counts_contradicted_runs`,
  `pilot_counts_claim_observations`. Çapası yenilenen: `protocol_without_the_contract`,
  `stderr_expectation_ignored` (kural `rival.side_holds`'a taşındı), `claim_rewritten_twice`;
  `tautology_not_checked` temeldeki çapasına döndü.
- **Doğrulama.** İlk sürüm: Windows 407 test OK (18 atlandı; aynı makinede temel 22de0c6: 398); Linux 425 OK
  (3 atlandı); 140/140 mutant öldü. Yeni testler temel kodda 9'dan 8'i kırmızı; yeşil kalan, iki taraflı
  kanıtlanmış kusurun düzeltmede kapanmasını koruyan E08 testidir. Şüpheci turundan sonra (`80d710e`): Windows 412
  test OK (18 atlandı); Linux (`snowball_linux_test:git`, ağsız, `git archive` kopyası) 430 OK (3 atlandı).
  `decide`, `reproduce`, `rival`, `rival_mcp` ve `state`'in bütün mutantları, durum yeniden üreticilerini bağlayan
  `cli` ve iş akışı mutantları ve `launch`'ın pilot satırı mutantlarıyla: 152/152 öldü (altı kapsayıcı, her birinde
  önce yeşil baz koşu); E260'ın 23'ünün her biri bu satırın testlerinden biriyle. 264 mutant çapasının her biri
  tam bir kez eşleşir. Şüphecinin kendi mutantlarından üçü öldü; `SK_persistence_keeps_a_contradicted_symptom`
  yaşar ve yaşaması beklenir: E08'in ret satırı önce gelir, belirtiyi gösteren her baş reddedilir ve kapanış satırına
  ulaşmaz; mutant yalnız yeniden koşusu totolojik (belirti boş ağaçta da görünür) bir kabul başında farklıdır, o da
  E260'ın değiştirmediği E09 kuralıdır. Şüphecinin hedeflediği davranış (doğru metin kanıtlanmış kusuru kapatır)
  `proven_defect_cleared_by_its_correct_side` ve `contradicted_symptom_not_reproduced` ile ölçülür, ikisi de ölür.
- **Açık kalan.** Canlı hakem bu kod aktarılana kadar eski kuralla çalışır; `29`'un hash'i değişti, beynin kopyası
  için tohum dönemi gerekir. Rakibin incelediği başın kendi gözlemini görmesi durum yeniden üreticilerinin rakipten
  önce koşmasını ister: `yeniden` rakibin kararına bağlı, sırrı tutan `cagir` beyin kodu koşturamaz; bu bir iş akışı
  yeniden düzenlemesidir, bu satırın işi değildir. Ortak bir akışta olup kusurlu başta da görünen doğru taraf
  (`correct_stdout_contains: "done"` gibi) koşmadan ayırt edilemez: kendi başında kanıtı düşürür, sonraki rakip
  `contradicted: true` gözlemini görür. Kurucu'nun f97 isteği (vektör fikstürleri klonda) bu satırın işi değildir.

### E244 (2026-10-30) · kapsülde vektör girdileri · dal `gaps/fixtures-in-capsule`

- **Ne oldu.** Kurucu f97'de `29f`–`29j`'nin çapa saydığı fikstürleri göremediğini bildirdi; bir kez göremediği bir
  fikstüre uymak için açık geçen bir istisna yazdı. Hakem fikstürleri yalnız kendi kapsayıcılarına bağlıyordu
  (`fixtures`, `/vec`); Kurucu'nun kapsülünde `/vec` yoktu.
- **Karar (ajan tartışması).** Girdi evet, cevap asla. `vectors.founder_inputs` (`fixtures`'ın yanında, tek kaynak):
  `fixtures`'ın dosyaları, artı `cases.json`, her veri vakasının adlandırılmış alanları (`id`, `purpose`, `cmd`,
  `stdin`, `fixture`, `changed.{description, cmd, stdin, fixture}`); `expect` ve `expect_not` hiçbir derinlikte yok.
  Hakemin kapsayıcıları `fixtures`'ı değişmeden kullanır. Başlatıcı her oturumdan önce
  `gh api repos/<hakem>/tarball/main`'i indirir, yalnız `vectors/` üyelerini `filter="data"` ile açar, `<work>/vec`'i
  aynı fonksiyonla (kopya değil, `assertIs`) kurar ve `/vec`'e salt okunur bağlar; her vakanın `cmd`'si orada olduğu
  gibi koşar. İndirme ya da kurma başarısızsa oturum açılmaz, başlatıcı durur. Prompt: girdiler `/vec`'te, beklenen
  değer yok; sayfasıyla çelişen vektör kırmızı kalır ve operatör tohum dönemiyle yanıt verene kadar kabulü engeller,
  Kurucu onu kanıtıyla `seed_issue` olarak yazar, etrafından dolaşmaz; girdiyi özel durum yapmak gizlemedir (rakip
  çürütür); hakem reposu ve `snowball-mcp` okuma yasağı sürer. `seed_issue` bir vektörü kenara koymaz: öyle bir
  mekanizma yok, prompt da öyle demez. `29d`'ye `/vec` beyin testleri için yol olarak eklenmedi; `vectors.json`
  değişmedi.
- **Fikstürde cevap.** Cevap biçimli değer `answer_atoms`'dur (içerik adresi, yola bağlı neden, git ya da sha256
  hash'i; sayfa testi de aynı kuralı okur). Vakanın kendi girdisi (argv, stdin, fikstürleri, değişmiş girdisi dahil)
  taşıyorsa yankıdır (tarifin imajı, defter satırının uç hash'i: tohumda 20 değer); taşımıyorsa kodun hesaplaması
  gerekir (52 değer) ve hiçbir fikstürde olmamalıdır. Tohumda yok; olursa `founder_inputs` hiçbir şey yazmadan reddeder.
- **Kabul edilen risk.** Kurucu artık her vakanın girdisini görür: vektörler bir uygulamayı, bu girdileri tanıyıp
  cevabını döndüren bir arama tablosundan ayıramaz. Beklenen değerler görünmez, ama Kurucu kendi kodunu `/vec`'te
  koşturup çıktıyı sabitleyebilir; `chain`'in hash vektörlerinin satırları da beklenen hash'leriyle
  `chain/good.jsonl`'dadır (geçerli zincir hash'ini taşır; Kurucu'nun kodu bunu önceden de `/vec`'ten okuyabilirdi).
  Mekanik engel yok. Engeller: rakibin taze girdilerle çürütmeleri (özel durumlanmış girdi başka girdide düşer) ve
  prompt. Ölçü: rakibin özel durumlanmış bir girdiyi (bir `/vec` yolu, bir vaka kimliği, bir fikstürün içeriği)
  adlandıran çürütmeleri, pilot değerlendirmesinde (`docs/pilot-gunlugu.md`) sayılır; otomatik sayaç yok.
- **Kanıt (önce kırmızı).** Yeni ve değişen 10 test değiştirilmemiş kodda kırmızıydı: bağ yok (`0 != 1`, bağların
  sözlüğünde `/vec` yok), `founder_inputs`, `referee_vectors`, `refresh_inputs` ve `answer_atoms` yok
  (`AttributeError`), döngü `(['session'], True) != (['refresh', 'session'], True)`, prompt cümlesi yok.
- **Mutantlar.** Yeni 5: `capsule_inputs_not_mounted`, `capsule_inputs_writable`, `projection_leaks_expect`,
  `whole_referee_repo`, `fixture_answer_check_off`; `expected_values_mounted` öldürülmeye devam eder.
- **Doğrulama.** Windows: temel (`a7f3283`) 416 test OK (18 atlandı); dal 424 OK (18 atlandı). Döngüyü koşturan
  sahte pilotlar (`test_founder_capsule`, `test_reproducer_polarity`) `refresh_inputs`'u ezer, yoksa gerçek `gh`'ye
  giderlerdi. Mutantlar Windows'ta (`mutate.py`'nin `MUTANTS` ve `run_mutant`'ı, Windows ortamıyla; ilgili altı test
  modülü, önce yeşil baz): 5 yeni, `expected_values_mounted`, `run_tests_mounts_the_seed`,
  `reproduce_mounts_the_seed`, `new_vector_page_shows_a_hash` (sayfa testi artık `answer_atoms`'u okur) ve
  `launch.py`'nin 10 mutantı: 19/19 öldü. 284 çapanın her biri tam bir kez eşleşir. Linux ve bütün mutantlar
  koşulmadı (CI'nin `main` işi).
- **Açık kalan.** Canlı pilot bu dal birleştirilip başlatıcı yeniden başlatılana (imaj prompt'la yeniden kurulana)
  kadar `/vec`'siz koşar. Hakem reposundan gerçek tarball indirmesi denenmedi (pilotun reposuna dokunulmadı); test
  GitHub biçiminde bir tarball'la koşar.

### E246 (2026-10-30) · silme kuralı ve her zaman geri dönüş · dal `gaps/wip-and-data-guardrails`

- **Sahibin kararları (2026-10-30, bağlayıcı; özet).** Bir kullanıcı işe yaramayan bir şeye başlayıp duraklatmış
  olabilir, Snowball onu silmemeli; gerçekten aynı işi yapan parçaları mimari olarak birleştirip artıkları silebilir,
  ama biri bir şey geliştiriyorsa o silinmemeli. Ve sahibin kendi sözüyle "her zaman geri dönüş imkânı olmalı":
  önerilen her değişiklik, en başta silme, geri alınabilir olmalı; geri dönüşü olmayan bir istisna yok, sahibin
  onayıyla da. Sahip en profesyonel uygulamayı istedi: şirket hiçbir zaman veri kaybetmemeli.
- **Çelişki (spec, `main`'de).** `tohum/01:50` "ölü kod sıfır"; `03:16` K2 "Ölü kod, kullanılmayan export, koşmayan
  test hedefi", oracle araç; `18a:44` `gross_delete_cap` K2 silmelerini muaf tutuyordu; `07:18-21` ve `24:27`
  tabandaki her ihlal bulgu, mandal; `18a:22` K2 tabanı kural sayımında sıfır kaçırma; `18b:27` K2 `remove`; `10:42`,
  `10:54` K0–K2'de yargıç araç, panel yok, niyet savunması yalnız panelde (`04a:43-45`, `10a:28`); `31e:16-17`,
  `31e:24` ("çağıran sayısı sıfır → kaldır (Y4)"), `31g:58-59`, `31h:49` kaldırmayı sürüyordu. Y4 (`00:42-45`)
  sistemin kendi mekanizmalarıdır ama kapsamını söylemiyordu; `31e:24` onu hedefin koduna uyguluyordu.
  `asama-1/13b:18` (`dead-code`) "Üretim yolunda çağıranı olmayan kod yoktur" diyordu. Hiçbir kural bir K2 adayının
  modülü kendi testleriyle birlikte silmesini engellemiyordu; 72 saatlik pencere (`18a:31`) ve kırmızı test tetiği
  (`07:26-28`) kimsenin bakmadığı işi geri getirmez. Kopyanın `koş` ağacında `.git` yok (`24:24`): yakınlık yalnız
  `çek`te görünür.
- **Hedef (salt okunur, yalnız sayılar ve biçimler).** 6.621 üretim kaynağının 881'inin importeri yok (319 glob'la
  yüklenen migration, 180 giriş noktası ya da barrel, 132 betik, 67 araç yapılandırması, 5 çerçevenin bulduğu, 178
  diğer). Yalnız testlerin import ettiği, kurulmuş ve sınanmış ama bağlanmamış 61 dosya (27 klasör; 41 ön uç, 18 servis,
  2 kütüphane): son commit'i 27'sinde 30 gün içinde, 16'sında 31–90, 9'unda 91–180 gün, 9'unda daha eski. Hiçbir
  yerde anılmayan 44 kesin yetim: 4 / 7 / 9 / 24 (çoğu artık biçiminde, ama 11'i 90 gün içinde değişmiş). Bazı
  birimler import'la değil yalnız yapılandırmadaki ya da dokümandaki yolla anılıyor (aralarında dağıtılan servisler
  ve çalışma zamanında yüklenen ön uç modülleri): yalnız import'a bakan geçiş onları ölü okur. Bir serviste aynı
  yeteneğin bağlanmamış 3 alternatif uygulaması var: import tek başına artığı alternatif arayışından ayıramaz.
  Kaynak: operatörün klonu (sığ, 4 commit) ve dosya başına salt okunur GitHub API çağrıları; E78 orijinalin 90 günde
  ~4.817 commit aldığını yazar.
- **Araştırma (sıralı uygulama).** (1) Doğrulanmış geri yükleme: yedek, PITR, prova, RPO/RTO [Google SRE veri
  bütünlüğü; GitLab 2017 olay raporu; AWS Well-Architected; NIST SP 800-53; CISA]. (2) Genişlet-daralt, yıkıcı adım
  ayrı ve sonraki değişiklikte [Fowler ParallelChange ve evodb; Stripe çevrimiçi migration; GitLab; strong_migrations].
  (3) Yumuşak silme, pencere, sonra ayrı kalıcı silme [Google AIP-164; Google Cloud silme; Meta veri kaldırma].
  (4) Yıkıcı değişikliğin mekanik sınıflaması ve son commit'e bağlı, kalıcı kayıtlı ikinci kişi onayı [Atlas lint;
  strong_migrations; GitHub korumalı dallar; Google SRS bölüm 5]. (5) Geri alınabilir migration ve bildirilmiş geri
  alınamazlık [Rails `IrreversibleMigration`; Flyway undo]. (6) Üretime benzer kopyada prova [GitLab migration
  boru hattı]. (7) Sürümleme ve kullanımdan kaldırma penceresi [AIP-180; GraphQL `@deprecated`; RFC 9745, 8594;
  Confluent şema uyumluluğu; Pact `can-i-deploy`]. (8) Bayraklı kaldırma [Fowler feature toggles]. (9) Kod silmede
  çalışma zamanı kanıtı ve sahibe bildirim [Google Sensenmann; Meta SCARF]. (10) Denetim izi. Ana bulgular: geri
  migration şemayı geri getirir, kayıtları getirmez; "referans yok" terk edilmiş demek değildir. Tohuma bunların
  yalnız kısıtı girdi (önce arşiv, denenmiş yedek, kayıtlı onay); pencereler, kullanımdan kaldırma işareti ve
  birleştirme sırası sistemin tasarımıdır.
- **Karar ve yer.** Geri dönüş yasası bir kez, Y2'de (`00:32-34`): sistemin önerdiği her değişikliğin, en başta
  silmenin, geri dönüş yolu adımdan önce kanıtlanmıştır ve hiçbir sistem adımı onu sonradan kapatmaz; istisnası yok,
  sahibin onayı da açmaz. Y4 (`00:42-45`) artık kapsamını söyler: sistemin kendisi. `07a` (yeni, 54 satır) hedefin
  kodu, dokümanı ve verisi için tek kaynak: geri dönüşün biçimi (`07a:16-20`; kodda ve dokümanda merge'ün geri
  alınması, geçmiş yeniden yazılmadığı için kapanmaz; veride arşiv ve yedek; geri migration geri dönüş değildir);
  kullanılmıyor olmak ölü olmak değildir ve hangi sınıftan gelirse gelsin bir birimi kaldıran değişiklik silmedir
  (`07a:22-25`); yarım ya da duraklatılmış iş silinmez, onu anlatan plan ve tasarım dokümanı işin parçasıdır, kanıt
  yükü silendedir (1); gerçekten aynı işi yapan parçalar yürütmeyle kanıtlanıp birleştirilir, kaldırılan kopya için
  1'in kanıtı da gerekir, geliştirilen bir uygulama kopya sayılmaz (2); eskimiş artık yalnız sahibin onayladığı
  adayla (3); emin olunamıyorsa tutulur (4); silme adayı her birimin 2 ya da 3'ten hangisiyle silindiğini taşır
  (`07a:37`). Sahibin onayı adayın son hâline bağlı, kalıcı kayıttır; onay beklenmez (Y8), aday sahibe bırakılır ve
  döngü sürer (`07a:39-41`; `30:43`'teki "sahip düzeltir" deseni). Veriyi yok eden adım (`07a:43-51`) sahibin
  onayını, daha önceki ayrı bir adımda arşiv ya da yumuşak silmeyi ve adımı kapsayan, geri yüklemesi denenmiş,
  saklama süresi sınırsız yedeği taşır (sistem yedeği göremez, aday önkoşul olarak adlandırır, sahip doğrular;
  yedeğe yalnız sahip, sistemin dışında son verebilir). Bağlananlar: `01:50`, `03:16`, `10:54` (araç bulguya, `07a`
  silmeye karar verir), `15:56` (doküman düzeltmesi de silme kurallarına uyar), `18a:44` (K2 istisnası kalktı;
  Y11 gereği yalnız sıkılaşma), `31e:16-18`, `31e:21`, `31e:24`, `31g:59`, `31g:68`, `31h:22`, `31h:49`. Tohum
  mekanizma vermez: yarım işi artıktan ayırmanın, kullanımı ölçmenin ve onay kaydının yolu sistemin.
- **Aşama spec'i.** Tohum teslimi `spec/asama-*`'yı taşımaz (E180) ve tohumla gelen Aşama 0 ve 1 spec'i Kurucu'nun
  ilk taslağıdır (`02:11-15`). `02:14-15` artık genel kuralı söyler: aşama spec'i tohumla çelişirse tohum geçerlidir,
  çelişki bir spec kusurudur (donmamışta Kurucu düzeltir, donmuşta bildirir). Tohumun kendi kopyası `asama-1/13b:18`
  düzeltildi (`dead-code`: çağıranı olmayan her birim bildirilir, silinmesi `07a`'ya uyar; `asama-1/CHANGELOG`).
  Canlı beyindeki kopya tutuldu: Kurucu'nun `02`'nin kuralıyla kendisinin bulup bulmadığı ölçülür.
- **Açık kalan.** Canlı hakemin anayasal `policy.json`'unda `gross_delete_cap` operatörün işidir. Beyne teslim bu dal
  birleştirildikten sonra tohum dönemiyle.

### E247 (2026-10-30) · veri katmanı korkulukları · dal `gaps/wip-and-data-guardrails`

- **Soru ve onay.** Sahip: Snowball veritabanı, arka uç, ön uç ve aralarındaki iletişimde (yaratma, okuma, güncelleme,
  silme) nasıl davranır? Operatör kanıtla sınanmak üzere beş korkuluk önerdi; sahip 2026-10-30'da hepsini onayladı
  ("önerilerini de uygula"). Tohuma kısıt girdi (ne tutmalı, kim onaylar); mekanizma sistemin.
- **Hedef (salt okunur, yalnız sayılar ve biçimler).** Depolar: Postgres (zaman serisi eklentili), Redis, NATS, bir
  MQTT aracısı, S3 uyumlu nesne deposu. Tek sınıf tabanlı ORM migration çerçevesi: 15 hizmet alanında 18 klasörde
  ~465 migration sınıfı ve bir merkezî SQL klasörü; 52 `.sql`; kiracı başına şema biçimi; ~453'ü bir down adımı
  bildirir (gerçekten geri alıp almadığı denetlenmedi); bazı yapılandırma migration'ları açılışta koşar. Bazı test
  dışı yapılandırmalar ORM şema eşitlemesini açar: orada varlık düzenlemesi veritabanı şemasını değiştirir.
  Kod-önce GraphQL (federasyonlu alt grafikler ve bir geçit), 115 çözücü dosyası, ~1.494 Query/Mutation/Subscription
  süsleyicisi: çözücü ya da tip düzenlemesi API sözleşmesi düzenlemesidir, veritabanı şeması değil. REST: 111
  denetleyici, 565 yol süsleyicisi, 146 DTO dosyası. Ön uç: 147 dosyada ~1.094 GraphQL işlem dizesi, 90 dosya
  üretilmiş tipleri import eder. Olaylar: 140 işleyici, 124 dosyada ~137 NATS ve 96 MQTT konu dizesi, yalnız 10 olay
  şeması. Yazarlar (sezgisel): 30 kod taşıyan servis ya da crate'in 9'u iki ya da daha çok depo türüne yazar; 23
  tablo adı birden çok serviste varlık, 27 şema nitelikli tablo birden çok alanın migration'larında yaratılır: "sıfır
  ikinci yazar" bugün yanlış, "yeni ikinci yazar yok" tutabilir. 11 test dosyası veritabanını migration'lardan ya da
  kapsayıcıdan kurar: desen sistemce bulunabilir.
- **Beşinin yeri (bu dal; satırlar bu dalın sayfalarındadır).** Beşi de kapalı geçer: kapının gösteremediği şey
  yasaklanan sayılır.
  1. *Gerçek veri yok, test veritabanı yalnız kum havuzunda migration'lardan.* Y3 `00:36-40`: "gerçek veri yok";
     hedefin verisine yalnız `koş`ta, migration'larından kurulmuş, gerçek kayıtsız test kopyasında dokunulur;
     kopyayı kuran migration koşusu yasağa girmez (E77'nin kararı artık yasada). Ağsızlık aynen: Y10 `00:71-75`,
     `08:25-27`. Onaylayan: yasa; kimse açamaz.
  2. *Yıkıcı DB değişikliği sahibin onayı ve geri dönüş kanıtıyla.* Y3 `00:36-37`: migration yok (`main`'deki gibi;
     veriyi geri doldurma da dahil) ve veritabanı şemasını değiştiren kod yok; "şema" orada veritabanı şemasıdır, API
     şeması `23`'tedir. Kapı migration'ları her sınıfta reddeder (`01b:18`), veritabanı şemasının türetildiği tanıma
     dokunanı şemanın değişmediğini kanıtlamadıkça (`01b:22-23`). Kalıcı veriyi silen, üzerine yazan ya da bilgi
     kaybettiren bir yolu ekleyen ya da genişleten değişiklik hangi dosyada olursa olsun güvenlik yoludur; eklemediği
     ve genişletmediği gösterilemeyen değişiklik de: K6'ya kadar `blocked`, sonra K6 kapısı ve `07a`'nın veri
     şartları (`05:36-40`, `07a:43-51`: sahibin kayıtlı onayı, önce arşiv ya da yumuşak silme, süresiz denenmiş
     yedek). Onaylayan: sahip, geri dönüş kanıtıyla; onay beklenmez (Y8).
  3. *Sözleşme iki uçta, kırıcı değişiklik sürümsüz yok.* `23:50-55`: her uç kapsam kuralıyla aynı değişiklikte
     güncellenir ve sözleşme testiyle yeşildir; ayrı dağıtılan bir tüketiciyi kıran değişiklik yapılmaz, kırıcı biçim
     yalnız sürümle eskinin yanına gelir; kanıtlanamayan kırıcı, tüketicisizliği kanıtlanamayan sözleşme tüketicili
     sayılır. Eskinin kaldırılması bir silmedir (`07a`: uç bir birimdir, 1–4). Onaylayan: kapı; artık silmede sahip.
  4. *CRUD davranışı önce ve sonra testle.* `05:23-28`: birim silen, veri yolu ya da sözleşme ucu içeren değişiklikte
     testsiz kenar her sınıfta `blocked` (`main`'de silme K2'den, öteki her şey K5'ten); bunları içermediği
     gösterilemeyen değişiklik içeriyor sayılır; kenarın testleri yetki, kiracı yalıtımı ve idempotency dahil,
     düzeltilen davranışınki dışındakiler tabanda ve adayda yeşil; kum havuzunda koşamayan test test sayılmaz.
     Dayanaklar aynen: Y8 `00:62-66`, kapının yeniden koşusu `01b:45-48`, nöbetçi `07`, `guarded` test `30d:41-43`,
     çapraz kiracı matrisi `30b:9-16`. Onaylayan: kapı.
  5. *Tablo ya da konu başına ikinci yazar yok.* `07:21-24`: yazar mandalı; yazar `31:60`'ın tanımıyla modüldür;
     yazarı olan tabloya ya da konuya yeni yazar eklenmez, mevcut ikinci yazarlar borçtur ve yalnız azalır; kapı yeni
     yazar eklemediğini gösteremediği adayı geçirmez. Amaç (`01:50` "her gerçeğin tek sahibi") ve katalog (`31a`,
     `31g`) danışma olarak aynen; yazar taşımak göçse sahibin. Onaylayan: kapı.
- **Şüpheci turu (2026-10-30).** Taslağı 12 kırıkla çürüttü; hepsi kökünde kapandı: (a) "şema" nitelenmemişti, API
  şemasıyla çakışıyordu → Y3 ve `01b` "veritabanı şeması" der; (b) taslak "migration yok"u sessizce gevşetiyordu ve
  `30:43`, `31e:11`, `31g:11-12` Y3'e bayat atıf yapıyordu → "migration yok" aynen geri geldi, atıflar yeniden doğru;
  (c) veriyi yok eden yol yalnız yolla denetleniyordu → kapalı geçen cümle (`05:39-40`); (d) yazar mandalı açık
  geçiyordu ve yazarın boyu tanımsızdı → kapalı geçer, yazar `31`'in modülü; (e) K0 ve K1 korkuluk 4'ten muaftı →
  her sınıf; (f) geri dönüşün ömrü yoktu → Y2 "hiçbir sistem adımı sonradan kapatmaz", yedek süresiz; (g) hedefin
  dokümanı silme kuralının dışındaydı → `07a` kapsamı ve `15:56`; (h) `asama-1/13b:18` çelişiyordu ve tohum
  önceliği yazılı değildi → `02:14-15`, tohumun kopyası düzeltildi; (i) kural 2 geliştirilen bir yeniden yazımın
  silinmesine açıktı → kaldırılan kopya için 1'in kanıtı; (j) aynı kural birden çok yerdeydi (şema yasağı `05` ve
  `07a`'da, silme tavanı `07a`'da, Y4'ün kapsamı `07a` ve `31e`'de, geri dönüş `07a`'da) → her biri tek yerde,
  Y4'ün kapsamı Y4'te; (k) `07a` mekanizma veriyordu (birleştirme sırası, ayrı adımlar ve pencere, tarihli işaret,
  uyumluluk çıktısı) → çıkarıldı, sahibin istediği kısıt kaldı; (l) `31h:22` ve `31e:18` bağlanmamıştı → `07a`.
- **Açık kalan.** Mekanizmalar sistemin: şemanın değişmediğinin kanıtı, veriyi yok eden yolun ve veri yolunun
  tanınması, yazar haritası (harita katmanı b, `13`), sözleşme testleri ve kırıcılık denetimi, kum havuzunda
  migration'lardan test veritabanı (servis isteyen birim sonraki partide, `08:33-34`). Bugün yürütülemeyen kural
  `blocked` üretir (Y8); tohum bunların biçimini vermez.
- **Doğrulama (iki satır için).** Sayfalar ≤ 80 satır (`00` 80, `07a` 54); yasaklı ifade yok; hedefe özgü ad yok.
  Windows: `seed/bootstrap` `python -m unittest discover -s tests` 426 test OK (18 atlandı), son commit'in ağacında;
  bu dal test ya da kod değiştirmez, spec'i okuyan testler (`test_wiring`, `test_units`, `test_seed_epoch`) yeşil.
  Linux ve mutantlar koşulmadı (yalnız spec ve kayıt değişti).

### E161, MF14–MF18 (2026-10-30) · `revert_drill`, `prompt`, `status`, `genesis` · E161 kapandı · E270–E276 açıldı
- **Veri.** `vectors.json`'a dört veri grubu, 24 vaka (48 sonuç), iş akışının uzlaştırdığı vakalar olduğu gibi: komut,
  stdin ve beklenen değerler değiştirilmedi, düşen ya da kodlanamayan vaka yok. Vaka metinleri, komutlar, stdin ve
  fikstür baytları iş akışının şüpheci sonrası sözleşme dökümünden, beklenen değerler aktarılan metinden harfi
  harfine alındı; betik her vakanın karşılaştırılan alanlarının `expect`'in anahtarları olduğunu ve her fikstürün bir
  komutun `/vec/` yolu olduğunu denetledi. Aktarılan metinden tek fark `prompt.secret_never_sent`'tedir: metin JSON
  kaçışını çözülmüş gösteriyordu; vakanın seçimi altı karakterlik `p` (değişmişinde `q`) ister, öyle girdi
  (`append.refuse_secret_row` gibi; ham `vectors.json` sır biçimi taşımaz). 34 fikstür `vectors/<grup>/` altında,
  satır sonu dönüşümsüz (`.gitattributes`: defterler zincir, blok ve dosya baytları hash'lenir). Her grup arayüz
  sayfasını adlandırır (`29m`: `revert_drill`, `prompt`; `29n`: `status`, `genesis`) ve sayfa Kurucu'nun tohumunda
  yoksa koşmaz (`test_mf14_to_mf18_groups_wait_for_their_pages`). Tablo güdümlü zamanlama aynen; bitmiş hiçbir MF
  artık `vector_group_missing` uyarmaz, tohumdan düşen grup yine adlandırılır
  (`test_a_group_the_seed_has_no_vectors_for_is_named_not_invented`). Hiçbir fikstür vakasının hesaplaması gereken
  cevabı taşımaz (`founder_inputs` reddetmedi, `test_the_inputs_are_every_data_case_with_no_expected_value_at_any_depth`).
- **Arayüz.** `29m` (80 satır) ve `29n` (74); 80 satır sınırı (`tohum/15` 1) ikiye böldü. Komutlar, girdi biçimi,
  taklitler (sahte prova tohumu ve katalog; kayıtlı GitHub REST'i; `plan` hiçbir modeli, taklit `claude`'u da
  çağırmaz), karşılaştırılan alanlar, çıkış kodları, her vakanın amacı ve spec'in sessiz kaldığı yerde "seçim";
  beklenen değer yok. `29d`'de yalnız dört grubun satırı sayfasını gösterir; `INDEX.md`'ye iki satır, `00b` ve
  `docs/ana-taslak.md`'ye iki sayfa. `29f`–`29j`, `asama-*` ve paralel partilerin sayfalarına dokunulmadı.
  `VectorInterfacePagesTest` yedi sayfayı denetler.
- **Kanıt.** A'nın modülleri (`harness/revert_drill.py`, `dispatcher/llm_call.py`, `status/block.py`, `activate.py`,
  ortak `ledger/_common.py`) `local/reference_brain/referee/` altında; beyin onları bitmiş bildirmez (`done_mf` [1]).
  İki uyarlama, dosyalarında yazılı: A'nın `ledger/chain.py`'si `ledger/_common.py` adıyla (beynin MF1'i değişmedi);
  MF15 A'nın yalnız prompt kuralını taşıyan `gate/secrets.py`'si yerine bu beynin MF2'sini (`scan_text`) çağırır.
  `SeedVectorsOnReferenceImplementationsTest`: on altı veri grubu A'da 252/252 (MF14–MF18 48/48), `chain` 6/6. 61
  yeni kırık (`revert_drill` 15, biri A'nın ortak zincir doğrulamasında ve `genesis`'i de düşürür; `prompt` 13;
  `status` 12; `genesis` 21) ve `prompt.secret_never_sent`'i de düşüren MF2 kırığı (`github_format_missing`: MF15
  MF2'nin kuralıyla tarar): dosya sırası, yer değiştirmiş HMAC, son bayt ya da ilk 64 bit, düz sha256, kanonik
  olmayan anahtar, yok sayılan tohum, denetlenmeyen neden, taahhüt ya da örnek, dosyanın herhangi bir yerindeki
  taahhüt, tek neden, herhangi bir geri alma, doğrulanmayan zincir; ham ya da alan alan yerleştirme, şablonun hash'i,
  `min`'in tek terimi, kayan nokta USD, reddedilen ya da bildirilmeyen düşen alan, tamsayı sayılan boolean, taranmayan
  prompt, gönderilmeyene tavan, sınırda ya da bir mikroda fren; ilk devir ya da başlangıç, herhangi bir `events`
  satırının kararı, son `cost` satırı, sabit dokunuş, işaretli, son LF'siz, dosya sonuna uzanan ya da bütün dosyanın
  hash'i, görülmeyen ya da silinmede görülmeyen düzenleme, tavanı aşınca fren; özetten oyuncak tabanı, kayan `main`'i
  hata sayan, kopyanın `main`'i, olgu dışında Actions, kaydın tamamı, kanonik politika ya da özet, sabit politika
  hash'i, LF'li imports satırı, ilk imports satırı, ilk tohum dönemi, ilk güvenlik satırı, tarifin baytları ya da dosya
  sırası, denetlenmeyen Actions, App kapsamı, kurallar, kontrolün App'i, tek neden, doğrulanmayan güvenlik defteri.
  Her kırık hedeflediği her sonucu kırmızıya çevirir, çökerek değil cevap vererek; 24 vakanın her biri en az bir
  kırığın hedefi. Gerçek kumda (pinli python imajı, ağsız, salt okunur kaynak, `/vec`'te yalnız fikstürler,
  `DockerRunner`'ın argv'si; kapsayıcılar `snowball_wf5_*`) A 48/48 yeşil. İş akışının B'si (repoda değil, E274)
  değiştirilmeden gerçek veri koşucusunda (yerel koşucu) 48/48; bu, oturumun kaydıdır. `mutate.py`: 8 yeni mutant
  (MF16'nın beklenen değeri ve fikstürü, MF18'in fikstürü kayar; `prompt`'un sahte belirteci düz yazılır; sayfadan
  vaka düşer; `29n` dizinde yok; `29n` bir hash gösterir; `prompt` grubu sayfasını adlandırmaz), çapası daraltılan 1
  (`seed_secret_written_plain`: kaçış artık iki vakada), açıklaması güncellenen 1 (`data_groups_have_no_judge`).
- **Bütçe (E199 b).** Bütün MF'ler bitince push başına 258 vektör çağrısı (veri 252, `chain` 6). Yeni 48 çağrı gerçek
  kumda 6,5–11,7 s (ortalama 8,1 s; Windows Docker Desktop, başka bir oturumun dört kapsayıcısı koşarken): E161'in
  ölçümüyle (ortalama 3,2 s, en kötü 5,0 s) 826 s ile 1290 s, bugünkü yükle 2090 s; `BUDGET_S` 1200 s. E273.
- **Bulgular.** E270 sözleşmenin spec sessizken yaptığı seçimler (sınır); E271 vektörlerin okuduğu satırlar ve genesis
  yükü `26`'da yok, `26`'nın drill yükü taahhüdü açık deftere `instance_id`'yle yazdırır; E272 `status.md`
  düzenlemesine `asama-0`, `15` ve `01b` üç cevap verir; E273 vektör bütçesi bütün gruplarla aşılabilir; E274
  MF14–MF18'in B'si repoda değil; E275 tohumun içe aktarıcısı `26c:37-38`'in satırını yazmaz, gerçek aktarımdan
  sonra genesis kullanılamaz girdiyle durur (denendi); E276 `22a:51`'in "tohumun prova fikstürleri" tohumda yok.
- **Doğrulama.** Windows `seed/bootstrap` `python -m unittest discover -s tests` 429 test OK (18 atlandı); Linux
  (`snowball_linux_test:git`, ağaç `git -c core.autocrlf=false archive` ile, E242) 447 OK (3 atlandı). 8 yeni mutant,
  çapası ya da açıklaması değişen 2 ve dokunulan dosyalara ya da testlere bağlı 16 (`unowned_group_runs`,
  `groups_run_before_their_micro_feature`, `missing_group_not_named`, `interface_page_unchecked`,
  `seed_group_owner_drifts`, `seed_data_group_owner_drifts`, `seed_vector_expect_drifts`, `seed_new_expect_drifts`,
  `seed_new_fixture_drifts`, `vector_page_drops_a_case`, `new_vector_page_drops_a_case`, `new_vector_page_not_indexed`,
  `new_vector_page_shows_a_hash`, `new_vector_page_29j_not_indexed`, `projection_leaks_expect`,
  `fixture_answer_check_off`) Linux'ta, üç kapsayıcıda, her birinde önce yeşil baz koşu: 26/26 öldü. `local/e2e.py` ve
  bütün mutantlar koşulmadı (CI'nin `main` işi).
- **Açık kalan.** E270–E276; E230–E235.

### İnceleme 6 (2026-10-30) · E161 MF14–MF18'in beş bulgusu · `29o` · E277 açıldı
- **Yeniden üretme.** Düzeltilmemiş ağaçta (`73e766d`) gerçek veri koşucusuyla (yerel koşucu, A'nın kopyasında tek
  değişiklik): `status/block.py`'de `statuses[0]` `status` 10/10, `harness/revert_drill.py`'de `commits[0]` ya da
  `plants[0]` `revert_drill` 14/14 yeşil kaldı; `activate.py`'ye `25a:17`'nin bypass olgusu için tek `GET` eklenince
  `genesis` 1/12 (kayıtlı API 404, çıkış 2). Yeni vakalar ve sondaki dokunuş satırı yazılınca eski A ve eski B
  `genesis`'te 2/14 (sayacın aktarım dışı satırında çıkış 2). Bütçe testi eski koşucuda 258 çağrı × 5,0 s = 1290 s > 1200.
- **Bulgu 1 (`genesis` tavandı).** `29o` (`genesis` `29n`'den ayrıldı: ikisi birlikte 80 satıra sığmadı, `tohum/15` 1):
  okumalar `01b:59-60`'ın uçları (`brain/*` ve `main` için `rules/branches`, kuralların geldiği her ruleset'in
  `current_user_can_bypass`'ı) ve oyuncağın `actions/workflows`'u; yeni nedenler `rules_bypassable` (`25a:17`),
  `main_writable` (`25a:18`; `update` kuralı ya da en az bir onaylı inceleme isteyen `pull_request`), `toy_workflows`
  (`25a:20`, `25a:29-30`). Liste kapalı ve öyle yazılı: kayıtlı API okumada tavandır; bu yüzden spec'in genesis'e
  okuttuğu her olgu listededir. `bypass_actors` okunmaz (GitHub REST "Get a repository ruleset" notu: liste yalnız
  ruleset'e yazma erişimi olana döner; yazar App'i `administration:read`). Fikstürler: her `api*.json`'a hedef başına
  `main`'in `rules/branches`'ı, her kurala `ruleset_id` ve üç ruleset kaydı (oyuncağın `main`'i onaylı inceleme,
  kopyanınki `update` kuralıyla), oyuncağa `actions/workflows`; `api_faults.json`'da `main`'in onaysız `pull_request`'i
  ve bir iş akışı (`every_fault_named` altı neden); yeni `api_bypass.json` ve `genesis.bypass_named` (kopya,
  `pull_requests_only` ve `exempt`). Olgu hash'leri sözleşmenin okuma listesinden tohumun `canon`'uyla ayrıca hesaplandı
  ve A'nınkiyle aynı.
- **Bulgu 2 ve 3 (tek satırlı fikstürler).** `status.last_status_row` (`ledger_two.jsonl`: her devrin `status` satırı,
  `status_second.md` 2. devrin bloğu) ve `revert_drill.last_of_several_drills` (`two_drills.jsonl`: iki prova, anahtar
  ikincinin). B'nin `status`'u ve `revert_drill`'i değiştirilmeden ikisinde de beklenen değeri verir.
- **Bulgu 4 (bütçe).** `VectorRun` aynı komut ve stdin'i bir push'ta bir kez sorar (salt okunur ağaç ve `/vec`: aynı
  girdi); cevap vermeyen çağrı hatırlanmaz. Push başına 264 sonuç, 208 kapsayıcı. E273 açık kalır (yüklü makinede aşılır).
- **Bulgu 5 (sessizlik iddiası).** `29n`: `27:19`, `asama-0/12:38-39`, `26c:38`, `27:56`, `25:28`, `25:55` aktarım dışı
  dokunuşları sayaca koyar; `human_touches` sayacın her satırıdır; `29o` genesis'i son aktarım satırına bağlar.
  `imports_three.jsonl`'ın üçüncü satırı ve `genesis/imports.jsonl`'ın son satırı aktarım dışı dokunuştur (yalnız `ts`,
  `stage`, zincir). Satırın biçimi ve yazanı spec'te yok: E277.
- **Kanıt.** A (`activate.py`, beynin `done_mf`'i değişmedi) 264/264 veri ve `chain` sonucu yeşil; B (oturumun
  `wf5/rev6/B`'si: `status`, `revert_drill`, `prompt` değiştirilmeden, `genesis`'e 29 satır, `adapt_b.py`) dört grupta
  54/54. Gerçek kumda (pinli python imajı, ağsız, `/vec`'te yalnız fikstürler, kapsayıcılar `snowball_wf5_*`) A 54/54.
  17 yeni kırık (`revert_drill` 2, `status` 2, `genesis` 13), çapası taşınan 2 (`first_import_row`,
  `import_line_with_its_lf`); her kırık hedeflediği sonucu yanlış cevapla kırmızıya çevirir. `mutate.py`: 15 yeni mutant
  (ikisi incelemenin kendi mutasyonları, inceleme öncesi vektörler ikisinde de yeşildi:
  `reference_status_first_status_row`, `reference_drill_first_commitment`), sayfası `29o`'ya taşınan 1
  (`new_vector_page_29o_shows_a_hash`), çapası değişen 1 (`seed_mf18_fixture_drifts`).
- **Doğrulama.** Windows `seed/bootstrap` `python -m unittest discover -s tests` 431 test OK (18 atlandı); Linux
  (`snowball_linux_test:git`, ağaç `git stash create` ve `git -c core.autocrlf=false archive` ile, E242) 449 OK (3
  atlandı). Değiştirilen dosyalara bağlı 66 mutant (15 yeni, taşınan ya da çapası değişen 2, `vectors.py`,
  `vectors.json`, fikstürler, `29*` sayfaları, `INDEX.md` ve referans beyne bağlı 49) Linux'ta dört kapsayıcıda, her
  birinde önce yeşil baz koşu: 66/66 öldü. Dört `reference_*` mutantını `mutate.py`'de önce bir kırığın çapa sayımı
  yakalar (failfast sırası); her biri veri koşucusunda da vektörü kırmızıya çevirir (2, 1, 12 ve 1 sonuç; oturumun
  `semantic_kill.py`'si). `local/e2e.py` ve bütün mutantlar koşulmadı (CI'nin `main` işi).
- **Açık kalan.** E270–E277; E230–E235. Ayrıca, bu dalın dışında: `github_outage_ends_the_pilot` mutantının çapası
  (`seed/founder/launch.py`) E248'den beri yok.
### Kararlar partisi 1, ana dal üstünde (2026-10-30) · inceleme bulguları · E210 kapandı · E250 E251
- **Taban.** Paket 1'in commit'i (1aac5a7) güncel `main`'e (d8cfb13: MF8–MF13 vektörleri, E241–E244, E260) taşındı.
  Çakışma bu kayıtta (iki tarafın satırları sayı sırasıyla: E205–E208, E210, E230–E244, E250, E251, E260) ve
  `CHANGELOG`'da (iki satır da kalır); `29d` kendiliğinden birleşti (ana dalın `k0map`–`cause` satırları, paketin
  `diffguard` metni). Paket 2 (E173) taşınmadı: `spec/tohum`, `seed/bootstrap/vectors`, `local/` ve `tests/`'te
  `workspaces`, `Nx`, `nx.json`, `project.json`, `inBundle`, iç içe kilit yolu (`node_modules/…/node_modules`,
  `libs/`, `apps/`) ve "çalışma alanı" için `git grep` ana dalla aynı sayıyı verir.
- **E210 (inceleme, yüksek).** `profile.accept_widened` ve iki fikstürü 91239b3^'tekiyle bayt bayt aynı geri geldi
  (sha256 `6d25117a…`, `c2863245…`), `29k` vakayı yazar. Bu ağaçta A ve B: vaka kabul (çıkış 0), değişmiş girdi
  `narrows:security_paths` (çıkış 1); ana dalın A'sı ve B'si de aynı değeri verir, genişletmeye zaten izin
  veriyorlardı (denendi). Vakayı kırmızıya boyayan kırık `widening_rejected` (`14`'ün eski genel okuması: yol
  listesindeki her fark ret), değişmiş girdiyi boyayanlar `security_narrowing_accepted` ve `narrowing_accepted`.
  Yokluğu bağlayan test ve `seed_pins_widening` silindi; mutantlar `seed_widening_case_widens_nothing` (öneri
  türetmeye eşitlenince genel okuma vakadan geçer), `reference_profile_rejects_widening`, `blind_b_rejects_widening`.
  `29d`'nin `profile` satırı "yalnız genişleten öneri kabul" der.
- **E250 (inceleme, orta).** `26c`: işaret olmayan eleman (çıplak ad) isteği kullanılamaz yapar, `deps.fetch` çıkış 2.
  `29g`: çıkış 2'nin listesi okunamayan kilit ya da ayna ve biçimi tutmayan stdin (işaret olmayan eleman dahil); 2'de
  satır `{"ok": false}` (serbest `error`), hiçbir paket getirilmez. A'ya iş akışının A'sının satırları
  (`NAME_AT_VERSION`, kilit yolu eşleşmesi, işaret denetimi), B'ye iş akışının kör B'sinin `_validate_marks`'ı ve
  kilit yolu eşleşmesi geldi; ikisinin E173 kısımları alınmadı. Vakalar `install_script_marked_by_lock_path` (paket
  2'deki vakanın komutu, girdisi ve beklenen değeri) ve `bare_name_refused` (geçerli `snowball-fixture-b@2.0.0`'ın
  yanında çıplak `snowball-fixture-a`; değişmiş girdide `snowball-fixture-a@1.0.0`). Ana dalın A'sı ve B'si iki vakada
  kırmızı (kilit yolu `install_script_unmarked`, çıplak ad `ok: true`), bu ağacınkiler üç vakanın altı sonucunda yeşil
  (denendi). Kırıklar `lock_path_not_a_mark`, `lock_path_read_as_a_directory`, `bare_name_marks_nothing`,
  `bare_name_of_a_locked_package_taken`, `name_version_not_a_mark`; mutantlar `reference_bare_name_marks_nothing`,
  `blind_b_bare_name_marks_nothing`, `reference_lock_path_not_a_mark`, `seed_bare_name_stands_alone`. Paket 2'nin
  (yerel) bu ayrılığı kaydeden satırı bu dalda yoktur, paket taşınırken düşer. Sınır: `ad@sürüm`'ün sürüm biçimi (A
  `X.Y.Z` ister, B her sürümü alır; `@latest` ayrışır), kilitte hiçbir pakete uymayan `ad@sürüm` (ikisi de kabul eder,
  işaretlemez; "vakasız" yanlıştı, E252); vektör çıkış kodunu karşılaştırmaz (`29d`).
- **E195.** Paketin "vakası `k0map` arayüzüyle gelir" notu bu tabanda bayattı: `k0map` (`29h`) başa uygulanma vakası
  olmadan geldi, E230 onu yazılı olmayan kural sayar. Satır buna göre; `diffguard` paragrafı artık `29k`'de.
- **E251.** Sayfalar: `29f` 58, `29g` 60, `29k` 58, `29h` 66, `29i` 66, `29j` 59, `26c` 74, `29d` 50, `14` 65, `01b`
  70 satır. A'nın iki yorumundaki sayfa satırı göndermesi (`gate/check.py` `29k:38-39`, `ledger/_strict.py`
  `29f:21-22`) yeni satırlara. Teslimde `29k` hakemin yeni `vectors.json`'uyla birlikte gitmeli: sayfası beyinde
  olmayan `profile` ve `diffguard` `vector_group_missing` olur (E199 (a)).
- **Doğrulama.** 105 vaka (MF2–MF7 49), 216 sonuç (veri 210, `chain` 6), A'da yeşil; B MF2–MF7'de 98/98. Windows 423
  test OK (18 atlandı); Linux (`snowball_linux_test:git`, çalışma ağacının arşivi) 441 OK (3 atlandı), taban (d8cfb13)
  442, fark silinen test. `local/mutate.py` dört kapsayıcıda (shard 0–3/4): 294/294 mutant öldü. Yeni 11'den A'nın ve
  tohumun mutantları kendi vakasını kırmızıya boyar (A'nın yeşil testi, ya da kırık testinde "stayed green"; ayrıca
  denendi), B'ninkiler B'nin yeşil testiyle, sayfanınkiler sayfa testleriyle öldü.

### Kararlar partisi 1, şüpheci turu (2026-10-30) · E252
- **Bulgu.** Şüpheci 9c0aaac'ı çürüttü: sayfanın yazdığı ama hiçbir vakanın bağlamadığı kurallar (E252'nin satırı).
  Her okuma A'nın bir düzenlemesi olarak koşuldu (şüphecinin `readings.py`'si): önce 210/210 yeşil, şimdi her biri
  kırmızı; yalnız kilit yolunu paket adıyla okuyan okuma yeşil kalır (sınır, E252).
- **Vakalar.** Dokuz yeni vaka ve bir eski vakanın yeni değişmiş girdisi; her beklenen değer A ve B'nin ikisinin de
  verdiği (çıkış kodları da aynı; `x@` ve `@latest` gibi sürüm biçimleri vakaya girmedi, E250). İşaret olmayan
  elemanların değişmiş girdisi aynı: yerine `b`'nin kilit yolu (`b` iki kez işaretli, istek geçer); betiksiz paketi
  işaretleyen değişmiş girdi kalmadı. Yeni fikstürler `prop_units_reordered.json`, `prop_units_added.json`,
  `prop_widen_outside_tree.json`, `prop_widen_outside_tree_drop_excluded.json` (tek satır, `prop_equal.json`'ın
  biçiminde).
- **Kırıklar ve mutantlar.** Yeni kırıklar `narrowed_security_misnamed`, `widening_only_with_tree_files`,
  `unit_candidates_unchecked`, `unit_candidates_may_widen`, `unit_candidates_as_a_set`,
  `unit_candidates_widen_in_order`, `bare_name_outside_the_lock_taken`, `any_at_read_as_name_version`,
  `lock_path_shape_taken`, `root_key_taken`, `name_version_must_name_a_locked_package`; beş eski kırığın listesi yeni
  vakaları da sayar. 20 mutant: A'nın altı ve B'nin üç okuması (yeşil testler), tohumun yedi zayıflatması (kırık
  testinde "stayed green": ör. çıplak ad yine kilitteki paketin, kök `""` geçerli işaretsiz), iki sayfa vakası ve iki
  sayfa uzunluğu (`29`, `CHANGELOG`).
- **Sayfalar.** `26c` 76, `29g` 64, `29k` 62, `29` 79, `CHANGELOG` 77 satır; `29`'da yalnız üç düz yazı paragrafı 118
  sütuna yeniden sarıldı. A'nın `gate/check.py` göndermesi `29k:42-43`, B'nin iki `pathrules.py`'si `14:49-51`.
  E173'ten bir terim girmedi: `spec/tohum` ve `seed/bootstrap`'ta `git grep` ana dalla aynı sayıyı verir.
- **Doğrulama.** 114 vaka (MF2–MF7 58), 234 sonuç (veri 228, `chain` 6), A'da yeşil; B MF2–MF7'de 116/116. Şüphecinin
  `probe2.py`'si: A ve B 20 uç durumun 17'sinde aynı, ayrıştıkları üçü sürüm biçimi (E250). Windows 424 test OK (18
  atlandı); Linux (`snowball_linux_test:git`, çalışma ağacının arşivi) 442 OK (3 atlandı), fark sayfa uzunluğu testi.
  `local/mutate.py` dört kapsayıcıda (shard 0–3/4): 79/79, 79/79, 78/78, 78/78, yani 314/314 mutant öldü; yeni 20'nin
  her biri hedeflediği testle (ayrıca Windows'ta tek tek denendi).
### E162 devamı (2026-10-30) · Aşama 0 çıkışının dört denetimi · dal `gaps/stage0-exit-checks` · E107 kapandı · E280–E287 açıldı
- **Yer ve akış.** Denetimler `pull`'dadır: elde olan arşivi ve son kabul edilmiş commit'in defter blob'unu
  (`gitio.file_at`) okur, Kurucu'nun hiçbir şeyini koşmaz, kapsayıcı yoktur (`29b`; taslak `29e` "Tohum
  denetimleri"). Yeni modüller `ledgercheck.py`, `wiring.py`, `exitchecks.py`; kuralların tek yeri: zincir
  `canon.row_hash`, ağaç hash'i ve operatör adları `treehash` (`RESERVED_TOP`), ajan yapılandırması
  `classify.is_agent_config` (E90'ın her push denetimi aynı yüklemi kullanabilir), `targets[]` `config.load_summary`.
  Spec ve kod push'unda başarısızlık ön nedendir (test ve rakip yok). Çıkışta sonuçlar `meta["exit_checks"]`'e
  `{status: ok|failed|undecided, reasons, why}` olarak gider, testler yine koşar (tek istek eksiğin hepsini duyar);
  `decide` eşler: sonuç yoksa, biçimsizse ya da `undecided`'sa `not_checked:<koşul>` (neden `detail`'de), yokluk hiç
  geçmez; `failed` Kurucu'nundur. Çökme `pull_error` değil, `undecided`'dır. `EXIT_NOT_CHECKED` artık koşul → neden
  (açık satırıyla); `not_checked:` biçimi ve seri imzaları aynı. Durum şeması `snowball-bootstrap-state/3` aynı, taşıma
  yok; yalnız alan eklendi: `exit.checks`, kabulde `exit.toy_tree_sha256`; `meta.exit_checks`, `meta.toy_tree_sha256`.
- **#kurucu-defteri (E107, E280).** Kabul edilmiş defterin baytları başın defterinin önekidir (`truncated`,
  `rewritten`, `deleted`; tamamlanmamış son satır yalnız satır sonuyla kapanır); her satır satır sonuyla biter
  (`unterminated`), UTF-8 JSON nesnesidir (`not_utf8`, `not_json`), yinelenen anahtar, NaN ve 64'ten derin iç içelik yok
  (`duplicate_key`, `noncanonical`, `too_deep`; 100 000 seviye de ret, çökme değil), kanonik biçime sığar, `prev_hash`
  öncekinin `row_hash`'idir (ilki 64 sıfır), `row_hash` tutar, `part: founder`, `kind` test 30'un kümesinde. Neden
  `founder_ledger_invalid:<kural>:L<n>`. Spec ve kod push'u yalnız eklediği satırları (zincir son kabul edilmiş satıra
  bağlı), çıkış bütün dosyayı denetler; çıkışta defter yoksa `missing`. Kabul edilmiş satırdaki bozukluk
  `founder_ledger_accepted_invalid:<kural>:L<n>`: çıkışı kapatır, Kurucu'ya sayılmaz (`NOT_THE_FOUNDERS_EXIT`), çünkü
  eklemek onu değiştiremez; eksik son satır sonu istisnadır (eklemek düzeltir).
- **#is-akisi (E100, E132 (A); E281–E283).** `referee/.github/workflows/`'da yalnız `loop.yml` (`workflow_extra_file`,
  `workflow_missing`); altküme dışı `workflow_unparseable:loop.yml:L<n>:<neden>`; test 46'nın kuralları: üst düzey
  `permissions: {}`, yasaklı üç tetik dizgi, liste ve eşleme biçiminde (harf büyüklüğü fark etmez), tam beş iş ve her
  birinde tam `if: github.ref == 'refs/heads/main'` (`|| true` ret), `run:` içindeki `${{ }}`'de `github` bağlamı yok
  (`${{github.ref}}`, `toJSON(github)`, `GITHUB.` dahil; `env:` üzerinden veri serbest, E17), her `uses:` 40 haneli
  SHA'ya pinli (`@v4`, kısa SHA, `./`, `docker://` ret), her `actions/checkout`'ta `persist-credentials: false`,
  `getir` ve `kos` `permissions: {}` ve sırsız, sır/`id-token`/yazma kapsamı yalnız `cagir` ve `yaz`'da, üst düzey
  `env`'de sır yok, `secrets: inherit`, `toJSON(secrets)`, `secrets[...]` hiçbir yerde yok. Kod push'unda modülü
  `.github/workflows/loop.yml` olan MF (tablodan, MF17) bitince her push'ta, çıkışta her zaman. "İlk adım `control`"
  kuralı tohumun `control` arayüzü yokken denetlenemez: `not_checked:is-akisi` E282 nedeniyle kalır.
- **#agac (E130, E131 (A); E285).** Hakem ağacı hash'i `referee/`'nin tepesindeki operatör adlarını ve `bootstrap`'ı
  casefold ile reddeder (`referee/Policy.json`, `SETUP/`, `ſetup/`, `bootstrap/`); içe aktarma aynı hash'le
  `referee/Control.json`'da operatörün dosyasına dokunmadan durur. Ajan yapılandırması `referee/`'nin her derinliğinde
  ve harf büyüklüğünde `agent_config_in_referee:<yol>`; oyuncak alt ağacının hash'i (`tests/fixtures/toy-repo`) kabulde
  `exit.toy_tree_sha256`, alt ağaç yoksa `toy_tree_missing`; hash'i olmayan "geçti" sonucu `not_checked:agac`'tır.
- **#genellik (E284).** `targets[]` `26c`'nin tam anahtarlarıyla okunur (`identifers` gibi yazım hatası durdurur;
  `base_sha` henüz commit'i olmayan hedefte `null`); ad büyük-küçük harf duyarsız alt dizgi olarak her `referee/`
  yolunda ve UTF-8 okunan her dosyada aranır: `target_name_in_referee:<yol>`, adı taşıyan yol
  `path-sha256:<ilk 16 hane>` ile; `why` hedefi ve adı yalnız sırasıyla adlandırır, ad imzalı sonuca hiç girmez
  (test; şüpheci turunda yanlış çıktı: öbür koşullar aynı yolu açık yazıyordu, E290). `targets[]` yokken ya da bir hedefin `identifiers`'ı boşken `undecided`: `not_checked:genellik`, Kurucu'ya
  sayılmaz (operatörün adımı).
- **#spec ve #durustluk** denetlenmedi: `not_checked:spec` E286, `not_checked:durustluk` E79 ve E287 nedeniyle. Yalnız
  karar verilebilir parçalar (`#kimlik` satırları; "anahtar taahhütle aynı") koşulu tek başına geçiremez, ölü kod
  olurdu.
- **Tablo testi (E185'in devamı).** `asama-0/10` tablosunun her satırı ya kodda denetlenir (satırları `cli`, `decide`,
  `exitchecks`, `ledgercheck`, `wiring`, `treehash`'te tam bir kez durur) ya `EXIT_NOT_CHECKED`'tadır ya ikisi
  (#is-akisi); listedeki her nedenin adlandırdığı kayıt satırı açık olmalıdır (test kaydı okur, mutantların kopyası da
  `docs/eksik-kaydi.md` taşır). `EXIT_CHECKS`'teki her koşulun satırı kodla adlandırılır.
- **Önce kırmızı.** `tests/test_exit_checks.py` (53 test) modüller iskeletken (`NotImplementedError`) ve `cli`/`decide`
  bağlanmadan koşuldu: 53 testin hepsi kırmızı (5 başarısız, 92 hata, alt testlerle); sonra modül modül yeşil.
  `test_decision`'ın tablo testi ve `PullGates` defter testi geçerli satırlarla yenilendi, `test_flow`'un çıkış ve
  içe aktarma testi geçerli defter, `loop.yml`, oyuncak ve `targets[]` ile koşar ve yalnız `EXIT_NOT_CHECKED`'i boşaltır.
- **Canlı kanıt** (beynin salt okunur klonu `ebc999f`, kod koşulmadı; yalnız bu dalın denetimleri veriyi okudu):
  `loop.yml` `wiring.check` → `[]` (beş iş, ilk adımlar `control`); defter 195 satır, zincir sağlam, çıkışta
  `founder_ledger_accepted_invalid:kind:L185`, bir push'ta `[]`; beyinde `tests/fixtures/toy-repo/` yok; özette
  `targets[]` ve `honesty_commitment` yok. Bugün bir çıkış isteği şunlarla kapalı kalır: `toy_tree_missing` (Kurucu'nun),
  f185 (sahibin kararı, E280), `not_checked:genellik` (operatörün `targets[]`'ı, E284, E99), `not_checked:is-akisi`
  (E282), `not_checked:spec` (E286), `not_checked:durustluk` (E287: ekim yapılmadığı için bu pilotta dürüstçe
  geçemez, sahibin kararı). Kod push'larında canlı davranış değişir: eklenen defter satırları ve `loop.yml` her push'ta
  denetlenir; bugünkü dosya ve satırlar geçer, f185 kod push'unu hiç durdurmaz.
- **Ayrıca.** `local/mutate.py --only` virgüllü liste alır. `github_outage_ends_the_pilot`'un çapası E248'in commit'inden
  (`e705a03`, `except GitHubUnavailable` → `except Outage`) beri yoktu, mutant koşmuyordu: yeniden çapalandı.
- **Doğrulama.** Taban (`6d84d46`): Windows 428 test OK (18 atlandı), Linux (`snowball_linux_test:git`, ağacın LF
  arşivi) 446 OK (3 atlandı). Dal: Windows 481 OK (18 atlandı), Linux 499 OK (3 atlandı). Mutasyon (Linux, dört
  kapsayıcı, her listeden önce yeşil baz koşu): yeni 70 ve çapası yenilenen 4 mutantın 74'ü öldü; değişen dosyalardaki
  (`cli`, `decide`, `config`, `treehash`, `classify`) eski 116 mutantın 116'sı öldü; listenin kalan 169'u da öldü.
  Toplam 359/359, hayatta kalan ve çapası kayıp yok (323'ü son ağaçta; 36'sı, durdurulan ilk tam koşuda, bundan
  yalnız test yorumları, bu bölüm ve `wiring.py`'deki görünmez karakterlerin `chr()` ile yazılmasıyla ayrılan ağaçta).
- **Yapılmayan.** `spec/` değişmedi (altküme, `control` arayüzü ve seçimler `29b`/`29e`'ye tohum partisiyle yazılır;
  `26c`, `29f` başka partide); içe aktarmanın oyuncak hash karşılaştırması ve karantinası (E131 (B)), `.github/` ve
  `bootstrap/` silmesi (E100, `10a` #aktarim), çevrimdışı actionlint/zizmor ve sır-iş haritası (E132 (B)), Windows ad
  takma adları (E130), E90'ın her push `agent_config_modified`'i, `founder-ledger append` aracı (`asama-1/13`: tohuma).

### E162 devamı, şüpheci turu (2026-10-30) · dal `gaps/stage0-exit-checks` · E288–E292 açıldı ve kapandı
- **Kırılanlar (şüphecinin yeniden üretimleri, hepsi bu dalın `d6124c4`'ünde).** (1) `${{ '}}' && secrets.X }}`
  `kos`'a sır, `run:`'a `github` bağlamı, `cagir`'a `toJSON(secrets)` taşıyordu, `wiring.check` → `[]` (E288).
  (2) NFD `güneş`, `ıskele`/`İskele` #genellik'ten geçiyordu; UTF-16 ve ISO-8859-9 dosyadaki ad `ok`; yalnız
  oyuncağın boş `identifiers`'ı #genellik'i hiç karar veremez kılıyordu (E291). (3) Hedef adı #agac ve #is-akisi
  nedenlerinden imzalı sonuca giriyordu (E290). (4) `referee/.GITHUB/workflows/evil.yml` görünmüyordu, Windows'ta
  içe aktarma onu `.github/` ile birleştiriyordu (E289). (5) 1..16 bildiren push MF17'nin `wiring`'ini kapatıyordu
  (E292). (6) Dokuz mutant hiçbir testin ölçmediği bir yerdeydi. Daha az önemli: `shell:`, `defaults.run`,
  github-script'in `script`'i (E288'e alındı).
- **Kökler ve düzeltmeler.** İfade GitHub'ın şablon okuyucusunun kuralıyla ayrılır (bir `}}` tek tırnak içinde
  bitirmez), betik sayılan her alan tek yüklemle (`_github_in_script`) okunur. Adın biçimi tek işlevdir
  (`exitchecks.fold`; Python `re.IGNORECASE`'in aynı saydığı her çiftin aynı katlandığı bütün kod noktalarında
  tarandı); metin olmayan dosya sessiz geçmez (`referee_file_not_text`, Kurucu'nun); karar kopya hedefin adlarını
  ister. Adın gösterimi tek kuraldır (`exitchecks.withheld`), dört koşulun sonucuna ve çıkışın öbür nedenlerine
  uygulanır. Harf büyüklüğü: iş akışı dizini casefold ile tanınır, ağaç hash'i (pull, içe aktarma, oyuncak) harfçe
  ayrı ama NTFS'te tek iki adı reddeder (E130'un harf çakışması kuralı). `done_mf` küçülemez (`done_mf_withdrawn`),
  `wiring` son kabul edilmiş commit'in MF17'siyle de başlar. Durum şeması `snowball-bootstrap-state/3` aynı.
- **Önce kırmızı.** Yeni testler `d6124c4`'ün kodu üstünde koşuldu: 68 test, 18 başarısız ve 3 hata (alt testlerle
  daha çok); her kırık en az bir kırmızıyla görüldü. Mutant öldüren sınır testleri (dokuz eski mutant) eski kodda
  zaten geçer, onlar davranışı sabitler. Şüphecinin `test_skeptic171.py`'si (8 test) bu ağaçta yeşil.
- **Canlı kanıt** (beynin taze, salt okunur klonu `517b39d`, kod koşulmadı): #kurucu-defteri yalnız
  `founder_ledger_accepted_invalid:kind:L185` (229 satır), #is-akisi `ok`, #agac `ok` (oyuncak hash'i
  `6d234f7d…`; harf çakışması yok), #genellik `undecided` (özette `targets[]` yok, E284); `referee/`'de 80 dosya,
  metin olmayan yok; `done_mf` 1..18 (E292 canlı push'ları değiştirmez); hakem ağacı hash'i hesaplanır.
- **Doğrulama.** Windows (`seed/bootstrap`, `PYTHONPATH=.;tests`): 496 test OK (18 atlandı; tur öncesi 481). Linux
  (`snowball_linux_test:git`, ağacın LF arşivi): 514 OK (3 atlandı; tur öncesi 499). Mutasyon (Linux, dört
  `snowball_exit_*` kapsayıcısı, her listeden önce yeşil baz koşu): bu turun değiştirdiği dosyalara (`wiring`,
  `exitchecks`, `treehash`, `cli`, `ledgercheck`) bağlı her mutant, turun 32 yenisi ve çapası yenilenen 6'sı dahil
  142/142 öldü; hayatta kalan ve çapası kayıp yok (liste 391 mutant). Şüphecinin kendi dokuz tanımından sekizi bu
  ağaçta öldü (`MAX_DEPTH` 39 ve 100 de), dokuzuncunun (`generality_path_case_sensitive`) satırı artık yok, karşılığı
  listede ve ölü. Mutantların koştuğu ağaçtan commit'lenen yalnız bu madde ve iki test yorumuyla (mutant adları)
  ayrılır.
- **Yapılmayan.** `spec/` değişmedi (altküme, ifade sınırı, betik alanları ve katlama `29b`/`29e`'ye tohum partisiyle
  yazılır). E290'ın sınırı (yol hash'i beynin yollarından bulunur) ve E291'in metinsel sınırı (parçalanmış ya da
  kodlanmış ad) kayıtlı; `needs.<iş>.outputs` üzerinden sır taşıma E283'te karar verilemez kalır.

### Aşama 0 çıkış kararları (2026-10-30) · dal `gaps/stage0-exit-decisions` · E280 E282 E293 E296 E297 kapandı · E294 E295 açıldı
- **Öncülün düzeltmesi.** Kabul edilmiş bir defter satırı hiçbir kod push'unu durdurmaz (push yalnız eklenen
  satırları okur, `ledgercheck`); kırık, çıkışın hiç geçememesiydi: kabul edilmiş anlam kırığı Kurucu'ya sayılmıyor,
  eklemek onu değiştiremiyordu. Bu dalın seçimleri uygulayıcınındır, şüphecinin kanıtı tutan yerlerinde onun
  biçimiyle; sahip onları seçmedi, birleştirme onun incelemesidir. Dalın ilk commit'inin başlığındaki "the owner's
  decisions" bu yüzden fazladır.
- **E280 (şüphecinin (b) biçimi).** `learning` kümeye eklenmedi. `derived_from` yüklenmedi: o soy alanıdır, kapatma
  `superseded` tarafıdır (`22`, `26b`). Kapatma yeni bir kural olarak yazıldı, var olan kural diye sunulmadı: `13`
  "Kurucu defterinde kapatma", alan `26`'nın `founder` satırında `supersedes?`. Kabul edilmiş, anlamı bozuk (`part`,
  `kind`, `supersedes`) satırı sonraki geçerli satır `supersedes`'iyle kapatır; `supersedes` başka bir şeyi
  adlandırırsa satır geçersizdir; push'un eklediği bozuk satır kapatılsa da reddedilir. Kapanış çıkışta başın bütün
  defterinde okunur, kapatan satır çıkış isteğiyle de gelir; imzalı sonucun `checks.kurucu-defteri.why`'ı
  `L<n> superseded by L<m>` yazar. Bayt, JSON ve zincir kırığı kapanmaz (`ledgercheck.beyond_appending`), Kurucu'ya
  sayılmaz; kapatılmamış anlam kırığı artık Kurucu'nundur, çünkü eklemek onu kapatır (`29b` "Ret hafızası").
  Kapatılabilir küme önceden dondurulmuş sayılmaz: bu kural gelene dek kabul edilen her anlam kırığı aynı yoldan
  kapanır. `13`'ün "hiçbir kapı kararına girmez"i içerik içindir; yapı denetlenir (aynı madde).
- **E282.** Kurucu'nun bildirdiği çağrı (seed-035) incelendi ve benimsendi: hakem reposunun `main`'i kimliksiz ve
  seyrek çekilir, komut `bootstrap/`'tan koşar (`python -m` için `sys.path`'in başı `bootstrap/`'tır, kökteki bir
  dosya onu gölgeleyemez), `control.json` canlıdır. Dosyadan karar (`29p`, `wiring`): ilk adım bayt bayt tohumun
  adımı, sonraki her adım tam `go` koşulu (GitHub `success()`'i ekler), adımın üstünde yalnız kuralın saydığı
  anahtarlar (E296; ör. `PYTHONSAFEPATH`, başka bir `python3` ya da bir hizmet kapsayıcısı kontrolü değiştiremesin). Komutun döngü okuması:
  dört bayrak birlikte; kill switch, fren, bilinmeyen tetik ya da iş çıkış 2; `schedule` iken `loop_schedule` tam
  `true` değilse `go=false`; `merge_paused` ve `founder_resume`'u okumaz (okuyucuları `gate.check` ve başlatıcı).
- **E286.** Denetim yazılmadı, nedeni kesinleşti (satırda): iki maddenin makine tanımı yok, okuyucu maddesi E156'yı
  bekler, karar verilebilir parçalar koşulu tek başına geçiremez, yer dondurmadır (E180).
- **E287 → E293, E294 (şüphecinin adlandırmasıyla).** Kök neden çıkışta değil başlangıçtaydı: ilk durum özetin
  10a ve 10c alanlarını hiç istemiyordu (E293, `config.start_missing`, `fetch-state`). Aşama 0'ın #durustluk'u yalnız
  sahibin adlı istisnasıyla kalkar (E294): kural tek yerde (`02` "Sahip istisnası"), örneği operatörün verisi
  (`26c` `honesty_exception`); (A) sonucu `owner_exception`'ı `measured: false` ile her çıkış isteğinde yazar, koşul
  geçmiş ya da `UNMEASURABLE` sayılmaz; taşıma kuralı tohumda, Aşama 1'in donmamış taslağı `asama-1/08`'de değil
  (tohum dönemi oraya ulaşmaz). Ekimin makinesi ve kendisi E79/E287'de açık.
- **E284.** Kod değişmedi; #genellik'in karar şartı (`config.names_the_copy`) başlangıç kapısıyla tek kaynaktır.
  Kalan, operatörün `targets[]` adımıdır.
- **Önce kırmızı.** Yeni ve değişen testler (`test_exit_decisions` 29 test; `test_exit_checks`, `test_decision`'ın
  tablo testi, `test_flow`, `test_state`; `helpers.LOOP_YML` her işte tohumun kontrol adımıyla) `fe65ce6`'nın kodu
  üstünde: 136 test, 42 başarısız, 9 hata (alt testlerle). Kontrol komutunun "durur" durumları eski kodda argparse
  bilinmeyen bayrağı reddettiği için kazara geçer; onları mutantlar ölçer.
- **Canlı kanıt** (beynin taze, salt okunur arşivleri `f3f4933` ve `2d364da`, `gh api`; hiçbir şeyi koşulmadı): canlı
  `loop.yml` yeni kuralla `[]`; defter 243 ve 250 satır, push denetimi `[]`, çıkışta tek neden `founder_ledger_accepted_invalid:kind:L185`;
  kapatma kuralı canlı defterin bir kopyasında denendi ve çıkışı açtı (push denetimi `[]`); #agac `ok`, #genellik
  `undecided` (özette `targets[]` yok). Hakem reposunun `control.json`'unda `loop_schedule` yok: döngünün
  zamanlanmış koşuları `paused`, elle tetikleme koşar. Bu kanıt şüpheci turunda eskidi (aşağıda).
- **Doğrulama.** Windows (`seed/bootstrap`, `PYTHONPATH=.;tests`): 526 test OK (19 atlandı; önce 496). Linux
  (`snowball_linux_test:git`, ağacın LF arşivi): 545 OK (3 atlandı; önce 514). Mutasyon (Linux, sekiz
  `snowball_dec_*` kapsayıcısı, her listeden önce yeşil baz koşu): bütün liste, 476 mutant; turun 34 yenisi ve
  çapası yenilenen 6'sı dahil 475'i öldü. Hayatta kalan tek mutant `changelog_over_80_lines`'ın öncülünü günlüğün
  bölünmesi bozmuştu (8 boş satır 48 satırlık sayfayı 80'in üstüne çıkarmıyordu); artık 81 satır ekler ve öldü
  (`test_no_page_is_over_80_lines`). 476/476, çapası kayıp yok. Mutantların koştuğu ağaçtan commit'lenen yalnız bu
  madde, canlı kanıt maddesi ve o mutantın düzeltmesiyle ayrılır.
- **Şüpheci turu (E296, E297).** Şüphecinin kırıkları yeniden üretildi, kökten kapandı. (1) E296: adımın üstü yasak
  listesiyle denetleniyordu, `services` geçiyordu; kural artık izin verileni sayar, sayfa kodun listesini taşır.
  (2) E297: istisna ekimsiz de çıkışı açıyordu ve yeni pilot yalnız istisnayla başlıyordu; artık ikisi de
  `honesty_commitment` ister. (3) Hayatta kalan iki mutantı (`number == 2`, `isinstance`) testler öldürür (E296).
  (4) Canlı kanıt tazelendi (beyin `3f605a1` = tohum dönemi 3a, son kabul `3f01932`, 265 satır, salt okunur): yeni
  `ledgercheck`'le push denetimi `[]`, çıkışta iki neden, L185 ve L263 (ikisi de `kind: learning`; L263 Kurucu'nun
  son oturumundan); canlı defterin bir kopyasına ikisini kapatan iki geçerli satır eklenince push denetimi `[]`, çıkış
  `L185 superseded by L266; L263 superseded by L267` (yalnız benzetim, beyne hiçbir şey yazılmadı); canlı
  `loop.yml` yeni izin listesiyle `[]`, beş işine `services` eklenmiş hâli beş `workflow_control_context`. (5) Teslim
  sınırı (E280 satırında): kuraldan önce yazılıp kabul edilmemiş bozuk satır kapanmaz, her push'u reddeder; Kurucu'nun
  yolu kabul edilmemiş kuyruğu yeniden yazmaktır (`asama-0/10` buna izin verir), operatörün önlemi teslimi defterin
  son kabulle aynı olduğu ana koymaktır. Tohum döneminin adı 3b (3a, `c97803f`, `ledgercheck`'siz teslim edildi).
  (6) Kayıt dürüstlüğü: "f185 için Kurucu'ya talimat yok" yanlıştı; teslim edilen `ledgercheck.py` ve iki test f185'i
  çaresinin yanında adlandırıyordu (`seed/` beyne de gider); kaldırıldı, testlerdeki `L185` nötr satır numarasıyla
  değişti, canlı pilotun adı yalnız bu kayıtta. "İstisna insan dokunuşu sayılır" ve "PASS satırı istisnayı taşır"
  yazılı ama denetlenmiyor (E294'te, E277). E280'deki (b) seçimi sahibin değil uygulayıcınındır.
- **Şüpheci turunun doğrulaması.** Kırmızı-önce: yeni ve değişen testler bir önceki commit'in kodunda 13
  başarısız, 2 hata verdi. Windows: 529 OK (19 atlandı). Linux (LF arşivi): 548 OK (3 atlandı). Mutasyon (sekiz
  `snowball_dec_*` kapsayıcısı, her parça 61): 488/488 öldü; turun etkilediği 31 mutant ayrıca 31/31. Makine bu
  koşulardan sonra, commit'ten önce kapandı (2026-10-30 ~23:02Z); bu kaydın çalışma kopyası sıfır baytla kaldı,
  sağlam hâli sahnelenmiş sürümden geri yüklendi; main'le birleştirmeden sonra takımlar yeniden koşuldu.
- **Yapılmayan.** `spec/asama-0` ve `spec/asama-1` değişmedi (dondurma, E180; tohum dönemi taşımaz). E150
  (`founder-ledger append` aracı) sahibin kararında. Dürüstlük makinesi ve ekim (E79, E287), taşımanın kodu (E294),
  ilk koşu işareti (E14, E92), özel hakem reposunun okuma yolu (E295).
### E310–E320 (2026-10-30) · kendini geliştirmenin kanıtı: karne ve ders provası · dal `gaps/self-improvement-proof` · E64 E65 E310 E318 kapandı · E70 E319 kısmen · E311–E317, E320 açıldı
- **İstek.** Sahip iki öneriyi, uzmanlar doğrularsa, onayladı: (P1) canlı pilotun verisinden kendiliğinden üretilen
  bir kendini geliştirme karnesi; (P2) ders provasının (`22a`) MVP sınavı olarak Aşama 0 çıkışından hemen sonra gerçek
  beyinde koşulması. Ölçüm uzmanı, prova uzmanı ve şüpheci tartıştı; her iddia canlı veriyle (45–47 imzalı sonuç,
  257–265 defter satırı, operatörün ölçümleri) ya da yeniden üretimle.
- **Tutanlar.** Pilot kanıt olamaz: sabit ölçüt, karşı-olgu ve önceden yazılmış karar kuralı yok; karnenin ilk satırı
  "kanıtlandı mı: hayır", bileşik puan yok, her ölçü derecesiyle, küçük n `UNMEASURABLE`. E64 ve E65 yeniden üretildi.
  P2 Aşama 0 çıkışında koşamaz: ders organı yok ve öne almak aşama planını (`03`, `asama-1/13`) değiştirir, o plan
  tohum dönemiyle değişmez (E317, E180). İlk yazılan "organları söylemek Kurucu'ya çözümü verir" gerekçesi şüphecinin
  ikinci turunda tutmadı: Kurucu'nun elindeki `22` ve `22a` organları zaten adlandırıyor.
- **Çürütülenler.** Mekanik hata sınıfı anahtarı (uzmanın iki örnek tekrarı da anahtarla eşleşmedi; tek tam eşleşme
  E248'in kör push'uydu): push'lar arası tekrar `ölçülemez` kaldı (E70). Kurucu'yu öğrenen sayan defter-öneki
  ablasyonu (kapsül bütün geçmişi klonlar). %70 kalibrasyon hedefi (21/30 eşiğiyle provaların %41'i UNMEASURABLE,
  E319). İkinci yargıç olarak dökümün yeniden kurulması (tutarlılık denetler, doğruluk değil). Karnenin başlatıcının
  döngüsüne bağlanması (takılan bir `gh` döngüyü durdurur; yeniden başlatma bir müdahaledir). Başlık sayısının
  düzeltilmiş hâliyle tek başına verilmesi: MF7–MF18 hakemin kuralıyla 10/12, düzeltilmiş 11/12; ikisi yan yana.
  Pozitif kontrol eksikti (E318).
- **Yapılan, P1.** `seed/founder/scorecard.py` ve `scorecard_exclusions.json` (E310 satırı); üretilmiş `docs/karne.json`
  ve `docs/karne.md`; özel karne ve önbellek `F:\snowball-work\scorecard\` (47 artefakt, hepsi özetiyle); günlüğün
  "Ölçüm" tablosu karneye işaret eder; karne `docs/harita.md`'de (E301).
- **Yapılan, P2'nin tohum tarafı.** `seed/drill`: kör kapsam (E64), hakemin çekilişi ve eşit kollar (E65), doğru ders
  sorusu (E318), k = 30 ve kalibrasyon (E319, `calibrate`, `effect`); beş yeni simüle beyin (`label_peeker`,
  `overbroad_scope`, `llm_prior_discarder`, `cherry_picking_dispatcher`, `unequal_arms`); `drill` vektörleri yeniden
  üretildi (24 vaka, sahibi hâlâ Aşama 2 partisi). Sayfalar: `22a`, yeni `22b` (sözleşme, gizli taahhütlü havuz,
  kalibrasyon, ne zaman ve PASS neyi gösterir), `29c`, yeni `29q`, `18a`.
- **Yapılmayan.** Ders partisi (E317, sahibin kararı). `25`, `26`, `02` ve hakemin `decide`/`exitchecks`'i bu dalda
  değişmedi (öbür partinin); başlatıcı değişmedi (E312, E313 planlı yeniden başlatmayla); rakip kanaryaları (E311),
  tahmin alanı (E314), doğrulanmış öz-tespit (E315). Sigstore paketleri önbellektedir ama karne onları doğrulamaz
  (yalnız stdlib); operatör `python -m sigstore verify` ile doğrulayabilir.
- **Doğrulama.** Windows (`seed/bootstrap`, `PYTHONPATH=.;tests`): 524 test OK (18 atlandı; dal öncesi 506);
  `seed/drill`: 56 test OK (önce 31). Drill yargıcının 56 mutantının hepsi öldü (`local/mutate_drill.py`; ilk koşuda
  `small_arm_measured` yaşadı: `no_injection` artık çekiliş denetiminde FAIL alıyor ve kol boyu kuralına hiçbir
  simüle beyin ulaşmıyordu; kuralın kendi testi eklendi);
  karnenin 12 mutantı karne testleriyle öldü (tam liste CI'nın Linux mutasyon işinde); 500 prova: öğrenen 500/500
  PASS, 19 kusurlu beynin hiçbiri PASS almadı.
- **Şüphecinin ikinci turu.** Çürütmedi, sekiz kırık saydı; her biri yeniden üretildi (mutant, komut ya da kaynak
  satırı), sonra kökünden düzeltildi. (1) İlk denemesi işaretli birimin düzeltilmiş kuralı testsizdi; beş seçici daha:
  yeni ayrı test dünyası ve 13 yeni karne mutantı, hepsi öldü (E310). (2) "Kalıcılık" ve "yanlışı yanlış bilir"
  ölçüleni aşıyordu: kusurlar ayrı anahtarla, modülsüz testler MF'den ayrı sayılır; kalıcılık `ölçülemez` (E320),
  "yanlışı yanlış bilir" `ölçülemez` (E315). (3) E65'in eşit kolları yalnız plaseboyu kapsıyordu: etki çiftleri de
  (E65). (4) P2'nin gerekçesi aşama planına ve E180'e dayandırıldı, karar sahipte kaldı (E317); `22b`'nin "beş
  sorusu" düzeltildi. (5) Kalibrasyon kapısı nokta tahminidir: `calibrate` riski alt sınırda da verir, kapının alt
  sınıra bağlanması açık (E319). (6) Karne iki ayrı an karıştırıyordu: defter son sonucun başında okunur, başka başta
  okunmuşsa karne reddedilir. (7) Günlük elle tablonun bütün satırlarının karnede yeniden sayıldığını söylüyordu ve
  karnenin sayılarını elle kopyalıyordu: hangi satırların düştüğü yazıldı, kopya sayılar kaldırıldı. (8) Karne
  imzayı doğrulamadan "imzalı" diyordu, özetsiz artefakt denetimsiz önbelleğe giriyordu: söylenen düzeltildi, özetsiz
  artefakt karneyi reddeder. Karne aynı kayıt noktasında (47 sonuç, 265 defter satırı) yeniden üretildi; birim, oran
  ve push sayıları değişmedi. Doğrulama: Windows `seed/bootstrap` 532 test OK (18 atlandı; önce 524), `seed/drill` 60
  test OK (önce 56); karnenin 25 mutantının hepsi `test_scorecard`'la öldü (işaretli ilk deneme mutantı dahil),
  yargıcın 3 yeni mutantı öldü.
- **Birleştirme notu.** `gaps/stage0-exit-decisions` bu bölümün hemen önüne kendi bölümünü ekler; ikisi de kalır.

### E321–E324 (2026-10-31) · ders provasının sınav tarafı, tartışmanın hakem kararı · dal `gaps/drill-exam-fixes` · E317 E321–E324 kapandı
- **İstek.** E317'nin kararı: iki uzman tartıştı (biri provayı Aşama 1 çıkışına bağlamayı, öbürü Aşama 2'nin ilk işi
  yapmayı savundu), bir hakem karar verdi. Karar: Aşama 2 yerleşimi, Aşama 1 uzmanının sınav düzeltmeleriyle. Kayıt
  satırları ipucu sayıldı; her iddia kodda yeniden üretildi.
- **Yapılan, tohum metni.** `03` Aşama 2 satırı ("Ders görünümü ve enjeksiyonu (`18`), ilk okuyucusuyla; gerçek
  beyinde ders provası, sahibin MVP sınavı (`22b`)"); `02` (aşama özeti `03` satırındaki her `18` yeteneğini listeler);
  `18` (`#ders-dogru`); `18a` (`gate_rules.lesson_drill`: α_i, eşit etki kolları); `22a` (Etki satırı, anahtarda
  denemenin sırası); `22b` (havuz taahhüdünün zamanı, açık aileler dışarıda, her okuyucu modeliyle kalibrasyon, "Ne
  zaman" bölümü); yeni `22c` (`22b` 89 satıra çıkınca bölündü: hakemin çekilişi, eşit kollar, denemeler); `29c`,
  `29q`; `asama-1/13` Aşama 2 satırı (tohum teslimi taşımaz, E180; bağlayan `03` ve `22b`). Tohum günlüğünün en eski
  2.2 kaydı `main`'deki gibi `CHANGELOG-2.md`'ye taşındı.
- **Yapılan, `seed/drill`.** `_effect` her çifti ayrı denetler (E321) ve denemenin düzeyini anahtardan okur (E323);
  `sim.py` her etki koşusunun ayarlarını ve ders bloğu çıkarılmış prompt hash'ini kaydeder; yeni simüle beyin
  `unequal_effect_arms`, yeni düzenlenmiş prova `second_attempt`, `missing_evidence` etkide de; `effect <p> <p> [koşu
  [deneme]]`. Vektörler yeniden üretildi (26 vaka).
- **Kırmızı önce.** Yeni testler `0f1645d`'nin yargıcıyla koşturuldu: 71 testten 16'sı kırmızı (14 FAIL, 2 ERROR);
  `unequal_effect_arms` 200/200 provada PASS, `second_attempt` PASS.
- **Yapılmayan.** Karnenin sınav tanımı (`seed/founder/scorecard.py` `DEFINITIONS["exam"]`) hâlâ "sahibin kararını
  bekler (E317)" der; tanım hash'lenip karneye girdiği için karne bir sonraki üretimde düzelmeli. `policy.json`'un
  `required_exit_rows`'u (E322) ve havuz (E324) operatörün işidir.
- **Doğrulama.** Windows `seed/bootstrap` (`PYTHONPATH=.;tests`): 532 test OK (18 atlandı; `0f1645d`'de de 532);
  `seed/drill`: 71 test OK (önce 60); `local/mutate_drill.py` 69/69 mutant öldü (önce 59; şüphecinin etki kolları
  için yazdığı 3 mutantın yerini çift başına ve çiftler arası denetimin 8 mutantı aldı, denemelerin 5'i yeni).

### E338–E339 (2026-10-31) · sınıf merdiveni varsayılandır · dal `gaps/ladder-default` · E338 kapandı · E339 açıldı
- **İstek.** Sahip (2026-10-30): sınıf merdiveni sistemin kanıtla yeniden sıralayabileceği bir varsayılan mı olsun,
  uzmanlar karar versin. Güvenlik, öğrenme ve şüpheci uzmanları tartıştı, hakem şüphecinin biçimini kabul etti.
  Kararın satır çapaları ipucu sayıldı: kararın ardından `main` aynı sayfaları değiştirdi (ders provası Aşama 2'nin
  ilk işi oldu, E317, E321–E324), her değişiklik bugünkü `main`'de yeniden bulundu.
- **Yapılan, yalnız tohum metni.** `03`, `02`, `10`, `15`, `18`, `18a`, `26b`; çapalar `04a`, `07a`, `10a`, `11`, `12a`,
  `21a`, `22`, `30e`, `31a`, `31b`, `31d`, `31h`; metin `01a`, `04a`, `06`, `08`, `17`, `19`, `24`, `25a`, `26a`, `27`,
  `27a`, `29`, `30`, `30a`, `30f`; tohum günlüğü; README; pilot günlüğü. Hakem kodu yok (E339).
- **Yeniden bulunan.** `02` 80 satırdır (kararın yazıldığı 68 değil): madde 2'nin çapa satırı 32, çapa kuralı 71–72;
  sayfa 80'de kalsın diye olay listesi tek satırda. `03` 79 satır (kararın 74'ü artı ders provası kararını koruyan
  cümle, "aynı çıkışta" tanımı ve Aşama 4 paragrafı). `18`'in yeni satırı tablonun sonunda; `18` 20'ye (anayasal bölüm)
  sınıf önkoşulları eklendi, çünkü `class_requires` anayasaldır. `15` 3 `02`'nin çapa kuralını tekrarladığı için aynı
  biçimde değişti.
- **İkinci tur (inceleyici, aynı gün).** Dalın kendi açtığı çelişkiler (`main`'de yoktu) kökünden kapandı:
  (a) Aynı gerçek iki türlü okunuyordu: mühürlü depo `19` ve `25a`'da K5 ön koşulu, `01a` 18 ve 44, `24` 17 ve README'de
  Aşama 4; `oracle.run` `04a`'da LLM avcıyla, `26a` 63 ve `29` 58'de Aşama 4; K6 düzeltmesi `03` ve `30f`'te önkoşullarla,
  `30` 12 ve 42 ile `30a` 4'te Aşama 5. Tohumda iki tohum sayfası arasında öncelik kuralı yok (`02` yalnız aşama spec'ini
  tohuma bağlar), bu yüzden hepsi olaya bağlandı; hakemin kuralı (aşama numarasına bağlı metin koşulları aynı biçimde
  yeniden bağlanır) ve (7) denetimi için öbür sınıf sırasına bağlı koşullar da: `08` 54, `24` 67, `26a` 47, `27` 35,
  `27a` 36 LLM avcıya; `06` 19 Daha ucuz basamağa; `17` 73 genesis'in açılmasına. Kalan 27 satır Aşama 2'yi sayaç
  konumu olarak anar (E339 (7)).
  (b) `02`'nin olay listesi çapaları kapsamıyordu: harita katmanı listede değil ve PASS satırı yok. `13` katmanları
  sınıflara bağlar, çapalar o sınıfların açılışını bekler: `31a`, `31d`, `31h` K3 ve K4 açılışı; `31b` K2 silme (harita
  (a) K2 silmenin önkoşuludur, o çıkışta vardır). `22` yeteneğin tam adını, `11` Genesis yaşam döngüsünü (ikinci aday
  organ onu canlı yapar, `03`), `21a` Çok repolu terfiyi, `30e` aşama 0'ı bekler (etkinleştirme Aşama 0'ın (B)'sindedir,
  `25a` 7, PASS satırı ondan sonra yazılır).
  (c) E339'un (1)'i `03`'ün tablosuyla çelişiyordu ("önceki bir PASS satırı" K5'i hiç açtırmazdı) ve iki girdi seçimden
  önce kapanamaz: K6'nın Güvenlik yoluna dokunması (`05`: K6 canlı olana kadar güvenlik yoluna dokunulmaz), K2 silmenin
  harita (a)'sı (`13`: K2 silmeleriyle gelebilir). `03` "aynı çıkışta"yı tanımlar ve o iki girdiye yazar; E339 (1)
  girdileri türüne göre denetler; yetenek olmayan girdiler (`07a` kanıtları, harita (a), `class_floors` yazılı) ipucunda.
  (d) Çıkışta `UNMEASURABLE` sınavı geçiyordu ve "bu alt sınır" varsayılanınki okunabiliyordu: #sira-denetim seçilen
  sınıfın kendi alt sınırına bakar, `UNMEASURABLE` çıkış varsayılanı geri getirir (`19`: `UNMEASURABLE` asla `PASS`
  gibi davranmaz).
  (e) Varsayılan satır `10`'un yan yana koşusuyla çelişiyordu: `10` sınıf seçiminin böyle koşmadığını, seçimi hakemin
  tahmininin ve çıkış sınavının tarttığını söyler (hakemin C8'i reddetme gerekçesi: varsayılan sınıf koşmaz).
  (f) `03`'ün tablo başlığı sabit satırları da varsayılan sayıyordu: "(0, 1 ve 6 sabit)". Aşama 4 paragrafı `asama-4`'ü
  K5'in hedef taslağı olarak anar, ön koşulu tablodur (`asama-4/00-ozet` 9 "K0–K4 döngüleri canlı" der; tohum geçerli,
  `02` 1). (g) README 25 ve 36 ile pilot günlüğünün "Sıradaki"si.
- **Kararın metni dışında, gerekçesiyle.** `18` 69'daki "spec onu satır hash'iyle anar" kapının (3) denetimiydi:
  tohumdan çıktı, E339'da. Kalanlar: `03`'te sapmanın `18` satırlarını taşıması (yeteneğe anahtarlı çıkış satırları,
  `18`), kök ve son (hakemin "sabit kalan"ı), satırdaki `18` atıflı yeteneğin düşmemesi (ders provası kararı E317),
  "aynı çıkışta" tanımı ve iki girdisi ((c)), tablo başlığının parantezi ve Aşama 4 paragrafı ((f)); `18` 20'de sınıf
  önkoşulları (`class_requires` anayasaldır), #sira-tahmin'in `UNMEASURABLE` cümlesi ve `03` atfı (hakemin kuralı:
  `UNMEASURABLE` tahmin varsayılanı geri getirir), #sira-denetim'in biçimi ((d)); `15` 3 (`02`'nin çapa kuralının
  kopyası); `10` ((e)); ikinci turun yeniden bağlamaları ((a), (b)).
- **Yapılmayan.** `asama-1/11` (donmuş, tohum geçerli) ve `asama-1/00-ozet` (Güvenlik avcısı ve bekçi testlerini
  listelemiyor, E339'un ipucu); `asama-4/` (hedef taslak, Kurucu yeniden yazar, tohum geçerli); `policy.json`'un
  `class_requires`'ı hakem reposunda operatörün işidir, aynı tohum döneminde.
- **Doğrulama.** Windows `seed/bootstrap` (`PYTHONPATH=.;tests`): `tests.test_wiring` ve `tests.test_stages` 39 test OK,
  bütün paket 562 test OK (19 atlandı); `local/system_map.py --check` temiz; hiçbir sayfa 80 satırı geçmiyor (`03` 79,
  tohum günlüğü 79).

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
