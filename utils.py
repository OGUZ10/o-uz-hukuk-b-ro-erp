import streamlit as st
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

def ai_asistan_yaniti(m_kod, mesaj, conn):
    anahtar = ["durum", "aşama", "ne oldu", "bilgi", "sonuç"]
    if any(k in mesaj.lower() for k in anahtar):
        df = pd.read_sql_query(f"SELECT dosya_no, surec_asamasi FROM davalar WHERE muvekkil_kod='{m_kod}' LIMIT 1", conn)
        if not df.empty:
            asama = df.iloc[0]['surec_asamasi']
            yorum = "İnceleme aşamasında." if asama < 50 else "Karar aşamasına yakın."
            return f"🤖 G-ERP ASİSTAN: Dosyanız şu an %{asama} aşamasında. {yorum}"
    return None

# --- GENEL AYARLAR (Burayı bir kez doldurmanız yeterli) ---
OFIS_IBAN = "TR00 0000 0000 0000 0000 0000 00" # Kendi IBAN'ınızı yazın
OFIS_BANKA = "X Bankası - İstanbul Şubesi"

def whatsapp_linki_olustur(telefon, muvekkil, tutar, gecikme, iban, banka):
    """WhatsApp mesaj linkini hazırlayan yardımcı fonksiyon"""
    mesaj = (
        f"Sayın {muvekkil}, \n\n"
        f"Ofisimizdeki dosyanızla ilgili {tutar:,.2f} TL tutarındaki ödemenizin vadesi "
        f"{gecikme} gün geçmiştir. \n\n"
        f"Ödemenizi aşağıdaki hesaba yapmanızı rica ederiz: \n"
        f"🏦 {banka} \n"
        f"💳 IBAN: {iban} \n\n"
        f"İyi çalışmalar dileriz."
    )
    return f"https://wa.me/{telefon}?text={urllib.parse.quote(mesaj)}"

def borclu_whatsapp_linki(telefon, borclu, dosya_no, tutar, iban, banka):
    mesaj = (
        f"Sayın {borclu}, \n\n"
        f"{dosya_no} sayılı icra dosyanız kapsamında güncel borç bakiyeniz {tutar:,.2f} TL'dir. \n"
        f"Dosyanın işlem görmeye devam etmemesi ve ek masraf oluşmaması için ödemenizi "
        f"aşağıdaki hesaba yapmanızı rica ederiz: \n\n"
        f"🏦 {banka} \n"
        f"💳 IBAN: {iban} \n\n"
        f"Ödeme yaptıktan sonra dekont iletmeniz rica olunur."
    )
    return f"https://wa.me/{telefon}?text={urllib.parse.quote(mesaj)}"
