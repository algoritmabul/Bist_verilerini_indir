import yfinance as yf
import os

# XU100 sembollerini belirtin
symbols = [
    "XU100.IS", "MIATK.IS", "AKBNK.IS", "AKCNS.IS", "AKSGY.IS", "AKSA.IS", "AKSEN.IS", "AKGRT.IS", "ALGYO.IS", "ALARK.IS", "OYAKC.IS",
    "ALCTL.IS", "ALKIM.IS", "DOCO.IS", "ARCLK.IS", "ASELS.IS", "AYGAZ.IS", "BAGFS.IS", "BERA.IS", "BIMAS.IS", "BIZIM.IS", "DOCO.IS",
    "BRSAN.IS", "BRISA.IS", "BUCIM.IS", "CCOLA.IS", "CEMTS.IS", "CIMSA.IS", "DEVA.IS", "DOHOL.IS", "DOAS.IS", "EGEEN.IS", "BANVT.IS",
    "EGGUB.IS", "ECILC.IS", "EKGYO.IS", "ENJSA.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GOODY.IS", "ERBOS.IS", "GSDHO.IS", "PKENT.IS",
    "GUBRF.IS", "SAHOL.IS", "HLGYO.IS", "HEKTS.IS", "IHLGM.IS", "INDES.IS", "IPEKE.IS", "ISDMR.IS", "ISFIN.IS", "ISGYO.IS", "BRYAT.IS",
    "ISMEN.IS", "KRDMD.IS", "KARSN.IS", "KARTN.IS", "KERVT.IS", "KCHOL.IS", "KONYA.IS", "KORDS.IS", "KOZAL.IS", "KOZAA.IS", "MARTI.IS",
    "LOGO.IS", "MAVI.IS", "MGROS.IS", "MPARK.IS", "NTHOL.IS", "NETAS.IS", "ODAS.IS", "OTKAR.IS", "OYAKC.IS", "OZKGY.IS", "BURCE.IS",
    "PGSUS.IS", "PETKM.IS", "PNSUT.IS", "SASA.IS", "SELEC.IS", "SKBNK.IS", "SOKM.IS", "TATGD.IS", "TAVHL.IS", "TKFEN.IS",
    "TOASO.IS", "TRGYO.IS", "TCELL.IS", "TUPRS.IS", "THYAO.IS", "TTKOM.IS", "TTRAK.IS", "GARAN.IS", "HALKB.IS", "ISCTR.IS", "TUR",
    "TSKB.IS", "TURSG.IS", "SISE.IS", "VAKBN.IS", "ULKER.IS", "VERUS.IS", "VESBE.IS", "VESTL.IS", "YKBNK.IS", "YATAS.IS", "ZOREN.IS", "HRC.CO" , "USDTRY=X"
]

# XU100 dizini oluşturun
if not os.path.exists("XU100"):
    os.makedirs("XU100")

# Her sembol için verileri çekin ve "XU100.IS.CSV" olarak kaydedin
for symbol in symbols:
    # Verileri çekin
    stock_data = yf.download(symbol, period="max")

    # Sembol adını temizleyin
    clean_symbol = symbol.split(".")[0]

    # Verileri "XU100.IS.CSV" olarak kaydedin
    csv_filename = os.path.join("XU100", f"{clean_symbol}.IS.CSV")
    stock_data.to_csv(csv_filename)

    print(f"{csv_filename} dosyası oluşturuldu.")

print("Tüm veriler 'XU100' alt dizinine 'hepsi' olarak kaydedildi.")


