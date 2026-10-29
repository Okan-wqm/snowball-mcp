# Kurucu kapsülü ve pilot başlatıcısı

Kurucu (`spec/tohum/24a`) yalnız bu kapsülde çalışır: operatörün GitHub girişi ve Claude yapılandırması içeri
girmez. Kapsülün kökü salt okunur, yetkileri düşürülmüş; beyin her oturumda bellekte taze klonlanır, GitHub tek
evidir. Sınırlar `seed/bootstrap/tests/test_founder_capsule.py`'de sabitlidir.

**Klasör.** Pilotun her şeyi tek klasördedir (varsayılan `F:\snowball-work`); silinince pilot iz bırakmaz:

| Yol | Ne |
|---|---|
| `snowball-founder.env` | `GITHUB_TOKEN` (yalnız beyin reposu, Contents: Read and write) ve `CLAUDE_CODE_OAUTH_TOKEN` (`claude setup-token`); operatör yazar, yalnız kapsül okur |
| `aquaculture_platform/` | hedef klonu, kapsüle salt okunur |
| `referee/` | hakemin son imzalı sonucu (`result.json`), Kurucu okur |
| `logs/` | oturum dökümleri (`stream-json`) |
| `pilot-log.md` | operatörün raporu: her döngüde push, hakem kararı, yeni defter satırları ve bildirimler |
| `STOP` | oluşturulursa başlatıcı o adımdan sonra durur |

**Çalıştırma** (operatörün `gh` girişi ve Docker gerekir):

```
python seed/founder/launch.py --cycles 3
```

Her döngü: hakemin son sonucunu indir → bir Kurucu oturumu → beyin değiştiyse hakemi tetikle ve bekle (zamanlayıcısı
çalışmıyor, E32) → `pilot-log.md`'ye yaz. Push'suz iki oturumda, zaman aşımında ya da `STOP` dosyasında durur.
`--budget-usd` bütçe değil, kaçak frenidir. Döngülerin değerlendirmesi (ne buldu, ne kaçırdı, öğrendi mi) repoda
`docs/pilot-gunlugu.md`'dedir; her döngüden sonra güncellenir.
