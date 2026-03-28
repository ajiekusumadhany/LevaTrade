#!/usr/bin/env python3
"""
Simulate browser requests to test dashboard features
"""
import requests
import json
import time

def simulate_indicator_performance_click():
    print("🖱️ Simulating 'Indicator Performance' click...")
    
    # Simulate the exact request that browser makes
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'http://localhost:5000/'
    }
    
    try:
        response = requests.get(
            'http://localhost:5000/api/indicator-performance?mode=dry-run&days=30',
            headers=headers,
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Data loaded successfully")
                print(f"   📊 Indicators: {len(data.get('indicators', {}))}")
                print(f"   📈 Total Trades: {data.get('total_trades_analyzed', 0)}")
                
                # Check if data structure matches frontend expectations
                if 'indicators' in data and 'days_analyzed' in data:
                    print("   ✅ Data structure compatible with frontend")
                else:
                    print("   ❌ Data structure incompatible")
            else:
                print(f"   ❌ API returned error: {data.get('error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timeout")
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection error - Dashboard not running?")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")

def simulate_pair_performance_click():
    print("\n🖱️ Simulating 'Pair Performance' click...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'http://localhost:5000/'
    }
    
    try:
        response = requests.get(
            'http://localhost:5000/api/pair-performance?mode=dry-run&days=30',
            headers=headers,
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {response.elapsed.total_seconds():.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Data loaded successfully")
                print(f"   📊 Pairs: {len(data.get('pairs', {}))}")
                print(f"   📈 Categories: {len(data.get('categories', {}))}")
                
                # Check if data structure matches frontend expectations
                if 'pairs' in data and 'days_analyzed' in data:
                    print("   ✅ Data structure compatible with frontend")
                    
                    # Check first pair structure
                    if data['pairs']:
                        first_pair = list(data['pairs'].values())[0]
                        required_fields = ['current_volume_category', 'current_market_cap_category']
                        if all(field in first_pair for field in required_fields):
                            print("   ✅ Pair data structure complete")
                        else:
                            print("   ⚠️ Some pair fields missing")
                else:
                    print("   ❌ Data structure incompatible")
            else:
                print(f"   ❌ API returned error: {data.get('error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timeout")
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection error - Dashboard not running?")
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")

def check_dashboard_health():
    print("🏥 Checking Dashboard Health...")
    
    try:
        # Check main page
        response = requests.get('http://localhost:5000/', timeout=5)
        if response.status_code == 200:
            print("   ✅ Main dashboard accessible")
        else:
            print(f"   ❌ Main dashboard error: {response.status_code}")
            
        # Check basic API
        response = requests.get('http://localhost:5000/api/trading/status', timeout=5)
        if response.status_code == 200:
            print("   ✅ Basic API working")
        else:
            print(f"   ❌ Basic API error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Dashboard health check failed: {e}")

if __name__ == "__main__":
    print("🧪 BROWSER SIMULATION TEST")
    print("=" * 50)
    
    check_dashboard_health()
    time.sleep(1)
    
    simulate_indicator_performance_click()
    time.sleep(1)
    
    simulate_pair_performance_click()
    
    print("\n" + "=" * 50)
    print("🎯 If all tests pass but browser still shows 'Failed to load',")
    print("   the issue might be in JavaScript execution or DOM manipulation.")
    print("   Check browser console (F12) for JavaScript errors.")