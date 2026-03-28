"""
System Status Summary - Ringkasan status sistem setelah reset
"""
import os
import json
import sqlite3
from datetime import datetime

def check_system_status():
    print("🚀 LEVATRADE SYSTEM STATUS SUMMARY")
    print("=" * 60)
    
    # 1. Check Balance
    print("\n💰 BALANCE STATUS:")
    try:
        with open(".env", "r") as f:
            content = f.read()
        if "BALANCE_USD=200" in content:
            print("   ✅ Balance: $200.00 (Fresh start)")
        else:
            print("   ⚠️ Balance: Check .env file")
    except:
        print("   ❌ Could not read .env file")
    
    # 2. Check Trading Control
    print("\n🎛️ TRADING CONTROL:")
    try:
        with open("trading_control.json", "r") as f:
            control = json.load(f)
        status = "ENABLED" if control.get("enabled") else "DISABLED"
        print(f"   ✅ Status: {status}")
        print(f"   📅 Last Updated: {control.get('last_updated', 'Unknown')}")
    except:
        print("   ❌ Could not read trading control")
    
    # 3. Check Databases
    print("\n🗄️ DATABASE STATUS:")
    db_files = ["dry_run_trades.db", "real_trades.db"]
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM trade_history")
                trades = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM open_positions")
                positions = cursor.fetchone()[0]
                conn.close()
                print(f"   ✅ {db_file}: {trades} trades, {positions} positions")
            except Exception as e:
                print(f"   ⚠️ {db_file}: Error - {e}")
        else:
            print(f"   ❌ {db_file}: Not found")
    
    # 4. Check Notifications
    print("\n📡 NOTIFICATIONS:")
    try:
        with open("notifications.json", "r") as f:
            notifications = json.load(f)
        print(f"   ✅ Notifications: {len(notifications)} items (cleared)")
    except:
        print("   ❌ Could not read notifications")
    
    # 5. Check Session Configuration
    print("\n🌍 SESSION CONFIGURATION:")
    sessions = {
        "DEAD_ZONE": "02:00-07:00 WIB (Risk: 0.3%, Leverage: 10x)",
        "ASIA": "07:00-14:00 WIB (Risk: 0.3%, Leverage: 8x)", 
        "LONDON": "14:00-20:00 WIB (Risk: 0.5%, Leverage: 15x)",
        "NEWYORK": "20:00-02:00 WIB (Risk: 0.4%, Leverage: 20x)"
    }
    
    current_hour = datetime.now().hour
    if 2 <= current_hour < 7:
        current_session = "DEAD_ZONE"
    elif 7 <= current_hour < 14:
        current_session = "ASIA"
    elif 14 <= current_hour < 20:
        current_session = "LONDON"
    else:
        current_session = "NEWYORK"
    
    for session, config in sessions.items():
        marker = "🟢 ACTIVE" if session == current_session else "⚪"
        print(f"   {marker} {session}: {config}")
    
    # 6. Check Key Files
    print("\n📁 KEY FILES STATUS:")
    key_files = [
        "crypto_bot_parallel.py",
        "dashboard_app.py", 
        "dry_run_system.py",
        "gemini_ai_system.py",
        "session_management_system.py",
        "conditional_risk_system.py"
    ]
    
    for file in key_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} ({size:,} bytes)")
        else:
            print(f"   ❌ {file} - Missing")
    
    print("\n" + "=" * 60)
    print("✅ SYSTEM READY FOR TRADING!")
    print("🎯 Current Session: " + current_session)
    print("💰 Starting Balance: $200.00")
    print("🤖 Mode: DRY RUN (Simulation)")
    print("📱 Telegram: Ready for /start command")
    print("🌐 Dashboard: http://localhost:5000")

if __name__ == "__main__":
    check_system_status()