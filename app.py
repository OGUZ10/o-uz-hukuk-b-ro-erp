
import streamlit as st
from database import veritabani_kur, get_connection
import ui_components as ui
import psycopg2
import pandas as pd
from datetime import datetime, date
import uuid
from docx import Document
from io import BytesIO
import requests
import json
import os
from fpdf import FPDF
import urllib.parse
import pandas as pd
from datetime import timedelta
from database import get_connection  # database.py'den bağlantıyı çekiyoruz
from utils import ai_asistan_yaniti   # utils.py'den asistanı çekiyoruz


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

# 3. GİRİŞ EKRANI (Login)
def login_ekrani():
    st.title("⚖️ G-ERP Hukuk Otomasyonu")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Giriş Yap")
        kod = st.text_input("Cari Kod (TC/Vergi No)")
        sifre = st.text_input("Şifre", type="password")
        
        if st.button("Sisteme Gir"):
            if conn:
                query = "SELECT ad_soyad, rol, cari_kod FROM cari_kartlar WHERE cari_kod=%s AND sifre=%s"
                df = pd.read_sql_query(query, conn, params=(kod, sifre))
                
                if not df.empty:
                    st.session_state.giris_yapti = True
                    st.session_state.ad_soyad = df.iloc[0]['ad_soyad']
                    st.session_state.rol = df.iloc[0]['rol']
                    st.session_state.kullanici_kod = df.iloc[0]['cari_kod']
                    st.success(f"Hoş geldiniz, {st.session_state.ad_soyad}!")
                    st.rerun()
                else:
                    st.error("Kod veya şifre hatalı!")
    with col2:
        m_kod = st.text_input("Müvekkil Kodu", key="m_user")
        m_sifre = st.text_input("Müvekkil Şifre", type="password", key="m_pass")
        if st.button("Müvekkil Girişi Yap"):
            # Burada veritabanı kontrolü yapılmalı
            st.session_state.update({"oturum": True, "rol": "Müvekkil", "user_ad": "Müvekkil Kullanıcı", "user_kod": m_kod})
            st.rerun()      

# 4. ANA PROGRAM (Giriş Sonrası)
if not st.session_state.giris_yapti:
    login_ekrani()
else:
    # Üst Menü / SideBar
    st.sidebar.title(f"👤 {st.session_state.ad_soyad}")
    st.sidebar.info(f"Yetki: {st.session_state.rol.upper()}")
    
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.giris_yapti = False
        st.rerun()

    # --- ROL KONTROLÜ (AVUKAT / MÜVEKKİL AYRIMI) ---
    if st.session_state.rol == "avukat":
        st.header("👨‍base Yönetim Paneli (Avukat)")
        menu = st.sidebar.selectbox("İşlem Seçin", ["📊 Genel Bakış", "📂 Dosya Yönetimi", "💰 Kasa/Finans", "📄 Belge Sihirbazı","📅 Taksit Takip"])
        
        if menu == "📂 Dosya Yönetimi":
            # Sayfayı modül olarak içeri aktarıp çalıştırıyoruz
            from pages.davalar import davalar_sayfasi 
            davalar_sayfasi()

        if menu == "📊 Genel Bakış":
            from pages.dashboard import dashboard_sayfasi
            dashboard_sayfasi()
            #Burada tüm büronun verileri listelenecek.")
            # Diğer modüllerden (pages/...) fonksiyonlar buraya çağrılacak


        elif menu == "💰 Kasa/Finans":
            from pages.kasa import kasa_sayfasi # Yeni eklediğimiz sayfa
            kasa_sayfasi()
            
        elif menu == "📄 Belge Sihirbazı":
            from pages.belge_sihirbazi import belge_sihirbazi_sayfasi
            belge_sihirbazi_sayfasi()
            
        elif menu == "📅 Taksit Takip":
            from pages.taksitler import taksit_sayfasi
            taksit_sayfasi()

            
    elif st.session_state.rol == "müvekkil":
        st.header("📱 Müvekkil Bilgi Sistemi")
        st.write(f"Sayın {st.session_state.ad_soyad}, dosya durumunuzu aşağıdan takip edebilirsiniz.")
        
        # AI ASİSTAN (utils.py'den geliyor)
        st.subheader("🤖 AI Hukuk Asistanı")
        soru = st.text_input("Dosyam hakkında ne öğrenmek istersiniz? (Örn: Durum nedir?)")
        if soru:
            cevap = ai_asistan_yaniti(st.session_state.kullanici_kod, soru, conn)
            if cevap:
                st.chat_message("assistant").write(cevap)
            else:
                st.warning("Sorunuz anlaşılamadı. Lütfen 'durum' veya 'aşama' gibi kelimeler kullanın.")






# --- ASİSTAN VE WHATSAPP FONKSİYONLARI ---
def ai_asistan_yaniti(m_kod, mesaj, conn):
    anahtar = ["durum", "aşama", "ne oldu", "bilgi", "sonuç"]
    if any(k in mesaj.lower() for k in anahtar):
        try:
            # SQL Injection koruması için parametreli sorgu
            sorgu = "SELECT dosya_no, surec_asamasi FROM davalar WHERE muvekkil_kod=%s LIMIT 1"
            df = pd.read_sql_query(sorgu, conn, params=(m_kod,))
            if not df.empty:
                asama = df.iloc[0]['surec_asamasi']
                yorum = "İnceleme aşamasında." if asama < 50 else "Karar aşamasına yakın."
                return f"🤖 G-ERP ASİSTAN: {df.iloc[0]['dosya_no']} numaralı dosyanız şu an %{asama} aşamasında. {yorum}"
            return "🤖 G-ERP ASİSTAN: Kayıtlı dosyanız bulunamadı."
        except:
            return None
    return None

def borclu_whatsapp_linki(telefon, borclu, dosya_no, tutar, iban, banka):
    mesaj = (
        f"Sayın {borclu}, \n\n"
        f"{dosya_no} sayılı icra dosyanız kapsamında güncel borç bakiyeniz {tutar:,.2f} TL'dir. \n"
        f"Ödemenizi aşağıdaki hesaba yapmanızı rica ederiz: \n\n"
        f"🏦 {banka} \n"
        f"💳 IBAN: {iban} \n\n"
        f"Ödeme yaptıktan sonra dekont iletmeniz rica olunur."
    )
    return f"https://wa.me{telefon}?text={urllib.parse.quote(mesaj)}"




# 1. Başlangıç Ayarları
st.set_page_config(page_title="G-ERP Pro v18.6", layout="wide")
conn_sqlite = veritabani_kur() # Yerel DB'yi başlat

# 2. Oturum Durumu Kontrolü
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# 3. Akış Yönetimi
if not st.session_state.logged_in:
    # Giriş Paneli
    ui.login_ekrani(conn_sqlite)
else:
    # Ana Uygulama Paneli
    user = st.session_state.user
    st.sidebar.title(f"👤 {user['ad']}")
    st.sidebar.info(f"Yetki: {user['rol']}")
    
    # Menü Seçimi (Rolüne Göre)
    menü_listesi = ui.ROLLER.get(user['rol'], ["DASHBOARD"])
    secim = st.sidebar.radio("İşlem Menüsü", menü_listesi)
    
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.logged_in = False
        st.rerun()

    # Sayfa Yönlendirmeleri
    if secim == "📊 DASHBOARD":
        ui.dashboard_sayfası(conn_sqlite)
    elif secim == "⚖️ DAVA & İCRA":
        ui.dava_yonetim_sayfası(conn_sqlite)
    elif secim == "💰 FİNANS / KASA":
        ui.finans_sayfası(conn_sqlite)
    else:
        st.write(f"{secim} modülü yakında eklenecek...")

