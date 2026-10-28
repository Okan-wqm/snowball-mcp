# Kurulum, İkinci Bölüm: Aşama 0 Çıkışında Etkinleştirme

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 PASS verdiğinde, bir kez
Çapa: mühürlü depodaki kurulum özeti, ikinci bölüm

---

Hedef repoya dokunan kurulum, Aşama 0'ın ürettiği araçlarla yapılır; bu yüzden ikinci bölümdür.

| # | İş | Neden |
|---|---|---|
| 1 | Hedef repoda `brain/state` yetim dalını aç; ruleset: yalnız PR, zorunlu yalnız-ekleme kontrolü, zorla itme ve atlama yok | Zincir güvencesi |
| 2 | `brain/integration` dalını aç; ruleset: yalnız hakem kapısı merge eder | Entegrasyon dalı korumalı |
| 3 | Hedef reponun `brain/integration` ve `brain/state` ruleset'lerine zorunlu durum kontrolünü ekle; kaynağı hakem App'i | Kapı oyuncunun dışından gelsin; kullanıcı hesabında da çalışır |
| 4 | Beyni çağıran `hunt-harness.yml`'yi hedef reponun varsayılan dalına kendin ekle; zamanlayıcı yalnız varsayılan dalda çalışır. İçeriği hakem reposunda sürümlüdür; hedef reponun kendi iş akışı denetimleri varsa gereken kayıtları da ekle | App'in `workflows` izni yok |
| 5 | Hedef reponun mevcut iş akışlarının `brain/*` dallarında sırla koşmadığını doğrula ya da dışla | Ajan yazımlı kod sırla koşmasın |
| 6 | Koşucuyu seç; egress günlüğü ve konteyner özeti alınabildiğini bir koşuyla doğrula | Y10 kanıtı |
| 7 | `snowball init` koştur: profil hakem işinde türetilir, `brain/state`'e PR ile girer | İlk profil |

Bu bölümün özeti de mühürlü depoya yazılır. Bundan sonra her döngü, kurulumun bozulmadığını
hakem kayma denetimiyle doğrular (`01b`); bozulmuşsa sistem sert durur ve yeniden başlatma
operatörün işidir. HMAC anahtarı takvime göre yenilenir; yenileme hakem rotate işinin işidir.
