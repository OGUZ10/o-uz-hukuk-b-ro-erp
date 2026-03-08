import sqlite3
import psycopg2
import streamlit as st
import pandas as pd


# 1. BAĞLANTI (Senin kodun)
def get_connection():
    try:
        neon_config = st.secrets["neon"]
        conn = psycopg2.connect(
            host=neon_config["host"],
            database=neon_config["database"],
            user=neon_config["user"],
            password=neon_config["password"],
            port=neon_config["port"],
            sslmode='require'
        )
        return conn
    except Exception as e:
        st.error(f"⚠️ Neon Bağlantı Hatası: {e}")
        return None

# 2. VERİ OKUMA (Dashboard ve Listeler için ŞART)
def execute_read(query, params=None):
    conn = get_connection()
    if conn:
        try:
            # PostgreSQL verisini Pandas DataFrame'e dönüştürür
            df = pd.read_sql_query(query, conn, params=params)
            return df
        except Exception as e:
            st.error(f"❌ Okuma Hatası: {e}")
            return pd.DataFrame()
        finally:
            conn.close() # Hattı mutlaka kapatıyoruz!
    return pd.DataFrame()

# 3. VERİ YAZMA (Dava Ekleme, Kasa Kaydı için ŞART)
def execute_write(query, params=None):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit() # Değişikliği veritabanına işle
            return True
        except Exception as e:
            st.error(f"❌ Yazma Hatası: {e}")
            conn.rollback() # Hata varsa geri al
            return False
        finally:
            conn.close() # Hattı mutlaka kapatıyoruz!
    return False
