"""
Debug ICT Strategy - test langsung 1 symbol tanpa bot penuh
"""
import os
import sys
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from pybit.unified_trading import HTTP

load_dotenv()

BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', '')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', '')

session = HTTP(testnet=False, api_key=BYBIT_API_KEY, api_secret=BYBIT_API_SECRET)

def get_klines(symbol, interval='15', limit=100):
    try:
        r = session.get_kline(category="linear", symbol=symbol, interval=interval, limit=limit)
        if r['retCode'] == 0:
            df = pd.DataFrame(r['result']['list'],
                              columns=['timestamp','open','high','low','close','volume','turnover'])
            df = df.astype({'open':float,'high':float,'low':float,'close':float,'volume':float})
            return df.iloc[::-1].reset_index(drop=True)
        print(f"  API error: {r.get('retMsg')}")
        return None
    except Exception as e:
        print(f"  Exception: {e}")
        return None

def test_symbol(symbol):
    print(f"\n{'='*60}")
    print(f"TEST: {symbol}")
    print('='*60)

    # Ambil data
    bias_df  = get_klines(symbol, '15', 100)
    entry_df = get_klines(symbol, '5',  100)
    atr_df   = bias_df

    if bias_df is None or entry_df is None:
        print("❌ Gagal ambil data klines")
        return

    print(f"✅ Data OK - bias:{len(bias_df)} candles, entry:{len(entry_df)} candles")

    # Import ICT
    from ict_smc_strategy import (
        detect_market_structure, detect_order_blocks, detect_fvg,
        detect_liquidity_sweep, get_premium_discount_zone, is_in_kill_zone,
        _calculate_atr, _calculate_rsi
    )

    # --- BIAS (15m) ---
    bias_df['rsi'] = _calculate_rsi(bias_df['close'], 14)
    bias_struct   = detect_market_structure(bias_df, swing_length=5)
    bias_pd       = get_premium_discount_zone(bias_df, lookback=50)
    bias_liq      = detect_liquidity_sweep(bias_df, lookback=20)

    print(f"\n📊 BIAS (15m):")
    print(f"   Structure : {bias_struct['bias']}")
    print(f"   BOS       : bull={bias_struct['bos_bullish']} bear={bias_struct['bos_bearish']}")
    print(f"   CHoCH     : bull={bias_struct['choch_bullish']} bear={bias_struct['choch_bearish']}")
    print(f"   Swing H   : {bias_struct['last_swing_high']}")
    print(f"   Swing L   : {bias_struct['last_swing_low']}")
    print(f"   Swing highs found: {len(bias_struct['swing_highs'])}")
    print(f"   Swing lows  found: {len(bias_struct['swing_lows'])}")
    print(f"   PD Zone   : {bias_pd['zone']} ({bias_pd['position_pct']:.1f}%)")
    print(f"   Liquidity : ssl={bias_liq['ssl_swept']} bsl={bias_liq['bsl_swept']}")
    print(f"   RSI bias  : {bias_df.iloc[-1]['rsi']:.1f}")

    # --- ENTRY (5m) ---
    entry_df['rsi']     = _calculate_rsi(entry_df['close'], 14)
    entry_df['vol_avg'] = entry_df['volume'].rolling(20).mean()
    entry_ob  = detect_order_blocks(entry_df, lookback=30)
    entry_fvg = detect_fvg(entry_df, lookback=20)
    entry_liq = detect_liquidity_sweep(entry_df, lookback=15)

    current_price = entry_df.iloc[-1]['close']
    volume_spike  = entry_df.iloc[-1]['volume'] > entry_df.iloc[-1]['vol_avg'] * 1.3

    print(f"\n📊 ENTRY (5m):")
    print(f"   Price     : {current_price}")
    print(f"   RSI entry : {entry_df.iloc[-1]['rsi']:.1f}")
    print(f"   Vol spike : {volume_spike} (vol={entry_df.iloc[-1]['volume']:.0f} avg={entry_df.iloc[-1]['vol_avg']:.0f})")
    print(f"   OB bull   : {entry_ob['price_in_bullish_ob']} | OB bear: {entry_ob['price_in_bearish_ob']}")
    print(f"   FVG bull  : {entry_fvg['price_in_bullish_fvg']} | FVG bear: {entry_fvg['price_in_bearish_fvg']}")
    print(f"   Liq ssl   : {entry_liq['ssl_swept']} | bsl: {entry_liq['bsl_swept']}")
    print(f"   OBs found : bull={len(entry_ob['all_bullish_obs'])} bear={len(entry_ob['all_bearish_obs'])}")
    print(f"   FVGs found: bull={len(entry_fvg['all_bullish_fvgs'])} bear={len(entry_fvg['all_bearish_fvgs'])}")

    # --- ATR ---
    atr_df = bias_df.copy()
    atr_df['atr'] = _calculate_atr(atr_df, 14)
    atr_value = atr_df.iloc[-1]['atr']
    print(f"\n📊 ATR (15m): {atr_value:.6f} ({(atr_value/current_price)*100:.3f}% of price)")

    # --- SCORING SIMULASI ---
    print(f"\n📊 SCORING SIMULASI:")
    direction = 'LONG' if bias_struct['bias'] == 'BULLISH' else 'SHORT'
    if bias_struct['bias'] == 'NEUTRAL':
        print(f"   ❌ Bias NEUTRAL - tidak bisa score")
        return

    print(f"   Direction : {direction}")

    in_ob  = entry_ob['price_in_bullish_ob'] if direction=='LONG' else entry_ob['price_in_bearish_ob']
    in_fvg = entry_fvg['price_in_bullish_fvg'] if direction=='LONG' else entry_fvg['price_in_bearish_fvg']
    liq    = (bias_liq['ssl_swept'] or entry_liq['ssl_swept']) if direction=='LONG' else (bias_liq['bsl_swept'] or entry_liq['bsl_swept'])
    bos    = bias_struct['bos_bullish'] if direction=='LONG' else bias_struct['bos_bearish']

    score = 0
    score += 2 if bos else 0
    score += 1 if (bias_struct['choch_bullish'] if direction=='LONG' else bias_struct['choch_bearish']) else 0
    score += 2 if liq else 0
    score += 2 if in_ob else 0
    score += 1 if in_fvg else 0
    score += 1 if volume_spike else 0
    score += 1 if bias_pd['in_ote'] else 0

    print(f"   BOS(+2)   : {bos} → +{2 if bos else 0}")
    print(f"   CHoCH(+1) : {bias_struct['choch_bullish'] if direction=='LONG' else bias_struct['choch_bearish']} → +{1 if (bias_struct['choch_bullish'] if direction=='LONG' else bias_struct['choch_bearish']) else 0}")
    print(f"   Liq(+2)   : {liq} → +{2 if liq else 0}")
    print(f"   OB(+2)    : {in_ob} → +{2 if in_ob else 0}")
    print(f"   FVG(+1)   : {in_fvg} → +{1 if in_fvg else 0}")
    print(f"   VolSpike(+1): {volume_spike} → +{1 if volume_spike else 0}")
    print(f"   OTE(+1)   : {bias_pd['in_ote']} → +{1 if bias_pd['in_ote'] else 0}")
    print(f"   TOTAL SCORE: {score}/10")

    # Premium/Discount check — pakai logika baru
    pd_ok = True
    if direction == 'LONG' and bias_pd['zone'] == 'PREMIUM':
        pd_ok = bias_struct['choch_bullish'] or bias_liq['ssl_swept']
        if not pd_ok:
            print(f"   ⚠️  LONG di PREMIUM - butuh CHoCH/SSL: {pd_ok}")
    if direction == 'SHORT' and bias_pd['zone'] == 'DISCOUNT':
        pd_ok = bias_struct['choch_bearish'] or bias_liq['bsl_swept']
        if not pd_ok:
            print(f"   ⚠️  SHORT di DISCOUNT - butuh CHoCH/BSL: {pd_ok}")

    if not pd_ok:
        print(f"   ❌ REJECT: PD Zone filter gagal")

    # Kondisi yang dibutuhkan untuk signal muncul
    print(f"\n💡 KAPAN SIGNAL AKAN MUNCUL ({direction}):")
    if direction == 'SHORT' and bias_pd['zone'] == 'DISCOUNT':
        print(f"   Market sedang free fall di DISCOUNT zone")
        print(f"   Tunggu salah satu:")
        print(f"   1. Harga naik ke PREMIUM (>55% range = >{bias_pd['recent_low'] + (bias_pd['recent_high']-bias_pd['recent_low'])*0.55:.4f})")
        print(f"   2. Ada BSL sweep (spike di atas {bias_liq['bsl_level']:.4f} lalu reject)")
        print(f"   3. CHoCH bearish terbentuk di 15m")
    elif direction == 'LONG' and bias_pd['zone'] == 'PREMIUM':
        print(f"   Market di PREMIUM zone")
        print(f"   Tunggu: SSL sweep atau CHoCH bullish")
    else:
        print(f"   Setup hampir siap! Butuh: liq={liq} ob={in_ob} fvg={in_fvg}")

    # Kill zone
    from session_management_system import get_current_session_parameters
    sp = get_current_session_parameters(1000, {}, {})
    sess = sp['session']
    kz = is_in_kill_zone(sess)
    print(f"\n📊 SESSION: {sess} | Kill Zone: {kz['in_kill_zone']} | UTC hour: {kz['current_hour_utc']}")

    min_scores = {'DEAD_ZONE':6,'ASIA':4,'LONDON':4,'NEWYORK':3}
    min_s = min_scores.get(sess, 4)
    print(f"   Min score needed: {min_s}")
    if score >= min_s and pd_ok:
        print(f"   ✅ LOLOS SCORING!")
    else:
        print(f"   ❌ TIDAK LOLOS (score={score} min={min_s} pd_ok={pd_ok})")

if __name__ == '__main__':
    # Test beberapa pair top volume
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
    for s in symbols:
        test_symbol(s)
    print("\n\nDone.")
