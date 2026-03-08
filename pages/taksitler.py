import streamlit as st
import pandas as pd
from database import get_connection
from datetime import datetime, timedelta

def taksit_sayfasi():
    conn = get_connection()
    if not st.session_state.get('giris_yapti') or st.session_state.rol != "avukat":
        st.error("Yetkisiz erişim!")
        return

    st.title("📅 Taksitlendirme ve Tahsilat Takibi")

    # 1. Dosya Seçimi
    df_davalar = pd.read_sql_query("SELECT id, dosya_no, karsi_taraf FROM davalar", conn)
    secim = st.selectbox("Taksit planı yapılacak dosyayı seçin:", 
                         df_davalar.apply(lambda x: f"{x['dosya_no']} - {x['karsi_taraf']}", axis=1))
    
    if secim:
        dosya_id = df_davalar[df_davalar.apply(lambda x: f"{x['dosya_no']} - {x['karsi_taraf']}", axis=1) == secim]['id'].values[0]
        
        # 2. Taksit Planı Oluşturma Formu
        st.divider()
        st.subheader("➕ Yeni Taksit Planı Oluştur")
        with st.form("taksit_plani_formu"):
            col1, col2, col3 = st.columns(3)
            t_sayisi = col1.number_input("Taksit Sayısı", min_value=1, max_value=24, value=3)
            t_miktari = col2.number_input("Taksit Tutarı (TL)", min_value=0.0, step=500.0)
            baslangic = col3.date_input("İlk Taksit Tarihi", datetime.now())
            
            if st.form_submit_button("Planı Kaydet"):
                with conn.cursor() as cur:
                    for i in range(t_sayisi):
                        vade = baslangic + timedelta(days=i*30) # Her ay 1 taksit
                        cur.execute("""
                            INSERT INTO taksitler (dosya_id, taksit_no, vade_tarihi, miktar, durum) 
                            VALUES (%s, %s, %s, %s, 'Bekliyor')
                        """, (int(dosya_id), i+1, vade, t_miktari))
                    st.success(f"{t_sayisi} adet taksit başarıyla oluşturuldu!")
                    st.rerun()

        # 3. Mevcut Taksitleri Listeleme ve Tahsilat Butonu
        st.divider()
        st.subheader("📋 Ödeme Planı Durumu")
        df_taksitler = pd.read_sql_query("SELECT id, taksit_no, vade_tarihi, miktar, durum FROM taksitler WHERE dosya_id=%s ORDER BY vade_tarihi", conn, params=(int(dosya_id),))
        
        if not df_taksitler.empty:
            for idx, row in df_taksitler.iterrows():
                c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
                c1.write(f"Taksit {row['taksit_no']}")
                c2.write(f"{row['vade_tarihi'].strftime('%d/%m/%Y')}")
                c3.write(f"{row['miktar']:,.2f} TL")
                
                if row['durum'] == 'Bekliyor':
                    if c4.button("Tahsil Et", key=f"btn_{row['id']}"):
                        with conn.cursor() as cur:
                            cur.execute("UPDATE taksitler SET durum='Ödendi' WHERE id=%s", (int(row['id']),))
                            # Otomatik Kasaya Gelir Olarak İşle
                            cur.execute("INSERT INTO kasa (islem_tipi, miktar, aciklama) VALUES ('Gelir', %s, %s)", 
                                        (row['miktar'], f"Taksit Tahsilatı - Taksit ID: {row['id']}"))
                            st.success("Tahsilat kasaya işlendi!")
                            st.rerun()
                else:
                    c4.success("Ödendi")
        else:
            st.info("Bu dosya için henüz taksit planı oluşturulmamış.")

if __name__ == "__main__":
    taksit_sayfasi()
