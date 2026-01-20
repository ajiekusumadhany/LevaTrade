# 🚀 DOKUMENTASI LENGKAP SISTEM TRADING LEVATRADE

## 📋 DAFTAR ISI
1. [Overview Sistem](#overview-sistem)
2. [Arsitektur Sistem](#arsitektur-sistem)
3. [File-File Utama](#file-file-utama)
4. [Konfigurasi](#konfigurasi)
5. [Strategi Trading](#strategi-trading)
6. [Risk Management](#risk-management)
7. [Monitoring & Dashboard](#monitoring--dashboard)
8. [Setup & Installation](#setup--installation)
9. [Cara Penggunaan](#cara-penggunaan)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 OVERVIEW SISTEM

**LevaTrade** adalah sistem trading otomatis cryptocurrency yang menggunakan strategi berbasis sesi market dengan AI integration dan risk management yang komprehensif.

### ✨ Fitur Utama:
- **4-Session Strategy**: DEAD_ZONE, ASIA, LONDON, NEWYORK dengan risk berbeda
- **Conditional Risk Escalation**: Risk naik hanya jika semua kondisi terpenuhi
- **Parallel Processing**: Scan 100 symbols dengan 20 threads
- **AI Integration**: Gemini AI untuk market analysis dan reasoning
- **Comprehensive Risk Management**: Multiple layers of protection
- **Real-time Dashboard**: Web-based monitoring dan control
- **Telegram Integration**: Notifikasi dan kontrol via bot
- **Dry Run Mode**: Testing tanpa risiko modal

### 📊 Performa Target:
- **Daily Target**: 2-5% profit
- **Max Daily Loss**: 2% dari balance
- **Max Drawdown**: 20% (emergency stop)
- **Win Rate Target**: 60-70%
- **Risk per Trade**: 0.3-1.0% (tergantung sesi)

---

## 🏗️ ARSITEKTUR SISTEM

```
crypto_bot_parallel.py (ENTRY POINT)
    ↓
session_management_system.py (Deteksi sesi market)
    ↓
conditional_risk_system.py (Hitung risk berdasarkan kondisi)
    ↓
integrated_risk_management_system.py (Risk management terintegrasi)
    ↓
enhanced_trading_strategy.py (Strategy dengan semua critical fixes)
    ↓
dry_run_system.py / real_trade_system.py (Execute & track)
    ↓
gemini_ai_system.py (AI analysis & reasoning)
    ↓
error_notification_system.py (Notifikasi error)
    ↓
Telegram Bot (Alert ke user)
```

### 🔄 Flow Eksekusi:
1. **Startup**: Load konfigurasi dan initialize semua sistem
2. **Session Detection**: Deteksi sesi market saat ini
3. **Symbol Scanning**: Parallel scan 100 symbols setiap 5 menit
4. **Signal Analysis**: Analisis technical indicators untuk setiap symbol
5. **Risk Calculation**: Hitung risk berdasarkan conditional system
6. **AI Reasoning**: Gemini AI analisis market conditions
7. **Trade Execution**: Execute trade jika semua kondisi terpenuhi
8. **Monitoring**: Track posisi dan apply exit strategies
9. **Notification**: Kirim alert via Telegram

---

## 📁 FILE-FILE UTAMA

### 🚀 Entry Point & Core System
- **`crypto_bot_parallel.py`** - Bot trading utama dengan parallel processing
- **`session_management_system.py`** - Deteksi sesi trading otomatis
- **`conditional_risk_system.py`** - Advanced risk management dengan conditional escalation
- **`integrated_risk_management_system.py`** - Core risk management terintegrasi
- **`enhanced_trading_strategy.py`** - Strategy wrapper dengan semua critical fixes
- **`trading_system_wrapper.py`** - Wrapper untuk integrasi enhanced strategy

### 📈 Strategi Per Sesi
- **`london_session_strategy.py`** - Strategi breakout struktural untuk London
- **`newyork_session_strategy.py`** - Strategi momentum untuk New York
- **`asia_session_optimization.py`** - Strategi mean reversion untuk Asia

### 🛡️ Risk Management & Protection
- **`progressive_risk_system.py`** - Risk management bertahap berdasarkan urutan trade
- **`hard_stop_system.py`** - Emergency stop untuk drawdown >20%
- **`time_based_stop_system.py`** - Sistem stop berdasarkan waktu holding
- **`early_exit_system.py`** - Sistem early exit untuk profit protection

### 📊 Tracking & Monitoring
- **`dry_run_system.py`** - Simulasi trading dengan tracking lengkap
- **`real_trade_system.py`** - Sistem untuk trading nyata
- **`trading_session_system.py`** - Analisis performa per sesi market

### 🤖 AI & Notifikasi
- **`gemini_ai_system.py`** - Integrasi Gemini AI untuk market analysis
- **`error_notification_system.py`** - Sistem notifikasi error
- **`partial_tp_notification_system.py`** - Notifikasi partial take profit

### 🖥️ Dashboard & Control
- **`dashboard_app.py`** - Flask dashboard untuk monitoring
- **`dashboard_ai_chat.py`** - AI chat integration di dashboard
- **`trading_control_system.py`** - Sistem start/stop trading

---

## ⚙️ KONFIGURASI

### 🔐 Environment Variables (.env)
```bash
# Bybit API Configuration
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_api_secret

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading Configuration
BALANCE_USD=1000                    # Trading balance
MAX_RISK_PERCENT=1.0               # Max risk per trade (%)
MAX_LEVERAGE=20                    # Max leverage
MAX_OPEN_POSITIONS=5               # Max open positions

# Gemini AI Configuration
GEMINI_API_KEYS=key1,key2,key3     # Multiple keys for rotation
GEMINI_MODEL=gemini-2.0-flash-exp  # AI model

# Session Configuration (WIB Time)
DEAD_ZONE_START_HOUR=2             # Dead zone start
DEAD_ZONE_END_HOUR=7               # Dead zone end
DEAD_ZONE_RISK_PERCENT=0.3         # Dead zone risk (%)
DEAD_ZONE_MAX_LEVERAGE=10          # Dead zone max leverage

ASIA_START_HOUR=7                  # Asia start
ASIA_END_HOUR=14                   # Asia end
ASIA_RISK_PERCENT=0.3              # Asia risk (%)
ASIA_MAX_LEVERAGE=8                # Asia max leverage

LONDON_START_HOUR=14               # London start
LONDON_END_HOUR=20                 # London end
LONDON_RISK_PERCENT=0.5            # London risk (%)
LONDON_MAX_LEVERAGE=15             # London max leverage

NEWYORK_START_HOUR=20              # New York start
NEWYORK_END_HOUR=2                 # New York end (next day)
NEWYORK_RISK_PERCENT=0.4           # New York risk (%)
NEWYORK_MAX_LEVERAGE=20            # New York max leverage
```

### 📋 Strategy Configuration (strategy_config.json)
```json
{
    "risk_management": {
        "max_risk_percent": 1.0,
        "max_daily_loss_percent": 2.0,
        "max_drawdown_percent": 20.0,
        "correlation_limit": 3,
        "max_positions": 5
    },
    "session_config": {
        "dead_zone": {
            "risk_percent": 0.3,
            "max_leverage": 10,
            "max_positions": 2
        },
        "asia": {
            "risk_percent": 0.3,
            "max_leverage": 8,
            "max_positions": 3
        },
        "london": {
            "risk_percent": 0.5,
            "max_leverage": 15,
            "max_positions": 4
        },
        "newyork": {
            "risk_percent": 0.4,
            "max_leverage": 20,
            "max_positions": 5,
            "sniper_mode": {
                "enabled": true,
                "max_trades_per_day": 2,
                "risk_percent": 1.0
            }
        }
    },
    "technical_indicators": {
        "rsi_period": 14,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "ema_fast": 12,
        "ema_slow": 26,
        "bb_period": 20,
        "bb_std": 2
    }
}
```

### 🎛️ Trading Control (trading_control.json)
```json
{
    "trading_enabled": true,
    "dry_run_mode": true,
    "emergency_stop": false,
    "session_override": null,
    "risk_override": null,
    "max_positions_override": null
}
```

---

## 📈 STRATEGI TRADING

### 🌅 DEAD ZONE (02:00-07:00 WIB)
**Karakteristik**: Volume rendah, volatilitas minimal
- **Risk**: 0.3% per trade
- **Max Leverage**: 10x
- **Max Positions**: 2
- **Strategy**: Conservative scalping dengan tight stop loss
- **Target**: 0.5-1% profit per trade

### 🌏 ASIA SESSION (07:00-14:00 WIB)
**Karakteristik**: Mean reversion, range-bound market
- **Risk**: 0.3-0.4% per trade
- **Max Leverage**: 8x
- **Max Positions**: 3
- **Strategy**: Mean reversion dengan support/resistance
- **Target**: 1-2% profit per trade

### 🇬🇧 LONDON SESSION (14:00-20:00 WIB)
**Karakteristik**: Breakout struktural, high volatility
- **Risk**: 0.5-0.8% per trade
- **Max Leverage**: 15x
- **Max Positions**: 4
- **Strategy**: Structural breakout dengan momentum confirmation
- **Target**: 2-4% profit per trade

### 🇺🇸 NEW YORK SESSION (20:00-02:00 WIB)
**Karakteristik**: Momentum trading, highest volume
- **Risk**: 0.4-1.0% per trade
- **Max Leverage**: 20x
- **Max Positions**: 5
- **Strategy**: Momentum trading dengan trend following
- **Target**: 3-6% profit per trade
- **Special**: NY Sniper Mode (max 2 trades/day @ 1% risk)

### 🎯 Conditional Risk Escalation
Risk naik hanya jika SEMUA kondisi terpenuhi:
1. ✅ Win rate hari ini ≥ 60%
2. ✅ Profit hari ini > 0%
3. ✅ Drawdown saat ini < 10%
4. ✅ Tidak ada posisi loss berturut-turut ≥ 3
5. ✅ Market volatility dalam range normal

---

## 🛡️ RISK MANAGEMENT

### 🚨 Emergency Stops
1. **Hard Stop**: Trading berhenti jika drawdown > 20%
2. **Daily Loss Limit**: Stop trading jika loss harian > 2%
3. **Consecutive Loss**: Reduce risk setelah 3 loss berturut-turut
4. **Correlation Risk**: Max 3 posisi dengan korelasi tinggi

### ⏰ Time-Based Protection
- **Max Holding Time**: 4 jam per posisi
- **Session Transition**: Close semua posisi saat ganti sesi
- **Weekend Protection**: Reduce posisi sebelum weekend

### 🧠 Psychological Protection
- **Emotional State Tracking**: Monitor psychological state trader
- **Revenge Trading Prevention**: Block trading setelah big loss
- **Overconfidence Protection**: Limit risk setelah big win

### 📊 Position Sizing
```python
# Dynamic position sizing berdasarkan kondisi
def calculate_position_size(balance, risk_percent, session, conditions):
    base_risk = session_risk[session]
    
    # Conditional escalation
    if all_conditions_met(conditions):
        risk_multiplier = 1.5
    else:
        risk_multiplier = 1.0
    
    final_risk = min(base_risk * risk_multiplier, MAX_RISK_PERCENT)
    position_size = (balance * final_risk / 100) / stop_loss_distance
    
    return position_size
```

---

## 📊 MONITORING & DASHBOARD

### 🖥️ Web Dashboard (http://localhost:5000)
**Fitur**:
- Real-time trading status
- Profit/Loss tracking
- Position monitoring
- Session analysis
- AI chat integration
- Trading control (start/stop)

**Pages**:
- `/` - Main dashboard
- `/dry-run` - Dry run monitoring
- `/real-trades` - Real trades monitoring
- `/session-analysis` - Session performance analysis
- `/ai-chat` - AI chat interface

### 📱 Telegram Bot
**Commands**:
- `/status` - Trading status
- `/balance` - Current balance
- `/positions` - Open positions
- `/profit` - Daily profit/loss
- `/stop` - Stop trading
- `/start` - Start trading
- `/emergency` - Emergency stop

**Notifications**:
- Trade entry/exit alerts
- Profit/loss updates
- Risk warnings
- System errors
- Session transitions

### 📈 Performance Tracking
**Metrics**:
- Daily/Weekly/Monthly P&L
- Win rate per session
- Average profit per trade
- Maximum drawdown
- Sharpe ratio
- Risk-adjusted returns

---

## 🚀 SETUP & INSTALLATION

### 1️⃣ Prerequisites
```bash
# Python 3.8+
python --version

# Git
git --version
```

### 2️⃣ Clone Repository
```bash
git clone https://github.com/your-repo/levatrade.git
cd levatrade
```

### 3️⃣ Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt

# Install dashboard dependencies
pip install -r requirements_dashboard.txt
```

### 4️⃣ Configuration
```bash
# Copy environment template
copy .env.example .env

# Edit configuration
notepad .env
```

### 5️⃣ Setup API Keys
1. **Bybit API**: Create API key di Bybit dengan trading permission
2. **Telegram Bot**: Create bot via @BotFather
3. **Gemini AI**: Get API key dari Google AI Studio

### 6️⃣ Database Setup
```bash
# Databases akan dibuat otomatis saat pertama kali run
# dry_run_trades.db - untuk simulasi
# real_trades.db - untuk trading nyata
# strategy_performance.db - untuk tracking performa
# psychological_state.db - untuk psychological protection
```

---

## 🎮 CARA PENGGUNAAN

### 🧪 Mode Dry Run (Simulasi)
```bash
# Set dry run mode di .env
DRY_RUN_MODE=true

# Jalankan bot
python crypto_bot_parallel.py
```

### 💰 Mode Real Trading
```bash
# Set real trading mode di .env
DRY_RUN_MODE=false

# Pastikan balance dan risk sudah sesuai
BALANCE_USD=1000
MAX_RISK_PERCENT=0.5

# Jalankan bot
python crypto_bot_parallel.py
```

### 🖥️ Jalankan Dashboard
```bash
# Terminal baru
python dashboard_app.py

# Akses dashboard
http://localhost:5000
```

### 📱 Setup Telegram Bot
1. Start bot dengan `/start`
2. Verify chat ID di logs
3. Test dengan `/status`

### ⚙️ Kontrol Trading
```python
# Via dashboard
# Klik Start/Stop Trading button

# Via Telegram
/stop    # Stop trading
/start   # Start trading
/emergency  # Emergency stop

# Via file
# Edit trading_control.json
{
    "trading_enabled": false,
    "emergency_stop": true
}
```

---

## 🔧 TROUBLESHOOTING

### ❌ Common Issues

#### 1. API Connection Error
```
Error: Invalid API key or secret
```
**Solution**:
- Cek API key dan secret di .env
- Pastikan API key punya trading permission
- Cek IP whitelist di Bybit

#### 2. Telegram Bot Not Working
```
Error: Telegram bot token invalid
```
**Solution**:
- Cek bot token di .env
- Pastikan bot sudah di-start dengan /start
- Cek chat ID sudah benar

#### 3. Database Error
```
Error: Database locked
```
**Solution**:
- Stop semua instance bot
- Restart bot
- Jika masih error, hapus file .db dan restart

#### 4. High Memory Usage
```
Memory usage > 1GB
```
**Solution**:
- Reduce MAX_SYMBOLS di config
- Reduce THREAD_COUNT
- Restart bot secara berkala

#### 5. AI API Limit
```
Error: Gemini API quota exceeded
```
**Solution**:
- Add multiple API keys di GEMINI_API_KEYS
- Reduce AI analysis frequency
- Upgrade Gemini API plan

### 🔍 Debug Mode
```bash
# Enable debug logging
export DEBUG=true
python crypto_bot_parallel.py

# Check logs
tail -f trading.log
```

### 📊 Performance Monitoring
```bash
# Check system resources
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, RAM: {psutil.virtual_memory().percent}%')"

# Check database size
dir *.db

# Check log files
dir *.log
```

### 🆘 Emergency Procedures

#### Stop All Trading Immediately
```bash
# Method 1: Emergency stop via file
echo '{"trading_enabled": false, "emergency_stop": true}' > trading_control.json

# Method 2: Kill process
taskkill /f /im python.exe

# Method 3: Telegram command
/emergency
```

#### Reset System
```bash
# Backup databases
copy *.db backup/

# Reset configuration
copy .env.example .env
copy strategy_config.json.example strategy_config.json

# Clear logs
del *.log

# Restart fresh
python crypto_bot_parallel.py
```

---

## 📞 SUPPORT & MAINTENANCE

### 🔄 Regular Maintenance
- **Daily**: Check profit/loss dan system health
- **Weekly**: Review strategy performance dan adjust parameters
- **Monthly**: Update dependencies dan backup databases

### 📈 Performance Optimization
- Monitor CPU/RAM usage
- Optimize database queries
- Adjust thread count berdasarkan system capacity
- Regular cleanup log files

### 🛠️ Updates & Upgrades
- Keep dependencies updated
- Monitor Bybit API changes
- Update AI models
- Backup before major changes

---

## 📄 CHANGELOG

### Version 2.0.0 (Current)
- ✅ 4-Session strategy implementation
- ✅ Conditional risk escalation
- ✅ AI integration dengan Gemini
- ✅ Comprehensive risk management
- ✅ Web dashboard dengan real-time monitoring
- ✅ Telegram integration
- ✅ Psychological protection system

### Version 1.0.0
- ✅ Basic trading bot
- ✅ Simple risk management
- ✅ Telegram notifications

---

## 📜 LICENSE

MIT License - See LICENSE file for details

---

## 🤝 CONTRIBUTING

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---

**⚠️ DISCLAIMER**: Trading cryptocurrency melibatkan risiko tinggi. Gunakan sistem ini dengan bijak dan hanya dengan modal yang siap hilang. Selalu test di mode dry run terlebih dahulu sebelum trading dengan uang sungguhan.