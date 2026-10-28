# Takım Kurma Kuralları

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: takım kurarken ve ajan önerirken
Çapa: ajan dosyalarındaki köken alanları; reputation.jsonl; contracts/

---

- **Birim çekişme protokolüdür** (`10-cekisme-protokolu.md`): üretici, Savcı, Savunma,
  Uygulayıcı temsilcisi ve oracle. Kurucu, kendi yazdığı hiçbir artefakt için koltuklardan
  birine oturamaz.
- **Ajan ancak ölçülmüş boşluk için doğar** (`17-kas-buyutme-sinyalleri.md`). Öneride boşluğun
  ölçümü, kapsam, başarının hangi sayıyla ölçüleceği ve hedef değer / USD yazar.
- **Ajan ölçülmüş katkısı yoksa emekli olur**; mekanizma itibar ve ablasyondur.
- **Her ajan koşu başına durumsuzdur.** En az araç, varsayılan salt okunur, yazma yalnız izole
  worktree'de. Kişisel hafıza yoktur (`16-hafiza-modeli.md`).
- **Ajan tanımları üretilmiş artefaktlardır.** Her ajan dosyası hangi boşluk için, hangi
  ölçümle, hangi aşamada doğduğunu ve kimlik hash'ini taşır; kökeni belirsiz ajan dosyası yoktur.
  Her ajanın kendi üretilmiş sayfası vardır (`15-dokumantasyon.md`).
- **Uzmanlık havuzu profilden doğar.** Sabit roller: harness ve ölçüm mühendisi, test ve CI
  mühendisi, ajan ve prompt yazarı, maliyet mühendisi, her artefakt için rakip ve yargıç. Alan
  uzmanları (dil, çerçeve, veri katmanı, kenar) tohumda adla geçmez; profildeki baskın
  teknolojiler için genesis'ten doğar ve ablasyonla kalır.
- **Model politikası.** Yüksek işler **Opus 5.5** (`claude-opus-5-5`): Kurucu, spec taslakçısı,
  planlayıcı, keşif basamağındaki avcı, K5 ve üstü implementer. Düşük işler **Sonnet 5.5**
  (`claude-sonnet-5-5`): test-yazıcı, oracle düzelticisi, K0–K2 düzelticisi, merdivenin alt
  basamakları, defter bakımı. En ucuz model `policy.json`'da adlandırılır ve yalnız panelin faz 1–2'si
  için izinlidir. Kimlikler `24`'tedir; bağımsızlık kuralı `09a`'dadır ve model politikasının
  üstündedir.
- **Takım boyutu aşama spec'inde yazar.** Aşama 0 için iki ajan: Kurucu ve tohum rakibi.
  Aşama 2 ve 3'te altı ya da yedi. Sayı bütçeyle sınırlıdır; her ajanın hangi sayıyı oynattığı
  çıkış raporunda yazar.
- **Anlaşma değil, çürütme.** İki ajanın aynı sonuca varması kanıt değildir. Bir artefakt ancak
  farklı modelden ve ayrı bağlamdan bir rakip onu çürütmeyi deneyip başaramadığında kabul edilir.
  Başarılı çürütme, kabul kadar değerli bir çıktıdır.
- **Sözleşmeyle bağlanır, konuşarak değil.** Ortak arayüz koddan önce `<state_root>/contracts/`
  altında yazılır; öneri referansla kabul ya da çürütülür, iki tarafın testi yeşil olunca donar.
- **Entegrasyon tek canlı koşudur.** Takımın ortak çıktısı harness'te uçtan uca, gerçek veriyle,
  tek koşuda ölçülür. Dikişleri birim testi değil, bu koşu bulur.
- **Ajana kalıp verilmez, soru verilir.** Avcıya "şunu ara" değil, "bu özellik nerede bozuluyor ve
  bir insanın ne değiştirmesi gerekir"; yargıca "kural tetiklendi mi" değil, "üründe birinin
  değiştirmesi gereken bir hata var mı ve kanıtı ne".
- **Olgunluk ölçümdür** (`23-yama-degil-mimari-cozum.md`).
