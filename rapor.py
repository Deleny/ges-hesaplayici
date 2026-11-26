# Hesap sonucunu indirilebilir bir PDF rapora çevirir.
from datetime import date
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from hesap import KADEME1_FIYAT, KADEME2_FIYAT, KADEME_ESIGI_KWH, PANEL_GUCU_W
from pvgis import AY_ADLARI

# Türkçe harfler (ş, ğ, ı, İ) için yazı tipini dosyadan yüklüyoruz
YAZI_TIPLERI = Path(__file__).parent / "fonts"
HUCRE_MAVISI = (30, 63, 102)
SOLUK = (100, 110, 120)


def virgul(sayi):
    """3.8 -> '3,8'"""
    return str(sayi).replace(".", ",")


def binlik(sayi):
    """12345 -> '12.345'"""
    return f"{sayi:,}".replace(",", ".")


def tl(sayi):
    """12345 -> '12.345 TL'"""
    return f"{binlik(sayi)} TL"


def pdf_olustur(enlem, boylam, fatura, cati, kw_fiyat, s):
    """Girdileri ve hesapla() sonucunu (s) alıp PDF dosyasını bayt olarak döndürür."""
    pdf = FPDF(format="A4")
    pdf.set_margins(20, 20, 20)
    pdf.add_page()
    pdf.add_font("Barlow", "", YAZI_TIPLERI / "Barlow-Regular.ttf")
    pdf.add_font("Barlow", "B", YAZI_TIPLERI / "Barlow-SemiBold.ttf")
    pdf.set_draw_color(190, 198, 205)  # tablo çizgileri soluk gri

    def baslik(metin, boyut=13):
        pdf.set_font("Barlow", "B", boyut)
        pdf.set_text_color(*HUCRE_MAVISI)
        pdf.cell(0, 9, metin, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Barlow", "", 11)

    def iki_sutunlu_tablo(satirlar):
        with pdf.table(col_widths=(60, 110), text_align=("LEFT", "LEFT"),
                       first_row_as_headings=False, line_height=7) as tablo:
            for etiket, deger in satirlar:
                satir = tablo.row()
                satir.cell(etiket)
                satir.cell(deger)
        pdf.ln(4)

    # Başlık
    baslik("Çatı GES fizibilite raporu", boyut=20)
    pdf.set_text_color(*SOLUK)
    pdf.cell(0, 6, f"Hazırlanma tarihi: {date.today():%d.%m.%Y}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # Girdiler
    baslik("Girdiler")
    iki_sutunlu_tablo([
        ("Konum", f"{virgul(f'{enlem:.4f}')}° K, {virgul(f'{boylam:.4f}')}° D"),
        ("Aylık elektrik faturası", tl(fatura)),
        ("Çatı alanı", f"{cati} m²"),
        ("Kurulum fiyatı", f"{tl(kw_fiyat)}/kW"),
    ])

    # Sonuç
    baslik("Sonuç")
    iki_sutunlu_tablo([
        ("Geri ödeme süresi", f"{virgul(s['geri_odeme_yil'])} yıl"),
        ("Kurulum maliyeti", tl(s["maliyet"])),
        ("Yıllık tasarruf", tl(s["yillik_tasarruf"])),
        ("Sistem gücü", f"{virgul(s['kurulu_guc'])} kW ({s['panel_sayisi']} panel x {PANEL_GUCU_W} W)"),
        ("Yıllık üretim", f"{binlik(s['yillik_uretim'])} kWh"),
        ("Yıllık tüketim", f"{binlik(s['yillik_tuketim'])} kWh"),
    ])
    if s["cati_yetersiz"]:
        pdf.multi_cell(0, 6, "Not: Çatı alanı tüketimin tamamını karşılamaya yetmiyor. Hesap, "
                             "çatıya sığan en fazla panel sayısıyla yapıldı.")
        pdf.ln(4)

    # Aylık tablo
    baslik("Aylık üretim ve tüketim (kWh)")
    with pdf.table(col_widths=(60, 55, 55), text_align=("LEFT", "RIGHT", "RIGHT"),
                   line_height=6.5) as tablo:
        tablo.row(["Ay", "Üretim", "Tüketim"])
        for ad, uretim in zip(AY_ADLARI, s["aylik_uretim"]):
            tablo.row([ad, binlik(uretim), binlik(s["aylik_tuketim"])])
    pdf.ln(6)

    # Varsayımlar
    pdf.set_font("Barlow", "", 9)
    pdf.set_text_color(*SOLUK)
    pdf.multi_cell(0, 5, (
        f"Elektrik, EPDK mesken kademeli tarifesiyle hesaplandı: ayda ilk {KADEME_ESIGI_KWH} kWh "
        f"{virgul(KADEME1_FIYAT)} TL, fazlası {virgul(KADEME2_FIYAT)} TL (KDV hariç; enerji fonu, "
        "BTV ve KDV ayrıca eklendi). Mahsuplaşma her ay ayrı yapıldığı için tüketimi aşan üretim "
        "tasarrufa sayılmadı. Güneş verisi PVGIS'ten (Avrupa Komisyonu Ortak Araştırma Merkezi) "
        "alındı. Sonuçlar ön fizibilite içindir; kesin teklif için yerinde keşif gerekir."
    ))

    return bytes(pdf.output())
