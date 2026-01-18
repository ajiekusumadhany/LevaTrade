#!/usr/bin/env python3
"""
Test script untuk memverifikasi logika entry zone
"""

def test_entry_zone_logic():
    """Test logika pengecekan entry zone"""
    
    print("=" * 60)
    print("TEST LOGIKA ENTRY ZONE")
    print("=" * 60)
    
    # Simulasi PROMUSDT SHORT
    resistance = 3.8000
    atr = 0.0500
    
    # Entry zone untuk SHORT
    entry_low = resistance - atr * 0.5  # 3.7750
    entry_high = resistance              # 3.8000
    
    print(f"Entry Zone: ${entry_low:.4f} - ${entry_high:.4f}")
    print(f"ATR: ${atr:.4f}")
    
    # Test cases
    test_cases = [
        {
            'name': 'Harga di dalam zone',
            'close': 3.7800,
            'low': 3.7750,
            'high': 3.7850,
            'should_enter': True
        },
        {
            'name': 'Harga sedikit di bawah zone (PROMUSDT case)',
            'close': 3.7670,  # Kasus PROMUSDT
            'low': 3.7650,
            'high': 3.7700,
            'should_enter': True  # Dengan toleransi ATR
        },
        {
            'name': 'Harga menyentuh entry_high',
            'close': 3.7900,
            'low': 3.7850,
            'high': 3.8000,  # Menyentuh resistance
            'should_enter': True
        },
        {
            'name': 'Harga jauh di bawah zone',
            'close': 3.7400,
            'low': 3.7350,
            'high': 3.7450,
            'should_enter': False
        },
        {
            'name': 'Harga di atas zone (sudah breakout)',
            'close': 3.8100,
            'low': 3.8050,
            'high': 3.8150,
            'should_enter': False
        }
    ]
    
    print(f"\nTesting {len(test_cases)} scenarios:\n")
    
    for i, case in enumerate(test_cases, 1):
        current_close = case['close']
        current_low = case['low']
        current_high = case['high']
        
        # Logika LAMA (ketat)
        old_logic = current_low <= entry_high and current_high >= entry_low
        
        # Logika BARU (fleksibel) - untuk SHORT
        tolerance = atr * 0.2  # 20% dari ATR (lebih konservatif)
        price_in_range = (entry_low - tolerance) <= current_close <= entry_high
        not_breakout = current_close <= entry_high * 1.005  # Max 0.5% di atas resistance
        new_logic = price_in_range and not_breakout
        
        print(f"{i}. {case['name']}")
        print(f"   Price: Close=${current_close:.4f}, Low=${current_low:.4f}, High=${current_high:.4f}")
        print(f"   Tolerance: ${tolerance:.4f} (20% ATR)")
        print(f"   Range: ${entry_low - tolerance:.4f} - ${entry_high:.4f}")
        print(f"   Max breakout: ${entry_high * 1.005:.4f}")
        print(f"   Old Logic: {'✅ ENTER' if old_logic else '❌ NO ENTRY'}")
        print(f"   New Logic: {'✅ ENTER' if new_logic else '❌ NO ENTRY'}")
        print(f"   Expected:  {'✅ ENTER' if case['should_enter'] else '❌ NO ENTRY'}")
        
        if new_logic == case['should_enter']:
            print(f"   Result: ✅ CORRECT")
        else:
            print(f"   Result: ❌ WRONG")
        
        print()
    
    # Fokus pada kasus PROMUSDT
    print("=" * 60)
    print("ANALISIS KASUS PROMUSDT")
    print("=" * 60)
    
    promusdt_close = 3.7670
    promusdt_low = 3.7650
    promusdt_high = 3.7700
    
    print(f"PROMUSDT Data:")
    print(f"  Close: ${promusdt_close:.4f}")
    print(f"  Low: ${promusdt_low:.4f}")
    print(f"  High: ${promusdt_high:.4f}")
    print(f"  Entry Zone: ${entry_low:.4f} - ${entry_high:.4f}")
    
    # Cek logika lama
    old_check = promusdt_low <= entry_high and promusdt_high >= entry_low
    print(f"\nLogika Lama:")
    print(f"  {promusdt_low:.4f} <= {entry_high:.4f} = {promusdt_low <= entry_high}")
    print(f"  {promusdt_high:.4f} >= {entry_low:.4f} = {promusdt_high >= entry_low}")
    print(f"  Result: {old_check} → {'ENTER' if old_check else 'NO ENTRY'}")
    
    # Cek logika baru
    tolerance = atr * 0.2
    price_in_range = (entry_low - tolerance) <= promusdt_close <= entry_high
    not_breakout = promusdt_close <= entry_high * 1.005
    new_check = price_in_range and not_breakout
    
    print(f"\nLogika Baru:")
    print(f"  Tolerance: ${tolerance:.4f} (20% ATR)")
    print(f"  Price range: ${entry_low - tolerance:.4f} <= ${promusdt_close:.4f} <= ${entry_high:.4f} = {price_in_range}")
    print(f"  Not breakout: ${promusdt_close:.4f} <= ${entry_high * 1.005:.4f} = {not_breakout}")
    print(f"  Result: {new_check} → {'ENTER' if new_check else 'NO ENTRY'}")
    
    print(f"\n🎯 KESIMPULAN:")
    if not old_check and new_check:
        print(f"  ✅ Masalah diperbaiki! Bot sekarang akan entry pada PROMUSDT SHORT")
        print(f"  📊 Harga ${promusdt_close:.4f} masuk dalam toleransi ${entry_low - tolerance:.4f} - ${entry_high:.4f}")
    elif old_check and new_check:
        print(f"  ✅ Kedua logika mengizinkan entry")
    else:
        print(f"  ❌ Masih ada masalah dengan logika entry")

if __name__ == "__main__":
    test_entry_zone_logic()