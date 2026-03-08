import streamlit as st
import pandas as pd
from database import get_connection
from datetime import datetime

def kasa_sayfasi():
    conn = get_connection()
    if not st.session_state.get('giris_yapti') or st.session_state.rol != "avukat":
        st.error("Yetkisiz erişim!")
        return

    st.title("💰 Kasa ve Finans Yönetimi")
    
    # --- ÜST ÖZET KARTLARI ---
    col1, col2, col3 = st.columns(3)
    try:
        toplam_gelir = pd.read_sql_query("SELECT SUM(miktar) as total FROM kasa WHERE islem_tipi='Gelir'", conn).fillna(0).iloc[0]['total']
        toplam_gider = pd.read_sql_query("SELECT SUM(miktar) as total FROM kasa WHERE islem_tipi='Gider'", conn).fillna(0).iloc[0]['total']
        col1.metric("Toplam Gelir", f"{toplam_gelir:,.2f} TL")
        col2.metric("Toplam Gider", f"{toplam_gider:,.2f} TL", delta_color="inverse")
        col3.metric("Kasa Bakiye", f"{(toplam_gelir - toplam_gider):,.2f} TL")
    except:
        st.info("Henüz finansal veri bulunmuyor.")

    # --- YENİ İŞLEM EKLEME ---
    st.divider()
    with st.expander("➕ Yeni Kasa İşlemi Ekle"):
        with st.form("kasa_formu", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            islem = c1.selectbox("İşlem Tipi", ["Gelir", "Gider"])
            miktar = c2.number_input("Miktar (TL)", min_value=0.0, step=100.0)
            tarih = c3.date_input("İşlem Tarihi", datetime.now())
            aciklama = st.text_input("Açıklama (Örn: Dosya Masrafı, Vekalet Ücreti)")
            
            if st.form_submit_button("Kasaya İşle"):
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO kasa (islem_tipi, miktar, aciklama, tarih) VALUES (%s, %s, %s, %s)",
                                (islem, miktar, aciklama, tarih))
                    st.success("İşlem kaydedildi!")
                    st.rerun()

    # --- SON İŞLEMLER TABLOSU ---
    st.subheader("📑 Son Hareketler")
    df_kasa = pd.read_sql_query("SELECT tarih, islem_tipi, miktar, aciklama FROM kasa ORDER BY id DESC LIMIT 20", conn)
    if not df_kasa.empty:
        st.dataframe(df_kasa, use_container_width=True)

if __name__ == "__main__":
    kasa_sayfasi()
