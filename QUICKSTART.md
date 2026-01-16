# 🚀 Quick Start Guide

## Langkah Cepat (5 Menit)

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Setup Telegram Bot

1. Buka Telegram → Cari **@BotFather**
2. Kirim: `/newbot`
3. Nama bot: `My Crypto Bot` (bebas)
4. Username: `mycrypto_alert_bot` (harus diakhiri _bot)
5. **Copy token** yang diberikan

### 3️⃣ Edit File .env

File `.env` sudah ada dengan Bybit testnet API. Tinggal isi Telegram:

```env
# Bybit sudah diisi (testnet)
BYBIT_API_KEY=lSmK9Zc8q0rw1ctrRo
BYBIT_API_SECRET=qkhv4Tgg6B1SNMlDIhWEBBmxbBhk3IRPMj1C

# Isi yang ini:
TELEGRAM_BOT_TOKEN=paste_token_dari_botfather_disini
TELEGRAM_CHAT_ID=akan_diisi_nanti
```

### 4️⃣ Dapatkan Chat ID

1. **Kirim pesan** "Hello" ke bot Anda di Telegram
2. Jalankan:
```bash
python test_telegram.py
```
3. Script akan tampilkan Chat ID Anda
4. **Copy Chat ID** dan paste ke `.env`

### 5️⃣ Test Koneksi

```bash
# Test Bybit
python test_bybit.py

# Test Telegram (akan kirim pesan test)
python test_telegram.py
```

### 6️⃣ Jalankan Bot! 🎉

```bash
python crypto_bot.py
```

Bot akan:
- ✅ Monitor BTC, ETH, SOL setiap 5 menit
- ✅ Kirim alert ke Telegram saat ada setup trading
- ✅ Tampilkan entry zone, TP, SL, leverage, risk management

---

## Contoh Output

```
🚀 Bot started...
📊 Monitoring symbols: BTCUSDT, ETHUSDT, SOLUSDT
⏰ Timeframe: 240m (4H)
--------------------------------------------------
✓ Scan completed at 14:30:15
✓ Scan completed at 14:35:15
✅ Alert sent for BTCUSDT
✓ Scan completed at 14:40:15
```

## Contoh Alert Telegram

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

⏰ 2026-01-16 14:35:22
```

---

## Troubleshooting

**"Unauthorized" error:**
- Token Telegram salah, cek lagi di @BotFather

**"Chat not found":**
- Belum kirim pesan ke bot, kirim "Hello" dulu

**Tidak ada alert:**
- Normal, bot hanya kirim saat ada setup valid
- Coba ubah `SYMBOLS` atau tunggu beberapa jam

**Bybit error:**
- Testnet kadang maintenance, coba lagi nanti
- Atau ganti `testnet=False` di `crypto_bot.py` untuk mainnet (data only)

---

## Kustomisasi

Edit `crypto_bot.py`:

```python
# Ganti symbol yang dimonitor
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT']

# Ganti modal
BALANCE = 5000  # USD

# Ganti risk per trade
MAX_RISK = 1.0  # 1% per trade (lebih aman)

# Ganti max leverage
MAX_LEVERAGE = 10  # Lebih konservatif
```

---

## Next Steps

- 📊 Monitor beberapa hari untuk lihat performa
- 🔧 Adjust parameter sesuai risk appetite
- 📈 Tambah symbol lain yang ingin dimonitor
- 🤖 Develop fitur auto-trading (advanced)

**Happy Trading! 🚀**
