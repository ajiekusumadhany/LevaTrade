"""
ICT / SMC Strategy Engine
Implementasi Inner Circle Trader (ICT) & Smart Money Concepts (SMC)

Konsep yang diimplementasikan:
1. Market Structure - BOS (Break of Structure) & CHoCH (Change of Character)
2. Order Block (OB) - Bullish & Bearish
3. Fair Value Gap (FVG) - Imbalance area
4. Liquidity Sweep - Buy/Sell side liquidity grab
5. Premium & Discount Zone - Fibonacci 50% equilibrium
6. Kill Zone - Waktu entry optimal per sesi
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List, Tuple


# ==================
# HELPER FUNCTIONS (standalone, no circular import)
# ==================

def _calculate_ema(data: pd.Series, period: int) -> pd.Series:
    return data.ewm(span=period, adjust=False).mean()

def _calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    delta = data.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def _calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tr = pd.concat([
        df['high'] - df['low'],
        abs(df['high'] - df['close'].shift()),
        abs(df['low'] - df['close'].shift())
    ], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


# ==================
# MARKET STRUCTURE
# ==================

def detect_market_structure(df: pd.DataFrame, swing_length: int = 5) -> Dict:
    """
    Deteksi struktur market: HH, HL, LH, LL
    BOS = Break of Structure (konfirmasi trend)
    CHoCH = Change of Character (potensi reversal)
    """
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    n = len(df)

    # Cari swing highs dan lows
    swing_highs = []
    swing_lows = []

    for i in range(swing_length, n - swing_length):
        # Swing High: titik tertinggi di antara swing_length candle kiri & kanan
        if all(highs[i] >= highs[i - j] for j in range(1, swing_length + 1)) and \
           all(highs[i] >= highs[i + j] for j in range(1, swing_length + 1)):
            swing_highs.append((i, highs[i]))

        # Swing Low: titik terendah
        if all(lows[i] <= lows[i - j] for j in range(1, swing_length + 1)) and \
           all(lows[i] <= lows[i + j] for j in range(1, swing_length + 1)):
            swing_lows.append((i, lows[i]))

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return {
            'bias': 'NEUTRAL',
            'bos': False, 'bos_bullish': False, 'bos_bearish': False,
            'choch': False, 'choch_bullish': False, 'choch_bearish': False,
            'last_swing_high': None, 'last_swing_low': None,
            'swing_highs': swing_highs, 'swing_lows': swing_lows,
            'bullish_structure': False, 'bearish_structure': False,
        }

    # Ambil 2 swing terakhir
    sh1_idx, sh1_val = swing_highs[-2]
    sh2_idx, sh2_val = swing_highs[-1]
    sl1_idx, sl1_val = swing_lows[-2]
    sl2_idx, sl2_val = swing_lows[-1]

    current_price = closes[-1]

    # Tentukan bias berdasarkan struktur HH/HL atau LH/LL
    bullish_structure = sh2_val > sh1_val and sl2_val > sl1_val  # HH + HL
    bearish_structure = sh2_val < sh1_val and sl2_val < sl1_val  # LH + LL

    # BOS: harga break swing high/low terakhir (konfirmasi trend)
    bos_bullish = current_price > sh2_val  # Break above last swing high
    bos_bearish = current_price < sl2_val  # Break below last swing low

    # CHoCH: struktur berubah (reversal signal)
    choch_bullish = bearish_structure and current_price > sh2_val
    choch_bearish = bullish_structure and current_price < sl2_val

    if bullish_structure or bos_bullish:
        bias = 'BULLISH'
    elif bearish_structure or bos_bearish:
        bias = 'BEARISH'
    else:
        bias = 'NEUTRAL'

    return {
        'bias': bias,
        'bos': bos_bullish or bos_bearish,
        'bos_bullish': bos_bullish,
        'bos_bearish': bos_bearish,
        'choch': choch_bullish or choch_bearish,
        'choch_bullish': choch_bullish,
        'choch_bearish': choch_bearish,
        'last_swing_high': sh2_val,
        'last_swing_low': sl2_val,
        'swing_highs': swing_highs,
        'swing_lows': swing_lows,
        'bullish_structure': bullish_structure,
        'bearish_structure': bearish_structure,
    }


# ==================
# ORDER BLOCK (OB)
# ==================

def detect_order_blocks(df: pd.DataFrame, lookback: int = 30) -> Dict:
    """
    Order Block = candle terakhir sebelum impulse move besar.
    Bullish OB: candle bearish terakhir sebelum impulse naik
    Bearish OB: candle bullish terakhir sebelum impulse turun
    """
    opens = df['open'].values
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    n = len(df)

    bullish_obs = []
    bearish_obs = []

    # Scan dari belakang
    for i in range(max(3, n - lookback), n - 3):
        body_size = abs(closes[i] - opens[i])
        avg_body = np.mean([abs(closes[j] - opens[j]) for j in range(max(0, i - 10), i)])
        if avg_body == 0:
            continue

        # Impulse move setelah candle ini (3 candle ke depan)
        future_move_up = max(closes[i+1:i+4]) - closes[i]
        future_move_down = closes[i] - min(closes[i+1:i+4])
        impulse_threshold = avg_body * 1.5

        # Bullish OB: candle bearish (close < open) diikuti impulse naik
        if closes[i] < opens[i] and future_move_up > impulse_threshold:
            bullish_obs.append({
                'index': i,
                'top': opens[i],      # Top of bearish candle = open
                'bottom': closes[i],  # Bottom = close
                'mid': (opens[i] + closes[i]) / 2,
                'strength': future_move_up / avg_body
            })

        # Bearish OB: candle bullish (close > open) diikuti impulse turun
        if closes[i] > opens[i] and future_move_down > impulse_threshold:
            bearish_obs.append({
                'index': i,
                'top': closes[i],     # Top of bullish candle = close
                'bottom': opens[i],   # Bottom = open
                'mid': (closes[i] + opens[i]) / 2,
                'strength': future_move_down / avg_body
            })

    current_price = closes[-1]

    # Cari OB yang paling relevan (terdekat dengan harga saat ini)
    nearest_bullish_ob = None
    nearest_bearish_ob = None

    # Bullish OB: harga harus di atas OB (OB di bawah harga = support)
    valid_bull_obs = [ob for ob in bullish_obs if ob['bottom'] < current_price < ob['top'] * 1.05]
    if valid_bull_obs:
        nearest_bullish_ob = max(valid_bull_obs, key=lambda x: x['bottom'])

    # Bearish OB: harga harus di bawah OB (OB di atas harga = resistance)
    valid_bear_obs = [ob for ob in bearish_obs if ob['top'] * 0.95 < current_price < ob['top']]
    if valid_bear_obs:
        nearest_bearish_ob = min(valid_bear_obs, key=lambda x: x['top'])

    return {
        'bullish_ob': nearest_bullish_ob,
        'bearish_ob': nearest_bearish_ob,
        'price_in_bullish_ob': nearest_bullish_ob is not None,
        'price_in_bearish_ob': nearest_bearish_ob is not None,
        'all_bullish_obs': bullish_obs[-5:],
        'all_bearish_obs': bearish_obs[-5:],
    }


# ==================
# FAIR VALUE GAP (FVG)
# ==================

def detect_fvg(df: pd.DataFrame, lookback: int = 20) -> Dict:
    """
    FVG = gap antara candle 1 dan candle 3 (candle 2 adalah impulse).
    Bullish FVG: low[i+2] > high[i]  → gap di atas (harga mungkin balik fill)
    Bearish FVG: high[i+2] < low[i]  → gap di bawah
    """
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    n = len(df)

    bullish_fvgs = []
    bearish_fvgs = []

    for i in range(max(0, n - lookback - 2), n - 2):
        # Bullish FVG: low candle ke-3 > high candle ke-1
        if lows[i + 2] > highs[i]:
            gap_size = lows[i + 2] - highs[i]
            bullish_fvgs.append({
                'top': lows[i + 2],
                'bottom': highs[i],
                'mid': (lows[i + 2] + highs[i]) / 2,
                'size': gap_size,
                'index': i + 1
            })

        # Bearish FVG: high candle ke-3 < low candle ke-1
        if highs[i + 2] < lows[i]:
            gap_size = lows[i] - highs[i + 2]
            bearish_fvgs.append({
                'top': lows[i],
                'bottom': highs[i + 2],
                'mid': (lows[i] + highs[i + 2]) / 2,
                'size': gap_size,
                'index': i + 1
            })

    current_price = closes[-1]

    # Cari FVG yang belum ter-fill dan relevan dengan harga saat ini
    nearest_bullish_fvg = None
    nearest_bearish_fvg = None

    # Bullish FVG di bawah harga (support / area beli)
    valid_bull_fvgs = [f for f in bullish_fvgs if f['bottom'] < current_price < f['top'] * 1.02]
    if valid_bull_fvgs:
        nearest_bullish_fvg = max(valid_bull_fvgs, key=lambda x: x['bottom'])

    # Bearish FVG di atas harga (resistance / area jual)
    valid_bear_fvgs = [f for f in bearish_fvgs if f['bottom'] * 0.98 < current_price < f['top']]
    if valid_bear_fvgs:
        nearest_bearish_fvg = min(valid_bear_fvgs, key=lambda x: x['top'])

    return {
        'bullish_fvg': nearest_bullish_fvg,
        'bearish_fvg': nearest_bearish_fvg,
        'price_in_bullish_fvg': nearest_bullish_fvg is not None,
        'price_in_bearish_fvg': nearest_bearish_fvg is not None,
        'all_bullish_fvgs': bullish_fvgs[-5:],
        'all_bearish_fvgs': bearish_fvgs[-5:],
    }


# ==================
# LIQUIDITY SWEEP
# ==================

def detect_liquidity_sweep(df: pd.DataFrame, lookback: int = 20) -> Dict:
    """
    Liquidity Sweep = harga spike melewati equal highs/lows lalu balik.
    Buy Side Liquidity (BSL): di atas equal highs → sweep = bearish reversal
    Sell Side Liquidity (SSL): di bawah equal lows → sweep = bullish reversal
    """
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    n = len(df)

    # Cari equal highs (BSL) dan equal lows (SSL) dalam lookback
    recent_highs = highs[max(0, n - lookback - 1): n - 1]
    recent_lows = lows[max(0, n - lookback - 1): n - 1]

    if len(recent_highs) < 3:
        return {'bsl_swept': False, 'ssl_swept': False, 'sweep_direction': None}

    # Equal highs: beberapa high yang berdekatan (dalam 0.1% range)
    max_recent_high = np.max(recent_highs)
    min_recent_low = np.min(recent_lows)

    current_high = highs[-1]
    current_low = lows[-1]
    current_close = closes[-1]
    prev_close = closes[-2]

    # BSL Sweep: spike di atas recent high tapi close di bawahnya (rejection)
    bsl_swept = (current_high > max_recent_high * 1.001) and (current_close < max_recent_high)

    # SSL Sweep: spike di bawah recent low tapi close di atasnya (rejection)
    ssl_swept = (current_low < min_recent_low * 0.999) and (current_close > min_recent_low)

    sweep_direction = None
    if ssl_swept:
        sweep_direction = 'BULLISH'  # SSL sweep → expect move up
    elif bsl_swept:
        sweep_direction = 'BEARISH'  # BSL sweep → expect move down

    return {
        'bsl_swept': bsl_swept,
        'ssl_swept': ssl_swept,
        'sweep_direction': sweep_direction,
        'bsl_level': max_recent_high,
        'ssl_level': min_recent_low,
        'liquidity_grabbed': bsl_swept or ssl_swept,
    }


# ==================
# PREMIUM & DISCOUNT ZONE
# ==================

def get_premium_discount_zone(df: pd.DataFrame, lookback: int = 50) -> Dict:
    """
    Premium = di atas 50% Fibonacci (mahal → cari SELL)
    Discount = di bawah 50% Fibonacci (murah → cari BUY)
    Equilibrium = tepat di 50%
    """
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    n = len(df)

    recent_high = np.max(highs[max(0, n - lookback):])
    recent_low = np.min(lows[max(0, n - lookback):])
    current_price = closes[-1]

    if recent_high == recent_low:
        return {'zone': 'EQUILIBRIUM', 'fib_50': current_price, 'position_pct': 50.0}

    fib_50 = (recent_high + recent_low) / 2
    fib_618 = recent_low + (recent_high - recent_low) * 0.618  # OTE zone atas
    fib_382 = recent_low + (recent_high - recent_low) * 0.382  # OTE zone bawah

    position_pct = ((current_price - recent_low) / (recent_high - recent_low)) * 100

    if position_pct > 55:
        zone = 'PREMIUM'
    elif position_pct < 45:
        zone = 'DISCOUNT'
    else:
        zone = 'EQUILIBRIUM'

    # OTE (Optimal Trade Entry): 61.8% - 78.6% retracement
    ote_buy_zone = current_price <= fib_618 and current_price >= fib_382
    ote_sell_zone = current_price >= fib_382 and current_price <= fib_618

    return {
        'zone': zone,
        'fib_50': fib_50,
        'fib_382': fib_382,
        'fib_618': fib_618,
        'recent_high': recent_high,
        'recent_low': recent_low,
        'position_pct': position_pct,
        'in_discount': zone == 'DISCOUNT',
        'in_premium': zone == 'PREMIUM',
        'in_ote': ote_buy_zone,
    }


# ==================
# KILL ZONE CHECK
# ==================

def is_in_kill_zone(session: str) -> Dict:
    """
    Untuk swing trading D/4H/1H, kill zone tidak seketat scalping.
    Tetap dipakai sebagai bonus score saja.
    London open (07:00-10:00 UTC) dan NY open (13:00-16:00 UTC)
    adalah waktu terbaik untuk entry swing.
    """
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour

    # Waktu terbaik untuk entry swing (volume tinggi)
    kill_zones = {
        'ASIA':      [(1, 8)],           # Asia session
        'LONDON':    [(7, 16)],          # London + overlap
        'NEWYORK':   [(13, 22)],         # NY session
        'DEAD_ZONE': [(0, 24)],          # Swing: semua jam valid
    }

    zones = kill_zones.get(session, [(0, 24)])
    in_kz = any(start <= hour < end for start, end in zones)

    # NY Lunch masih dihindari untuk entry baru
    ny_lunch = 17 <= hour < 19

    return {
        'in_kill_zone': in_kz,
        'ny_lunch_avoid': ny_lunch,
        'current_hour_utc': hour,
        'session': session,
    }


# ==================
# MAIN ICT SIGNAL ANALYZER
# ==================

def calculate_ict_indicators(tf_data: Dict) -> Optional[Dict]:
    """
    Hitung semua ICT indicators dari multi-timeframe data.
    Menggantikan calculate_multi_tf_indicators() yang lama.
    """
    try:
        bias_df = tf_data['bias'].copy()
        entry_df = tf_data['entry'].copy()
        atr_df = tf_data['atr'].copy()

        # ATR untuk risk management
        atr_df['atr'] = _calculate_atr(atr_df, 14)
        atr_value = atr_df.iloc[-1]['atr']

        # Volume
        entry_df['vol_avg'] = entry_df['volume'].rolling(20).mean()

        # ---- ICT Analysis pada Bias TF (15m) ----
        bias_structure = detect_market_structure(bias_df, swing_length=3)
        bias_pd = get_premium_discount_zone(bias_df, lookback=50)
        bias_liquidity = detect_liquidity_sweep(bias_df, lookback=20)

        # ---- ICT Analysis pada Entry TF (5m) ----
        entry_ob = detect_order_blocks(entry_df, lookback=30)
        entry_fvg = detect_fvg(entry_df, lookback=20)
        entry_structure = detect_market_structure(entry_df, swing_length=3)
        entry_liquidity = detect_liquidity_sweep(entry_df, lookback=15)

        # Trigger TF (1H) — pure price action, bukan EMA
        trigger_info = None
        if tf_data.get('trigger') is not None:
            trigger_df = tf_data['trigger'].copy()
            # ICT trigger: candle close di atas/bawah candle sebelumnya (momentum konfirmasi)
            last_close  = trigger_df.iloc[-1]['close']
            last_open   = trigger_df.iloc[-1]['open']
            prev_close  = trigger_df.iloc[-2]['close']
            prev_high   = trigger_df.iloc[-2]['high']
            prev_low    = trigger_df.iloc[-2]['low']
            trigger_info = {
                'above_ema': last_close > prev_high,   # Close di atas high candle sebelumnya = bullish engulf
                'momentum_up': last_close > last_open, # Candle bullish
                'close': last_close,
            }

        current_price = entry_df.iloc[-1]['close']
        volume_spike  = entry_df.iloc[-1]['volume'] > entry_df.iloc[-1]['vol_avg'] * 1.3

        return {
            'bias': bias_structure,
            'bias_pd': bias_pd,
            'bias_liquidity': bias_liquidity,
            'entry_ob': entry_ob,
            'entry_fvg': entry_fvg,
            'entry_structure': entry_structure,
            'entry_liquidity': entry_liquidity,
            'trigger': trigger_info,
            'atr_value': atr_value,
            'current_price': current_price,
            'volume_spike': volume_spike,
            'bias_rsi': 50,   # placeholder
            'entry_rsi': 50,  # placeholder
        }

    except Exception as e:
        print(f"❌ Error calculating ICT indicators: {e}")
        return None


def analyze_ict_signal(symbol: str, ict_ind: Dict, session_params: Dict, tf_config: Dict) -> Optional[Dict]:
    """
    ICT/SMC Signal Logic - MURNI ICT, tanpa RSI/EMA/MACD.

    Entry Model:
    1. Market Structure (BOS/CHoCH) di 15m → bias
    2. Premium/Discount Zone (Fib 50%) → arah entry
    3. Liquidity Sweep (SSL/BSL) → konfirmasi smart money
    4. Order Block atau FVG di 5m → zona entry presisi
    5. Kill Zone → timing optimal
    6. Scoring → minimum confluence
    """
    try:
        current_session = session_params['session']
        current_price   = ict_ind['current_price']
        atr_value       = ict_ind['atr_value']

        bias          = ict_ind['bias']
        bias_pd       = ict_ind['bias_pd']
        bias_liquidity= ict_ind['bias_liquidity']
        entry_ob      = ict_ind['entry_ob']
        entry_fvg     = ict_ind['entry_fvg']
        entry_liquidity= ict_ind['entry_liquidity']
        trigger       = ict_ind['trigger']

        # ── Log state ──────────────────────────────────────────
        print(f"  📊 [{symbol}] "
              f"bias={bias['bias']} bos_bull={bias['bos_bullish']} bos_bear={bias['bos_bearish']} "
              f"choch_bull={bias['choch_bullish']} choch_bear={bias['choch_bearish']} "
              f"pd={bias_pd['zone']}({bias_pd['position_pct']:.0f}%) "
              f"ssl={bias_liquidity['ssl_swept']} bsl={bias_liquidity['bsl_swept']} "
              f"OB_bull={entry_ob['price_in_bullish_ob']} OB_bear={entry_ob['price_in_bearish_ob']} "
              f"FVG_bull={entry_fvg['price_in_bullish_fvg']} FVG_bear={entry_fvg['price_in_bearish_fvg']}")

        # ══════════════════════════════════════════════════════
        # STEP 1: BIAS — Market Structure (15m)
        # ══════════════════════════════════════════════════════
        bias_bullish = bias['bias'] == 'BULLISH'
        bias_bearish = bias['bias'] == 'BEARISH'

        if not (bias_bullish or bias_bearish):
            print(f"  ❌ [{symbol}] REJECT: bias NEUTRAL")
            return None

        direction = 'LONG' if bias_bullish else 'SHORT'

        # ══════════════════════════════════════════════════════
        # STEP 2: PREMIUM / DISCOUNT ZONE
        # Ideal: LONG di Discount, SHORT di Premium
        # Reversal boleh kalau ada CHoCH + liquidity sweep
        # ══════════════════════════════════════════════════════
        if direction == 'LONG' and bias_pd['in_premium']:
            # Harga mahal tapi mau LONG → harus ada bukti reversal
            if not (bias['choch_bullish'] or bias_liquidity['ssl_swept']):
                print(f"  ❌ [{symbol}] REJECT: LONG di PREMIUM tanpa CHoCH/SSL sweep")
                return None

        if direction == 'SHORT' and bias_pd['in_discount']:
            # Harga murah tapi mau SHORT → harus ada bukti reversal
            if not (bias['choch_bearish'] or bias_liquidity['bsl_swept']):
                print(f"  ❌ [{symbol}] REJECT: SHORT di DISCOUNT tanpa CHoCH/BSL sweep")
                return None

        # ══════════════════════════════════════════════════════
        # STEP 3: LIQUIDITY SWEEP (konfirmasi smart money)
        # ══════════════════════════════════════════════════════
        if direction == 'LONG':
            liquidity_confirmed = bias_liquidity['ssl_swept'] or entry_liquidity['ssl_swept']
        else:
            liquidity_confirmed = bias_liquidity['bsl_swept'] or entry_liquidity['bsl_swept']

        # ══════════════════════════════════════════════════════
        # STEP 4: ORDER BLOCK / FVG (5m) — zona entry presisi
        # ══════════════════════════════════════════════════════
        in_ob  = False
        in_fvg = False
        entry_zone_top    = current_price
        entry_zone_bottom = current_price
        setup_type = 'ICT-STRUCTURE'

        if direction == 'LONG':
            if entry_ob['price_in_bullish_ob']:
                in_ob = True
                ob = entry_ob['bullish_ob']
                entry_zone_top    = ob['top']
                entry_zone_bottom = ob['bottom']
                setup_type = 'ICT-OB-LONG'
            elif entry_fvg['price_in_bullish_fvg']:
                in_fvg = True
                fvg = entry_fvg['bullish_fvg']
                entry_zone_top    = fvg['top']
                entry_zone_bottom = fvg['bottom']
                setup_type = 'ICT-FVG-LONG'
        else:
            if entry_ob['price_in_bearish_ob']:
                in_ob = True
                ob = entry_ob['bearish_ob']
                entry_zone_top    = ob['top']
                entry_zone_bottom = ob['bottom']
                setup_type = 'ICT-OB-SHORT'
            elif entry_fvg['price_in_bearish_fvg']:
                in_fvg = True
                fvg = entry_fvg['bearish_fvg']
                entry_zone_top    = fvg['top']
                entry_zone_bottom = fvg['bottom']
                setup_type = 'ICT-FVG-SHORT'

        # ══════════════════════════════════════════════════════
        # STEP 5: KILL ZONE — timing optimal per sesi
        # ══════════════════════════════════════════════════════
        kz = is_in_kill_zone(current_session)
        kill_zone_bonus = kz['in_kill_zone']

        # NY Lunch: skip semua sesi
        if kz['ny_lunch_avoid']:
            print(f"  ❌ [{symbol}] REJECT: NY Lunch (17-19 UTC)")
            return None

        # Dead Zone: hanya masuk kalau ada BOS/CHoCH + OB/FVG
        if current_session == 'DEAD_ZONE':
            if not (bias['bos'] or bias['choch']):
                print(f"  ❌ [{symbol}] REJECT: DEAD_ZONE butuh BOS/CHoCH")
                return None
            if not (in_ob or in_fvg):
                print(f"  ❌ [{symbol}] REJECT: DEAD_ZONE butuh OB/FVG")
                return None

        # ══════════════════════════════════════════════════════
        # STEP 6: SESSION FILTER — pure ICT per sesi
        # ══════════════════════════════════════════════════════
        if current_session == 'ASIA':
            # Asia: mean reversion ke OB/FVG, butuh minimal OB atau FVG
            if not (in_ob or in_fvg):
                print(f"  ❌ [{symbol}] REJECT: ASIA butuh OB/FVG (ob={in_ob} fvg={in_fvg})")
                return None

        elif current_session == 'LONDON':
            # London: breakout, butuh BOS + OB/FVG atau liquidity sweep
            has_entry_zone = in_ob or in_fvg
            has_confirmation = bias['bos'] or liquidity_confirmed
            if not (has_entry_zone or (has_confirmation and liquidity_confirmed)):
                print(f"  ❌ [{symbol}] REJECT: LONDON butuh (OB/FVG) atau (BOS+liquidity) "
                      f"(ob={in_ob} fvg={in_fvg} bos={bias['bos']} liq={liquidity_confirmed})")
                return None

        elif current_session == 'NEWYORK':
            # NY: momentum, butuh minimal liquidity sweep atau OB/FVG
            if not (liquidity_confirmed or in_ob or in_fvg):
                print(f"  ❌ [{symbol}] REJECT: NEWYORK butuh liquidity/OB/FVG "
                      f"(liq={liquidity_confirmed} ob={in_ob} fvg={in_fvg})")
                return None

        # ══════════════════════════════════════════════════════
        # STEP 7: TRIGGER (1H) — konfirmasi momentum candle
        # Untuk swing: cukup candle searah, tidak harus engulf
        # ══════════════════════════════════════════════════════
        if tf_config.get('use_trigger') and trigger is not None:
            if direction == 'LONG':
                # Candle 1H harus bullish (close > open)
                trigger_ok = trigger['momentum_up']
            else:
                # Candle 1H harus bearish (close < open) = not momentum_up
                trigger_ok = not trigger['momentum_up']
            if not trigger_ok:
                print(f"  ❌ [{symbol}] REJECT: 1H trigger gagal - candle tidak searah {direction}")
                return None

        # ══════════════════════════════════════════════════════
        # STEP 8: ICT CONFLUENCE SCORE
        # Semua berbasis ICT — tidak ada RSI/MACD
        # ══════════════════════════════════════════════════════
        score = 0
        bos_dir = bias['bos_bullish'] if direction == 'LONG' else bias['bos_bearish']
        choch_dir = bias['choch_bullish'] if direction == 'LONG' else bias['choch_bearish']

        score += 3 if bos_dir else 0          # BOS = konfirmasi trend kuat
        score += 2 if choch_dir else 0        # CHoCH = reversal signal
        score += 2 if liquidity_confirmed else 0  # Liquidity sweep
        score += 2 if in_ob else 0            # Order Block
        score += 1 if in_fvg else 0           # Fair Value Gap
        score += 1 if kill_zone_bonus else 0  # Kill Zone timing
        score += 1 if bias_pd['in_discount'] and direction == 'LONG' else 0  # Ideal PD
        score += 1 if bias_pd['in_premium']  and direction == 'SHORT' else 0 # Ideal PD

        min_scores = {
            'DEAD_ZONE': 5,
            'ASIA':      4,
            'LONDON':    3,
            'NEWYORK':   3,
        }
        min_score = min_scores.get(current_session, 3)

        if score < min_score:
            print(f"  ❌ [{symbol}] REJECT: Score {score}/{min_score} "
                  f"bos={bos_dir} choch={choch_dir} liq={liquidity_confirmed} "
                  f"ob={in_ob} fvg={in_fvg} kz={kill_zone_bonus}")
            return None

        # ══════════════════════════════════════════════════════
        # STEP 9: SL & TP — ICT style (swing points)
        # ══════════════════════════════════════════════════════
        if direction == 'LONG':
            # SL: di bawah swing low terakhir (atau bawah OB/FVG)
            sl_ref = min(
                bias['last_swing_low'] if bias['last_swing_low'] else current_price,
                entry_zone_bottom
            )
            sl_price = sl_ref - (atr_value * 0.15)
            # TP: ke swing high terakhir
            if bias['last_swing_high'] and bias['last_swing_high'] > current_price:
                tp_price = bias['last_swing_high']
            else:
                tp_price = current_price + (atr_value * 2.5)
        else:
            # SL: di atas swing high terakhir (atau atas OB/FVG)
            sl_ref = max(
                bias['last_swing_high'] if bias['last_swing_high'] else current_price,
                entry_zone_top
            )
            sl_price = sl_ref + (atr_value * 0.15)
            # TP: ke swing low terakhir
            if bias['last_swing_low'] and bias['last_swing_low'] < current_price:
                tp_price = bias['last_swing_low']
            else:
                tp_price = current_price - (atr_value * 2.5)

        sl_distance = abs(current_price - sl_price)
        tp_distance = abs(tp_price - current_price)

        if sl_distance == 0:
            print(f"  ❌ [{symbol}] REJECT: SL distance = 0")
            return None

        rr_ratio = tp_distance / sl_distance

        if rr_ratio < 1.5:
            print(f"  ❌ [{symbol}] REJECT: R:R {rr_ratio:.2f} < 1.5")
            return None

        leverage = min(session_params.get('max_leverage', 15), 15)

        print(f"  ✅ [{symbol}] SIGNAL {direction} | {setup_type} | "
              f"score={score} R:R={rr_ratio:.2f} | "
              f"kz={kill_zone_bonus} ob={in_ob} fvg={in_fvg} liq={liquidity_confirmed} | "
              f"pd={bias_pd['zone']}")

        return {
            'symbol': symbol,
            'direction': direction,
            'close': current_price,
            'entry_low': entry_zone_bottom,
            'entry_high': entry_zone_top,
            'sl': sl_price,
            'tp': tp_price,
            'leverage': leverage,
            'atr_value': atr_value,
            'sl_percent': (sl_distance / current_price) * 100,
            'rr_ratio': rr_ratio,
            'setup_type': setup_type,
            'lev_mode': f'{leverage}x',
            'rsi_level': 50,  # placeholder untuk kompatibilitas AI
            'volume_spike': False,
            'session': current_session,
            'tf_config': tf_config,
            'ict_score': score,
            'kill_zone_active': kill_zone_bonus,
            'liquidity_confirmed': liquidity_confirmed,
            'in_order_block': in_ob,
            'in_fvg': in_fvg,
            # Flags untuk AI reasoning (ICT context)
            'ema_fast_above_slow': bias_bullish,
            'macd_bullish': bias_bullish,
            'rsi_oversold': False,
            'rsi_overbought': False,
            'rsi_neutral': True,
            'volume_confirmation': liquidity_confirmed,
            'volatility_confirmation': atr_value > 0,
            'price_near_support': in_ob and direction == 'LONG',
            'price_near_resistance': in_ob and direction == 'SHORT',
            'trend_alignment': bos_dir,
            'momentum_confirmation': liquidity_confirmed,
            'ema_fast_value': current_price,
            'ema_slow_value': current_price,
            'macd_line_value': 0.0,
            'signal_line_value': 0.0,
            'support_resistance': entry_zone_bottom if direction == 'LONG' else entry_zone_top,
            'price_distance_from_level': abs(current_price - (entry_zone_bottom if direction == 'LONG' else entry_zone_top)),
            'bias_structure': bias['bias'],
            'bos_confirmed': bias['bos'],
            'choch_detected': bias['choch'],
            'pd_zone': bias_pd['zone'],
            'fib_position_pct': bias_pd['position_pct'],
        }

    except Exception as e:
        print(f"  ❌ [{symbol}] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None
