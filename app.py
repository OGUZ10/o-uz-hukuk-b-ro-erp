
import streamlit as st
import pandas as pd
from database import get_connection
from utils import ai_asistan_yaniti

# 1. SİSTEM AYARLARI
st.set_page_config(page_title="G-ERP Pro v18.6", layout="wide")

# Veritabanı bağlantısını başlat
conn = get_connection()

# 2. SESSION STATE (Oturum Yönetimi)
if 'giris_yapti' not in st.session_state:
    st.session_state.giris_yapti = False
    st.session_state.rol = None
    st.session_state.ad_soyad = None
    st.session_state.kullanici_kod = None

# 3. GİRİŞ EKRANI
def login_ekrani():
    st.title("⚖️ G-ERP Hukuk Otomasyonu")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Büro Girişi")
        kod = st.text_input("Cari Kod (TC/Vergi No)", key="user_kod")
        sifre = st.text_input("Şifre", type="password", key="user_pass")
        
        if st.button("Sisteme Gir"):
            # --- ACİL GİRİŞ KONTROLÜ (Test için) ---
            if kod == "admin" and sifre == "9999":
                st.session_state.giris_yapti = True
                st.session_state.ad_soyad = "Sistem Yöneticisi"
                st.session_state.rol = "avukat"
                st.session_state.kullanici_kod = "ADMIN01"
                st.success("Yönetici girişi başarılı!")
                st.rerun()
            
            # --- VERİTABANI GİRİŞ KONTROLÜ ---
            elif conn:
                try:
                    query = "SELECT ad_soyad, rol, cari_kod FROM cari_kartlar WHERE cari_kod=%s AND sifre=%s"
                    df = pd.read_sql_query(query, conn, params=(kod, sifre))
                    
                    if not df.empty:
                        st.session_state.giris_yapti = True
                        st.session_state.ad_soyad = df.iloc[0]['ad_soyad']
                        st.session_state.rol = df.iloc[0]['rol'].lower()
                        st.session_state.kullanici_kod = df.iloc[0]['cari_kod']
                        st.rerun()
                    else:
                        st.error("Kod veya şifre hatalı!")
                except Exception as e:
                    st.error(f"Veritabanı hatası: {e}")
    
    with col2:
        st.info("💡 Not: İlk kez giriyorsanız Cari Kod: 'admin' ve Şifre: '9999' kullanarak sisteme erişebilirsiniz.")

# 4. ANA PROGRAM AKIŞI
if not st.session_state.giris_yapti:
    login_ekrani()
else:
    # Sidebar Ayarları
    st.sidebar.title(f"👤 {st.session_state.ad_soyad}")
    st.sidebar.info(f"Yetki: {st.session_state.rol.upper()}")
    
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.giris_yapti = False
        st.rerun()

    # Sayfa Yönlendirmeleri
    if st.session_state.rol == "avukat":
        menu = st.sidebar.selectbox("İşlem Seçin", 
            ["📊 Genel Bakış", "📂 Dosya Yönetimi", "💰 Kasa/Finans", "📅 Taksit Takip", "📄 Belge Sihirbazı"])
        
        if menu == "📊 Genel Bakış":
            from pages.dashboard import dashboard_sayfasi
            dashboard_sayfasi()
            
        elif menu == "📂 Dosya Yönetimi":
            from pages.davalar import davalar_sayfasi
            davalar_sayfasi()
            
        elif menu == "💰 Kasa/Finans":
            try:
                from pages.kasa import kasa_sayfasi
                kasa_sayfasi()
            except (ModuleNotFoundError, ImportError):
                st.error("⚠️ 'pages/kasa.py' dosyası bulunamadı. Lütfen GitHub'da dosya adını ve yolunu kontrol edin.")
            except Exception as e:
                st.error(f"❌ Kasa modülü yüklenirken bir hata oluştu: {e}")
        elif menu == "📅 Taksit Takip":
            from pages.taksitler import taksit_sayfasi
            taksit_sayfasi()
            
        elif menu == "📄 Belge Sihirbazı":
            try:
                from pages.belge_sihirbazi import belge_sihirbazi_sayfasi
                belge_sihirbazi_sayfasi()
            except ModuleNotFoundError:
                st.error("⚠️ 'pages/belge_sihirbazi.py' dosyası bulunamadı. Lütfen GitHub'da dosya adını kontrol edin.")
            except Exception as e:
                st.error(f"❌ Sihirbaz yüklenirken bir hata oluştu: {e}")




    elif st.session_state.rol == "müvekkil":
        from pages.muvekkil_paneli import muvekkil_sayfasi
        muvekkil_sayfasi()
