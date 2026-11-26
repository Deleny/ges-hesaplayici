# GES fizibilite hesaplayıcının web arayüzü.
# Çalıştırmak için: .\venv\Scripts\streamlit.exe run app.py
import altair as alt
import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

from hesap import (KADEME1_FIYAT, KADEME2_FIYAT, KADEME_ESIGI_KWH, KW_BASI_MALIYET_TL,
                   PANEL_GUCU_W, hesapla)
from rapor import pdf_olustur, tl, virgul

# Grafikte kısa ay adları (telefonda uzun adlar kesiliyor)
KISA_AYLAR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
              "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]

# Renkler .streamlit/config.toml'daki temayla aynı
GUNES_SARISI = "#E3A008"
HUCRE_MAVISI = "#1E3F66"
GRI = "#A3ADB8"

# Aynı girdilerle tekrar hesaplanırsa PVGIS'e yeniden istek atılmasın
hesapla_onbellekli = st.cache_data(hesapla)


st.set_page_config(page_title="Çatı GES Hesaplayıcı")
# Streamlit'in sayfa üstündeki büyük boşluğunu küçült
st.html("<style>[data-testid='stMainBlockContainer'] { padding-top: 2.5rem; }</style>")
st.title("Çatı GES hesaplayıcı")
st.write("Haritada çatınızın yerine tıklayın ve aylık faturanızı girin. Kaç panel "
         "gerektiğini, kurulum maliyetini ve sistemin kendini kaç yılda ödeyeceğini görün.")

# --- Harita: tıklanan nokta konum olarak seçilir ---
if "konum" not in st.session_state:
    st.session_state.konum = None

# Fare tekerleği haritayı değil sayfayı kaydırsın; yakınlaştırma +/- tuşlarıyla
harita = folium.Map(location=[39.0, 35.0], zoom_start=6, tiles="OpenStreetMap",
                    scroll_wheel_zoom=False)

# İşaretçi ayrı bir katmanda: böylece tıklayınca harita baştan yüklenmez, yakınlaştırma korunur
isaret_katmani = folium.FeatureGroup(name="Seçilen konum")
if st.session_state.konum:
    folium.CircleMarker(
        location=st.session_state.konum,
        radius=9,
        color=HUCRE_MAVISI,
        weight=3,
        fill=True,
        fill_color=GUNES_SARISI,
        fill_opacity=1,
    ).add_to(isaret_katmani)

harita_sonucu = st_folium(
    harita,
    key="harita",
    height=320,
    use_container_width=True,
    feature_group_to_add=isaret_katmani,
    returned_objects=["last_clicked"],  # sadece tıklamada sayfa yenilensin
)

tiklanan = harita_sonucu.get("last_clicked") if harita_sonucu else None
if tiklanan:
    yeni_konum = (round(tiklanan["lat"], 4), round(tiklanan["lng"], 4))
    if yeni_konum != st.session_state.konum:
        st.session_state.konum = yeni_konum
        st.rerun()  # işaretçi hemen görünsün

# --- Girdiler ---
with st.form("girdiler"):
    sol, orta, sag = st.columns(3)
    fatura = sol.number_input("Aylık elektrik faturası (TL)", min_value=100, value=1500, step=100)
    cati = orta.number_input("Çatı alanı (m²)", min_value=5, value=40, step=5)
    kw_fiyat = sag.number_input(
        "Kurulum fiyatı (TL/kW)", min_value=1000, value=KW_BASI_MALIYET_TL, step=1000,
        help="Varsayılan değer yaklaşık piyasa fiyatıdır. Elinizde teklif varsa onun kW başı "
             "fiyatını girin.",
    )

    # Tuş pasifken nedeni hemen üstünde yazsın
    if st.session_state.konum:
        enlem, boylam = st.session_state.konum
        st.caption(f"Seçilen konum: {enlem:.4f}° K, {boylam:.4f}° D".replace(".", ","))
    else:
        st.caption("Hesaplamak için haritada çatınızın yerine tıklayın.")

    hesapla_tusu = st.form_submit_button(
        "Hesapla", type="primary", disabled=st.session_state.konum is None
    )

if hesapla_tusu:
    enlem, boylam = st.session_state.konum
    try:
        with st.spinner("PVGIS'ten güneş verisi alınıyor..."):
            s = hesapla_onbellekli(enlem, boylam, fatura, cati, kw_fiyat)
    except requests.RequestException:
        st.error("Bu konum için güneş verisi alınamadı. Nokta denizin üstündeyse karada "
                 "bir yer seçin; değilse internet bağlantınızı kontrol edin.")
        st.stop()

    if s["panel_sayisi"] == 0:
        st.error("Bu çatıya hiç panel sığmıyor. Çatı alanını büyütüp tekrar deneyin.")
        st.stop()

    st.subheader("Sonuç")
    # 2x2 düzen: dört sütunda büyük TL rakamları sığmıyor
    k1, k2 = st.columns(2)
    k3, k4 = st.columns(2)
    k1.metric("Geri ödeme süresi", f"{s['geri_odeme_yil']} yıl".replace(".", ","))
    k2.metric("Kurulum maliyeti", tl(s["maliyet"]))
    k3.metric("Yıllık tasarruf", tl(s["yillik_tasarruf"]))
    k4.metric(f"Sistem gücü ({s['panel_sayisi']} panel)", f"{s['kurulu_guc']} kW".replace(".", ","))

    if s["cati_yetersiz"]:
        st.warning("Çatı alanı tüketiminizin tamamını karşılamaya yetmiyor. "
                   "Hesap, çatıya sığan en fazla panel sayısıyla yapıldı.")

    # on_click="ignore": indirince sayfa yenilenmesin, sonuçlar ekranda kalsın
    st.download_button(
        "PDF rapor indir",
        data=pdf_olustur(enlem, boylam, fatura, cati, kw_fiyat, s),
        file_name="ges-fizibilite-raporu.pdf",
        mime="application/pdf",
        on_click="ignore",
    )

    st.subheader("Aylık üretim ve tüketim (kWh)")
    # Grafik için her satır bir ay + seri (Tüketim / Üretim) olacak şekilde düzenle
    tablo = pd.DataFrame({
        "Ay": KISA_AYLAR * 2,
        "Seri": ["Tüketim"] * 12 + ["Üretim"] * 12,
        "kWh": [s["aylik_tuketim"]] * 12 + s["aylik_uretim"],
    })
    grafik = alt.Chart(tablo).mark_bar().encode(
        x=alt.X("Ay:N", sort=KISA_AYLAR, title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("Seri:N", sort=["Tüketim", "Üretim"]),
        y=alt.Y("kWh:Q", title=None, scale=alt.Scale(domainMin=0)),  # eksen sıfırdan başlasın
        color=alt.Color("Seri:N", title=None, legend=alt.Legend(orient="bottom"),
                        scale=alt.Scale(domain=["Tüketim", "Üretim"], range=[GRI, GUNES_SARISI])),
        tooltip=["Ay", "Seri", "kWh"],
    )
    st.altair_chart(grafik, use_container_width=True)

    st.caption(
        f"Elektriği EPDK mesken kademeli tarifesiyle hesapladık: ayda ilk {KADEME_ESIGI_KWH} kWh "
        f"{virgul(KADEME1_FIYAT)} TL, fazlası {virgul(KADEME2_FIYAT)} TL (KDV hariç; fon, BTV ve "
        f"KDV ayrıca eklendi). Kurulumu {tl(kw_fiyat)}/kW, paneli {PANEL_GUCU_W} W "
        "aldık. Mahsuplaşma her ay ayrı yapıldığı için tüketiminizi aşan üretimi tasarrufa "
        "saymadık. Güneş verisi PVGIS'ten."
    )
