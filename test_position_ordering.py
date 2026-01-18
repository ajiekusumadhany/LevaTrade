#!/usr/bin/env python3
"""
Test position ordering - newest first
"""
from dry_run_system import dry_run_system
from datetime import datetime

def test_position_ordering():
    """Test that positions are returned in newest-first order"""
    print("🧪 Testing Position Ordering...")
    
    # Get open positions
    positions = dry_run_system.get_open_positions()
    
    if not positions:
        print("ℹ️  No open positions to test ordering")
        return
    
    print(f"📊 Found {len(positions)} open positions:")
    
    # Check if positions are ordered by entry_time DESC (newest first)
    for i, pos in enumerate(positions):
        entry_time = pos.get('entry_time', 'Unknown')
        symbol = pos.get('symbol', 'Unknown')
        direction = pos.get('direction', 'Unknown')
        
        # Parse entry time for display
        try:
            if entry_time != 'Unknown':
                dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00')).replace(tzinfo=None)
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                time_str = 'Unknown'
        except:
            time_str = entry_time
        
        print(f"   {i+1}. {symbol} {direction} - Entry: {time_str}")
    
    # Verify ordering
    if len(positions) > 1:
        print("\n🔍 Verifying order (newest first)...")
        
        for i in range(len(positions) - 1):
            current_time = positions[i].get('entry_time', '')
            next_time = positions[i + 1].get('entry_time', '')
            
            if current_time and next_time:
                try:
                    current_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00')).replace(tzinfo=None)
                    next_dt = datetime.fromisoformat(next_time.replace('Z', '+00:00')).replace(tzinfo=None)
                    
                    if current_dt >= next_dt:
                        print(f"   ✅ Position {i+1} is newer than position {i+2}")
                    else:
                        print(f"   ❌ Position {i+1} is older than position {i+2} - ORDER INCORRECT!")
                        return False
                except Exception as e:
                    print(f"   ⚠️  Could not compare times: {e}")
        
        print("✅ All positions are correctly ordered (newest first)")
    else:
        print("ℹ️  Only one position, ordering cannot be verified")
    
    return True

if __name__ == "__main__":
    test_position_ordering()