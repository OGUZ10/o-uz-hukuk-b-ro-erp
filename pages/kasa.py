import streamlit as st
import pandas as pd
from database import get_connection

def kasa_sayfasi(): # Bu isim app.py'deki import ile birebir aynı olmalı

    conn = get_connection()
    st.subheader("💰 Kasa ve Finans Yönetimi")
    
    # Kasa hareketlerini çek
    try:
        df_kasa = pd.read_sql_query("SELECT * FROM kasa ORDER BY id DESC LIMIT 10", conn)
        if not df_kasa.empty:
            st.table(df_kasa)
        else:
            st.info("Henüz kasa hareketi bulunmuyor.")
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")

if __name__ == "__main__":
    kasa_sayfasi()
