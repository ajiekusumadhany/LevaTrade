#!/usr/bin/env python3
"""
Test AI Reasoning System - Untuk menguji apakah AI reasoning menggunakan data indikator yang benar
"""
import asyncio
import json
from datetime import datetime
from gemini_ai_system import get_gemini_analyst
from indicator_analysis_system import IndicatorAnalysisSystem

async def test_entry_reasoning():
    """Test entry reasoning dengan data sample"""
    print("🧪 Testing AI Entry Reasoning...")
    
    # Sample signal data seperti yang dibuat di crypto_bot_parallel.py
    sample_signal = {
        'symbol': 'BTCUSDT',
        'direction': 'LONG',
        'close': 45000.0,
        'tp': 46000.0,
        'sl': 44000.0,
        'pos_size': 0.1,
        'leverage': 10,
        'rsi_level': 35.5,
        
        # Boolean indicators (yang seharusnya dianalisis)
        'ema_fast_above_slow': True,
        'macd_bullish': True,
        'rsi_oversold': True,
        'rsi_overbought': False,
        'rsi_neutral': False,
        'volume_confirmation': True,
        'volatility_confirmation': True,
        'price_near_support': True,
        'price_near_resistance': False,
        'trend_alignment': True,
        'momentum_confirmation': True,
        
        # Numerical values
        'atr_value': 500.0,
        'ema_fast_value': 45100.0,
        'ema_slow_value': 44900.0,
        'macd_line_value': 50.0,
        'signal_line_value': 30.0,
        'support_resistance': 44800.0,
        'price_distance_from_level': 0.004
    }
    
    print(f"📊 Sample Signal Data:")
    print(f"   Symbol: {sample_signal['symbol']}")
    print(f"   Direction: {sample_signal['direction']}")
    print(f"   Price: ${sample_signal['close']}")
    print(f"   RSI: {sample_signal['rsi_level']}")
    
    # Test indicator analysis
    analyzer = IndicatorAnalysisSystem()
    indicators = {k: v for k, v in sample_signal.items() if k not in ['symbol', 'direction', 'close', 'tp', 'sl', 'pos_size', 'leverage']}
    
    passed_indicators, failed_indicators = analyzer.analyze_indicators(indicators, sample_signal['direction'])
    
    print(f"\n🔍 Indicator Analysis Results:")
    print(f"   Passed: {len(passed_indicators)} indicators")
    print(f"   Failed: {len(failed_indicators)} indicators")
    print(f"   Pass Rate: {len(passed_indicators) / (len(passed_indicators) + len(failed_indicators)) * 100:.1f}%")
    
    print(f"\n✅ PASSED INDICATORS:")
    for indicator in passed_indicators:
        print(f"   - {indicator['description']}: {indicator['actual']}")
    
    print(f"\n❌ FAILED INDICATORS:")
    for indicator in failed_indicators:
        print(f"   - {indicator['description']}: {indicator['actual']}")
    
    # Test AI reasoning
    try:
        gemini_analyst = get_gemini_analyst()
        if gemini_analyst:
            print(f"\n🤖 Generating AI Entry Reasoning...")
            ai_reasoning = await gemini_analyst.generate_entry_reasoning(sample_signal)
            
            print(f"\n📝 AI ENTRY REASONING:")
            print(f"{'='*60}")
            print(ai_reasoning)
            print(f"{'='*60}")
            
            # Check if reasoning mentions passed/failed indicators
            reasoning_lower = ai_reasoning.lower()
            mentions_passed = any(word in reasoning_lower for word in ['passed', 'mendukung', 'positif'])
            mentions_failed = any(word in reasoning_lower for word in ['failed', 'tidak mendukung', 'negatif'])
            
            print(f"\n🔍 REASONING QUALITY CHECK:")
            print(f"   Mentions passed indicators: {'✅' if mentions_passed else '❌'}")
            print(f"   Mentions failed indicators: {'✅' if mentions_failed else '❌'}")
            print(f"   Length: {len(ai_reasoning)} characters")
            
        else:
            print("❌ Gemini analyst not available")
            
    except Exception as e:
        print(f"❌ Error testing AI reasoning: {e}")
        import traceback
        traceback.print_exc()

async def test_exit_reasoning():
    """Test exit reasoning dengan data sample"""
    print("\n🧪 Testing AI Exit Reasoning...")
    
    # Sample position data untuk exit
    sample_position = {
        'symbol': 'BTCUSDT',
        'direction': 'LONG',
        'entry_price': 45000.0,
        'exit_price': 46000.0,
        'entry_time': datetime.now().isoformat(),
        'realized_pnl': 100.0,
        'pnl_percentage': 2.22,
        'entry_indicators': {
            'ema_fast_above_slow': True,
            'macd_bullish': True,
            'rsi_oversold': True,
            'rsi_overbought': False,
            'rsi_neutral': False,
            'volume_confirmation': True,
            'volatility_confirmation': True,
            'price_near_support': True,
            'price_near_resistance': False,
            'trend_alignment': True,
            'momentum_confirmation': True,
            'rsi_level': 35.5,
            'atr_value': 500.0,
            'ema_fast_value': 45100.0,
            'ema_slow_value': 44900.0,
            'macd_line_value': 50.0,
            'signal_line_value': 30.0,
            'support_resistance': 44800.0,
            'price_distance_from_level': 0.004
        },
        
        # CRITICAL: Add realistic market data saat entry
        'market_cap': 850000000000,  # $850B market cap
        'market_cap_rank': 1,
        'total_volume_24h': 25000000000,  # $25B volume
        'circulating_supply': 19500000,
        'total_supply': 21000000,
        'max_supply': 21000000,
        'price_change_24h': 1000.0,  # +$1000 change
        'price_change_percentage_24h': 2.27,  # +2.27%
        'price_change_percentage_7d': 5.5,  # +5.5% weekly
        'price_change_percentage_30d': 12.8,  # +12.8% monthly
        'ath': 69000.0,
        'ath_change_percentage': -34.8,
        'atl': 15476.0,
        'atl_change_percentage': 190.8,
        'bybit_volume_24h': 2500000000,  # $2.5B Bybit volume
        'bybit_turnover_24h': 112500000000,  # $112.5B turnover
        'liquidity_score': 9.5,  # High liquidity
        'volatility_score': 3.2,  # Moderate volatility
        'market_dominance': 42.5,  # 42.5% dominance
        'market_cap_category': 'Large Cap',
        'volume_category': 'Very High Volume',
        'market_data_timestamp': datetime.now().isoformat(),
        'trading_session': 'NEWYORK'
    }
    
    print(f"📊 Sample Position Data:")
    print(f"   Symbol: {sample_position['symbol']}")
    print(f"   Direction: {sample_position['direction']}")
    print(f"   Entry: ${sample_position['entry_price']}")
    print(f"   Exit: ${sample_position['exit_price']}")
    print(f"   PnL: {sample_position['pnl_percentage']:.2f}%")
    
    # Test indicator analysis for entry
    analyzer = IndicatorAnalysisSystem()
    passed_indicators, failed_indicators = analyzer.analyze_indicators(
        sample_position['entry_indicators'], 
        sample_position['direction']
    )
    
    print(f"\n🔍 Entry Indicators Analysis:")
    print(f"   Passed: {len(passed_indicators)} indicators")
    print(f"   Failed: {len(failed_indicators)} indicators")
    
    # Test AI exit reasoning
    try:
        gemini_analyst = get_gemini_analyst()
        if gemini_analyst:
            print(f"\n🤖 Generating AI Exit Reasoning...")
            ai_reasoning = await gemini_analyst.generate_exit_reasoning(sample_position, "TP_HIT")
            
            print(f"\n📝 AI EXIT REASONING:")
            print(f"{'='*60}")
            print(ai_reasoning)
            print(f"{'='*60}")
            
            # Check reasoning quality
            reasoning_lower = ai_reasoning.lower()
            mentions_entry_quality = any(word in reasoning_lower for word in ['pass rate', 'entry', 'sinyal'])
            mentions_market_data = any(word in reasoning_lower for word in ['market', 'volume', 'volatilitas'])
            
            print(f"\n🔍 EXIT REASONING QUALITY CHECK:")
            print(f"   Mentions entry signal quality: {'✅' if mentions_entry_quality else '❌'}")
            print(f"   Mentions market data: {'✅' if mentions_market_data else '❌'}")
            print(f"   Length: {len(ai_reasoning)} characters")
            
        else:
            print("❌ Gemini analyst not available")
            
    except Exception as e:
        print(f"❌ Error testing exit reasoning: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    print("🚀 Starting AI Reasoning Tests...")
    print("="*60)
    
    await test_entry_reasoning()
    await test_exit_reasoning()
    
    print("\n✅ AI Reasoning Tests Completed!")

if __name__ == "__main__":
    asyncio.run(main())