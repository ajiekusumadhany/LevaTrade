"""
Progressive Risk System - Risk management bertahap untuk proteksi mental
"""
from datetime import datetime
from dry_run_system import dry_run_system

class ProgressiveRiskSystem:
    def __init__(self):
        self.base_risk_percent = 1.0  # 1% base risk
        
        # Risk tiers berdasarkan urutan trade harian
        self.risk_tiers = {
            'early': {'trades': (1, 5), 'risk_multiplier': 0.3},    # Trade 1-5: 0.3R
            'middle': {'trades': (6, 10), 'risk_multiplier': 0.5},  # Trade 6-10: 0.5R  
            'normal': {'trades': (11, 999), 'risk_multiplier': 1.0} # Trade 11+: 1R
        }
        
        # Loss gates - DISABLED (removed by user request)
        self.loss_gates = []  # No loss gates
        
        self.max_open_risk_percent = 10.0  # Max total risk dari semua posisi terbuka (10% untuk 10-20 posisi)
        
    def get_daily_trade_count(self):
        """Hitung jumlah trade hari ini"""
        today = datetime.now().date().isoformat()
        all_trades = dry_run_system.get_trade_history(1000)
        
        daily_trades = 0
        for trade in all_trades:
            trade_date = trade['exit_time'][:10]
            if trade_date == today:
                daily_trades += 1
        
        return daily_trades
    
    def get_current_risk_multiplier(self):
        """Dapatkan risk multiplier berdasarkan jumlah trade hari ini"""
        daily_trades = self.get_daily_trade_count()
        
        for tier_name, tier_config in self.risk_tiers.items():
            min_trades, max_trades = tier_config['trades']
            if min_trades <= daily_trades + 1 <= max_trades:  # +1 karena trade berikutnya
                return tier_config['risk_multiplier']
        
        return self.risk_tiers['normal']['risk_multiplier']  # Default 1.0
    
    def get_adjusted_risk_percent(self, current_balance):
        """Dapatkan risk percentage yang sudah disesuaikan"""
        # Base risk dengan multiplier bertahap
        risk_multiplier = self.get_current_risk_multiplier()
        adjusted_risk = self.base_risk_percent * risk_multiplier
        
        # Check loss gates
        daily_stats = daily_stop_system.get_daily_stats()
        daily_loss_percent = daily_stats['daily_loss_percent']
        
        # Jika mendekati loss gate, kurangi risk
        if daily_loss_percent >= 1.0:  # Jika sudah loss 1%+
            adjusted_risk *= 0.5  # Kurangi risk jadi setengah
            print(f"⚠️  Risk reduced due to daily loss: {daily_loss_percent:.1f}%")
        
        return adjusted_risk
    
    def check_loss_gates(self):
        """Check apakah perlu break karena loss gate"""
        daily_stats = daily_stop_system.get_daily_stats()
        daily_loss_percent = daily_stats['daily_loss_percent']
        
        for gate in self.loss_gates:
            if daily_loss_percent >= gate['threshold']:
                print(f"🚨 LOSS GATE TRIGGERED: {daily_loss_percent:.1f}% >= {gate['threshold']}%")
                print(f"⏸️  MANDATORY BREAK: {gate['break_minutes']} minutes")
                return gate['break_minutes']
        
        return 0  # No break needed
    
    def check_max_open_risk(self):
        """Check total risk dari semua posisi terbuka"""
        current_positions = dry_run_system.get_open_positions()
        current_balance = dry_run_system.get_current_balance()
        
        total_open_risk = 0
        for pos in current_positions:
            # Risk per posisi = SL distance × quantity
            entry_price = pos.get('entry_price', 0)
            sl_price = pos.get('sl_price', 0) 
            quantity = pos.get('quantity', 0)
            
            if entry_price and sl_price and quantity:
                position_risk = abs(entry_price - sl_price) * quantity
                total_open_risk += position_risk
        
        total_open_risk_percent = (total_open_risk / current_balance) * 100 if current_balance > 0 else 0
        
        if total_open_risk_percent >= self.max_open_risk_percent:
            print(f"🛑 MAX OPEN RISK: {total_open_risk_percent:.1f}% >= {self.max_open_risk_percent}%")
            return False
        
        return True
    
    def can_open_new_position(self):
        """Check apakah boleh buka posisi baru"""
        # Check loss gates
        break_minutes = self.check_loss_gates()
        if break_minutes > 0:
            return False, f"Loss gate triggered - break {break_minutes} minutes"
        
        # Check max open risk
        if not self.check_max_open_risk():
            return False, "Max open risk exceeded"
        
        return True, "OK"
    
    def get_risk_info(self):
        """Get informasi risk management saat ini"""
        daily_trades = self.get_daily_trade_count()
        risk_multiplier = self.get_current_risk_multiplier()
        current_balance = dry_run_system.get_current_balance()
        adjusted_risk = self.get_adjusted_risk_percent(current_balance)
        
        # Tier info
        tier_name = "normal"
        for name, config in self.risk_tiers.items():
            min_trades, max_trades = config['trades']
            if min_trades <= daily_trades + 1 <= max_trades:
                tier_name = name
                break
        
        return {
            'daily_trades': daily_trades,
            'tier_name': tier_name,
            'risk_multiplier': risk_multiplier,
            'base_risk_percent': self.base_risk_percent,
            'adjusted_risk_percent': adjusted_risk,
            'max_open_risk_percent': self.max_open_risk_percent
        }

# Global instance
progressive_risk_system = ProgressiveRiskSystem()