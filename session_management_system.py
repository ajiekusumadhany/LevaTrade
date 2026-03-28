"""
Session Management System - Read from .env configuration
Automatically switch strategies based on current time (WIB)
WITH CONDITIONAL RISK FRAMEWORK - Prevent NY variance destruction
"""
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from conditional_risk_system import get_conditional_risk, get_risk_status

# WIB timezone (UTC+7)
WIB = timezone(timedelta(hours=7))

class SessionManager:
    def __init__(self):
        load_dotenv()
        
        # Load session configurations from .env
        self.sessions = {
            'DEAD_ZONE': {
                'start_hour': int(os.getenv('DEAD_ZONE_START_HOUR', '2')),
                'end_hour': int(os.getenv('DEAD_ZONE_END_HOUR', '7')),
                'strategy': os.getenv('DEAD_ZONE_STRATEGY', 'ultra_conservative'),
                'default_risk': float(os.getenv('DEAD_ZONE_RISK_PERCENT', '0.3')),
                'max_risk': float(os.getenv('DEAD_ZONE_MAX_RISK_PERCENT', '0.3')),
                'max_leverage': int(os.getenv('DEAD_ZONE_MAX_LEVERAGE', '10')),
                'max_positions': int(os.getenv('DEAD_ZONE_MAX_POSITIONS', '20')),
                'tp_multiplier': float(os.getenv('DEAD_ZONE_TP_MULTIPLIER', '2.0')),
                'sl_multiplier': float(os.getenv('DEAD_ZONE_SL_MULTIPLIER', '0.4')),
                'description': 'SURVIVAL MODE - Perfect setups only'
            },
            'ASIA': {
                'start_hour': int(os.getenv('ASIA_START_HOUR', '7')),
                'end_hour': int(os.getenv('ASIA_END_HOUR', '14')),
                'strategy': os.getenv('ASIA_STRATEGY', 'mean_reversion'),
                'default_risk': float(os.getenv('ASIA_RISK_PERCENT', '0.3')),
                'max_risk': float(os.getenv('ASIA_MAX_RISK_PERCENT', '0.4')),
                'max_leverage': int(os.getenv('ASIA_MAX_LEVERAGE', '8')),
                'max_positions': int(os.getenv('ASIA_MAX_POSITIONS', '20')),
                'tp_multiplier': float(os.getenv('ASIA_TP_MULTIPLIER', '0.8')),
                'sl_multiplier': float(os.getenv('ASIA_SL_MULTIPLIER', '0.4')),
                'description': 'RANGE TRADING - Anti-breakout, mean reversion'
            },
            'LONDON': {
                'start_hour': int(os.getenv('LONDON_START_HOUR', '14')),
                'end_hour': int(os.getenv('LONDON_END_HOUR', '20')),
                'strategy': os.getenv('LONDON_STRATEGY', 'structural_breakout_pullback'),
                'default_risk': float(os.getenv('LONDON_RISK_PERCENT', '0.5')),
                'max_risk': float(os.getenv('LONDON_MAX_RISK_PERCENT', '0.8')),
                'max_leverage': int(os.getenv('LONDON_MAX_LEVERAGE', '15')),
                'max_positions': int(os.getenv('LONDON_MAX_POSITIONS', '20')),
                'tp_multiplier': float(os.getenv('LONDON_TP_MULTIPLIER', '2.0')),
                'sl_multiplier': float(os.getenv('LONDON_SL_MULTIPLIER', '0.8')),
                'description': 'BREAKOUT HUNTER - Structure + pullback'
            },
            'NEWYORK': {
                'start_hour': int(os.getenv('NEWYORK_START_HOUR', '20')),
                'end_hour': int(os.getenv('NEWYORK_END_HOUR', '2')),
                'strategy': os.getenv('NEWYORK_STRATEGY', 'momentum_continuation_reversal'),
                'default_risk': float(os.getenv('NEWYORK_RISK_PERCENT', '0.4')),
                'max_risk': float(os.getenv('NEWYORK_MAX_RISK_PERCENT', '1.0')),
                'max_leverage': int(os.getenv('NEWYORK_MAX_LEVERAGE', '20')),
                'max_positions': int(os.getenv('NEWYORK_MAX_POSITIONS', '20')),
                'tp_multiplier': float(os.getenv('NEWYORK_TP_MULTIPLIER', '1.5')),
                'sl_multiplier': float(os.getenv('NEWYORK_SL_MULTIPLIER', '0.5')),
                'description': 'MOMENTUM RIDER - Conditional 1% (SNIPER MODE)'
            }
        }
    
    def get_current_session(self):
        """Get current trading session based on WIB time"""
        now_wib = datetime.now(WIB)
        current_hour = now_wib.hour
        
        # Check each session
        for session_name, config in self.sessions.items():
            start_hour = config['start_hour']
            end_hour = config['end_hour']
            
            # Handle sessions that cross midnight
            if start_hour > end_hour:  # DEAD_ZONE (22-6) and NEWYORK (20-2)
                if current_hour >= start_hour or current_hour < end_hour:
                    return session_name, config
            else:  # ASIA (7-14) and LONDON (14-20)
                if start_hour <= current_hour < end_hour:
                    return session_name, config
        
        # Fallback to DEAD_ZONE if no session matches
        return 'DEAD_ZONE', self.sessions['DEAD_ZONE']
    
    def get_session_parameters(self, session_name=None, current_balance=1000, market_data=None, indicators=None):
        """Get trading parameters for current or specified session with conditional risk"""
        if session_name is None:
            session_name, config = self.get_current_session()
        else:
            config = self.sessions.get(session_name, self.sessions['DEAD_ZONE'])
        
        # Get conditional risk (safe framework)
        if market_data and indicators:
            risk_percent = get_conditional_risk(session_name, current_balance, market_data, indicators)
        else:
            # Fallback to default risk if no market data
            risk_percent = config['default_risk']
        
        return {
            'session': session_name,
            'strategy': config['strategy'],
            'description': config['description'],
            'risk_percent': risk_percent,
            'default_risk': config['default_risk'],
            'max_risk': config['max_risk'],
            'max_leverage': config['max_leverage'],
            'max_positions': config['max_positions'],
            'tp_multiplier': config['tp_multiplier'],
            'sl_multiplier': config['sl_multiplier']
        }
    
    def is_session_active(self, session_name):
        """Check if specified session is currently active"""
        current_session, _ = self.get_current_session()
        return current_session == session_name
    
    def get_next_session_change(self):
        """Get time until next session change"""
        now_wib = datetime.now(WIB)
        current_hour = now_wib.hour
        current_session, _ = self.get_current_session()
        
        # Find next session change time
        session_changes = [
            (2, 'NEWYORK -> DEAD_ZONE'),   # 02:00 WIB
            (7, 'DEAD_ZONE -> ASIA'),      # 07:00 WIB  
            (14, 'ASIA -> LONDON'),        # 14:00 WIB
            (20, 'LONDON -> NEWYORK')      # 20:00 WIB
        ]
        
        for change_hour, change_desc in session_changes:
            if current_hour < change_hour:
                # Next change is today
                next_change = now_wib.replace(hour=change_hour, minute=0, second=0, microsecond=0)
                time_until = next_change - now_wib
                return time_until, change_desc
        
        # Next change is tomorrow (first change of next day)
        next_change = now_wib.replace(hour=2, minute=0, second=0, microsecond=0) + timedelta(days=1)
        time_until = next_change - now_wib
        return time_until, 'NEWYORK -> DEAD_ZONE'
    
    def get_session_status(self):
        """Get comprehensive session status with risk management info"""
        current_session, config = self.get_current_session()
        time_until_change, next_change = self.get_next_session_change()
        
        # Get risk management status
        risk_status = get_risk_status()
        
        # Session emojis
        session_emojis = {
            'DEAD_ZONE': '🟥',
            'ASIA': '🟨', 
            'LONDON': '🟩',
            'NEWYORK': '🟦'  # Changed from NEW_YORK to NEWYORK
        }
        
        # Session names
        session_names = {
            'DEAD_ZONE': 'Dead Zone',
            'ASIA': 'Asia Session',
            'LONDON': 'London Session', 
            'NEWYORK': 'New York Session'  # Changed from NEW_YORK to NEWYORK
        }
        
        return {
            'current_session': current_session,
            'session_emoji': session_emojis.get(current_session, '🕐'),
            'session_name': session_names.get(current_session, 'Unknown Session'),
            'strategy': config['strategy'],
            'description': config['description'],
            'default_risk': config['default_risk'],
            'max_risk': config['max_risk'],
            'risk_range': f"{config['default_risk']:.1f}%-{config['max_risk']:.1f}%",
            'max_leverage': config['max_leverage'],
            'max_positions': config['max_positions'],
            'tp_multiplier': config['tp_multiplier'],
            'sl_multiplier': config['sl_multiplier'],
            'time_until_change': str(time_until_change).split('.')[0],  # Remove microseconds
            'next_change': next_change,
            'current_time_wib': datetime.now(WIB).strftime('%Y-%m-%d %H:%M:%S WIB'),
            # Risk management status
            'risk_status': risk_status,
            'daily_pnl': risk_status['daily_pnl'],
            'ny_sniper_remaining': risk_status['ny_sniper_trades_remaining'],
            'risk_mode': risk_status['risk_mode']
        }

def implement_dead_zone_strategy():
    """Implement DEAD_ZONE ultra-conservative strategy"""
    
    print("🌙 IMPLEMENTING DEAD_ZONE ULTRA-CONSERVATIVE STRATEGY")
    print("=" * 60)
    
    # Load current environment
    load_dotenv()
    
    # Read current .env file
    with open('.env', 'r') as f:
        env_lines = f.readlines()
    
    print("📊 DEAD_ZONE SESSION CHARACTERISTICS:")
    print("- Waktu: 22:00 – 06:00 WIB (low liquidity)")
    print("- Volume: Sangat rendah")
    print("- Masalah: Win rate historis 4.3%")
    print("- Pendekatan: Ultra-konservatif, survival mode")
    
    print("\n🔧 STRATEGY: ULTRA-CONSERVATIVE FILTERING")
    print("✅ Semua indikator WAJIB align")
    print("✅ Market cap >$1B only")
    print("✅ Perfect setup only")
    print("❌ Tolak semua yang tidak sempurna")
    
    # DEAD_ZONE session specific settings
    dead_zone_settings = {
        # Enable DEAD_ZONE with ultra-conservative strategy
        'DEAD_ZONE_SESSION_ENABLED': 'true',
        'DEAD_ZONE_STRATEGY_TYPE': 'ultra_conservative',
        
        # Time settings (22:00-06:00 WIB)
        'DEAD_ZONE_START_HOUR': '22',  # 22:00 WIB
        'DEAD_ZONE_END_HOUR': '6',     # 06:00 WIB
        
        # Ultra-conservative parameters
        'DEAD_ZONE_RISK_PERCENT': '0.3',  # Minimal risk
        'DEAD_ZONE_MAX_LEVERAGE': '10',   # Low leverage
        'DEAD_ZONE_MAX_POSITIONS': '3',   # Very limited positions
        
        # TP/SL for survival (5:1 R/R)
        'DEAD_ZONE_TP_MULTIPLIER': '2.0',  # Large TP
        'DEAD_ZONE_SL_MULTIPLIER': '0.4',  # Tight SL
        
        # Ultra-strict filters
        'DEAD_ZONE_MIN_MARKET_CAP': '1000000000',  # $1B minimum
        'DEAD_ZONE_MIN_VOLATILITY': '0.3',         # Some movement needed
        'DEAD_ZONE_MAX_VOLATILITY': '0.8',         # Not too volatile
        'DEAD_ZONE_MIN_VOLUME_24H': '50000000',    # $50M minimum
        
        # Perfect alignment requirements
        'DEAD_ZONE_REQUIRE_ALL_INDICATORS': 'true',
        'DEAD_ZONE_REQUIRE_TREND_ALIGNMENT': 'true',
        'DEAD_ZONE_REQUIRE_MOMENTUM_CONFIRMATION': 'true',
        'DEAD_ZONE_REQUIRE_VOLUME_CONFIRMATION': 'true',
        'DEAD_ZONE_REQUIRE_SR_LEVEL': 'true',
        
        # RSI perfect ranges
        'DEAD_ZONE_RSI_LONG_MIN': '25',    # Oversold but not extreme
        'DEAD_ZONE_RSI_LONG_MAX': '40',    # Oversold range
        'DEAD_ZONE_RSI_SHORT_MIN': '60',   # Overbought range
        'DEAD_ZONE_RSI_SHORT_MAX': '75',   # Overbought but not extreme
        
        # MACD and EMA requirements
        'DEAD_ZONE_REQUIRE_MACD_ALIGNMENT': 'true',
        'DEAD_ZONE_REQUIRE_EMA_ALIGNMENT': 'true',
        'DEAD_ZONE_REQUIRE_VOLATILITY_CONFIRMATION': 'true',
        
        # Emergency stops (very strict)
        'DEAD_ZONE_MAX_DAILY_LOSS': '50',         # Stop at $50 loss
        'DEAD_ZONE_MAX_CONSECUTIVE_LOSSES': '5',  # Stop after 5 losses
        'DEAD_ZONE_EMERGENCY_STOP_ENABLED': 'true',
        
        # No direction bias (neutral)
        'DEAD_ZONE_LONG_WEIGHT': '0.5',
        'DEAD_ZONE_SHORT_WEIGHT': '0.5',
        
        # Quality over quantity
        'DEAD_ZONE_MIN_SETUP_SCORE': '0.9',  # 90% setup quality required
        'DEAD_ZONE_PERFECT_SETUP_ONLY': 'true',
    }
    
    print("\n🛠️ IMPLEMENTING DEAD_ZONE SETTINGS:")
    
    # Update environment variables
    updated_lines = []
    existing_vars = set()
    
    for line in env_lines:
        if '=' in line and not line.strip().startswith('#'):
            var_name = line.split('=')[0].strip()
            if var_name in dead_zone_settings:
                updated_lines.append(f"{var_name}={dead_zone_settings[var_name]}\n")
                existing_vars.add(var_name)
                print(f"  ✅ {var_name}={dead_zone_settings[var_name]}")
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Add new variables that don't exist
    print("\n📝 ADDING NEW DEAD_ZONE VARIABLES:")
    for var_name, var_value in dead_zone_settings.items():
        if var_name not in existing_vars:
            updated_lines.append(f"{var_name}={var_value}\n")
            print(f"  ➕ {var_name}={var_value}")
    
    # Write updated .env file
    with open('.env', 'w') as f:
        f.writelines(updated_lines)
    
    print("\n✅ DEAD_ZONE environment variables updated")
    
    return dead_zone_settings

# Global session manager instance
session_manager = SessionManager()

def get_current_session_parameters(current_balance=1000, market_data=None, indicators=None):
    """Get current session trading parameters with conditional risk"""
    return session_manager.get_session_parameters(None, current_balance, market_data, indicators)

def get_session_status():
    """Get current session status"""
    return session_manager.get_session_status()

def is_session_active(session_name):
    """Check if session is active"""
    return session_manager.is_session_active(session_name)

if __name__ == "__main__":
    # Implement DEAD_ZONE strategy
    dead_zone_settings = implement_dead_zone_strategy()
    
    print("\n🎯 DEAD_ZONE STRATEGY IMPLEMENTED")
    print("=" * 60)
    print("✅ Ultra-conservative filtering")
    print("✅ Perfect setup requirements")
    print("✅ Survival mode activated")
    print("✅ 5:1 Risk/Reward ratio")
    
    print(f"\n🔧 Total DEAD_ZONE settings: {len(dead_zone_settings)}")
    
    # Show current session status
    print("\n📊 CURRENT SESSION STATUS:")
    print("=" * 40)
    status = get_session_status()
    for key, value in status.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("\n🌙 DEAD_ZONE session configured for survival trading!")
    print("\n🎯 ALL 4 SESSIONS NOW IMPLEMENTED:")
    print("🌙 DEAD_ZONE: Ultra-conservative (0.3% risk)")
    print("🌏 ASIA: Mean reversion (0.3% risk)")
    print("🟢 LONDON: Structural breakout (0.8% risk)")
    print("🔵 NEW YORK: Momentum trading (1.0% risk)")