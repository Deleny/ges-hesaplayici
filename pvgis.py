# PVGIS'ten (Avrupa Birliği'nin ücretsiz güneş verisi servisi) aylık üretimi çeker.
import requests

PVGIS_ADRESI = "https://re.jrc.ec.europa.eu/api/v5_3/PVcalc"

AY_ADLARI = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
             "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def uretim_getir(enlem, boylam, guc_kw=1, kayip_yuzde=14):
    """Verilen konumdaki güneş sistemi için aylık ve yıllık üretimi (kWh) döndürür.

    guc_kw: sistemin kurulu gücü (kW)
    kayip_yuzde: kablo, evirici, kir vb. kayıpların toplamı (PVGIS varsayılanı %14)
    Panel açısı ve yönü PVGIS'e en verimli değerler olarak hesaplatılır.
    """
    parametreler = {
        "lat": enlem,
        "lon": boylam,
        "peakpower": guc_kw,
        "loss": kayip_yuzde,
        "optimalangles": 1,      # en verimli eğim ve yönü PVGIS bulsun
        "outputformat": "json",
    }
    cevap = requests.get(PVGIS_ADRESI, params=parametreler, timeout=30)
    cevap.raise_for_status()
    veri = cevap.json()

    aylik = [round(ay["E_m"]) for ay in veri["outputs"]["monthly"]["fixed"]]
    yillik = round(veri["outputs"]["totals"]["fixed"]["E_y"])
    egim = veri["inputs"]["mounting_system"]["fixed"]["slope"]["value"]
    yon = veri["inputs"]["mounting_system"]["fixed"]["azimuth"]["value"]

    return {"aylik": aylik, "yillik": yillik, "egim": egim, "yon": yon}


if __name__ == "__main__":
    # Deneme: Ankara, 1 kW'lık sistem
    sonuc = uretim_getir(39.93, 32.85)

    print(f"Panel eğimi: {sonuc['egim']}°, yönü: {sonuc['yon']}° (0 = tam güney)")
    print("Aylık üretim (1 kW için):")
    for ad, kwh in zip(AY_ADLARI, sonuc["aylik"]):
        print(f"  {ad:<8} {kwh:>4} kWh")
    print(f"Yıllık toplam: {sonuc['yillik']} kWh")
