# Değişiklik Günlüğü — Aşama 1

Tarih: 2026-10-29
Okunma: bir sayfanın geçmişi aranırken
Çapa: git geçmişi ve zincirdeki spec hash satırları

- 2.2 (2026-11-23, E735; tohum dönemi AI, P1 çıkış dönemi): §1.10'un Sonnet düzeltmesi satırı çağrı başı anahtarlarını
  adlandırır (`constitutional.stage_params.fix_call_max_usd`, `fix_call_max_s`; sahip kararı (2026-11-23)); §1.13'te P3
  MF2'nin testi 59, yeni P3 MF3 sonda döngüsü ve kalkışı (test 60). Tohum teslimi bu sayfaları taşımaz (E180); bağlayan
  `tohum/18a` ve `tohum/26s`'dir, canlı beyindeki kopyayı Kurucu `tohum/02`'nin öncelik kuralıyla uzlaştırır.
- 2.2 (2026-11-20, E672, E673; sahip kararı): ilk dilim deterministiktir; §1.6'nın sırası MF1, MF2, MF3, MF5, MF6,
  sonra P2 ve P3, sonra MF4, MF7, MF8 (numaralar korunur); §1.13'te P1 MF8 bulgu yazıcısı (test 12), P1 MF9 izin
  listesi ve `accept` yazıcısı (test 55), P3 (eski MF8 ve düzeltme gidiş-dönüşü); §1.5 3 ve §1.13d hizalandı.
  Bağlayan `tohum/26h`'dir; canlı beyindeki kopyayı Kurucu `tohum/02`'nin öncelik kuralıyla uzlaştırır.
- 2.2 (2026-11-20, E656, E664): Aşama 1'de güvenlik avcısı yoktur, araç kullanan ilk çalışma-zamanı ajanıyla en geç
  Aşama 4'te gelir; P2'nin MF2'si (`agent.dispatch`, test 22) düştü (§1.4, §1.6, §1.10, §1.12, §1.13); §1.8'in kabul
  oranı ve canlı merge sayısı, §1.10'un Kurucu, çalışma-zamanı LLM ve rakip satırları `tohum/18a`'nın anahtarlarıyla.
  Tohum teslimi bu sayfaları taşımaz (E180); bağlayan `tohum/30f`, `26e` ve `18a`'dır, canlı beyindeki kopyayı Kurucu
  `tohum/02`'nin öncelik kuralıyla uzlaştırır.
- 2.2 (2026-11-05, E553): §1.10'un tohum rakibi satırı 15 USD'den 1000 USD'ye: sahibin kararı, rakip `claude` CLI
  aboneliğiyle koşar ve fren yalnız kaçak frenidir (`tohum/18a`, `asama-0/12`'deki ilke).
- 2.2 (2026-10-31, E317): §1.13'ün Aşama 2 satırı: ders provası Aşama 2'nin ilk partisidir, ders görünümünden önce, ve sahibin MVP sınavıdır (`tohum/22b`). Tohum teslimi bu sayfayı taşımaz (E180); bağlayan `tohum/03` ve `tohum/22b`'dir, canlı beyindeki kopyayı Kurucu `tohum/02`'nin öncelik kuralıyla uzlaştırır.
- 2.2 (2026-10-30, E246): §1.13b `dead-code` artık "çağıranı olmayan kod yoktur" demez: çağıranı olmayan her birim bildirilir, silinmesi `tohum/07a`'ya uyar (yarım iş silinmez). Tohum teslimi `spec/asama-*`'yı taşımaz (E180); canlı beyindeki kopyayı Kurucu `tohum/02`'nin öncelik kuralıyla uzlaştırır.
- 2.2 (2026-10-29, daraltma): Aşama 0'ın daraltılmasıyla (`asama-0/CHANGELOG`) hakem donuk değildir, yalnız aktarımla değişir: P1 (organ koşucusu, snapshot, vaka seti, harness, LLM yokluğu, `drift.check`, Gözcü, `operating{}` ayarı) Aşama 1 MF1'den önce, P2 (güvenlik gözlemi, `agent.dispatch`, avcı koltuğu) içeride, çıkış partisi (`exit.sample`, snapshot kanaryası, `spec.lint`) (A) ile (B) arasında (yeni §1.13; Aşama 0 2.2'nin §0.4–§0.7'si ve §0.8'in metrikleri §1.13a–§1.13e'ye taşındı). Push kabulü önyükleme hakemindedir; MF6'nın `accept` satırını döngünün `yaz`'ı yazar ve ilk organ merge'üdür. Çıkış (A) + aktarım + (B); `#kapsama-kaydi` (`hunk_covered`, `mutant_killed`) ve `#zayif-oracle` satırları; `#lint` ve `#lock` tohumun spec denetimi ve kilit çiftidir. Bütçe kaçak frenidir; oturum ve USD ölçüdür, abonelik penceresi (429) kesintidir.
- 2.2 (2026-10-29): iç kullanımda API anahtarı ve geçit yoktur (`tohum/CHANGELOG`): `llm.call` çağrısı `claude` CLI'siyle, çağrı başı tavan `--max-budget-usd`; `#belirtec` çağrı başı bütçedir, koşuya bağlı belirteç satışta gelir (§1.5, §1.8, §1.10).
- 2.2 (2026-10-28): yalnız oyuncu organları, sekiz mikro özellik; aday yayımlanır, hakem yoklar ve uygular; düzeltici araçsız tek çağrı; harita, sözleşme, itibar, ders enjeksiyonu, organ yaşam döngüsü, bisect ve `main` senkronu ilk okuyucularına taşındı; çıkışta en az bir canlı merge ve geri alma sınırının dürüst ifadesi. Sonra: özet getirdiği yetenekleri beyan eder, çıkış satırları `#kimlik` taşır; eksik zorunlu satırlar eklendi (bütçe belirteci, giden prompt taraması, lisans kapısı) ve öğrenmenin ham maddesini sınayan geri alma provası.
- 2.1 (2026-10-28): keşif tüm ihlaller ve taban; mandal; harita (a) ve kapsama; sözleşme; nöbetçi, bisect, şablonlu ders; kapı yeniden koşturur; kurulum istisnası ile hakem bileşenleri; kanarya kuralı; teslim listesi tamamlandı.
- 2.0 (2026-10-28): inceleme sonrası yeniden yazım: fark oracle'ı, `fix` aralığı, güvenlik yollarına
  dokunmama, SHADOW→ACTIVE dev sayılarıyla (N = 3), 72 saatlik pencere ve 3 haftalık takvim,
  sıralı mikro özellikler, tam teslim listesi, model ayrıklığı, üretilmiş sayfalar, doğruluk
  özellikleri bölümü, inşa-zamanı bütçesi.
- 1.0 (2026-10-28): bölüm başına sayfalar.
- 0.1–0.5 (2026-10-28): tek dosya taslak dönemi.
