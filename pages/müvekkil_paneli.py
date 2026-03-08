import streamlit as st
import pandas as pd
from database import get_connection

def muvekkil_sayfasi():
    # Müvekkil giriş yaptığında session_state'den gelen cari_kod kullanılır
    muvekkil_kod = st.session_state.kullanici_kod
    ad_soyad = st.session_state.ad_soyad
    
    st.header(f"👋 Hoş Geldiniz, {ad_soyad}")
    st.caption(f"Müvekkil Cari Kodu: {muvekkil_kod}")
    
    conn = get_connection()
    
    if not conn:
        st.error("Veritabanı bağlantısı kurulamadı.")
        return

    # 1. DOSYALARIM ÖZETİ
    tab1, tab2 = st.tabs(["📂 Davalarım ve Safahat", "💳 Ödemelerim ve Borç Durumu"])

    with tab1:
        st.subheader("Aktif Dava Dosyalarınız")
        try:
            # Sadece bu müvekkile ait davaları çek
            # Not: cari_kartlar ve davalar tablosu cari_kod üzerinden ilişkili olmalıdır
            query = """
            SELECT dosya_no, dava_turu, mahkeme, durum, acilis_tarihi, detaylar 
            FROM davalar 
            WHERE muvekkil_kod = %s
            """
            df_davalar = pd.read_sql_query(query, conn, params=(muvekkil_kod,))
            
            if not df_davalar.empty:
                for index, row in df_davalar.iterrows():
                    with st.expander(f"📌 {row['dosya_no']} - {row['dava_turu']}"):
                        c1, c2 = st.columns(2)
                        c1.write(f"**Mahkeme:** {row['mahkeme']}")
                        c1.write(f"**Açılış Tarihi:** {row['acilis_tarihi']}")
                        c2.write(f"**Durum:** :blue[{row['durum']}]")
                        st.info(f"**Son Güncelleme / Özet:**\n{row['detaylar']}")
            else:
                st.info("Sistemde kayıtlı aktif davanız bulunmamaktadır.")
        except Exception as e:
            st.error("Davalar yüklenirken bir hata oluştu.")

    with tab2:
        st.subheader("Ödeme Planı ve Geçmişi")
        try:
            # Müvekkilin taksitlerini çek
            query_taksit = """
            SELECT t.vade_tarihi, t.taksit_tutari, t.durum, d.dosya_no
            FROM taksitler t
            JOIN davalar d ON t.dava_id = d.id
            WHERE d.muvekkil_kod = %s
            ORDER BY t.vade_tarihi ASC
            """
            df_taksit = pd.read_sql_query(query_taksit, conn, params=(muvekkil_kod,))
            
            if not df_taksit.empty:
                # Toplam Borç Özeti
                toplam_borc = df_taksit[df_taksit['durum'] != 'Ödendi']['taksit_tutari'].sum()
                st.metric("Kalan Toplam Borç", f"{toplam_borc:,.2f} ₺")
                
                # Taksit Tablosu
                st.dataframe(
                    df_taksit,
                    column_config={
                        "vade_tarihi": st.column_config.DateColumn("Vade"),
                        "taksit_tutari": st.column_config.NumberColumn("Tutar", format="%.2f ₺"),
                        "durum": "Ödeme Durumu",
                        "dosya_no": "İlgili Dosya"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Tanımlanmış bir ödeme planınız bulunmuyor.")
        except Exception as e:
            st.error("Finansal bilgiler yüklenemedi.")

    # 3. AVUKATA NOT BIRAK (İsteğe Bağlı)
    st.divider()
    with st.expander("✉️ Avukatıma Mesaj Gönder"):
        mesaj = st.text_area("Mesajınız veya sorularınızı buraya yazabilirsiniz.")
        if st.button("Gönder"):
            st.success("Mesajınız başarıyla iletildi. (Simüle edildi)")
