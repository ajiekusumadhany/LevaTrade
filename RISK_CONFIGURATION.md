# 🎯 RISK CONFIGURATION GUIDE

## 📝 Pengaturan Risk di File .env

Sekarang Anda bisa mengatur semua parameter trading di file `.env` tanpa perlu edit kode!

### 🔧 Parameter yang Bisa Diatur:

```env
# Trading Configuration
MAX_RISK_PERCENT=1.0        # Risk per trade (%)
BALANCE_USD=1000            # Balance simulasi (USD)
MAX_LEVERAGE=10             # Maksimal leverage
MAX_OPEN_POSITIONS=20       # Maksimal posisi bersamaan
```

## 🎯 Contoh Pengaturan Risk:

### 🔰 Conservative (Aman)
```env
MAX_RISK_PERCENT=0.5        # 0.5% per trade
BALANCE_USD=1000            # $1000 balance
MAX_LEVERAGE=5              # Max 5x leverage
MAX_OPEN_POSITIONS=10       # Max 10 posisi
```
**Hasil:** Risk $5 per trade, margin $5-25 per posisi

### 💼 Moderate (Seimbang)
```env
MAX_RISK_PERCENT=1.0        # 1% per trade
BALANCE_USD=1000            # $1000 balance
MAX_LEVERAGE=10             # Max 10x leverage
MAX_OPEN_POSITIONS=20       # Max 20 posisi
```
**Hasil:** Risk $10 per trade, margin $10-100 per posisi

### ⚡ Aggressive (Berisiko)
```env
MAX_RISK_PERCENT=2.0        # 2% per trade
BALANCE_USD=1000            # $1000 balance
MAX_LEVERAGE=20             # Max 20x leverage
MAX_OPEN_POSITIONS=30       # Max 30 posisi
```
**Hasil:** Risk $20 per trade, margin $20-400 per posisi

## 📊 Cara Kerja Formula:

### 1. Margin per Trade
```
Margin = BALANCE_USD × MAX_RISK_PERCENT / 100
```

### 2. Position Size
```
Position Value = Margin × Leverage
Position Size = Position Value / Entry Price
```

### 3. Contoh Perhitungan
**Setting:** `MAX_RISK_PERCENT=1.0`, `BALANCE_USD=1000`, Leverage=5x
- Margin per trade = $1000 × 1% = **$10**
- Position value = $10 × 5x = **$50**
- Jika BTCUSDT = $50,000, maka position size = $50 / $50,000 = **0.001 BTC**

## ⚠️ PENTING:

### ✅ Yang Benar:
- Risk percentage berdasarkan **margin yang digunakan**
- Position size **tidak akan pernah** melebihi balance
- Leverage hanya **mengurangi margin**, bukan memperbesar risk

### ❌ Yang Salah (formula lama):
- Risk berdasarkan SL distance → position size tidak terbatas
- Bisa menghasilkan position 10x lebih besar dari balance
- Risk management tidak konsisten

## 🚀 Cara Menggunakan:

1. **Edit file `.env`** sesuai risk tolerance Anda
2. **Restart bot** untuk apply setting baru
3. **Monitor hasil** di dashboard dan console
4. **Adjust** jika perlu berdasarkan performance

## 📈 Rekomendasi Berdasarkan Experience:

### 👶 Pemula
- MAX_RISK_PERCENT: **0.5-1.0%**
- MAX_LEVERAGE: **3-5x**
- MAX_OPEN_POSITIONS: **5-10**

### 💼 Intermediate  
- MAX_RISK_PERCENT: **1.0-1.5%**
- MAX_LEVERAGE: **5-10x**
- MAX_OPEN_POSITIONS: **10-20**

### 🏆 Advanced
- MAX_RISK_PERCENT: **1.5-2.0%**
- MAX_LEVERAGE: **10-20x**
- MAX_OPEN_POSITIONS: **20-30**

## 🔄 Live Update:

Setiap kali Anda mengubah `.env`, restart bot untuk apply setting baru. Bot akan menampilkan konfigurasi saat startup:

```
🎯 Risk Configuration:
   - Risk per trade: 1.0% ($10)
   - Max leverage: 10x
   - Max positions: 20
   - Balance: $1000
```

**Happy Trading! 🚀**