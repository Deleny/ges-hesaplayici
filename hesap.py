# Faturadan sistem boyutu, maliyet ve geri ödeme süresini hesaplar.
import math

from pvgis import AY_ADLARI, uretim_getir

# --- Varsayılan değerler (güncellendikçe buradan değiştirilir) ---
# Mesken kademeli tarifesi, EPDK 2026 2. çeyrek (KDV hariç TL/kWh)
KADEME_ESIGI_KWH = 240      # aylık ilk 240 kWh düşük fiyattan
KADEME1_FIYAT = 2.92        # eşiğe kadar olan kısım
KADEME2_FIYAT = 4.32        # eşiği aşan kısım
# Enerji fonu %1 ve BTV %5 enerji bedeline eklenir (1,06), KDV %10 hepsinin üstüne (1,10)
VERGI_CARPANI = 1.06 * 1.10

KW_BASI_MALIYET_TL = 40000  # çatı GES kurulumu, KDV dahil yaklaşık TL/kW
PANEL_GUCU_W = 550          # tek panelin gücü
PANEL_ALANI_M2 = 2.6        # tek panelin kapladığı alan
KULLANILABILIR_ORAN = 0.7   # çatının ne kadarına panel konabilir (baca, gölge, kenar boşlukları)


def fatura_hesapla(kwh):
    """Aylık tüketimden (kWh) vergiler dahil faturayı (TL) hesaplar."""
    enerji_bedeli = (KADEME1_FIYAT * min(kwh, KADEME_ESIGI_KWH)
                     + KADEME2_FIYAT * max(kwh - KADEME_ESIGI_KWH, 0))
    return enerji_bedeli * VERGI_CARPANI


def tuketim_bul(fatura_tl):
    """fatura_hesapla'nın tersi: faturadan aylık tüketimi (kWh) bulur."""
    enerji_bedeli = fatura_tl / VERGI_CARPANI
    esik_bedeli = KADEME1_FIYAT * KADEME_ESIGI_KWH  # ilk 240 kWh'nin bedeli
    if enerji_bedeli <= esik_bedeli:
        return enerji_bedeli / KADEME1_FIYAT
    return KADEME_ESIGI_KWH + (enerji_bedeli - esik_bedeli) / KADEME2_FIYAT


def hesapla(enlem, boylam, aylik_fatura_tl, cati_alani_m2, kw_basi_maliyet=KW_BASI_MALIYET_TL):
    # 1) Faturadan tüketimi bul
    aylik_tuketim = tuketim_bul(aylik_fatura_tl)
    yillik_tuketim = aylik_tuketim * 12

    # 2) Bu konumda 1 kW'lık sistem ne kadar üretiyor?
    uretim_1kw = uretim_getir(enlem, boylam)

    # 3) Tüketimi karşılamak için kaç panel gerekir, çatıya kaç panel sığar?
    gereken_kw = yillik_tuketim / uretim_1kw["yillik"]
    gereken_panel = math.ceil(gereken_kw * 1000 / PANEL_GUCU_W)
    sigan_panel = math.floor(cati_alani_m2 * KULLANILABILIR_ORAN / PANEL_ALANI_M2)
    panel_sayisi = min(gereken_panel, sigan_panel)
    kurulu_guc = panel_sayisi * PANEL_GUCU_W / 1000

    # 4) Sistemin aylık üretimi (1 kW değerini kurulu güçle çarp)
    aylik_uretim = [round(kwh * kurulu_guc) for kwh in uretim_1kw["aylik"]]

    # 5) Tasarruf: Türkiye'de mahsuplaşma aylık yapılır. Her ay fatura, tüketimden
    #    üretim düşülerek kalan kısım üzerinden kesilir. Fazla üretim hesaba katılmaz
    #    (temkinli hesap). Üretim önce pahalı 2. kademeden düşer, bu yüzden faturası
    #    yüksek olan daha çok tasarruf eder.
    aylik_tasarruf = [
        fatura_hesapla(aylik_tuketim) - fatura_hesapla(max(aylik_tuketim - uretim, 0))
        for uretim in aylik_uretim
    ]
    yillik_tasarruf = sum(aylik_tasarruf)

    # 6) Maliyet ve geri ödeme
    maliyet = kurulu_guc * kw_basi_maliyet
    geri_odeme_yil = maliyet / yillik_tasarruf if yillik_tasarruf > 0 else None

    return {
        "aylik_tuketim": round(aylik_tuketim),
        "yillik_tuketim": round(yillik_tuketim),
        "panel_sayisi": panel_sayisi,
        "cati_yetersiz": sigan_panel < gereken_panel,
        "kurulu_guc": kurulu_guc,
        "aylik_uretim": aylik_uretim,
        "yillik_uretim": sum(aylik_uretim),
        "maliyet": round(maliyet),
        "yillik_tasarruf": round(yillik_tasarruf),
        "geri_odeme_yil": round(geri_odeme_yil, 1) if geri_odeme_yil else None,
    }


if __name__ == "__main__":
    # Deneme: Ankara, aylık 1500 TL fatura, 40 m² çatı
    s = hesapla(39.93, 32.85, aylik_fatura_tl=1500, cati_alani_m2=40)

    print(f"Aylık tüketim:   {s['aylik_tuketim']} kWh  (yıllık {s['yillik_tuketim']} kWh)")
    print(f"Sistem:          {s['panel_sayisi']} panel x {PANEL_GUCU_W} W = {s['kurulu_guc']} kW")
    if s["cati_yetersiz"]:
        print("                 (çatı tüketimin tamamını karşılamaya yetmiyor)")
    print(f"Yıllık üretim:   {s['yillik_uretim']} kWh")
    print(f"Kurulum maliyeti: {s['maliyet']:,} TL")
    print(f"Yıllık tasarruf: {s['yillik_tasarruf']:,} TL")
    print(f"Geri ödeme:      {s['geri_odeme_yil']} yıl")
    print("\nAy        Üretim  Tüketim")
    for ad, uretim in zip(AY_ADLARI, s["aylik_uretim"]):
        print(f"  {ad:<8} {uretim:>5}  {s['aylik_tuketim']:>5}")
