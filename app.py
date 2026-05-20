import streamlit as st
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import datetime
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="YAFT Kereste", page_icon="🌲")

# --- BAŞLIK ---
st.markdown("<h1 style='text-align: center; color: darkblue;'>YAFT İNŞAAT VE TİCARET A.Ş.</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Mobil Kereste Hesaplayıcı</h4>", unsafe_allow_html=True)

# --- FONT AYARLARI (WEB İÇİN GARANTİLİ) ---
def get_turkish_font():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, "DejaVuSans.ttf")
    font_name = "DejaVuSans"
    
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        return font_name 
    except Exception as e:
        st.error(f"🚨 Font Dosyası Bulunamadı!\nAranan Yer: {font_path}\nHata Detayı: {e}")
        return "Helvetica"

# --- HAFIZA ---
if 'veriler' not in st.session_state:
    st.session_state.veriler = []

# --- GİRİŞ ALANI ---
with st.container():
    st.write("---")
    
    islem = st.radio("İşlem Türü Seçin:", ["Normal (Ekle)", "İndirim (Çıkar)"], horizontal=True)
    
    agac_listesi = ["İnşaatlık", "Çam", "Meşe", "Kayın", "Gürgen", "Ladin", "Kavak", "Diğer"]
    secilen = st.selectbox("Ağaç Cinsi Seç:", agac_listesi)
    
    if secilen == "Diğer":
        cins = st.text_input("Diğer Cinsi Yazın:", value="")
    else:
        cins = secilen

    col1, col2 = st.columns(2)
    with col1:
        adet_giris = st.number_input("Adet", min_value=1, value=1, step=1)
        en = st.number_input("En (cm)", min_value=0.0, step=0.1)
    with col2:
        kalinlik = st.number_input("Kalınlık (cm)", min_value=0.0, step=0.1)
        boy = st.number_input("Boy (cm)", min_value=0.0, step=0.1)

    if st.button("HESAPLA VE LİSTEYE İŞLE", type="primary", use_container_width=True):
        if en > 0 and kalinlik > 0 and boy > 0:
            hacim_m3 = (adet_giris * en * kalinlik * boy) / 1000000
            if not cins: cins = "-"
            
            # YENİ MANTIK: İndirimde sadece hacim düşer, adet pozitif kalır
            if islem == "İndirim (Çıkar)":
                hacim_m3 = -hacim_m3
                islem_adi = "İndirim"
            else:
                islem_adi = "Normal"
            
            yeni_veri = {
                "İşlem": islem_adi,
                "Ağaç Cinsi": cins,
                "Adet": adet_giris,
                "En": en,
                "Kalınlık": kalinlik,
                "Boy": boy,
                "Hacim (m3)": hacim_m3
            }
            st.session_state.veriler.append(yeni_veri)
            st.success(f"Başarılı: {cins} - {islem_adi} işlemi eklendi!")
        else:
            st.error("Lütfen ölçüleri eksiksiz girin.")

# --- LİSTE VE PDF ---
if len(st.session_state.veriler) > 0:
    st.divider()
    df = pd.DataFrame(st.session_state.veriler)
    
    st.subheader("📋 Detaylı İşlem Listesi")
    df_ekran = df.copy()
    df_ekran["Hacim (m3)"] = df_ekran["Hacim (m3)"].apply(lambda x: round(x, 4))
    st.dataframe(df_ekran, use_container_width=True)
    
    st.divider()
    st.subheader("📊 Ağaç Türüne Göre Özet")
    
    # Gruplama işlemi (Adet normal toplanır, Hacim kendi içinde artı eksi toplanır)
    ozet_df = df.groupby("Ağaç Cinsi")[["Adet", "Hacim (m3)"]].sum().reset_index()
    ozet_df.columns = ["Ağaç Cinsi", "İşlem Gören Adet", "Toplam Hacim (m3)"]
    
    ozet_ekran = ozet_df.copy()
    ozet_ekran["Toplam Hacim (m3)"] = ozet_ekran["Toplam Hacim (m3)"].apply(lambda x: round(x, 4))
    st.dataframe(ozet_ekran, use_container_width=True)

    genel_toplam_m3 = df["Hacim (m3)"].sum()
    genel_toplam_adet = df["Adet"].sum()
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.info(f"**GENEL TOPLAM ADET:** {genel_toplam_adet}")
    with col_t2:
        st.info(f"**GENEL TOPLAM HACİM:** {genel_toplam_m3:.4f} m³")

    def create_pdf(dataframe, summary_df, total_adet, total_m3):
        buffer = io.BytesIO()
        tr_font = get_turkish_font()

        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        styles['Heading1'].fontName = tr_font
        styles['Heading4'].fontName = tr_font
        styles['Normal'].fontName = tr_font

        baslik_stili = ParagraphStyle('Baslik', parent=styles['Heading1'], fontName=tr_font, fontSize=18, textColor=colors.darkblue, alignment=TA_CENTER, spaceAfter=12)
        elements.append(Paragraph("YAFT İNŞAAT VE TİCARET A.Ş.", baslik_stili))
        elements.append(Spacer(1, 10))
        
        alt_baslik_stili = ParagraphStyle('AltBaslik', parent=styles['Normal'], fontName=tr_font, alignment=TA_CENTER)
        elements.append(Paragraph(f"Gelişmiş Kereste Dökümü - {datetime.datetime.now().strftime('%d.%m.%Y')}", alt_baslik_stili))
        elements.append(Spacer(1, 20))

        elements.append(Paragraph("Detaylı İşlem Listesi:", styles['Heading4']))
        elements.append(Spacer(1, 5))
        
        data = [['İşlem', 'Ağaç Cinsi', 'Adet', 'En', 'Kalınlık', 'Boy', 'Hacim (m3)']]
        for index, row in dataframe.iterrows():
            data.append([row['İşlem'], row['Ağaç Cinsi'], row['Adet'], row['En'], row['Kalınlık'], row['Boy'], f"{row['Hacim (m3)']:.4f}"])
        
        t = Table(data, colWidths=[55, 90, 45, 45, 55, 50, 70])
        style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), tr_font),
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.aliceblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ])
        t.setStyle(style)
        elements.append(t)
        
        elements.append(Spacer(1, 25))

        elements.append(Paragraph("ÖZET RAPOR (Türlere Göre Toplamlar):", styles['Heading4']))
        elements.append(Spacer(1, 5))

        summary_data = [['Ağaç Cinsi', 'İşlem Gören Adet', 'Toplam Hacim (m3)']]
        for index, row in summary_df.iterrows():
            summary_data.append([row['Ağaç Cinsi'], row['İşlem Gören Adet'], f"{row['Toplam Hacim (m3)']:.4f}"])
        
        summary_data.append(["GENEL TOPLAM:", str(total_adet), f"{total_m3:.4f}"])

        t_sum = Table(summary_data, colWidths=[150, 110, 150])
        style_sum = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), tr_font),
            ('BACKGROUND', (0, 0), (-1, 0), colors.firebrick),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), tr_font),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ])
        t_sum.setStyle(style_sum)
        elements.append(t_sum)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    pdf_bytes = create_pdf(df, ozet_df, genel_toplam_adet, genel_toplam_m3)
    st.download_button(label="📄 Gelişmiş PDF İNDİR", data=pdf_bytes, file_name=f"YAFT_Gelismiş_Kereste_{datetime.datetime.now().strftime('%Y-%m-%d')}.pdf", mime="application/pdf", type="secondary", use_container_width=True)
    
    if st.button("LİSTEYİ TEMİZLE", type="secondary", use_container_width=True):
        st.session_state.veriler = []
        st.rerun()