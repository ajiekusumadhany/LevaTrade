#!/usr/bin/env python3
"""
Debug dashboard loading issues
"""
import requests
import json
import time

def debug_indicator_performance():
    print("🔍 DEBUGGING INDICATOR PERFORMANCE")
    print("-" * 40)
    
    try:
        start_time = time.time()
        response = requests.get('http://localhost:5000/api/indicator-performance?mode=dry-run&days=30')
        end_time = time.time()
        
        print(f"⏱️ Response time: {end_time - start_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        print(f"📏 Response size: {len(response.content)} bytes")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check success
            print(f"✅ Success: {data.get('success', False)}")
            
            if data.get('success'):
                # Check required fields
                required_fields = ['indicators', 'days_analyzed', 'total_trades_analyzed']
                for field in required_fields:
                    if field in data:
                        print(f"✅ {field}: Present")
                        if field == 'indicators':
                            print(f"   📊 Count: {len(data[field])}")
                        else:
                            print(f"   📊 Value: {data[field]}")
                    else:
                        print(f"❌ {field}: Missing")
                
                # Check indicator structure
                if data.get('indicators'):
                    first_indicator_key = list(data['indicators'].keys())[0]
                    first_indicator = data['indicators'][first_indicator_key]
                    
                    print(f"\n📋 First indicator ({first_indicator_key}):")
                    required_indicator_fields = ['description', 'overall_accuracy', 'total_trades', 'avg_pnl']
                    for field in required_indicator_fields:
                        if field in first_indicator:
                            print(f"   ✅ {field}: {first_indicator[field]}")
                        else:
                            print(f"   ❌ {field}: Missing")
                
                # Check if response is too large
                if len(response.content) > 100000:  # 100KB
                    print("⚠️ Response might be too large for frontend")
                
            else:
                print(f"❌ API Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - API too slow")
    except json.JSONDecodeError:
        print("❌ Invalid JSON response")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def debug_pair_performance():
    print("\n🔍 DEBUGGING PAIR PERFORMANCE")
    print("-" * 40)
    
    try:
        start_time = time.time()
        response = requests.get('http://localhost:5000/api/pair-performance?mode=dry-run&days=30')
        end_time = time.time()
        
        print(f"⏱️ Response time: {end_time - start_time:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        print(f"📏 Response size: {len(response.content)} bytes")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check success
            print(f"✅ Success: {data.get('success', False)}")
            
            if data.get('success'):
                # Check required fields
                required_fields = ['pairs', 'days_analyzed']
                for field in required_fields:
                    if field in data:
                        print(f"✅ {field}: Present")
                        if field == 'pairs':
                            print(f"   📊 Count: {len(data[field])}")
                        else:
                            print(f"   📊 Value: {data[field]}")
                    else:
                        print(f"❌ {field}: Missing")
                
                # Check pair structure
                if data.get('pairs'):
                    first_pair_key = list(data['pairs'].keys())[0]
                    first_pair = data['pairs'][first_pair_key]
                    
                    print(f"\n📋 First pair ({first_pair_key}):")
                    required_pair_fields = ['current_volume_category', 'current_market_cap_category', 'total_pnl', 'win_rate']
                    for field in required_pair_fields:
                        if field in first_pair:
                            value = first_pair[field]
                            if isinstance(value, dict):
                                print(f"   ✅ {field}: {value}")
                            else:
                                print(f"   ✅ {field}: {value}")
                        else:
                            print(f"   ❌ {field}: Missing")
                
                # Check if response is too large
                if len(response.content) > 100000:  # 100KB
                    print("⚠️ Response might be too large for frontend")
                
            else:
                print(f"❌ API Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - API too slow")
    except json.JSONDecodeError:
        print("❌ Invalid JSON response")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def check_dashboard_logs():
    print("\n📋 DASHBOARD LOGS CHECK")
    print("-" * 40)
    print("Check the dashboard console output for any Python errors.")
    print("Look for lines containing 'ERROR', 'Exception', or 'Traceback'.")

if __name__ == "__main__":
    print("🐛 DASHBOARD DEBUG SESSION")
    print("=" * 50)
    
    debug_indicator_performance()
    debug_pair_performance()
    check_dashboard_logs()
    
    print("\n" + "=" * 50)
    print("🎯 TROUBLESHOOTING STEPS:")
    print("1. If response time > 5 seconds: API is too slow")
    print("2. If response size > 100KB: Data might be too large")
    print("3. If any required fields missing: API structure issue")
    print("4. Check browser console (F12) for JavaScript errors")
    print("5. Try refreshing the page and clicking again")