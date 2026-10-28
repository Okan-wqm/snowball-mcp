# Çok Repo: Ne Taşınır, Ne Taşınmaz

Tarih: 2026-10-28 · Sürüm: 1.0 · Durum: taslak · Sahibi: operatör
Okunma: beyin yeni bir repoya bağlanırken
Çapa: genellik kendi-testi; her repo için ayrı `<state_root>`

---

Beyin repo bilmez, repo öğrenir. Repo Rust ise kaslar Rust alanında, TypeScript ise TypeScript
alanında büyür. Aynı beyin farklı repolarda farklı organlar taşır.

## Repo tanıma, keşfin ilk adımıdır

Beyin bağlanınca önce araç zincirini kendisi çıkarır ve `profile.json`'a yazar: diller ve
oranları, derleyici, test koşucu, lint ve biçimleyici, "etkilenenleri test et" komutu, CI
sistemi, paket yöneticileri, güvenlik yolları. Tohum sayfalarındaki her kural komut adı yerine
profil alanına bakar; tohumda hedef repoya ait hiçbir yol, araç ya da karar belgesi adı geçmez
ve genellik testi bunu tohum için de denetler.

Derleme grafiğinin ya da test hedeflerinin dışında kalan her dizin bir kapsama boşluğudur.
Beyin bunu sessizce geçmez: kapsama haritasına "görülmüyor" yazar ve bu bir kas büyütme
sinyalidir.

## Hata sınıfları alan bağımsız, adapter'lar alan bağımlı

Lint, tip, ölü kod, sözleşme paritesi, mantık ve güvenlik sınıfları her dilde vardır. Her
sınıfın adapter'ı o dilin aracını sarar; beyin aracı bilmez, profilden okur ve sarıcıyı o araç
için üretir. Alan uzmanı ajanlar da profilden doğar: tohumda belirli bir çerçevenin adını taşıyan uzman yoktur, "profildeki
baskın çerçeve için uzman" vardır ve o uzman genesis'ten geçer.

## Taşınma kuralı

| Taşınır | Taşınmaz |
|---|---|
| Beyin kodu | Vakalar, held-out, mühür |
| Organ tanımları, yeni repoda DRAFT'tan başlar ve kanıtını orada toplar | Profil |
| Kaçırma nedeni kategorileri | İtibar |
| Dersler, hit/miss sayaçları sıfırlanmış, "başka repoda öğrenildi" etiketiyle | Harita, kapsama, defterler |

Bir repoda doğan tarif öbür repoda ancak ablasyonla gerekliliğini kanıtlarsa kalır.

## Kullanıcının dosyaları kullanıcının sisteminde

Repoya özgü her şey kullanıcının reposunda ya da kullanıcının mühürlü deposunda durur. Beynin
tarafında yalnız kod ve kök hash'lerin imzalı kaydı vardır. Beyin kaldırıldığında repo bütün
hafızasıyla kullanıcının elinde kalır; başka bir beyin aynı dosyalardan devam edebilir.
