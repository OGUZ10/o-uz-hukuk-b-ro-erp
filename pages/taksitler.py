import streamlit as st
import pandas as pd
from database import get_connection
from datetime import datetime, timedelta

def taksit_sayfasi():
    st.header("📅 Taksit ve Ödeme Takip Sistemi")
    conn = get_connection()

    tab1, tab2, tab3 = st.tabs(["🔔 Ödeme Takvimi", "➕ Yeni Taksit Planı", "✅ Tahsilat Girişi"])

    with tab1:
        st.subheader("Yaklaşan ve Geciken Taksitler")
        if conn:
            try:
                # Taksitleri ve ilgili dava bilgilerini çekiyoruz
                query = """
                SELECT t.id, d.dosya_no, d.muvekkil_ad, t.vade_tarihi, t.taksit_tutari, t.durum
                FROM taksitler t
                JOIN davalar d ON t.dava_id = d.id
                WHERE t.durum != 'Ödendi'
                ORDER BY t.vade_tarihi ASC
                """
                df = pd.read_sql_query(query, conn)
                
                # Gecikenleri işaretlemek için basit bir renklendirme
                today = datetime.now().date()
                df['vade_tarihi'] = pd.to_datetime(df['vade_tarihi']).dt.date
                
                st.dataframe(
                    df,
                    column_config={
                        "vade_tarihi": st.column_config.DateColumn("Vade Tarihi"),
                        "taksit_tutari": st.column_config.NumberColumn("Tutar", format="%.2f ₺"),
                        "durum": "Durum"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            except:
                st.info("Görüntülenecek aktif taksit bulunmamaktadır.")

    with tab2:
        st.subheader("Borç Yapılandırma (Taksitlendirme)")
        with st.form("taksit_olusturma_formu"):
            # Mevcut davaları seçmek için liste çekelim
            try:
                davalar_df = pd.read_sql_query("SELECT id, dosya_no, muvekkil_ad FROM davalar", conn)
                dava_secenekleri = {f"{row['dosya_no']} - {row['muvekkil_ad']}": row['id'] for _, row in davalar_df.iterrows()}
                secilen_dava_metin = st.selectbox("İlgili Dosya", list(dava_secenekleri.keys()))
                dava_id = dava_secenekleri[secilen_dava_metin]
            except:
                st.error("Önce 'Dosya Yönetimi'nden bir dava açmalısınız.")
                dava_id = None

            col1, col2, col3 = st.columns(3)
            with col1:
                toplam_borc = st.number_input("Toplam Borç Tutarı", min_value=0.0)
            with col2:
                taksit_sayisi = st.number_input("Taksit Sayısı", min_value=1, max_value=48, value=1)
            with col3:
                baslangic_vadesi = st.date_input("İlk Taksit Vadesi")

            submit = st.form_submit_button("📅 Taksit Planını Oluştur")

            if submit and dava_id:
                try:
                    cursor = conn.cursor()
                    taksit_tutari = toplam_borc / taksit_sayisi
                    
                    for i in range(taksit_sayisi):
                        vade = baslangic_vadesi + timedelta(days=30 * i)
                        query = """
                        INSERT INTO taksitler (dava_id, vade_tarihi, taksit_tutari, durum) 
                        VALUES (%s, %s, %s, 'Bekliyor')
                        """
                        cursor.execute(query, (dava_id, vade, taksit_tutari))
                    
                    conn.commit()
                    st.success(f"{taksit_sayisi} adet taksit başarıyla oluşturuldu.")
                except Exception as e:
                    st.error(f"Hata: {e}")

    with tab3:
        st.subheader("Ödeme Al")
        taksit_id = st.text_input("Ödenen Taksit ID (Listeden bakınız)")
        if st.button("Ödemeyi Onayla"):
            if taksit_id:
                try:
                    cursor = conn.cursor()
                    # Taksidi güncelle
                    cursor.execute("UPDATE taksitler SET durum = 'Ödendi' WHERE id = %s", (taksit_id,))
                    # Kasa hareketlerine ekle (Otomatik entegrasyon)
                    cursor.execute("""
                        INSERT INTO kasa_hareketleri (tarih, tur, miktar, kategori, aciklama)
                        SELECT CURRENT_DATE, 'Gelir', taksit_tutari, 'Vekalet Ücreti', 'Taksit Tahsilatı'
                        FROM taksitler WHERE id = %s
                    """, (taksit_id,))
                    conn.commit()
                    st.success("Tahsilat başarıyla işlendi ve kasaya aktarıldı!")
                except Exception as e:
                    st.error(f"Hata: {e}")
