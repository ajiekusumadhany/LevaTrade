"""
Test performance parallel vs sequential scanning
"""
import os
import time
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import threading

load_dotenv()

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')

session = HTTP(
    testnet=True,
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)

api_lock = threading.Lock()

def get_top_symbols(limit=100):
    """Get top volume symbols"""
    try:
        with api_lock:
            response = session.get_tickers(category="linear")
        
        if response['retCode'] == 0:
            tickers = response['result']['list']
            usdt_pairs = [
                t['symbol'] for t in tickers 
                if t['symbol'].endswith('USDT') and float(t['volume24h']) > 0
            ]
            return usdt_pairs[:limit]
        return []
    except:
        return []

def fetch_kline(symbol):
    """Fetch kline data for one symbol"""
    try:
        with api_lock:
            response = session.get_kline(
                category="linear",
                symbol=symbol,
                interval="240",
                limit=50
            )
        return symbol, response['retCode'] == 0
    except:
        return symbol, False

def test_sequential(symbols):
    """Test sequential scanning"""
    print("\n📊 Testing SEQUENTIAL scanning...")
    start = time.time()
    
    success = 0
    for symbol in symbols:
        _, ok = fetch_kline(symbol)
        if ok:
            success += 1
    
    elapsed = time.time() - start
    print(f"✅ Sequential: {success}/{len(symbols)} symbols in {elapsed:.2f}s")
    print(f"   Speed: {len(symbols)/elapsed:.2f} symbols/sec")
    return elapsed

def test_parallel(symbols, workers=20):
    """Test parallel scanning"""
    print(f"\n⚡ Testing PARALLEL scanning ({workers} workers)...")
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(fetch_kline, symbols))
    
    success = sum(1 for _, ok in results if ok)
    elapsed = time.time() - start
    print(f"✅ Parallel: {success}/{len(symbols)} symbols in {elapsed:.2f}s")
    print(f"   Speed: {len(symbols)/elapsed:.2f} symbols/sec")
    return elapsed

if __name__ == "__main__":
    print("🔧 Performance Test - Parallel vs Sequential")
    print("=" * 50)
    
    # Get symbols
    print("\n📊 Loading top volume symbols...")
    symbols = get_top_symbols(100)
    
    if not symbols:
        print("❌ Failed to load symbols")
        exit(1)
    
    print(f"✅ Loaded {len(symbols)} symbols")
    print(f"   Top 10: {', '.join(symbols[:10])}")
    
    # Test with smaller sample first
    test_symbols = symbols[:20]
    print(f"\n🧪 Testing with {len(test_symbols)} symbols...")
    print("=" * 50)
    
    # Sequential test
    seq_time = test_sequential(test_symbols)
    
    # Parallel test
    par_time = test_parallel(test_symbols, workers=10)
    
    # Results
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"   Sequential: {seq_time:.2f}s")
    print(f"   Parallel:   {par_time:.2f}s")
    print(f"   Speedup:    {seq_time/par_time:.2f}x faster")
    
    # Estimate for 100 symbols
    print(f"\n💡 Estimated time for 100 symbols:")
    print(f"   Sequential: ~{seq_time * 100 / len(test_symbols):.0f}s ({seq_time * 100 / len(test_symbols) / 60:.1f} minutes)")
    print(f"   Parallel:   ~{par_time * 100 / len(test_symbols):.0f}s ({par_time * 100 / len(test_symbols) / 60:.1f} minutes)")
    
    print("\n✅ Test completed!")
