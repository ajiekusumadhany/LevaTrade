"""
Test koneksi API Bybit MAINNET (hanya untuk cek balance, tidak trading)
"""
import os
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

load_dotenv()

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

print(f"API Key: {BYBIT_API_KEY}")
print(f"Testing MAINNET connection...")

try:
    # Test dengan MAINNET
    session = HTTP(
        testnet=False,  # MAINNET
        api_key=BYBIT_API_KEY,
        api_secret=BYBIT_API_SECRET
    )
    
    # Test server time
    response = session.get_server_time()
    print(f"✅ Server time: OK")
    
    # Test wallet balance
    try:
        response = session.get_wallet_balance(accountType="UNIFIED")
        if response['retCode'] == 0:
            print("✅ MAINNET Balance:")
            print("-" * 40)
            
            coins = response['result']['list'][0]['coin']
            total_equity = float(response['result']['list'][0]['totalEquity'])
            
            print(f"💰 Total Equity: ${total_equity:.2f}")
            
            # Cari USDT
            usdt_balance = 0
            for coin in coins:
                if coin['coin'] == 'USDT':
                    balance = float(coin['walletBalance'])
                    available = float(coin['availableToWithdraw'])
                    print(f"💎 USDT Balance: ${balance:.2f} (Available: ${available:.2f})")
                    usdt_balance = balance
                    break
            
            if usdt_balance == 0:
                print("⚠️  No USDT balance found")
        else:
            print(f"❌ Wallet error: {response['retMsg']}")
            
    except Exception as e:
        print(f"❌ Wallet error: {e}")

except Exception as e:
    print(f"❌ Connection error: {e}")

print("\n" + "="*50)
print("📝 CATATAN:")
print("- Jika API key ini untuk MAINNET, Anda perlu buat API key terpisah untuk TESTNET")
print("- Untuk trading demo, gunakan TESTNET API key")
print("- Untuk data market, bisa pakai MAINNET (read-only)")
print("- Buka https://testnet.bybit.com untuk buat testnet API key")