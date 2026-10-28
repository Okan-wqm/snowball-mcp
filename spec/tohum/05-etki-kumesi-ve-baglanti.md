# Etki Kümesi ve Bağlantı Kuralı

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: koda dokunmadan önce ve yeni organ tasarlarken
Çapa: repo haritası kenarları; organ başına tek başına koşu

---

**Etki kümesi kuralı.** İş yapan hiçbir ajan, dokunacağı dosyaların etki kümesini okumadan
yazamaz. Etki kümesi repo haritasından (`13-memory-ve-zincir.md`) gelir: bu dosyayı kim import
ediyor, hangi event'i üretiyor ya da tüketiyor, hangi tabloya yazıyor, hangi sözleşmenin ucu,
hangi güvenlik sınırının içinde, hangi bağımlılığa dayanıyor. Oracle, doğrulama kapsamını
profildeki etkilenen-test komutu artı etki kümesiyle kurar.

- Etki kümesinde testi olmayan bir kenar kapsama boşluğudur. Silme içeren değişikliklerde K2'den,
  diğerlerinde K5'ten itibaren böyle bir değişiklik `blocked`'dır.
- Graf aracı yalnız proje düzeyinde bağ veriyorsa etki kümesi proje düzeyindedir ve bu,
  kapsama haritasında "kaba" olarak işaretlenir; dosya düzeyi bağ ihtiyacı bir kas sinyalidir.
- Güvenlik sınırı kenarına dokunan değişiklik, hangi sınıf bulmuş olursa olsun K6'dır; K6 oracle'ı
  canlı değilse `blocked` kalır. Harita katmanı (c) gelene kadar güvenlik sınırını profildeki
  `security_paths` tanımlar. K6 canlı olana kadar güvenlik yollarına hiç dokunulmaz, biçimleyici
  ve `--fix` dahil (`04a` 10).
- Bağımlılık manifesti değişikliği K6'dır ve Y3 gereği `blocked`'dır; bağımlılık eklemek
  sistemin işi değildir.
- Derleme grafiğinin dışında kalan dizinlerdeki değişiklik, o dizin için profilde bir araç zinciri
  yoksa `blocked`'dır ve kapsama boşluğu sinyali üretir.

Bir yeri yaparken başka bir yeri bozmamanın ve bir güvenlik açığı açmamanın mekanizması budur;
ajanın dikkati değil.

**Bağlantı kuralı.** Organlar veriyle bağlanır, kodla değil. Her organın çıktısı bir sonrakinin
girdisidir ve her yazarın bir okuyucusu vardır; döngü böyle kapanır. Ama hiçbir organ bir
diğerinin kodunu import ederek bağlanmaz: her organ tek başına koşulabilir, ölçülebilir ve
değiştirilebilir. Kar topu katman katman büyür; bir katman ancak harness'te anlamlı bir sayı
oynatınca yapışır (Y5). Her şeyin her şeyi import ettiği bir sistemde hiçbir parça tek başına
ölçülemez ve hiçbir parça silinemez.

**Sözleşme önce.** Birlikte çalışan organlar arayüzü koddan önce `<state_root>/contracts/`
altında yazar; öneri referansla kabul ya da çürütülür, iki tarafın testi yeşil olunca donar. İlk
sözleşme Aşama 1'de adapter ile düzeltici arasındaki bulgu biçimidir.
