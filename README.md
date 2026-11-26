# Çatı GES Hesaplayıcı

Bir çatıya kurulacak güneş enerjisi sisteminin (GES) ön fizibilitesini çıkaran web uygulaması.
Haritadan konumu seçip aylık elektrik faturasını ve çatı alanını giriyorsunuz; uygulama
kaç panel gerektiğini, kurulum maliyetini, yıllık tasarrufu ve geri ödeme süresini hesaplıyor.
Sonucu PDF rapor olarak da indirebiliyorsunuz.

## Nasıl hesaplıyor

1. **Tüketim:** Faturayı EPDK mesken kademeli tarifesine göre tersine çevirip aylık tüketimi (kWh) bulur.
2. **Güneş verisi:** Seçilen konum için PVGIS'ten 1 kW'lık sistemin aylık üretimini alır.
   Panel eğimi ve yönü en verimli değerlere göre PVGIS tarafından seçilir.
3. **Sistem boyutu:** Yıllık tüketimi karşılayacak panel sayısını bulur, çatıya sığan panel
   sayısıyla sınırlar (çatının %70'i kullanılabilir kabul edilir).
4. **Tasarruf:** Türkiye'de mahsuplaşma aylık yapıldığı için her ay "panelsiz fatura - panelli
   fatura" farkını hesaplar. Tüketimi aşan üretim tasarrufa sayılmaz.
5. **Geri ödeme:** Kurulum maliyetini yıllık tasarrufa böler.

## Veri kaynakları

| Veri | Kaynak |
|---|---|
| Aylık güneş üretimi | [PVGIS](https://re.jrc.ec.europa.eu/pvg_tools/) (Avrupa Komisyonu Ortak Araştırma Merkezi), ücretsiz API |
| Elektrik tarifesi | EPDK mesken kademeli tarifesi, 2026 2. çeyrek |
| Harita | OpenStreetMap |

## Varsayımlar

Değerler `hesap.py` dosyasının en üstünde durur, güncellemek için oradan değiştirilir.

| Değer | Varsayılan |
|---|---|
| Kademe eşiği | Aylık 240 kWh |
| Kademe 1 / Kademe 2 fiyatı | 2,92 / 4,32 TL/kWh (KDV hariç) |
| Vergiler | Enerji fonu %1, BTV %5, KDV %10 |
| Kurulum fiyatı | 40.000 TL/kW (arayüzden değiştirilebilir) |
| Panel | 550 W, 2,6 m² |
| Sistem kayıpları | %14 |

Sonuçlar ön fizibilite içindir; kesin teklif için yerinde keşif gerekir.

## Çalıştırma

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\streamlit.exe run app.py
```

Uygulama tarayıcıda `http://localhost:8501` adresinde açılır.

## Dosyalar

| Dosya | Görevi |
|---|---|
| `pvgis.py` | PVGIS'e istek atıp aylık üretimi çeker |
| `hesap.py` | Tarife, sistem boyutu, tasarruf ve geri ödeme hesabı |
| `rapor.py` | Sonucu PDF rapora çevirir |
| `app.py` | Streamlit arayüzü: harita, form, sonuç kartları, grafik |
| `.streamlit/config.toml` | Renk ve yazı tipi ayarları |
| `fonts/` | PDF'te Türkçe karakterler için Barlow yazı tipi (SIL Open Font License) |
