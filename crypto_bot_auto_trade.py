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
MAX_OPEN_POSITIONS = int(os.getenv('MAX_OPEN_POSITIONS', '3'))  # Default 3 untuk auto trade

# Scan Parameters
TOP_VOLUME_COUNT = 100
TIMEFRAME = '240'  # 4H
SCAN_INTERVAL = 900  # 15 menit

# AUTO TRADING SETTINGS ⚠️
AUTO_TRADE_ENABLED = True   # ENABLED untuk auto trading
DRY_RUN = False             # False = real order ke Bybit (testnet)
MIN_POSITION_SIZE_USD = 10  # Minimum $10 per posisi

# Indicator Parameters
EMA_FAST = 21
EMA_SLOW = 55
RSI_LENGTH = 14
TP_ATR_MULT = 2.0
SL_ATR_MULT = 1.2
PIVOT_LENGTH = 5

# Parallel Processing
MAX_WORKERS = 20

# ==================
# BYBIT CLIENT
# ==================
# TESTNET - Demo Bybit dengan fake money
session = HTTP(
    testnet=True,  # TESTNET = Demo account
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)

# ==================
# TELEGRAM BOT
# ==================
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Thread-safe lock
api_lock = threading.Lock()

# Track open positions
open_positions = {}

# ==================
# TRADING FUNCTIONS
# ==================
def get_account_balance():
    """Get account balance"""
    try:
        with api_lock:
            response = session.get_wallet_balance(accountType="UNIFIED")
        
        if response['retCode'] == 0:
            balances = response['result']['list'][0]['coin']
            usdt_balance = next((b for b in balances if b['coin'] == 'USDT'), None)
            if usdt_balance:
                return float(usdt_balance['walletBalance'])
        return 0
    except Exception as e:
        print(f"Error getting balance: {e}")
        return 0

def set_leverage(symbol, leverage):
    """Set leverage untuk symbol"""
    try:
        with api_lock:
            response = session.set_leverage(
                category="linear",
                symbol=symbol,
                buyLeverage=str(leverage),
                sellLeverage=str(leverage)
            )
        return response['retCode'] == 0
    except Exception as e:
        print(f"Error setting leverage: {e}")
        return False

def place_order(symbol, side, qty, price=None, order_type="Market", 
                tp_price=None, sl_price=None, reduce_only=False):
    """Place order ke Bybit"""
    try:
        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side,  # "Buy" or "Sell"
            "orderType": order_type,
            "qty": str(qty),
            "reduceOnly": reduce_only
        }
        
        if price:
            params["price"] = str(price)
        
        if tp_price:
            params["takeProfit"] = str(tp_price)
        
        if sl_price:
            params["stopLoss"] = str(sl_price)
        
        with api_lock:
            response = session.place_order(**params)
        
        if response['retCode'] == 0:
            return {
                'success': True,
                'orderId': response['result']['orderId'],
                'orderLinkId': response['result'].get('orderLinkId', '')
            }
        else:
            return {
                'success': False,
                'error': response['retMsg']
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_position(symbol):
    """Get current position"""
    try:
        with api_lock:
            response = session.get_positions(
                category="linear",
                symbol=symbol
            )
        
        if response['retCode'] == 0 and response['result']['list']:
            pos = response['result']['list'][0]
            return {
                'size': float(pos['size']),
                'side': pos['side'],
                'avgPrice': float(pos['avgPrice']),
                'unrealisedPnl': float(pos['unrealisedPnl'])
            }
        return None
    except Exception as e:
        print(f"Error getting position: {e}")
        return None

def close_position(symbol, side, qty):
    """Close position"""
    # Reverse side untuk close
    close_side = "Sell" if side == "Buy" else "Buy"
    return place_order(symbol, close_side, qty, reduce_only=True)

# ==================
# HELPER FUNCTIONS (sama seperti sebelumnya)
# ==================
def get_top_volume_symbols(limit=100):
    try:
        with api_lock:
            response = session.get_tickers(category="linear")
        
        if response['retCode'] == 0:
            tickers = response['result']['list']
            usdt_pairs = [
                {
                    'symbol': t['symbol'],
                    'volume': float(t['volume24h']),
                    'turnover': float(t['turnover24h']),
                    'price': float(t['lastPrice'])
                }
                for t in tickers 
                if t['symbol'].endswith('USDT') and float(t['volume24h']) > 0
            ]
            usdt_pairs.sort(key=lambda x: x['turnover'], reverse=True)
            top_symbols = [pair['symbol'] for pair in usdt_pairs[:limit]]
            
            print(f"📊 Top {len(top_symbols)} volume symbols loaded:")
            for i, pair in enumerate(usdt_pairs[:10], 1):
                print(f"   {i}. {pair['symbol']} - Volume: ${pair['turnover']:,.0f}")
            print(f"   ... and {len(top_symbols) - 10} more")
            
            return top_symbols
        return []
    except Exception as e:
        print(f"Exception in get_top_volume_symbols: {e}")
        return []

def get_klines(symbol, interval='240', limit=200):
    try:
        with api_lock:
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
            df = df.iloc[::-1].reset_index(drop=True)
            return df
        return None
    except:
        return None

def calculate_ema(data, period):
    return data.ewm(span=period, adjust=False).mean()

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(df, period=14):
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
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

def find_pivot_high(df, length=5):
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

def analyze_symbol(symbol):
    try:
        df = get_klines(symbol, TIMEFRAME)
        if df is None or len(df) < 100:
            return None
        
        df['ema_fast'] = calculate_ema(df['close'], EMA_FAST)
        df['ema_slow'] = calculate_ema(df['close'], EMA_SLOW)
        df['rsi'] = calculate_rsi(df['close'], RSI_LENGTH)
        df['atr'] = calculate_atr(df, 14)
        df['macd_line'], df['signal_line'] = calculate_macd(df['close'])
        
        last = df.iloc[-1]
        close = last['close']
        ema_fast = last['ema_fast']
        ema_slow = last['ema_slow']
        rsi = last['rsi']
        atr = last['atr']
        macd_line = last['macd_line']
        signal_line = last['signal_line']
        
        resistance = find_pivot_high(df, PIVOT_LENGTH)
        support = find_pivot_low(df, PIVOT_LENGTH)
        
        bullish = ema_fast > ema_slow and macd_line > signal_line and rsi > 55
        bearish = ema_fast < ema_slow and macd_line < signal_line and rsi < 45
        
        if not bullish and not bearish:
            return None
        
        if bullish and support:
            entry_low = support
            entry_high = support + atr * 0.5
            entry_price = (entry_low + entry_high) / 2
            tp = entry_price + atr * TP_ATR_MULT
            sl = entry_price - atr * SL_ATR_MULT
            direction = "LONG"
            side = "Buy"
        elif bearish and resistance:
            entry_low = resistance - atr * 0.5
            entry_high = resistance
            entry_price = (entry_low + entry_high) / 2
            tp = entry_price - atr * TP_ATR_MULT
            sl = entry_price + atr * SL_ATR_MULT  # SL DI ATAS entry untuk SHORT!
            direction = "SHORT"
            side = "Sell"
        else:
            return None
        
        current_low = df.iloc[-1]['low']
        current_high = df.iloc[-1]['high']
        in_zone_price_only = current_low <= entry_high and current_high >= entry_low
        in_zone = (bullish or bearish) and in_zone_price_only
        
        if not in_zone:
            return None
        
        sl_distance = abs(close - sl)
        raw_lev = (MAX_RISK / 100) * close / sl_distance
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
        pos_size = max_position_value / close  # Quantity dalam coins
        position_value_usd = pos_size * close  # Nilai posisi dalam USD
        
        # Verifikasi margin yang digunakan
        actual_margin = position_value_usd / suggest_lev
        sl_percent = sl_distance / close * 100
        rr_ratio = TP_ATR_MULT / SL_ATR_MULT
        
        return {
            'symbol': symbol,
            'direction': direction,
            'side': side,
            'close': close,
            'entry_low': entry_low,
            'entry_high': entry_high,
            'sl': sl,
            'tp': tp,
            'leverage': suggest_lev,
            'lev_mode': lev_mode,
            'risk_amount': max_margin_per_trade,  # Margin yang digunakan
            'sl_percent': sl_percent,
            'rr_ratio': rr_ratio,
            'pos_size': pos_size,
            'pos_size_usd': pos_size * close
        }
    except:
        return None

# ==================
# AUTO TRADING
# ==================
async def execute_trade(signal):
    """Execute trade berdasarkan signal"""
    symbol = signal['symbol']
    
    # Check if already have position
    if symbol in open_positions:
        print(f"⚠️  {symbol} already has open position, skipping...")
        return False
    
    # Check max positions
    if len(open_positions) >= MAX_OPEN_POSITIONS:
        print(f"⚠️  Max positions ({MAX_OPEN_POSITIONS}) reached, skipping {symbol}...")
        return False
    
    # Check minimum position size
    if signal['pos_size_usd'] < MIN_POSITION_SIZE_USD:
        print(f"⚠️  {symbol} position size ${signal['pos_size_usd']:.2f} < ${MIN_POSITION_SIZE_USD}, skipping...")
        return False
    
    if DRY_RUN:
        print(f"\n🧪 DRY RUN - Would execute trade:")
        print(f"   Symbol: {symbol}")
        print(f"   Side: {signal['side']}")
        print(f"   Size: {signal['pos_size']:.3f}")
        print(f"   Leverage: {signal['leverage']}x")
        print(f"   TP: ${signal['tp']:.4f}")
        print(f"   SL: ${signal['sl']:.4f}")
        
        # Simulate position
        open_positions[symbol] = {
            'side': signal['side'],
            'size': signal['pos_size'],
            'entry': signal['close'],
            'tp': signal['tp'],
            'sl': signal['sl'],
            'time': datetime.now()
        }
        return True
    
    # REAL TRADING
    print(f"\n🚀 Executing trade for {symbol}...")
    
    # 1. Set leverage
    if not set_leverage(symbol, signal['leverage']):
        print(f"❌ Failed to set leverage for {symbol}")
        return False
    
    print(f"✅ Leverage set to {signal['leverage']}x")
    
    # 2. Place order with TP/SL
    result = place_order(
        symbol=symbol,
        side=signal['side'],
        qty=signal['pos_size'],
        order_type="Market",
        tp_price=signal['tp'],
        sl_price=signal['sl']
    )
    
    if result['success']:
        print(f"✅ Order placed successfully!")
        print(f"   Order ID: {result['orderId']}")
        
        # Track position
        open_positions[symbol] = {
            'side': signal['side'],
            'size': signal['pos_size'],
            'entry': signal['close'],
            'tp': signal['tp'],
            'sl': signal['sl'],
            'orderId': result['orderId'],
            'time': datetime.now()
        }
        
        # Send Telegram notification
        await send_trade_notification(signal, result['orderId'])
        
        return True
    else:
        print(f"❌ Order failed: {result['error']}")
        return False

async def send_trade_notification(signal, order_id="DRY_RUN"):
    """Kirim notifikasi trade ke Telegram"""
    emoji = "📈" if signal['direction'] == "LONG" else "📉"
    mode = "🧪 DRY RUN" if DRY_RUN else "🚀 LIVE TRADE"
    
    message = f"""
{mode}
{emoji} <b>{signal['direction']} - {signal['symbol']}</b>

💰 <b>Entry Price:</b> ${signal['close']:.4f}
📊 <b>Position Size:</b> {signal['pos_size']:.3f} (${signal['pos_size_usd']:.2f})
⚡ <b>Leverage:</b> {signal['leverage']}x ({signal['lev_mode']})

🎯 <b>Take Profit:</b> ${signal['tp']:.4f}
🛑 <b>Stop Loss:</b> ${signal['sl']:.4f}

💵 <b>Risk Amount:</b> ${signal['risk_amount']:.2f}
📉 <b>SL %:</b> {signal['sl_percent']:.2f}%
🎲 <b>R:R:</b> 1:{signal['rr_ratio']:.2f}

🆔 <b>Order ID:</b> {order_id}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    try:
        await telegram_bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# ==================
# TELEGRAM NOTIFICATION (untuk signal saja)
# ==================
async def send_telegram_alert(signal):
    emoji = "📈" if signal['direction'] == "LONG" else "📉"
    
    message = f"""
{emoji} <b>{signal['direction']} SIGNAL - {signal['symbol']}</b>

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
# PARALLEL SCANNING
# ==================
def scan_symbols_parallel(symbols):
    signals = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(analyze_symbol, symbols))
    signals = [r for r in results if r is not None]
    return signals

# ==================
# MAIN LOOP
# ==================
sent_alerts = {}

async def main():
    print("🚀 Bot started (Auto Trading Mode)...")
    print(f"⚡ Max Workers: {MAX_WORKERS} threads")
    print(f"⏰ Timeframe: {TIMEFRAME}m (4H)")
    print(f"🔄 Scan Interval: {SCAN_INTERVAL//60} minutes")
    print(f"🤖 Auto Trade: {'ENABLED' if AUTO_TRADE_ENABLED else 'DISABLED'}")
    print(f"🧪 Dry Run: {'YES (Simulation)' if DRY_RUN else 'NO (Real Trading)'}")
    print(f"📊 Max Positions: {MAX_OPEN_POSITIONS}")
    print("-" * 50)
    
    # Get balance
    if not DRY_RUN:
        balance = get_account_balance()
        print(f"💰 Account Balance: ${balance:.2f}")
        print("-" * 50)
    
    # Get symbols
    print("\n📊 Loading top volume symbols...")
    symbols = get_top_volume_symbols(TOP_VOLUME_COUNT)
    
    if not symbols:
        print("❌ Failed to load symbols")
        return
    
    print(f"✅ Loaded {len(symbols)} symbols")
    print("-" * 50)
    
    scan_count = 0
    
    while True:
        try:
            scan_count += 1
            start_time = time.time()
            
            print(f"\n🔍 Scan #{scan_count} started at {datetime.now().strftime('%H:%M:%S')}")
            print(f"📊 Scanning {len(symbols)} symbols in parallel...")
            print(f"💼 Open positions: {len(open_positions)}/{MAX_OPEN_POSITIONS}")
            
            signals = scan_symbols_parallel(symbols)
            
            elapsed = time.time() - start_time
            print(f"⏱️  Scan completed in {elapsed:.2f}s")
            print(f"📈 Found {len(signals)} signals")
            
            if signals:
                for signal in signals:
                    alert_key = f"{signal['symbol']}_{signal['direction']}"
                    current_time = int(time.time() / (int(TIMEFRAME) * 60))
                    
                    # Send alert
                    if alert_key not in sent_alerts or sent_alerts[alert_key] != current_time:
                        await send_telegram_alert(signal)
                        sent_alerts[alert_key] = current_time
                        
                        # Execute trade if enabled
                        if AUTO_TRADE_ENABLED:
                            await execute_trade(signal)
                        
                        await asyncio.sleep(1)
            
            # Refresh symbols every 10 scans
            if scan_count % 10 == 0:
                print("\n🔄 Refreshing top volume symbols...")
                new_symbols = get_top_volume_symbols(TOP_VOLUME_COUNT)
                if new_symbols:
                    symbols = new_symbols
                    print(f"✅ Symbols refreshed")
            
            wait_minutes = SCAN_INTERVAL // 60
            print(f"\n💤 Waiting {wait_minutes} minutes for next scan...")
            print("-" * 50)
            await asyncio.sleep(SCAN_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n👋 Bot stopped by user")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
