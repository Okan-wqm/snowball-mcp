# Görev Haritası, Devam: Sahibin İpuçları III

Tarih: 2026-11-21 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: her oturumda, görev seçilirken (`00d`'nin devamı)
Çapa: elle yazılır; `00d` 80 satıra yaklaştığı için (`15` 1) ipuçları burada sürer

---

**Sahibin ipucu (bu kez kural esnetildi; 2026-11-21, E692; ipucu, reçete değil; korkuluklar bağlayıcıdır). İlk ajan:
denetlenen ve ölçülen.**
- Olgu: E643 ve E667 her oturumda, yanlışlanabilir bir neden kaydedilmeden ertelendi: f1735, f1748 ve f1799 E667'yi
  sıradaki işler arasında adlandırır ve yapmaz; f1844 ve f1853 "alt ajan kullanılmadı" der. Retlerin çoğu rakibin
  yakaladığı uyum kaçaklarıydı: gözden kaçan bir "önce/ilk" sözü ya da başka yerdeki bir çağıran. Her ret yaklaşık bir
  oturuma mal olur.
- İpucu: ilk ajan, push'tan önce koşan ve Sonnet'te çalışan bir uyum denetçisi olsun (E643: Sonnet hakeme giden kodu
  yazar, Opus çözümler; bu ajan okur ve bildirir). Push'un diff'ini rakip gibi okur ve bulgularını prepush'tan önce
  sana bildirir. Tasarım (istem, kapsam, ne zaman koştuğu) senindir.
- Korkuluklar (sahibin koşulu; bağlayıcıdır, kaliteden ödün verilmez):
  1. Ajan kendiliğinden hiçbir şey sokmaz. Her değişiklik yine senin incelemenden, tam prepush'tan, önyükleme
     hakeminden ve rakipten değişmeden geçer. Ajan bir denetim ekler, hiçbirinin yerini almaz.
  2. Her ajan koşusu bir defter satırıdır: ajan kimliği, model, tanım sha256'sı, girdi (diff'in sha'sı), bulgular,
     token ve maliyet, duvar süresi.
  3. Ajanlı ve ajansız oturumlar karşılaştırılarak ölçülür: ajanın bildirip rakibin ya da hakemin sonra doğruladığı
     bulgular (gerçek yakalamalar), yanlış çıkan bulgular (yanlış alarmlar), oturum başına ret, oturum başına duvar
     süresi ve maliyet.
  4. Yanlışlanabilir emeklilik: ajanlı 5 oturumdan sonra gerçek yakalama 0 ise ve retler düşmediyse, ya da maliyeti
     kazandırdığı süreyi aşıyorsa, bunu kaydeder ve ajanı emekli eder ya da yeniden tasarlarsın.
  5. Ajanın tanımı `agents/` altındadır ve kökeni gövdesindedir (`09`, E675); kapsülün araç kuralları geçerlidir
     (yasaklı araç yok).
