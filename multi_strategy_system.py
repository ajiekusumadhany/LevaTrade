"""
Multi-Strategy System
Menjalankan 5 strategy secara paralel dan memilih sinyal terbaik.

Strategies:
1. ICT_SMC       - Smart Money Concepts (existing)
2. MEAN_REVERSION - Bollinger Bands + Z-Score
3. TREND_FOLLOW  - Supertrend + Donchian Channel
4. FUNDING_RATE  - Funding Rate Bias + Mean Reversion
5. ORDERFLOW     - Volume Delta + CVD (Cumulative Volume Delta)
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List
from ict_smc_strategy import calculate_ict_indicators, analyze_ict_signal


# ══════════════════════════════════════════════════════
# STRATEGY 1: ICT / SMC (wrapper ke existing engine)
# ══════════════════════════════════════════════════════

def run_ict_smc(symbol: str, tf_data: Dict, session_params: Dict, tf_config: Dict) -> Optional[Dict]:
    """Wrapper ke ICT/SMC engine yang sudah ada"""
    indicators = calculate_ict_indicators(tf_data)
    if indicators is None:
        return None
    signal = analyze_ict_signal(symbol, indicators, session_params, tf_config)
    if signal:
        signal['strategy'] = 'ICT_SMC'
        signal['strategy_label'] = '📐 ICT/SMC'
    return signal


# ══════════════════════════════════════════════════════
# STRATEGY 2: MEAN REVERSION (Bollinger Bands + Z-Score)
# ══════════════════════════════════════════════════════

def run_mean_reversion(symbol: str, tf_data: Dict, session_params: Dict) -> Optional[Dict]:
    """
    Mean Reversion menggunakan Bollinger Bands dan Z-Score.
    Entry: harga menyentuh lower/upper band + Z-Score ekstrem
    Exit: kembali ke mean (middle band)
    """
    try:
        df = tf_data['entry'].copy()
        if len(df) < 30:
            return None

        close = df['close']
        atr_df = tf_data['atr'].copy()

        # Bollinger Bands (20, 2)
        bb_period = 20
        bb_std = 2.0
        bb_mid = close.rolling(bb_period).mean()
        bb_std_val = close.rolling(bb_period).std()
        bb_upper = bb_mid + bb_std * bb_std_val
        bb_lower = bb_mid - bb_std * bb_std_val

        # Z-Score (20 period)
        z_score = (close - bb_mid) / bb_std_val

        # ATR untuk SL/TP
        tr = pd.concat([
            atr_df['high'] - atr_df['low'],
            abs(atr_df['high'] - atr_df['close'].shift()),
            abs(atr_df['low'] - atr_df['close'].shift())
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        current_price = close.iloc[-1]
        current_z = z_score.iloc[-1]
        current_bb_upper = bb_upper.iloc[-1]
        current_bb_lower = bb_lower.iloc[-1]
        current_bb_mid = bb_mid.iloc[-1]
        atr_value = atr.iloc[-1]

        # Volume confirmation
        vol_avg = df['volume'].rolling(20).mean().iloc[-1]
        vol_spike = df['volume'].iloc[-1] > vol_avg * 1.2

        direction = None
        score = 0

        # LONG: harga di bawah lower band + Z-Score < -1.5
        if current_price <= current_bb_lower and current_z < -1.5:
            direction = 'LONG'
            score += 3
            if current_z < -2.0:
                score += 1  # Extreme oversold
            if vol_spike:
                score += 1

        # SHORT: harga di atas upper band + Z-Score > 1.5
        elif current_price >= current_bb_upper and current_z > 1.5:
            direction = 'SHORT'
            score += 3
            if current_z > 2.0:
                score += 1  # Extreme overbought
            if vol_spike:
                score += 1

        if direction is None or score < 3:
            return None

        # TP ke middle band, SL di 1.5x ATR dari entry
        if direction == 'LONG':
            tp = current_bb_mid
            sl = current_price - (atr_value * 1.5)
        else:
            tp = current_bb_mid
            sl = current_price + (atr_value * 1.5)

        rr = abs(tp - current_price) / abs(sl - current_price) if abs(sl - current_price) > 0 else 0
        if rr < 1.0:
            return None

        leverage = min(session_params.get('max_leverage', 10), 10)

        return {
            'symbol': symbol,
            'direction': direction,
            'close': current_price,
            'tp': tp,
            'sl': sl,
            'leverage': leverage,
            'atr_value': atr_value,
            'setup_type': f'MR-BB-{"LONG" if direction == "LONG" else "SHORT"}',
            'ict_score': score,
            'strategy': 'MEAN_REVERSION',
            'strategy_label': '📊 Mean Reversion',
            'session': session_params.get('session', 'UNKNOWN'),
            'z_score': round(current_z, 2),
            'bb_position': 'LOWER' if direction == 'LONG' else 'UPPER',
        }

    except Exception as e:
        print(f"❌ [MEAN_REVERSION] Error for {symbol}: {e}")
        return None


# ══════════════════════════════════════════════════════
# STRATEGY 3: TREND FOLLOWING (Supertrend + Donchian)
# ══════════════════════════════════════════════════════

def _supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0):
    """Calculate Supertrend indicator"""
    tr = pd.concat([
        df['high'] - df['low'],
        abs(df['high'] - df['close'].shift()),
        abs(df['low'] - df['close'].shift())
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    hl2 = (df['high'] + df['low']) / 2
    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr

    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)

    for i in range(1, len(df)):
        if df['close'].iloc[i] > upper_band.iloc[i - 1]:
            direction.iloc[i] = 1   # Bullish
        elif df['close'].iloc[i] < lower_band.iloc[i - 1]:
            direction.iloc[i] = -1  # Bearish
        else:
            direction.iloc[i] = direction.iloc[i - 1]

        supertrend.iloc[i] = lower_band.iloc[i] if direction.iloc[i] == 1 else upper_band.iloc[i]

    return supertrend, direction


def run_trend_following(symbol: str, tf_data: Dict, session_params: Dict) -> Optional[Dict]:
    """
    Trend Following menggunakan Supertrend + Donchian Channel.
    Entry: Supertrend flip + breakout Donchian
    """
    try:
        df = tf_data['entry'].copy()
        bias_df = tf_data['bias'].copy()
        if len(df) < 30 or len(bias_df) < 20:
            return None

        close = df['close']

        # Supertrend pada entry TF
        st, st_dir = _supertrend(df, period=10, multiplier=3.0)

        # Donchian Channel (20 period)
        dc_period = 20
        dc_upper = df['high'].rolling(dc_period).max()
        dc_lower = df['low'].rolling(dc_period).min()
        dc_mid = (dc_upper + dc_lower) / 2

        # ATR
        tr = pd.concat([
            df['high'] - df['low'],
            abs(df['high'] - df['close'].shift()),
            abs(df['low'] - df['close'].shift())
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        # Bias dari HTF (EMA 50 vs 200)
        bias_ema50 = bias_df['close'].ewm(span=50, adjust=False).mean()
        bias_ema200 = bias_df['close'].ewm(span=200, adjust=False).mean()
        htf_bullish = bias_ema50.iloc[-1] > bias_ema200.iloc[-1]

        current_price = close.iloc[-1]
        current_st_dir = st_dir.iloc[-1]
        prev_st_dir = st_dir.iloc[-2]
        current_dc_upper = dc_upper.iloc[-1]
        current_dc_lower = dc_lower.iloc[-1]
        atr_value = atr.iloc[-1]

        # Volume
        vol_avg = df['volume'].rolling(20).mean().iloc[-1]
        vol_confirm = df['volume'].iloc[-1] > vol_avg * 1.3

        direction = None
        score = 0

        # LONG: Supertrend flip ke bullish + breakout Donchian upper + HTF bullish
        if current_st_dir == 1 and prev_st_dir == -1:  # Fresh flip
            if htf_bullish:
                direction = 'LONG'
                score += 4
            elif current_price > current_dc_upper:
                direction = 'LONG'
                score += 3
        elif current_st_dir == 1 and current_price > current_dc_upper and htf_bullish:
            direction = 'LONG'
            score += 3

        # SHORT: Supertrend flip ke bearish + breakdown Donchian lower + HTF bearish
        elif current_st_dir == -1 and prev_st_dir == 1:  # Fresh flip
            if not htf_bullish:
                direction = 'SHORT'
                score += 4
            elif current_price < current_dc_lower:
                direction = 'SHORT'
                score += 3
        elif current_st_dir == -1 and current_price < current_dc_lower and not htf_bullish:
            direction = 'SHORT'
            score += 3

        if vol_confirm:
            score += 1

        if direction is None or score < 3:
            return None

        # SL di Supertrend line, TP di 2x ATR
        if direction == 'LONG':
            sl = st.iloc[-1] - (atr_value * 0.2)
            tp = current_price + (atr_value * 2.5)
        else:
            sl = st.iloc[-1] + (atr_value * 0.2)
            tp = current_price - (atr_value * 2.5)

        rr = abs(tp - current_price) / abs(sl - current_price) if abs(sl - current_price) > 0 else 0
        if rr < 1.5:
            return None

        leverage = min(session_params.get('max_leverage', 10), 15)

        return {
            'symbol': symbol,
            'direction': direction,
            'close': current_price,
            'tp': tp,
            'sl': sl,
            'leverage': leverage,
            'atr_value': atr_value,
            'setup_type': f'TF-ST-{"LONG" if direction == "LONG" else "SHORT"}',
            'ict_score': score,
            'strategy': 'TREND_FOLLOW',
            'strategy_label': '📈 Trend Following',
            'session': session_params.get('session', 'UNKNOWN'),
            'supertrend_dir': 'BULLISH' if current_st_dir == 1 else 'BEARISH',
            'htf_bias': 'BULLISH' if htf_bullish else 'BEARISH',
        }

    except Exception as e:
        print(f"❌ [TREND_FOLLOW] Error for {symbol}: {e}")
        return None


# ══════════════════════════════════════════════════════
# STRATEGY 4: FUNDING RATE BIAS
# ══════════════════════════════════════════════════════

# Cache funding rates (diisi dari luar via set_funding_rates)
_funding_cache: Dict[str, float] = {}

def set_funding_rates(rates: Dict[str, float]):
    """Update funding rate cache dari Bybit API"""
    global _funding_cache
    _funding_cache = rates

def get_funding_rate(symbol: str) -> Optional[float]:
    return _funding_cache.get(symbol)


def run_funding_rate(symbol: str, tf_data: Dict, session_params: Dict) -> Optional[Dict]:
    """
    Funding Rate Strategy:
    - Funding sangat positif (>0.05%) → market overleveraged LONG → bias SHORT
    - Funding sangat negatif (<-0.05%) → market overleveraged SHORT → bias LONG
    Dikombinasikan dengan mean reversion untuk entry presisi.
    """
    try:
        funding = get_funding_rate(symbol)
        if funding is None:
            return None

        THRESHOLD = 0.0005  # 0.05%

        if abs(funding) < THRESHOLD:
            return None  # Funding normal, skip

        df = tf_data['entry'].copy()
        if len(df) < 20:
            return None

        close = df['close']
        bb_mid = close.rolling(20).mean()
        bb_std_val = close.rolling(20).std()
        bb_upper = bb_mid + 1.5 * bb_std_val
        bb_lower = bb_mid - 1.5 * bb_std_val

        tr = pd.concat([
            df['high'] - df['low'],
            abs(df['high'] - df['close'].shift()),
            abs(df['low'] - df['close'].shift())
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        current_price = close.iloc[-1]
        atr_value = atr.iloc[-1]
        current_bb_mid = bb_mid.iloc[-1]

        direction = None
        score = 0

        # Funding sangat positif → SHORT (longs akan kena funding, cenderung close)
        if funding > THRESHOLD:
            if current_price >= bb_upper.iloc[-1]:  # Harga sudah di atas, bagus untuk short
                direction = 'SHORT'
                score = 4
            elif current_price > current_bb_mid:
                direction = 'SHORT'
                score = 3

        # Funding sangat negatif → LONG
        elif funding < -THRESHOLD:
            if current_price <= bb_lower.iloc[-1]:
                direction = 'LONG'
                score = 4
            elif current_price < current_bb_mid:
                direction = 'LONG'
                score = 3

        if direction is None or score < 3:
            return None

        if direction == 'LONG':
            tp = current_bb_mid + (atr_value * 0.5)
            sl = current_price - (atr_value * 1.2)
        else:
            tp = current_bb_mid - (atr_value * 0.5)
            sl = current_price + (atr_value * 1.2)

        rr = abs(tp - current_price) / abs(sl - current_price) if abs(sl - current_price) > 0 else 0
        if rr < 1.0:
            return None

        leverage = min(session_params.get('max_leverage', 10), 8)

        return {
            'symbol': symbol,
            'direction': direction,
            'close': current_price,
            'tp': tp,
            'sl': sl,
            'leverage': leverage,
            'atr_value': atr_value,
            'setup_type': f'FR-{"LONG" if direction == "LONG" else "SHORT"}',
            'ict_score': score,
            'strategy': 'FUNDING_RATE',
            'strategy_label': '💰 Funding Rate',
            'session': session_params.get('session', 'UNKNOWN'),
            'funding_rate': round(funding * 100, 4),  # dalam persen
            'funding_bias': 'OVERLEVERAGED_LONG' if funding > 0 else 'OVERLEVERAGED_SHORT',
        }

    except Exception as e:
        print(f"❌ [FUNDING_RATE] Error for {symbol}: {e}")
        return None


# ══════════════════════════════════════════════════════
# STRATEGY 5: ORDERFLOW / CVD (Cumulative Volume Delta)
# ══════════════════════════════════════════════════════

def run_orderflow(symbol: str, tf_data: Dict, session_params: Dict) -> Optional[Dict]:
    """
    Orderflow menggunakan CVD (Cumulative Volume Delta) sebagai proxy.
    CVD proxy: candle bullish = buy volume, candle bearish = sell volume.
    Divergence antara price dan CVD = sinyal reversal/continuation.
    """
    try:
        df = tf_data['entry'].copy()
        if len(df) < 30:
            return None

        close = df['close']
        open_ = df['open']
        volume = df['volume']

        # CVD proxy: volume * sign(close - open)
        candle_delta = volume * np.sign(close - open_)
        cvd = candle_delta.cumsum()

        # Normalize CVD untuk perbandingan
        cvd_norm = (cvd - cvd.rolling(20).mean()) / (cvd.rolling(20).std() + 1e-9)

        # Price momentum (ROC 5)
        price_roc = close.pct_change(5)

        # ATR
        tr = pd.concat([
            df['high'] - df['low'],
            abs(df['high'] - df['close'].shift()),
            abs(df['low'] - df['close'].shift())
        ], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()

        current_price = close.iloc[-1]
        current_cvd_norm = cvd_norm.iloc[-1]
        current_price_roc = price_roc.iloc[-1]
        atr_value = atr.iloc[-1]

        # Volume spike
        vol_avg = volume.rolling(20).mean().iloc[-1]
        vol_spike = volume.iloc[-1] > vol_avg * 1.5

        direction = None
        score = 0

        # BULLISH DIVERGENCE: harga turun tapi CVD naik (buyers absorb selling)
        price_falling = current_price_roc < -0.01  # Harga turun >1%
        cvd_rising = current_cvd_norm > 0.5         # CVD di atas rata-rata

        # BEARISH DIVERGENCE: harga naik tapi CVD turun
        price_rising = current_price_roc > 0.01
        cvd_falling = current_cvd_norm < -0.5

        if price_falling and cvd_rising:
            direction = 'LONG'
            score = 3
            if current_cvd_norm > 1.0:
                score += 1
            if vol_spike:
                score += 1

        elif price_rising and cvd_falling:
            direction = 'SHORT'
            score = 3
            if current_cvd_norm < -1.0:
                score += 1
            if vol_spike:
                score += 1

        # CONTINUATION: CVD dan price searah dengan kuat
        elif current_cvd_norm > 1.5 and current_price_roc > 0.02 and vol_spike:
            direction = 'LONG'
            score = 3

        elif current_cvd_norm < -1.5 and current_price_roc < -0.02 and vol_spike:
            direction = 'SHORT'
            score = 3

        if direction is None or score < 3:
            return None

        if direction == 'LONG':
            tp = current_price + (atr_value * 2.0)
            sl = current_price - (atr_value * 1.0)
        else:
            tp = current_price - (atr_value * 2.0)
            sl = current_price + (atr_value * 1.0)

        rr = abs(tp - current_price) / abs(sl - current_price) if abs(sl - current_price) > 0 else 0
        if rr < 1.5:
            return None

        leverage = min(session_params.get('max_leverage', 10), 12)

        return {
            'symbol': symbol,
            'direction': direction,
            'close': current_price,
            'tp': tp,
            'sl': sl,
            'leverage': leverage,
            'atr_value': atr_value,
            'setup_type': f'OF-CVD-{"LONG" if direction == "LONG" else "SHORT"}',
            'ict_score': score,
            'strategy': 'ORDERFLOW',
            'strategy_label': '🌊 Orderflow/CVD',
            'session': session_params.get('session', 'UNKNOWN'),
            'cvd_normalized': round(current_cvd_norm, 2),
            'price_roc': round(current_price_roc * 100, 2),
        }

    except Exception as e:
        print(f"❌ [ORDERFLOW] Error for {symbol}: {e}")
        return None


# ══════════════════════════════════════════════════════
# MULTI-STRATEGY RUNNER
# ══════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════
# MULTI-STRATEGY RUNNER — SMC sebagai filter utama
# ══════════════════════════════════════════════════════

CONFIRMATOR_STRATEGIES = ['MEAN_REVERSION', 'TREND_FOLLOW', 'FUNDING_RATE', 'ORDERFLOW']

def run_all_strategies(
    symbol: str,
    tf_data: Dict,
    session_params: Dict,
    tf_config: Dict,
    enabled_strategies: List[str] = None
) -> Optional[Dict]:
    """
    SMC adalah filter utama. Sinyal SMC hanya dieksekusi jika minimal
    1 strategy konfirmator setuju dengan arah yang sama.

    Flow:
    1. Jalankan ICT_SMC → jika tidak ada sinyal, stop.
    2. Jalankan 4 konfirmator (MR, TF, FR, OF).
    3. Cek apakah ada konfirmator yang searah dengan SMC.
    4. Jika ada → eksekusi sinyal SMC + catat konfirmator yang setuju.
    5. Jika tidak ada → reject, tidak ada trade.
    """
    # Step 1: SMC harus ada dulu
    smc_signal = run_ict_smc(symbol, tf_data, session_params, tf_config)
    if smc_signal is None:
        return None

    smc_direction = smc_signal['direction']

    # Step 2: Jalankan semua konfirmator
    confirmators = []

    mr_sig = run_mean_reversion(symbol, tf_data, session_params)
    if mr_sig and mr_sig['direction'] == smc_direction:
        confirmators.append(mr_sig['strategy_label'])
    elif mr_sig:
        print(f"  ⚠️  [{symbol}] MR arah berlawanan: {mr_sig['direction']} vs SMC {smc_direction}")
    else:
        print(f"  ⚠️  [{symbol}] MR: no signal")

    tf_sig = run_trend_following(symbol, tf_data, session_params)
    if tf_sig and tf_sig['direction'] == smc_direction:
        confirmators.append(tf_sig['strategy_label'])
    elif tf_sig:
        print(f"  ⚠️  [{symbol}] TF arah berlawanan: {tf_sig['direction']} vs SMC {smc_direction}")
    else:
        print(f"  ⚠️  [{symbol}] TF: no signal")

    fr_sig = run_funding_rate(symbol, tf_data, session_params)
    if fr_sig and fr_sig['direction'] == smc_direction:
        confirmators.append(fr_sig['strategy_label'])
    elif fr_sig:
        print(f"  ⚠️  [{symbol}] FR arah berlawanan: {fr_sig['direction']} vs SMC {smc_direction}")
    else:
        print(f"  ⚠️  [{symbol}] FR: no signal (funding normal atau tidak tersedia)")

    of_sig = run_orderflow(symbol, tf_data, session_params)
    if of_sig and of_sig['direction'] == smc_direction:
        confirmators.append(of_sig['strategy_label'])
    elif of_sig:
        print(f"  ⚠️  [{symbol}] OF arah berlawanan: {of_sig['direction']} vs SMC {smc_direction}")
    else:
        print(f"  ⚠️  [{symbol}] OF: no signal (tidak ada CVD divergence)")

    # Step 3: Minimal 1 konfirmator harus setuju
    if not confirmators:
        print(f"  ❌ [{symbol}] SMC {smc_direction} REJECTED — no confirmator agrees")
        return None

    # Step 4: Eksekusi sinyal SMC, tambahkan info konfirmator
    smc_signal['confirmators'] = confirmators
    smc_signal['confirmator_count'] = len(confirmators)
    # Tambah bonus score per konfirmator
    smc_signal['ict_score'] = smc_signal.get('ict_score', 0) + len(confirmators)

    conf_str = ' + '.join(confirmators)
    print(f"  ✅ [{symbol}] SMC {smc_direction} CONFIRMED by {len(confirmators)} strategy: {conf_str} | score={smc_signal['ict_score']}")

    return smc_signal
