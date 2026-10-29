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
| E06 | Yeniden üretici sözleşmesi belirsiz; stderr ve çıktı atılıyor | K | — | R2 D4 | spec yazıldı · kod açık |
| E07 | Yeniden üretilemeyen iddia iz bırakmıyor | K | evet | D4 R2 | spec yazıldı · kod açık |
| E08 | Kanıtlanmış kusur unutuluyor; tekrar sayacı iddia metnine bağlı | K | evet | R1 D9 | spec yazıldı · kod açık |
| E09 | Totolojik yeniden üretici (`true`) "yeniden üretildi" sayılıyor | K | evet | R3 | spec yazıldı · kod açık |
| E10 | Rakip Kurucu'nun defterini görüyor (spec yasaklıyor) | K | evet | R6 S3 | spec yazıldı · kod açık |
| E11 | Rakibin kendi hataları Kurucu'nun "öğrenmiyor" sayacına yazılıyor | K | evet | R11 S11 D8 | spec yazıldı · kod açık |
| E12 | Kalıcı 4xx ve izolasyon hataları sonsuza dek kesinti diye yeniden deneniyor | K | evet | D6 | spec yazıldı · kod açık |
| E13 | Rakip harcaması bazı yollarda hiç yazılmıyor | K | — | R9 D5 W4 | açık |
| E14 | İmzalı durum kaybolursa hakem sessizce tohumdan yeniden başlıyor | K | evet | W1 D7 | spec yazıldı · kod açık |
| E15 | Eski imzalı durum geri yüklenebiliyor (zincir yok) | K | — | W2 | spec yazıldı · kod açık |
| E16 | `yaz`'daki "canlı" kill switch canlı değil; iptal `yaz`'ı durdurmuyor | K | evet | W3 | spec yazıldı · kod açık |
| E17 | İş akışında şablon enjeksiyonu; imza kimliği `main`'e sabit değil | K | — | W7 | kapandı · parti 1 |
| E18 | Testlerin toplam süresi sınırsız; yavaş test "ret" değil "kesinti" | K | — | W8 X5 D12 | açık |
| E19 | Kurucu kaynaklı hatalar altyapı arızası sınıflanıyor | K | — | D12 | açık |
| E20 | Çıkıştaki "bağımsız rakip denemesi" sayımı yanlış; yeniden deneme rakibi tekrar çağırıyor | K | evet | D10 D11 | spec yazıldı · kod açık |
| E21 | Donmuş spec yeniden dondurulabiliyor; her aşama dizini donuyor | K | evet | S1 D14 | spec yazıldı · kod açık |
| E22 | Tohumdaki Aşama 0 spec'i değiştirilmeden dondurulamıyor | K | — | S2 | spec yazıldı · kod açık |
| E23 | Çıkış kontrolü hakemin yapmadığı denetimleri sayıyor | K | evet | S4 | spec yazıldı · kod açık |
| E24 | Kurulum özeti, vektör, koltuk ve politika hash'leri denetlenmiyor | K | — | S5 | spec yazıldı · kod açık |
| E25 | Aşama 0'ın `llm.call` ve `agent.dispatch` sayfaları API anahtarı ve geçit varsayıyor | K | evet | S6 | kapandı · spec (Aşama 0 MF20/MF22 kodu Kurucu'nun) |
| E26 | Bu repoda CI yok | K | evet | W5 | kapandı · `.github/workflows/ci.yml`, ilk tam koşu yeşil (run 40845743667) |
| E27 | İzolasyon hatası ancak tam koşudan sonra fark ediliyor | B | — | R8 | açık |
| E28 | Kapsayıcı çıktısı belleğe sınırsız alınıyor | B | — | X2 | açık |
| E29 | Operatörü uyaran hiçbir şey yok | B | evet | W6 | spec yazıldı · kod açık |
| E30 | Kablolama testleri izinleri, adım çıktılarını ve tetikleri denetlemiyor | K | — | W10 | açık |
| E31 | Action'lar eskimiş Node 20 sürümlerinde; her action'a izin var | B | — | W9 | açık |
| E32 | Zamanlayıcı hiç tetiklenmedi; açık repo güvenlik ayarları kapalı | K | evet | W12 | onaylandı; sır taraması ve itme koruması açıldı, beyin reposunda Actions kapatıldı (2026-10-29) · zamanlayıcı açık |
| E33 | CLI sürüm kayması ve koşu kökeni kaydedilmiyor | B | — | R12 W11 | açık |
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
| E63 | Ajan bilgisinin bütün müşterilerden öğrenilmesi: beceri ve organlar, promptlar, puanlar; terfi, gölge denemesi, bağlamla taşıma, gizlilik ve toplu anonim puan | B | operatör yönü | operatör, 2026-10-29 | açık (çok repo ile, `21`, `21a`) |
| E64 | Prova yargıcı dersin içinde gizli aile etiketini arıyor; kör bir beyin geçemez, getirme hiç sınanmıyor | K | — | e2e-7 L1 | açık |
| E65 | Ders verme/saklama deneyini beynin kendisi yapıyor; kollar eşit mi denetlenmiyor (işe yaramaz ders %100 kredi alıyor) | K | — | e2e-7 L2 | açık |
| E66 | Ders başına canlı kredi neredeyse hiç ölçülemiyor; boş derslerin ~%10'u geçiyor | B | evet (18b) | e2e-7 L3 | açık |
| E67 | Bildirim ödülü 'kusur ekle, sonra bildir' tuzağı kuruyor; kendi soyundan gelen kusura kredi yok, kök neden başına tek kredi | K | evet (E53'ü biçimler) | e2e-7 L4 | açık |
| E68 | Kendini ayarlayan sınır kuralı sansürlü gözlemle merdiven gibi yükseliyor; sınıra takılan gözlem ölçüye girmemeli | K | evet (E55'i düzeltir) | e2e-7 L5 | açık |
| E69 | Kredi ve itibar yalnız birleşen işi sayıyor; kaçınmayı ve riskli alandan uzak durmayı ödüllendiriyor | B | — | e2e-7 L6 | açık |
| E70 | Sistemin öğrenip öğrenmediğini çürütebilecek zamanlanmış ölçüm yok; 'aynı hata'nın kimliği yok | B | — | e2e-7 L7 | açık |
| E71 | `cause` etiketi tek bir ekilmiş merge ile doğrulanıyor; yanlış etiket kalıcı, düzeltme satırı yok | B | — | e2e-7 L8 | açık |
| E72 | Çoklu karşılaştırma ve tekrarlı bakış yalnız held-out havuzda sayılıyor; boş organ ~%34 kabul alabilir | B | evet (19 anayasal) | e2e-7 L9 | açık |
| E73 | 'Hiç unutmaz' defterde doğru, davranışta değil: arşivlenen ders geri dönmüyor, arşiv blob'larının kalıcı yeri yok | B | — | e2e-7 L10 | açık |
| E74 | Serbest metin dersler kalıcı prompt enjeksiyonu yolu (hafıza zehirlenmesi), geri çekmesi pratikte yok | B | evet (katalog) | e2e-7 L11 | açık |
| E75 | İtibar karşılaştırmaları karışık (zor işler önce sıradakine) ve zaman/model değişimini hesaba katmıyor | B | — | e2e-7 L12 | açık |
| E76 | Aşama 0 ilk gerçek döngüden önce bütün hakemi kuruyor; gerçek değer Aşama 4-6'da; ilk kabule ulaşamama riski | K | evet (yol haritası) | e2e-8 G1 | açık |
| E77 | Çok dilli, veritabanlı monorepo için birim ve çalışma ortamı modeli yok (profilde units, services, env imajı yok) | K | evet (Y3 ifadesi) | e2e-8 G2 | açık |
| E78 | Hedefin dondurulmuş kopyası: insan düzeltmesi gelmez, ölçüm havuzu dolmaz, kabul edilen düzeltmenin orijinale yolu yok | B | evet | e2e-8 G3 | açık |
| E79 | Kurucu'nun dört görevi ölçülmüyor: dürüstlük provası (çelişen vektör, ekilmiş açık, teyit) gerekli | K | evet (bütçe) | e2e-8 G4 | açık |
| E80 | Hazır bir ajana karşı taban yok; 'en iyi sistem' iddiası ölçülemez | B | evet (bütçe) | e2e-8 G5 | açık |
| E81 | Asıl hedeflerin metriği yok: birim notu (en zayıf boyut) ve gizlilik kanaryası | B | — | e2e-8 G6 | açık |
| E82 | Aşama 1-3 zayıf hedef testlerine oracle olarak güveniyor; hunk kapsaması ve mutant öldürme Aşama 4'te açılıyor | B | — | e2e-8 G7 | açık |
| E83 | Tenant ve BOLA açıkları için veri akışı aracı yok; lisans mantığı tutarsız (özel CLI içeride, LGPL araçlar dışarıda) | B | evet (lisans) | e2e-8 G8 | açık |
| E84 | Kendini geliştirme tek soylu açgözlü arama; arşiv ve popülasyon araması yok | B | evet (bütçe payı) | e2e-8 G9 | açık |
| E85 | Model değişiminde yeniden yeterlilik protokolü yok; bütün seatler tek aileden | B | evet | e2e-8 G10 | açık |
| E86 | Rekor erişilebilirliği sert durma; tek operatör için aşırı | B | evet | e2e-8 G11 | açık |
| E87 | Bağımlılık açıklarını kapatmak kalıcı yasak (Y3); en sık açık sınıfı bulunur ama kapatılamaz | S | evet (Y3) | e2e-8 G12 | açık |
| E62 | Filo genelinde güvenlik: bir repoda doğrulanan açık dedektöre dönüşür, gizlilik duvarından geçer, bağlı bütün repolarda taranır; her repoya yalnız kendi açığı bildirilir | B | operatör yönü | operatör, 2026-10-29 | açık (çok repo ile, `21`) |
| E60 | Satış zamanı: sistemin ürettiği dosyaların yeri; varsayılan müşteride, açık izinle müşteri başına ayrı, özel, şifreli barındırma; güvenlik bulguları hep müşteride | satış | operatör sorusu | operatör, 2026-10-29 | satışta açılır |
| E61 | Satış zamanı: repolar arası öğrenmede gizlilik duvarı; kalıp taşınır, müşteri bilgisi taşınmaz; terfi öncesi otomatik sızıntı kontrolü ve sözleşmede izin | satış | operatör sorusu | operatör, 2026-10-29 | satışta açılır |
| E59 | Satış zamanı: üyelik bitince sistemin müşteride oluşturduğu her şey silinir (kabul edilmiş kod hariç), silme makbuzu verilir | satış | operatör yönü | operatör, 2026-10-29 | satışta açılır |
| E58 | Hedeften iz bırakmadan çıkış: sistemin her şeyi tek klasörde (`.brain/`, yetim `brain/state` dalı); çıkış prosedürü yazılı değil ve denenmiyor | B | operatör yönü | operatör, 2026-10-29 | açık |
| E57 | Bağımsız güvenlik avcısı: Kurucu'dan ve rakipten ayrı, salt okunur, kanıtla bildiren, hakemi, beyni ve hedefleri tarayan, kanaryalarla ölçülen organ | K | operatör yönü | operatör, 2026-10-29 | spec yazıldı (`30f`) · kod açık |
| E56 | Güvenlik birinci sınıf: zafiyet kataloğu, hedef repoya özel güvenlik kuralları ve testleri, zincirli güvenlik defteri, güvenlikten öğrenme | K | operatör yönü | operatör, 2026-10-29 | spec yazıldı (`30`–`30e`), defter 8 satır ve testi · kod açık |
| E55 | Sınırlar kendini ayarlar: işletim sınırları ölçüme dayalı ve operatörün bandı içinde; ekonomik sınırlar operatörde; güvenlik yasaları sabit | K | operatör yönü | operatör, 2026-10-29 | açık (parti 3, E18 ile) |
| E54 | Ortak kader ve sürekli iletişim: Kurucu, hakem (rakibiyle) ve beyin birbirinde gördüğü eksiği tek bir zincirli bildirim kanalına yazar, her koşuda okur; hakem kendi zayıflığını da bildirir; ölçülür | K | operatör yönü | operatör, 2026-10-29 | açık (E53 ile tek mekanizma, parti 2'den sonra) |
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
  geliştiricilerinin yerel kopyaları erişimimizde değildir; Rekor'a yalnız hash yazılır ve kalıcıdır; özel
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
