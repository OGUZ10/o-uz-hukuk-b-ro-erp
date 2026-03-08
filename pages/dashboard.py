import streamlit as st
import pandas as pd
from database import get_connection
import plotly.express as px # Görsel grafikler için

def dashboard_sayfasi():
    conn = get_connection()
    if not st.session_state.get('giris_yapti') or st.session_state.rol != "avukat":
        st.error("Yetkisiz erişim!")
        return

    st.title("📊 Büro Genel Bakış Paneli")
    
    # --- 1. ÜST ÖZET METRİKLERİ ---
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Verileri çekelim
        dava_sayisi = pd.read_sql_query("SELECT COUNT(*) as count FROM davalar", conn).iloc[0]['count']
        kasa_gelir = pd.read_sql_query("SELECT SUM(miktar) FROM kasa WHERE islem_tipi='Gelir'", conn).iloc[0][0] or 0
        kasa_gider = pd.read_sql_query("SELECT SUM(miktar) FROM kasa WHERE islem_tipi='Gider'", conn).iloc[0][0] or 0
        bekleyen_taksit = pd.read_sql_query("SELECT SUM(miktar) FROM taksitler WHERE durum='Bekliyor'", conn).iloc[0][0] or 0

        col1.metric("Aktif Dosyalar", f"{dava_sayisi} Adet")
        col2.metric("Kasa Bakiyesi", f"{(kasa_gelir - kasa_gider):,.2f} TL")
        col3.metric("Tahsil Edilecek", f"{bekleyen_taksit:,.2f} TL", delta="Gelecek Nakit")
        col4.metric("Toplam Gelir", f"{kasa_gelir:,.2f} TL")
    except:
        st.warning("Veriler henüz tam yüklenmedi.")

    st.divider()

    # --- 2. GRAFİKLER VE LİSTELER ---
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("📈 Dosya Aşamaları Dağılımı")
        df_davalar = pd.read_sql_query("SELECT dosya_no, surec_asamasi FROM davalar", conn)
        if not df_davalar.empty:
            fig = px.bar(df_davalar, x='dosya_no', y='surec_asamasi', color='surec_asamasi', 
                         title="Dosyaların Yüzdelik İlerleme Durumu", labels={'surec_asamasi':'Aşama (%)'})
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("🚨 Yaklaşan Taksitler")
        query = """
            SELECT d.dosya_no, t.vade_tarihi, t.miktar 
            FROM taksitler t 
            JOIN davalar d ON t.dosya_id = d.id 
            WHERE t.durum='Bekliyor' ORDER BY t.vade_tarihi LIMIT 5
        """
        df_yaklasan = pd.read_sql_query(query, conn)
        if not df_yaklasan.empty:
            st.dataframe(df_yaklasan, hide_index=True)
        else:
            st.success("Yakın zamanda bekleyen ödeme yok.")

if __name__ == "__main__":
    dashboard_sayfasi()
