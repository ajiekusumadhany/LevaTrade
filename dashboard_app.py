"""
Flask Dashboard untuk Dry Run Trading System
"""
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import sqlite3
import os
from datetime import datetime, timedelta
from dry_run_system import dry_run_system
from real_trade_system import real_trade_system
from dashboard_ai_chat import setup_ai_chat_routes
from trading_session_system import get_session_analyzer
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get balance from environment
BALANCE_USD = float(os.getenv('BALANCE_USD', '1000'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'trading_dashboard_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Setup AI chat routes
ai_chat = setup_ai_chat_routes(app, socketio)

# Set socketio instance in trading systems for notifications
from dry_run_system import set_socketio_instance as set_dry_run_socketio
from real_trade_system import set_socketio_instance as set_real_trade_socketio
set_dry_run_socketio(socketio)
set_real_trade_socketio(socketio)

# Global variables untuk real-time updates
latest_signals = []
latest_prices = {}

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/notifications')
def get_notifications():
    """API endpoint untuk mendapatkan notifikasi baru"""
    last_id = int(request.args.get('last_id', 0))
    
    try:
        from notification_system import get_new_notifications
        notifications = get_new_notifications(last_id)
        return jsonify({'success': True, 'notifications': notifications})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/notifications/clear', methods=['POST'])
def clear_notifications():
    """API endpoint untuk membersihkan semua notifikasi"""
    try:
        from notification_system import mark_notifications_as_read
        mark_notifications_as_read()
        return jsonify({'success': True, 'message': 'Notifications cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/trading/status')
def get_trading_status():
    """API endpoint untuk mendapatkan status trading"""
    try:
        from trading_control_system import get_trading_status
        status = get_trading_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/trading/start', methods=['POST'])
def start_trading_api():
    """API endpoint untuk start trading"""
    try:
        from trading_control_system import start_trading
        result = start_trading('dashboard')
        
        # Send notification via Telegram
        try:
            from telegram import Bot
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            if bot_token and chat_id:
                bot = Bot(token=bot_token)
                bot.send_message(
                    chat_id=chat_id,
                    text="✅ <b>Trading STARTED</b>\n📱 Controlled from Dashboard\n🤖 Bot will resume taking new positions",
                    parse_mode='HTML'
                )
        except Exception as telegram_error:
            print(f"⚠️ Telegram notification failed: {telegram_error}")
        
        return jsonify({'success': True, 'message': 'Trading started'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/trading/stop', methods=['POST'])
def stop_trading_api():
    """API endpoint untuk stop trading"""
    try:
        from trading_control_system import stop_trading
        result = stop_trading('dashboard')
        
        # Send notification via Telegram
        try:
            from telegram import Bot
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            if bot_token and chat_id:
                bot = Bot(token=bot_token)
                bot.send_message(
                    chat_id=chat_id,
                    text="🛑 <b>Trading STOPPED</b>\n📱 Controlled from Dashboard\n⏸️ Bot will not take new positions\n📊 Existing positions will continue to be monitored",
                    parse_mode='HTML'
                )
        except Exception as telegram_error:
            print(f"⚠️ Telegram notification failed: {telegram_error}")
        
        return jsonify({'success': True, 'message': 'Trading stopped'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/positions')
def get_positions():
    """API endpoint untuk open positions dengan percentage PnL"""
    mode = request.args.get('mode', 'dry-run')
    
    if mode == 'dry-run':
        positions = dry_run_system.get_open_positions()
    else:
        positions = real_trade_system.get_open_positions()
    
    # Tambahkan persentase PnL untuk setiap posisi berdasarkan margin yang digunakan
    for pos in positions:
        if pos.get('unrealized_pnl') is not None and pos.get('position_value_usd') and pos.get('leverage'):
            # Calculate PnL percentage from MARGIN USED (bukan risk amount)
            # Margin = Position Value / Leverage
            margin_used = pos['position_value_usd'] / pos['leverage'] if pos.get('leverage', 1) > 0 else pos['position_value_usd']
            
            # PnL percentage dari margin yang benar-benar digunakan
            pos['pnl_percentage'] = (pos['unrealized_pnl'] / margin_used) * 100 if margin_used > 0 else 0
        else:
            pos['pnl_percentage'] = 0.0
    
    return jsonify(positions)

@app.route('/api/trade-details/<trade_id>')
def get_trade_details(trade_id):
    """API endpoint untuk mendapatkan detail trade berdasarkan ID"""
    mode = request.args.get('mode', 'dry_run')
    
    try:
        if mode == 'dry_run':
            # Get specific trade from dry run system
            conn = sqlite3.connect('dry_run_trades.db')
        else:
            # Get specific trade from real trade system
            conn = sqlite3.connect('real_trades.db')
        
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trade_history WHERE id = ?', (trade_id,))
        trade_data = cursor.fetchone()
        
        if not trade_data:
            return jsonify({'success': False, 'error': 'Trade not found'})
        
        # Handle different schema versions - extract only the first columns we need
        if mode == 'dry_run':
            # Dry run schema: 40 columns total, we need first 17
            if len(trade_data) >= 40:  # New schema with market data (40 columns)
                (trade_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes, ai_entry_reasoning, ai_exit_reasoning) = trade_data[:17]
            elif len(trade_data) >= 17:  # Schema with AI reasoning but no market data
                (trade_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes, ai_entry_reasoning, ai_exit_reasoning) = trade_data[:17]
            else:  # Old schema without AI reasoning (15 columns)
                (trade_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes) = trade_data[:15]
                ai_entry_reasoning = ""
                ai_exit_reasoning = ""
        else:  # real trade
            # Real trade schema: 43 columns total, we need first 20
            if len(trade_data) >= 43:  # New schema with market data (43 columns)
                (trade_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes, bybit_entry_order_id, 
                 bybit_exit_order_id, fees_paid, ai_entry_reasoning, ai_exit_reasoning) = trade_data[:20]
            elif len(trade_data) >= 20:  # Schema with AI reasoning but no market data
                (trade_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes, bybit_entry_order_id, 
                 bybit_exit_order_id, fees_paid, ai_entry_reasoning, ai_exit_reasoning) = trade_data[:20]
            else:  # Old schema without AI reasoning (18 columns)
                (trade_id, symbol, direction, entry_price, exit_price, quantity, leverage,
                 entry_time, exit_time, exit_reason, pnl, pnl_percentage, indicators,
                 position_value_usd, duration_minutes, bybit_entry_order_id, 
                 bybit_exit_order_id, fees_paid) = trade_data[:18]
                ai_entry_reasoning = ""
                ai_exit_reasoning = ""
        
        trade_details = {
            'id': trade_id,
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'leverage': leverage,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'exit_reason': exit_reason,
            'pnl': pnl,
            'pnl_percentage': pnl_percentage,
            'indicators': json.loads(indicators) if indicators else {},
            'position_value_usd': position_value_usd,
            'duration_minutes': duration_minutes,
            'ai_entry_reasoning': ai_entry_reasoning or '',
            'ai_exit_reasoning': ai_exit_reasoning or ''
        }
        
        conn.close()
        return jsonify({'success': True, 'trade': trade_details})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/history')
def get_history():
    """API endpoint untuk trade history dengan pagination"""
    limit = int(request.args.get('limit', 10))  # Default 10 per page
    offset = int(request.args.get('offset', 0))  # Starting position
    mode = request.args.get('mode', 'dry-run')
    
    if mode == 'dry-run':
        # Get total count first
        all_history = dry_run_system.get_trade_history(1000)  # Get large number to count
        total_count = len(all_history)
        
        # Get paginated data
        history = all_history[offset:offset + limit] if offset < len(all_history) else []
    else:
        # Get total count first
        all_history = real_trade_system.get_trade_history(1000)  # Get large number to count
        total_count = len(all_history)
        
        # Get paginated data
        history = all_history[offset:offset + limit] if offset < len(all_history) else []
    
    # Recalculate PnL percentage berdasarkan margin (bukan dari database)
    for trade in history:
        if trade.get('position_value_usd') and trade.get('leverage'):
            # Calculate margin used
            margin_used = trade['position_value_usd'] / trade['leverage'] if trade['leverage'] > 0 else trade['position_value_usd']
            # Recalculate PnL percentage
            trade['pnl_percentage'] = (trade['pnl'] / margin_used) * 100 if margin_used > 0 else 0
    
    # Calculate pagination info
    has_more = (offset + limit) < total_count
    current_page = (offset // limit) + 1
    total_pages = (total_count + limit - 1) // limit  # Ceiling division
    
    return jsonify({
        'trades': history,
        'pagination': {
            'total_count': total_count,
            'current_page': current_page,
            'total_pages': total_pages,
            'has_more': has_more,
            'limit': limit,
            'offset': offset
        }
    })

@app.route('/api/performance')
def get_performance():
    """API endpoint untuk performance metrics"""
    mode = request.args.get('mode', 'dry-run')
    
    if mode == 'dry-run':
        metrics = dry_run_system.get_performance_metrics()
        # Tambahkan unrealized PnL dari posisi terbuka
        open_positions = dry_run_system.get_open_positions()
    else:
        metrics = real_trade_system.get_performance_metrics()
        # Tambahkan unrealized PnL dari posisi terbuka
        open_positions = real_trade_system.get_open_positions()
    
    # Hitung total unrealized PnL
    total_unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in open_positions)
    
    # Hitung margin yang digunakan dan tersedia
    total_margin_used = 0
    for pos in open_positions:
        if pos.get('position_value_usd') and pos.get('leverage'):
            margin_used = pos['position_value_usd'] / pos['leverage']
            total_margin_used += margin_used
    
    # Balance saat ini
    if mode == 'dry-run':
        current_balance = dry_run_system.get_current_balance()
    else:
        current_balance = real_trade_system.get_real_balance()
    
    # Margin tersedia
    available_margin = current_balance - total_margin_used
    margin_usage_percent = (total_margin_used / current_balance) * 100 if current_balance > 0 else 0
    
    # Tambahkan ke metrics
    metrics['unrealized_pnl'] = total_unrealized_pnl
    metrics['open_positions_count'] = len(open_positions)
    metrics['total_margin_used'] = total_margin_used
    metrics['available_margin'] = available_margin
    metrics['margin_usage_percent'] = margin_usage_percent
    
    # Balance sudah dinamis dari get_performance_metrics() untuk kedua mode
    
    return jsonify(metrics)

@app.route('/api/session-status')
def get_session_status_api():
    """API endpoint untuk session status dan conditional risk info"""
    try:
        from session_management_system import get_session_status
        from conditional_risk_system import get_risk_status
        
        session_status = get_session_status()
        risk_status = get_risk_status()
        
        return jsonify({
            'success': True,
            'session_status': session_status,
            'risk_status': risk_status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/conditional-risk')
def get_conditional_risk_api():
    """API endpoint untuk conditional risk details"""
    try:
        from conditional_risk_system import get_risk_status
        
        risk_status = get_risk_status()
        
        return jsonify({
            'success': True,
            'risk_status': risk_status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/session-performance')
def get_session_performance():
    """API endpoint untuk session performance analysis"""
    mode = request.args.get('mode', 'dry-run').replace('-', '_')
    days = int(request.args.get('days', 30))
    
    try:
        from trading_session_system import get_session_analyzer
        session_analyzer = get_session_analyzer()
        performance = session_analyzer.get_session_performance(mode, days)
        
        return jsonify(performance)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/session-comparison')
def get_session_comparison():
    """API endpoint untuk session comparison"""
    mode = request.args.get('mode', 'dry-run').replace('-', '_')
    days = int(request.args.get('days', 30))
    
    try:
        from trading_session_system import get_session_analyzer
        session_analyzer = get_session_analyzer()
        comparison = session_analyzer.get_session_comparison(mode, days)
        
        return jsonify(comparison)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/best-worst-sessions')
def get_best_worst_sessions():
    """API endpoint untuk best/worst sessions"""
    mode = request.args.get('mode', 'dry-run').replace('-', '_')
    days = int(request.args.get('days', 30))
    
    try:
        from trading_session_system import get_session_analyzer
        session_analyzer = get_session_analyzer()
        best_worst = session_analyzer.get_best_worst_sessions(mode, days)
        
        return jsonify(best_worst)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/indicator-performance')
def get_indicator_performance():
    """API endpoint untuk overall indicator performance analysis"""
    mode = request.args.get('mode', 'dry-run').replace('-', '_')
    days = int(request.args.get('days', 30))
    
    from overall_indicator_performance_system import get_overall_indicator_analyzer
    
    analyzer = get_overall_indicator_analyzer()
    performance = analyzer.get_overall_indicator_performance(mode, days)
    
    if performance.get('success'):
        # Add category summary
        categories = analyzer.get_indicator_categories_summary(performance)
        performance['categories'] = categories
        
        # Add recommendations
        recommendations = analyzer.get_indicator_recommendations(performance)
        performance['recommendations'] = recommendations
    
    return jsonify(performance)

@app.route('/api/pair-performance')
def get_pair_performance():
    """API endpoint untuk pair performance analysis"""
    mode = request.args.get('mode', 'dry-run').replace('-', '_')
    days = int(request.args.get('days', 30))
    
    from pair_performance_system import get_pair_analyzer
    import asyncio
    
    analyzer = get_pair_analyzer()
    
    # Run async function in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    performance = loop.run_until_complete(analyzer.get_pair_performance(mode, days))
    loop.close()
    
    if performance.get('success'):
        # Add category summary
        categories = analyzer.get_pair_categories_summary(performance)
        performance['categories'] = categories
        
        # Add recommendations
        recommendations = analyzer.get_trading_recommendations(performance)
        performance['recommendations'] = recommendations
    
    return jsonify(performance)
@app.route('/api/chart-data')
def get_chart_data():
    """API endpoint untuk chart data dengan dynamic balance"""
    mode = request.args.get('mode', 'dry-run')
    
    # Get starting balance from environment
    import os
    from dotenv import load_dotenv
    load_dotenv()
    starting_balance = float(os.getenv('BALANCE_USD', '1167'))
    
    if mode == 'dry-run':
        # Get daily PnL for chart
        history = dry_run_system.get_trade_history(1000)  # Get more data for chart
    else:
        history = real_trade_system.get_trade_history(1000)
        # For real trading, get actual starting balance from API if needed
        try:
            actual_balance = real_trade_system.get_real_balance()
            if actual_balance > 0:
                starting_balance = actual_balance
        except:
            pass  # Use environment balance as fallback
    
    # Group by date
    daily_pnl = {}
    cumulative_pnl = 0
    
    for trade in reversed(history):  # Reverse to get chronological order
        date = trade['exit_time'][:10]  # Get date part
        if date not in daily_pnl:
            daily_pnl[date] = 0
        daily_pnl[date] += trade['pnl']
    
    # Create chart data
    chart_data = []
    
    # TAMBAH STARTING POINT - Balance awal sebelum ada trade
    if daily_pnl:  # Jika ada trade history
        first_date = min(daily_pnl.keys())
        # Tambah hari sebelum trade pertama sebagai starting point
        from datetime import datetime, timedelta
        start_date = (datetime.strptime(first_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        
        chart_data.append({
            'date': start_date,
            'daily_pnl': 0,
            'cumulative_pnl': 0,
            'balance': starting_balance  # Dynamic starting balance
        })
    else:
        # Jika belum ada trade, tampilkan hari ini dengan balance awal
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        chart_data.append({
            'date': today,
            'daily_pnl': 0,
            'cumulative_pnl': 0,
            'balance': starting_balance  # Dynamic starting balance
        })
    
    # Tambah data trade harian
    for date in sorted(daily_pnl.keys()):
        cumulative_pnl += daily_pnl[date]
        current_balance = starting_balance + cumulative_pnl
        
        chart_data.append({
            'date': date,
            'daily_pnl': daily_pnl[date],
            'cumulative_pnl': cumulative_pnl,
            'balance': current_balance,
            'roi_percent': ((cumulative_pnl / starting_balance) * 100) if starting_balance > 0 else 0
        })
    
    # Add current day if not already included
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    if not daily_pnl or today not in daily_pnl:
        # Get current dynamic balance for today
        if mode == 'dry-run':
            current_dynamic_balance = dry_run_system.get_current_balance()
            current_cumulative_pnl = current_dynamic_balance - starting_balance
        else:
            current_cumulative_pnl = cumulative_pnl  # Use last known PnL
            current_dynamic_balance = starting_balance + current_cumulative_pnl
        
        chart_data.append({
            'date': today,
            'daily_pnl': 0,  # No trades today yet
            'cumulative_pnl': current_cumulative_pnl,
            'balance': current_dynamic_balance,
            'roi_percent': ((current_cumulative_pnl / starting_balance) * 100) if starting_balance > 0 else 0
        })
    
    return jsonify(chart_data)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    # Send initial data
    emit('positions_update', dry_run_system.get_open_positions())
    emit('performance_update', dry_run_system.get_performance_metrics())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

def broadcast_updates():
    """Broadcast real-time updates to all clients"""
    while True:
        try:
            # Emit updates every 30 seconds untuk sinkron dengan position updates
            
            # Dry Run updates
            dry_positions = dry_run_system.get_open_positions()
            # Tambahkan persentase PnL untuk dry run positions berdasarkan margin
            for pos in dry_positions:
                if pos.get('unrealized_pnl') is not None and pos.get('position_value_usd') and pos.get('leverage'):
                    # Calculate PnL percentage from MARGIN USED
                    margin_used = pos['position_value_usd'] / pos['leverage'] if pos.get('leverage', 1) > 0 else pos['position_value_usd']
                    pos['pnl_percentage'] = (pos['unrealized_pnl'] / margin_used) * 100 if margin_used > 0 else 0
                else:
                    pos['pnl_percentage'] = 0.0
            
            dry_metrics = dry_run_system.get_performance_metrics()
            # Tambahkan unrealized PnL dan margin info untuk dry run
            dry_unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in dry_positions)
            
            # Hitung margin yang digunakan untuk dry run
            dry_total_margin_used = 0
            for pos in dry_positions:
                if pos.get('position_value_usd') and pos.get('leverage'):
                    margin_used = pos['position_value_usd'] / pos['leverage']
                    dry_total_margin_used += margin_used
            
            dry_current_balance = dry_run_system.get_current_balance()
            dry_available_margin = dry_current_balance - dry_total_margin_used
            dry_margin_usage_percent = (dry_total_margin_used / dry_current_balance) * 100 if dry_current_balance > 0 else 0
            
            dry_metrics['unrealized_pnl'] = dry_unrealized_pnl
            dry_metrics['open_positions_count'] = len(dry_positions)
            dry_metrics['total_margin_used'] = dry_total_margin_used
            dry_metrics['available_margin'] = dry_available_margin
            dry_metrics['margin_usage_percent'] = dry_margin_usage_percent
            
            socketio.emit('positions_update', {'mode': 'dry-run', 'data': dry_positions})
            socketio.emit('performance_update', {'mode': 'dry-run', 'data': dry_metrics})
            
            # Real Trade updates
            real_positions = real_trade_system.get_open_positions()
            # Tambahkan persentase PnL untuk real trade positions berdasarkan margin
            for pos in real_positions:
                if pos.get('unrealized_pnl') is not None and pos.get('position_value_usd') and pos.get('leverage'):
                    # Calculate PnL percentage from MARGIN USED
                    margin_used = pos['position_value_usd'] / pos['leverage'] if pos.get('leverage', 1) > 0 else pos['position_value_usd']
                    pos['pnl_percentage'] = (pos['unrealized_pnl'] / margin_used) * 100 if margin_used > 0 else 0
                else:
                    pos['pnl_percentage'] = 0.0
            
            real_metrics = real_trade_system.get_performance_metrics()
            # Update dengan real balance dari Bybit
            current_real_balance = real_trade_system.get_real_balance()
            real_metrics['balance'] = current_real_balance
            
            # Tambahkan unrealized PnL dan margin info untuk real trade
            real_unrealized_pnl = sum(pos.get('unrealized_pnl', 0) for pos in real_positions)
            
            # Hitung margin yang digunakan untuk real trade
            real_total_margin_used = 0
            for pos in real_positions:
                if pos.get('position_value_usd') and pos.get('leverage'):
                    margin_used = pos['position_value_usd'] / pos['leverage']
                    real_total_margin_used += margin_used
            
            real_available_margin = current_real_balance - real_total_margin_used
            real_margin_usage_percent = (real_total_margin_used / current_real_balance) * 100 if current_real_balance > 0 else 0
            
            real_metrics['unrealized_pnl'] = real_unrealized_pnl
            real_metrics['open_positions_count'] = len(real_positions)
            real_metrics['total_margin_used'] = real_total_margin_used
            real_metrics['available_margin'] = real_available_margin
            real_metrics['margin_usage_percent'] = real_margin_usage_percent
            
            socketio.emit('positions_update', {'mode': 'real-trade', 'data': real_positions})
            socketio.emit('performance_update', {'mode': 'real-trade', 'data': real_metrics})
            
            if latest_signals:
                socketio.emit('new_signal', latest_signals[-1])
            
            print(f"📊 Dashboard updated at {datetime.now().strftime('%H:%M:%S')} - Dry: {len(dry_positions)} positions, Real: {len(real_positions)} positions")
            
            time.sleep(30)  # Update setiap 30 detik untuk sinkron dengan position updates
        except Exception as e:
            print(f"Error in broadcast_updates: {e}")
            time.sleep(30)

# Start background thread for real-time updates
def start_background_thread():
    thread = threading.Thread(target=broadcast_updates)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    start_background_thread()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)