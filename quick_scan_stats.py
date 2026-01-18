"""
Quick scan untuk lihat statistik market
"""
import os
from pybit.unified_trading import HTTP
import pandas as pd
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import threading

load_dotenv()

session = HTTP(testnet=False, api_key='', api_secret='')
api_lock = threading.Lock()

EMA_FAST = 21
EMA_SLOW = 55
RSI_LENGTH = 14

def get_all_usdt_symbols():
    try:
        with api_lock:
            response = session.get_tickers(category="linear")
        if response['retCode'] == 0:
            tickers = response['result']['list']
            usdt_pairs = [
                {
                    'symbol': t['symbol'],
                    'turnover': float(t['turnover24h'])
                }
                for t in tickers 
                if t['symbol'].endswith('USDT') and float(t['volume24h']) > 0
            ]
            # Sort by volume
            usdt_pairs.sort(key=lambda x: x['turnover'], reverse=True)
            return [p['symbol'] for p in usdt_pairs[:100]]  # Top 100
        return []
    except:
        return []

def quick_check(symbol):
    try:
        with api_lock:
            response = session.get_kline(category="linear", symbol=symbol, interval="240", limit=100)
        
        if response['retCode'] != 0:
            return None
        
        data = response['result']['list']
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        df = df.astype({'close': float, 'high': float, 'low': float})
        df = df.iloc[::-1].reset_index(drop=True)
        
        if len(df) < 60:
            return None
        
        # Quick indicators
        df['ema_fast'] = df['close'].ewm(span=EMA_FAST, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=EMA_SLOW, adjust=False).mean()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=RSI_LENGTH).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_LENGTH).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        ema_fast_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_slow_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_fast_12 - ema_slow_26
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # ATR for entry zone
        high = df['high']
        low = df['low']
        close = df['close']
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()
        
        last = df.iloc[-1]
        
        ema_bull = last['ema_fast'] > last['ema_slow']
        macd_bull = last['macd'] > last['signal']
        rsi_bull = last['rsi'] > 55
        
        ema_bear = last['ema_fast'] < last['ema_slow']
        macd_bear = last['macd'] < last['signal']
        rsi_bear = last['rsi'] < 45
        
        bullish = ema_bull and macd_bull and rsi_bull
        bearish = ema_bear and macd_bear and rsi_bear
        
        # Check entry zone (simplified - just check if has support/resistance)
        in_entry_zone = False
        if bullish or bearish:
            # Simplified: assume has S/R, check if price near it
            # For real check, need pivot calculation
            in_entry_zone = True  # Placeholder
        
        return {
            'symbol': symbol,
            'rsi': last['rsi'],
            'ema_bull': ema_bull,
            'macd_bull': macd_bull,
            'rsi_bull': rsi_bull,
            'ema_bear': ema_bear,
            'macd_bear': macd_bear,
            'rsi_bear': rsi_bear,
            'bullish': bullish,
            'bearish': bearish,
            'in_entry': in_entry_zone
        }
    except:
        return None

print("🔍 Quick Market Scan - Top 100 Volume...")
print("=" * 70)

symbols = get_all_usdt_symbols()
print(f"📊 Scanning top {len(symbols)} volume symbols...\n")

with ThreadPoolExecutor(max_workers=20) as executor:
    results = list(executor.map(quick_check, symbols))

results = [r for r in results if r is not None]

bullish_count = sum(1 for r in results if r['bullish'])
bearish_count = sum(1 for r in results if r['bearish'])
neutral_count = len(results) - bullish_count - bearish_count

print(f"📈 MARKET STATISTICS (Top {len(results)} Volume)")
print("-" * 70)
print(f"Total Scanned:  {len(results)}")
print(f"Bullish Setup:  {bullish_count} ({bullish_count/len(results)*100:.1f}%)")
print(f"Bearish Setup:  {bearish_count} ({bearish_count/len(results)*100:.1f}%)")
print(f"Neutral:        {neutral_count} ({neutral_count/len(results)*100:.1f}%)")
print()
print(f"💡 Note: Setup = bias detected (bullish/bearish)")
print(f"   Signal = setup + price in entry zone")

if bullish_count > 0:
    print(f"\n📈 BULLISH SETUPS ({bullish_count}):")
    for r in [r for r in results if r['bullish']][:20]:
        print(f"   {r['symbol']:20s} RSI: {r['rsi']:5.1f}")

if bearish_count > 0:
    print(f"\n📉 BEARISH SETUPS ({bearish_count}):")
    for r in [r for r in results if r['bearish']][:20]:
        print(f"   {r['symbol']:20s} RSI: {r['rsi']:5.1f}")

# Show near signals
print(f"\n🔍 NEAR BULLISH (2/3 conditions):")
near_bull = [r for r in results if sum([r['ema_bull'], r['macd_bull'], r['rsi_bull']]) == 2]
print(f"   Found: {len(near_bull)}")
for r in near_bull[:10]:
    missing = []
    if not r['ema_bull']: missing.append("EMA")
    if not r['macd_bull']: missing.append("MACD")
    if not r['rsi_bull']: missing.append("RSI")
    print(f"   {r['symbol']:20s} RSI: {r['rsi']:5.1f} | Missing: {', '.join(missing)}")

print(f"\n🔍 NEAR BEARISH (2/3 conditions):")
near_bear = [r for r in results if sum([r['ema_bear'], r['macd_bear'], r['rsi_bear']]) == 2]
print(f"   Found: {len(near_bear)}")
for r in near_bear[:10]:
    missing = []
    if not r['ema_bear']: missing.append("EMA")
    if not r['macd_bear']: missing.append("MACD")
    if not r['rsi_bear']: missing.append("RSI")
    print(f"   {r['symbol']:20s} RSI: {r['rsi']:5.1f} | Missing: {', '.join(missing)}")

print("\n" + "=" * 70)
print("✅ Scan completed!")
print()
print("💡 Kesimpulan:")
print(f"   - Setup terdeteksi: {bullish_count + bearish_count} dari {len(results)}")
print(f"   - Untuk jadi SIGNAL, perlu masuk entry zone juga")
print(f"   - Bot akan alert saat setup + entry zone aktif")
