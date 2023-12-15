import pandas as pd
import os
import glob

# 'isyatirim' adındaki dizindeki tüm CSV dosyalarını bul
csv_files = glob.glob('isyatirim/*.csv')

# Veri doğrulama ve temizleme fonksiyonu
def validate_and_clean_data(df):
    # Eksik verileri doldurmadan önceki durumu kontrol et
    print("Eksik veri kontrolü:")
    print(df.isnull().sum())

    # Tarih sütunu hariç, sayısal sütunlardaki eksik verileri medyan ile doldur
    numeric_columns = df.select_dtypes(include=['number']).columns
    df[numeric_columns] = df[numeric_columns].fillna(df[numeric_columns].median())

    # Eksik verileri doldurduktan sonraki durumu kontrol et
    print("\nEksik veri doldurma sonrası:")
    print(df.isnull().sum())

    return df

# Her bir CSV dosyası için işlem yap
for csv_file in csv_files:
    # CSV dosyasını DataFrame olarak oku
    df = pd.read_csv(csv_file)

    print(f"\n{csv_file} dosyası için veri doğrulama ve temizleme işlemleri:")

    # Veri doğrulama ve temizleme
    df = validate_and_clean_data(df)

    # Düzeltilmiş DataFrame'i aynı dosya adı ile kaydet
    df.to_csv(csv_file, index=False)
    print(f"{csv_file} dosyası düzeltilerek tekrar kaydedildi.")




