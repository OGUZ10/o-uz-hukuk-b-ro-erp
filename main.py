import streamlit as st
import pandas as pd
import importlib
from database import get_connection

# --- 1. SİSTEM AYARLARI ---
st.set_page_config(page_title="G-ERP Pro v18.6", layout="wide", page_icon="⚖️")

# --- 2. DİNAMİK MENÜ YAPILANDIRMASI ---
# Format: "Menü Adı": ("dosya_yolu", "fonksiyon_adi", ["yetkili_roller"])
MENU_MAP = {
    "📊 Genel Bakış": ("pages.dashboard", "dashboard_sayfasi", ["avukat", "katip"]),
    "📂 Dosya Yönetimi": ("pages.davalar", "davalar_sayfasi", ["avukat", "katip"]),
    "💰 Kasa/Finans": ("pages.kasa", "kasa_sayfasi", ["avukat"]),
    "📅 Taksit Takip": ("pages.taksitler", "taksit_sayfasi", ["avukat", "katip"]),
    "📄 Belge Sihirbazı": ("pages.belge_sihirbazi", "belge_sihirbazi_sayfasi", ["avukat"]),
    "👤 Müvekkil Paneli": ("pages.muvekkil_paneli", "muvekkil_sayfasi", ["müvekkil"])
}

# --- 3. OTURUM YÖNETİMİ ---
if 'giris_yapti' not in st.session_state:
    st.session_state.update({
        'giris_yapti': False,
        'rol': None,
        'ad_soyad': None,
        'kullanici_kod': None
    })

def sayfa_yukle(secilen_menu):
    """Modülleri dinamik olarak import eder ve çalıştırır."""
    modul_yolu, fonksiyon_adi, _ = MENU_MAP[secilen_menu]
    try:
        modul = importlib.import_module(modul_yolu)
        sayfa_fonksiyonu = getattr(modul, fonksiyon_adi)
        sayfa_fonksiyonu()
    except ModuleNotFoundError:
        st.error(f"⚠️ `{modul_yolu}.py` dosyası bulunamadı. Lütfen dosya yolunu kontrol edin.")
    except Exception as e:
        st.error(f"❌ Modül yüklenirken hata oluştu: {e}")

# --- 4. GİRİŞ EKRANI ---
def login_ekrani():
    st.title("⚖️ G-ERP Hukuk Otomasyonu")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            kod = st.text_input("Cari Kod (TC/Vergi No)")
            sifre = st.text_input("Şifre", type="password")
            if st.button("Sisteme Gir"):
                # Önce Test Girişi Kontrolü
                if kod == "admin" and sifre == "9999":
                    st.session_state.update({'giris_yapti': True, 'ad_soyad': "Yönetici", 'rol': "avukat", 'kullanici_kod': "ADM01"})
                    st.rerun()
                # Veritabanı Kontrolü
                conn = get_connection()
                if conn:
                    query = "SELECT ad_soyad, rol, cari_kod FROM cari_kartlar WHERE cari_kod=%s AND sifre=%s"
                    df = pd.read_sql_query(query, conn, params=(kod, sifre))
                    if not df.empty:
                        st.session_state.update({
                            'giris_yapti': True,
                            'ad_soyad': df.iloc[0]['ad_soyad'],
                            'rol': df.iloc[0]['rol'].lower(),
                            'kullanici_kod': df.iloc[0]['cari_kod']
                        })
                        st.rerun()
                    else:
                        st.error("Hatalı kullanıcı kodu veya şifre!")

    with col2:
        st.info("💡 **Hızlı Erişim:** Deneme için `admin` / `9999` kullanabilirsiniz.")

# --- 5. ANA AKIŞ ---
if not st.session_state.giris_yapti:
    login_ekrani()
else:
    # Sidebar ve Profil
    with st.sidebar:
        st.subheader(f"👤 {st.session_state.ad_soyad}")
        st.caption(f"Yetki: {st.session_state.rol.upper()}")
        
        # Rol bazlı menü filtreleme
        kullanici_rolü = st.session_state.rol
        filtreli_menuler = [
            isim for isim, ayar in MENU_MAP.items() 
            if kullanici_rolü in ayar[2]
        ]
        
        secim = st.selectbox("Menü İşlemleri", filtreli_menuler)
        
        if st.button("Güvenli Çıkış"):
            st.session_state.giris_yapti = False
            st.rerun()

    # Sayfayı Çalıştır
    sayfa_yukle(secim)
