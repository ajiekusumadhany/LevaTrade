"""
Daily Stop System - Proteksi mental dan risk management harian
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from dry_run_system import dry_run_system

load_dotenv()

class DailyStopSystem:
    def __init__(self):
        self.max_daily_loss_percent = 10.0  # -10R daily stop
        self.current_daily_loss = 0.0
        self.daily_start_balance = 0.0
        self.last_reset_date = None
        self.is_stopped = False
        
    def reset_daily_counters(self):
        """Reset counters setiap hari baru (00:00 UTC / 07:00 WIB)"""
        today = datetime.now().date()
        
        if self.last_reset_date != today:
            # Reset daily counters
            self.daily_start_balance = dry_run_system.get_current_balance()
            self.current_daily_loss = 0.0
            self.is_stopped = False
            self.last_reset_date = today
            
            print(f"🌅 Daily Reset: Starting balance ${self.daily_start_balance:.2f}")
            return True
        return False
    
    def update_daily_pnl(self):
        """Update daily PnL dari trade history hari ini"""
        self.reset_daily_counters()
        
        # Get trades hari ini
        today = datetime.now().date().isoformat()
        all_trades = dry_run_system.get_trade_history(1000)
        
        daily_pnl = 0
        for trade in all_trades:
            trade_date = trade['exit_time'][:10]  # Get date part
            if trade_date == today:
                daily_pnl += trade['pnl']
        
        self.current_daily_loss = daily_pnl if daily_pnl < 0 else 0
        
        # Check daily stop
        daily_loss_percent = abs(self.current_daily_loss / self.daily_start_balance) * 100 if self.daily_start_balance > 0 else 0
        
        if daily_loss_percent >= self.max_daily_loss_percent:
            self.is_stopped = True
            print(f"🛑 DAILY STOP TRIGGERED: Loss {daily_loss_percent:.1f}% >= {self.max_daily_loss_percent}%")
            return True
        
        return False
    
    def can_trade(self):
        """Check apakah masih boleh trade hari ini"""
        self.update_daily_pnl()
        
        if self.is_stopped:
            daily_loss_percent = abs(self.current_daily_loss / self.daily_start_balance) * 100 if self.daily_start_balance > 0 else 0
            print(f"🚫 Trading STOPPED for today: Daily loss {daily_loss_percent:.1f}% >= {self.max_daily_loss_percent}%")
            return False
        
        return True
    
    def get_daily_stats(self):
        """Get daily statistics"""
        self.update_daily_pnl()
        
        daily_loss_percent = abs(self.current_daily_loss / self.daily_start_balance) * 100 if self.daily_start_balance > 0 else 0
        remaining_loss = self.max_daily_loss_percent - daily_loss_percent
        
        return {
            'daily_start_balance': self.daily_start_balance,
            'current_daily_loss': self.current_daily_loss,
            'daily_loss_percent': daily_loss_percent,
            'max_daily_loss_percent': self.max_daily_loss_percent,
            'remaining_loss_percent': max(0, remaining_loss),
            'is_stopped': self.is_stopped
        }

# Global instance
daily_stop_system = DailyStopSystem()