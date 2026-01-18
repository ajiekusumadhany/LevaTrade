#!/usr/bin/env python3
"""
Crypto Bot with Dual Interval System
- Position monitoring & early exit: 30 seconds
- New signal scanning: 3 minutes
"""
import os
import time
import asyncio
from datetime import datetime
from pybit.unified_trading import HTTP
import pandas as pd
import numpy as np
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import threading
from dry_run_system import dry_run_system
from early_exit_system import early_exit_system
from error_notification_system import error_notifier, notify_insufficient_balance, notify_order_rejected

# Load environment variables
load_dotenv()

# ==================
# KONFIGURASI
# ==================
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Trading Parameters
SCAN_ALL_USDT = False  # Kembali ke top volume untuk menghindari rate limit
TOP_VOLUME_COUNT = 100  # Top 100 pairs untuk balance antara coverage dan rate limit
TIMEFRAME = '15'  # 15M = 15 menit (scalping/intraday)
BALANCE = 1000  # USD
MAX_RISK = 1.0  # % (lebih kecil untuk 15M karena lebih sering trade)
MAX_LEVERAGE = 10  # Lebih rendah untuk 15M (risk management)

# Auto Trading Settings
AUTO_TRADE_ENABLED = True   # Enable/disable auto trading
DRY_RUN = True             # True = simulasi saja, False = trading nyata
MAX_OPEN_POSITIONS = 10     # Maksimal posisi terbuka bersamaan untuk scalping
MIN_POSITION_SIZE_USD = 10 # Minimal ukuran posisi dalam USD

# Dual Interval System
SCAN_INTERVAL = 180   # 3 menit untuk scan sinyal baru (menghindari rate limit)
POSITION_UPDATE_INTERVAL = 30  # 30 detik untuk update posisi & early exit monitoring

# Indicator Parameters (scalping agresif)
EMA_FAST = 5   # Sangat cepat untuk scalping
EMA_SLOW = 13  # Lebih cepat lagi
RSI_LENGTH = 9   # RSI lebih sensitif
TP_ATR_MULT = 0.8  # Target sangat dekat (scalping)
SL_ATR_MULT = 0.6  # SL sangat ketat (scalping)
PIVOT_LENGTH = 2   # Pivot sangat sensitif

# Parallel Processing
MAX_WORKERS = 100  # 1 thread per symbol untuk maksimal parallelism

# ==================
# BYBIT CLIENT
# ==================
session = HTTP(
    testnet=False,  # MAINNET - data dan trading real
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)

trading_session = HTTP(
    testnet=False,   # MAINNET - untuk real trading
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)

# Thread-safe lock untuk API calls
api_lock = threading.Lock()

# Track open positions
open_positions = {}  # {symbol: position_info}

# Track sent alerts
sent_alerts = {}  # Track alerts yang sudah dikirim

print("🚀 Crypto Bot with Dual Interval System")
print(f"📊 Position Updates: Every {POSITION_UPDATE_INTERVAL} seconds")
print(f"🔍 Signal Scanning: Every {SCAN_INTERVAL//60} minutes")
print("=" * 60)

if __name__ == "__main__":
    print("⚠️  This is the new dual interval bot structure")
    print("🔄 Copy functions from crypto_bot_parallel.py to complete this file")
    print("📝 Then update the main bot file with this structure")