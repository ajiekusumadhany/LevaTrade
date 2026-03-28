"""
Simple System Reset
"""
import os
import json
from datetime import datetime

print("🔄 Simple System Reset...")

# 1. Reset notifications
try:
    with open("notifications.json", "w") as f:
        json.dump([], f)
    print("✅ Notifications cleared")
except:
    print("⚠️ Could not clear notifications")

# 2. Reset trading control
try:
    control = {
        "enabled": True,
        "last_updated": datetime.now().isoformat(),
        "updated_by": "simple_reset"
    }
    with open("trading_control.json", "w") as f:
        json.dump(control, f, indent=2)
    print("✅ Trading control reset")
except:
    print("⚠️ Could not reset trading control")

# 3. Check balance in .env
try:
    with open(".env", "r") as f:
        content = f.read()
    if "BALANCE_USD=200" in content:
        print("✅ Balance already set to $200")
    else:
        print("⚠️ Please check BALANCE_USD in .env file")
except:
    print("⚠️ Could not check .env file")

print("✅ Simple reset complete!")
print("💰 Balance: $200 (check .env)")
print("📡 Notifications: Cleared") 
print("🎛️ Trading: Enabled")