"""
Test dashboard API endpoints
"""
import requests
import json

def test_api():
    base_url = "http://localhost:5000"
    
    try:
        # Test positions endpoint
        print("🔍 Testing /api/positions...")
        response = requests.get(f"{base_url}/api/positions")
        if response.status_code == 200:
            positions = response.json()
            print(f"✅ Found {len(positions)} positions")
            for pos in positions:
                print(f"   {pos['symbol']}: {pos['direction']} | Current: ${pos['current_price']:.4f} | PnL: ${pos['unrealized_pnl']:.2f}")
        else:
            print(f"❌ Error: {response.status_code}")
        
        # Test performance endpoint
        print("\n🔍 Testing /api/performance...")
        response = requests.get(f"{base_url}/api/performance")
        if response.status_code == 200:
            metrics = response.json()
            print(f"✅ Balance: ${metrics['balance']:.2f}")
            print(f"✅ Total PnL: ${metrics['total_pnl']:.2f}")
            print(f"✅ Win Rate: {metrics['win_rate']:.1f}%")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure dashboard is running on http://localhost:5000")

if __name__ == "__main__":
    test_api()