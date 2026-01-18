"""
Script untuk cek balance USDT di akun Bybit MAINNET (real account)
"""
import os
from pybit.unified_trading import HTTP
from dotenv import load_dotenv

load_dotenv()

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

# Trading session (MAINNET - real account)
trading_session = HTTP(
    testnet=False,   # MAINNET - untuk real account
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET
)

def get_account_balance():
    """Get account balance"""
    try:
        response = trading_session.get_wallet_balance(accountType="UNIFIED")
        
        if response['retCode'] == 0:
            print("✅ Account Balance:")
            print("-" * 40)
            
            account_list = response['result']['list']
            if not account_list:
                print("⚠️  No account data found")
                return 0
            
            account = account_list[0]
            coins = account.get('coin', [])
            total_equity = float(account.get('totalEquity', '0') or '0')
            
            print(f"💰 Total Equity: ${total_equity:.2f}")
            print("\n📊 Coin Balances:")
            
            usdt_balance = 0
            for coin in coins:
                try:
                    balance = float(coin.get('walletBalance', '0') or '0')
                    available = float(coin.get('availableToWithdraw', '0') or '0')
                    if balance > 0:
                        print(f"   {coin['coin']}: ${balance:.2f} (Available: ${available:.2f})")
                    
                    if coin['coin'] == 'USDT':
                        usdt_balance = balance
                except (ValueError, TypeError) as e:
                    print(f"   {coin['coin']}: Error parsing balance - {e}")
            
            print(f"\n💎 USDT Balance: ${usdt_balance:.2f}")
            return usdt_balance
        else:
            print(f"❌ Error: {response['retMsg']}")
            return 0
    except Exception as e:
        print(f"❌ Exception: {e}")
        return 0

if __name__ == "__main__":
    balance = get_account_balance()