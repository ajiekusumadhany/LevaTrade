#!/usr/bin/env python3
"""
OpenClaw Bridge — HTTP API antara trading bot dan OpenClaw agent.

Endpoint:
  POST /gate/signal       — pre-trade gate: approve/reject sinyal
  GET  /analysis/history  — ringkasan history untuk OpenClaw
  GET  /analysis/performance — performa per symbol/session
  POST /control/trading   — OpenClaw bisa enable/disable trading
  GET  /status            — health check

OpenClaw memanggil endpoint ini via skill HTTP tool.
Trading bot memanggil /gate/signal sebelum buka posisi.
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

BRIDGE_PORT    = int(os.getenv('OPENCLAW_BRIDGE_PORT', '18790'))
BRIDGE_SECRET  = os.getenv('OPENCLAW_BRIDGE_SECRET', 'changeme')
DRY_RUN_DB     = os.getenv('DRY_RUN_DB', 'dry_run_trades.db')
REAL_DB        = os.getenv('REAL_DB', 'real_trades.db')

# Thresholds untuk pre-trade gate
MIN_WIN_RATE   = float(os.getenv('GATE_MIN_WIN_RATE', '35.0'))   # % minimum
MIN_TRADES     = int(os.getenv('GATE_MIN_TRADES', '5'))           # min trades sebelum gate aktif
MAX_CONSEC_LOSS = int(os.getenv('GATE_MAX_CONSEC_LOSS', '3'))     # max loss beruntun per symbol


def _auth(req) -> bool:
    return req.headers.get('X-Bridge-Secret') == BRIDGE_SECRET


def _db(mode: str = 'dry_run') -> str:
    return DRY_RUN_DB if mode == 'dry_run' else REAL_DB


def _query(db_path: str, sql: str, params: tuple = ()) -> list:
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        return []


def _get_symbol_stats(symbol: str, direction: str, session: str, mode: str = 'dry_run') -> Dict:
    """Ambil statistik historis untuk symbol+direction+session dari DB."""
    db = _db(mode)

    # Win rate per symbol+direction+session (30 hari terakhir)
    rows = _query(db, '''
        SELECT pnl_percentage, exit_reason, entry_time
        FROM trade_history
        WHERE symbol = ? AND direction = ? AND trading_session = ?
          AND entry_time >= datetime('now', '-30 days')
        ORDER BY entry_time DESC
    ''', (symbol, direction, session))

    if not rows:
        # Coba tanpa filter session
        rows = _query(db, '''
            SELECT pnl_percentage, exit_reason, entry_time
            FROM trade_history
            WHERE symbol = ? AND direction = ?
              AND entry_time >= datetime('now', '-30 days')
            ORDER BY entry_time DESC
        ''', (symbol, direction))

    total = len(rows)
    if total == 0:
        return {'total': 0, 'win_rate': None, 'consec_loss': 0, 'avg_pnl': 0}

    wins = sum(1 for r in rows if r['pnl_percentage'] > 0)
    win_rate = (wins / total) * 100
    avg_pnl = sum(r['pnl_percentage'] for r in rows) / total

    # Hitung consecutive loss terbaru
    consec_loss = 0
    for r in rows:
        if r['pnl_percentage'] < 0:
            consec_loss += 1
        else:
            break

    return {
        'total': total,
        'win_rate': round(win_rate, 1),
        'consec_loss': consec_loss,
        'avg_pnl': round(avg_pnl, 2),
    }


def _get_session_stats(session: str, mode: str = 'dry_run') -> Dict:
    """Win rate keseluruhan untuk session tertentu."""
    db = _db(mode)
    rows = _query(db, '''
        SELECT pnl_percentage FROM trade_history
        WHERE trading_session = ?
          AND entry_time >= datetime('now', '-30 days')
    ''', (session,))
    if not rows:
        return {'total': 0, 'win_rate': None}
    total = len(rows)
    wins = sum(1 for r in rows if r['pnl_percentage'] > 0)
    return {'total': total, 'win_rate': round((wins / total) * 100, 1)}


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT: Pre-trade gate
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/gate/signal', methods=['POST'])
def gate_signal():
    """
    Trading bot panggil ini sebelum buka posisi.
    Body JSON: { symbol, direction, session, ict_score, rr_ratio, mode }
    Response:  { approved: bool, reason: str, stats: {...} }
    """
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    symbol    = data.get('symbol', '')
    direction = data.get('direction', '')
    session   = data.get('session', 'UNKNOWN')
    ict_score = float(data.get('ict_score', 0))
    rr_ratio  = float(data.get('rr_ratio', 0))
    mode      = data.get('mode', 'dry_run')

    stats = _get_symbol_stats(symbol, direction, session, mode)
    session_stats = _get_session_stats(session, mode)

    reasons_reject = []

    # Gate 1: win rate terlalu rendah (hanya aktif jika sudah ada cukup data)
    if stats['total'] >= MIN_TRADES and stats['win_rate'] is not None:
        if stats['win_rate'] < MIN_WIN_RATE:
            reasons_reject.append(
                f"Win rate {symbol} {direction} di {session} hanya {stats['win_rate']}% "
                f"({stats['total']} trades) — di bawah threshold {MIN_WIN_RATE}%"
            )

    # Gate 2: consecutive loss beruntun
    if stats['consec_loss'] >= MAX_CONSEC_LOSS:
        reasons_reject.append(
            f"{symbol} {direction} loss {stats['consec_loss']}x beruntun — skip dulu"
        )

    # Gate 3: session win rate buruk
    if session_stats['total'] >= MIN_TRADES and session_stats['win_rate'] is not None:
        if session_stats['win_rate'] < 30.0:
            reasons_reject.append(
                f"Session {session} win rate keseluruhan {session_stats['win_rate']}% — kondisi buruk"
            )

    approved = len(reasons_reject) == 0
    reason   = ' | '.join(reasons_reject) if reasons_reject else 'OK — semua gate passed'

    return jsonify({
        'approved': approved,
        'reason': reason,
        'stats': {
            'symbol_stats': stats,
            'session_stats': session_stats,
            'ict_score': ict_score,
            'rr_ratio': rr_ratio,
        }
    })


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT: History analysis (untuk OpenClaw baca dan analisis)
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/analysis/history', methods=['GET'])
def analysis_history():
    """Ringkasan trade history — OpenClaw pakai ini untuk analisis."""
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    mode  = request.args.get('mode', 'dry_run')
    days  = int(request.args.get('days', 30))
    limit = int(request.args.get('limit', 50))
    db    = _db(mode)

    trades = _query(db, '''
        SELECT symbol, direction, pnl_percentage, exit_reason,
               trading_session, market_cap_category, volume_category,
               liquidity_score, volatility_score, duration_minutes,
               entry_time, exit_time, indicators
        FROM trade_history
        WHERE entry_time >= datetime('now', ? || ' days')
        ORDER BY entry_time DESC
        LIMIT ?
    ''', (f'-{days}', limit))

    # Aggregate stats
    total = len(trades)
    wins  = sum(1 for t in trades if t['pnl_percentage'] > 0)
    total_pnl = sum(t['pnl_percentage'] for t in trades)

    # Per-symbol breakdown
    by_symbol: Dict = {}
    for t in trades:
        s = t['symbol']
        if s not in by_symbol:
            by_symbol[s] = {'total': 0, 'wins': 0, 'pnl': 0.0}
        by_symbol[s]['total'] += 1
        by_symbol[s]['wins']  += 1 if t['pnl_percentage'] > 0 else 0
        by_symbol[s]['pnl']   += t['pnl_percentage']

    for s in by_symbol:
        d = by_symbol[s]
        d['win_rate'] = round((d['wins'] / d['total']) * 100, 1) if d['total'] else 0
        d['avg_pnl']  = round(d['pnl'] / d['total'], 2) if d['total'] else 0

    # Per-session breakdown
    by_session: Dict = {}
    for t in trades:
        sess = t['trading_session'] or 'UNKNOWN'
        if sess not in by_session:
            by_session[sess] = {'total': 0, 'wins': 0, 'pnl': 0.0}
        by_session[sess]['total'] += 1
        by_session[sess]['wins']  += 1 if t['pnl_percentage'] > 0 else 0
        by_session[sess]['pnl']   += t['pnl_percentage']

    for sess in by_session:
        d = by_session[sess]
        d['win_rate'] = round((d['wins'] / d['total']) * 100, 1) if d['total'] else 0

    return jsonify({
        'mode': mode,
        'period_days': days,
        'summary': {
            'total_trades': total,
            'win_rate': round((wins / total) * 100, 1) if total else 0,
            'total_pnl_pct': round(total_pnl, 2),
        },
        'by_symbol': by_symbol,
        'by_session': by_session,
        'recent_trades': trades[:20],
    })


@app.route('/analysis/performance', methods=['GET'])
def analysis_performance():
    """Detail performa untuk OpenClaw — dipakai saat kamu tanya via Telegram."""
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    mode   = request.args.get('mode', 'dry_run')
    symbol = request.args.get('symbol', None)
    days   = int(request.args.get('days', 7))
    db     = _db(mode)

    where = "WHERE entry_time >= datetime('now', ? || ' days')"
    params: list = [f'-{days}']

    if symbol:
        where += ' AND symbol = ?'
        params.append(symbol)

    trades = _query(db, f'''
        SELECT symbol, direction, pnl_percentage, exit_reason,
               trading_session, market_cap_category, volume_category,
               ict_score, rr_ratio, duration_minutes, indicators
        FROM trade_history {where}
        ORDER BY entry_time DESC
    ''', tuple(params))

    # Pattern analysis: kondisi apa yang sering loss
    loss_patterns = []
    for t in trades:
        if t['pnl_percentage'] < 0:
            loss_patterns.append({
                'symbol': t['symbol'],
                'direction': t['direction'],
                'session': t['trading_session'],
                'exit_reason': t['exit_reason'],
                'market_cap': t['market_cap_category'],
                'volume': t['volume_category'],
                'pnl': t['pnl_percentage'],
            })

    return jsonify({
        'mode': mode,
        'symbol_filter': symbol,
        'period_days': days,
        'total_trades': len(trades),
        'loss_patterns': loss_patterns[:20],
        'all_trades': trades,
    })


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT: Control (OpenClaw bisa pause/resume trading)
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/control/trading', methods=['POST'])
def control_trading():
    """
    OpenClaw bisa pause/resume trading via Telegram command.
    Body: { action: 'enable'|'disable', reason: str }
    """
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    data   = request.get_json() or {}
    action = data.get('action', '')
    reason = data.get('reason', 'OpenClaw control')

    if action not in ('enable', 'disable'):
        return jsonify({'error': 'action harus enable atau disable'}), 400

    control = {
        'enabled': action == 'enable',
        'status_text': f'Trading {"Enabled" if action == "enable" else "Disabled"} by OpenClaw',
        'last_updated': datetime.now().isoformat(),
        'updated_by': f'openclaw: {reason}',
    }

    with open('trading_control.json', 'w') as f:
        json.dump(control, f, indent=2)

    return jsonify({'success': True, 'status': control})


@app.route('/control/gate_config', methods=['POST'])
def control_gate_config():
    """Update threshold gate secara dinamis dari OpenClaw."""
    if not _auth(request):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    global MIN_WIN_RATE, MAX_CONSEC_LOSS, MIN_TRADES

    if 'min_win_rate' in data:
        MIN_WIN_RATE = float(data['min_win_rate'])
    if 'max_consec_loss' in data:
        MAX_CONSEC_LOSS = int(data['max_consec_loss'])
    if 'min_trades' in data:
        MIN_TRADES = int(data['min_trades'])

    return jsonify({
        'success': True,
        'current_config': {
            'min_win_rate': MIN_WIN_RATE,
            'max_consec_loss': MAX_CONSEC_LOSS,
            'min_trades': MIN_TRADES,
        }
    })


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT: Status
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/status', methods=['GET'])
def status():
    try:
        with open('trading_control.json') as f:
            ctrl = json.load(f)
    except Exception:
        ctrl = {'enabled': True}

    # Count open positions
    open_pos = 0
    try:
        rows = _query(DRY_RUN_DB, 'SELECT COUNT(*) as c FROM open_positions')
        open_pos = rows[0]['c'] if rows else 0
    except Exception:
        pass

    return jsonify({
        'bridge': 'running',
        'trading_enabled': ctrl.get('enabled', True),
        'open_positions': open_pos,
        'gate_config': {
            'min_win_rate': MIN_WIN_RATE,
            'max_consec_loss': MAX_CONSEC_LOSS,
            'min_trades': MIN_TRADES,
        },
        'timestamp': datetime.now().isoformat(),
    })


if __name__ == '__main__':
    print(f"🦞 OpenClaw Bridge running on port {BRIDGE_PORT}")
    app.run(host='127.0.0.1', port=BRIDGE_PORT, debug=False)
