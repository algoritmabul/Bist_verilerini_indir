from isyatirimhisse import Financials
# BIMAS hisse senedi için finansal tabloları çekme örneği
bimas_financials = Financials().get_data(
    symbols=['THYAO','PGSUS','BIMAS', 'TUPRS' ],
    start_year='2013',
    end_year='2023',
    exchange='TRY',
    financial_group='1',
    save_to_excel=True
)
