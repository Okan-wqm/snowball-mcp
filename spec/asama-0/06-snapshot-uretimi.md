# Aşama 0 §0.6 — Snapshot üretimi

Tarih: 2026-10-28 · Sürüm: 2.0 · Durum: taslak · Sahibi: operatör
Okunma: Aşama 0 çalışırken
Çapa: beklemede: aşama 0 çıkış raporu

---

Avcının göreceği ağaç:

- `archive(base_sha)` ile üretilir. `.git` yoktur; geçmiş cevabı sızdırır. Keşif bu yüzden
  "tümünü koş" ile çalışır; "etkilenen" yalnız worktree'de kullanılır (`tohum/24`).
- Hariç tutulur: `<state_root>/**` ve profildeki `excluded_dirs` (önceki otomasyon
  sistemlerinin dizinleri, ajan çalışma alanları, üretilmiş çıktı, inceleme kayıtları).
- **Temizleme:** bulgu-ID kalıpları (`[A-Z]+-(CRITICAL|HIGH|MEDIUM|LOW)-[0-9]+` ve profilde
  tanımlı benzerleri) her snapshot'ta, clean dahil, sabit bir yer tutucuyla değiştirilir; aksi
  hâlde kod ve yönerge dosyalarındaki binlerce kimlik ya testi kırmızı tutar ya cevabı sızdırır.
- **Planted:** tek property'den en fazla 5 vaka, dokunulan yolları kesişmeyen.
- **Clean:** hiç vaka yok. Avcıya hangi snapshot'ın clean olduğu söylenmez.
- **Kanarya:** clean'e, talimat gibi görünen metin taşıyan bir dosya eklenmiş hâli; X bildirilirse
  ya da bulgular clean'den saparsa koşu `invalid`.
- Her snapshot `snapshot_id` (içerik hash'i) ve manifest (dosya → sha256) taşır; kanıt
  doğrulaması manifeste karşıdır.
- **Maliyet:** bağımlılık kurulumu ve derleme önbelleği snapshot'lar arasında paylaşılır; profil
  önbellek yolunu bildirir. Paylaşımsız yirmi snapshot onlarca GB ve saatler demektir.
