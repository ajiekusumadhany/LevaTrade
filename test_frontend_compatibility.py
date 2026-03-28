#!/usr/bin/env python3
"""
Test frontend compatibility for dashboard features
"""
import requests
import json

def test_indicator_frontend_compatibility():
    print("🔍 Testing Indicator Performance Frontend Compatibility...")
    
    response = requests.get('http://localhost:5000/api/indicator-performance?mode=dry-run&days=30')
    data = response.json()
    
    if not data.get('success'):
        print(f"❌ API failed: {data.get('error')}")
        return
    
    # Check required fields for frontend
    required_fields = [
        'indicators',
        'days_analyzed', 
        'total_trades_analyzed'
    ]
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return
    
    # Check indicator structure
    if data['indicators']:
        first_indicator = list(data['indicators'].values())[0]
        required_indicator_fields = [
            'description',
            'overall_accuracy',
            'total_trades',
            'avg_pnl'
        ]
        
        missing_indicator_fields = [field for field in required_indicator_fields if field not in first_indicator]
        if missing_indicator_fields:
            print(f"❌ Missing indicator fields: {missing_indicator_fields}")
            return
    
    print("✅ Indicator Performance frontend compatibility: PASSED")
    print(f"   - Indicators: {len(data['indicators'])}")
    print(f"   - Days analyzed: {data['days_analyzed']}")
    print(f"   - Total trades: {data['total_trades_analyzed']}")

def test_pair_frontend_compatibility():
    print("\n🔍 Testing Pair Performance Frontend Compatibility...")
    
    response = requests.get('http://localhost:5000/api/pair-performance?mode=dry-run&days=30')
    data = response.json()
    
    if not data.get('success'):
        print(f"❌ API failed: {data.get('error')}")
        return
    
    # Check required fields for frontend
    required_fields = [
        'pairs',
        'days_analyzed'
    ]
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return
    
    # Check pair structure
    if data['pairs']:
        first_pair = list(data['pairs'].values())[0]
        required_pair_fields = [
            'current_volume_category',
            'current_market_cap_category',
            'current_volume_24h',
            'total_pnl',
            'win_rate'
        ]
        
        missing_pair_fields = [field for field in required_pair_fields if field not in first_pair]
        if missing_pair_fields:
            print(f"❌ Missing pair fields: {missing_pair_fields}")
            return
        
        # Check category structure
        vol_cat = first_pair['current_volume_category']
        if not isinstance(vol_cat, dict) or 'category' not in vol_cat or 'color' not in vol_cat:
            print("❌ Invalid volume category structure")
            return
    
    print("✅ Pair Performance frontend compatibility: PASSED")
    print(f"   - Pairs: {len(data['pairs'])}")
    print(f"   - Days analyzed: {data['days_analyzed']}")

def test_browser_access():
    print("\n🌐 Testing Browser Access...")
    
    try:
        # Test main dashboard
        response = requests.get('http://localhost:5000/')
        if response.status_code == 200:
            print("✅ Main dashboard: Accessible")
        else:
            print(f"❌ Main dashboard: Status {response.status_code}")
            
        # Test if HTML contains the required elements
        html_content = response.text
        required_elements = [
            'indicator-performance',
            'pair-performance', 
            'showIndicatorPerformance',
            'showPairPerformance'
        ]
        
        missing_elements = [elem for elem in required_elements if elem not in html_content]
        if missing_elements:
            print(f"⚠️ Missing HTML elements: {missing_elements}")
        else:
            print("✅ All required HTML elements present")
            
    except Exception as e:
        print(f"❌ Browser access test failed: {e}")

if __name__ == "__main__":
    print("🧪 FRONTEND COMPATIBILITY TEST")
    print("=" * 50)
    
    test_indicator_frontend_compatibility()
    test_pair_frontend_compatibility()
    test_browser_access()
    
    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("1. Open browser: http://localhost:5000")
    print("2. Click 'Indicator Performance' in sidebar")
    print("3. Click 'Pair Performance' in sidebar")
    print("4. Check browser console (F12) for any JavaScript errors")