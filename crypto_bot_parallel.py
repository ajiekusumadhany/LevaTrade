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
import re
from dry_run_system import dry_run_system
from early_exit_system import early_exit_system
from error_notification_system import error_notifier, notify_insufficient_balance, notify_order_rejected
from gemini_ai_system import get_gemini_analyst
from progressive_risk_system import progressive_risk_system
from hard_stop_system import hard_stop_system

# Load environment variables
load_dotenv()

# ==================
# HTML CLEANING FOR TELEGRAM
# ==================
def clean_html_for_telegram(text: str) -> str:
    """
    Clean HTML content for Telegram compatibility
    Removes unsupported HTML tags and converts supported ones
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove or convert unsupported HTML tags
    text = re.sub(r'<div[^>]*>', '', text)
    text = re.sub(r'</div>', '\n', text)
    text = re.sub(r'<span[^>]*>', '', text)
    text = re.sub(r'</span>', '', text)
    text = re.sub(r'<p[^>]*>', '', text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<ul[^>]*>', '', text)
    text = re.sub(r'</ul>', '', text)
    text = re.sub(r'<ol[^>]*>', '', text)
    text = re.sub(r'</ol>', '', text)
    text = re.sub(r'<li[^>]*>', '• ', text)
    text = re.sub(r'</li>', '\n', text)
    text = re.sub(r'<h[1-6][^>]*>', '<b>', text)
    text = re.sub(r'</h[1-6]>', '</b>\n', text)
    
    # Convert supported HTML tags
    text = re.sub(r'<strong[^>]*>', '<b>', text)
    text = re.sub(r'</strong>', '</b>', text)
    text = re.sub(r'<em[^>]*>', '<i>', text)
    text = re.sub(r'</em>', '</i>', text)
    text = re.sub(r'<br[^>]*/?>', '\n', text)
    
    # Remove any remaining unsupported HTML tags (but keep <b>, <i>, <u>, <s>, <code>, <pre>)
    text = re.sub(r'<(?!/?(?:b|i|u|s|code|pre)\b)[^>]+>', '', text)
    
    # Fix unclosed tags by ensuring all opening tags have closing tags
    # Count and balance <b> tags
    b_open = text.count('<b>')
    b_close = text.count('</b>')
    if b_open > b_close:
        text += '</b>' * (b_open - b_close)
    elif b_close > b_open:
        text = '<b>' * (b_close - b_open) + text
    
    # Count and balance <i> tags
    i_open = text.count('<i>')
    i_close = text.count('</i>')
    if i_open > i_close:
        text += '</i>' * (i_open - i_close)
    elif i_close > i_open:
        text = '<i>' * (i_close - i_open) + text
    
    # Count and balance <u> tags
    u_open = text.count('<u>')
    u_close = text.count('</u>')
    if u_open > u_close:
        text += '</u>' * (u_open - u_close)
    elif u_close > u_open:
        text = '<u>' * (u_close - u_open) + text
    
    # Count and balance <s> tags
    s_open = text.count('<s>')
    s_close = text.count('</s>')
    if s_open > s_close:
        text += '</s>' * (s_open - s_close)
    elif s_close > s_open:
        text = '<s>' * (s_close - s_open) + text
    
    # Count and balance <code> tags
    code_open = text.count('<code>')
    code_close = text.count('</code>')
    if code_open > code_close:
        text += '</code>' * (code_open - code_close)
    elif code_close > code_open:
        text = '<code>' * (code_close - code_open) + text
    
    # Count and balance <pre> tags
    pre_open = text.count('<pre>')
    pre_close = text.count('</pre>')
    if pre_open > pre_close:
        text += '</pre>' * (pre_open - pre_close)
    elif pre_close > pre_open:
        text = '<pre>' * (pre_close - pre_open) + text
    
    # Clean up multiple newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r'^\s+|\s+$', '', text)
    
    return text

# ==================
# KONFIGURASI
# ==================
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Trading Parameters (dari environment variables)
BALANCE = float(os.getenv('BALANCE_USD', '1167'))  # Updated to actual balance
MAX_RISK = float(os.getenv('MAX_RISK_PERCENT', '0.5'))  # Reduced to 0.5% for safety
MIN_LEVERAGE = int(os.getenv('MIN_LEVERAGE', '5'))  # Default 5x minimum
MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '15'))  # Reduced to 15x for safety
MAX_OPEN_POSITIONS = int(os.getenv('MAX_OPEN_POSITIONS', '15'))  # Reduced to 15 positions

# Scan Parameters
SCAN_ALL_USDT = False  # Kembali ke top volume untuk menghindari rate limit
TOP_VOLUME_COUNT = 100  # Top 100 pairs untuk balance antara coverage dan rate limit
TIMEFRAME = '15'  # 15M = 15 menit (scalping/intraday)

# Auto Trading Settings
AUTO_TRADE_ENABLED = True   # Enable/disable auto trading
DRY_RUN = True             # True = simulasi saja, False = trading nyata
MIN_POSITION_SIZE_USD = 2  # Minimal ukuran posisi dalam USD (turun untuk balance $200)

# Scan Interval (scalping agresif)
SCAN_INTERVAL = 180   # 3 menit untuk scan sinyal baru (menghindari rate limit)
POSITION_UPDATE_INTERVAL = 30  # 30 detik untuk update posisi & early exit monitoring

# Indicator Parameters (scalping agresif)
EMA_FAST = 5   # Sangat cepat untuk scalping
EMA_SLOW = 13  # Lebih cepat lagi
RSI_LENGTH = 9   # RSI lebih sensitif
TP_ATR_MULT = 1.2  # Improved from 0.8 - Better risk/reward ratio (2:1)
SL_ATR_MULT = 0.6  # Keep tight SL for scalping
PIVOT_LENGTH = 2   # Pivot sangat sensitif

# Parallel Processing
MAX_WORKERS = 100  # 1 thread per symbol untuk maksimal parallelism

# ==================
# BYBIT CLIENT
# ==================
# GUNAKAN MAINNET untuk data dan trading
session = HTTP(
    testnet=False,  # MAINNET - data dan trading real
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)

# Trading session (MAINNET untuk real trading)
trading_session = HTTP(
    testnet=False,   # MAINNET - untuk real trading
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)

# ==================
# TELEGRAM BOT
# ==================
# Bot akan di-initialize di dalam async context

# Thread-safe lock untuk API calls
api_lock = threading.Lock()

# Track open positions
open_positions = {}  # {symbol: position_info}

# ==================
# AUTO TRADING FUNCTIONS
# ==================
def get_account_balance():
    """Get account balance with error handling"""
    try:
        with api_lock:
            response = trading_session.get_wallet_balance(accountType="UNIFIED")
        
        if response['retCode'] == 0:
            coins = response['result']['list'][0]['coin']
            usdt_balance = 0
            for coin in coins:
                if coin['coin'] == 'USDT':
                    usdt_balance = float(coin['walletBalance'])
                    break
            return usdt_balance
        elif response['retCode'] == 10006:  # Rate limit
            print(f"⚠️  Rate limit hit getting balance")
            return 0
        else:
            print(f"❌ Error getting balance: {response.get('retMsg', 'Unknown error')}")
            return 0
    except Exception as e:
        print(f"❌ Exception getting balance: {e}")
        # Send error notification for balance check failures
        asyncio.create_task(error_notifier.notify_trading_error(
            "network_error",
            "BALANCE_CHECK",
            {'connection_status': 'Failed', 'error_message': str(e)},
            e
        ))
        return 0

def set_leverage(symbol, leverage):
    """Set leverage for symbol"""
    try:
        with api_lock:
            response = trading_session.set_leverage(
                category="linear",
                symbol=symbol,
                buyLeverage=str(leverage),
                sellLeverage=str(leverage)
            )
        return response['retCode'] == 0
    except Exception as e:
        print(f"❌ Error setting leverage for {symbol}: {e}")
        return False

def place_order(symbol, side, qty, price=None, order_type="Market", tp_price=None, sl_price=None):
    """Place order with TP/SL"""
    try:
        order_params = {
            "category": "linear",
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": str(qty),
            "timeInForce": "GTC"
        }
        
        if price and order_type == "Limit":
            order_params["price"] = str(price)
        
        if tp_price:
            order_params["takeProfit"] = str(tp_price)
        
        if sl_price:
            order_params["stopLoss"] = str(sl_price)
        
        if DRY_RUN:
            print(f"🔄 [DRY RUN] Would place {side} order for {symbol}: {qty} @ {price if price else 'Market'}")
            print(f"   TP: {tp_price}, SL: {sl_price}")
            return True, "dry_run_order_id"
        
        with api_lock:
            response = trading_session.place_order(**order_params)
        
        if response['retCode'] == 0:
            order_id = response['result']['orderId']
            print(f"✅ Order placed for {symbol}: {order_id}")
            return True, order_id
        else:
            print(f"❌ Order failed for {symbol}: {response['retMsg']}")
            return False, None
    except Exception as e:
        print(f"❌ Error placing order for {symbol}: {e}")
        return False, None

def get_open_positions():
    """Get current open positions"""
    try:
        with api_lock:
            response = trading_session.get_positions(category="linear", settleCoin="USDT")
        
        if response['retCode'] == 0:
            positions = {}
            for pos in response['result']['list']:
                if float(pos['size']) > 0:
                    positions[pos['symbol']] = {
                        'side': pos['side'],
                        'size': float(pos['size']),
                        'entry_price': float(pos['avgPrice']),
                        'unrealized_pnl': float(pos['unrealisedPnl']),
                        'leverage': pos['leverage']
                    }
            return positions
        return {}
    except Exception as e:
        print(f"❌ Error getting positions: {e}")
        return {}

async def execute_trade(signal):
    """Execute trade based on signal with error handling"""
    try:
        symbol = signal['symbol']
        direction = signal['direction']
        
        # CRITICAL MARGIN SAFETY CHECK - Must be first check
        current_positions = dry_run_system.get_open_positions()
        current_balance = dry_run_system.get_current_balance()
        
        # Calculate current margin usage
        total_existing_margin = 0
        for pos in current_positions:
            pos_value = pos.get('position_value_usd', 0)
            leverage = pos.get('leverage', 1)
            if pos_value and leverage:
                existing_margin = pos_value / leverage
                total_existing_margin += existing_margin
        
        current_margin_usage = (total_existing_margin / current_balance) * 100 if current_balance > 0 else 0
        
        # HARD BLOCK: No new positions if margin usage > 90% (stricter limit)
        if current_margin_usage > 90:
            print(f"🚨🛑 MARGIN SAFETY BLOCK: Current usage {current_margin_usage:.1f}% > 90%")
            print(f"🚨🛑 REJECTING ALL NEW TRADES - Margin: ${total_existing_margin:.2f} / Balance: ${current_balance:.2f}")
            print(f"🚨🛑 {symbol} TRADE REJECTED - MARGIN LIMIT EXCEEDED")
            return False
        
        # Calculate required margin for new position
        position_value_usd = signal['position_value_usd']
        leverage = signal['leverage']
        required_margin = position_value_usd / leverage
        
        # Check if adding this position would exceed 90% (stricter)
        total_margin_after = total_existing_margin + required_margin
        margin_usage_after = (total_margin_after / current_balance) * 100
        
        if margin_usage_after > 90:
            print(f"🚨🛑 MARGIN SAFETY BLOCK: Adding {symbol} would cause {margin_usage_after:.1f}% usage (>90%)")
            print(f"🚨🛑 Current: ${total_existing_margin:.2f} + Required: ${required_margin:.2f} = ${total_margin_after:.2f}")
            print(f"🚨🛑 {symbol} TRADE REJECTED - WOULD EXCEED MARGIN LIMIT")
            return False

        # HARD STOP: Check drawdown 20%
        can_trade, reason = hard_stop_system.can_trade()
        if not can_trade:
            print(f"🚨🛑 HARD STOP: {reason}")
            print(f"🔴 BOT STOPPED - Manual restart required!")
            # Send emergency notification
            await error_notifier.notify_trading_error(
                "hard_stop_triggered",
                "EMERGENCY",
                hard_stop_system.get_status()
            )
            # Exit the entire program
            import sys
            sys.exit(1)
        
        # GUARDRAIL 3: Progressive Risk Check
        can_open, reason = progressive_risk_system.can_open_new_position()
        if not can_open:
            print(f"🛑 PROGRESSIVE RISK: {reason}")
            return False
        
        leverage = signal['leverage']
        qty = signal['pos_size']
        tp_price = signal['tp']
        sl_price = signal['sl']
        
        # Check if already have position for this symbol
        current_positions = dry_run_system.get_open_positions()
        if any(pos['symbol'] == symbol for pos in current_positions):
            print(f"⚠️  Already have position for {symbol}, skipping...")
            return False
        
        # Check max positions limit
        if len(current_positions) >= MAX_OPEN_POSITIONS:
            print(f"⚠️  Max positions ({MAX_OPEN_POSITIONS}) reached, skipping {symbol}...")
            await error_notifier.notify_trading_error(
                "position_limit", 
                symbol,
                {
                    'current_positions': len(current_positions),
                    'max_positions': MAX_OPEN_POSITIONS,
                    'total_exposure': sum(pos['position_value_usd'] for pos in current_positions)
                }
            )
            return False
        
        # Check minimum position size
        position_value_usd = signal['position_value_usd']
        if position_value_usd < MIN_POSITION_SIZE_USD:
            print(f"⚠️  Position size too small for {symbol}: ${position_value_usd:.2f} < ${MIN_POSITION_SIZE_USD}")
            return False
        
        # Generate AI entry reasoning before opening position
        try:
            gemini_analyst = get_gemini_analyst()
            if gemini_analyst:
                print(f"🤖 Generating AI entry reasoning for {symbol} {direction}...")
                ai_entry_reasoning = await gemini_analyst.generate_entry_reasoning(signal)
                signal['ai_entry_reasoning'] = ai_entry_reasoning
                print(f"✅ AI entry reasoning generated for {symbol}")
                
                # AI reasoning akan dikirim bersamaan dengan trade alert, bukan terpisah
                # await send_ai_entry_reasoning_telegram(symbol, direction, ai_entry_reasoning)
            else:
                signal['ai_entry_reasoning'] = ""
                print(f"⚠️  Gemini AI not available for {symbol}")
        except Exception as e:
            print(f"❌ Error generating AI entry reasoning for {symbol}: {e}")
            signal['ai_entry_reasoning'] = ""
        
        if DRY_RUN:
            # DOUBLE-CHECK: Prevent race condition duplicates
            current_positions_recheck = dry_run_system.get_open_positions()
            if any(pos['symbol'] == symbol for pos in current_positions_recheck):
                print(f"⚠️  Race condition detected! {symbol} position opened by another thread, skipping...")
                return False
            
            # Use dry run system
            position_id = await dry_run_system.open_position(signal)
            print(f"🚀 [DRY RUN] Trade executed for {symbol}: {direction} {qty} @ {leverage}x")
            return True
        else:
            # Real trading logic with comprehensive error handling
            
            # 1. Check account balance first
            current_balance = get_account_balance()
            required_margin = position_value_usd / leverage
            
            if current_balance < required_margin:
                print(f"❌ Insufficient balance for {symbol}: Required ${required_margin:.2f}, Available ${current_balance:.2f}")
                await notify_insufficient_balance(symbol, required_margin, current_balance, qty, leverage)
                return False
            
            # 2. Set leverage with error handling
            try:
                if not set_leverage(symbol, leverage):
                    print(f"❌ Failed to set leverage for {symbol}")
                    await error_notifier.notify_trading_error(
                        "leverage_error",
                        symbol,
                        {
                            'requested_leverage': leverage,
                            'max_leverage': MAX_LEVERAGE,
                            'position_value': position_value_usd
                        }
                    )
                    return False
            except Exception as lev_error:
                print(f"❌ Leverage error for {symbol}: {lev_error}")
                await error_notifier.notify_trading_error(
                    "leverage_error",
                    symbol,
                    {
                        'requested_leverage': leverage,
                        'max_leverage': MAX_LEVERAGE,
                        'position_value': position_value_usd
                    },
                    lev_error
                )
                return False
            
            # 3. Determine side
            side = "Buy" if direction == "LONG" else "Sell"
            
            # 4. Place market order with TP/SL and error handling
            try:
                success, order_id = place_order(
                    symbol=symbol,
                    side=side,
                    qty=qty,
                    order_type="Market",
                    tp_price=tp_price,
                    sl_price=sl_price
                )
                
                if success:
                    # Track position
                    open_positions[symbol] = {
                        'direction': direction,
                        'entry_time': datetime.now(),
                        'order_id': order_id,
                        'qty': qty,
                        'tp': tp_price,
                        'sl': sl_price,
                        'leverage': leverage,
                        'entry_price': signal['close'],  # Store entry price for early exit
                        'atr_value': signal.get('atr_value', 0.01)  # Store ATR for early exit
                    }
                    
                    print(f"🚀 Trade executed for {symbol}: {direction} {qty} @ {leverage}x")
                    return True
                else:
                    # Order failed
                    await notify_order_rejected(
                        symbol, 
                        "Market", 
                        signal['close'], 
                        qty, 
                        "Order placement failed",
                        "UNKNOWN"
                    )
                    return False
                    
            except Exception as order_error:
                print(f"❌ Order error for {symbol}: {order_error}")
                await notify_order_rejected(
                    symbol,
                    "Market",
                    signal['close'],
                    qty,
                    str(order_error),
                    "EXCEPTION"
                )
                return False
        
    except Exception as e:
        print(f"❌ Error executing trade for {signal['symbol']}: {e}")
        await error_notifier.notify_trading_error(
            "general_error",
            signal['symbol'],
            {'error_message': str(e)},
            e
        )
        return False

# ==================
# GET TOP VOLUME SYMBOLS
# ==================
def get_top_volume_symbols(limit=100):
    """Ambil top volume symbols dari Bybit dengan Open Interest filtering"""
    try:
        with api_lock:
            response = session.get_tickers(category="linear")
        
        if response['retCode'] == 0:
            tickers = response['result']['list']
            
            # Filter USDT pairs dengan kriteria scalping
            usdt_pairs = []
            
            for t in tickers:
                if t['symbol'].endswith('USDT') and float(t['volume24h']) > 0:
                    symbol_data = {
                        'symbol': t['symbol'],
                        'volume': float(t['volume24h']),
                        'turnover': float(t['turnover24h']),
                        'price': float(t['lastPrice']),
                        'open_interest': float(t.get('openInterest', 0)),
                        'price_change_percent': float(t.get('price24hPcnt', 0)) * 100
                    }
                    
                    # SCALPING FILTERS - Kriteria ketat untuk scalping
                    # 1. Minimum turnover untuk likuiditas
                    if symbol_data['turnover'] < 1000000:  # Min $1M turnover
                        continue
                    
                    # 2. Minimum Open Interest untuk depth
                    if symbol_data['open_interest'] < 500000:  # Min $500K OI
                        continue
                    
                    # 3. Hindari volatilitas ekstrem (>15% dalam 24h)
                    if abs(symbol_data['price_change_percent']) > 15:
                        continue
                    
                    # 4. Minimum price untuk menghindari micro caps
                    if symbol_data['price'] < 0.001:
                        continue
                    
                    usdt_pairs.append(symbol_data)
            
            # Sort by combined score: turnover + open_interest
            # Prioritas: Likuiditas tinggi + OI tinggi = Execution terbaik
            for pair in usdt_pairs:
                # Normalized score (0-1) untuk turnover dan OI
                turnover_score = min(pair['turnover'] / 1000000000, 1)  # Max 1B
                oi_score = min(pair['open_interest'] / 100000000, 1)    # Max 100M
                pair['scalping_score'] = (turnover_score * 0.6) + (oi_score * 0.4)
            
            # Sort by scalping score
            usdt_pairs.sort(key=lambda x: x['scalping_score'], reverse=True)
            
            if SCAN_ALL_USDT:
                # Ambil semua USDT pairs yang lolos filter
                top_symbols = [pair['symbol'] for pair in usdt_pairs]
                print(f"📊 {len(top_symbols)} USDT pairs loaded (with OI filter):")
            else:
                # Ambil top N saja
                top_symbols = [pair['symbol'] for pair in usdt_pairs[:limit]]
                print(f"📊 Top {len(top_symbols)} scalping-ready symbols loaded:")
            
            # Show top 10 dengan detail OI
            for i, pair in enumerate(usdt_pairs[:10], 1):
                oi_millions = pair['open_interest'] / 1000000
                print(f"   {i}. {pair['symbol']} - Vol: ${pair['turnover']:,.0f} | OI: ${oi_millions:.1f}M | Score: {pair['scalping_score']:.3f}")
            
            if len(top_symbols) > 10:
                print(f"   ... and {len(top_symbols) - 10} more")
            
            return top_symbols
        else:
            print(f"Error getting tickers: {response['retMsg']}")
            return []
    except Exception as e:
        print(f"Exception in get_top_volume_symbols: {e}")
        return []

# ==================
# HELPER FUNCTIONS
# ==================
def get_klines(symbol, interval='240', limit=200):
    """Ambil data candlestick dari Bybit dengan error handling"""
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
        elif response['retCode'] == 10006:  # Rate limit
            print(f"⚠️  Rate limit hit for {symbol}")
            # Don't send notification for every rate limit, just log
            return None
        else:
            print(f"❌ API error for {symbol}: {response.get('retMsg', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"❌ Exception getting klines for {symbol}: {e}")
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
    try:
        # EARLY EXIT: Skip jika sudah ada posisi untuk symbol ini
        current_positions = dry_run_system.get_open_positions()
        if any(pos['symbol'] == symbol for pos in current_positions):
            return None  # Skip analysis untuk symbol yang sudah ada posisinya
        
        df = get_klines(symbol, TIMEFRAME)
        if df is None or len(df) < 100:
            return None
        
        # Calculate indicators (scalping agresif)
        df['ema_fast'] = calculate_ema(df['close'], EMA_FAST)  # EMA 5
        df['ema_slow'] = calculate_ema(df['close'], EMA_SLOW)  # EMA 13
        df['rsi'] = calculate_rsi(df['close'], RSI_LENGTH)     # RSI 9
        df['atr'] = calculate_atr(df, 14)                      # ATR 14
        df['macd_line'], df['signal_line'] = calculate_macd(df['close'], 5, 13, 4)  # MACD sangat cepat untuk scalping
        
        # Get latest values
        last = df.iloc[-1]
        close = last['close']
        ema_fast = last['ema_fast']
        ema_slow = last['ema_slow']
        rsi = last['rsi']
        atr = last['atr']
        macd_line = last['macd_line']
        signal_line = last['signal_line']
        
        # Check for NaN values
        if pd.isna(atr) or atr == 0 or pd.isna(ema_fast) or pd.isna(ema_slow):
            return None
        
        # Support & Resistance
        resistance = find_pivot_high(df, PIVOT_LENGTH)
        support = find_pivot_low(df, PIVOT_LENGTH)
        
        # Market Bias (SCALPING AGRESIF - lebih sensitif)
        # Cek trend momentum saja, tidak perlu semua kondisi
        ema_bullish = ema_fast > ema_slow
        ema_bearish = ema_fast < ema_slow
        macd_bullish = macd_line > signal_line
        macd_bearish = macd_line < signal_line
        
        # RSI untuk momentum (lebih fleksibel)
        rsi_oversold = rsi < 35
        rsi_overbought = rsi > 65
        rsi_neutral = 35 <= rsi <= 65
        
        # SCALPING SIGNALS - Lebih selektif dengan filter kualitas
        bullish = False
        bearish = False
        
        # Tambahan filter kualitas untuk mengurangi noise
        volume_ok = df['volume'].iloc[-1] > df['volume'].rolling(20).mean().iloc[-1]  # Volume di atas rata-rata
        volatility_ok = atr > df['atr'].rolling(10).mean().iloc[-1] * 0.8  # ATR cukup untuk scalping
        
        # LONG conditions (lebih ketat)
        if ema_bullish and macd_bullish and rsi_neutral and volume_ok and volatility_ok:
            bullish = True
        elif ema_bullish and rsi_oversold and volume_ok:  # RSI oversold + trend up
            bullish = True
            
        # SHORT conditions (lebih ketat)  
        if ema_bearish and macd_bearish and rsi_neutral and volume_ok and volatility_ok:
            bearish = True
        elif ema_bearish and rsi_overbought and volume_ok:  # RSI overbought + trend down
            bearish = True
        
        # Entry Zones (SCALPING - tidak butuh support/resistance)
        # Gunakan price action saja dengan ATR
        if bullish:
            # LONG: entry di sekitar harga saat ini
            entry_low = close - atr * 0.1   # Entry zone sangat kecil
            entry_high = close + atr * 0.1
            entry_price = close  # Entry langsung di market price
            tp = entry_price + atr * TP_ATR_MULT  # 0.8x ATR (target dekat)
            sl = entry_price - atr * SL_ATR_MULT  # 0.6x ATR (SL ketat)
            direction = "LONG"
        elif bearish:
            # SHORT: entry di sekitar harga saat ini  
            entry_low = close - atr * 0.1
            entry_high = close + atr * 0.1
            entry_price = close  # Entry langsung di market price
            tp = entry_price - atr * TP_ATR_MULT  # 0.8x ATR (target dekat, DI BAWAH entry untuk SHORT!)
            sl = entry_price + atr * SL_ATR_MULT  # 0.6x ATR (SL ketat, DI ATAS entry untuk SHORT!)
            direction = "SHORT"
        else:
            return None
        
        # SCALPING: Selalu dalam zone (market order)
        in_zone = True  # Untuk scalping, kita entry langsung di market price
        
        # Risk Management (disesuaikan untuk 15M)
        sl_distance = abs(close - sl)
        
        # GUARDRAIL 1: SL minimum 0.08% (anti-wick protection)
        sl_percent_check = sl_distance / close
        if sl_percent_check < 0.0008:  # 0.08%
            print(f"⚠️  {symbol} SKIPPED: SL terlalu ketat ({sl_percent_check*100:.3f}% < 0.08%) - rawan wick")
            return None
        
        # Leverage berdasarkan SL distance untuk margin efficiency
        sl_percent = sl_distance / close  # SL sebagai persentase harga
        
        if sl_percent < 0.005:  # SL sangat dekat (<0.5%)
            suggest_lev = 20  # Max leverage untuk margin efficiency
            lev_mode = "AGGRESSIVE"
        elif sl_percent < 0.01:  # SL dekat (<1%)
            suggest_lev = 15
            lev_mode = "AGGRESSIVE" 
        elif sl_percent < 0.015:  # SL normal (<1.5%)
            suggest_lev = 10
            lev_mode = "NORMAL"
        elif sl_percent < 0.02:  # SL agak jauh (<2%)
            suggest_lev = 8
            lev_mode = "NORMAL"
        else:  # SL jauh (>2%)
            suggest_lev = 5   # Min leverage untuk safety
            lev_mode = "SAFE"
        
        # Pastikan dalam range yang diizinkan
        suggest_lev = min(MAX_LEVERAGE, max(MIN_LEVERAGE, suggest_lev))
        
        # Risk management untuk leveraged trading - gunakan balance dinamis untuk dry run
        if DRY_RUN:
            # Untuk dry run, gunakan balance dinamis (starting balance + total PnL)
            current_balance = dry_run_system.get_current_balance()
        else:
            # Untuk real trading, gunakan balance dari API
            current_balance = get_account_balance()
        
        # FORMULA BENAR:
        # Risk = $10 (1% balance)
        # Position Size = Risk / SL Distance (dalam USD)
        # Leverage hanya untuk mengurangi margin, tidak mempengaruhi position size
        
        # GUARDRAIL 3: Progressive Risk - gunakan risk bertahap
        adjusted_risk_percent = progressive_risk_system.get_adjusted_risk_percent(current_balance)
        risk_amount = current_balance * adjusted_risk_percent / 100
        
        # Show risk info
        risk_info = progressive_risk_system.get_risk_info()
        print(f"📊 RISK INFO: Trade #{risk_info['daily_trades']+1}, Tier: {risk_info['tier_name']}, Risk: {adjusted_risk_percent:.1f}%")
        
        # DEBUG: Print calculation
        print(f"🔍 DEBUG {symbol}: Balance=${current_balance:.2f}, Risk=${risk_amount:.2f}, SL_dist=${sl_distance:.6f}, Lev={suggest_lev}x")
        
        # Position size berdasarkan risk dan SL distance
        pos_size = risk_amount / sl_distance  # Quantity dalam coins
        position_value_usd = pos_size * close  # Nilai posisi dalam USD
        
        # MARGIN CHECK: Pastikan margin tidak melebihi balance yang tersedia
        required_margin = position_value_usd / suggest_lev
        
        # Check margin dengan posisi yang sudah ada
        current_positions = dry_run_system.get_open_positions() if DRY_RUN else get_open_positions()
        total_existing_margin = 0
        
        print(f"🔍 MARGIN DEBUG: Found {len(current_positions)} existing positions")
        
        if DRY_RUN:
            for i, pos in enumerate(current_positions, 1):
                pos_value = pos.get('position_value_usd')
                leverage = pos.get('leverage')
                if pos_value and leverage:
                    existing_margin = pos_value / leverage
                    total_existing_margin += existing_margin
                    print(f"   {i}. {pos['symbol']}: ${pos_value:.2f} / {leverage}x = ${existing_margin:.2f}")
                else:
                    print(f"   {i}. {pos['symbol']}: INVALID DATA (pos_value={pos_value}, leverage={leverage})")
        else:
            for symbol_pos, pos in current_positions.items():
                entry_price = pos.get('entry_price', 0) or 0
                size = pos.get('size', 0) or 0
                leverage = float(pos.get('leverage', 1) or 1)
                if entry_price and size and leverage:
                    existing_position_value = entry_price * size
                    existing_margin = existing_position_value / leverage
                    total_existing_margin += existing_margin
        
        total_margin_needed = total_existing_margin + required_margin
        margin_usage_percent = (total_margin_needed / current_balance) * 100
        
        print(f"🔍 MARGIN CALC: Existing=${total_existing_margin:.2f}, Required=${required_margin:.2f}, Total=${total_margin_needed:.2f}")
        print(f"🔍 MARGIN USAGE: {margin_usage_percent:.1f}% of ${current_balance:.2f}")
        
        # REJECT jika margin usage akan melebihi 90% (stricter safety buffer)
        if margin_usage_percent > 90:
            print(f"❌🛑 {symbol} REJECTED: Margin usage akan {margin_usage_percent:.1f}% (>90%)")
            print(f"   Current margin: ${total_existing_margin:.2f}, Required: ${required_margin:.2f}, Balance: ${current_balance:.2f}")
            print(f"❌🛑 SIGNAL REJECTED - MARGIN SAFETY LIMIT")
            return None
        
        print(f"🔍 Position: {pos_size:.3f} coins, Value: ${position_value_usd:.2f}")
        print(f"🔍 Margin: ${required_margin:.2f} ({margin_usage_percent:.1f}% total usage)")
        
        # Verifikasi: Jika kena SL, rugi = risk_amount
        sl_loss = abs(close - sl) * pos_size
        print(f"🔍 SL Loss Verification: ${sl_loss:.2f} (should be ${risk_amount:.2f})")
        
        # Verifikasi
        actual_margin = position_value_usd / suggest_lev
        sl_percent_display = sl_percent * 100  # Untuk display (0.25%)
        rr_ratio = TP_ATR_MULT / SL_ATR_MULT
        
        return {
            'symbol': symbol,
            'direction': direction,
            'close': close,
            'entry_low': entry_low,
            'entry_high': entry_high,
            'sl': sl,
            'tp': tp,
            'leverage': suggest_lev,
            'lev_mode': lev_mode,
            'risk_amount': risk_amount,  # Risk amount yang benar (1% dari balance)
            'sl_percent': sl_percent_display,  # SL percentage untuk display
            'rr_ratio': rr_ratio,
            'pos_size': pos_size,
            'position_value_usd': position_value_usd,
            # Detailed technical indicators for analysis (SESUAI STRATEGY)
            'ema_fast_above_slow': ema_fast > ema_slow,
            'macd_bullish': macd_line > signal_line,
            'rsi_oversold': rsi < 35,  # Sesuai strategy (bukan 30)
            'rsi_overbought': rsi > 65,  # Sesuai strategy (bukan 70)
            'rsi_neutral': 35 <= rsi <= 65,  # Sesuai strategy (bukan 30-70)
            'volume_confirmation': volume_ok,  # Actual volume check
            'volatility_confirmation': volatility_ok,  # Actual volatility check
            'price_near_support': direction == "LONG" and support and abs(close - support) / support < 0.02,
            'price_near_resistance': direction == "SHORT" and resistance and abs(close - resistance) / resistance < 0.02,
            'trend_alignment': (direction == "LONG" and ema_bullish) or (direction == "SHORT" and ema_bearish),
            'momentum_confirmation': (direction == "LONG" and macd_bullish) or (direction == "SHORT" and macd_bearish),
            # Numerical values
            'rsi_level': rsi,
            'atr_value': atr,
            'ema_fast_value': ema_fast,
            'ema_slow_value': ema_slow,
            'macd_line_value': macd_line,
            'signal_line_value': signal_line,
            'support_resistance': support if direction == "LONG" else resistance,
            'price_distance_from_level': abs(close - (support if direction == "LONG" else resistance)) / close * 100 if (support if direction == "LONG" else resistance) else 0
        }
    except Exception as e:
        return None

# ==================
# TELEGRAM NOTIFICATION
# ==================
async def send_telegram_alert(signal, trade_executed=True):
    """Kirim alert ke Telegram HANYA untuk trade yang berhasil dieksekusi"""
    if not trade_executed:
        print(f"⚠️ Skipping Telegram alert for {signal['symbol']} - Trade not executed")
        return False
        
    emoji = "📈" if signal['direction'] == "LONG" else "📉"
    
    # Message for EXECUTED trades only
    message = f"""
{emoji} <b>{signal['direction']} TRADE EXECUTED - {signal['symbol']}</b>
🚀 POSITION OPENED

💰 <b>Entry Price:</b> ${signal['close']:.6f}
🎯 <b>Entry Zone:</b> ${signal['entry_low']:.6f} - ${signal['entry_high']:.6f}
🛑 <b>Stop Loss:</b> ${signal['sl']:.6f}
✅ <b>Take Profit:</b> ${signal['tp']:.6f}

⚡ <b>Leverage:</b> {signal['leverage']}x ({signal['lev_mode']})
💵 <b>Risk Amount:</b> ${signal['risk_amount']:.2f}
📊 <b>Position Size:</b> {signal['pos_size']:.3f} coins
💎 <b>Position Value:</b> ${signal['position_value_usd']:.2f} USDT
📉 <b>SL %:</b> {signal['sl_percent']:.2f}%
🎲 <b>R:R:</b> 1:{signal['rr_ratio']:.2f}
"""

    # Add AI reasoning if available
    if signal.get('ai_entry_reasoning') and signal['ai_entry_reasoning'].strip():
        # Clean HTML tags for Telegram using improved function
        clean_reasoning = clean_html_for_telegram(signal['ai_entry_reasoning'])
        
        # Limit length for Telegram
        if len(clean_reasoning) > 1500:
            clean_reasoning = clean_reasoning[:1500] + "...\n\n[Analisis dipotong karena panjang pesan]"
        
        message += f"""

🤖 <b>AI ANALYSIS:</b>
{clean_reasoning}
"""

    # Add timestamp and branding
    message += f"""

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🚀 <i>Powered by LevaTrade</i>
"""
    
    try:
        # Create bot instance inside async context
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='HTML'
        )
        print(f"✅ Telegram alert sent for {signal['symbol']}")
        return True
    except TelegramError as e:
        print(f"❌ Telegram error for {signal['symbol']}: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error sending alert for {signal['symbol']}: {e}")
        return False

async def send_ai_entry_reasoning_telegram(symbol, direction, ai_reasoning):
    """Kirim AI Entry Reasoning ke Telegram"""
    try:
        emoji = "🤖" 
        direction_emoji = "📈" if direction == "LONG" else "📉"
        
        # Clean HTML tags for Telegram using improved function
        clean_reasoning = clean_html_for_telegram(ai_reasoning)
        
        # Limit message length (Telegram has 4096 char limit)
        if len(clean_reasoning) > 3000:
            clean_reasoning = clean_reasoning[:3000] + "...\n\n[Analisis dipotong karena panjang pesan]"
        
        message = f"""
{emoji} <b>AI ENTRY ANALYSIS</b>
{direction_emoji} <b>{symbol} {direction}</b>

{clean_reasoning}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🚀 <i>Powered by LevaTrade</i>
"""
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='HTML'
        )
        print(f"✅ AI Entry Reasoning sent to Telegram for {symbol}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending AI Entry Reasoning to Telegram: {e}")
        return False

async def send_ai_exit_reasoning_telegram(symbol, direction, exit_reason, pnl, ai_reasoning, entry_price=None, exit_price=None, duration_minutes=None):
    """Kirim AI Exit Reasoning ke Telegram dengan informasi trading lengkap"""
    try:
        emoji = "🤖"
        pnl_emoji = "💰" if pnl >= 0 else "💸"
        direction_emoji = "📈" if direction == "LONG" else "📉"
        
        # Status berdasarkan exit reason
        if exit_reason == "TP_HIT":
            status_emoji = "🎯✅"
            status_text = "TAKE PROFIT HIT"
        elif exit_reason == "SL_HIT":
            status_emoji = "🛑❌"
            status_text = "STOP LOSS HIT"
        else:
            status_emoji = "🚪"
            status_text = exit_reason
        
        # Format duration
        duration_str = "N/A"
        if duration_minutes is not None:
            hours = duration_minutes // 60
            minutes = duration_minutes % 60
            duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        # Build message with trading details
        entry_price_str = f"${entry_price:.6f}" if entry_price is not None else "$0.000000"
        exit_price_str = f"${exit_price:.6f}" if exit_price is not None else "$0.000000"
        
        message = f"""
{emoji} <b>AI EXIT ANALYSIS</b>
{status_emoji} <b>{status_text}</b>
{direction_emoji} <b>{symbol} {direction}</b>

💰 <b>Entry Price:</b> {entry_price_str}
🎯 <b>Exit Price:</b> {exit_price_str}
{pnl_emoji} <b>PnL:</b> ${pnl:.2f}
⏱️ <b>Duration:</b> {duration_str}
"""

        # Add AI reasoning if available
        if ai_reasoning and ai_reasoning.strip():
            try:
                # Clean HTML tags for Telegram using improved function
                clean_reasoning = clean_html_for_telegram(ai_reasoning)
                
                # Limit message length
                if len(clean_reasoning) > 2000:
                    clean_reasoning = clean_reasoning[:2000] + "...\n\n[Analisis dipotong karena panjang pesan]"
                
                message += f"""

🧠 <b>AI REASONING:</b>
{clean_reasoning}
"""
            except Exception as clean_error:
                print(f"❌ Error cleaning AI reasoning HTML: {clean_error}")
                # Fallback: strip all HTML tags
                clean_reasoning = re.sub(r'<[^>]+>', '', ai_reasoning)
                if len(clean_reasoning) > 2000:
                    clean_reasoning = clean_reasoning[:2000] + "...\n\n[Analisis dipotong karena panjang pesan]"
                
                message += f"""

🧠 <b>AI REASONING:</b>
{clean_reasoning}
"""

        # Add timestamp and branding
        message += f"""

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🚀 <i>Powered by LevaTrade</i>
"""
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Try sending with HTML parsing first
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
            print(f"✅ AI Exit Reasoning sent to Telegram for {symbol}")
            return True
            
        except Exception as html_error:
            print(f"❌ HTML parsing error: {html_error}")
            print(f"🔍 Problematic message length: {len(message)} chars")
            
            # Fallback: Send without HTML parsing
            try:
                # Strip all HTML tags for plain text
                plain_message = re.sub(r'<[^>]+>', '', message)
                await bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=plain_message,
                    parse_mode=None
                )
                print(f"✅ AI Exit Reasoning sent to Telegram (plain text) for {symbol}")
                return True
                
            except Exception as plain_error:
                print(f"❌ Failed to send even plain text: {plain_error}")
                return False
        
    except Exception as e:
        print(f"❌ General error sending AI Exit Reasoning to Telegram: {e}")
        return False

# ==================
# PARALLEL SCANNING
# ==================
def scan_symbols_parallel(symbols):
    """Scan multiple symbols in parallel"""
    signals = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(analyze_symbol, symbols))
    
    # Filter out None results
    signals = [r for r in results if r is not None]
    
    return signals

async def monitor_early_exits():
    """Monitor open positions for early exit conditions"""
    if not AUTO_TRADE_ENABLED or DRY_RUN:
        return  # Only for real trading
    
    try:
        current_positions = get_open_positions()
        if not current_positions:
            return
        
        print(f"🔍 Monitoring {len(current_positions)} positions for early exits...")
        
        for symbol, position in current_positions.items():
            # Get current market data for the symbol
            df = get_klines(symbol, TIMEFRAME, 50)  # Get recent data for indicators
            if df is None or len(df) < 20:
                continue
            
            # Calculate current indicators
            df['ema_fast'] = calculate_ema(df['close'], EMA_FAST)
            df['ema_slow'] = calculate_ema(df['close'], EMA_SLOW)
            df['macd_line'], df['signal_line'] = calculate_macd(df['close'], 5, 13, 4)
            
            current_price = df.iloc[-1]['close']
            current_indicators = {
                'current_price': current_price,
                'ema_fast': df.iloc[-1]['ema_fast'],
                'ema_slow': df.iloc[-1]['ema_slow'],
                'macd_line': df.iloc[-1]['macd_line'],
                'signal_line': df.iloc[-1]['signal_line']
            }
            
            # Convert position format for early exit system
            position_data = {
                'symbol': symbol,
                'direction': position['side'].upper(),  # Buy -> LONG, Sell -> SHORT
                'entry_price': position['entry_price'],
                'entry_time': datetime.now().isoformat(),  # Approximate, would need to track actual entry time
                'atr_value': open_positions.get(symbol, {}).get('atr_value', 0.01)  # Use stored ATR or fallback
            }
            
            # Check for early exit conditions
            exit_actions = early_exit_system.check_early_exit(position_data, current_price, current_indicators)
            
            if exit_actions:
                for action in exit_actions:
                    print(f"🚪 Early exit action for {symbol}: {action['reason']}")
                    
                    # Send notification
                    await early_exit_system.send_early_exit_notification(position_data, action)
                    
                    # Execute the exit action (simplified for now)
                    if action['type'] == 'partial_tp':
                        print(f"   📈 Would close {action['percentage']}% of {symbol} position")
                        # TODO: Implement partial position closing
                    elif action['type'] == 'full_exit':
                        print(f"   🚪 Would close full {symbol} position")
                        # TODO: Implement full position closing
                    elif action['type'] == 'update_sl':
                        print(f"   🔄 Would update SL for {symbol} to ${action['new_sl']:.4f}")
                        # TODO: Implement SL update
    
    except Exception as e:
        print(f"❌ Error in early exit monitoring: {e}")
        await error_notifier.notify_trading_error(
            "early_exit_error",
            "SYSTEM",
            {'error_message': str(e)},
            e
        )
sent_alerts = {}  # Track alerts yang sudah dikirim

async def main():
    """Main loop untuk monitoring"""
    print("🚀 Bot started (Aggressive Scalping Mode - 15M)...")
    print(f"⚡ Max Workers: {MAX_WORKERS} threads")
    print(f"⏰ Timeframe: {TIMEFRAME}m (15M)")
    print(f"🔄 Scan Interval: {SCAN_INTERVAL//60} minutes {SCAN_INTERVAL%60} seconds")
    print(f"📊 Mode: {'ALL USDT PAIRS' if SCAN_ALL_USDT else f'TOP {TOP_VOLUME_COUNT} VOLUME'}")
    print(f"📈 Indicators: EMA {EMA_FAST}/{EMA_SLOW}, RSI {RSI_LENGTH}, MACD 5/13/4")
    print(f"🎯 TP/SL: {TP_ATR_MULT}x/{SL_ATR_MULT}x ATR (SCALPING), Max Risk: {MAX_RISK}%, Max Lev: {MAX_LEVERAGE}x")
    
    # Auto Trading Status
    if AUTO_TRADE_ENABLED:
        mode_text = "DRY RUN (Simulation)" if DRY_RUN else "LIVE TRADING"
        print(f"🤖 Auto Trading: ENABLED ({mode_text})")
        print(f"📊 Max Positions: {MAX_OPEN_POSITIONS}, Min Size: ${MIN_POSITION_SIZE_USD}")
        
        # Check balance if live trading
        balance = 0
        if not DRY_RUN:
            balance = get_account_balance()
            print(f"💰 Account Balance: ${balance:.2f} USDT")
    else:
        print(f"🤖 Auto Trading: DISABLED (Alerts Only)")
        balance = 0
    
    print("-" * 50)
    
    # Send bot started notification
    await error_notifier.notify_system_status("bot_started", {
        'mode': "DRY RUN" if DRY_RUN else "LIVE TRADING",
        'symbol_count': TOP_VOLUME_COUNT,
        'timeframe': f"{TIMEFRAME}m",
        'scan_interval': f"{SCAN_INTERVAL//60}m {SCAN_INTERVAL%60}s",
        'balance': balance
    })
    
    # Get top volume symbols
    print("\n📊 Loading top volume symbols...")
    symbols = get_top_volume_symbols(TOP_VOLUME_COUNT)
    
    if not symbols:
        print("❌ Failed to load symbols")
        await error_notifier.notify_system_status("bot_stopped", {
            'reason': 'Failed to load symbols',
            'runtime': '0s',
            'total_trades': 0,
            'final_pnl': 0
        })
        return
    
    print(f"✅ Loaded {len(symbols)} symbols")
    print("-" * 50)
    
    scan_count = 0
    start_time = datetime.now()
    
    try:
        while True:
            try:
                # HARD STOP CHECK: Check setiap loop
                can_trade, reason = hard_stop_system.can_trade()
                if not can_trade:
                    print(f"🚨🛑 HARD STOP TRIGGERED: {reason}")
                    print(f"🔴 BOT STOPPED - Manual restart required!")
                    # Send emergency notification
                    await error_notifier.notify_trading_error(
                        "hard_stop_triggered",
                        "EMERGENCY",
                        hard_stop_system.get_status()
                    )
                    # Exit the entire program
                    import sys
                    sys.exit(1)
                
                scan_count += 1
                start_time = time.time()
                
                print(f"\n🔍 Scan #{scan_count} started at {datetime.now().strftime('%H:%M:%S')}")
                print(f"📊 Scanning {len(symbols)} symbols in parallel...")
                
                # Scan all symbols in parallel
                signals = scan_symbols_parallel(symbols)
                
                # Update dry run positions with current prices (jika DRY_RUN aktif)
                # Hanya update setiap 30 detik untuk posisi yang open
                if DRY_RUN:
                    # Check if it's time to update positions (every 30 seconds)
                    current_time = time.time()
                    if not hasattr(main, 'last_position_update'):
                        main.last_position_update = 0
                    
                    if current_time - main.last_position_update >= 30:  # 30 seconds
                        # Collect current prices for open positions
                        open_positions_symbols = [pos['symbol'] for pos in dry_run_system.get_open_positions()]
                        if open_positions_symbols:
                            current_prices = {}
                            print(f"📊 Updating prices for {len(open_positions_symbols)} open positions...")
                            
                            for symbol in open_positions_symbols:
                                df = get_klines(symbol, TIMEFRAME, 1)
                                if df is not None and len(df) > 0:
                                    current_prices[symbol] = df.iloc[-1]['close']
                            
                            if current_prices:
                                await dry_run_system.update_positions(current_prices)
                                
                                # Debug: Show updated positions with percentage PnL berdasarkan margin
                                positions = dry_run_system.get_open_positions()
                                for pos in positions:
                                    # Calculate margin used for PnL percentage (consistent with dashboard)
                                    leverage = pos.get('leverage', 1) or 1  # Handle None leverage
                                    position_value_usd = pos.get('position_value_usd', 0) or 0  # Handle None position_value_usd
                                    unrealized_pnl = pos.get('unrealized_pnl', 0) or 0  # Handle None unrealized_pnl
                                    
                                    margin_used = position_value_usd / leverage if leverage > 0 else position_value_usd
                                    pnl_pct = (unrealized_pnl / margin_used) * 100 if margin_used > 0 else 0
                                    pnl_color = "🟢" if unrealized_pnl >= 0 else "🔴"
                                    
                                    current_price = pos.get('current_price', pos.get('entry_price', 0))
                                    print(f"   {pnl_color} {pos['symbol']}: {pos['direction']} {pos['quantity']:.3f} @ ${pos['entry_price']:.4f} | Current: ${current_price:.4f} | PnL: ${unrealized_pnl:.2f} ({pnl_pct:+.2f}%)")
                            
                            main.last_position_update = current_time
                        else:
                            print("📊 No open positions to update")
                            main.last_position_update = current_time
                
                elapsed = time.time() - start_time
                print(f"⏱️  Scan completed in {elapsed:.2f}s")
                print(f"📈 Found {len(signals)} signals")
                
                # Monitor open positions for early exits
                if AUTO_TRADE_ENABLED and not DRY_RUN:
                    await monitor_early_exits()
                
                # Send alerts and execute trades for new signals
                if signals:
                    print(f"\n📨 Processing {len(signals)} signal(s)...")
                    for signal in signals:
                        alert_key = f"{signal['symbol']}_{signal['direction']}"
                        current_time_key = int(time.time() / (int(TIMEFRAME) * 60))
                        
                        if alert_key not in sent_alerts or sent_alerts[alert_key] != current_time_key:
                            print(f"   📤 Processing signal for {signal['symbol']} {signal['direction']}...")
                            
                            # Execute trade if auto trading enabled
                            trade_executed = False
                            if AUTO_TRADE_ENABLED:
                                print(f"   🚀 Attempting to execute trade for {signal['symbol']}...")
                                trade_executed = await execute_trade(signal)
                            
                            # ONLY send Telegram alert if trade was actually executed
                            if trade_executed:
                                print(f"   📱 Sending Telegram alert for EXECUTED trade: {signal['symbol']}")
                                success = await send_telegram_alert(signal, trade_executed=True)
                                if success:
                                    sent_alerts[alert_key] = current_time_key
                            else:
                                print(f"   ❌ Trade NOT executed for {signal['symbol']} - No Telegram alert sent")
                            
                            await asyncio.sleep(1)  # Delay antar alert
                        else:
                            print(f"   ⏭️  Skipping {signal['symbol']} (already sent this period)")
                else:
                    print("   ℹ️  No signals found in this scan")
                
                # Monitor open positions
                if AUTO_TRADE_ENABLED:
                    if DRY_RUN:
                        # Show dry run positions dengan persentase PnL berdasarkan margin
                        current_positions = dry_run_system.get_open_positions()
                        if current_positions:
                            print(f"\n📊 Open Positions (DRY RUN): {len(current_positions)}")
                            for pos in current_positions:
                                # Calculate margin used for PnL percentage (consistent with dashboard)
                                leverage = pos.get('leverage', 1) or 1  # Handle None leverage
                                position_value_usd = pos.get('position_value_usd', 0) or 0  # Handle None position_value_usd
                                unrealized_pnl = pos.get('unrealized_pnl', 0) or 0  # Handle None unrealized_pnl
                                
                                margin_used = position_value_usd / leverage if leverage > 0 else position_value_usd
                                pnl_pct = (unrealized_pnl / margin_used) * 100 if margin_used > 0 else 0
                                pnl_emoji = "🟢" if unrealized_pnl >= 0 else "🔴"
                                
                                entry_price = pos.get('entry_price', 0)
                                print(f"   {pnl_emoji} {pos['symbol']}: {pos['direction']} {pos['quantity']:.3f} @ ${entry_price:.4f} | PnL: ${unrealized_pnl:.2f} ({pnl_pct:+.2f}%)")
                    else:
                        # Show real positions dengan persentase PnL berdasarkan margin
                        current_positions = get_open_positions()
                        if current_positions:
                            print(f"\n📊 Open Positions: {len(current_positions)}")
                            for symbol, pos in current_positions.items():
                                # Calculate margin used for PnL percentage (consistent with dashboard)
                                entry_price = pos.get('entry_price', 0) or 0
                                size = pos.get('size', 0) or 0
                                leverage = float(pos.get('leverage', 1) or 1)
                                unrealized_pnl = pos.get('unrealized_pnl', 0) or 0
                                
                                position_value = entry_price * size
                                margin_used = position_value / leverage if leverage > 0 else position_value
                                pnl_pct = (unrealized_pnl / margin_used) * 100 if margin_used > 0 else 0
                                pnl_emoji = "🟢" if unrealized_pnl >= 0 else "🔴"
                                
                                side = pos.get('side', 'UNKNOWN')
                                print(f"   {pnl_emoji} {symbol}: {side} {size} @ {entry_price:.4f} | PnL: ${unrealized_pnl:.2f} ({pnl_pct:+.2f}%)")
                
                # Refresh symbols list setiap 10 scan
                if scan_count % 10 == 0:
                    print("\n🔄 Refreshing top volume symbols...")
                    new_symbols = get_top_volume_symbols(TOP_VOLUME_COUNT)
                    if new_symbols:
                        symbols = new_symbols
                        print(f"✅ Symbols refreshed")
                
                # Wait with dual interval system
                wait_minutes = SCAN_INTERVAL // 60
                print(f"\n💤 Next signal scan in {wait_minutes} minutes, position updates every {POSITION_UPDATE_INTERVAL}s...")
                print("-" * 50)
                
                # Sleep in 30-second intervals to allow position updates
                for i in range(0, SCAN_INTERVAL, POSITION_UPDATE_INTERVAL):
                    await asyncio.sleep(POSITION_UPDATE_INTERVAL)
                    
                    # Position update every 30 seconds during wait
                    if i > 0:  # Skip first iteration (i=0)
                        print(f"\n📊 Position Update (during wait) at {datetime.now().strftime('%H:%M:%S')}")
                        
                        try:
                            # Update positions for dry run
                            if DRY_RUN:
                                open_positions_symbols = [pos['symbol'] for pos in dry_run_system.get_open_positions()]
                                if open_positions_symbols:
                                    current_prices = {}
                                    for symbol in open_positions_symbols:
                                        df = get_klines(symbol, TIMEFRAME, 1)
                                        if df is not None and len(df) > 0:
                                            current_prices[symbol] = df.iloc[-1]['close']
                                    
                                    if current_prices:
                                        await dry_run_system.update_positions(current_prices)
                                        print(f"   ✅ Updated {len(current_prices)} positions")
                            
                            # Early exit monitoring for real trading
                            if AUTO_TRADE_ENABLED and not DRY_RUN:
                                await monitor_early_exits()
                                
                        except Exception as e:
                            print(f"   ❌ Error in position update: {e}")
                            await error_notifier.notify_trading_error(
                                "position_update_error",
                                "POSITION_UPDATE",
                                {'error_message': str(e)},
                                e
                            )
                
            except KeyboardInterrupt:
                print("\n👋 Bot stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                await error_notifier.notify_trading_error(
                    "system_error",
                    "MAIN_LOOP",
                    {'error_message': str(e)},
                    e
                )
                await asyncio.sleep(60)
    
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        await error_notifier.notify_trading_error(
            "fatal_error",
            "MAIN_FUNCTION",
            {'error_message': str(e)},
            e
        )
    
    # Send bot stopped notification
    runtime = datetime.now() - start_time
    runtime_str = f"{runtime.total_seconds()//3600:.0f}h {(runtime.total_seconds()%3600)//60:.0f}m"
    
    # Get final stats
    total_trades = 0
    final_pnl = 0
    if DRY_RUN:
        trades = dry_run_system.get_trade_history(1000)  # Get all trades
        total_trades = len(trades)
        final_pnl = sum(trade.get('pnl', 0) for trade in trades)
    
    await error_notifier.notify_system_status("bot_stopped", {
        'reason': 'Manual stop or error',
        'runtime': runtime_str,
        'total_trades': total_trades,
        'final_pnl': final_pnl
    })

if __name__ == "__main__":
    asyncio.run(main())
