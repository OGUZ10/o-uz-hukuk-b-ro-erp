
import streamlit as st
import pandas as pd
from database import get_connection
from utils import ai_asistan_yaniti


# 1. SİSTEM AYARLARI
st.set_page_config(page_title="G-ERP Pro v18.6", layout="wide", page_icon="⚖️")

# CSS ile buton ve arayüzü biraz daha profesyonel yapalım
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

conn = get_connection()

# 2. SESSION STATE
if 'giris_yapti' not in st.session_state:
    st.session_state.update({
        'giris_yapti': False,
        'rol': None,
        'ad_soyad': None,
        'kullanici_kod': None
    })

# 3. GİRİŞ FONKSİYONU
def login_ekrani():
    st.title("⚖️ G-ERP Hukuk Otomasyonu")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.container(border=True):
            st.subheader("Büro Girişi")
            kod = st.text_input("Cari Kod (TC/Vergi No)")
            sifre = st.text_input("Şifre", type="password")
            
            if st.button("Sisteme Gir"):
                # Test Girişi
                if kod == "admin" and sifre == "9999":
                    st.session_state.update({
                        'giris_yapti': True,
                        'ad_soyad': "Sistem Yöneticisi",
                        'rol': "avukat",
                        'kullanici_kod': "ADMIN01"
                    })
                    st.rerun()
                
                # DB Girişi
                elif conn:
                    try:
                        query = "SELECT ad_soyad, rol, cari_kod FROM cari_kartlar WHERE cari_kod=%s AND sifre=%s"
                        df = pd.read_sql_query(query, conn, params=(kod, sifre))
                        
                        if not df.empty:
                            row = df.iloc[0]
                            st.session_state.update({
                                'giris_yapti': True,
                                'ad_soyad': row['ad_soyad'],
                                'rol': str(row['rol']).lower(),
                                'kullanici_kod': row['cari_kod']
                            })
                            st.rerun()
                        else:
                            st.error("❌ Hatalı giriş bilgileri.")
                    except Exception as e:
                        st.error(f"Sistem Hatası: {e}")

    with col2:
        st.info("### 💡 Bilgilendirme\nSisteme erişim yetkiniz yoksa lütfen baro yöneticinizle iletişime geçin.")

# 4. ANA PROGRAM AKIŞI
if not st.session_state.giris_yapti:
    login_ekrani()
else:
    # Sidebar
    with st.sidebar:
        st.title(f"👤 {st.session_state.ad_soyad}")
        st.caption(f"Yetki Düzeyi: {st.session_state.rol.upper()}")
        st.divider()
        
        if st.button("Güvenli Çıkış"):
            st.session_state.giris_yapti = False
            st.rerun()

    # Sayfa Yönlendirmeleri (Dynamic Loading)
    if st.session_state.rol == "avukat":
        menu = st.sidebar.radio("Menü", 
            ["📊 Genel Bakış", "📂 Dosya Yönetimi", "💰 Kasa/Finans", "📅 Taksit Takip", "📄 Belge Sihirbazı"])
        
        try:
            if menu == "📊 Genel Bakış":
                from pages.dashboard import dashboard_sayfasi
                dashboard_sayfasi()
            elif menu == "📂 Dosya Yönetimi":
                from pages.davalar import davalar_sayfasi
                davalar_sayfasi()
            elif menu == "💰 Kasa/Finans":
                from pages.kasa import kasa_sayfasi
                kasa_sayfasi()
            elif menu == "📅 Taksit Takip":
                from pages.taksitler import taksit_sayfasi
                taksit_sayfasi()
            elif menu == "📄 Belge Sihirbazı":
                from pages.belge_sihirbazi import belge_sihirbazi_sayfasi
                belge_sihirbazi_sayfasi()
        except ModuleNotFoundError as e:
            st.error(f"Modül eksik: {e.name}. Lütfen dosya yolunu kontrol edin.")
            
    elif st.session_state.rol == "müvekkil":
        from pages.muvekkil_paneli import muvekkil_sayfasi
        muvekkil_sayfasi()
