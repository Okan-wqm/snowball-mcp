# İş Boyutu ve Gerçek Test

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: her mikro görevde ve her test yazarken
Çapa: profildeki CI erişilebilirlik denetimi; PR'daki kasıtlı bozma kaydı

---

**İş boyutu kuralı.** Bir aşama, çıkış testiyle ölçülebilecek kadar özellik içerir. İş birimi
mikro görevdir: tek oturumda biter, tek bir şeyi ekler ya da düzeltir, kendi gerçek testiyle
gelir. Her aşama spec'i mikro özelliklerini sırayla listeler; her biri kendi canlı koşusuyla
kapanır. Bitmeyen iş "devam ediyor" değil, yanlış boyutlanmıştır ve bölünür. Bir PR'da birden
fazla mekanizma gelmez.

**Gerçek test kuralı.** Bir test ancak üç şartı birden sağlıyorsa testtir:

1. **Kasıtlı bozma.** Değişiklik geri alındığında test kırmızıya döner ve bu PR'da gösterilir.
   Geri alındığında yeşil kalan test, test değildir.
2. **Canlı yol.** Test, mekanizmayı üretim kodunun çağırdığı yoldan çalıştırır; yardımcı
   fonksiyonu doğrudan çağırmaz. Yardımcıyı doğrudan çağıran suite, üretim yolu onu hiç
   çağırmasa da yeşil kalır.
3. **Erişilebilir hedef.** Test, CI'da bir şeyin gerçekten çalıştırdığı bir hedefte koşar. Beyin
   bunu her repoda profildeki CI tanımından doğrular; repoda böyle bir denetim yoksa beyin kendi
   erişilebilirlik denetimini `<state_root>` için kurar.

Mock yalnız dış dünya için kullanılır: ağ, LLM sağlayıcısı, saat. Organlar arasındaki dikişler
mock'lanmaz; onları aşama çıkışındaki tek canlı koşu test eder.

**Sıfır test, kırmızıdır.** Etkilenen bir projede hiç test koşmamışsa sonuç yeşil değil
kırmızıdır; atlanan suite, geçmiş suite sayılmaz.
