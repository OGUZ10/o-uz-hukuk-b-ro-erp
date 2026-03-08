import streamlit as st
import pandas as pd
from database import get_connection
from datetime import datetime

def davalar_sayfasi():
    st.header("📂 Dosya ve Dava Yönetimi")
    
    # Veritabanı bağlantısı
    conn = get_connection()
    
    # Üst Sekmeler: Listeleme ve Yeni Kayıt
    tab1, tab2 = st.tabs(["📋 Dava Listesi", "➕ Yeni Dava Aç"])
    
    with tab1:
        st.subheader("Aktif Dava Dosyaları")
        
        if conn:
            try:
                # Verileri çek (Örnek sorgu - tablo adlarınıza göre güncelleyin)
                query = "SELECT id, dosya_no, muvekkil_ad, karsi_taraf, dava_turu, durum, acilis_tarihi FROM davalar ORDER BY acilis_tarihi DESC"
                df = pd.read_sql_query(query, conn)
                
                # Arama ve Filtreleme
                search = st.text_input("🔍 Dosya No veya Müvekkil Adı ile Ara", "")
                if search:
                    df = df[df['dosya_no'].str.contains(search, case=False) | df['muvekkil_ad'].str.contains(search, case=False)]
                
                # Renkli Durum Göstergesi (Opsiyonel Stil)
                def color_durum(val):
                    color = '#28a745' if val == 'Devam Ediyor' else '#dc3545' if val == 'Kapalı' else '#ffc107'
                    return f'color: {color}; font-weight: bold'

                st.dataframe(
                    df,
                    column_config={
                        "id": None, # ID'yi gizle
                        "dosya_no": "Dosya No",
                        "muvekkil_ad": "Müvekkil",
                        "karsi_taraf": "Karşı Taraf",
                        "dava_turu": "Dava Türü",
                        "durum": st.column_config.SelectboxColumn("Durum", options=["Devam Ediyor", "Karar Çıktı", "İstinaf", "Kapalı"]),
                        "acilis_tarihi": st.column_config.DateColumn("Açılış Tarihi")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            except Exception as e:
                st.info("💡 Henüz kayıtlı dava bulunamadı veya tablo yapısı eksik. Lütfen veritabanını kontrol edin.")

    with tab2:
        st.subheader("Yeni Dosya Kartı Oluştur")
        with st.form("yeni_dava_formu", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                dosya_no = st.text_input("Dosya No (Örn: 2024/150 Esas)")
                muvekkil = st.text_input("Müvekkil Ad Soyad / Ünvan")
                dava_turu = st.selectbox("Dava Türü", ["İş Davası", "Boşanma", "İcra Takibi", "Ceza", "Gayrimenkul", "Diğer"])
            
            with col2:
                karsi_taraf = st.text_input("Karşı Taraf")
                mahkeme = st.text_input("Mahkeme / Daire")
                tarih = st.date_input("Dava Açılış Tarihi", value=datetime.now())
            
            detaylar = st.text_area("Dava Özeti ve Notlar")
            
            submit = st.form_submit_button("💾 Dosyayı Kaydet")
            
            if submit:
                if dosya_no and muvekkil:
                    try:
                        cursor = conn.cursor()
                        insert_query = """
                            INSERT INTO davalar (dosya_no, muvekkil_ad, karsi_taraf, dava_turu, mahkeme, acilis_tarihi, detaylar, durum)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Devam Ediyor')
                        """
                        cursor.execute(insert_query, (dosya_no, muvekkil, karsi_taraf, dava_turu, mahkeme, tarih, detaylar))
                        conn.commit()
                        st.success(f"✅ {dosya_no} numaralı dosya başarıyla sisteme işlendi.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Kayıt sırasında hata oluştu: {e}")
                else:
                    st.warning("Lütfen zorunlu alanları (Dosya No ve Müvekkil) doldurun.")
