#!/usr/bin/env python3
"""
Fix dashboard cache and browser issues
"""
import os
import time

def clear_browser_cache_instructions():
    print("🧹 CLEAR BROWSER CACHE")
    print("-" * 40)
    print("1. Open browser and go to http://localhost:5000")
    print("2. Press Ctrl+Shift+R (or Cmd+Shift+R on Mac) to hard refresh")
    print("3. Or press F12 → Right-click refresh button → 'Empty Cache and Hard Reload'")
    print("4. Or go to Settings → Privacy → Clear browsing data → Cached images and files")

def check_dashboard_status():
    print("📊 DASHBOARD STATUS CHECK")
    print("-" * 40)
    
    import requests
    try:
        response = requests.get('http://localhost:5000/')
        if response.status_code == 200:
            print("✅ Dashboard is running at http://localhost:5000")
        else:
            print(f"❌ Dashboard error: {response.status_code}")
    except:
        print("❌ Dashboard is not running!")
        print("   Run: python dashboard_app.py")

def test_specific_features():
    print("\n🧪 FEATURE TEST")
    print("-" * 40)
    
    import requests
    
    # Test indicator performance
    try:
        response = requests.get('http://localhost:5000/api/indicator-performance?mode=dry-run&days=30', timeout=10)
        if response.status_code == 200 and response.json().get('success'):
            print("✅ Indicator Performance API: Working")
        else:
            print("❌ Indicator Performance API: Failed")
    except Exception as e:
        print(f"❌ Indicator Performance API: Error - {e}")
    
    # Test pair performance
    try:
        response = requests.get('http://localhost:5000/api/pair-performance?mode=dry-run&days=30', timeout=10)
        if response.status_code == 200 and response.json().get('success'):
            print("✅ Pair Performance API: Working")
        else:
            print("❌ Pair Performance API: Failed")
    except Exception as e:
        print(f"❌ Pair Performance API: Error - {e}")

def browser_troubleshooting_steps():
    print("\n🔧 BROWSER TROUBLESHOOTING")
    print("-" * 40)
    print("If still showing 'Failed to load', try these steps:")
    print()
    print("1. HARD REFRESH:")
    print("   - Press Ctrl+Shift+R (Windows/Linux)")
    print("   - Press Cmd+Shift+R (Mac)")
    print()
    print("2. CHECK BROWSER CONSOLE:")
    print("   - Press F12 to open Developer Tools")
    print("   - Click 'Console' tab")
    print("   - Look for red error messages")
    print("   - Try clicking the features again")
    print()
    print("3. DISABLE BROWSER EXTENSIONS:")
    print("   - Try in Incognito/Private mode")
    print("   - Or disable ad blockers temporarily")
    print()
    print("4. TRY DIFFERENT BROWSER:")
    print("   - Chrome, Firefox, Edge, Safari")
    print()
    print("5. CHECK NETWORK TAB:")
    print("   - F12 → Network tab")
    print("   - Click feature → Look for failed requests")
    print("   - Check if API calls return 200 status")

def create_test_html():
    print("\n📄 CREATING TEST HTML")
    print("-" * 40)
    
    test_html = """<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Feature Test</title>
    <script>
        async function testIndicatorPerformance() {
            try {
                console.log('Testing Indicator Performance...');
                const response = await fetch('/api/indicator-performance?mode=dry-run&days=30');
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('indicator-result').innerHTML = 
                        `✅ SUCCESS: ${Object.keys(data.indicators).length} indicators loaded`;
                    console.log('Indicator data:', data);
                } else {
                    document.getElementById('indicator-result').innerHTML = 
                        `❌ ERROR: ${data.error}`;
                }
            } catch (error) {
                document.getElementById('indicator-result').innerHTML = 
                    `❌ EXCEPTION: ${error.message}`;
                console.error('Indicator error:', error);
            }
        }
        
        async function testPairPerformance() {
            try {
                console.log('Testing Pair Performance...');
                const response = await fetch('/api/pair-performance?mode=dry-run&days=30');
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('pair-result').innerHTML = 
                        `✅ SUCCESS: ${Object.keys(data.pairs).length} pairs loaded`;
                    console.log('Pair data:', data);
                } else {
                    document.getElementById('pair-result').innerHTML = 
                        `❌ ERROR: ${data.error}`;
                }
            } catch (error) {
                document.getElementById('pair-result').innerHTML = 
                    `❌ EXCEPTION: ${error.message}`;
                console.error('Pair error:', error);
            }
        }
    </script>
</head>
<body style="font-family: Arial; padding: 20px; background: #1a1a1a; color: white;">
    <h1>🧪 Dashboard Feature Test</h1>
    
    <div style="margin: 20px 0;">
        <button onclick="testIndicatorPerformance()" style="padding: 10px 20px; margin: 5px; background: #ff6b35; color: white; border: none; border-radius: 5px; cursor: pointer;">
            Test Indicator Performance
        </button>
        <div id="indicator-result" style="margin: 10px 0; padding: 10px; background: #333; border-radius: 5px;">
            Click button to test...
        </div>
    </div>
    
    <div style="margin: 20px 0;">
        <button onclick="testPairPerformance()" style="padding: 10px 20px; margin: 5px; background: #06d6a0; color: white; border: none; border-radius: 5px; cursor: pointer;">
            Test Pair Performance
        </button>
        <div id="pair-result" style="margin: 10px 0; padding: 10px; background: #333; border-radius: 5px;">
            Click button to test...
        </div>
    </div>
    
    <div style="margin: 20px 0; padding: 15px; background: #444; border-radius: 5px;">
        <h3>📋 Instructions:</h3>
        <ol>
            <li>Open browser console (F12)</li>
            <li>Click the test buttons above</li>
            <li>Check console for detailed logs</li>
            <li>If tests pass but main dashboard fails, it's a UI issue</li>
        </ol>
    </div>
    
    <div style="margin: 20px 0;">
        <a href="/" style="color: #06d6a0;">← Back to Main Dashboard</a>
    </div>
</body>
</html>"""
    
    with open('templates/test.html', 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print("✅ Test page created: http://localhost:5000/test")

if __name__ == "__main__":
    print("🔧 DASHBOARD CACHE & BROWSER FIX")
    print("=" * 50)
    
    check_dashboard_status()
    test_specific_features()
    create_test_html()
    clear_browser_cache_instructions()
    browser_troubleshooting_steps()
    
    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("1. Visit: http://localhost:5000/test")
    print("2. Test the features there first")
    print("3. If test page works, clear browser cache")
    print("4. Then try main dashboard again")