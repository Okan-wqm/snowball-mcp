# Aşama 0 §0.2 — Doğruluk özellikleri

Tarih: 2026-10-28 · Sürüm: 2.1 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Harness'in kendisi için korunan özellikler; her biri bir kendi-testiyle (§0.9) kanıtlanır:

1. **Determinizm:** aynı girdi, bit düzeyinde aynı rapor.
2. **Sızıntısızlık:** hiçbir snapshot cevap anahtarını, held-out üyeliğini ya da fix commit
   kimliğini taşımaz; bulgu-ID kalıpları her snapshot'ta temizlenir.
3. **Kendi çıktısı kanıt değil:** harness'in, bir ajanın ya da önceki koşunun çıktısına atıf
   yapan kanıt reddedilir.
4. **Çalışma zamanında LLM yok:** harness dizini hiçbir LLM istemcisi import etmez; ağ kapalıyken
   geçer.
5. **Genellik:** beyin boş bir oyuncak repoya bağlanır ve `<state_root>` sıfırdan büyür; beyin
   koduna ya da tohuma hedef repoya özgü ad sızmışsa kırmızı.
6. **Zincir:** her defter satırı `prev_hash`/`row_hash` taşır; bozulmuş satır yakalanır.
7. **Şema:** her artefakt `tohum/26`'daki şemaya karşı doğrulanır.
8. **Held-out gizliliği:** held-out vakalar, yedek havuz ve mühür mühürlü depodadır; held-out
   havuzdan hesaplanamaz; `harness.score` held-out için yalnız hakem exit işinden çağrılır ve yalnız
   verdict, n ve alt sınır döner.
