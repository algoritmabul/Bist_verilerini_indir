"""panel.py icin TV DataFeed veri yukleme eki (tvdatafeed-enhanced).

BIST (IMKB) ve Kripto borsalarindan TradingView uzerinden veri indirir,
panelin kendi CSV klasorlerine (mevcut CSV biçimiyle) yazar ve paneli
yeni veriyle yeniler. panel.py'nin "dizinden oku" mantigina DOKUNMAZ:
TV verisi de sanki kullanici CSV'siymiş gibi aynı kapıdan girer.

Kullanim (panel.py icinde, _arayuz_kur sonrasi):
    from panel_tvdata_ekleri import tv_butonu_ekle
    tv_butonu_ekle(self)

Gereksinim: pip install tvdatafeed-enhanced
"""

import json
import os
import re
import shutil
import threading
import time
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd

# ---- panel paleti (panel.py ile aynı görünüm) ------------------------------
BG = "#f8f5ea"
PANEL = "#f8f5ea"
PANEL_ALT = "#eae4d5"
GRID = "#d2cbb9"
TEXT = "#292820"
MUTED = "#777264"
YESEM = "#57857a"        # TV VERİ butonu (LOAD DATA kırmızısından ayrışsın)
YESEM_AKTIF = "#6f9c8d"
HATA_KIRMIZI = "#bd4942"
OK_YESIL = "#4e7a3a"

# ---- seçenekler -------------------------------------------------------------
KAYNAKLAR = ("BIST (IMKB)", "Kripto")

KRIPTO_BORSALARI = (
    "BINANCE", "BYBIT", "COINBASE", "OKX",
    "KUCOIN", "MEXC", "BITFINEX", "GATEIO",
)

# ---- toplu indirme listeleri -----------------------------------------------
# Gömülü listeler: getmidas / infoyatirim canlı endeks tablolarından,
# Ekim-Aralık 2026 dönemi (TRMET ile CVKMD/CWENE/DOAS/ENERY/MAVI/TSKB girişleri
# dahil — güncel). Endeks kuraımları 3 ayda bir değişir; panel.py yanına
# bist30.txt / bist50.txt / bist100.txt / bist_tumu.txt konursa DOSYA geçerli olur.
TOPLU_LISTELER = ("BIST 30", "BIST 50", "BIST 100", "BIST TÜMÜ")

BIST30_LISTESI = (
    "AEFES", "AKBNK", "ASELS", "ASTOR", "BIMAS", "EKGYO", "ENKAI", "EREGL",
    "FROTO", "GARAN", "GUBRF", "ISCTR", "KCHOL", "KRDMD", "MGROS", "PETKM",
    "PGSUS", "SAHOL", "SASA", "SISE", "TAVHL", "TCELL", "THYAO", "TOASO",
    "TRALT", "TRMET", "TTKOM", "TUPRS", "VAKBN", "YKBNK",
)

BIST50_LISTESI = (
    "AEFES", "AKBNK", "AKSEN", "ALARK", "ASELS", "ASTOR", "BIMAS", "BRSAN",
    "BTCIM", "CANTE", "CCOLA", "CIMSA", "CVKMD", "CWENE", "DOAS", "ECILC",
    "EKGYO", "ENERY", "ENKAI", "EREGL", "FROTO", "GARAN", "GLRMK", "GUBRF",
    "HALKB", "HEKTS", "ISCTR", "KCHOL", "KRDMD", "MAVI", "MGROS", "OYAKC",
    "PETKM", "PGSUS", "SAHOL", "SASA", "SISE", "TAVHL", "TCELL", "THYAO",
    "TOASO", "TRALT", "TRMET", "TSKB", "TTKOM", "TUPRS", "TURSG", "ULKER",
    "VAKBN", "YKBNK",
)

BIST100_LISTESI = (
    "AEFES", "AGHOL", "AHGAZ", "AKBNK", "AKCNS", "AKFYE", "AKSA", "AKSEN",
    "ALARK", "ALBRK", "ALTNY", "ANHYT", "ANSGR", "ARCLK", "ASELS", "ASTOR",
    "AYGAZ", "BERA", "BIMAS", "BINHO", "BRSAN", "BRYAT", "BTCIM", "CANTE",
    "CCOLA", "CIMSA", "CVKMD", "CWENE", "DOAS", "DOHOL", "ECILC", "ECZYT",
    "EGEEN", "EGGUB", "EKGYO", "ENERY", "ENJSA", "ENKAI", "ENTRA", "EREGL",
    "EUREN", "FENER", "FROTO", "GARAN", "GLRMK", "GLYHO", "GRSEL", "GUBRF",
    "GWIND", "HALKB", "HEKTS", "ISCTR", "ISDMR", "ISMEN", "KARSN", "KATMR",
    "KCAER", "KCHOL", "KORDS", "KRDMD", "LMKDC", "MAVI", "MGROS", "MPARK",
    "OBAMS", "ODAS", "OTKAR", "OYAKC", "PAHOL", "PETKM", "PGSUS", "RGYAS",
    "RYSAS", "SAHOL", "SASA", "SISE", "SNGYO", "SOKM", "TABGD", "TAVHL",
    "TCELL", "TCKRC", "THYAO", "TKFEN", "TOASO", "TRALT", "TRENJ", "TRGYO",
    "TRMET", "TSKB", "TTKOM", "TTRAK", "TUKAS", "TUPRS", "TURSG", "ULKER",
    "VAKBN", "VESTL", "YKBNK", "ZOREN",
)

_GOMULU_TOPLU = {
    "BIST 30": BIST30_LISTESI,
    "BIST 50": BIST50_LISTESI,
    "BIST 100": BIST100_LISTESI,
}

TOPLU_DOSYALAR = {
    "BIST 30": "bist30.txt",
    "BIST 50": "bist50.txt",
    "BIST 100": "bist100.txt",
    "BIST TÜMÜ": "bist_tumu.txt",
}

AYAR_DOSYASI = "tv_veri_ayarlar.json"   # panel.py yanında: kalıcı SEÇ + son ayarlar

# (etiket, Interval öznitelik adayları, intraday mi?)
# Farklı tvDatafeed sürümlerindeki ad farklarına karşı aday listesi tutulur.
TV_ARALIKLAR = (
    ("1dk",    ("in_1_minute",), True),
    ("3dk",    ("in_3_minute", "in_3_minutes"), True),
    ("5dk",    ("in_5_minute",), True),
    ("15dk",   ("in_15_minute", "in_15_minutes"), True),
    ("30dk",   ("in_30_minute", "in_30_minutes"), True),
    ("45dk",   ("in_45_minute",), True),
    ("1sa",    ("in_1_hour",), True),
    ("2sa",    ("in_2_hour",), True),
    ("3sa",    ("in_3_hour",), True),
    ("4sa",    ("in_4_hour",), True),
    ("1gün",   ("in_daily", "in_1_day"), False),
    ("1hafta", ("in_weekly",), False),
    ("1ay",    ("in_monthly",), False),
)

MIN_BAR = 100
MAK_BAR = 5000   # TradingView çekim sınırı (kaynak: tvdatafeed-enhanced belgesi)

_KUTUPHANE_ONBELLEK = None


# ------------------------------------------------------------------ kalıcı ayarlar --
def _modul_dizini():
    """panel_tvdata_ekleri.py'nin bulunduğu klasör (= panel.py'nin yeri)."""
    return Path(__file__).resolve().parent


def ayar_yolu():
    return _modul_dizini() / AYAR_DOSYASI


def ayar_oku(yol=None):
    """Kalıcı ayarları okur (dosya yoksa/bozuksa {})."""
    yol = Path(yol) if yol else ayar_yolu()
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
        return veri if isinstance(veri, dict) else {}
    except Exception:
        return {}


def ayar_yaz(ayar, yol=None):
    """Kalıcı ayarları yazar; başarısızlık sessizce yutulur (panel çalışmaya devam)."""
    try:
        yol = Path(yol) if yol else ayar_yolu()
        yol.write_text(json.dumps(ayar, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


# ------------------------------------------------------------------ kütüphane --
def kutuphane_yukle():
    """tvDatafeed modülünü tembel yükler -> (TvDatafeed, Interval).

    Yükleme başarısızsa kurulum komutunu içeren anlaşılır hata fırlatır.
    """
    global _KUTUPHANE_ONBELLEK
    if _KUTUPHANE_ONBELLEK is not None:
        return _KUTUPHANE_ONBELLEK
    try:
        from tvDatafeed import TvDatafeed, Interval
    except Exception as hata:
        raise RuntimeError(
            "tvDatafeed kütüphanesi bulunamadı.\n"
            "Kurulum:  pip install tvdatafeed-enhanced\n"
            f"(ayrıntı: {hata})"
        ) from hata
    _KUTUPHANE_ONBELLEK = (TvDatafeed, Interval)
    return _KUTUPHANE_ONBELLEK


def interval_nesnesi(Interval, adaylar):
    """Interval enum'unda aday adlardan ilk bulunanı döndürür."""
    for ad in adaylar:
        deger = getattr(Interval, ad, None)
        if deger is not None:
            return deger
    raise RuntimeError(f"Interval bulunamadı: {', '.join(adaylar)}")


def aralik_bilgisi(etiket):
    """'1sa' -> (aday_attr_adları, intraday_mi)."""
    for ad, adaylar, intraday in TV_ARALIKLAR:
        if ad == etiket:
            return adaylar, intraday
    raise RuntimeError(f"Geçersiz aralık: {etiket}")


# ---------------------------------------------------------------------- indirme --
def _sembol_temiz(sembol, borsa):
    """'BIST:THYAO' -> 'THYAO', 'BINANCE:BTCUSDT' -> 'BTCUSDT'."""
    s = str(sembol).strip().upper()
    if ":" in s:
        on, son = s.split(":", 1)
        if on == str(borsa).strip().upper():
            s = son.strip()
    return s.replace(" ", "")


def _tv_baglan(kullanici="", sifre=""):
    TvDatafeed, _ = kutuphane_yukle()
    if kullanici and sifre:
        return TvDatafeed(kullanici, sifre)
    return TvDatafeed()


def tv_veri_cek(borsa, sembol, aralik_etiket, bar_sayisi=2000,
                kullanici="", sifre="", tv=None, Interval=None):
    """TradingView'dan veri indirir, panele uygun normal df döndürür.

    Dönen df: DatetimeIndex (ad: DATETIME) + open/high/low/close/volume
    (küçük harf). Tekrarlı/sırasız barlar temizlenir.
    Toplu indirmede tv+Interval VERİLİR: bağlantı bir kez kurulur, her sembol
    için yeniden bağlanılmaz ve kütüphane importu atlanır.
    """
    if tv is None or Interval is None:
        TvDatafeed, Interval = kutuphane_yukle()
        if tv is None:
            tv = _tv_baglan(kullanici, sifre)
    sembol = _sembol_temiz(sembol, borsa)
    if not sembol:
        raise RuntimeError("Sembol boş olamaz.")
    bar_sayisi = int(max(MIN_BAR, min(MAK_BAR, int(bar_sayisi))))
    adaylar, _intraday = aralik_bilgisi(aralik_etiket)
    aralik = interval_nesnesi(Interval, adaylar)

    df = tv.get_hist(
        symbol=sembol,
        exchange=str(borsa).strip().upper(),
        interval=aralik,
        n_bars=bar_sayisi,
    )
    if df is None or len(df) == 0:
        raise RuntimeError(
            f"{borsa}:{sembol} için veri dönmedi.\n"
            "Sembol/borsa yazımını kontrol edin (Ara düğmesini kullanın)."
        )

    df = df.rename(columns=str.lower)
    sutunlar = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
    if "close" not in sutunlar:
        raise RuntimeError(f"{borsa}:{sembol}: close sütunu yok, veri kullanılamaz.")
    df = df[sutunlar].copy()
    df = df.dropna(subset=[c for c in ("open", "high", "low", "close") if c in df.columns])
    df.index = pd.DatetimeIndex(df.index, name="DATETIME")
    df = df[~df.index.duplicated(keep="last")].sort_index()
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0)
    if len(df) == 0:
        raise RuntimeError(f"{borsa}:{sembol}: geçerli OHLC barı bulunamadı.")
    return df


def tv_sembol_ara(sorgu, borsa, kullanici="", sifre="", adet=40):
    """TradingView sembol araması -> ['THYAO', 'ASELS', ...]."""
    sorgu = str(sorgu).strip()
    if not sorgu:
        return []
    tv = _tv_baglan(kullanici, sifre)
    try:
        sonuc = tv.search_symbol(sorgu, str(borsa).strip().upper()) or []
    except Exception:
        return []
    adlar = []
    for kayit in sonuc:
        try:
            if isinstance(kayit, dict):
                ad = kayit.get("symbol", "")
            else:
                ad = getattr(kayit, "symbol", "")
            ad = str(ad).strip().upper()
            if ad and ad not in adlar:
                adlar.append(ad)
        except Exception:
            continue
        if len(adlar) >= adet:
            break
    return adlar


# ---------------------------------------------------------------- toplu listeler --
def _sembol_listesi_coz(metin):
    """'THYAO, asels\\nGARAN  # yorum' -> ['THYAO', 'ASELS', 'GARAN'] (sıra korunur).

    Boşluk/virgül/noktalı virgül ayraçlı, satır satır da olur; '#' sonrası
    (satır ortasında bile) yorum sayılır.
    """
    bulunan = []
    for satir in str(metin).splitlines():
        satir = satir.split("#", 1)[0]
        for ham in re.split(r"[\s,;]+", satir):
            s = ham.strip().upper()
            if not s:
                continue
            s = re.sub(r"[^A-Z0-9.\-]", "", s)
            if s and s not in bulunan:
                bulunan.append(s)
    return bulunan


def toplu_liste_oku(liste_ad, dizin=None):
    """(semboller, kaynak_notu) — önce panel.py yanındaki <liste>.txt, yoksa gömülü.

    BIST TÜMÜ gömülü olarak BIST 100 listesiyle temsil edilir; gerçek tüm
    piyasa için panel.py yanına bist_tumu.txt koyun (her satıra bir sembol,
    '#' ile yorum). Dosyadaki liste varsa O geçerli olur (endeks kuraımları
    3 ayda bir değiştiği için liste dosyasıyla güncellenebilir).
    """
    ad = TOPLU_DOSYALAR.get(liste_ad)
    dizin = Path(dizin) if dizin else _modul_dizini()
    if ad:
        dosya = dizin / ad
        if dosya.exists():
            try:
                metin = dosya.read_text(encoding="utf-8-sig", errors="replace")
            except Exception:
                metin = ""
            semboller = _sembol_listesi_coz(metin)
            if semboller:
                return semboller, f"{ad} (dosya)"
    if liste_ad == "BIST TÜMÜ":
        return list(BIST100_LISTESI), "gömülü BIST 100 — tüm piyasa için bist_tumu.txt koyun"
    return list(_GOMULU_TOPLU.get(liste_ad, ())), "gömülü liste"


# -------------------------------------------------------------------- CSV yazımı --
def _varsayilan_bicim():
    """Referans CSV yokken kullanılan biçim.

    Tarih ISO (yyyy-mm-dd) seçilir: pandas 'dd.mm.yyyy'yi ay-gün sanıp
    gün>12'de bozulur; ISO her okuyucuda belirsizliksiz ayrışır.
    Referans CSV varsa biçim ondan taklit edilir (o her zaman çalışır).
    """
    return {
        "ayirac": ",",
        "kolonlar": ["Date", "Open", "High", "Low", "Close", "Volume"],
        "tarih_fmt": "%Y-%m-%d",
        "saat_ayri": False,
        "saat_fmt": "%H:%M",
        "ondalik_virgul": False,
        "bom": False,
    }


def _tarih_fmt_hucresi(hucre):
    """'05.06.2020 10:00' -> '%d.%m.%Y %H:%M' gibi strftime biçimi çıkarır."""
    s = str(hucre).strip()
    if not s:
        return "%d.%m.%Y"
    saat_eki = ""
    tarih = s
    if ":" in s:
        parcalar = s.split()
        saat = parcalar[-1]
        tarih = " ".join(parcalar[:-1])
        saat_eki = " %H:%M:%S" if saat.count(":") >= 2 else " %H:%M"
    if tarih.count("-") == 2:
        taban = "%Y-%m-%d"
    elif tarih.count(".") == 2:
        taban = "%d.%m.%Y"
    elif tarih.count("/") == 2:
        taban = "%d/%m/%Y"
    else:
        taban = "%d.%m.%Y"
    return taban + saat_eki


def ilk_csv_bicimi(dizin):
    """Dizindeki ilk okunabilir CSV'nin biçimini öğrenir (biçim taklidi).

    Döndürür: {'ayirac', 'kolonlar', 'tarih_fmt', 'saat_ayri',
               'saat_fmt', 'ondalik_virgul', 'bom'} — klasör boşsa None.
    """
    dizin = Path(dizin)
    if not dizin.exists():
        return None
    for dosya in sorted(dizin.glob("*.csv")):
        try:
            ham = dosya.read_bytes()[:8192]
        except Exception:
            continue
        if not ham:
            continue
        bom = ham.startswith(b"\xef\xbb\xbf")
        metin = ham.decode("utf-8-sig", errors="replace")
        satirlar = [s for s in metin.splitlines() if s.strip()]
        if not satirlar:
            continue
        baslik = satirlar[0]
        ayirac = ";" if baslik.count(";") > baslik.count(",") else ","
        kolonlar = [k.strip() for k in baslik.split(ayirac) if k.strip() != ""]
        if not kolonlar:
            continue
        kucuk = {k.lower(): i for i, k in enumerate(kolonlar)}

        tarih_fmt = "%d.%m.%Y"
        saat_ayri = any(k in kucuk for k in ("time", "saat"))
        ondalik_virgul = False
        if len(satirlar) > 1:
            hucreler = [h.strip() for h in satirlar[1].split(ayirac)]
            i_date = kucuk.get("date", kucuk.get("datetime", kucuk.get("tarih", -1)))
            if 0 <= i_date < len(hucreler) and hucreler[i_date]:
                tarih_fmt = _tarih_fmt_hucresi(hucreler[i_date])
            if ayirac == ";":
                ondalik_virgul = any(
                    re.fullmatch(r"-?\d+,\d+", h) is not None for h in hucreler
                )
        if saat_ayri and " %H" in tarih_fmt:
            tarih_fmt = tarih_fmt.split(" ")[0]
        return {
            "ayirac": ayirac,
            "kolonlar": kolonlar,
            "tarih_fmt": tarih_fmt,
            "saat_ayri": saat_ayri,
            "saat_fmt": "%H:%M",
            "ondalik_virgul": ondalik_virgul,
            "bom": bom,
        }
    return None


def _sayi_yaz(deger, ondalik_virgul):
    if deger is None or pd.isna(deger):
        return ""
    s = f"{float(deger):.6f}".rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s.replace(".", ",") if ondalik_virgul else s


def csv_yaz(df, yol, bicim=None, saat_yaz=True):
    """TV df'sini öğrenilen/varsayılan biçimde CSV olarak yazar.

    df: open/high/low/close/volume (küçük harf) + DatetimeIndex.
    saat_yaz=False (günlük/haftalık/aylık indirmeler): tarih kolonuna
    YALNIZ tarih yazılır (yyyy-mm-dd); ayrı Time kolonu varsa başlıktan
    tamamen çıkarılır. TV günlük barına seans saati (örn. 09:00)
    iliştirilmiş gelse bile dosyada saat OLMAZ.
    """
    yol = Path(yol)
    bicim = dict(bicim) if bicim else _varsayilan_bicim()
    kolonlar = list(bicim["kolonlar"])
    kucuk = {str(k).strip().lower(): k for k in kolonlar}

    def bul(*adlar):
        for a in adlar:
            if a in kucuk:
                return kucuk[a]
        return None

    c_tarih = bul("date", "datetime", "tarih", "zaman")
    c_saat = bul("time", "saat")
    c_o, c_h, c_l = bul("open"), bul("high"), bul("low")
    c_c, c_v = bul("close"), bul("volume")
    if c_tarih is None or c_c is None:
        raise RuntimeError(
            f"Hedef CSV biçiminde 'Date' ve 'Close' kolonları bulunamadı: {kolonlar}"
        )

    if not saat_yaz:
        # günlük/haftalık/aylık: saat bilgisini tamamen kaldır
        c_saat = None
        saat_adlari = {str(k).strip().lower() for k in ("time", "saat")}
        kolonlar = [k for k in kolonlar if str(k).strip().lower() not in saat_adlari]

    idx = pd.DatetimeIndex(df.index)
    saatli = bool(((idx.hour != 0) | (idx.minute != 0)).any())
    fmt = bicim["tarih_fmt"]
    if not saat_yaz:
        fmt = fmt.split(" ")[0] if " " in fmt else fmt
    elif bicim["saat_ayri"]:
        fmt = fmt.split(" ")[0] if " " in fmt else fmt
    elif saatli and "%H" not in fmt:
        fmt = fmt + " %H:%M"

    ov = bool(bicim["ondalik_virgul"])
    satirlar = []
    for ts, satir in zip(idx, df.itertuples(index=False)):
        deger = {}
        deger[c_tarih] = ts.strftime(fmt)
        if c_saat:
            deger[c_saat] = ts.strftime(bicim.get("saat_fmt", "%H:%M"))
        for kolon, ad in ((c_o, "open"), (c_h, "high"), (c_l, "low"),
                          (c_c, "close"), (c_v, "volume")):
            if kolon:
                deger[kolon] = _sayi_yaz(getattr(satir, ad, float("nan")), ov)
        satirlar.append([deger.get(k, "") for k in kolonlar])

    cikti = pd.DataFrame(satirlar, columns=kolonlar)
    yol.parent.mkdir(parents=True, exist_ok=True)
    kodlama = "utf-8-sig" if bicim.get("bom") else "utf-8"
    cikti.to_csv(yol, sep=bicim["ayirac"], index=False, encoding=kodlama,
                 lineterminator="\n")
    return yol


# -------------------------------------------------------------- panel entegrasyonu --
def _mutlak_yol(yol):
    """Yolu mutlak ve normalize edilmiş döndürür.

    Göreli/bozuk yollar sessizce çalışma dizinine (panelin koştuğu yer,
    yani betiğin bulunduğu dizin) yazılmasın: hedef her zaman TAM yoldur;
    böylece diyalogda ve toplu indirme onayında birebir aynı yer görünür.
    """
    p = Path(str(yol).strip()).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    return Path(os.path.normpath(str(p)))


def hedef_dizin(panel, intraday):
    """Panelin veri klasörünü döndürür (intraday -> 60dk, değilse günlük).

    Kullanıcının kurulumu:
      60dk  -> D:\\new\\yeniden\\metastock-60dk-csv
      günlük -> D:\\new\\yeniden\\metastock-gun-csv
    Bunlar panel.veri (VeriPeriyot) özniteliklerinden okunur; okunamazsa
    fibo_kanal'daki KLASOR_60DK / KLASOR_GUNLUK sabitleri yedek olarak
    kullanılır (aynı klasörler). Dönen yol daima MUTLAKTIR; boş öznitelik
    değeri o adım için yok sayılır (betik dizinine sessiz yazım engeli).
    """
    veri = getattr(panel, "veri", None)
    ad = "csv_60dk_dizini" if intraday else "csv_gunluk_dizini"
    yol = getattr(veri, ad, None)
    if yol:
        return _mutlak_yol(yol)
    try:
        import fibo_kanal as fk
        sabit = "KLASOR_60DK" if intraday else "KLASOR_GUNLUK"
        yol = getattr(fk, sabit, None)
        if yol:
            return _mutlak_yol(yol)
    except Exception:
        pass
    return None


def periyot_etiketi(intraday):
    """Panel PERIYOTLAR değerine çevirir: intraday -> '60dk', değilse 'gunluk'."""
    return "60dk" if intraday else "gunluk"


def panel_kopyasi_yaz(sembol, kaynak_yol, hedef_dir, kopya_klasor):
    """Hedef, panelin gerçek veri klasöründen farklıysa CSV'yi oraya da yazar.

    Panel (panel.veri) ve fibo_kanal yalnız KENDİ klasörlerinden okur; kullanıcı
    SEÇ ile başka bir hedef belirlediyse indirme SEÇİLEN klasöre yazılır ama
    panelin o türdeki (60dk/gün) veri klasörüne de AYNI adda kopya düşer —
    böylece panel ve fibo kanal yeni veriyi görür. Betiğin bulunduğu dizine
    ASLA yazılmaz (eski _fibo_yedek_yaz davranışı kaldırıldı). Klasörler
    aynıysa kopya gerekmez.
    """
    try:
        if not kopya_klasor or hedef_dir is None:
            return None
        kopya = _mutlak_yol(kopya_klasor) / Path(kaynak_yol).name
        if kopya.resolve() == Path(hedef_dir).resolve():
            return None            # hedef zaten panelin klasörü; kopya gereksiz
        if kopya.resolve() == Path(kaynak_yol).resolve():
            return None            # kaynakla aynı dosya
        if not kopya.parent.exists():
            return None            # panel klasörü yoksa kopyanın yeri de yok
        shutil.copyfile(kaynak_yol, kopya)
        return kopya
    except Exception:
        return None


def sembol_yaz(df, sembol, hedef, bicim, intraday, kopya_klasor=None):
    """Tek sembolün CSV'sini TEK kapıdan yazar (tekil + toplu indirme ortak yolu).

    intraday=True (1dk–4sa) -> hedef klasöre saatli yazım; intraday=False
    (1gün/1hafta/1ay) -> yalnız tarih. 60dk/gün ayrımı ve hedef disiplini
    burada tek noktadan garanti edilir; betik dizinine hiçbir koşulda
    yazılmaz. Döndürür: (yazılan_yol, panel_kopyası_yolu|None).
    """
    yol = csv_yaz(df, Path(hedef) / f"{sembol}.csv", bicim, saat_yaz=intraday)
    kopya = panel_kopyasi_yaz(sembol, yol, hedef, kopya_klasor)
    return yol, kopya


def panele_uygula(panel, sembol, periyot):
    """Yeni sembolü panelin sembol listesine ekler ve veri yükler."""
    panele_sembol_ekle(panel, [sembol], periyot)


def panele_sembol_ekle(panel, semboller, periyot):
    """Sembolleri (tek/çok) panelin listesine ekler ve veri yüklemeyi tetikler.

    Toplu indirme sonrası tek veri_yukle çağrılır; seçili sembol geçerliyse
    korunur, değilse listenin ilk sembolü seçilir.
    """
    semboller = [str(s).strip().upper() for s in (semboller or []) if str(s).strip()]
    if not semboller:
        return
    mevcut = list(getattr(panel, "semboller", []) or [])
    birlesik = sorted(set(mevcut) | set(semboller))
    panel.semboller = birlesik
    try:
        panel.sembol_combo.configure(values=birlesik)
    except Exception:
        pass
    try:
        if str(panel.sembol_var.get()).strip().upper() not in birlesik:
            panel.sembol_var.set(semboller[0])
        panel.periyot_var.set(periyot)
    except Exception:
        pass
    panel.veri_yukle()


def tv_butonu_ekle(panel, text="TV VERİ"):
    """Panel üst çubuğuna (LOAD DATA yanıya) TV VERİ düğmesini ekler."""
    kontrol = panel.load_button.master          # header içindeki 'controls' çerçevesi
    dugme = tk.Button(
        kontrol,
        text=text,
        command=lambda: TVVeriDialog(panel),
        bg=YESEM,
        fg="white",
        activebackground=YESEM_AKTIF,
        activeforeground="white",
        relief="flat",
        padx=14,
        pady=9,
        font=("Segoe UI", 9, "bold"),
        cursor="hand2",
    )
    dugme.grid(row=1, column=3, padx=(12, 0))
    return dugme


# --------------------------------------------------------------------- diyalog --
class TVVeriDialog(tk.Toplevel):
    """TV veri indirme penceresi: BIST / Kripto seçimli."""

    def __init__(self, panel):
        super().__init__(panel)
        self.panel = panel
        self.title("TV Veri Yükle · BIST / Kripto (tvdatafeed-enhanced)")
        self.configure(bg=BG, padx=18, pady=14)
        self.resizable(False, False)
        self.transient(panel)
        self.grab_set()

        # kalıcı ayarlar: elle seçilen klasörler TÜR BAZINDA saklanır ve
        # panel kapatılıp açılsa bile hatırlanır (panel.py yanındaki json)
        self._sonuc = None          # işçi ilmek sonucu (ok, veri, hata)
        self._ilerleme = None       # toplu indirme ilerlemesi (isçi yazar, yoksa okur)
        self._iptal = False
        self._hedef = None
        self._ozel_hedefler = {"60dk": None, "gunluk": None}
        _kayitli = (ayar_oku().get("ozel_hedefler") or {})
        for _t in ("60dk", "gunluk"):
            _v = _kayitli.get(_t)
            if _v:
                self._ozel_hedefler[_t] = Path(_v)

        satir = 0

        def etiket(parent, metin, r, sutun=0, bold=False):
            tk.Label(
                parent, text=metin, bg=BG, fg=MUTED if not bold else TEXT,
                font=("Segoe UI", 8, "bold") if bold else ("Segoe UI", 8),
                anchor="w",
            ).grid(row=r, column=sutun, sticky="w", pady=(10, 2))

        baslik = tk.Label(
            self, text="TV'den VERİ İNDİR  ·  BIST (IMKB) / KRİPTO",
            bg=BG, fg=TEXT, font=("Segoe UI", 13, "bold"),
        )
        baslik.grid(row=satir, column=0, columnspan=3, sticky="w")
        satir += 1

        govde = tk.Frame(self, bg=BG)
        govde.grid(row=satir, column=0, columnspan=3, sticky="ew", pady=(6, 0))

        # VERİ KAYNAĞI
        etiket(govde, "VERİ KAYNAĞI", 0)
        self.kaynak_var = tk.StringVar(value=KAYNAKLAR[0])
        self.kaynak_combo = ttk.Combobox(
            govde, textvariable=self.kaynak_var, values=list(KAYNAKLAR),
            state="readonly", width=22,
        )
        self.kaynak_combo.grid(row=1, column=0, sticky="w")
        self.kaynak_combo.bind("<<ComboboxSelected>>", lambda _e: self._kaynak_degisti())

        # BORSA
        etiket(govde, "BORSA", 0, sutun=1)
        self.borsa_var = tk.StringVar(value="BIST")
        self.borsa_combo = ttk.Combobox(
            govde, textvariable=self.borsa_var, values=("BIST",),
            state="readonly", width=14,
        )
        self.borsa_combo.grid(row=1, column=1, sticky="w", padx=(16, 0))

        # SEMBOL + ARA
        etiket(govde, "SEMBOL", 2)
        self.sembol_var = tk.StringVar()
        self.sembol_combo = ttk.Combobox(
            govde, textvariable=self.sembol_var, values=[], width=22, state="normal",
        )
        self.sembol_combo.grid(row=3, column=0, sticky="w")
        self.ara_buton = tk.Button(
            govde, text="ARA", command=self._ara,
            bg=PANEL_ALT, fg=TEXT, activebackground=GRID, activeforeground=TEXT,
            relief="flat", padx=10, pady=4, font=("Segoe UI", 8, "bold"),
            cursor="hand2",
        )
        self.ara_buton.grid(row=3, column=1, sticky="w", padx=(16, 0))

        # ARALIK + BAR
        etiket(govde, "ARALIK", 4)
        self.aralik_var = tk.StringVar(value="1sa")
        self.aralik_combo = ttk.Combobox(
            govde, textvariable=self.aralik_var,
            values=[ad for ad, _a, _i in TV_ARALIKLAR],
            state="readonly", width=22,
        )
        self.aralik_combo.grid(row=5, column=0, sticky="w")
        self.aralik_combo.bind(
            "<<ComboboxSelected>>",
            lambda _e: (self._hedef_yenile(), self._ayar_kaydet()),
        )

        etiket(govde, "BAR SAYISI", 4, sutun=1)
        self.bar_var = tk.StringVar(value="2000")
        self.bar_spin = ttk.Spinbox(
            govde, from_=MIN_BAR, to=MAK_BAR, increment=100,
            textvariable=self.bar_var, width=14,
        )
        self.bar_spin.grid(row=5, column=1, sticky="w", padx=(16, 0))

        # HEDEF KLASÖR
        etiket(govde, "HEDEF KLASÖR (panelin veri klasörü)", 6)
        self.hedef_var = tk.StringVar(value="")
        self.hedef_giris = tk.Entry(
            govde, textvariable=self.hedef_var, width=52, state="readonly",
            readonlybackground=PANEL_ALT, fg=TEXT,
        )
        self.hedef_giris.grid(row=7, column=0, columnspan=2, sticky="w")
        self.hedef_sec = tk.Button(
            govde, text="SEÇ", command=self._hedef_sec,
            bg=PANEL_ALT, fg=TEXT, activebackground=GRID, activeforeground=TEXT,
            relief="flat", padx=10, pady=4, font=("Segoe UI", 8, "bold"),
            cursor="hand2",
        )
        self.hedef_sec.grid(row=7, column=2, sticky="w", padx=(8, 0))
        self.hedef_sifirla = tk.Button(
            govde, text="SIFIRLA", command=self._hedef_sifirla,
            bg=PANEL_ALT, fg=TEXT, activebackground=GRID, activeforeground=TEXT,
            relief="flat", padx=10, pady=4, font=("Segoe UI", 8, "bold"),
            cursor="hand2",
        )
        self.hedef_sifirla.grid(row=7, column=3, sticky="w", padx=(6, 0))

        # TV HESABI (opsiyonel)
        etiket(govde, "TV KULLANICI ADI (opsiyonel)", 8)
        self.kullanici_giris = tk.Entry(govde, width=24)
        self.kullanici_giris.grid(row=9, column=0, sticky="w")
        etiket(govde, "TV ŞİFRE (opsiyonel)", 8, sutun=1)
        self.sifre_giris = tk.Entry(govde, width=16, show="•")
        self.sifre_giris.grid(row=9, column=1, sticky="w", padx=(16, 0))

        # TOPLU İNDİRME (BIST endeks listeleri)
        etiket(govde, "TOPLU İNDİRME (BIST)", 10)
        self.toplu_var = tk.StringVar(value=TOPLU_LISTELER[0])
        self.toplu_combo = ttk.Combobox(
            govde, textvariable=self.toplu_var, values=list(TOPLU_LISTELER),
            state="readonly", width=22,
        )
        self.toplu_combo.grid(row=11, column=0, sticky="w")
        self.toplu_indir = tk.Button(
            govde, text="TOPLU İNDİR", command=self._toplu_indir,
            bg=YESEM, fg="white",
            activebackground=YESEM_AKTIF, activeforeground="white",
            relief="flat", padx=12, pady=6, font=("Segoe UI", 8, "bold"),
            cursor="hand2",
        )
        self.toplu_indir.grid(row=11, column=1, sticky="w", padx=(16, 0))
        self.durdur_buton = tk.Button(
            govde, text="DURDUR", command=self._toplu_durdur,
            bg=PANEL_ALT, fg=TEXT, activebackground=GRID, activeforeground=TEXT,
            relief="flat", padx=10, pady=6, font=("Segoe UI", 8, "bold"),
            state="disabled", cursor="hand2",
        )
        self.durdur_buton.grid(row=11, column=2, sticky="w", padx=(8, 0))

        satir += 1
        islem = tk.Frame(self, bg=BG)
        islem.grid(row=satir, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        self.indir_buton = tk.Button(
            islem, text="İNDİR VE PANELE YÜKLE", command=self._indir,
            bg=YESEM, fg="white",
            activebackground=YESEM_AKTIF, activeforeground="white",
            relief="flat", padx=18, pady=9, font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        self.indir_buton.grid(row=0, column=0, sticky="w")
        self.kapat_buton = tk.Button(
            islem, text="KAPAT", command=self.destroy,
            bg=PANEL_ALT, fg=TEXT, activebackground=GRID, activeforeground=TEXT,
            relief="flat", padx=14, pady=9, font=("Segoe UI", 9),
            cursor="hand2",
        )
        self.kapat_buton.grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.durum_var = tk.StringVar(value="Hazır.")
        self.durum = tk.Label(
            islem, textvariable=self.durum_var, bg=BG, fg=MUTED,
            font=("Segoe UI", 8), anchor="w", justify="left", wraplength=360,
        )
        self.durum.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        satir += 1
        ipucu = (
            "Notlar: Anonim bağlantıda TradingView verisi sınırlı olabilir; ücretsiz "
            "hesap bilgisi girerseniz daha fazla bar iner. Tek çekimde en fazla "
            f"{MAK_BAR:,} bar. Günlük/haftalık/aylık indirmelerde CSV'ye yalnız "
            "tarih yazılır. Dosyalar yalnız HEDEF klasöre yazılır; betiğin "
            "(panel.py'nin) bulunduğu dizine ASLA yazılmaz: 1dk–4sa 60dk "
            "klasörüne, 1gün/1hafta/1ay gün klasörüne gider. SEÇ ile seçtiğiniz "
            "klasör KALICIDIR (panel.py yanındaki tv_veri_ayarlar.json'a yazılır; "
            "panel kapansa bile hatırlanır), SIFIRLA otomatik klasöre döndürür. "
            "TOPLU İNDİRME BIST 30/50/100 listeleriyle çalışır; tüm piyasa için "
            "panel.py yanına bist_tumu.txt koyun (her satıra bir sembol). Toplu "
            "indirmede semboller arası 1 sn beklenir; hata alırsanız DURDUR'a "
            "basıp TV hesabı girerek deneyin."
        )
        tk.Label(
            self, text=ipucu, bg=BG, fg=MUTED, font=("Segoe UI", 8),
            anchor="w", justify="left", wraplength=460,
        ).grid(row=satir, column=0, columnspan=3, sticky="w", pady=(12, 0))

        # kayıtlı ayarları uygula: kullanıcı bir kez seçti mi, bir daha seçmez
        _kayit = ayar_oku()
        if _kayit.get("kaynak") in KAYNAKLAR:
            self.kaynak_var.set(_kayit["kaynak"])
        self._kaynak_degisti()
        if self.kaynak_var.get() == "Kripto" and str(_kayit.get("borsa") or "").upper() in KRIPTO_BORSALARI:
            self.borsa_var.set(str(_kayit["borsa"]).upper())
        if _kayit.get("aralik") in [ad for ad, _a, _i in TV_ARALIKLAR]:
            self.aralik_var.set(_kayit["aralik"])
        try:
            _bar = int(_kayit.get("bar"))
            self.bar_var.set(str(max(MIN_BAR, min(MAK_BAR, _bar))))
        except Exception:
            pass

        self._hedef_yenile()
        self.sembol_combo.focus_set()

    # ---- davranışlar ------------------------------------------------------
    def _hedef_coz(self, intraday):
        """Yazım anında hedef klasör.

        Elle seçilen klasör (SEÇ) TÜR BAZINDA ve KALICIDIR: 60dk türünde
        seçildiyse yalnız intraday indirmelerde, günlük türünde seçildiyse
        yalnız 1gün/1hafta/1ay indirmelerde geçerlidir; panel kapatılıp
        açılsa bile hatırlanır (tv_veri_ayarlar.json). Kayıtlı seçim yoksa
        otomatik hedef (panel/fibo klasörleri) kullanılır.
        """
        tip = "60dk" if intraday else "gunluk"
        ozel = self._ozel_hedefler.get(tip)
        if ozel is not None:
            return ozel
        try:
            return hedef_dizin(self.panel, intraday)
        except Exception:
            return None

    def _ayar_kaydet(self):
        """Geçerli seçimleri kalıcı ayar dosyasına yazar (json)."""
        try:
            bar = int(self.bar_var.get())
        except Exception:
            bar = 2000
        ayar_yaz({
            "kaynak": self.kaynak_var.get(),
            "borsa": self.borsa_var.get(),
            "aralik": self.aralik_var.get(),
            "bar": max(MIN_BAR, min(MAK_BAR, bar)),
            "ozel_hedefler": {
                k: (str(v) if v else None)
                for k, v in self._ozel_hedefler.items()
            },
        })

    def _tip_suanki(self):
        """Seçili aralığın türü ('60dk' / 'gunluk'); belirlenemezse None."""
        try:
            _adaylar, intraday = aralik_bilgisi(self.aralik_var.get())
            return "60dk" if intraday else "gunluk"
        except Exception:
            return None

    def _kaynak_degisti(self):
        kripto = self.kaynak_var.get() == "Kripto"
        if kripto:
            self.borsa_combo.configure(values=list(KRIPTO_BORSALARI), state="readonly")
            self.borsa_var.set("BINANCE")
            self.sembol_combo.configure(values=[])
            self.sembol_var.set("")
        else:
            self.borsa_combo.configure(values=("BIST",), state="disabled")
            self.borsa_var.set("BIST")
            self.sembol_combo.configure(values=[])
            self.sembol_var.set("")
        if hasattr(self, "bar_var"):
            self._ayar_kaydet()

    def _hedef_yenile(self):
        tip = self._tip_suanki()
        intraday = None if tip is None else (tip == "60dk")
        self._hedef = self._hedef_coz(intraday) if intraday is not None else None
        if self._hedef is not None:
            elle = tip is not None and self._ozel_hedefler.get(tip) is not None
            ek = "  (elle seçildi — kalıcı)" if elle else "  (otomatik)"
            self.hedef_var.set(str(self._hedef) + ek)
        else:
            self.hedef_var.set("(klasör bulunamadı — SEÇ ile belirtin)")

    def _hedef_sec(self):
        baslangic = str(self._hedef) if self._hedef is not None else str(Path.home())
        secim = filedialog.askdirectory(title="CSV'nin yazılacağı klasör",
                                        initialdir=baslangic, parent=self)
        if not secim:
            return
        tip = self._tip_suanki()
        if tip is not None:
            # KALICI: panel.py yanındaki tv_veri_ayarlar.json'a yazılır;
            # panel kapatılıp açılsa bile aynı klasör kullanılır.
            self._ozel_hedefler[tip] = Path(secim)
            self._ayar_kaydet()
            self._hedef_yenile()

    def _hedef_sifirla(self):
        """Şu anki türün elle seçimini siler; otomatik klasöre döner."""
        tip = self._tip_suanki()
        if tip is None:
            return
        self._ozel_hedefler[tip] = None
        self._ayar_kaydet()
        self._hedef_yenile()

    def _kimlik_bilgisi(self):
        kullanici = self.kullanici_giris.get().strip()
        sifre = self.sifre_giris.get().strip()
        if bool(kullanici) != bool(sifre):
            raise RuntimeError("TV hesabı: kullanıcı adı ve şifreyi birlikte girin (ya da ikisini boş bırakın).")
        return kullanici, sifre

    def _ara(self):
        sorgu = self.sembol_var.get().strip()
        if not sorgu:
            messagebox.showinfo("Sembol arama", "Önce aramak istediğiniz harfleri/kodu yazın.", parent=self)
            return
        try:
            kullanici, sifre = self._kimlik_bilgisi()
        except Exception as hata:
            messagebox.showwarning("TV hesabı", str(hata), parent=self)
            return
        borsa = self.borsa_var.get().strip()
        self.ara_buton.configure(state="disabled", text="...")
        self.durum_var.set(f"{borsa}'de '{sorgu}' aranıyor…")
        self.update_idletasks()

        def isci():
            try:
                adlar = tv_sembol_ara(sorgu, borsa, kullanici, sifre)
                self._sonuc = ("ara", True, adlar, None)
            except Exception as hata:
                self._sonuc = ("ara", False, [], str(hata))

        threading.Thread(target=isci, daemon=True).start()
        self.after(80, lambda: self._yoska("ara"))

    def _indir(self):
        sembol = _sembol_temiz(self.sembol_var.get(), self.borsa_var.get())
        if not sembol:
            messagebox.showwarning("Sembol", "Bir sembol girin (örn. THYAO veya BTCUSDT).", parent=self)
            return
        hedef = self._hedef
        if hedef is None:
            messagebox.showwarning(
                "Hedef klasör",
                "Panelin veri klasörü bulunamadı. Önce SEÇ ile bir klasör belirtin.",
                parent=self,
            )
            return
        try:
            kullanici, sifre = self._kimlik_bilgisi()
        except Exception as hata:
            messagebox.showwarning("TV hesabı", str(hata), parent=self)
            return
        try:
            bar = int(self.bar_var.get())
        except Exception:
            messagebox.showwarning("Bar sayısı", "Geçerli bir sayı girin.", parent=self)
            return

        borsa = self.borsa_var.get().strip()
        aralik = self.aralik_var.get()
        self._ayar_kaydet()
        self.indir_buton.configure(state="disabled")
        self.toplu_indir.configure(state="disabled")
        self.durum_var.set(f"İndiriliyor: {borsa}:{sembol} · {aralik} · {bar} bar …")
        self.durum.configure(fg=MUTED)
        self.update_idletasks()

        def isci():
            try:
                df = tv_veri_cek(borsa, sembol, aralik, bar, kullanici, sifre)
                self._sonuc = ("indir", True, df, None)
            except Exception as hata:
                self._sonuc = ("indir", False, None, str(hata))

        threading.Thread(target=isci, daemon=True).start()
        self.after(80, lambda: self._yoska("indir"))

    def _toplu_indir(self):
        """Seçili BIST listesini (30/50/100/TÜMÜ) sırayla indirir.

        Tek bağlantı + semboller arası 1 sn bekleme (TV hız limiti); ilerleme
        durum satırında akar, DURDUR ile yarıda kesilebilir. Hedef klasör,
        aralık ve bar sayısı yukarıdaki seçimlerden alınır.
        """
        liste_ad = self.toplu_var.get()
        semboller, liste_notu = toplu_liste_oku(liste_ad)
        if not semboller:
            messagebox.showwarning("Toplu liste", "Sembol listesi boş.", parent=self)
            return
        try:
            kullanici, sifre = self._kimlik_bilgisi()
            bar = int(self.bar_var.get())
        except Exception as hata:
            messagebox.showwarning("Toplu indirme", str(hata), parent=self)
            return
        aralik = self.aralik_var.get()
        try:
            _adaylar, intraday = aralik_bilgisi(aralik)
        except Exception as hata:
            messagebox.showwarning("Aralık", str(hata), parent=self)
            return
        hedef = self._hedef_coz(intraday)
        if hedef is None:
            messagebox.showwarning(
                "Hedef klasör",
                "Panelin veri klasörü bulunamadı. SEÇ ile belirtin.",
                parent=self,
            )
            return
        # panelin GERÇEK veri klasörü (SEÇ override'ı yok sayılır): hedef
        # farklıysa verinin panelde/fiboda da görünmesi için oraya kopya düşer
        kopya_klasor = hedef_dizin(self.panel, intraday)
        periyot = periyot_etiketi(intraday)
        tahmin = max(1, (len(semboller) * 2 + 59) // 60)
        tip = "60dk" if intraday else "gunluk"
        tur = "60dk" if intraday else "günlük"
        etiket = ("elle seçildi — kalıcı"
                  if self._ozel_hedefler.get(tip) is not None else "otomatik")
        kopya_notu = ""
        try:
            if kopya_klasor is not None and \
                    Path(kopya_klasor).resolve() != Path(hedef).resolve():
                kopya_notu = (f"\n\nPanel veri klasörüne de kopya yazılacak:\n"
                              f"{kopya_klasor}")
        except Exception:
            pass
        tamam = messagebox.askyesno(
            "Toplu indirme",
            f"{liste_ad} · {len(semboller)} sembol · {aralik} ({tur}) · {bar} bar\n\n"
            f"{tur.upper()} verileri ŞURAYA yazılacak ({etiket}):\n{hedef}"
            f"{kopya_notu}\n\n"
            f"Liste: {liste_notu}\n"
            f"Tahmini süre ~{tahmin} dk. Devam edilsin mi?",
            parent=self,
        )
        if not tamam:
            return
        self._ayar_kaydet()
        self._iptal = False
        self._ilerleme = None
        self._sonuc = None
        self.indir_buton.configure(state="disabled")
        self.toplu_indir.configure(state="disabled")
        self.durdur_buton.configure(state="normal")
        self.durum_var.set(
            f"Toplu indirme başlıyor: {len(semboller)} sembol → {hedef}")
        self.durum.configure(fg=MUTED)
        self.update_idletasks()

        def isci():
            indirilen, hatalar = [], []
            try:
                TvDatafeed, Interval = kutuphane_yukle()
                tv = _tv_baglan(kullanici, sifre)
            except Exception as hata:
                self._sonuc = ("toplu", False, ([], [("", str(hata))], False,
                                                liste_ad, liste_notu, periyot,
                                                hedef), None)
                return
            bicim = ilk_csv_bicimi(hedef) or _varsayilan_bicim()
            for i, sembol in enumerate(semboller, 1):
                if self._iptal:
                    break
                try:
                    df = tv_veri_cek("BIST", sembol, aralik, bar,
                                     tv=tv, Interval=Interval)
                    # 60dk/gün ayrımı tek kapıda: sembol_yaz (hedef klasöre yazar)
                    sembol_yaz(df, sembol, hedef, bicim, intraday, kopya_klasor)
                    indirilen.append(sembol)
                except Exception as hata:
                    msj = str(hata).strip().splitlines()[0] if str(hata).strip() else "hata"
                    hatalar.append((sembol, msj))
                self._ilerleme = (i, len(semboller), sembol)
                time.sleep(1.0)      # TradingView hız limitine saygı
            self._sonuc = ("toplu", True, (indirilen, hatalar, self._iptal,
                                           liste_ad, liste_notu, periyot,
                                           hedef), None)

        threading.Thread(target=isci, daemon=True).start()
        self.after(80, lambda: self._yoska("toplu"))

    def _toplu_durdur(self):
        self._iptal = True
        self.durdur_buton.configure(state="disabled")
        self.durum_var.set("Durduruluyor… (o anki sembol bitince durur)")

    def _yoska(self, mod):
        if not self.winfo_exists():
            return
        if self._sonuc is None:
            if mod == "toplu" and self._ilerleme is not None:
                i, toplam, simge = self._ilerleme
                self.durum_var.set(f"Toplu indirme: {i}/{toplam} · {simge} …")
            self.after(80, lambda: self._yoska(mod))
            return
        tur, ok, veri, hata = self._sonuc
        self._sonuc = None
        if tur == "ara":
            self.ara_buton.configure(state="normal", text="ARA")
            if ok and veri:
                self.sembol_combo.configure(values=veri)
                self.sembol_var.set(veri[0])
                self.durum_var.set(f"{len(veri)} sembol bulundu; listeden seçin.")
                self.durum.configure(fg=TEXT)
            elif ok:
                self.durum_var.set("Sonuç bulunamadı (farklı yazım deneyin).")
                self.durum.configure(fg=MUTED)
            else:
                self.durum_var.set(f"Arama başarısız: {hata}")
                self.durum.configure(fg=HATA_KIRMIZI)
            return

        # ---- toplu ----
        if tur == "toplu":
            self.indir_buton.configure(state="normal")
            self.toplu_indir.configure(state="normal")
            self.durdur_buton.configure(state="disabled")
            if not ok:
                _i, _h, _ip, _la, _ln, _p, _hd = veri
                msj = _h[0][1] if _h else "bilinmeyen hata"
                self.durum_var.set(f"Toplu indirme başlayamadı: {msj}")
                self.durum.configure(fg=HATA_KIRMIZI)
                return
            indirilen, hatalar, iptal, liste_ad, liste_notu, periyot, hedef = veri
            parcalar = [f"{len(indirilen)} sembol yazıldı → {hedef} "
                        f"({liste_ad} · {liste_notu})"]
            if iptal:
                parcalar.append("DURDUR ile yarıda kesildi")
            if hatalar:
                ornek = ", ".join(s for s, _m in hatalar[:6])
                parcalar.append(
                    f"{len(hatalar)} başarısız: {ornek}{' …' if len(hatalar) > 6 else ''}"
                )
            self.durum.configure(fg=OK_YESIL if indirilen else HATA_KIRMIZI)
            self.durum_var.set("\n".join(parcalar) + f"\nPanel {periyot} listesi tazeleniyor…")
            try:
                panele_sembol_ekle(self.panel, indirilen, periyot)
            except Exception as hata:
                self.durum_var.set(self.durum_var.get() + f"\nPanel tazelenemedi: {hata}")
                self.durum.configure(fg=HATA_KIRMIZI)
            return

        # ---- indir ----
        self.indir_buton.configure(state="normal")
        self.toplu_indir.configure(state="normal")
        self.durdur_buton.configure(state="disabled")
        if not ok:
            self.durum_var.set(f"İndirilemedi: {hata}")
            self.durum.configure(fg=HATA_KIRMIZI)
            return

        df, sembol = veri, _sembol_temiz(self.sembol_var.get(), self.borsa_var.get())
        try:
            _adaylar, intraday = aralik_bilgisi(self.aralik_var.get())
            # yazım anında TAZE çözüm: 60dk <-> günlük yanlış klasöre yazılmasın
            hedef = self._hedef_coz(intraday)
            if hedef is None:
                raise RuntimeError("hedef klasör çözülemedi (SEÇ ile belirtin)")
            bicim = ilk_csv_bicimi(hedef) or _varsayilan_bicim()
            kopya_klasor = hedef_dizin(self.panel, intraday)
            # günlük/haftalık/aylık (intraday=False) -> CSV'ye saat YAZILMAZ
            yol, _kopya = sembol_yaz(df, sembol, hedef, bicim, intraday,
                                     kopya_klasor)
        except Exception as hata:
            self.durum_var.set(f"CSV yazılamadı: {hata}")
            self.durum.configure(fg=HATA_KIRMIZI)
            return

        periyot = periyot_etiketi(intraday)
        self.durum.configure(fg=OK_YESIL)
        self.durum_var.set(
            f"{sembol}: {len(df):,} bar yazıldı → {yol}\nPanel {periyot} periyoduyla yükleniyor…"
        )
        try:
            panele_uygula(self.panel, sembol, periyot)
        except Exception as hata:
            self.durum_var.set(
                f"CSV yazıldı ({yol}) ama panel yüklemesi hata verdi: {hata}\n"
                "Panele dönüp sembolü seçerek LOAD DATA'ya basın."
            )
            self.durum.configure(fg=HATA_KIRMIZI)
# --------------------------------------------------------------- standalone panel --
class _MiniVeri:
    """panel.veri (VeriPeriyot) yerine geçen minimal taşıyıcı."""
    def __init__(self, kok):
        self.csv_60dk_dizini = str(kok / "csv_60dk")
        self.csv_gunluk_dizini = str(kok / "csv_gunluk")


class MiniPanel(tk.Tk):
    """panel_tvdata_ekleri.py'yi tek başına çalıştıran minimal panel.

    panel.py'ye ihtiyaç duymadan TV VERİ diyaloğunu açar; indirilen CSV'leri
    betiğin yanındaki csv_60dk / csv_gunluk klasörlerine yazar ve seçili
    sembolün önizlemesini gösterir.
    """

    def __init__(self):
        super().__init__()
        self.title("TV Veri İndirici · Standalone")
        self.configure(bg=BG)
        self.geometry("1000x640")

        kok = _modul_dizini()
        self.veri = _MiniVeri(kok)
        Path(self.veri.csv_60dk_dizini).mkdir(parents=True, exist_ok=True)
        Path(self.veri.csv_gunluk_dizini).mkdir(parents=True, exist_ok=True)

        self.semboller = self._sembolleri_tara()
        self.sembol_var = tk.StringVar(value=(self.semboller[0] if self.semboller else ""))
        self.periyot_var = tk.StringVar(value="gunluk")

        # -------- header ---------------------------------------------------
        header = tk.Frame(self, bg=BG, padx=14, pady=10)
        header.pack(fill="x")

        kontrol = tk.Frame(header, bg=BG)
        kontrol.pack(side="left")

        self.load_button = tk.Button(
            kontrol, text="LOAD DATA", command=self.veri_yukle,
            bg=HATA_KIRMIZI, fg="white", activebackground="#d15a52",
            activeforeground="white", relief="flat", padx=14, pady=9,
            font=("Segoe UI", 9, "bold"), cursor="hand2",
        )
        self.load_button.grid(row=1, column=0)
        # tv_butonu_ekle() aynı frame'e (row=1, column=3) butonu koyacak;
        # column 3'ü boş bırakıyoruz.

        bilgi = tk.Frame(header, bg=BG)
        bilgi.pack(side="left", padx=(20, 0))

        tk.Label(bilgi, text="SEMBOL", bg=BG, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w")
        self.sembol_combo = ttk.Combobox(
            bilgi, textvariable=self.sembol_var, values=self.semboller,
            width=16, state="readonly",
        )
        self.sembol_combo.grid(row=1, column=0, sticky="w")

        tk.Label(bilgi, text="PERİYOT", bg=BG, fg=MUTED,
                 font=("Segoe UI", 8, "bold")).grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Combobox(
            bilgi, textvariable=self.periyot_var, values=("60dk", "gunluk"),
            width=10, state="readonly",
        ).grid(row=1, column=1, sticky="w", padx=(12, 0))

        tk.Button(
            bilgi, text="YENİLE", command=self._yenile_semboller,
            bg=PANEL_ALT, fg=TEXT, activebackground=GRID, activeforeground=TEXT,
            relief="flat", padx=10, pady=4, font=("Segoe UI", 8, "bold"),
            cursor="hand2",
        ).grid(row=1, column=2, sticky="w", padx=(8, 0))

        # TV VERİ butonunu ekle (panel.load_button.master -> kontrol frame)
        tv_butonu_ekle(self)

        # -------- önizleme -------------------------------------------------
        self.metin = tk.Text(
            self, bg=PANEL_ALT, fg=TEXT, font=("Consolas", 9),
            relief="flat", padx=10, pady=10, wrap="none",
        )
        self.metin.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self._metin_yaz(self._ilk_metin())

    # ---- yardımcılar ------------------------------------------------------
    def _sembolleri_tara(self):
        adlar = set()
        for k in (self.veri.csv_60dk_dizini, self.veri.csv_gunluk_dizini):
            p = Path(k)
            if p.exists():
                for f in p.glob("*.csv"):
                    adlar.add(f.stem.upper())
        return sorted(adlar)

    def _yenile_semboller(self):
        self.semboller = self._sembolleri_tara()
        self.sembol_combo.configure(values=self.semboller)
        if self.semboller and not self.sembol_var.get():
            self.sembol_var.set(self.semboller[0])

    def _metin_yaz(self, metin):
        self.metin.configure(state="normal")
        self.metin.delete("1.0", "end")
        self.metin.insert("end", metin)
        self.metin.configure(state="disabled")

    def _ilk_metin(self):
        return (
            "TV VERİ butonuna basarak TradingView'dan veri indirebilirsiniz.\n\n"
            f"60dk klasörü    : {self.veri.csv_60dk_dizini}\n"
            f"Günlük klasörü  : {self.veri.csv_gunluk_dizini}\n\n"
            "İndirilen CSV'ler bu klasörlere yazılır. Sembol seçip LOAD DATA'ya\n"
            "basınca önizleme burada görünür. Klasörleri TV VERİ penceresindeki\n"
            "SEÇ düğmesiyle değiştirebilirsiniz (kalıcıdır).\n"
        )

    # ---- panel arayüzü (panel.py'nin yerine geçen metot) ------------------
    def veri_yukle(self):
        sembol = self.sembol_var.get().strip().upper()
        periyot = self.periyot_var.get()
        if not sembol:
            self._metin_yaz("Önce bir sembol seçin.")
            return
        klasor = (self.veri.csv_60dk_dizini if periyot == "60dk"
                  else self.veri.csv_gunluk_dizini)
        yol = Path(klasor) / f"{sembol}.csv"
        if not yol.exists():
            self._metin_yaz(
                f"Dosya bulunamadı:\n  {yol}\n\n"
                "Önce TV VERİ ile indirin veya YENİLE'ye basın."
            )
            return
        try:
            df = pd.read_csv(yol)
            ozet = (
                f"Dosya    : {yol}\n"
                f"Satır    : {len(df):,}\n"
                f"Kolonlar : {list(df.columns)}\n\n"
                f"İlk 20 satır:\n{df.head(20).to_string()}\n"
            )
            if len(df) > 20:
                ozet += f"\n... son 5 satır:\n{df.tail(5).to_string()}"
        except Exception as hata:
            ozet = f"Dosya okunamadı: {yol}\nHata: {hata}"
        self._metin_yaz(ozet)


def main():
    panel = MiniPanel()

    # withdraw() YERİNE: pencereyi minik ve ekran dışına yerleştir.
    # Böylece Tk açısından hâlâ "mapped" sayılır → transient() ve
    # grab_set() sorunsuz çalışır, TV VERİ penceresi görünür olur.
    panel.geometry("10x10+-5000+-5000")
    panel.update_idletasks()

    def ac():
        try:
            dlg = TVVeriDialog(panel)
            dlg.lift()
            dlg.focus_force()
            dlg.protocol("WM_DELETE_WINDOW", panel.destroy)
        except Exception as hata:
            # Bir şey patlarsa sessizce ölmeyelim; konsola yazıp paneli göster
            import traceback
            traceback.print_exc()
            panel.deiconify()                 # paneli geri getir
            panel.geometry("1000x640+80+80")
            messagebox.showerror(
                "TV Veri penceresi açılamadı",
                f"{hata}\n\nDetaylar konsolda.",
                parent=panel,
            )

    panel.after(250, ac)     # WM'nin pencereyi haritalaması için biraz bekle
    panel.mainloop()

if __name__ == "__main__":
    main()