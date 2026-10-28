# Genesis: Organ Yazma, Ölçme, Kaldırma, Yeniden Yazma

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: yeni organ yazarken ve ablasyonda
Çapa: organ kaydı zinciri; ablasyon raporları; genesis-queue.jsonl

---

Genesis bir aşama değil, döngünün organ ekleme yoludur ve Aşama 1'den itibaren vardır: ilk
adapter ve ilk düzeltici de bu yoldan doğar. Aşamalar genesis'in hangi sınıfta ve hangi organ
türünde çalışabileceğini açar. Organ: adapter, dedektör, skill, ajan, memory türü, property,
harita adapter'ı, ders kümesi.

**Yaşam döngüsü.** Geçişler yalnız ölçümle olur ve zincire yazılır; eşik kuralları `policy.json`'da.

| Durum | Anlamı | Geçiş koşulu |
|---|---|---|
| DRAFT | Yazıldı, çekişme protokolünden geçiyor | Beş faz; oracle PASS |
| SHADOW | Canlıda koşuyor, ölçülüyor, hiçbir karara girmiyor | Dev setinde tabanı anlamlı geçer, clean'de sessiz, bütçe içinde; en az `shadow_min_runs` koşu (başlangıç 3) |
| ACTIVE | Çıktısı karara giriyor, merge kapısına gidebiliyor | Dev harness sayıları; itibar penceresi ACTIVE'den sonra dolar, önce değil |
| DEGRADED | Ölçülüyor, karara girmiyor | İtibar alt sınırı iki pencere eşik altı, ablasyon katkısı sıfır, kapsayıcılık ihlali |
| RETIRED | Dispatch dışı; tanımı ve geçmişi zincirde | İki yeniden yazımdan sonra da alt dilim ya da iki ablasyonda sıfır katkı |

SHADOW çıktılarının oracle sonuçları itibara sayılır; deneme süresi puan kazandırır, aksi hâlde
hiçbir organ ACTIVE'e ulaşamaz.

**Kabul.** Bir organ ancak eşli testte anlamlı kazanç (`19-olcum-istatistigi.md`) ya da aynı
isabette en az beşte bir daha düşük maliyet gösterirse kabul edilir. Tek koşuluk fark kabul
değildir.

**Gereklilik ablasyonla ölçülür.** Bir organın gerekliliği, onsuz harness'in ne kaybettiğidir.
Ölçü tek sayı değil bileşik skordur: recall, precision, değer / USD ve kapsama. Bedava organlar
her döngü, LLM organları rastgele yüzde yirmilik alt kümelerle ve aylık harcamanın en fazla
onda biriyle ablasyona girer. Katkısı yok görünen organ DEGRADED'e iner; iki ablasyonda üst
üste sıfır RETIRED demektir. Aynı döngüde birbiriyle örtüşen iki organ birlikte emekli edilmez;
biri gidince öteki yeniden ölçülür. "İleride lazım olur" gerekçe değildir.

**Yeniden yazım soyağacıdır.** Yeniden yazılan organ yeni kimliktir (yeni hash), `derived_from`
ile eskisine bağlıdır ve DRAFT'tan başlar; itibar tabanı zincir boyunca taşınır, yeniden yazım
eksiyi sıfırlamaz. "Bu ajan geçen yıl neydi, kaç kez yeniden yazıldı, her sürüm ne kadar
isabet etti" tek sorgudur.

**Sınırlar.** Genesis harness'i, yasaları, `policy.json`'un anayasal bölümünü, donmuş
koltukları ve kendi puanlayıcısını yazamaz. Bir pencerede üretilen taslak sayısı bütçeyle
sınırlıdır; taşma Gözcü'nün işaretidir, çünkü çok taslak çoğu zaman ölçülmemiş bir boşluğun
izidir. Tetikler `17-kas-buyutme-sinyalleri.md`'dedir.
