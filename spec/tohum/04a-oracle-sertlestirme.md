# Oracle Sertleştirme: Test Yanlış Nedenle Yeşile Dönmesin

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: her oracle koşusunda ve test-yazıcı tasarlarken
Çapa: beklemede: aşama 1 — oracle koşu kayıtları

---

Yürütme oracle'ı sistemin son sözüdür; bu yüzden en çok burada oyun aranır.

1. **Test önce mühürlenir.** Test-yazıcının testi, düzeltici görmeden hash'lenir ve zincire
   yazılır. Test yolları profildeki `test_path_rules`'dur ve satır içi test modüllerini de kapsar.
   Düzeltici test yollarına yazamaz.
2. **Test, property'den yazılır.** Test-yazıcı testi bulgunun iddiasından değil, property
   tanımından ve beklenen doğru davranıştan yazar; ders okumaz, avcının gerekçesini görmez.
3. **Kırmızı, başarısız assertion demektir.** Derlenmeyen kod, eksik sembol ya da import hatası
   kırmızı sayılmaz.
4. **3/3 kırmızı, 3/3 yeşil.** Önbellek kapalı, taze konteyner. Üçte biri bile sapıyorsa test
   flaky'dir; bulgu `unresolved` olur.
5. **Hunk kapsaması.** Yeşil koşuda test, düzeltilen hunk'ın satırlarını gerçekten çalıştırmış
   olmalıdır; satır kapsaması ölçülür. Projede test koşmuş olması yetmez.
6. **Mutant öldürme.** Test, düzeltilen hunk'ın en az bir mutantını kırmızıya düşürür. Mutantları
   hakemin kendi aracı üretir; hedef repoya bağımlılık eklenmez.
7. **Oracle kapsamı dar, kapı kapsamı geniş.** Oracle koşusu yalnız üreme testini ve hunk'ı
   kapsayan testleri koşar. Profildeki etkilenen-test komutunun tamamını merge anında kapı bir kez
   koşar; sıfır test koşması kırmızıdır.
8. **Yapısal hedef.** `required_change` bir dizidir (`26`); düzeltici yalnız o dosyalara yazar ve
   `op` sınıfa göre izinli küme içindedir.
9. **Deterministik diff-guard.** Kapı reddeder: profildeki dil başına `banned_constructs` (bastırma
   yorumları, tip kaçışları, susturma kalıpları, test atlama), `policy.json`'daki yasaklı ifadeler,
   yapılandırma ve manifest değişikliği, `.gitattributes`, tavanın üstünde **brüt** silme.
10. **Güvenlik yolları.** K6 oracle'ı canlı olana kadar güvenlik yollarına hiçbir yol dokunamaz,
    biçimleyici dahil. K6 canlı olunca yalnız K6 kapısından geçer.
11. **Niyet kanıtı.** Panelde "belgelenmiş niyet" savunması yalnız git blame yazarı beyin ya da
    hakem olmayan bir kaynağa dayanabilir.
12. **TP penceresi.** Hayatta kalma penceresinde geri alınan TP, geriye dönük FP sayılır.
13. **Oracle geçerliliği ölçülür.** Flake oranı ve TP düzeltmelerinin geri alınma oranı oracle
    takımının itibarıdır.

Bu oracle insan etiketinden zayıftır: bir test yanlış şeyi ölçebilir ve yanlış bir iddiayı
doğrulayan bir test de kırmızıdan yeşile döner. Bu şartlar zayıflığı sınırlar, sıfırlamaz;
rapor bunu açıkça yazar.
