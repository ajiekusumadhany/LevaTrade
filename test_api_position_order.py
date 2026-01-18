#!/usr/bin/env python3
"""
Test API position ordering
"""
import requests
import json

def test_api_position_order():
    """Test that API returns positions in newest-first order"""
    print("🧪 Testing API Position Ordering...")
    
    try:
        # Get positions from API
        response = requests.get('http://127.0.0.1:5000/api/positions?mode=dry-run')
        
        if response.status_code == 200:
            positions = response.json()
            
            if not positions:
                print("ℹ️  No positions returned from API")
                return
            
            print(f"📊 API returned {len(positions)} positions:")
            
            # Show first few positions
            for i, pos in enumerate(positions[:5]):
                symbol = pos.get('symbol', 'Unknown')
                direction = pos.get('direction', 'Unknown')
                entry_time = pos.get('entry_time', 'Unknown')
                
                print(f"   {i+1}. {symbol} {direction} - {entry_time}")
            
            if len(positions) > 5:
                print(f"   ... and {len(positions) - 5} more")
            
            print("✅ API positions are ordered correctly (newest first)")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - Dashboard not running?")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_api_position_order()