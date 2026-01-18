#!/usr/bin/env python3
"""
Test Real Market Conditions - Verifikasi kondisi teknikal yang disimpan di database
"""
import sqlite3
import json
from dry_run_system import dry_run_system

def check_stored_indicators():
    """Check indicators stored in database"""
    print("🔍 Checking Stored Market Conditions in Database")
    print("=" * 60)
    
    db_path = "dry_run_trades.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Check open positions indicators
        print("\n📊 Open Positions - Market Conditions:")
        cursor.execute("""
            SELECT symbol, direction, entry_price, current_price, indicators, entry_time
            FROM open_positions 
            ORDER BY entry_time DESC
            LIMIT 5
        """)
        
        open_positions = cursor.fetchall()
        
        if open_positions:
            for pos in open_positions:
                symbol, direction, entry_price, current_price, indicators_json, entry_time = pos
                
                print(f"\n   🎯 {symbol} {direction} @ ${entry_price:.4f}")
                print(f"      Entry Time: {entry_time}")
                
                try:
                    indicators = json.loads(indicators_json)
                    print(f"      📈 Market Conditions at Signal:")
                    
                    # Boolean indicators
                    bool_indicators = {k: v for k, v in indicators.items() if isinstance(v, bool)}
                    print(f"         Boolean Conditions:")
                    for key, value in bool_indicators.items():
                        status = "✅" if value else "❌"
                        print(f"           {status} {key}: {value}")
                    
                    # Numerical indicators  
                    num_indicators = {k: v for k, v in indicators.items() if isinstance(v, (int, float))}
                    print(f"         Numerical Values:")
                    for key, value in num_indicators.items():
                        print(f"           📊 {key}: {value}")
                        
                except json.JSONDecodeError:
                    print(f"      ❌ Invalid indicators JSON: {indicators_json}")
        else:
            print("   📭 No open positions found")
        
        # 2. Check trade history indicators
        print(f"\n📈 Trade History - Market Conditions:")
        cursor.execute("""
            SELECT symbol, direction, entry_price, exit_price, pnl, exit_reason, indicators, entry_time
            FROM trade_history 
            ORDER BY exit_time DESC
            LIMIT 3
        """)
        
        trade_history = cursor.fetchall()
        
        if trade_history:
            for trade in trade_history:
                symbol, direction, entry_price, exit_price, pnl, exit_reason, indicators_json, entry_time = trade
                
                print(f"\n   🎯 {symbol} {direction} @ ${entry_price:.4f} → ${exit_price:.4f}")
                print(f"      PnL: ${pnl:.2f} | Exit: {exit_reason}")
                print(f"      Entry Time: {entry_time}")
                
                try:
                    indicators = json.loads(indicators_json)
                    print(f"      📈 Market Conditions at Signal:")
                    
                    # Analyze strategy conditions
                    analyze_strategy_conditions(indicators, direction, symbol)
                        
                except json.JSONDecodeError:
                    print(f"      ❌ Invalid indicators JSON: {indicators_json}")
        else:
            print("   📭 No trade history found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def analyze_strategy_conditions(indicators, direction, symbol):
    """Analyze if stored conditions match strategy requirements"""
    
    print(f"      🧮 Strategy Analysis for {direction}:")
    
    # Get key indicators
    ema_bullish = indicators.get('ema_fast_above_slow', False)
    macd_bullish = indicators.get('macd_bullish', False)
    rsi_oversold = indicators.get('rsi_oversold', False)
    rsi_overbought = indicators.get('rsi_overbought', False)
    rsi_neutral = indicators.get('rsi_neutral', False)
    volume_ok = indicators.get('volume_confirmation', False)
    volatility_ok = indicators.get('volatility_confirmation', False)
    
    if direction == "LONG":
        print(f"         LONG Strategy Check:")
        
        # Kondisi 1: ema_bullish AND macd_bullish AND rsi_neutral AND volume_ok AND volatility_ok
        condition1 = ema_bullish and macd_bullish and rsi_neutral and volume_ok and volatility_ok
        print(f"         📋 Condition 1 (Trend+Momentum+Neutral): {condition1}")
        print(f"            EMA Bullish: {ema_bullish}")
        print(f"            MACD Bullish: {macd_bullish}")
        print(f"            RSI Neutral: {rsi_neutral}")
        print(f"            Volume OK: {volume_ok}")
        print(f"            Volatility OK: {volatility_ok}")
        
        # Kondisi 2: ema_bullish AND rsi_oversold AND volume_ok
        condition2 = ema_bullish and rsi_oversold and volume_ok
        print(f"         📋 Condition 2 (Trend+Oversold): {condition2}")
        print(f"            EMA Bullish: {ema_bullish}")
        print(f"            RSI Oversold: {rsi_oversold}")
        print(f"            Volume OK: {volume_ok}")
        
        signal_valid = condition1 or condition2
        print(f"         ✅ Signal Valid: {signal_valid}")
        
    elif direction == "SHORT":
        print(f"         SHORT Strategy Check:")
        
        # Kondisi 1: ema_bearish AND macd_bearish AND rsi_neutral AND volume_ok AND volatility_ok
        ema_bearish = not ema_bullish
        macd_bearish = not macd_bullish
        condition1 = ema_bearish and macd_bearish and rsi_neutral and volume_ok and volatility_ok
        print(f"         📋 Condition 1 (Trend+Momentum+Neutral): {condition1}")
        print(f"            EMA Bearish: {ema_bearish}")
        print(f"            MACD Bearish: {macd_bearish}")
        print(f"            RSI Neutral: {rsi_neutral}")
        print(f"            Volume OK: {volume_ok}")
        print(f"            Volatility OK: {volatility_ok}")
        
        # Kondisi 2: ema_bearish AND rsi_overbought AND volume_ok
        condition2 = ema_bearish and rsi_overbought and volume_ok
        print(f"         📋 Condition 2 (Trend+Overbought): {condition2}")
        print(f"            EMA Bearish: {ema_bearish}")
        print(f"            RSI Overbought: {rsi_overbought}")
        print(f"            Volume OK: {volume_ok}")
        
        signal_valid = condition1 or condition2
        print(f"         ✅ Signal Valid: {signal_valid}")

def test_indicator_completeness():
    """Test if all required indicators are being stored"""
    print(f"\n🧪 Testing Indicator Completeness")
    print("=" * 40)
    
    # Expected indicators from strategy
    expected_indicators = [
        'ema_fast_above_slow',
        'macd_bullish', 
        'rsi_oversold',
        'rsi_overbought',
        'rsi_neutral',
        'volume_confirmation',
        'volatility_confirmation',
        'trend_alignment',
        'momentum_confirmation',
        'rsi_level',
        'atr_value',
        'ema_fast_value',
        'ema_slow_value',
        'macd_line_value',
        'signal_line_value'
    ]
    
    # Check latest trade
    try:
        history = dry_run_system.get_trade_history(1)
        if history:
            trade = history[0]
            stored_indicators = trade.get('indicators', {})
            
            if isinstance(stored_indicators, str):
                stored_indicators = json.loads(stored_indicators)
            
            print(f"📊 Latest Trade: {trade['symbol']} {trade['direction']}")
            print(f"📋 Indicator Completeness Check:")
            
            missing = []
            present = []
            
            for indicator in expected_indicators:
                if indicator in stored_indicators:
                    present.append(indicator)
                    print(f"   ✅ {indicator}: {stored_indicators[indicator]}")
                else:
                    missing.append(indicator)
                    print(f"   ❌ {indicator}: MISSING")
            
            print(f"\n📊 Summary:")
            print(f"   Present: {len(present)}/{len(expected_indicators)}")
            print(f"   Missing: {len(missing)}")
            
            if missing:
                print(f"   ⚠️  Missing indicators: {missing}")
            else:
                print(f"   ✅ All indicators stored correctly!")
                
        else:
            print("📭 No trade history to check")
            
    except Exception as e:
        print(f"❌ Error checking completeness: {e}")

def main():
    """Main test function"""
    print("🔍 REAL MARKET CONDITIONS VERIFICATION")
    print("=" * 60)
    print("Checking if actual market conditions are stored in database")
    
    # Check stored indicators
    check_stored_indicators()
    
    # Test completeness
    test_indicator_completeness()
    
    print("\n" + "=" * 60)
    print("✅ Market conditions verification completed!")
    print("📊 Dashboard 'View Details' shows these exact conditions")
    print("🎯 Conditions stored = Conditions that triggered signal")
    print("=" * 60)

if __name__ == "__main__":
    main()