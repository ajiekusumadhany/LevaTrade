from dry_run_system import dry_run_system

positions = dry_run_system.get_open_positions()
print(f"Total positions: {len(positions)}")

for pos in positions:
    symbol = pos['symbol']
    position_value = pos['position_value_usd']
    leverage = pos['leverage']
    unrealized_pnl = pos['unrealized_pnl']
    entry_price = pos['entry_price']
    sl_price = pos['sl_price']
    quantity = pos['quantity']
    direction = pos['direction']
    
    # Margin yang benar-benar dipakai
    actual_margin = position_value / leverage
    
    # Risk amount = SL distance × quantity
    risk_amount = abs(entry_price - sl_price) * quantity
    
    # PnL percentage berdasarkan risk amount (BENAR)
    pnl_pct_risk = (unrealized_pnl / risk_amount) * 100 if risk_amount > 0 else 0
    
    # PnL percentage berdasarkan margin (SALAH)
    pnl_pct_margin = (unrealized_pnl / actual_margin) * 100 if actual_margin > 0 else 0
    
    print(f"\n{symbol} {direction}:")
    print(f"  Entry: ${entry_price:.6f}, SL: ${sl_price:.6f}")
    print(f"  Position Value: ${position_value:.2f}")
    print(f"  Leverage: {leverage}x")
    print(f"  Actual Margin: ${actual_margin:.2f}")
    print(f"  Risk Amount: ${risk_amount:.2f}")
    print(f"  Unrealized PnL: ${unrealized_pnl:.2f}")
    print(f"  PnL % (dari risk): {pnl_pct_risk:.2f}% ✅")
    print(f"  PnL % (dari margin): {pnl_pct_margin:.2f}% ❌")
    
    # Simulasi jika kena SL
    if direction == "LONG":
        sl_pnl = (sl_price - entry_price) * quantity
    else:  # SHORT
        sl_pnl = (entry_price - sl_price) * quantity
    
    sl_pct_risk = (sl_pnl / risk_amount) * 100
    print(f"  Jika kena SL: ${sl_pnl:.2f} ({sl_pct_risk:.0f}%) ✅")