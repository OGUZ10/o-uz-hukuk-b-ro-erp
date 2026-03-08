import sqlite3
import psycopg2
import streamlit as st
import pandas as pd
import streamlit as st



# POSTGRESQL BAĞLANTISI (Bulut)
# POSTGRESQL BAĞLANTISI (Bulut - Güncellendi: Tablo Oluşturma ve Admin Ekleme)
def get_connection():
    try:
       
        url = st.secrets["DB_URL"]
        conn = psycopg2.connect(url)
        conn.autocommit = True # Komutların anında işlenmesi için kritik
        cur = conn.cursor()

        # 1. Adım: Şema netleştirme (Neon bazen farklı şemaya bakabilir)
        cur.execute("SET search_path TO public")

        # 2. Adım: Tabloları sırayla ve bağımsız bloklar halinde oluşturma
        # Not: Önce ana tablolar (cari_kartlar), sonra bağlı tablolar (talepler vb.) oluşmalı

        # TÜM TABLOLARIN TEK SEFERDE OLUŞTURULMASI

        tablo_sorgulari = [
            """CREATE TABLE IF NOT EXISTS cari_kartlar (
                id SERIAL PRIMARY KEY,
                cari_kod TEXT UNIQUE NOT NULL,
                ad_soyad TEXT NOT NULL,
                tip TEXT, 
                sifre TEXT DEFAULT '1234',
                bakiye DECIMAL(15,2) DEFAULT 0
            );""",
            """CREATE TABLE IF NOT EXISTS icra_dosyalari (
                id SERIAL PRIMARY KEY,
                dosya_no TEXT UNIQUE,
                borclu_ad TEXT,
                anapara DOUBLE PRECISION,
                vade_tarihi DATE,
                faiz_turu TEXT,
                toplam_alacak DOUBLE PRECISION DEFAULT 0,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",
            """CREATE TABLE IF NOT EXISTS davalar (
                id SERIAL PRIMARY KEY,
                dosya_no TEXT UNIQUE NOT NULL,
                muvekkil_kod TEXT,
                karsi_taraf TEXT,
                tip TEXT, 
                toplam_alacak DECIMAL(15,2),
                tahsil_edilen DECIMAL(15,2) DEFAULT 0,
                surec_asamasi INTEGER DEFAULT 10
            );""",
            """CREATE TABLE IF NOT EXISTS kasa (
                id SERIAL PRIMARY KEY,
                tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                islem_tipi TEXT,
                miktar DECIMAL(15,2),
                ilgili_kod TEXT,
                aciklama TEXT
            );""",
            """CREATE TABLE IF NOT EXISTS talepler (
                id SERIAL PRIMARY KEY,
                muvekkil_kod TEXT,
                baslik TEXT,
                mesaj TEXT,
                kategori TEXT,
                durum TEXT DEFAULT 'Bekliyor',
                tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",
            """CREATE TABLE IF NOT EXISTS takvim (
                id SERIAL PRIMARY KEY,
                baslik TEXT NOT NULL,
                etkinlik_tipi TEXT,
                baslangic_tarihi TIMESTAMP NOT NULL,
                aciklama TEXT,
                durum TEXT DEFAULT 'Bekliyor'
            );""",
            """CREATE TABLE IF NOT EXISTS sistem_loglari (
                id SERIAL PRIMARY KEY,
                islem_yapan TEXT,
                islem_tipi TEXT,
                detay TEXT,
                tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );"""
            """CREATE TABLE IF NOT EXISTS evraklar (
                id SERIAL PRIMARY KEY,
                dosya_no TEXT REFERENCES davalar(dosya_no),
                evrak_adi TEXT,
                evrak_tipi TEXT,
                yukleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                veri BYTEA,
                muvekkil_gorsun BOOLEAN DEFAULT FALSE
            );""",
            """CREATE TABLE IF NOT EXISTS mesajlar (
                id SERIAL PRIMARY KEY,
                dosya_no TEXT REFERENCES davalar(dosya_no),
                gonderen_rol TEXT, 
                mesaj TEXT,
                tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                okundu BOOLEAN DEFAULT FALSE
            );""",
                """CREATE TABLE IF NOT EXISTS masraflar (
                id SERIAL PRIMARY KEY,
                dosya_no TEXT REFERENCES davalar(dosya_no),
                masraf_turu TEXT,
                miktar DECIMAL(15,2),
                tarih DATE DEFAULT CURRENT_DATE
            );""",


            ]
        for sorgu in tablo_sorgulari:
            try:
                cur.execute(sorgu)
                
            except Exception as e:
                st.warning(f"Bir tablo oluşturulurken atlandı: {e}")

                # Veritabanı tablosuna 'son_hatirlatma' sütunu ekleme (Eğer yoksa)
                # EKSİK SÜTUNLARI GARANTİYE ALMA (ALTER TABLE)
            # Eğer tablo eskiden oluşmuşsa ama rol yoksa burası ekler
                
            try:
                with conn.cursor() as cur:
                    cur.execute("ALTER TABLE cari_kartlar ADD COLUMN IF NOT EXISTS son_hatirlatma DATE")
                    conn.commit()
            except:
                pass # Sütun zaten varsa hata vermemesi için
            # Veritabanı bağlantısının (conn) hemen altına bir kez çalışacak şekilde:
            try:
                with conn.cursor() as cur:
                    # Borçlu telefonu ve son hatırlatma tarihi sütunlarını ekliyoruz
                    cur.execute("ALTER TABLE davalar ADD COLUMN IF NOT EXISTS borclu_tel VARCHAR(20)")
                    cur.execute("ALTER TABLE davalar ADD COLUMN IF NOT EXISTS borclu_son_hatirlatma DATE")
                    conn.commit()
            except:
                pass
            # Veritabanı bağlantısının altına:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS taksitler (
                        id SERIAL PRIMARY KEY,
                        dosya_id INTEGER REFERENCES davalar(id),
                        taksit_no INTEGER,
                        vade_tarihi DATE,
                        miktar DECIMAL(12,2),
                        durum VARCHAR(20) DEFAULT 'Bekliyor',
                        takvim_event_id TEXT
                        )
                 """)
                    conn.commit()
            except:
                pass
    

        cur.close()
        
        return conn
    except Exception as e:
        st.error(f"⚠️ Neon Bağlantı Hatası: {e}")
        return None
    
# Global bağlantı değişkeni
db_conn = get_connection()
    
# --- SİSTEM AYARLARI ---
#uygulma başlatma
st.set_page_config(page_title="G-ERP Pro v18.6", layout="wide")
            



# 1. VERİ KAYDETME FONKSİYONU (Hataları Giderilmiş Hali)
def veri_kaydet(dosya_no, muvekkil, tip, borclu_ad, borclu_tel, alacak, borc):
    conn = sqlite3.connect('hukuk_otomasyon.db')
    cursor = conn.cursor()
    # Tablo yoksa oluştur (toplam_borc sütunu eklendi)
    cursor.execute('''CREATE TABLE IF NOT EXISTS dosyalar 
                     (dosya_no TEXT PRIMARY KEY, muvekkil TEXT, tip TEXT, 
                      borclu_ad TEXT, borclu_tel TEXT, toplam_alacak REAL, toplam_borc REAL)''')
    
    # "Upsert" Mantığı: 7 sütun için 7 adet '?' kullanıldı
    sql = """
    INSERT INTO dosyalar (dosya_no, muvekkil, tip, borclu_ad, borclu_tel, toplam_alacak, toplam_borc)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(dosya_no) DO UPDATE SET
        muvekkil=excluded.muvekkil,
        tip=excluded.tip,
        borclu_ad=excluded.borclu_ad,
        borclu_tel=excluded.borclu_tel,
        toplam_alacak=excluded.toplam_alacak,
        toplam_borc=excluded.toplam_borc
    """
    cursor.execute(sql, (dosya_no, muvekkil, tip, borclu_ad, borclu_tel, alacak, borc))
    conn.commit()
    conn.close()

# 2. ANA VERİTABANI KURULUM FONKSİYONU
def veritabani_kur():
    # 'hukuk_otomasyon.db' isminde birleştirildi
    conn = sqlite3.connect('hukuk_otomasyon.db', check_same_thread=False)
    cur = conn.cursor()
    
    # Tüm tabloları tek seferde ve hatasız kuruyoruz
    tablo_komutlari = [
        """CREATE TABLE IF NOT EXISTS cari_kartlar (
            cari_kod TEXT PRIMARY KEY, 
            ad_soyad TEXT NOT NULL, 
            tip TEXT, 
            sifre TEXT DEFAULT '1234', 
            bakiye REAL DEFAULT 0,
            rol TEXT DEFAULT 'Müvekkil',
            son_hatirlatma DATE);""",
            
        """CREATE TABLE IF NOT EXISTS davalar (
            dosya_no TEXT PRIMARY KEY, 
            muvekkil_kod TEXT, 
            karsi_taraf TEXT, 
            tip TEXT, 
            toplam_alacak REAL, 
            tahsil_edilen REAL DEFAULT 0, 
            surec_asamasi INTEGER DEFAULT 10,
            borclu_tel TEXT,
            borclu_son_hatirlatma DATE);""",
            
        """CREATE TABLE IF NOT EXISTS kasa (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
            islem_tipi TEXT, 
            miktar REAL, 
            ilgili_kod TEXT, 
            aciklama TEXT, 
            kalem_turu TEXT);""",
            
        """CREATE TABLE IF NOT EXISTS evraklar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dosya_no TEXT,
            evrak_adi TEXT,
            evrak_tipi TEXT,
            yukleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            veri BLOB,
            muvekkil_gorsun BOOLEAN DEFAULT FALSE);""",
            
        """CREATE TABLE IF NOT EXISTS taksitler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dosya_no TEXT,
            taksit_no INTEGER,
            vade_tarihi DATE,
            miktar REAL,
            durum TEXT DEFAULT 'Bekliyor');"""
    ]
    
    for komut in tablo_komutlari:
        cur.execute(komut)

    # GİRİŞ İÇİN ADMİN HESABI OLUŞTUR
    
    cur.execute("INSERT OR IGNORE INTO cari_kartlar (cari_kod, ad_soyad, sifre, rol) VALUES (?, ?, ?, ?)", 
               ('admin', 'Sistem Yöneticisi', 'admin123', 'ADMIN'))
               
    conn.commit()
    return conn

# Uygulama başladığında çalışacak olan bağlantı:
conn_sqlite = veritabani_kur()
# 3. VERİTABANI SEÇİCİ (MODÜLLER İÇİN)
def get_db():
    """Önce Bulut (Postgres) dener, hata alırsa Yerel (SQLite) döner."""
    cloud_conn = get_connection()
    if cloud_conn:
        return cloud_conn
    return veritabani_kur()

# Uygulama genelinde kullanılacak bağlantı nesnesi
conn = get_db()

