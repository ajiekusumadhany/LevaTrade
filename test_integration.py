#!/usr/bin/env python3
"""
Integration Test - Test complete system integration
"""
import asyncio
import time
from datetime import datetime
from dry_run_system import dry_run_system
from early_exit_system import early_exit_system
from error_notification_system import error_notifier

async def test_complete_integration():
    """Test complete system integration"""
    print("🧪 Testing Complete System Integration...")
    print("=" * 60)
    
    # Test 1: Dry Run System
    print("\n1. Testing Dry Run System...")
    
    # Create a test signal
    test_signal = {
        'symbol': 'BTCUSDT',
        'direction': 'LONG',
        'close': 50000.0,
        'entry_low': 49950.0,
        'entry_high': 50050.0,
        'sl': 49500.0,
        'tp': 50800.0,
        'leverage': 5,
        'lev_mode': 'NORMAL',
        'risk_amount': 10.0,
        'sl_percent': 1.0,
        'rr_ratio': 1.6,
        'pos_size': 0.001,
        'position_value_usd': 50.0,
        'atr_value': 250.0,
        # Technical indicators
        'ema_fast_above_slow': True,
        'macd_bullish': True,
        'rsi_oversold': False,
        'rsi_overbought': False,
        'rsi_neutral': True,
        'rsi_level': 45.0,
        'ema_fast_value': 50020.0,
        'ema_slow_value': 49980.0,
        'macd_line_value': 15.0,
        'signal_line_value': 10.0
    }
    
    # Open position
    position_id = dry_run_system.open_position(test_signal)
    print(f"   ✅ Position opened: {position_id}")
    
    # Check open positions
    open_positions = dry_run_system.get_open_positions()
    print(f"   📊 Open positions: {len(open_positions)}")
    
    # Update with current price (simulate price movement)
    print("\n   📈 Simulating price movements...")
    
    # Price goes up slightly
    dry_run_system.update_positions({'BTCUSDT': 50100.0})
    positions = dry_run_system.get_open_positions()
    if positions:
        pos = positions[0]
        print(f"   💰 Price: ${pos['current_price']:.2f}, PnL: ${pos['unrealized_pnl']:.2f}")
    
    # Price hits TP
    print("   🎯 Simulating TP hit...")
    dry_run_system.update_positions({'BTCUSDT': 50800.0})
    
    # Check if position was closed
    await asyncio.sleep(2)  # Wait for notification
    open_positions = dry_run_system.get_open_positions()
    closed_positions = dry_run_system.get_closed_positions()
    print(f"   📊 Open: {len(open_positions)}, Closed: {len(closed_positions)}")
    
    # Test 2: Error Notification System
    print("\n2. Testing Error Notification System...")
    
    await error_notifier.notify_trading_error(
        "insufficient_balance",
        "ETHUSDT",
        {
            'required_amount': 100.0,
            'available_balance': 50.0,
            'position_size': 0.05,
            'leverage': 10
        }
    )
    print("   ✅ Error notification sent")
    
    # Test 3: Early Exit System
    print("\n3. Testing Early Exit System...")
    
    # Create another position for early exit testing
    test_signal2 = test_signal.copy()
    test_signal2['symbol'] = 'ETHUSDT'
    test_signal2['close'] = 2500.0
    test_signal2['tp'] = 2600.0
    test_signal2['sl'] = 2450.0
    
    position_id2 = dry_run_system.open_position(test_signal2)
    print(f"   ✅ Second position opened: {position_id2}")
    
    # Simulate price movement for partial TP
    dry_run_system.update_positions({'ETHUSDT': 2515.0})  # Small profit
    
    # Test early exit conditions
    positions = dry_run_system.get_open_positions()
    if positions:
        eth_position = next((p for p in positions if p['symbol'] == 'ETHUSDT'), None)
        if eth_position:
            position_data = {
                'symbol': eth_position['symbol'],
                'direction': eth_position['direction'],
                'entry_price': eth_position['entry_price'],
                'entry_time': eth_position['entry_time'],
                'atr_value': 25.0  # ETH ATR
            }
            
            current_indicators = {
                'current_price': 2515.0,
                'ema_fast': 2510,
                'ema_slow': 2505,
                'macd_line': 5,
                'signal_line': 3
            }
            
            exit_actions = early_exit_system.check_early_exit(position_data, 2515.0, current_indicators)
            print(f"   📊 Early exit actions: {len(exit_actions)}")
            
            for action in exit_actions:
                print(f"   - {action['type']}: {action['reason']}")
                await early_exit_system.send_early_exit_notification(position_data, action)
    
    # Test 4: System Status Notifications
    print("\n4. Testing System Status Notifications...")
    
    await error_notifier.notify_system_status("bot_started", {
        'mode': 'DRY RUN (Integration Test)',
        'symbol_count': 2,
        'timeframe': '15m',
        'scan_interval': '3m 0s',
        'balance': 1000.0
    })
    print("   ✅ Bot started notification sent")
    
    await asyncio.sleep(1)
    
    await error_notifier.notify_system_status("bot_stopped", {
        'reason': 'Integration test completed',
        'runtime': '5m 0s',
        'total_trades': 2,
        'final_pnl': 25.50
    })
    print("   ✅ Bot stopped notification sent")
    
    # Test 5: Performance Summary
    print("\n5. Testing Performance Summary...")
    
    performance = dry_run_system.get_performance_summary()
    print(f"   📊 Performance Summary:")
    print(f"      Total Trades: {performance.get('total_trades', 0)}")
    print(f"      Win Rate: {performance.get('win_rate', 0):.1f}%")
    print(f"      Total PnL: ${performance.get('total_pnl', 0):.2f}")
    print(f"      Profit Factor: {performance.get('profit_factor', 0):.2f}")
    
    error_summary = error_notifier.get_error_summary()
    print(f"   ❌ Error Summary:")
    print(f"      Total Errors: {error_summary['total_errors']}")
    print(f"      Error Types: {list(error_summary['error_counts'].keys())}")
    
    print("\n" + "=" * 60)
    print("✅ Integration Test Completed Successfully!")
    print("📱 Check your Telegram for all notifications")
    print("📊 Check dashboard for position updates")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_complete_integration())