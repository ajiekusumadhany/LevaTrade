"""
Script untuk test koneksi Bybit Testnet
"""
import os
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

load_dotenv()

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

print("🔧 Testing Bybit Testnet Connection...")
print(f"API Key: {BYBIT_API_KEY[:10]}...")
print("-" * 50)

# Initialize session
session = HTTP(
    testnet=True,
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)

# Test 1: Get server time
try:
    response = session.get_server_time()
    print("✅ Server Time:", response)
except Exception as e:
    print("❌ Server Time Error:", e)

# Test 2: Get account info (requires API key)
try:
    response = session.get_wallet_balance(accountType="UNIFIED")
    print("✅ Wallet Balance:", response)
except Exception as e:
    print("❌ Wallet Balance Error:", e)

# Test 3: Get market data (public, no API key needed)
try:
    response = session.get_kline(
        category="linear",
        symbol="BTCUSDT",
        interval="240",
        limit=5
    )
    if response['retCode'] == 0:
        print("✅ Market Data (BTCUSDT 4H):")
        for candle in response['result']['list'][:3]:
            print(f"   Time: {candle[0]}, Close: {candle[4]}")
    else:
        print("❌ Market Data Error:", response['retMsg'])
except Exception as e:
    print("❌ Market Data Error:", e)

# Test 4: Get tickers
try:
    response = session.get_tickers(category="linear", symbol="BTCUSDT")
    if response['retCode'] == 0:
        ticker = response['result']['list'][0]
        print(f"✅ Ticker BTCUSDT: ${ticker['lastPrice']}")
    else:
        print("❌ Ticker Error:", response['retMsg'])
except Exception as e:
    print("❌ Ticker Error:", e)

print("-" * 50)
print("✅ Test selesai!")
