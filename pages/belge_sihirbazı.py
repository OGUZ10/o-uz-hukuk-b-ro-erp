import streamlit as st
import pandas as pd
from database import get_connection
from datetime import datetime

def belge_sihirbazi_sayfasi():
    conn = get_connection()
    if not st.session_state.get('giris_yapti') or st.session_state.rol != "avukat":
        st.error("Yetkisiz erişim!")
        return

    st.title("📄 Akıllı Belge Sihirbazı")
    st.write("Veritabanındaki bilgilerle otomatik dilekçe ve form oluşturun.")

    # 1. Dosya Seçimi (Bilgileri buradaki dosya nosuna göre çekeceğiz)
    df_davalar = pd.read_sql_query("SELECT dosya_no FROM davalar", conn)
    secili_dosya = st.selectbox("Hangi dosya için belge hazırlanacak?", df_davalar['dosya_no'])

    if secili_dosya:
        # Seçilen dosyaya ait detayları çek
        query = "SELECT d.dosya_no, d.karsi_taraf, c.ad_soyad as muvekkil FROM davalar d JOIN cari_kartlar c ON d.muvekkil_kod = c.cari_kod WHERE d.dosya_no=%s"
        df_detay = pd.read_sql_query(query, conn, params=(secili_dosya,))
        
        if not df_detay.empty:
            detay = df_detay.iloc[0]
            
            st.divider()
            belge_tipi = st.selectbox("Belge Tipi Seçin", ["Vekaletname Sunma Dilekçesi", "İcra Takip Talebi", "Duruşma Mazeret Dilekçesi"])
            
            # ŞABLON OLUŞTURMA (Dinamik Metin)
            if belge_tipi == "Vekaletname Sunma Dilekçesi":
                taslak = f"""
                T.C. İSTANBUL NÖBETÇİ MAHKEMESİ'NE
                
                DOSYA NO: {detay['dosya_no']}
                
                DAVACI: {detay['muvekkil']}
                VEKİLİ: Av. {st.session_state.ad_soyad}
                DAVALI: {detay['karsi_taraf']}
                
                KONU: Vekaletname sunulması hakkındadır.
                
                AÇIKLAMALAR: Sayın mahkemenizin yukarıda numarası belirtilen dosyasında davacı {detay['muvekkil']} vekili olarak atanmış bulunmaktayız. Ekte sunduğumuz vekaletnamenin kabulü ile sistem üzerinden vekil kaydımızın yapılmasını saygılarımızla arz ve talep ederiz. {datetime.now().strftime('%d/%m/%Y')}
                
                Av. {st.session_state.ad_soyad}
                """
                
                st.text_area("Düzenlenebilir Belge Metni", taslak, height=300)
                st.download_button("Belgeyi TXT Olarak İndir", taslak, file_name=f"{secili_dosya}_dilekce.txt")

### 2. Adım: `app.py` İçine Bağla
`app.py` dosyasındaki Avukat menüsüne bu seçeneği ekle:

```python
    if st.session_state.rol == "avukat":
        menu = st.sidebar.selectbox("Menü", ["📊 Genel Bakış", "📂 Dosya Yönetimi", "💰 Kasa/Finans", "📄 Belge Sihirbazı"])
        
        # ... diğer elifler ...
        
        elif menu == "📄 Belge Sihirbazı":
            from pages.belge_sihirbazi import belge_sihirbazi_sayfasi
            belge_sihirbazi_sayfasi()
