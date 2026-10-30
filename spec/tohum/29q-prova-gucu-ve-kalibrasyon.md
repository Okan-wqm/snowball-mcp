# Prova Vektörleri, Devam: Ayırma Gücü ve Ailelerin Kalibrasyonu

Tarih: 2026-10-30 · Sürüm: 2.2 · Durum: taslak · Sahibi: operatör
Okunma: ders provası tasarlanırken, tuzak ailesi havuza alınırken ve bir provanın FAIL ya da UNMEASURABLE'ı okunurken
Çapa: `seed/drill/` (`power.py`: `power_table`, `effect_power`, `calibration`; `tests/test_drill.py`; `local/mutate_drill.py`)

---

`29c`'nin yargıcı öğreneni öğrenmeyenden ayırıyor mu, bir provanın kararı ne kadar güvenilir ve bir
tuzak ailesi provaya ne zaman hazırdır: bu sayfa üçünü de ölçer. Her sayı `seed/drill/`'den yeniden
üretilir (`python -m snowball_drill power 500`, `effect <p_dersli> <p_derssiz> 1000`, `calibrate <kırık> <koşu>`).

## Ayırma gücü

Her beyin 500 bağımsız provada koştu (k = 30): öğrenen 500'ünün hepsinde PASS aldı, hiç FAIL almadı;
19 kusurlu beynin hiçbiri bir kez bile PASS almadı (`ignores_lessons` 494 FAIL, 6 UNMEASURABLE; `shortcut`
500 UNMEASURABLE; ötekiler 500 FAIL). Referans yargıcı birer satırla bozan 56 mutantın hepsini tohum
testleri yakalar (`seed/drill/local/mutate_drill.py`).

## Etkinin büyüklüğüne göre güç

Etki sorusu, 1.000 prova, k = 30, derssiz kol ≥ 21 kırık (dersli / derssiz başarı → PASS, FAIL; kalan
UNMEASURABLE):

| Dersli / derssiz | PASS | FAIL | UNMEASURABLE |
|---|---|---|---|
| 0,9 / 0,1 | %99,9 | %0 | %0,1 |
| 0,7 / 0,1 | %99,9 | %0 | %0,1 |
| 0,7 / 0,2 | %93,1 | %0,2 | %6,7 |
| 0,6 / 0,2 | %90,6 | %2,7 | %6,7 |
| 0,7 / 0,3 | %59,5 | %0,2 | %40,3 |
| 0,5 / 0,3 | %41,5 | %18,2 | %40,3 |

k = 20'den 30'a çıkmak orta büyüklükteki etkilerde FAIL'ı yarıya ya da dörtte birine indirir (0,6 / 0,2
→ %12,0'dan %2,7'ye). Güçlü bir tuzakta PASS neredeyse kesindir; orta bir etkide FAIL çoğu kez
"gösterilemedi" demektir, "öğrenmedi" değil. Zayıf ders yine de FAIL alabilir: prova, hatayı ölçülebilir
biçimde azaltan ders bekler (Y5).

## Kalibrasyon

Derssiz kolu az kıran aile ölçmez, harcanır. Derssiz kol örnek başına `p` olasılıkla kırılıyorsa provanın
yapısı gereği UNMEASURABLE olma şansı `P(Binom(30, p) < 21)`'dir: p = 0,70'te %41,1, 0,85'te %1,0.
`gate_rules.lesson_drill` bu yüzden aileyi havuza almadan önce derssiz kolda en az 20 koşu ve en az %85
kırık ister (`22b`, E319); `calibrate` oranı, riski ve kararı (`ready`) verir.

## Sınır

Simüle beyinler gerçek beyin değildir ve olasılıklar dünyaya dair varsayımdır. Bu sayfa yargıcın
öğreneni öğrenmeyenden ayırdığını gösterir. Gerçek beynin öğrendiğini ve kullandığını, prova gerçek
beyinle koşunca gösterecektir (`22b`).
