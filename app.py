
import streamlit as st
from database import get_connection
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




# 1. SİSTEM AYARLARI (Sadece bir kez en üstte olmalı)
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
        st.subheader("Büro Girişi")
        kod = st.text_input("Cari Kod (TC/Vergi No)", key="l_kod")
        sifre = st.text_input("Şifre", type="password", key="l_sifre")
        
        if st.button("Sisteme Gir"):
            if conn:
                query = "SELECT ad_soyad, rol, cari_kod FROM cari_kartlar WHERE cari_kod=%s AND sifre=%s"
                try:
                    df = pd.read_sql_query(query, conn, params=(kod, sifre))
                    if not df.empty:
                        st.session_state.giris_yapti = True
                        st.session_state.ad_soyad = df.iloc[0]['ad_soyad']
                        st.session_state.rol = df.iloc[0]['rol'].lower()
                        st.session_state.kullanici_kod = df.iloc[0]['cari_kod']
                        st.success(f"Hoş geldiniz, {st.session_state.ad_soyad}!")
                        st.rerun()
                    else:
                        st.error("Kod veya şifre hatalı!")
                except Exception as e:
                    st.error(f"Giriş hatası: {e}")

    with col2:
        st.subheader("Hızlı Bilgi")
        st.info("Müvekkilleriniz cari kodları ve şifreleri ile sistemden dosyalarını takip edebilirler.")

# 4. ANA PROGRAM (Giriş Sonrası)
if not st.session_state.giris_yapti:
    login_ekrani()
else:
    # Üst Menü / SideBar
    st.sidebar.title(f"👤 {st.session_state.ad_soyad}")
    st.sidebar.info(f"Yetki: {st.session_state.rol.upper()}")
    
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.giris_yapti = False
        st.session_state.rol = None
        st.rerun()

    # --- ROL KONTROLÜ ---
    if st.session_state.rol == "avukat":
        st.header("👨‍⚖️ Yönetim Paneli (Avukat)")
        menu = st.sidebar.selectbox("İşlem Seçin", 
            ["📊 Genel Bakış", "📂 Dosya Yönetimi", "💰 Kasa/Finans", "📅 Taksit Takip", "📄 Belge Sihirbazı"])
        
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

    elif st.session_state.rol == "müvekkil":
        st.header("📱 Müvekkil Bilgi Sistemi")
        st.write(f"Sayın {st.session_state.ad_soyad}, hoş geldiniz.")
        
        from pages.muvekkil_paneli import muvekkil_sayfasi
        muvekkil_sayfasi()
