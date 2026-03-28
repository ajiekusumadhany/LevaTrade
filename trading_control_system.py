"""
Trading Control System - Start/Stop trading via Dashboard and Telegram
"""
import json
import os
from datetime import datetime

CONTROL_FILE = "trading_control.json"

class TradingController:
    def __init__(self):
        self.control_file = CONTROL_FILE
        self.load_status()
    
    def load_status(self):
        """Load trading status from file"""
        try:
            if os.path.exists(self.control_file):
                with open(self.control_file, 'r') as f:
                    data = json.load(f)
                    self.is_trading_enabled = data.get('enabled', True)
                    self.last_updated = data.get('last_updated', datetime.now().isoformat())
                    self.updated_by = data.get('updated_by', 'system')
            else:
                self.is_trading_enabled = True
                self.last_updated = datetime.now().isoformat()
                self.updated_by = 'system'
                self.save_status()
        except Exception as e:
            print(f"⚠️ Error loading trading status: {e}")
            self.is_trading_enabled = True
            self.last_updated = datetime.now().isoformat()
            self.updated_by = 'system'
    
    def save_status(self):
        """Save trading status to file"""
        try:
            data = {
                'enabled': self.is_trading_enabled,
                'last_updated': self.last_updated,
                'updated_by': self.updated_by
            }
            with open(self.control_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"⚠️ Error saving trading status: {e}")
    
    def start_trading(self, updated_by='dashboard'):
        """Start trading"""
        self.is_trading_enabled = True
        self.last_updated = datetime.now().isoformat()
        self.updated_by = updated_by
        self.save_status()
        print(f"✅ Trading STARTED by {updated_by}")
        return True
    
    def stop_trading(self, updated_by='dashboard'):
        """Stop trading (no new entries)"""
        self.is_trading_enabled = False
        self.last_updated = datetime.now().isoformat()
        self.updated_by = updated_by
        self.save_status()
        print(f"🛑 Trading STOPPED by {updated_by}")
        return True
    
    def is_trading_allowed(self):
        """Check if trading is allowed"""
        self.load_status()  # Refresh status
        return self.is_trading_enabled
    
    def get_status(self):
        """Get current trading status"""
        self.load_status()
        return {
            'enabled': self.is_trading_enabled,
            'last_updated': self.last_updated,
            'updated_by': self.updated_by,
            'status_text': 'ACTIVE' if self.is_trading_enabled else 'STOPPED'
        }

# Global trading controller instance
trading_controller = TradingController()

def is_trading_enabled():
    """Quick function to check if trading is enabled"""
    return trading_controller.is_trading_allowed()

def start_trading(updated_by='system'):
    """Start trading"""
    return trading_controller.start_trading(updated_by)

def stop_trading(updated_by='system'):
    """Stop trading"""
    return trading_controller.stop_trading(updated_by)

def get_trading_status():
    """Get trading status"""
    return trading_controller.get_status()

if __name__ == "__main__":
    # Test the trading controller
    print("🧪 Testing Trading Controller")
    print("=" * 40)
    
    # Check initial status
    status = get_trading_status()
    print(f"Initial status: {status}")
    
    # Test stop
    stop_trading('test')
    status = get_trading_status()
    print(f"After stop: {status}")
    
    # Test start
    start_trading('test')
    status = get_trading_status()
    print(f"After start: {status}")
    
    # Test is_enabled check
    print(f"Is trading enabled: {is_trading_enabled()}")