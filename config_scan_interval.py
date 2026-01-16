"""
Konfigurasi Scan Interval - Pilih yang sesuai kebutuhan
"""

print("=" * 70)
print("  SCAN INTERVAL CONFIGURATION GUIDE")
print("=" * 70)

configs = [
    {
        "name": "Ultra Fast",
        "interval": 60,  # 1 menit
        "scans_per_4h": 240,
        "pros": ["Catch entry paling cepat", "Real-time monitoring"],
        "cons": ["Banyak API calls", "Bisa noisy", "High CPU"],
        "use_case": "Scalping, 1m-5m timeframe"
    },
    {
        "name": "Fast",
        "interval": 300,  # 5 menit
        "scans_per_4h": 48,
        "pros": ["Cepat catch entry", "Good coverage", "Current setting"],
        "cons": ["Agak banyak API calls"],
        "use_case": "1H timeframe, Active trading"
    },
    {
        "name": "Balanced ⭐",
        "interval": 900,  # 15 menit
        "scans_per_4h": 16,
        "pros": ["Optimal balance", "Hemat resources", "Stable signals"],
        "cons": ["Sedikit delay"],
        "use_case": "4H timeframe (RECOMMENDED)"
    },
    {
        "name": "Conservative",
        "interval": 1800,  # 30 menit
        "scans_per_4h": 8,
        "pros": ["Sangat stabil", "Minimal API calls", "Low CPU"],
        "cons": ["Bisa miss entry cepat"],
        "use_case": "4H-1D timeframe, Conservative"
    },
    {
        "name": "Slow",
        "interval": 3600,  # 1 jam
        "scans_per_4h": 4,
        "pros": ["Paling stabil", "Minimal resources"],
        "cons": ["Miss banyak entry", "Terlalu lambat"],
        "use_case": "Daily timeframe"
    },
    {
        "name": "On Candle Close",
        "interval": 14400,  # 4 jam
        "scans_per_4h": 1,
        "pros": ["100% akurat", "Sama dengan TradingView"],
        "cons": ["Terlalu lambat", "Miss entry zone"],
        "use_case": "Backtest, Historical analysis"
    }
]

print("\n📊 AVAILABLE CONFIGURATIONS\n")

for i, config in enumerate(configs, 1):
    star = " ⭐" if "⭐" in config["name"] else ""
    print(f"{i}. {config['name']}{star}")
    print(f"   Interval: {config['interval']}s ({config['interval']//60} minutes)")
    print(f"   Scans per 4H candle: {config['scans_per_4h']}x")
    print(f"   ✅ Pros: {', '.join(config['pros'])}")
    print(f"   ❌ Cons: {', '.join(config['cons'])}")
    print(f"   💡 Use case: {config['use_case']}")
    print()

print("=" * 70)
print("  RECOMMENDATION FOR YOUR BOT")
print("=" * 70)

print("\n🎯 Current Setting: 5 minutes (300s)")
print("   - Good for catching entries quickly")
print("   - 48 scans per 4H candle")
print("   - Suitable for active monitoring")

print("\n⭐ Recommended: 15 minutes (900s)")
print("   - Optimal for 4H timeframe")
print("   - 16 scans per 4H candle (cukup untuk catch entry)")
print("   - Balance antara speed dan stability")
print("   - Hemat API calls dan resources")

print("\n💡 How to Change:")
print("   Edit crypto_bot_parallel.py, line ~350:")
print("   await asyncio.sleep(300)  # Current: 5 minutes")
print("   await asyncio.sleep(900)  # Change to: 15 minutes")

print("\n📊 COMPARISON TABLE")
print("-" * 70)
print("Interval | Scans/4H | API Calls/Day | Best For")
print("-" * 70)
print("1 min    | 240      | 34,560        | Scalping")
print("5 min    | 48       | 6,912         | 1H timeframe")
print("15 min ⭐ | 16       | 2,304         | 4H timeframe")
print("30 min   | 8        | 1,152         | Conservative")
print("1 hour   | 4        | 576           | Daily")
print("4 hour   | 1        | 144           | Backtest")

print("\n💰 COST CONSIDERATION")
print("-" * 70)
print("Bybit API: FREE (no rate limit untuk market data)")
print("Telegram: FREE (no limit)")
print()
print("Jadi bisa pakai interval apapun tanpa biaya tambahan!")
print("Tapi untuk stability dan efficiency, 15 menit optimal.")

print("\n🔧 ADVANCED: Dynamic Interval")
print("-" * 70)
print("Bisa juga pakai dynamic interval:")
print("- Saat ada setup aktif: scan setiap 5 menit")
print("- Saat tidak ada setup: scan setiap 30 menit")
print("- Hemat resources tapi tetap catch opportunities")

print("\n" + "=" * 70)
print("✅ Pilih interval sesuai trading style Anda!")
print("=" * 70)
