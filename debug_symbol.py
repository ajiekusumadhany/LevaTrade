"""
Debug script untuk compare dengan TradingView
Cek detail indicator untuk satu symbol
"""
import os
from pybit.unified_trading import HTTP
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')

session = HTTP(
    testnet=True,
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)

# Parameters (sama dengan TradingView)
EMA_FAST = 21
EMA_SLOW = 55
RSI_LENGTH = 14
TP_ATR_MULT = 2.0
SL_ATR_MULT = 1.2
PIVOT_LENGTH = 5

# Trading Parameters (dari environment variables)
BALANCE = float(os.getenv('BALANCE_USD', '1000'))  # Default $1000
MAX_RISK = float(os.getenv('MAX_RISK_PERCENT', '1.0'))  # Default 1%
MAX_LEVERAGE = int(os.getenv('MAX_LEVERAGE', '10'))  # Default 10x

def get_klines(symbol, interval='240', limit=200):
    """Ambil data candlestick"""
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
    """Find pivot high - SAMA dengan TradingView ta.pivothigh"""
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
    """Find pivot low - SAMA dengan TradingView ta.pivotlow"""
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
    """Debug detail untuk satu symbol"""
    print("=" * 70)
    print(f"  DEBUG: {symbol}")
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
    prev = df.iloc[-2]
    
    print(f"\n📊 LAST 3 CANDLES")
    print("-" * 70)
    for i in range(-3, 0):
        candle = df.iloc[i]
        label = "CURRENT" if i == -1 else f"PREV {abs(i)-1}"
        print(f"{label}: Close=${candle['close']:.4f}, High=${candle['high']:.4f}, Low=${candle['low']:.4f}")
    
    print(f"\n📊 CURRENT CANDLE (Latest)")
    print("-" * 70)
    print(f"Close:      ${last['close']:.4f}")
    print(f"High:       ${last['high']:.4f}")
    print(f"Low:        ${last['low']:.4f}")
    print(f"Open:       ${last['open']:.4f}")
    
    print(f"\n📈 INDICATORS")
    print("-" * 70)
    print(f"EMA Fast ({EMA_FAST}):  ${last['ema_fast']:.4f}")
    print(f"EMA Slow ({EMA_SLOW}):  ${last['ema_slow']:.4f}")
    print(f"RSI ({RSI_LENGTH}):      {last['rsi']:.2f}")
    print(f"ATR (14):     ${last['atr']:.4f}")
    print(f"MACD Line:    {last['macd_line']:.4f}")
    print(f"Signal Line:  {last['signal_line']:.4f}")
    
    # Support & Resistance
    resistance = find_pivot_high(df, PIVOT_LENGTH)
    support = find_pivot_low(df, PIVOT_LENGTH)
    
    print(f"\n🎯 SUPPORT & RESISTANCE")
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
    
    print(f"EMA Fast > EMA Slow:     {ema_bullish} {'✅' if ema_bullish else '❌'}")
    print(f"MACD > Signal:           {macd_bullish} {'✅' if macd_bullish else '❌'}")
    print(f"RSI > 55:                {rsi_bullish} {'✅' if rsi_bullish else '❌'}")
    print(f"→ BULLISH:               {ema_bullish and macd_bullish and rsi_bullish} {'🟢' if ema_bullish and macd_bullish and rsi_bullish else '⚪'}")
    
    print()
    print(f"EMA Fast < EMA Slow:     {ema_bearish} {'✅' if ema_bearish else '❌'}")
    print(f"MACD < Signal:           {macd_bearish} {'✅' if macd_bearish else '❌'}")
    print(f"RSI < 45:                {rsi_bearish} {'✅' if rsi_bearish else '❌'}")
    print(f"→ BEARISH:               {ema_bearish and macd_bearish and rsi_bearish} {'🔴' if ema_bearish and macd_bearish and rsi_bearish else '⚪'}")
    
    bullish = ema_bullish and macd_bullish and rsi_bullish
    bearish = ema_bearish and macd_bearish and rsi_bearish
    
    # Entry Zones
    print(f"\n🎯 ENTRY ZONES")
    print("-" * 70)
    
    if bullish and support:
        entry_low = support
        entry_high = support + last['atr'] * 0.5
        tp = last['close'] + last['atr'] * TP_ATR_MULT
        sl = last['close'] - last['atr'] * SL_ATR_MULT
        direction = "LONG"
        
        print(f"Direction:    {direction} 📈")
        print(f"Entry Low:    ${entry_low:.4f}")
        print(f"Entry High:   ${entry_high:.4f}")
        print(f"Stop Loss:    ${sl:.4f}")
        print(f"Take Profit:  ${tp:.4f}")
        
        # Check if in zone
        in_zone_price = last['low'] <= entry_high and last['high'] >= entry_low
        print(f"\n🔍 ENTRY ZONE CHECK")
        print(f"Current Low:  ${last['low']:.4f} <= ${entry_high:.4f} (Entry High): {last['low'] <= entry_high} {'✅' if last['low'] <= entry_high else '❌'}")
        print(f"Current High: ${last['high']:.4f} >= ${entry_low:.4f} (Entry Low):  {last['high'] >= entry_low} {'✅' if last['high'] >= entry_low else '❌'}")
        print(f"→ IN ZONE (Price Only):  {in_zone_price} {'🟢' if in_zone_price else '⚪'}")
        print(f"→ IN ZONE (With Bias):   {bullish and in_zone_price} {'🟢' if bullish and in_zone_price else '⚪'}")
        
    elif bearish and resistance:
        entry_low = resistance - last['atr'] * 0.5
        entry_high = resistance
        tp = last['close'] - last['atr'] * TP_ATR_MULT
        sl = last['close'] + last['atr'] * SL_ATR_MULT
        direction = "SHORT"
        
        print(f"Direction:    {direction} 📉")
        print(f"Entry Low:    ${entry_low:.4f}")
        print(f"Entry High:   ${entry_high:.4f}")
        print(f"Stop Loss:    ${sl:.4f}")
        print(f"Take Profit:  ${tp:.4f}")
        
        # Check if in zone
        in_zone_price = last['low'] <= entry_high and last['high'] >= entry_low
        print(f"\n🔍 ENTRY ZONE CHECK")
        print(f"Current Low:  ${last['low']:.4f} <= ${entry_high:.4f} (Entry High): {last['low'] <= entry_high} {'✅' if last['low'] <= entry_high else '❌'}")
        print(f"Current High: ${last['high']:.4f} >= ${entry_low:.4f} (Entry Low):  {last['high'] >= entry_low} {'✅' if last['high'] >= entry_low else '❌'}")
        print(f"→ IN ZONE (Price Only):  {in_zone_price} {'🟢' if in_zone_price else '⚪'}")
        print(f"→ IN ZONE (With Bias):   {bearish and in_zone_price} {'🟢' if bearish and in_zone_price else '⚪'}")
        
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
        
        # Risk management untuk leveraged trading
        max_margin_per_trade = BALANCE * MAX_RISK / 100  # $10 untuk 1% risk
        
        # Position size berdasarkan margin yang tersedia dan leverage
        max_position_value = max_margin_per_trade * suggest_lev
        pos_size = max_position_value / last['close']  # Quantity dalam coins
        position_value_usd = pos_size * last['close']  # Nilai posisi dalam USD
        
        # Verifikasi margin yang digunakan
        actual_margin = position_value_usd / suggest_lev
        sl_percent = sl_distance / last['close'] * 100
        rr_ratio = TP_ATR_MULT / SL_ATR_MULT
        
        print(f"\n💰 RISK MANAGEMENT")
        print("-" * 70)
        print(f"SL Distance:  ${sl_distance:.4f}")
        print(f"SL Percent:   {sl_percent:.2f}%")
        print(f"Raw Leverage: {raw_lev:.2f}x")
        print(f"Suggest Lev:  {suggest_lev}x ({lev_mode})")
        print(f"Risk Amount:  ${risk_amount:.2f}")
        print(f"Position Size: {pos_size:.3f}")
        print(f"R:R Ratio:    1:{rr_ratio:.2f}")
        
    else:
        print("⚪ No setup (Neutral or missing S/R)")
        if not bullish and not bearish:
            print("   Reason: Market is NEUTRAL")
        elif bullish and not support:
            print("   Reason: BULLISH but no Support found")
        elif bearish and not resistance:
            print("   Reason: BEARISH but no Resistance found")
    
    print("\n" + "=" * 70)
    print("✅ Debug completed!")
    print("=" * 70)

if __name__ == "__main__":
    import sys
    
    # Default symbol
    symbol = "XRPUSDT"
    
    # Allow command line argument
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        if not symbol.endswith('USDT'):
            symbol += 'USDT'
    
    debug_symbol(symbol)
