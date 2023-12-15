import pandas as pd
import os
import glob

# 'isyatirim' adında bir alt dizin oluştur
# Eğer zaten varsa bu adımı atlar
os.makedirs('isyatirim', exist_ok=True)

# Çalıştırıldığı dizindeki tüm Excel dosyalarını bul
excel_files = glob.glob('./*.xlsx')

# Her bir Excel dosyası için işlem yap
for excel_file in excel_files:
    # Excel dosyasını DataFrame olarak oku
    df = pd.read_excel(excel_file)

    # İstenen sütunları seç (Excel'deki gerçek isimleri kullan)
    selected_columns = ['DATE', 'CLOSING_TL', 'HIGH_TL', 'LOW_TL', 'CLOSING_TL', 'VOLUME_TL', 'CLOSING_USD', 'XU100_TL']
    
    # Excel dosyasında bu sütunlar varsa işlem yap
    if set(selected_columns).issubset(df.columns):
        df_selected = df[selected_columns].copy()
        
        # Sütun isimlerini değiştir
        df_selected.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_USD', 'XU100_TL']

        # Yeni CSV dosyasının adını belirle (Orijinal Excel dosyası adı + '_is')
        csv_file_name = os.path.splitext(os.path.basename(excel_file))[0] + '.is.csv'
        
        # Yeni dosya yolu oluştur
        csv_file_path = os.path.join('isyatirim', csv_file_name)

        # DataFrame'i CSV dosyası olarak kaydet
        df_selected.to_csv(csv_file_path, index=False)
        print(f"{excel_file} dosyası {csv_file_path} olarak kaydedildi.")
    else:
        print(f"{excel_file} dosyasında istenen sütunlar bulunamadı.")


