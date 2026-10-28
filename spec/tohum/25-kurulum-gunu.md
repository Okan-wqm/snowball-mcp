# Kurulum Günü: Operatörün Bir Kerelik İşi

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: ilk başlatmadan önce, bir kez
Çapa: kurulum kontrol listesi; hedef repo ruleset'leri; mühürlü depo

---

Döngü içinde insan yoktur; döngüden önce bir günlük insan işi vardır. Hepsi bir kerelik ve
hepsi listede; listede olmayan hiçbir şey sonradan insandan istenmez.

| # | İş | Neden |
|---|---|---|
| 1 | Beyin reposunu aç, beyin GitHub App'ini kur; App'in `workflows` izni yok | PR kendi kapısını düzenleyemesin |
| 2 | Hedef repoda `brain/integration` dalını aç; ruleset: yalnız merge kapısı yazar, zorla itme yok | Entegrasyon dalı insan merge'i istemez ama korumasız da değildir |
| 3 | Hedef repoda `brain/state` yetim dalını aç; ruleset: yalnız ekleme, CI doğrular | Zincir güvencesi |
| 4 | Org ruleset'iyle beyin reposundan SHA-pinli zorunlu iş akışını kapı olarak bağla | Kapı beynin dışından gelsin |
| 5 | Mühürlü depoyu aç (özel repo ya da CI gizli depolama); yalnız exit ve rotate işlerinin kimliği okuyabilsin | Held-out gizliliği; hedef repo herkese açık olabilir |
| 6 | Secret store: GitHub App anahtarı, model sağlayıcı kimliği (tercihen OIDC), HMAC mühür anahtarı | Ajan konteynerine hiçbiri girmez |
| 7 | Koşucuyu seç ve profile yaz; egress günlüğü ve konteyner özeti alınabildiğini bir koşuyla doğrula | Y10 kanıtı |
| 8 | `policy.json` anayasal bölümünü doldur: aylık tavan ve paylar, regresyon dondurma eşiği, döngü başına PR ve CI dakika tavanı, kill switch yeri | Operatörün tek döngü dışı kolu |
| 9 | Kill switch: bayrak dosyası + App kurulumunu askıya alma yolu + sağlayıcı harcama tavanı; üçünü bir kez dene | Durdurma hakkı |
| 10 | Beyni ilk kez başlat: `snowball init` profili üretir ve kanıtlar; Kurucu `tohum/00`'dan başlar | |

Kurulumdan sonra operatörün elinde yalnız `00a`'daki güçler kalır. Bu liste bir sayfadır ve
`profile.json`'daki `bootstrap_done` alanı her maddeye bir kanıt (ruleset kimliği, koşu
kimliği) bağlar; kanıtsız madde eksik sayılır ve beyin başlamaz.
