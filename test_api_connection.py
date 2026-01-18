"""
Test koneksi API Bybit testnet
"""
import os
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

load_dotenv()

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

print(f"API Key: {BYBIT_API_KEY}")
print(f"API Secret: {BYBIT_API_SECRET[:10]}...")

# Test koneksi
try:
    # Test dengan testnet
    session = HTTP(
        testnet=True,
        api_key=BYBIT_API_KEY,
        api_secret=BYBIT_API_SECRET
    )
    
    print("\n🔍 Testing API connection...")
    
    # Test 1: Get server time (public endpoint)
    response = session.get_server_time()
    print(f"✅ Server time: {response}")
    
    # Test 2: Get account info (private endpoint)
    try:
        response = session.get_wallet_balance(accountType="UNIFIED")
        print(f"✅ Wallet response: {response}")
    except Exception as e:
        print(f"❌ Wallet error: {e}")
        
        # Try alternative method
        try:
            response = session.get_coin_balance(accountType="UNIFIED", coin="USDT")
            print(f"✅ USDT balance response: {response}")
        except Exception as e2:
            print(f"❌ USDT balance error: {e2}")

except Exception as e:
    print(f"❌ Connection error: {e}")