"""
Hard Stop System - Emergency stop untuk drawdown besar
"""
import os
from datetime import datetime
from dotenv import load_dotenv
from dry_run_system import dry_run_system

load_dotenv()

class HardStopSystem:
    def __init__(self):
        self.max_drawdown_percent = 20.0  # 20% drawdown = HARD STOP
        self.starting_balance = float(os.getenv('BALANCE_USD', '1000'))
        self.is_hard_stopped = False
        self.hard_stop_reason = ""
        self.hard_stop_time = None
        
    def check_drawdown(self):
        """Check apakah drawdown sudah mencapai 20%"""
        current_balance = dry_run_system.get_current_balance()
        
        # Calculate drawdown from starting balance
        drawdown_amount = self.starting_balance - current_balance
        drawdown_percent = (drawdown_amount / self.starting_balance) * 100
        
        # HARD STOP jika drawdown >= 20%
        if drawdown_percent >= self.max_drawdown_percent and not self.is_hard_stopped:
            self.is_hard_stopped = True
            self.hard_stop_reason = f"DRAWDOWN {drawdown_percent:.1f}% >= {self.max_drawdown_percent}%"
            self.hard_stop_time = datetime.now()
            
            print(f"🚨🛑 HARD STOP TRIGGERED! 🛑🚨")
            print(f"📉 Drawdown: {drawdown_percent:.1f}% (${drawdown_amount:.2f})")
            print(f"💰 Starting Balance: ${self.starting_balance:.2f}")
            print(f"💰 Current Balance: ${current_balance:.2f}")
            print(f"⏰ Stop Time: {self.hard_stop_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"")
            print(f"🔴 BOT AKAN BERHENTI TOTAL!")
            print(f"🔍 ANALISA STRATEGI DIPERLUKAN!")
            print(f"🔧 Manual restart required setelah review")
            print(f"")
            
            return True
            
        return False
    
    def can_trade(self):
        """Check apakah masih boleh trading"""
        if self.is_hard_stopped:
            return False, self.hard_stop_reason
            
        # Check drawdown setiap kali dipanggil
        if self.check_drawdown():
            return False, self.hard_stop_reason
            
        return True, "OK"
    
    def get_status(self):
        """Get status hard stop system"""
        current_balance = dry_run_system.get_current_balance()
        drawdown_amount = self.starting_balance - current_balance
        drawdown_percent = (drawdown_amount / self.starting_balance) * 100
        
        return {
            'is_hard_stopped': self.is_hard_stopped,
            'hard_stop_reason': self.hard_stop_reason,
            'hard_stop_time': self.hard_stop_time,
            'starting_balance': self.starting_balance,
            'current_balance': current_balance,
            'drawdown_amount': drawdown_amount,
            'drawdown_percent': drawdown_percent,
            'max_drawdown_percent': self.max_drawdown_percent
        }
    
    def reset_hard_stop(self):
        """Reset hard stop (hanya untuk manual restart setelah analisa)"""
        self.is_hard_stopped = False
        self.hard_stop_reason = ""
        self.hard_stop_time = None
        print(f"🔄 Hard Stop system reset - Bot dapat trading lagi")

# Global instance
hard_stop_system = HardStopSystem()