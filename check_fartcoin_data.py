#!/usr/bin/env python3
"""
Check FARTCOINUSDT trade data to verify indicators
"""
from dry_run_system import dry_run_system
import json

def check_fartcoin_data():
    """Check FARTCOINUSDT trade indicators"""
    print("🔍 Checking FARTCOINUSDT Trade Data")
    print("=" * 50)
    
    # Get trade history
    history = dry_run_system.get_trade_history(10)
    
    # Find FARTCOINUSDT trade
    fart_trade = None
    for trade in history:
        if trade['symbol'] == 'FARTCOINUSDT':
            fart_trade = trade
            break
    
    if not fart_trade:
        print("❌ FARTCOINUSDT trade not found")
        return
    
    print(f"📊 FARTCOINUSDT {fart_trade['direction']} Trade:")
    print(f"   Entry: ${fart_trade['entry_price']:.6f}")
    print(f"   Exit: ${fart_trade['exit_price']:.6f}")
    print(f"   PnL: ${fart_trade['pnl']:.2f} ({fart_trade['pnl_percentage']:.2f}%)")
    print(f"   Exit Reason: {fart_trade['exit_reason']}")
    
    # Parse indicators
    try:
        if isinstance(fart_trade['indicators'], str):
            indicators = json.loads(fart_trade['indicators'])
        else:
            indicators = fart_trade['indicators']
        
        print(f"\n📈 Technical Indicators (saat sinyal):")
        
        # Boolean indicators
        boolean_indicators = {}
        numerical_indicators = {}
        
        for key, value in indicators.items():
            if isinstance(value, bool):
                boolean_indicators[key] = value
            else:
                numerical_indicators[key] = value
        
        print(f"\n✅ Boolean Conditions:")
        for key, value in boolean_indicators.items():
            status = "✅ TRUE" if value else "❌ FALSE"
            print(f"   {key}: {status}")
        
        print(f"\n📊 Numerical Values:")
        for key, value in numerical_indicators.items():
            print(f"   {key}: {value}")
        
        # Analyze for SHORT strategy
        print(f"\n🔍 SHORT Strategy Analysis:")
        
        # Check conditions
        ema_bearish = not boolean_indicators.get('ema_fast_above_slow', True)
        macd_bearish = not boolean_indicators.get('macd_bullish', True)
        rsi_oversold = boolean_indicators.get('rsi_oversold', False)
        rsi_overbought = boolean_indicators.get('rsi_overbought', False)
        rsi_neutral = boolean_indicators.get('rsi_neutral', False)
        volume_ok = boolean_indicators.get('volume_confirmation', False)
        volatility_ok = boolean_indicators.get('volatility_confirmation', False)
        
        print(f"   EMA Bearish (fast < slow): {ema_bearish}")
        print(f"   MACD Bearish (macd < signal): {macd_bearish}")
        print(f"   RSI Oversold (< 35): {rsi_oversold}")
        print(f"   RSI Overbought (> 65): {rsi_overbought}")
        print(f"   RSI Neutral (35-65): {rsi_neutral}")
        print(f"   Volume OK: {volume_ok}")
        print(f"   Volatility OK: {volatility_ok}")
        
        # Determine which condition triggered
        print(f"\n🎯 Strategy Condition Check:")
        
        # Condition 1: ema_bearish AND macd_bearish AND rsi_neutral AND volume_ok AND volatility_ok
        condition1 = ema_bearish and macd_bearish and rsi_neutral and volume_ok and volatility_ok
        print(f"   Condition 1 (Trend + Momentum + Neutral RSI): {condition1}")
        
        # Condition 2: ema_bearish AND rsi_overbought AND volume_ok
        condition2 = ema_bearish and rsi_overbought and volume_ok
        print(f"   Condition 2 (Trend + Overbought RSI): {condition2}")
        
        if condition1:
            print(f"   ✅ Triggered by: Bearish trend + momentum + neutral RSI")
        elif condition2:
            print(f"   ✅ Triggered by: Bearish trend + overbought RSI")
        else:
            print(f"   ⚠️  No clear condition match - possible data issue")
            
        # Check RSI level
        rsi_level = numerical_indicators.get('rsi_level', 50)
        print(f"\n📊 RSI Analysis:")
        print(f"   RSI Level: {rsi_level:.2f}")
        if rsi_level < 35:
            print(f"   Status: Oversold (< 35)")
        elif rsi_level > 65:
            print(f"   Status: Overbought (> 65)")
        else:
            print(f"   Status: Neutral (35-65)")
            
    except Exception as e:
        print(f"❌ Error parsing indicators: {e}")
        print(f"Raw indicators: {fart_trade['indicators']}")

if __name__ == "__main__":
    check_fartcoin_data()