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

# Load environment variables
load_dotenv()

# ==================
# KONFIGURASI
# ==================
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Trading Parameters (dari environment variables)
BALANCE = float(os.getenv('BALANCE_USD', '1000'))  # Default $1000
MAX_RISK = float(os.getenv('MAX_RISK_PERCENT', '2.0'))  # Default 2% untuk 4H
MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '20'))  # Default 20x untuk 4H
MAX_OPEN_POSITIONS = int(os.getenv('MAX_OPEN_POSITIONS', '3'))  # Default 3 untuk 4H

# Symbol Configuration
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']  # Fixed symbols untuk mode normal
TIMEFRAME = '240'  # 4H = 240 menit

# Indicator Parameters
EMA_FAST = 21
EMA_SLOW = 55
RSI_LENGTH = 14
TP_ATR_MULT = 2.0
SL_ATR_MULT = 1.2
PIVOT_LENGTH = 5

# ==================
# BYBIT CLIENT
# ==================
# GUNAKAN MAINNET untuk data yang sama dengan TradingView
session = HTTP(
    testnet=False,  # MAINNET - data sama dengan TradingView
    api_key=BYBIT_API_KEY if BYBIT_API_KEY else '',
    api_secret=BYBIT_API_SECRET if BYBIT_API_SECRET else ''
)

# ==================
# TELEGRAM BOT
# ==================
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ==================
# HELPER FUNCTIONS
# ==================
def get_klines(symbol, interval='240', limit=200):
    """Ambil data candlestick dari Bybit"""
    try:
        response = session.get_kline(
            category="linear",
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        
        if response['retCode'] == 0:
            data = response['result']['list']
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            df = df.astype({
                'open': float, 'high': float, 'low': float, 
                'close': float, 'volume': float
            })
            df = df.iloc[::-1].reset_index(drop=True)  # Reverse untuk urutan ascending
            return df
        else:
            print(f"Error getting klines for {symbol}: {response['retMsg']}")
            return None
    except Exception as e:
        print(f"Exception in get_klines: {e}")
        return None

def calculate_ema(data, period):
    """Calculate EMA"""
    return data.ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    """Calculate RSI"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(df, period=14):
    """Calculate ATR"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_macd(data, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

def find_pivot_high(df, length=5):
    """Find pivot high (resistance)"""
    highs = df['high'].values
    for i in range(len(highs) - length * 2):
        idx = len(highs) - length - 1 - i
        if idx < length or idx >= len(highs) - length:
            continue
        
        is_pivot = True
        for j in range(1, length + 1):
            if highs[idx] <= highs[idx - j] or highs[idx] <= highs[idx + j]:
                is_pivot = False
                break
        
        if is_pivot:
            return highs[idx]
    return None

def find_pivot_low(df, length=5):
    """Find pivot low (support)"""
    lows = df['low'].values
    for i in range(len(lows) - length * 2):
        idx = len(lows) - length - 1 - i
        if idx < length or idx >= len(lows) - length:
            continue
        
        is_pivot = True
        for j in range(1, length + 1):
            if lows[idx] >= lows[idx - j] or lows[idx] >= lows[idx + j]:
                is_pivot = False
                break
        
        if is_pivot:
            return lows[idx]
    return None

# ==================
# ANALISIS MARKET
# ==================
def analyze_symbol(symbol):
    """Analisis satu symbol"""
    df = get_klines(symbol, TIMEFRAME)
    if df is None or len(df) < 100:
        return None
    
    # Calculate indicators
    df['ema_fast'] = calculate_ema(df['close'], EMA_FAST)
    df['ema_slow'] = calculate_ema(df['close'], EMA_SLOW)
    df['rsi'] = calculate_rsi(df['close'], RSI_LENGTH)
    df['atr'] = calculate_atr(df, 14)
    df['macd_line'], df['signal_line'] = calculate_macd(df['close'])
    
    # Get latest values
    last = df.iloc[-1]
    close = last['close']
    ema_fast = last['ema_fast']
    ema_slow = last['ema_slow']
    rsi = last['rsi']
    atr = last['atr']
    macd_line = last['macd_line']
    signal_line = last['signal_line']
    
    # Support & Resistance
    resistance = find_pivot_high(df, PIVOT_LENGTH)
    support = find_pivot_low(df, PIVOT_LENGTH)
    
    # Market Bias
    bullish = ema_fast > ema_slow and macd_line > signal_line and rsi > 55
    bearish = ema_fast < ema_slow and macd_line < signal_line and rsi < 45
    
    if not bullish and not bearish:
        return None
    
    # Entry Zones
    if bullish and support:
        entry_low = support
        entry_high = support + atr * 0.5
        entry_price = (entry_low + entry_high) / 2  # Mid-point entry
        tp = entry_price + atr * TP_ATR_MULT
        sl = entry_price - atr * SL_ATR_MULT
        direction = "LONG"
    elif bearish and resistance:
        entry_low = resistance - atr * 0.5
        entry_high = resistance
        entry_price = (entry_low + entry_high) / 2  # Mid-point entry
        tp = entry_price - atr * TP_ATR_MULT  # TP di BAWAH entry untuk SHORT
        sl = entry_price + atr * SL_ATR_MULT  # SL di ATAS entry untuk SHORT
        direction = "SHORT"
    else:
        return None
    
    # Check if price in entry zone
    current_close = df.iloc[-1]['close']
    current_low = df.iloc[-1]['low']
    current_high = df.iloc[-1]['high']
    
    # Untuk SHORT: entry zone adalah di sekitar resistance
    # Lebih fleksibel: izinkan entry jika harga mendekati resistance dari bawah
    if direction == "SHORT":
        # Harga boleh sedikit di bawah entry zone (masih dalam range pullback)
        tolerance = atr * 0.2  # Toleransi 20% dari ATR (lebih konservatif)
        price_in_range = (entry_low - tolerance) <= current_close <= entry_high
        # Jangan izinkan entry jika sudah breakout di atas resistance
        not_breakout = current_close <= entry_high * 1.005  # Max 0.5% di atas resistance
        in_zone = price_in_range and not_breakout
    else:  # LONG
        # Untuk LONG: harga harus di sekitar support
        tolerance = atr * 0.2
        price_in_range = entry_low <= current_close <= (entry_high + tolerance)
        # Jangan izinkan entry jika sudah breakdown di bawah support
        not_breakdown = current_close >= entry_low * 0.995  # Max 0.5% di bawah support
        in_zone = price_in_range and not_breakdown
    
    if not in_zone:
        return None
    
    # Risk Management
    sl_distance = abs(entry_price - sl)
    raw_lev = (MAX_RISK / 100) * entry_price / sl_distance
    suggest_lev = min(MAX_LEVERAGE, max(1, round(raw_lev)))
    
    if suggest_lev <= 3:
        lev_mode = "SAFE"
    elif suggest_lev <= 8:
        lev_mode = "NORMAL"
    else:
        lev_mode = "AGGRESSIVE"
    
    # Risk management untuk leveraged trading
    max_margin_per_trade = BALANCE * MAX_RISK / 100  # $20 untuk 2% risk
    
    # Position size berdasarkan margin yang tersedia dan leverage
    max_position_value = max_margin_per_trade * suggest_lev
    pos_size = max_position_value / entry_price  # Quantity dalam coins
    position_value_usd = pos_size * entry_price  # Nilai posisi dalam USD
    
    # Verifikasi margin yang digunakan
    actual_margin = position_value_usd / suggest_lev
    sl_percent = sl_distance / entry_price * 100
    rr_ratio = TP_ATR_MULT / SL_ATR_MULT
    
    return {
        'symbol': symbol,
        'direction': direction,
        'close': close,
        'entry_price': entry_price,
        'entry_low': entry_low,
        'entry_high': entry_high,
        'sl': sl,
        'tp': tp,
        'leverage': suggest_lev,
        'lev_mode': lev_mode,
        'risk_amount': max_margin_per_trade,  # Margin yang digunakan
        'sl_percent': sl_percent,
        'rr_ratio': rr_ratio,
        'pos_size': pos_size
    }

# ==================
# TELEGRAM NOTIFICATION
# ==================
async def send_telegram_alert(signal):
    """Kirim alert ke Telegram"""
    emoji = "📈" if signal['direction'] == "LONG" else "📉"
    
    message = f"""
{emoji} <b>{signal['direction']} SETUP - {signal['symbol']}</b>

💰 <b>Price:</b> ${signal['close']:.4f}
🎯 <b>Entry Zone:</b> ${signal['entry_low']:.4f} - ${signal['entry_high']:.4f}
🛑 <b>Stop Loss:</b> ${signal['sl']:.4f}
✅ <b>Take Profit:</b> ${signal['tp']:.4f}

⚡ <b>Leverage:</b> {signal['leverage']}x ({signal['lev_mode']})
💵 <b>Risk Amount:</b> ${signal['risk_amount']:.2f}
📊 <b>Position Size:</b> {signal['pos_size']:.3f}
📉 <b>SL %:</b> {signal['sl_percent']:.2f}%
🎲 <b>R:R:</b> 1:{signal['rr_ratio']:.2f}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    try:
        await telegram_bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='HTML'
        )
        print(f"✅ Alert sent for {signal['symbol']}")
    except TelegramError as e:
        print(f"❌ Telegram error: {e}")

# ==================
# MAIN LOOP
# ==================
sent_alerts = {}  # Track alerts yang sudah dikirim

async def main():
    """Main loop untuk monitoring"""
    print("🚀 Bot started...")
    print(f"📊 Monitoring symbols: {', '.join(SYMBOLS)}")
    print(f"⏰ Timeframe: {TIMEFRAME}m (4H)")
    print("-" * 50)
    
    while True:
        try:
            for symbol in SYMBOLS:
                signal = analyze_symbol(symbol)
                
                if signal:
                    # Cek apakah alert sudah pernah dikirim untuk candle ini
                    alert_key = f"{symbol}_{signal['direction']}"
                    current_time = int(time.time() / (int(TIMEFRAME) * 60))
                    
                    if alert_key not in sent_alerts or sent_alerts[alert_key] != current_time:
                        await send_telegram_alert(signal)
                        sent_alerts[alert_key] = current_time
                
                # Delay antar symbol
                await asyncio.sleep(2)
            
            # Check setiap 5 menit
            print(f"✓ Scan completed at {datetime.now().strftime('%H:%M:%S')}")
            await asyncio.sleep(300)
            
        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
