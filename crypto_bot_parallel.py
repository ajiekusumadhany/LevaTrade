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
from trading_control_system import is_trading_enabled
from session_management_system import get_current_session_parameters, get_session_status
from time_based_stop_system import register_position_entry, check_time_based_exits, remove_position_tracking

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
BALANCE = float(os.getenv('BALANCE_USD', '1000000'))
MIN_LEVERAGE = int(os.getenv('MIN_LEVERAGE', '5'))
MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '20'))

# Session-based parameters will override these static settings
MAX_RISK = 0.5  # Default, akan di-override oleh session parameters
MAX_OPEN_POSITIONS = 20  # Default, akan di-override oleh session parameters

# Scan Parameters
SCAN_ALL_USDT = False  # Kembali ke top volume untuk menghindari rate limit
TOP_VOLUME_COUNT = 100  # Top 100 pairs untuk balance antara coverage dan rate limit

# 🎯 MULTI-TIMEFRAME SCALPING SETUP (OPTIMAL)
BIAS_TF = '15'      # 15m = Market bias & struktur (otak)
ENTRY_TF = '5'      # 5m = Entry signal presisi (tangan)
TRIGGER_TF = '1'    # 1m = Fine entry timing (pisau bedah - opsional)
ATR_TF = '15'       # 15m = ATR stabil untuk risk calc

# Auto Trading Settings
AUTO_TRADE_ENABLED = True   # Enable/disable auto trading
DRY_RUN = True             # True = simulasi saja, False = trading nyata
MIN_POSITION_SIZE_USD = 2  # Minimal ukuran posisi dalam USD (turun untuk balance $200)

# Scan Interval (scalping agresif dengan multi-TF)
SCAN_INTERVAL = 120   # 2 menit untuk scan sinyal baru (lebih cepat untuk scalping)
POSITION_UPDATE_INTERVAL = 3  # 3 detik untuk update posisi (lebih ketat untuk scalping)

# Indicator Parameters (multi-timeframe scalping)
# 15M BIAS INDICATORS (Struktur & Trend)
EMA_FAST_BIAS = 8   # EMA cepat untuk bias 15m
EMA_SLOW_BIAS = 21  # EMA lambat untuk bias 15m
RSI_BIAS = 14       # RSI untuk bias 15m

# 5M ENTRY INDICATORS (Presisi Entry)
EMA_FAST_ENTRY = 5   # EMA cepat untuk entry 5m
EMA_SLOW_ENTRY = 13  # EMA lambat untuk entry 5m
RSI_ENTRY = 9        # RSI sensitif untuk entry 5m

# 1M TRIGGER INDICATORS (Fine Timing - Opsional)
EMA_TRIGGER = 3      # EMA sangat cepat untuk trigger 1m
RSI_TRIGGER = 7      # RSI sangat sensitif untuk trigger 1m

# RISK MANAGEMENT (15M ATR - STABIL)
TP_ATR_MULT = 1.5    # TP multiplier (lebih konservatif untuk scalping)
SL_ATR_MULT = 0.8    # SL multiplier (tight tapi aman)
PIVOT_LENGTH = 3     # Pivot untuk S/R detection

# SESSION-SPECIFIC TIMEFRAME USAGE
SESSION_TF_CONFIG = {
    'DEAD_ZONE': {
        'bias_tf': '15',
        'entry_tf': '5',
        'use_trigger': False,  # NO 1m - likuiditas tipis
        'atr_tf': '15'
    },
    'ASIA': {
        'bias_tf': '15', 
        'entry_tf': '5',
        'use_trigger': False,  # 5m paling stabil untuk mean reversion
        'atr_tf': '15'
    },
    'LONDON': {
        'bias_tf': '15',
        'entry_tf': '5', 
        'use_trigger': True,   # 1m untuk pullback breakout
        'atr_tf': '15'
    },
    'NEWYORK': {
        'bias_tf': '15',
        'entry_tf': '3',       # 3m lebih aman dari 1m untuk momentum
        'use_trigger': True,   # 1m setelah momentum confirm
        'atr_tf': '15'
    }
}

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
        
        # TRADING CONTROL CHECK - Must be first check
        if not is_trading_enabled():
            print(f"🛑 TRADING STOPPED: {symbol} {direction} signal ignored - Trading is currently disabled")
            return False
        
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
        
        # Get max margin usage from environment
        max_margin_usage = float(os.getenv('MAX_MARGIN_USAGE_PERCENT', 65))
        
        # HARD BLOCK: No new positions if margin usage exceeds limit
        if current_margin_usage > max_margin_usage:
            print(f"🚨🛑 MARGIN SAFETY BLOCK: Current usage {current_margin_usage:.1f}% > {max_margin_usage}%")
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
        
        if margin_usage_after > max_margin_usage:
            print(f"🚨🛑 MARGIN SAFETY BLOCK: Adding {symbol} would cause {margin_usage_after:.1f}% usage (>{max_margin_usage}%)")
            print(f"🚨🛑 Current: ${total_existing_margin:.2f} + Required: ${required_margin:.2f} = ${total_margin_after:.2f}")
            print(f"🚨🛑 {symbol} TRADE REJECTED - WOULD EXCEED MARGIN LIMIT")
            return False

        # HARD STOP: Check drawdown 20% - SATU-SATUNYA LIMIT YANG BERLAKU
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
        
        # SEMUA LIMIT LAINNYA DIHAPUS - Tidak ada progressive risk check
        # SEMUA LIMIT LAINNYA DIHAPUS - Tidak ada max positions limit
        # SEMUA LIMIT LAINNYA DIHAPUS - Tidak ada consecutive loss limit
        # SEMUA LIMIT LAINNYA DIHAPUS - Tidak ada daily loss limit
        
        leverage = signal['leverage']
        qty = signal['pos_size']
        tp_price = signal['tp']
        sl_price = signal['sl']
        
        # Check if already have position for this symbol
        current_positions = dry_run_system.get_open_positions()
        if any(pos['symbol'] == symbol for pos in current_positions):
            print(f"⚠️  Already have position for {symbol}, skipping...")
            return False
        
        # SEMUA LIMIT DIHAPUS - Tidak ada max positions limit
        # SEMUA LIMIT DIHAPUS - Tidak ada session limit
        # SEMUA LIMIT DIHAPUS - Trading akan terus berjalan sampai drawdown 20%
        
        print(f"🚀 NO LIMITS MODE: {symbol} {direction} - All session limits removed")
        print(f"🚀 Only 20% drawdown stop applies - Trading continues unlimited")
        
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
            
            # Register position for time-based stop tracking
            current_time = datetime.now()
            current_balance = dry_run_system.get_current_balance()
            session_params = get_current_session_parameters(current_balance, {}, {})
            current_session = session_params['session']
            register_position_entry(symbol, current_time, current_session)
            
            # Record the trade opening for conditional risk system
            from conditional_risk_system import record_trade_result
            # Note: We'll record the result when position closes, not opens
            
            print(f"🚀 [DRY RUN] Trade executed for {symbol}: {direction} {qty} @ {leverage}x")
            return True
        else:
            # Real trading logic with comprehensive error handling
            
            # Get session parameters for real trading
            session_params = get_current_session_parameters(current_balance, {}, {})
            session_max_leverage = session_params['max_leverage']
            
            # 1. Check account balance first
            current_balance = get_account_balance()
            required_margin = position_value_usd / leverage
            
            if current_balance < required_margin:
                print(f"❌ Insufficient balance for {symbol}: Required ${required_margin:.2f}, Available ${current_balance:.2f}")
                await notify_insufficient_balance(symbol, required_margin, current_balance, qty, leverage)
                return False
            
            # 2. Set leverage with error handling (use session-based max leverage)
            try:
                if not set_leverage(symbol, leverage):
                    print(f"❌ Failed to set leverage for {symbol}")
                    await error_notifier.notify_trading_error(
                        "leverage_error",
                        symbol,
                        {
                            'requested_leverage': leverage,
                            'max_leverage': session_max_leverage,
                            'session': session_params['session'],
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
                        'max_leverage': session_max_leverage,
                        'session': session_params['session'],
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
                    
                    # Register position for time-based stop tracking
                    current_balance = get_account_balance()
                    session_params = get_current_session_parameters(current_balance, {}, {})
                    current_session = session_params['session']
                    register_position_entry(symbol, datetime.now(), current_session)
                    
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
# ==================
# MULTI-TIMEFRAME DATA FUNCTIONS
# ==================
def get_multi_timeframe_data(symbol, session_config):
    """Ambil data multi-timeframe sesuai session config"""
    try:
        data = {}
        
        # 1. BIAS TIMEFRAME (15m) - Market Structure & Trend
        bias_tf = session_config['bias_tf']
        bias_data = get_klines(symbol, bias_tf, 100)
        if bias_data is None or len(bias_data) < 50:
            return None
        data['bias'] = bias_data
        
        # 2. ENTRY TIMEFRAME (5m/3m) - Entry Signals
        entry_tf = session_config['entry_tf']
        entry_data = get_klines(symbol, entry_tf, 100)
        if entry_data is None or len(entry_data) < 50:
            return None
        data['entry'] = entry_data
        
        # 3. TRIGGER TIMEFRAME (1m) - Fine Timing (Opsional)
        if session_config['use_trigger']:
            trigger_data = get_klines(symbol, '1', 50)
            if trigger_data is not None and len(trigger_data) >= 20:
                data['trigger'] = trigger_data
            else:
                data['trigger'] = None
        else:
            data['trigger'] = None
        
        # 4. ATR TIMEFRAME (15m) - Risk Calculation
        atr_tf = session_config['atr_tf']
        if atr_tf != bias_tf:
            atr_data = get_klines(symbol, atr_tf, 50)
            data['atr'] = atr_data if atr_data is not None else bias_data
        else:
            data['atr'] = bias_data
        
        return data
        
    except Exception as e:
        print(f"❌ Error getting multi-timeframe data for {symbol}: {e}")
        return None

def calculate_multi_tf_indicators(tf_data):
    """Calculate indicators untuk setiap timeframe"""
    try:
        indicators = {}
        
        # BIAS INDICATORS (15m) - Market Structure
        bias_df = tf_data['bias'].copy()
        bias_df['ema_fast'] = calculate_ema(bias_df['close'], EMA_FAST_BIAS)
        bias_df['ema_slow'] = calculate_ema(bias_df['close'], EMA_SLOW_BIAS)
        bias_df['rsi'] = calculate_rsi(bias_df['close'], RSI_BIAS)
        bias_df['macd_line'], bias_df['signal_line'] = calculate_macd(bias_df['close'], 12, 26, 9)
        
        indicators['bias'] = {
            'ema_fast': bias_df.iloc[-1]['ema_fast'],
            'ema_slow': bias_df.iloc[-1]['ema_slow'],
            'rsi': bias_df.iloc[-1]['rsi'],
            'macd_line': bias_df.iloc[-1]['macd_line'],
            'signal_line': bias_df.iloc[-1]['signal_line'],
            'close': bias_df.iloc[-1]['close'],
            'trend_bullish': bias_df.iloc[-1]['ema_fast'] > bias_df.iloc[-1]['ema_slow'],
            'macd_bullish': bias_df.iloc[-1]['macd_line'] > bias_df.iloc[-1]['signal_line']
        }
        
        # ENTRY INDICATORS (5m/3m) - Entry Signals
        entry_df = tf_data['entry'].copy()
        entry_df['ema_fast'] = calculate_ema(entry_df['close'], EMA_FAST_ENTRY)
        entry_df['ema_slow'] = calculate_ema(entry_df['close'], EMA_SLOW_ENTRY)
        entry_df['rsi'] = calculate_rsi(entry_df['close'], RSI_ENTRY)
        entry_df['macd_line'], entry_df['signal_line'] = calculate_macd(entry_df['close'], 5, 13, 4)
        
        indicators['entry'] = {
            'ema_fast': entry_df.iloc[-1]['ema_fast'],
            'ema_slow': entry_df.iloc[-1]['ema_slow'],
            'rsi': entry_df.iloc[-1]['rsi'],
            'macd_line': entry_df.iloc[-1]['macd_line'],
            'signal_line': entry_df.iloc[-1]['signal_line'],
            'close': entry_df.iloc[-1]['close'],
            'trend_bullish': entry_df.iloc[-1]['ema_fast'] > entry_df.iloc[-1]['ema_slow'],
            'macd_bullish': entry_df.iloc[-1]['macd_line'] > entry_df.iloc[-1]['signal_line'],
            'volume': entry_df.iloc[-1]['volume'],
            'volume_avg': entry_df['volume'].rolling(20).mean().iloc[-1]
        }
        
        # TRIGGER INDICATORS (1m) - Fine Timing
        if tf_data['trigger'] is not None:
            trigger_df = tf_data['trigger'].copy()
            trigger_df['ema'] = calculate_ema(trigger_df['close'], EMA_TRIGGER)
            trigger_df['rsi'] = calculate_rsi(trigger_df['close'], RSI_TRIGGER)
            
            indicators['trigger'] = {
                'ema': trigger_df.iloc[-1]['ema'],
                'rsi': trigger_df.iloc[-1]['rsi'],
                'close': trigger_df.iloc[-1]['close'],
                'above_ema': trigger_df.iloc[-1]['close'] > trigger_df.iloc[-1]['ema'],
                'momentum_up': trigger_df.iloc[-1]['close'] > trigger_df.iloc[-2]['close']
            }
        else:
            indicators['trigger'] = None
        
        # ATR CALCULATION (15m) - Risk Management
        atr_df = tf_data['atr'].copy()
        atr_df['atr'] = calculate_atr(atr_df, 14)
        indicators['atr_value'] = atr_df.iloc[-1]['atr']
        
        return indicators
        
    except Exception as e:
        print(f"❌ Error calculating multi-TF indicators: {e}")
        return None
def get_klines(symbol, interval='15', limit=200):
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
# ANALISIS MARKET - SESSION-BASED STRATEGY
# ==================
# ==================
# ANALISIS MARKET - MULTI-TIMEFRAME SCALPING
# ==================
def analyze_symbol(symbol):
    """Analisis satu symbol dengan multi-timeframe scalping approach"""
    try:
        # EARLY EXIT: Skip jika sudah ada posisi untuk symbol ini
        current_positions = dry_run_system.get_open_positions()
        if any(pos['symbol'] == symbol for pos in current_positions):
            return None  # Skip analysis untuk symbol yang sudah ada posisinya
        
        # Get current session parameters
        if DRY_RUN:
            current_balance = dry_run_system.get_current_balance()
        else:
            current_balance = get_account_balance()
        
        # Prepare market data for conditional risk evaluation
        market_data = {
            'volatility_score': 0.5,  # Default, would need real calculation
            'spread_percent': 0.05,  # Assume normal spread
            'market_cap': 1000000000,  # Default $1B
            'total_volume_24h': 100000000  # Default $100M
        }
        
        # Prepare indicators for conditional risk evaluation
        indicators_data = {
            'volume_confirmation': True,
            'breakout_strength': 0.7,
            'momentum_strength': 0.8,
            'atr_ratio': 1.0,
            'trend_strength': 0.7
        }
        
        # Get session parameters with conditional risk
        session_params = get_current_session_parameters(current_balance, market_data, indicators_data)
        current_session = session_params['session']
        
        # 🎯 GET SESSION-SPECIFIC TIMEFRAME CONFIG
        session_tf_config = SESSION_TF_CONFIG.get(current_session, SESSION_TF_CONFIG['LONDON'])
        
        print(f"🎯 ANALYZING {symbol} - SESSION: {current_session}")
        print(f"   📊 TF Setup: {session_tf_config['bias_tf']}m bias → {session_tf_config['entry_tf']}m entry" + 
              (f" → 1m trigger" if session_tf_config['use_trigger'] else ""))
        
        # 📊 GET MULTI-TIMEFRAME DATA
        tf_data = get_multi_timeframe_data(symbol, session_tf_config)
        if tf_data is None:
            return None
        
        # 📈 CALCULATE MULTI-TF INDICATORS
        indicators = calculate_multi_tf_indicators(tf_data)
        if indicators is None:
            return None
        
        # 🧠 MULTI-TIMEFRAME SIGNAL LOGIC
        signal = analyze_multi_tf_signal(symbol, indicators, session_params, session_tf_config)
        if signal is None:
            return None
        
        # Calculate position sizing with session parameters
        risk_percent = session_params['risk_percent']
        risk_amount = current_balance * risk_percent / 100
        
        # Position size berdasarkan risk dan SL distance
        sl_distance = abs(signal['close'] - signal['sl'])
        pos_size = risk_amount / sl_distance  # Quantity dalam coins
        position_value_usd = pos_size * signal['close']  # Nilai posisi dalam USD
        
        # MARGIN CHECK: Pastikan margin tidak melebihi balance yang tersedia
        required_margin = position_value_usd / signal['leverage']
        
        # Check margin dengan posisi yang sudah ada
        current_positions = dry_run_system.get_open_positions() if DRY_RUN else get_open_positions()
        total_existing_margin = 0
        
        if DRY_RUN:
            for pos in current_positions:
                pos_value = pos.get('position_value_usd', 0) or 0
                leverage = pos.get('leverage', 1) or 1
                if pos_value and leverage:
                    existing_margin = pos_value / leverage
                    total_existing_margin += existing_margin
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
        
        # Get max margin usage from environment
        max_margin_usage = float(os.getenv('MAX_MARGIN_USAGE_PERCENT', 65))
        
        # REJECT jika margin usage akan melebihi limit
        if margin_usage_percent > max_margin_usage:
            print(f"❌🛑 {symbol} REJECTED: Margin usage akan {margin_usage_percent:.1f}% (>{max_margin_usage}%)")
            return None
        
        # Update signal with calculated values
        signal['risk_amount'] = risk_amount
        signal['pos_size'] = pos_size
        signal['position_value_usd'] = position_value_usd
        
        print(f"✅ {symbol} {signal['direction']} - {signal.get('setup_type', 'MULTI-TF')} - Risk: {risk_percent}% - Leverage: {signal['leverage']}x")
        
        return signal
        
    except Exception as e:
        print(f"❌ Error analyzing {symbol}: {e}")
        return None

def analyze_multi_tf_signal(symbol, indicators, session_params, tf_config):
    """Analyze multi-timeframe signals dengan session-specific logic"""
    try:
        bias_ind = indicators['bias']
        entry_ind = indicators['entry']
        trigger_ind = indicators['trigger']
        atr_value = indicators['atr_value']
        
        current_session = session_params['session']
        current_price = entry_ind['close']
        
        # 🧠 STEP 1: BIAS CHECK (15m) - Market Structure
        bias_bullish = bias_ind['trend_bullish'] and bias_ind['macd_bullish']
        bias_bearish = not bias_ind['trend_bullish'] and not bias_ind['macd_bullish']
        
        if not (bias_bullish or bias_bearish):
            return None  # No clear bias
        
        # 📊 STEP 2: ENTRY SIGNAL (5m/3m) - Presisi Entry
        entry_aligned = (bias_bullish and entry_ind['trend_bullish']) or (bias_bearish and not entry_ind['trend_bullish'])
        entry_momentum = entry_ind['macd_bullish'] if bias_bullish else not entry_ind['macd_bullish']
        
        # Volume confirmation
        volume_spike = entry_ind['volume'] > entry_ind['volume_avg'] * 1.2
        
        if not (entry_aligned and entry_momentum):
            return None  # Entry tidak aligned dengan bias
        
        # ⚡ STEP 3: TRIGGER CHECK (1m) - Fine Timing (Opsional)
        trigger_ok = True  # Default OK jika tidak pakai trigger
        
        if tf_config['use_trigger'] and trigger_ind is not None:
            if bias_bullish:
                trigger_ok = trigger_ind['above_ema'] and trigger_ind['momentum_up']
            else:
                trigger_ok = not trigger_ind['above_ema'] and not trigger_ind['momentum_up']
        
        if not trigger_ok:
            return None  # Trigger timing tidak tepat
        
        # 🎯 STEP 4: SESSION-SPECIFIC LOGIC
        if current_session == 'DEAD_ZONE':
            # Conservative approach - hanya strong signals
            if bias_ind['rsi'] < 35 or bias_ind['rsi'] > 65:
                return None  # Avoid extreme RSI di dead zone
        
        elif current_session == 'ASIA':
            # Mean reversion bias - look for oversold/overbought
            if bias_bullish and entry_ind['rsi'] > 30:
                return None  # Wait for deeper pullback
            if bias_bearish and entry_ind['rsi'] < 70:
                return None  # Wait for higher bounce
        
        elif current_session == 'LONDON':
            # Breakout bias - momentum confirmation
            if not volume_spike:
                return None  # Volume confirmation wajib untuk breakout
        
        elif current_session == 'NEWYORK':
            # High momentum - additional safety
            if abs(bias_ind['rsi'] - 50) < 10:
                return None  # Avoid neutral RSI di NY session
        
        # 💰 STEP 5: CALCULATE ENTRY, SL, TP
        direction = "LONG" if bias_bullish else "SHORT"
        
        # SL & TP berdasarkan ATR (15m - stabil)
        if direction == "LONG":
            sl_price = current_price - (atr_value * SL_ATR_MULT)
            tp_price = current_price + (atr_value * TP_ATR_MULT)
        else:
            sl_price = current_price + (atr_value * SL_ATR_MULT)
            tp_price = current_price - (atr_value * TP_ATR_MULT)
        
        # Risk/Reward check
        sl_distance = abs(current_price - sl_price)
        tp_distance = abs(tp_price - current_price)
        rr_ratio = tp_distance / sl_distance if sl_distance > 0 else 0
        
        if rr_ratio < 1.2:  # Minimum R:R 1.2:1 untuk scalping
            return None
        
        # Leverage calculation
        leverage = min(session_params['max_leverage'], 15)  # Cap at 15x untuk scalping
        
        # Entry zone (untuk presisi)
        entry_buffer = atr_value * 0.1  # 10% ATR buffer
        entry_low = current_price - entry_buffer
        entry_high = current_price + entry_buffer
        
        signal = {
            'symbol': symbol,
            'direction': direction,
            'close': current_price,
            'entry_low': entry_low,
            'entry_high': entry_high,
            'sl': sl_price,
            'tp': tp_price,
            'leverage': leverage,
            'atr_value': atr_value,
            'sl_percent': (sl_distance / current_price) * 100,
            'rr_ratio': rr_ratio,
            'setup_type': f'MULTI-TF-{current_session}',
            'lev_mode': f'{leverage}x',
            'rsi_level': entry_ind['rsi'],
            'volume_spike': volume_spike,
            'session': current_session,
            'tf_config': tf_config,
            
            # Technical details untuk analysis
            'bias_bullish': bias_bullish,
            'entry_aligned': entry_aligned,
            'trigger_ok': trigger_ok,
            'bias_rsi': bias_ind['rsi'],
            'entry_rsi': entry_ind['rsi'],
            'bias_macd': bias_ind['macd_line'] - bias_ind['signal_line'],
            'entry_macd': entry_ind['macd_line'] - entry_ind['signal_line'],
            
            # CRITICAL: Add boolean indicators for AI reasoning
            'ema_fast_above_slow': entry_ind['trend_bullish'],  # EMA trend
            'macd_bullish': entry_ind['macd_bullish'],  # MACD signal
            'rsi_oversold': entry_ind['rsi'] < 30,  # RSI oversold
            'rsi_overbought': entry_ind['rsi'] > 70,  # RSI overbought
            'rsi_neutral': 30 <= entry_ind['rsi'] <= 70,  # RSI neutral
            'volume_confirmation': volume_spike,  # Volume confirmation
            'volatility_confirmation': atr_value > 0,  # ATR volatility
            'price_near_support': direction == "LONG" and entry_ind['rsi'] < 40,  # Support level for LONG
            'price_near_resistance': direction == "SHORT" and entry_ind['rsi'] > 60,  # Resistance level for SHORT
            'trend_alignment': entry_aligned,  # Multi-TF trend alignment
            'momentum_confirmation': entry_momentum,  # Momentum confirmation
            
            # Numerical indicator values for AI analysis
            'ema_fast_value': entry_ind.get('ema_fast', current_price),
            'ema_slow_value': entry_ind.get('ema_slow', current_price),
            'macd_line_value': entry_ind['macd_line'],
            'signal_line_value': entry_ind['signal_line'],
            'support_resistance': current_price,  # Current price as reference
            'price_distance_from_level': 0.0  # Distance from key level
        }
        
        return signal
        
    except Exception as e:
        print(f"❌ Error in multi-TF signal analysis: {e}")
        return None

# ==================
# TELEGRAM COMMAND HANDLERS
# ==================
async def handle_telegram_commands():
    """Handle Telegram commands for trading control with inline keyboard buttons"""
    try:
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from trading_control_system import start_trading, stop_trading, get_trading_status
        
        def get_control_keyboard(status_enabled=True):
            """Create inline keyboard for trading control"""
            keyboard = []
            
            if status_enabled:
                keyboard.append([
                    InlineKeyboardButton("🛑 Stop Trading", callback_data="stop_trading"),
                    InlineKeyboardButton("📊 Status", callback_data="trading_status")
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton("▶️ Start Trading", callback_data="start_trading"),
                    InlineKeyboardButton("📊 Status", callback_data="trading_status")
                ])
            
            keyboard.append([
                InlineKeyboardButton("📈 Positions", callback_data="show_positions"),
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_status")
            ])
            
            return InlineKeyboardMarkup(keyboard)
        
        async def start_command(update, context):
            """Handle /start command with control panel"""
            try:
                status = get_trading_status()
                
                # Get current positions count
                if DRY_RUN:
                    positions = dry_run_system.get_open_positions()
                    metrics = dry_run_system.get_performance_metrics()
                    mode_text = "🧪 DRY RUN (Simulation)"
                else:
                    positions = get_open_positions()
                    mode_text = "🔴 LIVE TRADING"
                    metrics = {'total_pnl': 0, 'win_rate': 0}
                
                status_emoji = "🟢" if status['enabled'] else "🔴"
                
                # Get session info safely
                try:
                    from session_management_system import get_session_status
                    session_status = get_session_status()
                    session_info = f"""
📅 <b>Current Session:</b>
• {session_status.get('session_emoji', '🕐')} {session_status.get('session_name', 'Unknown')}
• Strategy: {session_status.get('strategy', 'N/A')}
• Risk: {session_status.get('risk_range', 'N/A')}
• Next: {session_status.get('next_change', 'N/A')}"""
                except Exception as e:
                    print(f"⚠️ Session status error: {e}")
                    session_info = "\n📅 <b>Session Info:</b> Loading..."
                
                # Get session performance stats
                try:
                    from trading_session_system import get_session_analyzer
                    session_analyzer = get_session_analyzer()
                    performance = session_analyzer.get_session_performance("dry_run", 7)  # Last 7 days
                    
                    if performance.get('success'):
                        sessions = performance['sessions']
                        session_stats = ""
                        
                        for session_key, stats in sessions.items():
                            if stats['total_trades'] > 0:
                                session_stats += f"""
• {stats['color']} {stats['name']}: {stats['total_trades']} trades, {stats['win_rate']:.1f}% WR, ${stats['total_pnl']:.0f} PnL"""
                        
                        if session_stats:
                            session_info += f"\n\n📊 <b>7-Day Performance:</b>{session_stats}"
                    
                except Exception as e:
                    print(f"⚠️ Session performance error: {e}")
                
                # Calculate drawdown
                drawdown_info = ""
                try:
                    max_balance = metrics.get('max_balance', metrics.get('balance', 0))
                    current_balance = metrics.get('balance', 0)
                    if max_balance > 0:
                        drawdown_pct = ((max_balance - current_balance) / max_balance) * 100
                        if drawdown_pct > 0:
                            drawdown_info = f"\n📉 <b>Drawdown:</b> {drawdown_pct:.1f}%"
                except Exception as e:
                    print(f"⚠️ Drawdown calculation error: {e}")
                
                message = f"""🤖 <b>LevaTrade Bot Control Panel</b>

{status_emoji} <b>Status:</b> {status['status_text']}
🕐 <b>Updated:</b> {status['last_updated'][:19].replace('T', ' ')}
👤 <b>By:</b> {status['updated_by']}

🤖 <b>Bot Info:</b>
• Mode: {mode_text}
• Open Positions: {len(positions)}
• Total PnL: ${metrics.get('total_pnl', 0):.2f}
• Win Rate: {metrics.get('win_rate', 0):.1f}%{drawdown_info}{session_info}

💡 <b>Use buttons below to control trading:</b>"""
                
                keyboard = get_control_keyboard(status['enabled'])
                await update.message.reply_text(message, parse_mode='HTML', reply_markup=keyboard)
                
            except Exception as e:
                error_message = f"❌ Error: {str(e)}"
                await update.message.reply_text(error_message)
                print(f"❌ Error in start_command: {e}")
        
        async def button_callback(update, context):
            """Handle button callbacks"""
            query = update.callback_query
            await query.answer()
            
            try:
                if query.data == "start_trading":
                    result = start_trading('telegram')
                    status = get_trading_status()
                    
                    message = f"""✅ <b>Trading STARTED</b>
📱 Controlled from Telegram
🤖 Bot will resume taking new positions

📊 <b>Current Status:</b> {status['status_text']}
🕐 <b>Updated:</b> {status['last_updated'][:19].replace('T', ' ')}"""
                    
                    keyboard = get_control_keyboard(True)
                    try:
                        await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)
                    except Exception as edit_error:
                        if "message is not modified" in str(edit_error).lower():
                            await query.answer("Trading started!")
                        else:
                            raise edit_error
                    print(f"✅ Trading started via Telegram by user {query.from_user.id}")
                
                elif query.data == "stop_trading":
                    result = stop_trading('telegram')
                    status = get_trading_status()
                    
                    message = f"""🛑 <b>Trading STOPPED</b>
📱 Controlled from Telegram
⏸️ Bot will not take new positions
📊 Existing positions continue to be monitored

📊 <b>Current Status:</b> {status['status_text']}
🕐 <b>Updated:</b> {status['last_updated'][:19].replace('T', ' ')}"""
                    
                    keyboard = get_control_keyboard(False)
                    try:
                        await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)
                    except Exception as edit_error:
                        if "message is not modified" in str(edit_error).lower():
                            await query.answer("Trading stopped!")
                        else:
                            raise edit_error
                    print(f"🛑 Trading stopped via Telegram by user {query.from_user.id}")
                
                elif query.data == "trading_status" or query.data == "refresh_status":
                    try:
                        status = get_trading_status()
                        
                        # Get current positions count
                        if DRY_RUN:
                            positions = dry_run_system.get_open_positions()
                            metrics = dry_run_system.get_performance_metrics()
                            mode_text = "🧪 DRY RUN (Simulation)"
                        else:
                            positions = get_open_positions()
                            mode_text = "🔴 LIVE TRADING"
                            metrics = {'total_pnl': 0, 'win_rate': 0}
                        
                        status_emoji = "🟢" if status['enabled'] else "🔴"
                        
                        # Get session info safely
                        try:
                            from session_management_system import get_session_status
                            session_status = get_session_status()
                            session_info = f"""
📅 <b>Current Session:</b>
• {session_status.get('session_emoji', '🕐')} {session_status.get('session_name', 'Unknown')}
• Strategy: {session_status.get('strategy', 'N/A')}
• Risk: {session_status.get('risk_range', 'N/A')}
• Next: {session_status.get('next_change', 'N/A')}"""
                        except Exception as e:
                            print(f"⚠️ Session status error: {e}")
                            session_info = "\n📅 <b>Session Info:</b> Loading..."
                        
                        # Get session performance stats
                        try:
                            from trading_session_system import get_session_analyzer
                            session_analyzer = get_session_analyzer()
                            performance = session_analyzer.get_session_performance("dry_run", 7)  # Last 7 days
                            
                            if performance.get('success'):
                                sessions = performance['sessions']
                                session_stats = ""
                                
                                for session_key, stats in sessions.items():
                                    if stats['total_trades'] > 0:
                                        win_emoji = "✅" if stats['win_rate'] >= 50 else "❌"
                                        pnl_emoji = "💚" if stats['total_pnl'] >= 0 else "❤️"
                                        session_stats += f"""
{win_emoji} {stats['color']} {stats['name']}: {stats['winning_trades']}W/{stats['losing_trades']}L ({stats['win_rate']:.1f}%) {pnl_emoji}${stats['total_pnl']:.0f}"""
                                
                                if session_stats:
                                    session_info += f"\n\n📊 <b>7-Day Session Stats:</b>{session_stats}"
                            
                        except Exception as e:
                            print(f"⚠️ Session performance error: {e}")
                        
                        # Calculate drawdown
                        drawdown_info = ""
                        try:
                            max_balance = metrics.get('max_balance', metrics.get('balance', 0))
                            current_balance = metrics.get('balance', 0)
                            if max_balance > 0:
                                drawdown_pct = ((max_balance - current_balance) / max_balance) * 100
                                if drawdown_pct > 0:
                                    drawdown_info = f"\n📉 <b>Max Drawdown:</b> {drawdown_pct:.1f}%"
                        except Exception as e:
                            print(f"⚠️ Drawdown calculation error: {e}")
                        
                        message = f"""{status_emoji} <b>Trading Status</b>

📊 <b>Current Status:</b> {status['status_text']}
🕐 <b>Updated:</b> {status['last_updated'][:19].replace('T', ' ')}
👤 <b>By:</b> {status['updated_by']}

🤖 <b>Bot Info:</b>
• Mode: {mode_text}
• Open Positions: {len(positions)}
• Total PnL: ${metrics.get('total_pnl', 0):.2f}
• Win Rate: {metrics.get('win_rate', 0):.1f}%{drawdown_info}{session_info}"""
                        
                        keyboard = get_control_keyboard(status['enabled'])
                        try:
                            await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)
                        except Exception as edit_error:
                            if "message is not modified" in str(edit_error).lower():
                                await query.answer("Status is up to date")
                            else:
                                raise edit_error
                        
                    except Exception as e:
                        await query.edit_message_text(f"❌ Error getting status: {str(e)}")
                        print(f"❌ Error in trading_status callback: {e}")
                
                elif query.data == "show_positions":
                    try:
                        # Get current positions
                        if DRY_RUN:
                            positions = dry_run_system.get_open_positions()
                            metrics = dry_run_system.get_performance_metrics()
                            mode_text = "🧪 DRY RUN"
                        else:
                            positions = get_open_positions()
                            mode_text = "🔴 LIVE"
                            metrics = {'total_pnl': 0}
                        
                        if not positions:
                            message = f"""📈 <b>Open Positions ({mode_text})</b>

🚫 <b>No open positions</b>

💡 Bot is scanning for new opportunities...
📊 Total PnL: ${metrics.get('total_pnl', 0):.2f}"""
                        else:
                            total_unrealized = sum(pos.get('unrealized_pnl', 0) for pos in positions)
                            
                            message = f"""📈 <b>Open Positions ({mode_text})</b>

📊 <b>Total Positions:</b> {len(positions)}
💰 <b>Unrealized PnL:</b> ${total_unrealized:.2f}

"""
                            
                            # Show top 5 positions
                            for i, pos in enumerate(positions[:5], 1):
                                direction_emoji = "🟢" if pos.get('direction') == 'LONG' else "🔴"
                                pnl = pos.get('unrealized_pnl', 0)
                                pnl_emoji = "💚" if pnl >= 0 else "❤️"
                                pnl_pct = pos.get('pnl_percentage', 0)
                                
                                message += f"""{direction_emoji} <b>{pos.get('symbol', 'N/A')}</b>
   {pos.get('direction', 'N/A')} @ ${pos.get('entry_price', 0):.4f}
   {pnl_emoji} PnL: ${pnl:.2f} ({pnl_pct:.1f}%)
   ⚖️ Leverage: {pos.get('leverage', 1)}x

"""
                            
                            if len(positions) > 5:
                                message += f"... and {len(positions) - 5} more positions"
                        
                        status = get_trading_status()
                        keyboard = get_control_keyboard(status['enabled'])
                        try:
                            await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)
                        except Exception as edit_error:
                            if "message is not modified" in str(edit_error).lower():
                                await query.answer("Positions are up to date")
                            else:
                                raise edit_error
                        
                    except Exception as e:
                        await query.edit_message_text(f"❌ Error loading positions: {str(e)}")
                        print(f"❌ Error in show_positions callback: {e}")
                
            except Exception as e:
                await query.edit_message_text(f"❌ Error: {str(e)}")
                print(f"❌ Error in button_callback: {e}")
        
        # Legacy command handlers (still work)
        async def start_trading_command(update, context):
            """Handle /start_trading command"""
            try:
                result = start_trading('telegram')
                status = get_trading_status()
                
                message = f"""✅ <b>Trading STARTED</b>
📱 Use /start for control panel with buttons"""
                
                await update.message.reply_text(message, parse_mode='HTML')
                print(f"✅ Trading started via command by user {update.effective_user.id}")
                
            except Exception as e:
                await update.message.reply_text(f"❌ Error starting trading: {str(e)}")
                print(f"❌ Error in start_trading_command: {e}")
        
        async def stop_trading_command(update, context):
            """Handle /stop_trading command"""
            try:
                result = stop_trading('telegram')
                status = get_trading_status()
                
                message = f"""🛑 <b>Trading STOPPED</b>
📱 Use /start for control panel with buttons"""
                
                await update.message.reply_text(message, parse_mode='HTML')
                print(f"🛑 Trading stopped via command by user {update.effective_user.id}")
                
            except Exception as e:
                await update.message.reply_text(f"❌ Error stopping trading: {str(e)}")
                print(f"❌ Error in stop_trading_command: {e}")
        
        # Create application with timeout settings
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_handler(CommandHandler("start_trading", start_trading_command))
        application.add_handler(CommandHandler("stop_trading", stop_trading_command))
        
        # Start the bot in background with timeout
        try:
            await asyncio.wait_for(application.initialize(), timeout=10.0)
            await asyncio.wait_for(application.start(), timeout=10.0)
            
            # Start polling in background to receive messages
            print("🔄 Starting Telegram polling...")
            
            # Create a background task for polling
            async def start_polling_task():
                try:
                    await application.updater.start_polling(
                        poll_interval=1.0,
                        timeout=10,
                        bootstrap_retries=-1
                    )
                except Exception as e:
                    print(f"⚠️ Polling error: {e}")
            
            # Start polling as background task
            asyncio.create_task(start_polling_task())
            
            print("✅ Telegram command handlers initialized")
            print("✅ Telegram polling started")
            print("💡 Available commands:")
            print("   /start - Control panel with buttons")
            print("   /start_trading - Start trading (legacy)")
            print("   /stop_trading - Stop trading (legacy)")
            
            return application
        except asyncio.TimeoutError:
            print("⚠️ Telegram initialization timed out - continuing without Telegram commands")
            return None
        
    except Exception as e:
        print(f"❌ Error setting up Telegram commands: {e}")
        print("⚠️ Continuing without Telegram commands - Dashboard controls still available")
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
            # Get current market data for the symbol (use ENTRY_TF for monitoring)
            df = get_klines(symbol, ENTRY_TF, 50)  # Get recent data for indicators
            if df is None or len(df) < 20:
                continue
            
            # Calculate current indicators
            df['ema_fast'] = calculate_ema(df['close'], EMA_FAST_ENTRY)
            df['ema_slow'] = calculate_ema(df['close'], EMA_SLOW_ENTRY)
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
                    
                    # Execute the exit action with proper notifications
                    if action['type'] == 'partial_tp':
                        print(f"   📈 Executing partial TP: {action['percentage']}% of {symbol} position")
                        
                        # Get position info for notification
                        position_info = {
                            'symbol': symbol,
                            'direction': position.get('direction', 'UNKNOWN'),
                            'entry_price': position.get('entry_price', 0),
                            'current_price': current_price
                        }
                        
                        # Calculate profit amount (approximate)
                        profit_amount = action.get('profit_amount', 0)
                        profit_atr = action.get('profit_atr', 0)
                        
                        # Send notifications
                        try:
                            from partial_tp_notification_system import notify_partial_tp
                            await notify_partial_tp(position_info, action['percentage'], profit_amount, profit_atr)
                        except Exception as e:
                            print(f"   ⚠️ Partial TP notification error: {e}")
                        
                        # Mark partial TP as executed in position
                        position[f"partial_tp_{action['percentage']}_executed"] = True
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

def check_single_instance():
    """Check if another instance is already running"""
    import psutil
    import sys
    
    current_pid = os.getpid()
    script_name = "crypto_bot_parallel.py"
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid and proc.info['name'] == 'python.exe':
                cmdline = proc.info['cmdline']
                if cmdline and any(script_name in arg for arg in cmdline):
                    print(f"❌ Another instance of {script_name} is already running (PID: {proc.info['pid']})")
                    print(f"🛑 Please stop the existing instance first or use Ctrl+C to stop it")
                    print(f"💡 You can also kill it with: taskkill /PID {proc.info['pid']} /F")
                    sys.exit(1)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

async def main():
    """Main loop untuk monitoring"""
    # Check for existing instances
    check_single_instance()
    
    print("🚀 Bot started (Multi-Timeframe Scalping Mode)...")
    print(f"⚡ Max Workers: {MAX_WORKERS} threads")
    print(f"⏰ Multi-TF Setup: {BIAS_TF}m bias → {ENTRY_TF}m entry → {TRIGGER_TF}m trigger (session-dependent)")
    print(f"🔄 Scan Interval: {SCAN_INTERVAL//60} minutes {SCAN_INTERVAL%60} seconds")
    print(f"📊 Mode: {'ALL USDT PAIRS' if SCAN_ALL_USDT else f'TOP {TOP_VOLUME_COUNT} VOLUME'}")
    print(f"📈 Indicators: Multi-TF EMA/RSI/MACD, ATR from {ATR_TF}m")
    
    # Show current session status
    print("\n📊 CURRENT SESSION STATUS:")
    print("=" * 50)
    session_status = get_session_status()
    print(f"🕐 Current Time: {session_status['current_time_wib']}")
    print(f"📍 Active Session: {session_status['current_session']}")
    print(f"🎯 Strategy: {session_status['strategy']}")
    print(f"💰 Risk: {session_status['default_risk']}%-{session_status['max_risk']}% | Leverage: {session_status['max_leverage']}x | Positions: {session_status['max_positions']}")
    print(f"🎲 TP/SL: {session_status['tp_multiplier']}x/{session_status['sl_multiplier']}x ATR")
    print(f"⏳ Next Change: {session_status['next_change']} in {session_status['time_until_change']}")
    
    # Initialize Telegram command handlers
    print("\n🤖 Initializing Telegram command handlers...")
    telegram_app = await handle_telegram_commands()
    
    # Check initial trading status
    from trading_control_system import get_trading_status
    initial_status = get_trading_status()
    status_emoji = "🟢" if initial_status['enabled'] else "🔴"
    print(f"{status_emoji} Trading Status: {initial_status['status_text']}")
    if not initial_status['enabled']:
        print("⚠️  Trading is currently DISABLED - Bot will scan but not execute trades")
        print("💡 Use /start_trading in Telegram or Dashboard to enable trading")
    
    # Auto Trading Status
    if AUTO_TRADE_ENABLED:
        mode_text = "DRY RUN (Simulation)" if DRY_RUN else "LIVE TRADING"
        print(f"🤖 Auto Trading: ENABLED ({mode_text})")
        print(f"📊 Multi-timeframe scalping with session-based parameters")
        
        # Show timeframe setup per session
        print(f"\n🎯 TIMEFRAME SETUP PER SESSION:")
        for session, config in SESSION_TF_CONFIG.items():
            trigger_text = f" → {TRIGGER_TF}m trigger" if config['use_trigger'] else ""
            print(f"   {session}: {config['bias_tf']}m bias → {config['entry_tf']}m entry{trigger_text}")
        
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
        'timeframe_setup': f"{BIAS_TF}m→{ENTRY_TF}m→{TRIGGER_TF}m",
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
                    
                    if current_time - main.last_position_update >= 5:  # 5 seconds (lebih ketat untuk SL/TP monitoring)
                        # Collect current prices for open positions
                        open_positions_symbols = [pos['symbol'] for pos in dry_run_system.get_open_positions()]
                        if open_positions_symbols:
                            current_prices = {}
                            print(f"📊 Updating prices for {len(open_positions_symbols)} open positions...")
                            
                            for symbol in open_positions_symbols:
                                df = get_klines(symbol, ENTRY_TF, 1)  # Use entry TF for position updates
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
                        # Check if trading is enabled before processing signals
                        if not is_trading_enabled():
                            print(f"🛑 TRADING STOPPED: Skipping all signals - Trading is currently disabled")
                            print(f"   📊 {len(signals)} signals ignored: {[s['symbol'] + '_' + s['direction'] for s in signals]}")
                            break  # Skip all signals if trading is disabled
                        
                        alert_key = f"{signal['symbol']}_{signal['direction']}"
                        current_time_key = int(time.time() / (int(ENTRY_TF) * 60))  # Use ENTRY_TF for alert timing
                        
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
                    
                    # Position update every 5 seconds during wait (ketat untuk SL/TP monitoring)
                    if i > 0:  # Skip first iteration (i=0)
                        print(f"\n📊 Position Update (during wait) at {datetime.now().strftime('%H:%M:%S')}")
                        
                        try:
                            # Update positions for dry run
                            if DRY_RUN:
                                open_positions_symbols = [pos['symbol'] for pos in dry_run_system.get_open_positions()]
                                if open_positions_symbols:
                                    current_prices = {}
                                    for symbol in open_positions_symbols:
                                        df = get_klines(symbol, ENTRY_TF, 1)  # Use entry TF for updates
                                        if df is not None and len(df) > 0:
                                            current_prices[symbol] = df.iloc[-1]['close']
                                    
                                    if current_prices:
                                        await dry_run_system.update_positions(current_prices)
                                        print(f"   ✅ Updated {len(current_prices)} positions")
                                        
                                        # Check for time-based exits
                                        current_positions = dry_run_system.get_open_positions()
                                        positions_to_close = check_time_based_exits(current_positions)
                                        
                                        if positions_to_close:
                                            print(f"   ⏰ Found {len(positions_to_close)} positions to close due to time limits")
                                            
                                            for position_to_close in positions_to_close:
                                                symbol = position_to_close['symbol']
                                                duration = position_to_close['duration_minutes']
                                                max_duration = position_to_close['max_duration']
                                                session = position_to_close['session']
                                                
                                                print(f"   ⏰🚪 Closing {symbol} - Duration: {duration:.1f}m > {max_duration}m ({session})")
                                                
                                                # Close position in dry run system
                                                await dry_run_system.close_position(symbol, "TIME_STOP")
                                                
                                                # Remove from time tracking
                                                remove_position_tracking(symbol)
                                                
                                                # Send notification
                                                try:
                                                    from time_based_stop_system import send_time_stop_notification
                                                    await send_time_stop_notification(position_to_close)
                                                except ImportError:
                                                    print(f"   ⚠️ Time stop notification not available")
                                                except Exception as e:
                                                    print(f"   ⚠️ Time stop notification error: {e}")
                            
                            # Early exit monitoring for real trading
                            if AUTO_TRADE_ENABLED and not DRY_RUN:
                                await monitor_early_exits()
                                
                                # Check for time-based exits in real trading
                                current_positions = get_open_positions()
                                if current_positions:
                                    # Convert real positions to format expected by time-based stop
                                    positions_list = []
                                    for symbol, pos in current_positions.items():
                                        positions_list.append({
                                            'symbol': symbol,
                                            'direction': pos.get('side', 'UNKNOWN').upper(),
                                            'entry_price': pos.get('entry_price', 0),
                                            'current_price': 0,  # Will be updated
                                            'unrealized_pnl': pos.get('unrealized_pnl', 0)
                                        })
                                    
                                    positions_to_close = check_time_based_exits(positions_list)
                                    
                                    if positions_to_close:
                                        print(f"   ⏰ Found {len(positions_to_close)} real positions to close due to time limits")
                                        
                                        for position_to_close in positions_to_close:
                                            symbol = position_to_close['symbol']
                                            duration = position_to_close['duration_minutes']
                                            max_duration = position_to_close['max_duration']
                                            session = position_to_close['session']
                                            
                                            print(f"   ⏰🚪 Would close REAL position {symbol} - Duration: {duration:.1f}m > {max_duration}m ({session})")
                                            
                                            # TODO: Implement real position closing
                                            # For now, just remove from tracking and send notification
                                            remove_position_tracking(symbol)
                                            try:
                                                from time_based_stop_system import send_time_stop_notification
                                                await send_time_stop_notification(position_to_close)
                                            except ImportError:
                                                print(f"   ⚠️ Time stop notification not available")
                                            except Exception as e:
                                                print(f"   ⚠️ Time stop notification error: {e}")
                                
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
    finally:
        # Cleanup Telegram app
        if 'telegram_app' in locals() and telegram_app:
            try:
                await telegram_app.stop()
                await telegram_app.shutdown()
                print("✅ Telegram command handlers stopped")
            except Exception as e:
                print(f"⚠️ Error stopping Telegram handlers: {e}")
    
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
