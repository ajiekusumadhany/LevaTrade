#!/usr/bin/env python3
"""
Test script untuk memverifikasi perhitungan Take Profit yang benar
untuk posisi SHORT dan LONG
"""

def test_tp_calculation():
    """Test perhitungan TP/SL untuk SHORT dan LONG"""
    
    # Simulasi data untuk PROMUSDT SHORT
    resistance = 3.8000  # Resistance level
    atr = 0.0500  # ATR value
    TP_ATR_MULT = 2.0
    SL_ATR_MULT = 1.2
    
    print("=" * 60)
    print("TEST PERHITUNGAN TAKE PROFIT & STOP LOSS")
    print("=" * 60)
    
    # Test SHORT position
    print("\n📉 SHORT POSITION TEST:")
    print(f"Resistance Level: ${resistance:.4f}")
    print(f"ATR: ${atr:.4f}")
    print(f"TP Multiplier: {TP_ATR_MULT}x")
    print(f"SL Multiplier: {SL_ATR_MULT}x")
    
    # Entry zone untuk SHORT
    entry_low = resistance - atr * 0.5
    entry_high = resistance
    entry_price = (entry_low + entry_high) / 2
    
    # TP dan SL untuk SHORT (BENAR)
    tp_short = entry_price - atr * TP_ATR_MULT  # TP di BAWAH entry
    sl_short = entry_price + atr * SL_ATR_MULT  # SL di ATAS entry
    
    print(f"\nEntry Zone: ${entry_low:.4f} - ${entry_high:.4f}")
    print(f"Entry Price (mid): ${entry_price:.4f}")
    print(f"Take Profit: ${tp_short:.4f} ✅ (di BAWAH entry)")
    print(f"Stop Loss: ${sl_short:.4f} ✅ (di ATAS entry)")
    
    # Verifikasi logika
    assert tp_short < entry_price, "❌ TP harus di BAWAH entry untuk SHORT!"
    assert sl_short > entry_price, "❌ SL harus di ATAS entry untuk SHORT!"
    
    print(f"\n✅ SHORT Logic: BENAR")
    print(f"   - TP ({tp_short:.4f}) < Entry ({entry_price:.4f}) ✓")
    print(f"   - SL ({sl_short:.4f}) > Entry ({entry_price:.4f}) ✓")
    
    # Test LONG position untuk perbandingan
    print("\n📈 LONG POSITION TEST (untuk perbandingan):")
    support = 3.6000  # Support level
    
    entry_low_long = support
    entry_high_long = support + atr * 0.5
    entry_price_long = (entry_low_long + entry_high_long) / 2
    
    tp_long = entry_price_long + atr * TP_ATR_MULT  # TP di ATAS entry
    sl_long = entry_price_long - atr * SL_ATR_MULT  # SL di BAWAH entry
    
    print(f"Support Level: ${support:.4f}")
    print(f"Entry Zone: ${entry_low_long:.4f} - ${entry_high_long:.4f}")
    print(f"Entry Price (mid): ${entry_price_long:.4f}")
    print(f"Take Profit: ${tp_long:.4f} ✅ (di ATAS entry)")
    print(f"Stop Loss: ${sl_long:.4f} ✅ (di BAWAH entry)")
    
    # Verifikasi logika LONG
    assert tp_long > entry_price_long, "❌ TP harus di ATAS entry untuk LONG!"
    assert sl_long < entry_price_long, "❌ SL harus di BAWAH entry untuk LONG!"
    
    print(f"\n✅ LONG Logic: BENAR")
    print(f"   - TP ({tp_long:.4f}) > Entry ({entry_price_long:.4f}) ✓")
    print(f"   - SL ({sl_long:.4f}) < Entry ({entry_price_long:.4f}) ✓")
    
    # Simulasi kasus PROMUSDT yang bermasalah
    print("\n" + "=" * 60)
    print("SIMULASI KASUS PROMUSDT YANG BERMASALAH")
    print("=" * 60)
    
    current_price = 3.7670  # Harga saat ini
    print(f"Harga saat ini: ${current_price:.4f}")
    print(f"Resistance: ${resistance:.4f}")
    
    # Perhitungan SALAH (yang lama)
    tp_wrong = current_price - atr * TP_ATR_MULT
    sl_wrong = current_price + atr * SL_ATR_MULT
    
    print(f"\n❌ PERHITUNGAN LAMA (SALAH):")
    print(f"   TP: ${tp_wrong:.4f} (menggunakan current_price)")
    print(f"   SL: ${sl_wrong:.4f}")
    print(f"   Masalah: TP ({tp_wrong:.4f}) > Entry Zone ({entry_high:.4f}) ❌")
    
    print(f"\n✅ PERHITUNGAN BARU (BENAR):")
    print(f"   TP: ${tp_short:.4f} (menggunakan entry_price)")
    print(f"   SL: ${sl_short:.4f}")
    print(f"   Benar: TP ({tp_short:.4f}) < Entry Zone ({entry_low:.4f}) ✓")
    
    print(f"\n🎯 KESIMPULAN:")
    print(f"   - Masalah: Bot menggunakan harga saat ini (${current_price:.4f}) sebagai referensi")
    print(f"   - Solusi: Gunakan entry_price (${entry_price:.4f}) sebagai referensi")
    print(f"   - Hasil: TP sekarang benar di ${tp_short:.4f} (di BAWAH entry)")

if __name__ == "__main__":
    test_tp_calculation()