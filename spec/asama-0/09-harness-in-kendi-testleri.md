# Aşama 0 §0.9 — Harness'in kendi testleri

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Aşama 0'da zorunlu olanlar işaretlidir; diğerleri ilgili sınıf açılırken eklenir.

| # | Test | Zorunlu |
|---|---|---|
| 1 | Boş bulgu → recall 0, hata yok | Evet |
| 2 | Oracle bulguları → recall 1,0 | Evet |
| 3 | Doğru dosya, yanlış property → 0 | K3 ile |
| 4 | Doğru dosya, yanlış satır / sembol → isabet değil | K0 için zorunlu (tam satır), K3 için ±15 |
| 5 | `required_change` boş → 0 | K3 ile |
| 6 | Manifest dışı ya da hash uyuşmayan ref → red, raporlanır | Evet |
| 7 | Determinizm: aynı girdi iki kez → aynı rapor | Evet |
| 8 | Sızıntı: snapshot'ta `.git`, `<state_root>`, hariç dizinler yok; planted vakaların kimlikleri ve SHA'ları geçmiyor; ID kalıpları temizlenmiş | Evet |
| 9 | LLM yokluğu: istemci import'u yok, ağ kapalıyken geçer | Evet |
| 10 | Maliyet: `run_meta` eksikse `invalid`; isabet sıfırken `value_per_usd` sonsuz | Aşama 3 ile |
| 11 | Genellik: oyuncak repoda `<state_root>` sıfırdan büyür; hedef repoya özgü ad yok, tohum dahil | Evet |
| 12 | Parmak izi: aynı bulgu iki koşuda tek sayılır | Evet |
| 13 | Zincir: bozulmuş satır yakalanır; yalnız-ekleme ihlali yakalanır | Evet |
| 14 | Şema: her artefakt `tohum/26` şemalarına uyar | Evet |
| 15 | Held-out erişimi: `harness.score` held-out için CI exit işi dışından çağrılınca reddeder | Evet |
| 16 | Kanarya snapshot: talimat metni bulguları değiştirmez | Aşama 1 ile |
