# Crypto Trading Bot - Bybit + Telegram

Bot trading crypto yang menggunakan Bybit API untuk data market dan Telegram untuk notifikasi alert berdasarkan strategi H4 (4 jam).

## Fitur

- ✅ Analisis teknikal otomatis (EMA, RSI, MACD, ATR)
- ✅ Deteksi Support & Resistance (Pivot Points)
- ✅ Risk management otomatis (leverage, position size)
- ✅ Notifikasi Telegram real-time
- ✅ Multi-symbol monitoring

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Telegram Bot

1. Buka Telegram dan cari [@BotFather](https://t.me/botfather)
2. Kirim `/newbot` dan ikuti instruksi
3. Beri nama bot (contoh: "My Crypto Alert Bot")
4. Beri username bot (harus diakhiri 'bot', contoh: "mycryptoalert_bot")
5. Copy token yang diberikan (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. Paste token ke file `.env` di `TELEGRAM_BOT_TOKEN`

### 3. Dapatkan Chat ID

**Cara 1 - Otomatis (Recommended):**
```bash
# Edit .env, isi TELEGRAM_BOT_TOKEN dulu
# Kirim pesan "Hello" ke bot Anda di Telegram
python test_telegram.py
# Script akan menampilkan Chat ID Anda
```

**Cara 2 - Manual:**
1. Kirim pesan ke bot Anda di Telegram
2. Buka browser: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Cari `"chat":{"id":123456789` dan copy angkanya
4. Paste ke `.env` di `TELEGRAM_CHAT_ID`

### 4. Test Koneksi

**Test Bybit (sudah dikonfigurasi untuk testnet):**
```bash
python test_bybit.py
```

**Test Telegram:**
```bash
python test_telegram.py
```

### 5. Jalankan Bot

```bash
python crypto_bot.py
```

Bot akan scan market setiap 5 menit dan kirim alert ke Telegram saat ada setup trading.

## Konfigurasi Trading

Edit di `crypto_bot.py`:

```python
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']  # Symbol yang dimonitor
TIMEFRAME = '240'  # 4H
BALANCE = 1000  # Modal USD
MAX_RISK = 2.0  # Risk per trade %
MAX_LEVERAGE = 20  # Max leverage
```

## Cara Kerja

Bot akan:
1. Mengambil data candlestick 4H dari Bybit
2. Menghitung indikator (EMA 21/55, RSI, MACD, ATR)
3. Mendeteksi support/resistance
4. Mengidentifikasi bias market (bullish/bearish)
5. Menghitung entry zone, TP, SL, dan risk management
6. Mengirim alert ke Telegram saat kondisi terpenuhi

## Format Alert

```
📈 LONG SETUP - BTCUSDT

💰 Price: $45000.00
🎯 Entry Zone: $44800.00 - $45100.00
🛑 Stop Loss: $44200.00
✅ Take Profit: $46500.00

⚡ Leverage: 5x (NORMAL)
💵 Risk Amount: $20.00
📊 Position Size: 0.125
📉 SL %: 1.78%
🎲 R:R: 1:1.67
```

## Troubleshooting

**Bot tidak mengirim alert:**
- Pastikan TELEGRAM_BOT_TOKEN dan CHAT_ID benar
- Cek koneksi internet
- Pastikan sudah kirim pesan ke bot minimal 1x

**Error Bybit API:**
- Untuk data public, API key tidak wajib
- Cek koneksi internet
- Pastikan symbol valid (gunakan format: BTCUSDT, ETHUSDT, dll)

## Disclaimer

Bot ini hanya untuk edukasi. Trading crypto berisiko tinggi. Gunakan dengan bijak dan hanya dengan modal yang siap hilang.
