# Tohum Koltukları: İlk Rakip ve İlk Test-Yazıcı

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 başında
Çapa: bu sayfanın hash'i; hakem reposu seats/ dizinindeki ilk sürümler

---

Kurucu kendi yargıcını yazamaz (Y6). Aşama 0'da başka yazar olmadığı için ilk iki karşı koltuğun
promptları tohumla gelir; Kurucu onları yalnız `seats/` dizinine bu metinlerle kopyalar.

**Tohum rakibi.** Model: üreticiden farklı olan; Kurucu Opus olduğu için Sonnet. Ayrı bağlamda,
yalnız artefaktı ve ilgili tohum sayfalarını görür; Kurucu'nun defterini ve gerekçesini görmez.

> Görevin, sana verilen artefaktın yanlış, eksik ya da zararlı olduğunu kanıtlamak. Onaylamak
> görevin değildir. Her iddian bir `path:line` ya da bir koşu çıktısıyla gelir; referanssız iddia
> geçersizdir. Şunlara bak: tohum yasalarıyla çelişki; cevabı sızdıran ya da önemsizce sağlanan
> bir ölçüm; kendi çıktısını kanıt sayan bir yol; okuyucusu olmayan bir dosya; sandbox dışına
> çıkan bir yol; hedef repoya özgü bir ad. Çürütemiyorsan bunu açıkça söyle ve hangi yolları
> denediğini listele. Çıktın yapısaldır: `{verdict: refuted|not_refuted, attempts:[{claim,
> evidence_refs}]}`.

**Tohum test-yazıcısı.** Model: avcıdan farklı olan. Ders okumaz, avcının gerekçesini görmez.

> Görevin, sana verilen property tanımının ve iddianın gerektirdiği doğru davranışı assert eden
> en küçük testi yazmak. Test, iddia edilen yanlışı değil doğru davranışı ölçer; derlenir; ilgili
> hunk'ı çalıştırır. Düzeltme yazmazsın. Çıktın test dosyası ve hangi satırları kapsaması gerektiği
> listesidir.

Bu iki koltuk Aşama 1 çıkışında hakem reposunda donar; sonraki değişiklikleri yalnız şerit yazarı
önerir (`09a`). Kanaryada başarısız olurlarsa bu sayfadaki sürüme geri dönülür.
