# 🚀 LevaTrade - Advanced Crypto Trading Bot

## 📋 Overview
LevaTrade adalah sistem trading otomatis cryptocurrency yang menggunakan strategi berbasis sesi market dengan AI integration dan risk management yang komprehensif.

### ✨ Key Features
- **4-Session Strategy**: DEAD_ZONE, ASIA, LONDON, NEWYORK dengan risk berbeda
- **Conditional Risk Escalation**: Risk naik hanya jika semua kondisi terpenuhi  
- **Parallel Processing**: Scan 100 symbols dengan 20 threads
- **AI Integration**: Gemini AI untuk market analysis dan reasoning
- **Comprehensive Risk Management**: Multiple layers of protection
- **Real-time Dashboard**: Web-based monitoring dan control
- **Telegram Integration**: Notifikasi dan kontrol via bot
- **Dry Run Mode**: Testing tanpa risiko modal

## 🎯 Performance Targets
- **Daily Target**: 2-5% profit
- **Max Daily Loss**: 2% dari balance
- **Max Drawdown**: 20% (emergency stop)
- **Win Rate Target**: 60-70%
- **Risk per Trade**: 0.3-1.0% (tergantung sesi)

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements_dashboard.txt

# Setup configuration
copy .env.example .env
# Edit .env dengan API keys Anda
```

### 2. Configuration
Edit file `.env`:
```bash
# Bybit API
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_api_secret

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading Settings
BALANCE_USD=1000
MAX_RISK_PERCENT=1.0
MAX_LEVERAGE=20
MAX_OPEN_POSITIONS=5

# Gemini AI
GEMINI_API_KEYS=key1,key2,key3
```

### 3. Run System
```bash
# Dry Run Mode (Recommended untuk testing)
python crypto_bot_parallel.py

# Dashboard (Terminal baru)
python dashboard_app.py
# Akses: http://localhost:5000
```

## 📊 Session-Based Strategy

### 🌅 DEAD ZONE (02:00-07:00 WIB)
- **Risk**: 0.3% per trade | **Strategy**: Conservative scalping | **Target**: 0.5-1%

### 🌏 ASIA SESSION (07:00-14:00 WIB)  
- **Risk**: 0.3-0.4% per trade | **Strategy**: Mean reversion | **Target**: 1-2%

### 🇬🇧 LONDON SESSION (14:00-20:00 WIB)
- **Risk**: 0.5-0.8% per trade | **Strategy**: Structural breakout | **Target**: 2-4%

### 🇺🇸 NEW YORK SESSION (20:00-02:00 WIB)
- **Risk**: 0.4-1.0% per trade | **Strategy**: Momentum trading | **Target**: 3-6%
- **Special**: NY Sniper Mode (max 2 trades/day @ 1% risk)

## 🛡️ Risk Management

### 🚨 Emergency Stops
- **Hard Stop**: Drawdown > 20% | **Daily Loss**: > 2% | **Consecutive Loss**: 3x
- **Correlation Risk**: Max 3 posisi berkorelasi

### 🎯 Conditional Risk Escalation
Risk naik hanya jika SEMUA kondisi terpenuhi:
1. ✅ Win rate ≥ 60% | 2. ✅ Profit > 0% | 3. ✅ Drawdown < 10%
4. ✅ Loss berturut < 3 | 5. ✅ Volatility normal

## 📱 Telegram Commands
`/status` `/balance` `/positions` `/profit` `/stop` `/start` `/emergency`

## 🖥️ Dashboard Features
Real-time status • P&L tracking • Position monitoring • Session analysis • AI chat • Trading control

## 📁 Core Files
```
crypto_bot_parallel.py          # Main bot
session_management_system.py    # Session detection  
conditional_risk_system.py      # Risk management
enhanced_trading_strategy.py    # Trading strategy
gemini_ai_system.py            # AI integration
dashboard_app.py               # Web dashboard
dry_run_system.py              # Simulation
real_trade_system.py           # Real trading
```

## 🔧 Emergency Stop
```bash
# File-based
echo '{"trading_enabled": false, "emergency_stop": true}' > trading_control.json

# Process kill
taskkill /f /im python.exe

# Telegram
/emergency
```

## 📄 Documentation
- **[📖 Dokumentasi Lengkap](SISTEM_TRADING_DOKUMENTASI_LENGKAP.md)** - Panduan lengkap sistem
- **[🔧 Technical Documentation](TECHNICAL_DOCUMENTATION.md)** - Dokumentasi teknis developer
- **[⚡ Quick Start Guide](QUICKSTART.md)** - Panduan cepat memulai
- **[📊 Status & Setup](STATUS.md)** - Status sistem dan konfigurasi

## ⚠️ Disclaimer
Trading cryptocurrency melibatkan risiko tinggi. Gunakan dengan bijak dan hanya dengan modal yang siap hilang. Selalu test di dry run mode terlebih dahulu.

---

**Happy Trading! 🚀**