#!/usr/bin/env python3
"""
Test Early Exit System
"""
import asyncio
from datetime import datetime, timedelta
from early_exit_system import early_exit_system

async def test_early_exit_conditions():
    """Test early exit system with various scenarios"""
    print("🧪 Testing Early Exit System...")
    
    # Test position data
    base_position = {
        'symbol': 'BTCUSDT',
        'direction': 'LONG',
        'entry_price': 50000.0,
        'entry_time': (datetime.now() - timedelta(minutes=30)).isoformat(),
        'atr_value': 500.0  # $500 ATR
    }
    
    # Test 1: Partial TP 1 (0.3x ATR profit)
    print("\n1. Testing Partial TP 1 (0.3x ATR profit)...")
    current_price = 50150.0  # 0.3x ATR profit
    current_indicators = {
        'current_price': current_price,
        'ema_fast': 50100,
        'ema_slow': 50050,
        'macd_line': 10,
        'signal_line': 5
    }
    
    exit_actions = early_exit_system.check_early_exit(base_position, current_price, current_indicators)
    print(f"   Exit actions: {len(exit_actions)}")
    for action in exit_actions:
        print(f"   - {action['type']}: {action['reason']}")
        await early_exit_system.send_early_exit_notification(base_position, action)
    
    # Test 2: Partial TP 2 (0.6x ATR profit)
    print("\n2. Testing Partial TP 2 (0.6x ATR profit)...")
    current_price = 50300.0  # 0.6x ATR profit
    exit_actions = early_exit_system.check_early_exit(base_position, current_price, current_indicators)
    print(f"   Exit actions: {len(exit_actions)}")
    for action in exit_actions:
        print(f"   - {action['type']}: {action['reason']}")
        await early_exit_system.send_early_exit_notification(base_position, action)
    
    # Test 3: Time-based exit (over 2 hours)
    print("\n3. Testing time-based exit...")
    old_position = base_position.copy()
    old_position['entry_time'] = (datetime.now() - timedelta(hours=3)).isoformat()
    current_price = 50100.0
    
    exit_actions = early_exit_system.check_early_exit(old_position, current_price, current_indicators)
    print(f"   Exit actions: {len(exit_actions)}")
    for action in exit_actions:
        print(f"   - {action['type']}: {action['reason']}")
        await early_exit_system.send_early_exit_notification(old_position, action)
    
    # Test 4: Momentum reversal (EMA cross down for LONG)
    print("\n4. Testing momentum reversal...")
    bearish_indicators = {
        'current_price': 50050,
        'ema_fast': 50000,  # Fast EMA below slow EMA
        'ema_slow': 50020,
        'macd_line': -5,    # MACD below signal
        'signal_line': 5
    }
    
    exit_actions = early_exit_system.check_early_exit(base_position, 50050, bearish_indicators)
    print(f"   Exit actions: {len(exit_actions)}")
    for action in exit_actions:
        print(f"   - {action['type']}: {action['reason']}")
        await early_exit_system.send_early_exit_notification(base_position, action)
    
    # Test 5: SHORT position with profit
    print("\n5. Testing SHORT position with profit...")
    short_position = {
        'symbol': 'ETHUSDT',
        'direction': 'SHORT',
        'entry_price': 2500.0,
        'entry_time': (datetime.now() - timedelta(minutes=45)).isoformat(),
        'atr_value': 50.0
    }
    
    current_price = 2485.0  # 0.3x ATR profit for SHORT
    short_indicators = {
        'current_price': current_price,
        'ema_fast': 2490,
        'ema_slow': 2495,
        'macd_line': -2,
        'signal_line': -1
    }
    
    exit_actions = early_exit_system.check_early_exit(short_position, current_price, short_indicators)
    print(f"   Exit actions: {len(exit_actions)}")
    for action in exit_actions:
        print(f"   - {action['type']}: {action['reason']}")
        await early_exit_system.send_early_exit_notification(short_position, action)
    
    print("\n✅ All early exit tests completed!")
    print("📱 Check your Telegram for notifications")

if __name__ == "__main__":
    asyncio.run(test_early_exit_conditions())