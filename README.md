# 📈 BIST Verilerini İndir

Bu depo, **Borsa İstanbul (BIST)** hisselerine ait tarihsel fiyat verilerini, temel analiz tablolarını (Gelir Tablosu, Bilanço, Nakit Akış Tablosu), XU100 endeks verilerini ve **TradingView üzerinden BIST/Kripto verilerini** **Python** kullanarak indirmenizi, düzenlemenizi ve yerel bilgisayarınıza kaydetmenizi sağlayan betikleri içerir.

Veri kaynağı olarak **`isyatirimhisse`**, **`yfinance`** ve **`tvdatafeed-enhanced`** kütüphaneleri kullanılmaktadır.

---

## 🚀 Özellikler

- **XU100 ve Hisse Fiyat Verileri:** `yfinance` ile BIST hisselerinin ve XU100 endeksinin tüm tarihsel verilerini CSV olarak indirir.
- **Temel Analiz Verileri (isyatirim):** `isyatirimhisse` ile belirtilen hisselerin Gelir Tablosu, Bilanço ve Nakit Akış Tablosu verilerini Excel formatında indirir.
- **Temel Analiz Verileri (yahoo):** `yfinance` ile herhangi bir hissenin finansal tablolarını Excel'e aktarır.
- **Toplu Veri İndirme:** `Sirketler.xlsx` dosyasındaki hisse kodlarını okuyarak her bir hisse için ayrı ayrı tarihsel veri indirir.
- **Excel → CSV Dönüşümü:** İndirilen Excel dosyalarını standartlaştırılmış sütun isimleriyle CSV formatına çevirir.
- **CSV Temizleme:** CSV dosyalarındaki eksik sayısal verileri medyan ile doldurarak veri setini temizler.
- **🆕 TradingView Üzerinden Canlı Veri (TV VERİ):** `panel_tvdata_ekleri.py` modülü ile BIST (IMKB) ve Kripto borsalarından TradingView verisi indirir; panelin kendi CSV klasörlerine mevcut biçimi taklit ederek yazar.

---

## 📋 Gereksinimler

Betikleri çalıştırabilmek için sisteminizde **Python 3.7+** kurulu olmalıdır. Gerekli kütüphaneleri yüklemek için terminalinizde aşağıdaki komutu çalıştırın:

```bash
pip install yfinance pandas isyatirimhisse openpyxl tvdatafeed-enhanced
```

> **Not:** `isyatirimhisse` kütüphanesi hakkında detaylı bilgi için [PyPI sayfasını](https://pypi.org/project/isyatirimhisse/) ziyaret edebilirsiniz. `yfinance` için [buraya](https://pypi.org/project/yfinance/), `tvdatafeed-enhanced` için [buraya](https://pypi.org/project/tvdatafeed-enhanced/) göz atabilirsiniz.

---

## 📂 Dosya Yapısı ve Betik Açıklamaları

| Dosya Adı | Açıklama |
|---|---|
| `Hisse_verilerini_indir.py` | `yfinance` kullanarak önceden tanımlanmış BIST hisselerinin ve XU100 endeksinin tüm tarihsel verilerini `XU100/` klasörüne CSV olarak kaydeder. |
| `temel analiz isyatirim.py` | `isyatirimhisse` ile belirtilen hisselerin (ör. THYAO, PGSUS, BIMAS, TUPRS) 2013–2023 yılları arasındaki finansal tablolarını Excel olarak indirir. |
| `yahoo_temel_analiz.py` | `yfinance` ile `TICKER` değişkeninde belirtilen hissenin Gelir Tablosu, Bilanço ve Nakit Akış Tablosunu ayrı Excel dosyalarına kaydeder. |
| `verileri indir isyatirim.py` | `sirketler/sirketler.xlsx` dosyasının **XU100** sayfasındaki hisse kodlarını okur ve her bir hisse için 1970'ten itibaren tarihsel veriyi Excel olarak indirir. |
| `veirleri csv yap.py` | Bulunduğu dizindeki tüm `.xlsx` dosyalarını okur, gerekli sütunları seçer ve `isyatirim/` klasörüne `.is.csv` uzantılı CSV dosyaları olarak kaydeder. |
| `csv düzeltici.py` | `isyatirim/` klasöründeki tüm CSV dosyalarını tarar, sayısal sütunlardaki eksik değerleri medyan ile doldurur ve dosyaları düzeltilmiş haliyle tekrar kaydeder. |
| `Sirketler.xlsx` | `verileri indir isyatirim.py` betiğinin kullandığı, hisse kodlarını içeren Excel dosyasıdır. |
| **`panel_tvdata_ekleri.py`** | **🆕 TradingView üzerinden BIST/Kripto verisi indiren panel eki. Bkz. aşağıdaki ayrı bölüm.** |

---

## ⚙️ Kullanım Adımları

### 1. XU100 ve Hisse Fiyat Verilerini İndirme (`yfinance`)

```bash
python Hisse_verilerini_indir.py
```

- Betik, içinde tanımlı olan hisse sembollerini (`XU100.IS`, `AKBNK.IS`, `THYAO.IS` vb.) `yfinance` üzerinden çeker.
- Veriler, çalıştırılan dizinde otomatik olarak oluşturulan **`XU100/`** klasörüne `HISSEKODU.IS.CSV` formatında kaydedilir.
- **Yeni hisse eklemek için:** Betik içindeki `symbols` listesine `"OYAKC.IS"` formatında ekleme yapabilirsiniz.

### 2. Temel Analiz Verilerini İndirme (isyatirimhisse)

```bash
python "temel analiz isyatirim.py"
```

- Betik içindeki `symbols` listesinde belirtilen hisseler için `start_year` ve `end_year` aralığındaki finansal tabloları Excel olarak indirir.
- İndirilen dosyalar, `isyatirimhisse` kütüphanesinin varsayılan davranışına göre kaydedilir.

### 3. Temel Analiz Verilerini İndirme (yahoo)

```bash
python yahoo_temel_analiz.py
```

- Betik içindeki `TICKER` değişkenine istediğiniz hissenin kodunu (`"DOCO.IS"` gibi) yazın.
- Çalıştırıldığında üç ayrı Excel dosyası oluşturur:
  - `gelir-tablosu.xlsx`
  - `balance_bilanco.xlsx`
  - `nakit_akış.xlsx`

### 4. Toplu Veri İndirme (`Sirketler.xlsx` üzerinden)

```bash
python "verileri indir isyatirim.py"
```

- `sirketler/sirketler.xlsx` dosyasının **XU100** sayfasındaki `Kod` sütununu okur.
- Listedeki her hisse için 02.01.1970 tarihinden itibaren tarihsel veriyi `HISSEKODU.xlsx` olarak kaydeder.
- **Önemli:** Bu betiğin çalışması için `sirketler` adında bir klasör oluşturup içine `sirketler.xlsx` dosyasını koymanız gerekir.

### 5. Excel Dosyalarını CSV'ye Dönüştürme

```bash
python "veirleri csv yap.py"
```

- Betiğin bulunduğu dizindeki tüm `.xlsx` dosyalarını tarar.
- `DATE`, `CLOSING_TL`, `HIGH_TL`, `LOW_TL`, `VOLUME_TL`, `CLOSING_USD`, `XU100_TL` sütunlarını seçer ve sütun adlarını standart OHLCV formatına dönüştürür.
- Dönüştürülen dosyaları `isyatirim/` klasörüne `DOSYAADI.is.csv` olarak kaydeder.

### 6. CSV Dosyalarındaki Eksik Verileri Temizleme

```bash
python "csv düzeltici.py"
```

- `isyatirim/` klasöründeki tüm `.csv` dosyalarını okur.
- Tarih sütunu hariç sayısal sütunlardaki eksik değerleri o sütunun **medyanı** ile doldurur.
- Temizlenmiş veriyi aynı dosya adıyla tekrar kaydeder.

---

## 📡 TV VERİ — TradingView Veri Yükleme Eki (`panel_tvdata_ekleri.py`)

Bu modül, **TradingView** üzerinden BIST (IMKB) ve Kripto borsalarından veri indirmenizi sağlar. `panel.py`'ye entegre çalışabildiği gibi **tek başına** da çalıştırılabilir.

### 🎯 Ne Yapar?

- `tvdatafeed-enhanced` kütüphanesini kullanarak TradingView'dan OHLCV barı çeker.
- İndirilen veriyi, panelin mevcut CSV biçimini **otomatik taklit ederek** (ayırıcı, sütun adları, tarih formatı, ondalık virgül vb.) panele uyumlu şekilde kaydeder.
- Panelin "dizinden oku" mantığına **dokunmaz** — TV verisi de sanki kullanıcı CSV'siymiş gibi aynı kapıdan girer.
- **60dk** (intraday: 1dk–4sa) ve **günlük** (1gün/1hafta/1ay) verileri doğru klasörlere yönlendirir; günlük/haftalık/aylık verilerde CSV'ye **yalnız tarih** yazılır (saat eklenmez).

### 💱 Desteklenen Kaynaklar

| Kaynak | Borsa | Sembol Örneği |
|---|---|---|
| **BIST (IMKB)** | `BIST` | `THYAO`, `ASELS`, `GARAN` |
| **Kripto** | `BINANCE`, `BYBIT`, `COINBASE`, `OKX`, `KUCOIN`, `MEXC`, `BITFINEX`, `GATEIO` | `BTCUSDT`, `ETHUSDT` |

### ⏱️ Desteklenen Zaman Aralıkları

`1dk`, `3dk`, `5dk`, `15dk`, `30dk`, `45dk`, `1sa`, `2sa`, `3sa`, `4sa`, `1gün`, `1hafta`, `1ay`

- **Bar sayısı:** 100 – 5000 arası (tek çekimde en fazla 5000 bar).

### 📦 Toplu İndirme (BIST 30 / 50 / 100 / TÜMÜ)

- Gömülü BIST 30/50/100 listeleriyle tek tıkla toplu indirme.
- **Daha güncel liste için:** `panel_tvdata_ekleri.py` (veya `panel.py`) yanına `bist30.txt`, `bist50.txt`, `bist100.txt` ya da `bist_tumu.txt` koyun. Her satıra bir sembol; `#` ile yorum ekleyebilirsiniz. Dosya varsa gömülü listenin yerine o kullanılır.
- Toplu indirmede TradingView hız limitine saygı için semboller arası **1 saniye** beklenir; **DURDUR** düğmesiyle yarıda kesilebilir.

### 🔌 Kullanım

#### A) Panel'e Entegre Etme

`panel.py` içinde `_arayuz_kur()` çağrısından **sonra** şu iki satırı ekleyin:

```python
from panel_tvdata_ekleri import tv_butonu_ekle
tv_butonu_ekle(self)
```

Panelin üst çubuğunda **LOAD DATA** düğmesinin yanında yeşil bir **TV VERİ** düğmesi belirir.

#### B) Tek Başına Çalıştırma

```bash
python panel_tvdata_ekleri.py
```

Bu durumda minimal bir panel açılır; **TV VERİ** diyaloğu üzerinden indirme yapılır ve CSV'ler betiğin yanındaki `csv_60dk/` ve `csv_gunluk/` klasörlerine yazılır.

### 🗂️ Hedef Klasör Mantığı

- **Otomatik hedef:** Panelin (veya `fibo_kanal` modülünün) tanımladığı 60dk/günlük veri klasörleri.
- **Elle hedef (SEÇ):** Tür bazında (60dk / günlük) kalıcıdır; `tv_veri_ayarlar.json` dosyasına yazılır ve panel kapansa bile hatırlanır. **SIFIRLA** otomatik klasöre döndürür.
- **Panel kopyası:** Panelin gerçek veri klasörü SEÇ'ten farklıysa, indirilen CSV oraya da kopyalanır — böylece panel ve fibo kanal yeni veriyi görür. Betiğin bulunduğu dizine **asla** yazılmaz.

### ⚙️ Kalıcı Ayarlar (`tv_veri_ayarlar.json`)

Modül, `panel_tvdata_ekleri.py` yanında şu ayarları saklar:

- Veri kaynağı (BIST / Kripto)
- Borsa (Kripto için)
- Zaman aralığı
- Bar sayısı
- Tür bazında özel hedef klasörler

Panel yeniden açıldığında bu ayarlar otomatik yüklenir.

### 🧪 Örnek Akış

1. **TV VERİ** düğmesine basın.
2. **VERİ KAYNAĞI:** BIST veya Kripto seçin.
3. **SEMBOL:** Örn. `THYAO` (BIST) veya `BTCUSDT` (BINANCE). Emin değilseniz **ARA** düğmesiyle TradingView'da arayın.
4. **ARALIK:** Örn. `1sa` (intraday) veya `1gün` (günlük).
5. **BAR SAYISI:** Örn. `2000`.
6. **HEDEF KLASÖR:** Otomatik gelir; isterseniz **SEÇ** ile değiştirin.
7. **İNDİR VE PANELE YÜKLE** düğmesine basın.

Toplu indirme için **TOPLU İNDİRME** açılır menüsünden `BIST 30/50/100/TÜMÜ` seçip **TOPLU İNDİR** düğmesine basın.

### ⚠️ Notlar

- **Anonim bağlantıda** TradingView verisi sınırlı olabilir. Ücretsiz bir hesap bilgisi girerek daha fazla bar indirebilirsiniz.
- **Maksimum bar:** Tek çekimde 5000 bar.
- **CSV biçimi:** Hedef klasörde daha önce indirilmiş bir CSV varsa biçimi (ayırıcı, tarih formatı, ondalık virgül, BOM) ondan taklit edilir; yoksa ISO tarih formatı (`yyyy-mm-dd`) kullanılır.
- **Hız limiti:** Toplu indirmede semboller arası 1 sn beklenir; hata alırsanız **DURDUR**'a basıp TV hesabı girerek yeniden deneyin.

---

## 📌 Notlar

- `Hisse_verilerini_indir.py` betiğindeki `symbols` listesinde `"DOCO.IS"` ve `"OYAKC.IS"` gibi bazı hisse kodları **mükerrer** olarak yer almaktadır; dilerseniz listeden tekrarları kaldırabilirsiniz.
- `verileri indir isyatirim.py` betiği, `sirketler/sirketler.xlsx` dosyasını bekler. Bu dosya depoda `Sirketler.xlsx` olarak yer almaktadır; betiği çalıştırmadan önce dosyayı `sirketler` klasörü altına taşımanız veya betikteki yolu güncellemeniz gerekir.
- `isyatirimhisse` kütüphanesi, İş Yatırım'ın sunduğu verileri kullanır ve zaman zaman API değişikliklerinden etkilenebilir. Güncel kullanım için kütüphanenin dokümantasyonunu kontrol edin.
- `yfinance` ile indirilen veriler Yahoo Finance'in sunduğu verilere dayanır; bazı hisseler için veri aralıkları farklılık gösterebilir.
- **`tvdatafeed-enhanced`**, TradingView'ın resmi olmayan bir API'sini kullanır. TradingView bu API'yi zaman zaman değiştirebilir; kütüphane güncellemelerini takip edin.
- **BIST 30/50/100 endeks kuralları** 3 ayda bir değişir; gömülü listeler Ekim–Aralık 2026 dönemine göredir. Güncel tutmak için ilgili `.txt` dosyalarını modül yanına bırakın.

---

## 🤝 Katkıda Bulunma

Her türlü katkıya açıktır. Hata bildirimi, yeni özellik talebi veya kod iyileştirmesi için lütfen bir **Issue** açın veya **Pull Request** gönderin.

---

## 📄 Lisans

Bu proje için bir lisans dosyası bulunmamaktadır. Varsayılan olarak tüm hakları saklıdır. Kullanım koşulları için depo sahibiyle iletişime geçebilirsiniz.
