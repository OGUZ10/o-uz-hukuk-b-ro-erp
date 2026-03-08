import streamlit as st
import pandas as pd
from database import get_connection
from datetime import datetime

def kasa_sayfasi():
    st.header("💰 Finans ve Kasa Yönetimi")
    conn = get_connection()

    # 1. ÖZET METRİKLER (KPIs)
    if conn:
        try:
            # Toplam Gelir/Gider Hesabı (Sorgular tablo yapınıza göre güncellenmelidir)
            df_kasa = pd.read_sql_query("SELECT tur, miktar FROM kasa_hareketleri", conn)
            toplam_gelir = df_kasa[df_kasa['tur'] == 'Gelir']['miktar'].sum()
            toplam_gider = df_kasa[df_kasa['tur'] == 'Gider']['miktar'].sum()
            net_durum = toplam_gelir - toplam_gider
        except:
            toplam_gelir, toplam_gider, net_durum = 0, 0, 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Toplam Tahsilat", f"{toplam_gelir:,.2f} ₺", delta_color="normal")
        m2.metric("Toplam Gider", f"{toplam_gider:,.2f} ₺", "-")
        m3.metric("Kasa Bakiyesi", f"{net_durum:,.2f} ₺", delta=f"{net_durum:,.2f} ₺")

    st.divider()

    # 2. İŞLEM TABLARI
    tab1, tab2 = st.tabs(["📊 Hareket Kayıtları", "💸 Yeni İşlem Ekle"])

    with tab1:
        st.subheader("Finansal Hareket Listesi")
        if conn:
            try:
                query = """
                SELECT tarih, aciklama, kategori, miktar, tur 
                FROM kasa_hareketleri 
                ORDER BY tarih DESC
                """
                df_liste = pd.read_sql_query(query, conn)
                
                # Tablo Görselleştirme
                st.dataframe(
                    df_liste,
                    column_config={
                        "tarih": st.column_config.DateColumn("İşlem Tarihi"),
                        "miktar": st.column_config.NumberColumn("Tutar", format="%.2f ₺"),
                        "tur": "Tür (Gelir/Gider)"
                    },
                    use_container_width=True,
                    hide_index=True
                )
            except:
                st.info("Henüz bir finansal hareket bulunmuyor.")

    with tab2:
        st.subheader("Gelir/Gider Girişi")
        with st.form("kasa_formu"):
            col1, col2 = st.columns(2)
            with col1:
                tarih = st.date_input("İşlem Tarihi")
                tur = st.selectbox("İşlem Türü", ["Gelir", "Gider"])
                miktar = st.number_input("Tutar (₺)", min_value=0.0, step=100.0)
            with col2:
                kategori = st.selectbox("Kategori", [
                    "Vekalet Ücreti", "Dosya Masrafı", "Yol/Yemek", "Kira/Aidat", "Personel", "Vergi/Sigorta", "Diğer"
                ])
                aciklama = st.text_input("Açıklama (Örn: 2024/15 Esas Avans)")
            
            submit = st.form_submit_button("💰 İşlemi Kaydet")

            if submit:
                if miktar > 0:
                    try:
                        cursor = conn.cursor()
                        query = "INSERT INTO kasa_hareketleri (tarih, tur, miktar, kategori, aciklama) VALUES (%s, %s, %s, %s, %s)"
                        cursor.execute(query, (tarih, tur, miktar, kategori, aciklama))
                        conn.commit()
                        st.success("İşlem başarıyla kaydedildi!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")
                else:
                    st.warning("Lütfen geçerli bir tutar girin.")
