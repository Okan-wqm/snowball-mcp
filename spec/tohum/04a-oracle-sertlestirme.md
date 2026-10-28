# Oracle Sertleştirme: Test Yanlış Nedenle Yeşile Dönmesin

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: her oracle koşusunda ve test-yazıcı tasarlarken
Çapa: oracle koşu kayıtlarındaki 3/3 hash'leri ve mutant sonuçları

---

Yürütme oracle'ı sistemin son sözüdür; bu yüzden en çok burada oyun aranır. Şartlar:

1. **Test önce mühürlenir.** Test-yazıcının testi, düzeltici görmeden hash'lenir ve zincire
   yazılır. Düzeltici test yollarına yazamaz; yazarsa koşu geçersizdir.
2. **Kırmızı, başarısız assertion demektir.** Derlenmeyen kod, eksik sembol ya da import hatası
   kırmızı sayılmaz. Test snapshot'ta derlenmeli ve bir assertion'da düşmelidir.
3. **3/3 kırmızı, 3/3 yeşil.** Düzeltmeden önce üç koşu kırmızı, sonra üç koşu yeşil; önbellek
   kapalı, taze konteyner. Üçte biri bile sapıyorsa test flaky'dir ve bulgu `unresolved` olur.
4. **Mutant öldürme.** Test, düzeltilen hunk'ın en az bir mutantını (ters koşul, kaldırılmış
   satır, değiştirilmiş sabit) kırmızıya düşürmelidir; düşürmüyorsa test yanlış şeyi ölçüyordur.
5. **Etki kümesi testleri yeşil.** Profildeki etkilenen-test komutu artı etki kümesindeki
   projelerin test hedefleri; sıfır test koşması kırmızıdır.
6. **Düzeltme yapısal hedefe bağlı.** `required_change` serbest metin değil
   `{file, symbol, op}` yapısıdır; düzeltici yalnız o dosyalara yazar.
7. **Deterministik diff-guard.** Kapı, düzeltme diff'inde şunları reddeder: lint ve tip
   bastırma yorumları, `any` benzeri kaçışlar, `void` ile susturma, test atlama, yapılandırma
   düzenlemesi, bağımlılık manifesti değişikliği, tavanın üstünde net silme. Güvenlik yollarında
   yalnız biçimleyici ve operatörün izin listesindeki davranış koruyan kurallar çalışır.
8. **Niyet kanıtı.** Panelde "belgelenmiş niyet" savunması yalnız git blame yazarı beyin
   olmayan bir kaynağa dayanabilir; beynin merge ettiği bir yorum niyet kanıtı değildir.
9. **Oracle geçerliliği ölçülür.** Flake oranı ve TP düzeltmelerinin geri alınma oranı oracle
   takımının itibarıdır (`20-metrikler.md`).

Bu oracle insan etiketinden zayıftır: bir test yanlış şeyi ölçebilir. Bu şartlar zayıflığı
sınırlar, sıfırlamaz; rapor bunu açıkça yazar.
