import yfinance as yf
import pandas as pd

# Yatırım yapılan hisse senedinin simgesi (örneğin: GOOGL)
TICKER = "DOCO.IS"

# Yahoo Finance'ten finansal verileri çek
ticker_data = yf.Ticker(TICKER)

# Gelir Tablosu
income_statement = ticker_data.financials
income_statement.to_excel('gelir-tablosu.xlsx', index=True)

# Bilanço
balance_sheet = ticker_data.balance_sheet
balance_sheet.to_excel('balance_bilanco.xlsx', index=True)

# Nakit Akış Tablosu
cash_flow = ticker_data.cashflow
cash_flow.to_excel('nakit_akış.xlsx', index=True)
