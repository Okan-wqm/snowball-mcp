# Geri Dönüş ve Silme: Kimsenin İşi Kaybolmaz

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: koda ya da veriye dokunan her adayda; silen, birleştiren ya da veriyi yok eden adayda baştan sona
Çapa: beklemede: aşama 2 — silme adaylarının kapı kararları, sahibin onay kayıtları, geri almalar

---

**Sahibin kararı (2026-10-30).** Biri bir şeye başlamış, işe yaramadığı için duraklatmış olabilir;
Snowball onu silmez. Gerçekten aynı işi yapan parçaları mimari olarak birleştirip kopyaları
silebilir; ama biri bir şey geliştiriyorsa o silinmez. Bu sayfa bu kararı ve Y2'nin geri dönüş
yasasını kapının adaydan denetlediği kısıtlar olarak tek yerde tutar. Kısıt neyin tutması ve
kimin onaylaması gerektiğini söyler; yarım işi artıktan ayırmanın, kullanımı ölçmenin ve
kanıtlamanın yolunu sistem tasarlar. Kurallar hedefin kodu ve verisi içindir; sistemin kendi
organlarına Y4 ve `13`'ün emekliliği uygulanır.

**Geri dönüş önce gelir.** Her aday geri dönüş yolunu ve kanıtını adlandırır. Kodda yol, hakemin
merge'ü geri almasıdır (`07`): taban yeşildir, geçmiş yeniden yazılmaz (`01b`). Geri almanın
tamamen geri getiremediği her etki (veri, şema, ayrı dağıtılan bir tüketici) kendi geri dönüşünü
adımdan önce kanıtlar; kanıtlayamayan aday geçmez.

**Kullanılmıyor olmak ölü olmak değildir.** Çağıranı olmayan kod yarım kalmış ya da duraklatılmış
bir iş olabilir; K2'nin aracı kullanılmayanı bulur, silmeye karar vermez. Silme yalnız şu
kurallarla olur:

1. **Yarım ya da duraklatılmış iş silinmez,** yalnız kanıtıyla bildirilir. Kanıt yükü silendedir:
   kimsenin geliştirmediği kanıtlanmamış her birim yarım iş sayılır.
2. **Gerçekten aynı işi yapan parçalar birleştirilebilir.** Aynılık benzerlikle değil yürütmeyle
   kanıtlanır (Y8, `31`). Önce bütün çağıranlar kalan uygulamaya taşınır ve kopyanın davranışını
   sınayan testler onda yeşil koşar; kopya ayrı ve sonraki bir adayda, birleştirme hayatta kalma
   penceresini doldurunca silinir.
3. **Eskimiş artık yalnız sahibin onayladığı adayla silinir.** Artık, kimsenin geliştirmediği ve
   bir işin kopyası olmayan birimdir; 1'in kanıtı ile sahibin onayı birlikte gerekir.
4. **Emin olunamıyorsa tutulur ve bildirilir.** Kanıt eksik ya da çelişkiliyse silme yoktur.

**Sahibin onayı.** Hedefin sahibinin, adayın son hâline bağlı, kalıcı ve kurcalamaya dayanıklı
kaydıdır; hiçbir ajanın, rakibin ya da kapının kararı onun yerine geçmez. Onay beklenmez (Y8):
onay gerektiren aday sahibe bırakılır, döngü başka işle sürer; onaysız aday hiçbir zaman geçmez.

**Veriyi yok eden adım.** Kalıcı veriyi silen, üzerine yazan ya da bilgi kaybettirerek dönüştüren
her adım (temizleme işi dahil; sınıflaması `05`) sahibin onayını ve şunları taşır; kapı her
birini adaydan denetler:

- **Ayrı adımlar.** Veriyi kullanmayı bırakan adım ile yok eden adım ayrı adaylardadır;
  aralarındaki pencere adayda yazılıdır ve yok eden aday pencere dolmadan geçmez.
- **Önce geri getirilebilir.** Yok etmeden önce veri, önceki bir adayda yerinde geri getirilebilir
  kılınmıştır (arşiv ya da yumuşak silme) ve saklama süresi yazılıdır; kalıcı silme kendi adımıdır.
- **Denenmiş yedek.** Adımı kapsayan, geri yüklemesi provayla denenmiş, doğrulanmış bir yedek
  vardır. Sistem yedeği göremez: aday onu önkoşul olarak adlandırır, sahip doğrular.
- **Kuru koşu yalnız test kopyasında** (Y3); kopyanın gösteremedikleri (gerçek kayıtlar, kilit
  süreleri, üretime benzer bir provanın sonucu) adayda sahibin önkoşulu olarak yazılıdır.
- **Geri migration geri dönüş değildir:** şemayı geri getirir, kayıtları getirmez.

**Silme adayının taşıdıkları.** Her silme adayı, silinen her birim için 1–3'ten hangisiyle
silindiğini ve geri dönüşünü kanıtıyla taşır; türüne göre ayrıca:

| Silinen | Ayrıca |
|---|---|
| Kod: modül, dosya, export, test hedefi | Etki kümesinin testleri tabanda ve adayda yeşil (`05`); brüt silme tavanın içinde, istisnasız (`18a`) |
| API yüzeyi: şema alanı, uç, olay ya da yük alanı | Önce ayrı bir adayda tarihli kullanımdan kaldırma işareti (`23`); kaldırma o tarih geçince, ayrı dağıtılan her tüketicide sıfır kullanım kanıtı ve uyumluluk denetiminin çıktısıyla |
| Şema: tablo, kolon, tip, kısıt | Sistem yazmaz (Y3). Sahibe bildirdiği kaldırma aşamalıdır: önce o şemayı okuyan ve yazan kod kalmaz, sonra ayrı bir adımda şema daralır; veri şartları ona da uygulanır |
| Veri | Yukarıdaki beş şart ve sahibin onayı |

**Bildirmek silmek değildir.** Silinmeyen her birim, nedeni (1, onaysız 3 ya da 4) ve kanıtıyla
bulgu olarak kalır (`15`).
