"""
Debug script dengan MAINNET data (sama dengan TradingView)
"""
import os
from pybit.unified_trading import HTTP
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# GUNAKAN MAINNET untuk data yang sama dengan TradingView
session = HTTP(
    testnet=False,  # MAINNET
    api_key='',  # Tidak perlu API key untuk data public
    api_secret=''
)

# Parameters
EMA_FAST = 21
EMA_SLOW = 55
RSI_LENGTH = 14
TP_ATR_MULT = 2.0
SL_ATR_MULT = 1.2
PIVOT_LENGTH = 5
BALANCE = 1000
MAX_RISK = 2.0
MAX_LEVERAGE = 20

def get_klines(symbol, interval='240', limit=200):
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
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
            df = df.astype({
                'open': float, 'high': float, 'low': float, 
                'close': float, 'volume': float
            })
            df = df.iloc[::-1].reset_index(drop=True)
            return df
        return None
    except Exception as e:
        print(f"Error: {e}")
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

def debug_symbol(symbol):
    print("=" * 70)
    print(f"  DEBUG: {symbol} (MAINNET DATA)")
    print("=" * 70)
    
    df = get_klines(symbol, '240', 200)
    if df is None:
        print("❌ Failed to get data")
        return
    
    # Calculate indicators
    df['ema_fast'] = calculate_ema(df['close'], EMA_FAST)
    df['ema_slow'] = calculate_ema(df['close'], EMA_SLOW)
    df['rsi'] = calculate_rsi(df['close'], RSI_LENGTH)
    df['atr'] = calculate_atr(df, 14)
    df['macd_line'], df['signal_line'] = calculate_macd(df['close'])
    
    # Get latest values
    last = df.iloc[-1]
    
    print(f"\n📊 LAST 5 CANDLES (4H)")
    print("-" * 70)
    for i in range(-5, 0):
        candle = df.iloc[i]
        label = "→ CURRENT" if i == -1 else f"  PREV {abs(i)-1}"
        time_str = candle['timestamp'].strftime('%Y-%m-%d %H:%M')
        print(f"{label}: {time_str} | C=${candle['close']:.4f}, H=${candle['high']:.4f}, L=${candle['low']:.4f}")
    
    print(f"\n📈 INDICATORS (Current Candle)")
    print("-" * 70)
    print(f"EMA Fast ({EMA_FAST}):  ${last['ema_fast']:.4f}")
    print(f"EMA Slow ({EMA_SLOW}):  ${last['ema_slow']:.4f}")
    print(f"RSI ({RSI_LENGTH}):      {last['rsi']:.2f}")
    print(f"ATR (14):     ${last['atr']:.4f}")
    print(f"MACD Line:    {last['macd_line']:.6f}")
    print(f"Signal Line:  {last['signal_line']:.6f}")
    print(f"MACD Hist:    {last['macd_line'] - last['signal_line']:.6f}")
    
    # Support & Resistance
    resistance = find_pivot_high(df, PIVOT_LENGTH)
    support = find_pivot_low(df, PIVOT_LENGTH)
    
    print(f"\n🎯 SUPPORT & RESISTANCE (Pivot Length={PIVOT_LENGTH})")
    print("-" * 70)
    print(f"Resistance:   ${resistance:.4f}" if resistance else "Resistance:   None")
    print(f"Support:      ${support:.4f}" if support else "Support:      None")
    
    # Market Bias
    print(f"\n🔍 MARKET BIAS CONDITIONS")
    print("-" * 70)
    
    ema_bullish = last['ema_fast'] > last['ema_slow']
    macd_bullish = last['macd_line'] > last['signal_line']
    rsi_bullish = last['rsi'] > 55
    
    ema_bearish = last['ema_fast'] < last['ema_slow']
    macd_bearish = last['macd_line'] < last['signal_line']
    rsi_bearish = last['rsi'] < 45
    
    print(f"BULLISH CONDITIONS:")
    print(f"  EMA Fast > EMA Slow:   {ema_bullish} {'✅' if ema_bullish else '❌'} ({last['ema_fast']:.4f} > {last['ema_slow']:.4f})")
    print(f"  MACD > Signal:         {macd_bullish} {'✅' if macd_bullish else '❌'} ({last['macd_line']:.6f} > {last['signal_line']:.6f})")
    print(f"  RSI > 55:              {rsi_bullish} {'✅' if rsi_bullish else '❌'} ({last['rsi']:.2f} > 55)")
    print(f"  → BULLISH:             {ema_bullish and macd_bullish and rsi_bullish} {'🟢 YES' if ema_bullish and macd_bullish and rsi_bullish else '⚪ NO'}")
    
    print(f"\nBEARISH CONDITIONS:")
    print(f"  EMA Fast < EMA Slow:   {ema_bearish} {'✅' if ema_bearish else '❌'} ({last['ema_fast']:.4f} < {last['ema_slow']:.4f})")
    print(f"  MACD < Signal:         {macd_bearish} {'✅' if macd_bearish else '❌'} ({last['macd_line']:.6f} < {last['signal_line']:.6f})")
    print(f"  RSI < 45:              {rsi_bearish} {'✅' if rsi_bearish else '❌'} ({last['rsi']:.2f} < 45)")
    print(f"  → BEARISH:             {ema_bearish and macd_bearish and rsi_bearish} {'🔴 YES' if ema_bearish and macd_bearish and rsi_bearish else '⚪ NO'}")
    
    bullish = ema_bullish and macd_bullish and rsi_bullish
    bearish = ema_bearish and macd_bearish and rsi_bearish
    
    # Entry Zones
    print(f"\n🎯 ENTRY ZONES & SIGNALS")
    print("-" * 70)
    
    if bullish and support:
        entry_low = support
        entry_high = support + last['atr'] * 0.5
        tp = last['close'] + last['atr'] * TP_ATR_MULT
        sl = last['close'] - last['atr'] * SL_ATR_MULT
        
        in_zone_price = last['low'] <= entry_high and last['high'] >= entry_low
        
        print(f"✅ LONG SETUP DETECTED 📈")
        print(f"Entry Zone:   ${entry_low:.4f} - ${entry_high:.4f}")
        print(f"Stop Loss:    ${sl:.4f}")
        print(f"Take Profit:  ${tp:.4f}")
        print(f"\nEntry Zone Check:")
        print(f"  Low <= Entry High:  ${last['low']:.4f} <= ${entry_high:.4f} = {last['low'] <= entry_high} {'✅' if last['low'] <= entry_high else '❌'}")
        print(f"  High >= Entry Low:  ${last['high']:.4f} >= ${entry_low:.4f} = {last['high'] >= entry_low} {'✅' if last['high'] >= entry_low else '❌'}")
        print(f"  → ALERT STATUS:     {'🟢 ENTRY ZONE ACTIVE' if in_zone_price else '⚪ WAIT'}")
        
    elif bearish and resistance:
        entry_low = resistance - last['atr'] * 0.5
        entry_high = resistance
        tp = last['close'] - last['atr'] * TP_ATR_MULT
        sl = last['close'] + last['atr'] * SL_ATR_MULT
        
        in_zone_price = last['low'] <= entry_high and last['high'] >= entry_low
        
        print(f"✅ SHORT SETUP DETECTED 📉")
        print(f"Entry Zone:   ${entry_low:.4f} - ${entry_high:.4f}")
        print(f"Stop Loss:    ${sl:.4f}")
        print(f"Take Profit:  ${tp:.4f}")
        print(f"\nEntry Zone Check:")
        print(f"  Low <= Entry High:  ${last['low']:.4f} <= ${entry_high:.4f} = {last['low'] <= entry_high} {'✅' if last['low'] <= entry_high else '❌'}")
        print(f"  High >= Entry Low:  ${last['high']:.4f} >= ${entry_low:.4f} = {last['high'] >= entry_low} {'✅' if last['high'] >= entry_low else '❌'}")
        print(f"  → ALERT STATUS:     {'🟢 ENTRY ZONE ACTIVE' if in_zone_price else '⚪ WAIT'}")
        
        # Risk Management
        sl_distance = abs(last['close'] - sl)
        raw_lev = (MAX_RISK / 100) * last['close'] / sl_distance
        suggest_lev = min(MAX_LEVERAGE, max(1, round(raw_lev)))
        
        if suggest_lev <= 3:
            lev_mode = "SAFE"
        elif suggest_lev <= 8:
            lev_mode = "NORMAL"
        else:
            lev_mode = "AGGRESSIVE"
        
        risk_amount = BALANCE * MAX_RISK / 100
        sl_percent = sl_distance / last['close'] * 100
        rr_ratio = TP_ATR_MULT / SL_ATR_MULT
        pos_size = risk_amount / sl_distance * suggest_lev
        
        print(f"\n💰 RISK MANAGEMENT")
        print(f"Leverage:     {suggest_lev}x ({lev_mode})")
        print(f"Risk Amount:  ${risk_amount:.2f}")
        print(f"Position Size: {pos_size:.3f}")
        print(f"SL %:         {sl_percent:.2f}%")
        print(f"R:R:          1:{rr_ratio:.2f}")
        
    else:
        print("⚪ NO SETUP")
        if not bullish and not bearish:
            print("   Reason: Market is NEUTRAL")
        elif bullish and not support:
            print("   Reason: BULLISH but no Support found")
        elif bearish and not resistance:
            print("   Reason: BEARISH but no Resistance found")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    import sys
    
    symbol = "XRPUSDT"
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'
    
    debug_symbol(symbol)
    print("✅ Debug completed! (Using MAINNET data)")
