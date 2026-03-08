import streamlit as st
import pandas as pd
from database import get_connection

# 1. Veritabanı bağlantısını çek
conn = get_connection()
if conn is None:
        st.error("Veritabanına bağlanılamadı! Lütfen database.py ayarlarını kontrol edin.")
        st.stop()


def davalar_sayfasi():
    # 2. Yetki Kontrolü (Güvenlik için)
    if not st.session_state.get('giris_yapti') or st.session_state.get('rol') != 'avukat':
        st.error("⚠️ Bu sayfaya sadece Avukat yetkisiyle erişilebilir. Lütfen giriş yapın.")
        return

    st.header("📂 Dosya ve Dava Yönetimi")
    
    # --- YENİ DOSYA KAYDI FORMU ---
    st.subheader("➕ Yeni Dosya Kaydı")
    with st.form("yeni_dosya_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            d_no = st.text_input("Dosya No (Örn: 2024/100)")
            m_kod = st.text_input("Müvekkil Cari Kod (TC/Vergi)")
        with col2:
            k_taraf = st.text_input("Karşı Taraf")
            asama = st.slider("Süreç Aşaması (%)", 0, 100, 10)
        
        kaydet = st.form_submit_button("Dosyayı Veritabanına İşle")
        
        if kaydet:
            if d_no and m_kod:
                try:
                    with conn.cursor() as cur:
                        sorgu = "INSERT INTO davalar (dosya_no, muvekkil_kod, karsi_taraf, surec_asamasi) VALUES (%s, %s, %s, %s)"
                        cur.execute(sorgu, (d_no, m_kod, k_taraf, asama))
                        st.success(f"✅ {d_no} nolu dosya başarıyla kaydedildi.")
                        st.rerun() # Listeyi güncellemek için sayfayı yenile
                except Exception as e:
                    st.error(f"❌ Kayıt Hatası: {e}")
            else:
                st.warning("Lütfen Dosya No ve Müvekkil Kodunu doldurun.")

    # --- MEVCUT DOSYALARI LİSTELEME ---
    st.divider()
    st.subheader("📋 Kayıtlı Dosyalar")
    
    try:
        # Verileri çek
        df_davalar = pd.read_sql_query("SELECT dosya_no, muvekkil_kod, karsi_taraf, surec_asamasi FROM davalar ORDER BY id DESC", conn)
        
        if not df_davalar.empty:
            # Sütun isimlerini güzelleştirelim
            df_davalar.columns = ["Dosya No", "Müvekkil Kodu", "Karşı Taraf", "Aşama (%)"]
            st.dataframe(df_davalar, use_container_width=True, hide_index=True)
        else:
            st.info("Henüz kayıtlı dosya bulunmuyor.")
    except Exception as e:
        st.error(f"Veriler listelenirken hata oluştu: {e}")

# Sayfayı ana programda çağırabilmek için çalıştır
# pages/davalar.py dosyasının en son satırı:
if __name__ == "__main__":
    davalar_sayfasi()


