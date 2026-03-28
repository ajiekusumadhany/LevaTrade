# ⚠️ AUTO TRADING CONFIGURATION

## PENTING! Baca ini sebelum enable auto trading

### Current Settings (crypto_bot_auto_trade.py):

```python
# Line 20-25
AUTO_TRADE_ENABLED = False  # ⚠️ SET TRUE UNTUK ENABLE
DRY_RUN = True              # True = simulasi, False = real
MAX_OPEN_POSITIONS = 3      # Max 3 posisi bersamaan
MIN_POSITION_SIZE_USD = 10  # Minimum $10 per posisi
```

### Testnet vs Mainnet:

**Testnet (Line 48):**
```python
session = HTTP(
    testnet=False,  # ⚠️ Saat ini MAINNET
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)
```

**Untuk Testnet, ubah ke:**
```python
session = HTTP(
    testnet=True,  # TESTNET
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)
```

---

## 🔧 Cara Enable Auto Trading:

### Option 1: DRY RUN (Simulasi - AMAN)
1. Edit `crypto_bot_auto_trade.py` line 20:
   ```python
   AUTO_TRADE_ENABLED = True
   DRY_RUN = True  # Simulasi saja
   ```
2. Jalankan: `python crypto_bot_auto_trade.py`
3. Bot akan print "DRY RUN" tapi tidak execute real order

### Option 2: TESTNET (Testing dengan fake money)
1. Pastikan punya Bybit Testnet account
2. Edit `crypto_bot_auto_trade.py`:
   - Line 20: `AUTO_TRADE_ENABLED = True`
   - Line 21: `DRY_RUN = False`
   - Line 48: `testnet=True`
3. Pastikan API key di `.env` adalah testnet API
4. Jalankan: `python crypto_bot_auto_trade.py`

### Option 3: MAINNET (REAL TRADING - HATI-HATI!)
1. ⚠️ **SANGAT BERBAHAYA!** Gunakan uang real
2. Edit `crypto_bot_auto_trade.py`:
   - Line 20: `AUTO_TRADE_ENABLED = True`
   - Line 21: `DRY_RUN = False`
   - Line 48: `testnet=False`
3. Pastikan API key di `.env` adalah mainnet API
4. Start dengan balance kecil!
5. Jalankan: `python crypto_bot_auto_trade.py`

---

## 📊 Dashboard vs Auto Trading:

**Dashboard (`dashboard_app.py`):**
- ✅ Hanya monitoring & display
- ✅ Tidak execute order
- ✅ Aman untuk dijalankan
- ✅ Real-time web interface

**Auto Trading (`crypto_bot_auto_trade.py`):**
- ⚠️ Execute order otomatis
- ⚠️ Bisa loss uang
- ⚠️ Perlu monitoring ketat
- ⚠️ Start dengan testnet/dry run

**Bisa jalankan keduanya bersamaan:**
- Terminal 1: `python dashboard_app.py` (monitoring)
- Terminal 2: `python crypto_bot_auto_trade.py` (trading)

---

## 🚨 SAFETY CHECKLIST:

Sebelum enable auto trading, pastikan:

- [ ] Sudah test dengan DRY_RUN = True
- [ ] Sudah test di Testnet
- [ ] Paham risk management (MAX_RISK, MAX_LEVERAGE)
- [ ] Set MAX_OPEN_POSITIONS yang reasonable
- [ ] Monitor 24/7 atau gunakan stop loss
- [ ] Punya Telegram alert aktif
- [ ] Balance cukup untuk margin
- [ ] API key punya permission trading

---

## 💡 Rekomendasi:

**Untuk Pemula:**
1. Jalankan dashboard dulu: `python dashboard_app.py`
2. Monitor beberapa hari
3. Lihat signal yang muncul
4. Manual trading dulu
5. Baru enable auto trading dengan DRY_RUN
6. Test di testnet
7. Baru mainnet dengan balance kecil

**Untuk Testing:**
```bash
# Terminal 1: Dashboard
python dashboard_app.py

# Terminal 2: Auto Trading (DRY RUN)
# Edit crypto_bot_auto_trade.py: AUTO_TRADE_ENABLED = True, DRY_RUN = True
python crypto_bot_auto_trade.py
```

---

## ❓ FAQ:

**Q: Kenapa dashboard tidak auto trading?**
A: Dashboard hanya untuk monitoring. Auto trading ada di file terpisah.

**Q: Aman tidak auto trading?**
A: Tidak 100% aman. Selalu ada risk. Start dengan testnet/dry run.

**Q: Bisa rugi?**
A: Ya, bisa rugi. Crypto trading berisiko tinggi.

**Q: Perlu monitor terus?**
A: Ya, sangat disarankan. Bot bisa error atau market crash.

---

**Status Saat Ini:**
- Dashboard: ✅ Running (monitoring only)
- Auto Trading: ❌ Disabled (aman)

**Untuk enable auto trading, edit `crypto_bot_auto_trade.py` sesuai instruksi di atas.**
