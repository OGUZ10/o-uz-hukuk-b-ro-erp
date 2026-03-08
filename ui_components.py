import streamlit as st
import pandas as pd

# Sabit Tanımlar
ROLLER = {
    "Avukat": ["📊 DASHBOARD", "⚖️ DAVA & İCRA", "💰 FİNANS / KASA", "📇 CARİLER", "📊 ANALİZ"],
    "Müvekkil": ["🏠 DOSYALARIM", "💰 HESAP EKSTREM", "📩 MESAJ GÖNDER"]
}

def login_ekrani(conn):
    st.markdown("<h1 style='text-align: center;'>⚖️ G-ERP Hukuk Otomasyonu</h1>", unsafe_allow_html=True)
    with st.container():
        col1, col2, col3 = st.columns([1,2,1]) # Ortayı biraz daha genişletelim
        with col2:
            with st.form("login_form"):
                k_kod = st.text_input("Cari Kod (Örn: AV001)")
                k_sifre = st.text_input("Şifre (Örn: admin123)", type="password")
                submit = st.form_submit_button("Sisteme Giriş Yap")
                
                if submit:
                    cur = conn.cursor()
                    # Bilgileri çekiyoruz
                    cur.execute("SELECT cari_kod, ad_soyad, rol FROM cari_kartlar WHERE cari_kod=? AND sifre=?", (k_kod, k_sifre))
                    user_res = cur.fetchone()
                    
                    if user_res:
                        st.session_state.logged_in = True
                        # Veritabanından gelen sırayla (0:kod, 1:ad, 2:rol) sözlüğe atıyoruz
                        st.session_state.user = {
                            "kod": user_res[0], 
                            "ad": user_res[1], 
                            "rol": user_res[2]
                        }
                        st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                        st.rerun()
                    else:
                        st.error("Hatalı kod veya şifre!")


def dashboard_sayfası(conn):
    st.header("📊 Genel Durum Paneli")
    c1, c2, c3 = st.columns(3)
    
    # Basit Sayaçlar (Hata almamak için boş olsa da çalışır)
    dava_sayisi = pd.read_sql("SELECT COUNT(*) FROM davalar", conn).iloc[0,0]
    cari_sayisi = pd.read_sql("SELECT COUNT(*) FROM cari_kartlar", conn).iloc[0,0]
    
    c1.metric("Toplam Dava", dava_sayisi)
    c2.metric("Kayıtlı Cari", cari_sayisi)
    c3.metric("Bekleyen Görevler", "12")

def dava_yonetim_sayfası(conn):
    st.header("⚖️ Dava ve İcra Yönetimi")
    # Buraya senin kodundaki formları ekleyeceğiz
    st.info("Dava kayıt ve liste ekranı buraya gelecek.")
