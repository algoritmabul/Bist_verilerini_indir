from isyatirimhisse import StockData
import pandas as pd

# StockData örneğini oluştur
stock_data = StockData()

# Hisse senedi sembollerini içeren Excel dosyasını oku (XU100 sayfasından)
symbols_df = pd.read_excel('sirketler/sirketler.xlsx', sheet_name='XU100')

# 'Kod' sütunundaki hisse senedi sembollerini kullan
for symbol in symbols_df['Kod']:
    # Hisse senedi verisini al
    df = stock_data.get_data(
        symbols=[symbol], 
        start_date='02-01-1970'
    )

    # Veriyi Excel dosyasına kaydet
    df.to_excel(f'{symbol}.xlsx')

    