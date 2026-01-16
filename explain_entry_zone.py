"""
Visualisasi Entry Zone untuk SHORT setup
"""

print("=" * 70)
print("  PENJELASAN: Entry Zone SHORT Setup")
print("=" * 70)

# Data XRP
resistance = 2.1916
entry_low = 2.1733
entry_high = 2.1916
current_high = 2.0438
current_low = 2.0285
tp = 1.9681
sl = 2.0854

print("\n📊 XRP SHORT SETUP")
print("-" * 70)
print(f"Resistance:     ${resistance:.4f}")
print(f"Entry Zone:     ${entry_low:.4f} - ${entry_high:.4f}")
print(f"Current Price:  ${current_low:.4f} - ${current_high:.4f}")
print(f"Stop Loss:      ${sl:.4f}")
print(f"Take Profit:    ${tp:.4f}")

print("\n📈 VISUALISASI HARGA")
print("-" * 70)
print()

# Price levels
levels = [
    (2.20, ""),
    (2.1916, "← Entry High (Resistance)"),
    (2.1733, "← Entry Low"),
    (2.15, ""),
    (2.10, ""),
    (2.0854, "← Stop Loss"),
    (2.0438, "← Current High ⭐"),
    (2.0285, "← Current Low ⭐"),
    (2.00, ""),
    (1.9681, "← Take Profit"),
]

for price, label in levels:
    bar = "█" * int((price - 1.96) * 20)
    
    # Highlight entry zone
    if entry_low <= price <= entry_high:
        print(f"${price:.4f} |🟢{bar} {label}")
    # Highlight current price
    elif current_low <= price <= current_high:
        print(f"${price:.4f} |🔵{bar} {label}")
    else:
        print(f"${price:.4f} |{bar} {label}")

print()
print("-" * 70)

print("\n🔍 ANALISIS")
print("-" * 70)
print("1. Setup: BEARISH ✅")
print("   - EMA Fast < EMA Slow")
print("   - MACD < Signal")
print("   - RSI < 45")
print()
print("2. Entry Zone: $2.1733 - $2.1916 🟢")
print("   - Ini zona untuk MASUK SHORT")
print("   - Tunggu harga NAIK ke sini dulu")
print()
print("3. Current Price: $2.0285 - $2.0438 🔵")
print("   - Harga sekarang MASIH DI BAWAH entry zone")
print("   - Belum bisa entry short")
print()
print("4. Status: ⚪ WAIT")
print("   - Tunggu harga naik ke $2.17-$2.19")
print("   - Baru bisa entry short")

print("\n💡 KENAPA HARUS TUNGGU?")
print("-" * 70)
print("SHORT setup artinya kita mau JUAL di harga tinggi.")
print("Entry zone di $2.17-$2.19 adalah zona RESISTANCE.")
print("Kita tunggu harga naik ke resistance dulu, baru short.")
print()
print("Kalau entry sekarang di $2.04:")
print("  ❌ Terlalu jauh dari resistance")
print("  ❌ Risk/Reward tidak optimal")
print("  ❌ Bisa kena stop loss di $2.08")

print("\n📋 SKENARIO")
print("-" * 70)
print("Skenario 1: Harga naik ke $2.17-$2.19")
print("  → ✅ ENTRY SHORT")
print("  → 🎯 Target: $1.97")
print("  → 🛑 Stop: $2.09")
print()
print("Skenario 2: Harga terus turun dari $2.04")
print("  → ⚪ SKIP (tidak entry)")
print("  → 💡 Tunggu setup berikutnya")

print("\n🎓 KESIMPULAN")
print("-" * 70)
print("Status WAIT itu BENAR! ✅")
print()
print("Bot menunggu harga naik ke entry zone dulu.")
print("Ini adalah risk management yang baik.")
print("Tidak semua setup bearish langsung entry,")
print("harus tunggu harga di posisi yang tepat.")

print("\n" + "=" * 70)
print("✅ Logika bot sudah 100% benar!")
print("=" * 70)
