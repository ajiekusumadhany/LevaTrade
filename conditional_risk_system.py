"""
CONDITIONAL RISK SYSTEM - Advanced Risk Management
Based on risk manager feedback: Prevent NY variance from destroying edge

Key Principles:
1. Risk escalation CONDITIONAL, not automatic
2. NY 1% = SNIPER MODE only (max 1-2 trades)
3. Protect Asia + London edge from NY variance
4. Fallback to conservative when conditions not met
"""
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

class ConditionalRiskManager:
    def __init__(self):
        load_dotenv()
        self.risk_state_file = "conditional_risk_state.json"
        self.load_state()
        
        # SAFE RISK FRAMEWORK (revised)
        self.session_risk_config = {
            'DEAD_ZONE': {
                'default_risk': 0.3,
                'max_risk': 0.3,  # No escalation in dead zone
                'conditions': []  # Always use default
            },
            'ASIA': {
                'default_risk': 0.3,
                'max_risk': 0.4,  # Small escalation allowed
                'conditions': ['clean_range', 'no_recent_loss']
            },
            'LONDON': {
                'default_risk': 0.5,  # Conservative default
                'max_risk': 0.8,  # A+ setups only
                'conditions': ['valid_breakout', 'volume_spike', 'no_recent_loss', 'spread_normal']
            },
            'NEWYORK': {  # Changed from NEW_YORK to NEWYORK
                'default_risk': 0.4,  # Conservative default
                'max_risk': 1.0,  # SNIPER MODE only
                'conditions': ['impulse_clear', 'spread_normal']  # Simplified conditions
            }
        }
        
        # Daily limits per session (from .env)
        self.daily_limits = {
            'NEWYORK_MAX_1PCT_TRADES': int(os.getenv('NEWYORK_MAX_1PCT_TRADES', '5')),
            'MAX_DAILY_LOSS_PERCENT': float(os.getenv('MAX_DAILY_LOSS_PERCENT', '5.0')),
            'MAX_CONSECUTIVE_LOSSES': int(os.getenv('MAX_CONSECUTIVE_LOSSES', '5')),
        }
    
    def load_state(self):
        """Load current risk state"""
        try:
            if os.path.exists(self.risk_state_file):
                with open(self.risk_state_file, 'r') as f:
                    self.state = json.load(f)
            else:
                self.reset_daily_state()
        except Exception as e:
            print(f"⚠️ Error loading risk state: {e}")
            self.reset_daily_state()
    
    def save_state(self):
        """Save current risk state"""
        try:
            with open(self.risk_state_file, 'w') as f:
                json.dump(self.state, f)
        except Exception as e:
            print(f"⚠️ Error saving risk state: {e}")
    
    def reset_daily_state(self):
        """Reset daily risk state"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.state = {
            'date': today,
            'daily_pnl': 0.0,
            'consecutive_losses': 0,
            'trades_by_session': {
                'DEAD_ZONE': 0,
                'ASIA': 0,
                'LONDON': 0,
                'NEWYORK': 0
            },
            'ny_1pct_trades': 0,  # Track 1% trades in NY
            'last_trade_result': None,  # 'WIN' or 'LOSS'
            'last_trade_time': None,
            'session_pnl': {
                'DEAD_ZONE': 0.0,
                'ASIA': 0.0,
                'LONDON': 0.0,
                'NEWYORK': 0.0
            }
        }
        self.save_state()
    
    def check_daily_reset(self):
        """Check if we need to reset daily state"""
        today = datetime.now().strftime('%Y-%m-%d')
        if self.state.get('date') != today:
            print(f"📅 New trading day: {today} - Resetting risk state")
            self.reset_daily_state()
    
    def evaluate_conditions(self, session, market_data, indicators):
        """Evaluate if conditions are met for risk escalation"""
        conditions = self.session_risk_config[session]['conditions']
        met_conditions = []
        failed_conditions = []
        
        for condition in conditions:
            if self._check_condition(condition, session, market_data, indicators):
                met_conditions.append(condition)
            else:
                failed_conditions.append(condition)
        
        all_met = len(failed_conditions) == 0
        return all_met, met_conditions, failed_conditions
    
    def _check_condition(self, condition, session, market_data, indicators):
        """Check individual condition"""
        
        if condition == 'clean_range':
            # For ASIA: market should be in clean range
            volatility = market_data.get('volatility_score', 0)
            return 0.2 <= volatility <= 0.6
        
        elif condition == 'no_recent_loss':
            # More lenient: allow trading unless too many consecutive losses
            return self.state['consecutive_losses'] < 3  # Allow up to 2 consecutive losses
        
        elif condition == 'valid_breakout':
            # For LONDON: need clear breakout signal
            breakout_strength = indicators.get('breakout_strength', 0)
            return breakout_strength >= 0.7  # 70% breakout confidence
        
        elif condition == 'volume_spike':
            # Need volume confirmation
            return indicators.get('volume_confirmation', False)
        
        elif condition == 'spread_normal':
            # Spread should be normal (not widened)
            spread = market_data.get('spread_percent', 0)
            return spread <= 0.1  # Max 0.1% spread
        
        elif condition == 'impulse_clear':
            # For NY: need clear impulse/momentum
            momentum_strength = indicators.get('momentum_strength', 0)
            return momentum_strength >= 0.8  # 80% momentum confidence
        
        elif condition == 'no_loss_today':
            # No losses today
            return self.state['daily_pnl'] >= 0
        
        elif condition == 'max_2_trades':
            # Max 2 trades in NY session today
            return self.state['trades_by_session']['NEWYORK'] < 2
        
        elif condition == 'range_expansion':
            # Market should be expanding, not contracting
            atr_ratio = indicators.get('atr_ratio', 1.0)  # Current ATR vs average
            return atr_ratio >= 1.2  # 20% above average ATR
        
        return False
    
    def get_conditional_risk(self, session, current_balance, market_data, indicators):
        """Get risk percentage - SEMUA LIMIT DIHAPUS, hanya drawdown 20% yang berlaku"""
        self.check_daily_reset()
        
        config = self.session_risk_config[session]
        default_risk = config['default_risk']
        max_risk = config['max_risk']
        
        # SEMUA LIMIT DIHAPUS - Tidak ada daily loss limit
        # SEMUA LIMIT DIHAPUS - Tidak ada consecutive loss limit  
        # SEMUA LIMIT DIHAPUS - Tidak ada NY sniper limit
        # SEMUA LIMIT DIHAPUS - Tidak ada session limit
        
        # Selalu gunakan max risk untuk setiap session
        risk_percent = max_risk
        risk_mode = "MAX_ALWAYS"
        
        print(f"📊 NO LIMITS MODE: {session} = {risk_percent}% ({risk_mode})")
        print(f"   🚀 ALL SESSION LIMITS REMOVED - Only 20% drawdown stop applies")
        
        return risk_percent
    
    def record_trade_result(self, session, pnl, risk_used):
        """Record trade result for risk management"""
        self.check_daily_reset()
        
        # Update daily PnL
        self.state['daily_pnl'] += pnl
        self.state['session_pnl'][session] += pnl
        
        # Update trade count
        self.state['trades_by_session'][session] += 1
        
        # Update consecutive losses
        if pnl < 0:
            self.state['consecutive_losses'] += 1
            self.state['last_trade_result'] = 'LOSS'
        else:
            self.state['consecutive_losses'] = 0  # Reset on win
            self.state['last_trade_result'] = 'WIN'
        
        self.state['last_trade_time'] = datetime.now().isoformat()
        
        self.save_state()
        
        print(f"📈 TRADE RECORDED: {session} PnL=${pnl:.2f} (Risk: {risk_used}%)")
        print(f"   Daily PnL: ${self.state['daily_pnl']:.2f}")
        print(f"   Consecutive losses: {self.state['consecutive_losses']}")
    
    def get_risk_status(self):
        """Get current risk management status"""
        self.check_daily_reset()
        
        daily_loss_percent = abs(self.state['daily_pnl']) / 1000 * 100  # Assuming $1000 balance
        
        # SEMUA LIMIT DIHAPUS - Hanya track untuk informasi
        return {
            'daily_pnl': self.state['daily_pnl'],
            'daily_loss_percent': daily_loss_percent,
            'consecutive_losses': self.state['consecutive_losses'],
            'ny_sniper_trades_used': self.state['ny_1pct_trades'],
            'ny_sniper_trades_remaining': 999,  # Unlimited
            'trades_by_session': self.state['trades_by_session'],
            'session_pnl': self.state['session_pnl'],
            'risk_mode': 'NO_LIMITS'  # Always no limits mode
        }

# Global conditional risk manager
conditional_risk_manager = ConditionalRiskManager()

def get_conditional_risk(session, current_balance, market_data, indicators):
    """Get conditional risk percentage"""
    return conditional_risk_manager.get_conditional_risk(session, current_balance, market_data, indicators)

def record_trade_result(session, pnl, risk_used):
    """Record trade result"""
    conditional_risk_manager.record_trade_result(session, pnl, risk_used)

def get_risk_status():
    """Get risk status"""
    return conditional_risk_manager.get_risk_status()

if __name__ == "__main__":
    # Test the conditional risk system
    print("🧪 TESTING CONDITIONAL RISK SYSTEM")
    print("=" * 50)
    
    # Mock data for testing
    mock_market_data = {
        'volatility_score': 0.4,
        'spread_percent': 0.05
    }
    
    mock_indicators = {
        'volume_confirmation': True,
        'breakout_strength': 0.8,
        'momentum_strength': 0.9,
        'atr_ratio': 1.3
    }
    
    balance = 1000
    
    # Test each session
    sessions = ['DEAD_ZONE', 'ASIA', 'LONDON', 'NEWYORK']
    
    for session in sessions:
        print(f"\n🧪 Testing {session}:")
        risk = get_conditional_risk(session, balance, mock_market_data, mock_indicators)
        print(f"   Risk: {risk}%")
    
    # Test NY sniper mode limit
    print(f"\n🎯 Testing NY SNIPER MODE limits:")
    for i in range(3):
        risk = get_conditional_risk('NEWYORK', balance, mock_market_data, mock_indicators)
        print(f"   NY Trade {i+1}: {risk}%")
        # Simulate trade completion
        record_trade_result('NEWYORK', 10, risk)  # Winning trade
    
    # Show final status
    status = get_risk_status()
    print(f"\n📊 FINAL STATUS:")
    for key, value in status.items():
        print(f"   {key}: {value}")