#!/usr/bin/env python3
"""
Trading Session Analysis System
Menganalisis performa trading berdasarkan sesi market (Asia, London, New York, Dead Zone)
"""
import sqlite3
import json
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import pytz

class TradingSessionAnalyzer:
    def __init__(self):
        self.dry_run_db = "dry_run_trades.db"
        self.real_db = "real_trades.db"
        
        # Define trading sessions in WIB (UTC+7)
        self.sessions = {
            'DEAD_ZONE': {
                'name': 'Dead Zone',
                'time_range': '02:00 - 07:00 WIB',
                'start_hour': 2,
                'end_hour': 7,
                'color': '🟥',
                'description': 'Low volatility period'
            },
            'ASIA': {
                'name': 'Asia Session',
                'time_range': '07:00 - 14:00 WIB',
                'start_hour': 7,
                'end_hour': 14,
                'color': '🟨',
                'description': 'Asian markets active'
            },
            'LONDON': {
                'name': 'London Session',
                'time_range': '14:00 - 20:00 WIB',
                'start_hour': 14,
                'end_hour': 20,
                'color': '🟩',
                'description': 'European markets active'
            },
            'NEWYORK': {
                'name': 'New York Session',
                'time_range': '20:00 - 02:00 WIB',
                'start_hour': 20,
                'end_hour': 2,  # Next day
                'color': '🟦',
                'description': 'American markets active'
            }
        }
    
    def get_trading_session(self, timestamp_str: str) -> str:
        """
        Determine which trading session a timestamp belongs to
        """
        try:
            # Parse timestamp
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Convert to WIB (UTC+7)
            wib_tz = pytz.timezone('Asia/Jakarta')
            
            if dt.tzinfo is None:
                # If no timezone info, assume it's already local time (WIB)
                wib_time = wib_tz.localize(dt)
            else:
                # If has timezone info, convert to WIB
                wib_time = dt.astimezone(wib_tz)
            
            hour = wib_time.hour
            
            # Determine session based on hour (WIB)
            # NEWYORK: 20:00-02:00 (spans midnight)
            # DEAD_ZONE: 02:00-07:00  
            # ASIA: 07:00-14:00
            # LONDON: 14:00-20:00
            
            if 0 <= hour < 2:  # 00:00-01:59 (NEWYORK continues from previous day)
                return 'NEWYORK'
            elif 2 <= hour < 7:  # 02:00-06:59 (DEAD_ZONE)
                return 'DEAD_ZONE'
            elif 7 <= hour < 14:  # 07:00-13:59 (ASIA)
                return 'ASIA'
            elif 14 <= hour < 20:  # 14:00-19:59 (LONDON)
                return 'LONDON'
            else:  # 20:00-23:59 (NEWYORK starts)
                return 'NEWYORK'
                
        except Exception as e:
            print(f"Error parsing timestamp {timestamp_str}: {e}")
            return 'UNKNOWN'
    
    def add_session_column_to_database(self):
        """
        Add trading_session column to existing databases
        """
        databases = [self.dry_run_db, self.real_db]
        
        for db_path in databases:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Add session column to open_positions if not exists
                try:
                    cursor.execute('ALTER TABLE open_positions ADD COLUMN trading_session TEXT DEFAULT ""')
                    print(f"✅ Added trading_session column to open_positions in {db_path}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"⚠️  Column trading_session already exists in open_positions ({db_path})")
                    else:
                        print(f"❌ Error adding column to open_positions: {e}")
                
                # Add session column to trade_history if not exists
                try:
                    cursor.execute('ALTER TABLE trade_history ADD COLUMN trading_session TEXT DEFAULT ""')
                    print(f"✅ Added trading_session column to trade_history in {db_path}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"⚠️  Column trading_session already exists in trade_history ({db_path})")
                    else:
                        print(f"❌ Error adding column to trade_history: {e}")
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                print(f"❌ Error updating database {db_path}: {e}")
    
    def update_existing_sessions(self):
        """
        Update trading_session for existing records
        """
        databases = [
            (self.dry_run_db, "Dry Run"),
            (self.real_db, "Real Trade")
        ]
        
        for db_path, db_name in databases:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                print(f"\n🔄 Updating {db_name} Database...")
                
                # Update open_positions
                cursor.execute('SELECT id, entry_time FROM open_positions WHERE trading_session = "" OR trading_session IS NULL')
                positions = cursor.fetchall()
                
                updated_positions = 0
                for pos_id, entry_time in positions:
                    session = self.get_trading_session(entry_time)
                    cursor.execute('UPDATE open_positions SET trading_session = ? WHERE id = ?', (session, pos_id))
                    updated_positions += 1
                
                print(f"   📊 Updated {updated_positions} open positions")
                
                # Update trade_history
                cursor.execute('SELECT id, entry_time FROM trade_history WHERE trading_session = "" OR trading_session IS NULL')
                trades = cursor.fetchall()
                
                updated_trades = 0
                for trade_id, entry_time in trades:
                    session = self.get_trading_session(entry_time)
                    cursor.execute('UPDATE trade_history SET trading_session = ? WHERE id = ?', (session, trade_id))
                    updated_trades += 1
                
                print(f"   📈 Updated {updated_trades} trade history records")
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                print(f"❌ Error updating {db_name}: {e}")
    
    def get_session_performance(self, mode: str = "dry_run", days: int = 30) -> Dict:
        """
        Get comprehensive performance analysis by trading session
        """
        db_path = self.dry_run_db if mode == "dry_run" else self.real_db
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Get trade history with session data
            cursor.execute('''
                SELECT trading_session, symbol, direction, pnl, pnl_percentage, 
                       exit_reason, entry_time, indicators
                FROM trade_history 
                WHERE entry_time >= ? AND trading_session != ""
                ORDER BY entry_time DESC
            ''', (cutoff_date,))
            
            trades = cursor.fetchall()
            conn.close()
            
            # Initialize session stats
            session_stats = {}
            for session_key, session_info in self.sessions.items():
                session_stats[session_key] = {
                    'name': session_info['name'],
                    'time_range': session_info['time_range'],
                    'color': session_info['color'],
                    'description': session_info['description'],
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'total_pnl': 0,
                    'win_rate': 0,
                    'avg_win': 0,
                    'avg_loss': 0,
                    'max_win': 0,
                    'max_loss': 0,
                    'profit_factor': 0,
                    'total_wins_pnl': 0,
                    'total_losses_pnl': 0,
                    'symbols': {},
                    'directions': {'LONG': 0, 'SHORT': 0},
                    'exit_reasons': {},
                    'indicator_performance': {},
                    'trades': []
                }
            
            # Process trades
            for trade in trades:
                session, symbol, direction, pnl, pnl_pct, exit_reason, entry_time, indicators_json = trade
                
                if session not in session_stats:
                    continue
                
                stats = session_stats[session]
                stats['total_trades'] += 1
                stats['total_pnl'] += pnl
                stats['directions'][direction] += 1
                
                # Track exit reasons
                if exit_reason not in stats['exit_reasons']:
                    stats['exit_reasons'][exit_reason] = 0
                stats['exit_reasons'][exit_reason] += 1
                
                # Track symbols
                if symbol not in stats['symbols']:
                    stats['symbols'][symbol] = {'trades': 0, 'pnl': 0, 'wins': 0}
                stats['symbols'][symbol]['trades'] += 1
                stats['symbols'][symbol]['pnl'] += pnl
                
                # Win/Loss tracking
                if pnl > 0:
                    stats['winning_trades'] += 1
                    stats['total_wins_pnl'] += pnl
                    stats['max_win'] = max(stats['max_win'], pnl_pct)
                    stats['symbols'][symbol]['wins'] += 1
                else:
                    stats['losing_trades'] += 1
                    stats['total_losses_pnl'] += abs(pnl)
                    stats['max_loss'] = min(stats['max_loss'], pnl_pct)
                
                # Process indicators
                if indicators_json:
                    try:
                        indicators = json.loads(indicators_json) if isinstance(indicators_json, str) else indicators_json
                        self._process_session_indicators(stats, indicators, direction, pnl > 0)
                    except:
                        pass
                
                # Store trade for detailed analysis
                stats['trades'].append({
                    'symbol': symbol,
                    'direction': direction,
                    'pnl': pnl,
                    'pnl_percentage': pnl_pct,
                    'exit_reason': exit_reason,
                    'entry_time': entry_time
                })
            
            # Calculate final metrics
            for session_key, stats in session_stats.items():
                if stats['total_trades'] > 0:
                    stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
                    
                    if stats['winning_trades'] > 0:
                        stats['avg_win'] = stats['total_wins_pnl'] / stats['winning_trades']
                    
                    if stats['losing_trades'] > 0:
                        stats['avg_loss'] = stats['total_losses_pnl'] / stats['losing_trades']
                        stats['profit_factor'] = stats['total_wins_pnl'] / stats['total_losses_pnl']
                    else:
                        stats['profit_factor'] = float('inf') if stats['total_wins_pnl'] > 0 else 0
                    
                    # Calculate symbol win rates
                    for symbol_data in stats['symbols'].values():
                        if symbol_data['trades'] > 0:
                            symbol_data['win_rate'] = (symbol_data['wins'] / symbol_data['trades']) * 100
            
            return {
                'mode': mode,
                'days_analyzed': days,
                'total_trades': len(trades),
                'sessions': session_stats,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Error analyzing session performance: {e}")
            return {'error': str(e), 'success': False}
    
    def _process_session_indicators(self, stats: Dict, indicators: Dict, direction: str, is_win: bool):
        """Process indicators for session analysis"""
        from indicator_analysis_system import IndicatorAnalysisSystem
        
        analyzer = IndicatorAnalysisSystem()
        passed_indicators, failed_indicators = analyzer.analyze_indicators(indicators, direction)
        
        # Process passed indicators
        for indicator in passed_indicators:
            name = indicator['name']
            if name not in stats['indicator_performance']:
                stats['indicator_performance'][name] = {
                    'total_passed': 0,
                    'total_failed': 0,
                    'wins_when_passed': 0,
                    'losses_when_passed': 0
                }
            
            stats['indicator_performance'][name]['total_passed'] += 1
            if is_win:
                stats['indicator_performance'][name]['wins_when_passed'] += 1
            else:
                stats['indicator_performance'][name]['losses_when_passed'] += 1
        
        # Process failed indicators
        for indicator in failed_indicators:
            name = indicator['name']
            if name not in stats['indicator_performance']:
                stats['indicator_performance'][name] = {
                    'total_passed': 0,
                    'total_failed': 0,
                    'wins_when_passed': 0,
                    'losses_when_passed': 0
                }
            
            stats['indicator_performance'][name]['total_failed'] += 1
    
    def get_best_worst_sessions(self, mode: str = "dry_run", days: int = 30) -> Dict:
        """Get best and worst performing sessions"""
        performance = self.get_session_performance(mode, days)
        
        if not performance.get('success'):
            return performance
        
        sessions = performance['sessions']
        
        # Filter sessions with trades
        active_sessions = {k: v for k, v in sessions.items() if v['total_trades'] > 0}
        
        if not active_sessions:
            return {'error': 'No active sessions found', 'success': False}
        
        # Sort by different metrics
        by_win_rate = sorted(active_sessions.items(), key=lambda x: x[1]['win_rate'], reverse=True)
        by_profit_factor = sorted(active_sessions.items(), key=lambda x: x[1]['profit_factor'], reverse=True)
        by_total_pnl = sorted(active_sessions.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
        by_total_trades = sorted(active_sessions.items(), key=lambda x: x[1]['total_trades'], reverse=True)
        
        return {
            'best_win_rate': by_win_rate[0] if by_win_rate else None,
            'worst_win_rate': by_win_rate[-1] if by_win_rate else None,
            'best_profit_factor': by_profit_factor[0] if by_profit_factor else None,
            'worst_profit_factor': by_profit_factor[-1] if by_profit_factor else None,
            'most_profitable': by_total_pnl[0] if by_total_pnl else None,
            'least_profitable': by_total_pnl[-1] if by_total_pnl else None,
            'most_active': by_total_trades[0] if by_total_trades else None,
            'least_active': by_total_trades[-1] if by_total_trades else None,
            'success': True
        }
    
    def update_trade_session(self, db_path: str, trade_id: int, entry_time: str):
        """
        Update trading session for a specific trade
        """
        try:
            session = self.get_trading_session(entry_time)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Update both open_positions and trade_history if they exist
            cursor.execute('UPDATE open_positions SET trading_session = ? WHERE id = ?', (session, trade_id))
            cursor.execute('UPDATE trade_history SET trading_session = ? WHERE id = ?', (session, trade_id))
            
            conn.commit()
            conn.close()
            
            return session
            
        except Exception as e:
            print(f"❌ Error updating trade session: {e}")
            return 'UNKNOWN'
        """Get detailed comparison between sessions"""
        performance = self.get_session_performance(mode, days)
        
        if not performance.get('success'):
            return performance
        
        sessions = performance['sessions']
        
        # Create comparison matrix
        comparison = {
            'overview': {
                'total_trades': sum(s['total_trades'] for s in sessions.values()),
                'total_pnl': sum(s['total_pnl'] for s in sessions.values()),
                'overall_win_rate': 0
            },
            'session_rankings': {
                'by_win_rate': [],
                'by_profit_factor': [],
                'by_total_pnl': [],
                'by_avg_win': []
            },
            'session_details': sessions,
            'recommendations': []
        }
        
        # Calculate overall win rate
        total_wins = sum(s['winning_trades'] for s in sessions.values())
        total_trades = sum(s['total_trades'] for s in sessions.values())
        if total_trades > 0:
            comparison['overview']['overall_win_rate'] = (total_wins / total_trades) * 100
        
        # Create rankings
        active_sessions = [(k, v) for k, v in sessions.items() if v['total_trades'] > 0]
        
        comparison['session_rankings']['by_win_rate'] = sorted(
            active_sessions, key=lambda x: x[1]['win_rate'], reverse=True
        )
        comparison['session_rankings']['by_profit_factor'] = sorted(
            active_sessions, key=lambda x: x[1]['profit_factor'], reverse=True
        )
        comparison['session_rankings']['by_total_pnl'] = sorted(
            active_sessions, key=lambda x: x[1]['total_pnl'], reverse=True
        )
        comparison['session_rankings']['by_avg_win'] = sorted(
            active_sessions, key=lambda x: x[1]['avg_win'], reverse=True
        )
        
        # Generate recommendations
        if active_sessions:
            best_session = max(active_sessions, key=lambda x: x[1]['win_rate'])
            worst_session = min(active_sessions, key=lambda x: x[1]['win_rate'])
            
            comparison['recommendations'] = [
                f"Best session: {best_session[1]['name']} with {best_session[1]['win_rate']:.1f}% win rate",
                f"Avoid: {worst_session[1]['name']} with {worst_session[1]['win_rate']:.1f}% win rate",
                f"Most active: {max(active_sessions, key=lambda x: x[1]['total_trades'])[1]['name']}",
                f"Most profitable: {max(active_sessions, key=lambda x: x[1]['total_pnl'])[1]['name']}"
            ]
        
        return comparison
    
    def get_session_comparison(self, mode: str = "dry_run", days: int = 30) -> Dict:
        """Get detailed comparison between sessions"""
        performance = self.get_session_performance(mode, days)
        
        if not performance.get('success'):
            return performance
        
        sessions = performance['sessions']
        
        # Create comparison matrix
        comparison = {
            'overview': {
                'total_trades': sum(s['total_trades'] for s in sessions.values()),
                'total_pnl': sum(s['total_pnl'] for s in sessions.values()),
                'overall_win_rate': 0
            },
            'session_rankings': {
                'by_win_rate': [],
                'by_profit_factor': [],
                'by_total_pnl': [],
                'by_avg_win': []
            },
            'session_details': sessions,
            'recommendations': [],
            'success': True
        }
        
        # Calculate overall win rate
        total_wins = sum(s['winning_trades'] for s in sessions.values())
        total_trades = sum(s['total_trades'] for s in sessions.values())
        if total_trades > 0:
            comparison['overview']['overall_win_rate'] = (total_wins / total_trades) * 100
        
        # Create rankings
        active_sessions = [(k, v) for k, v in sessions.items() if v['total_trades'] > 0]
        
        comparison['session_rankings']['by_win_rate'] = sorted(
            active_sessions, key=lambda x: x[1]['win_rate'], reverse=True
        )
        comparison['session_rankings']['by_profit_factor'] = sorted(
            active_sessions, key=lambda x: x[1]['profit_factor'], reverse=True
        )
        comparison['session_rankings']['by_total_pnl'] = sorted(
            active_sessions, key=lambda x: x[1]['total_pnl'], reverse=True
        )
        comparison['session_rankings']['by_avg_win'] = sorted(
            active_sessions, key=lambda x: x[1]['avg_win'], reverse=True
        )
        
        # Generate recommendations
        if active_sessions:
            best_session = max(active_sessions, key=lambda x: x[1]['win_rate'])
            worst_session = min(active_sessions, key=lambda x: x[1]['win_rate'])
            
            comparison['recommendations'] = [
                f"Best session: {best_session[1]['name']} with {best_session[1]['win_rate']:.1f}% win rate",
                f"Avoid: {worst_session[1]['name']} with {worst_session[1]['win_rate']:.1f}% win rate",
                f"Most active: {max(active_sessions, key=lambda x: x[1]['total_trades'])[1]['name']}",
                f"Most profitable: {max(active_sessions, key=lambda x: x[1]['total_pnl'])[1]['name']}"
            ]
        
        return comparison

# Global instance
session_analyzer = TradingSessionAnalyzer()

def get_session_analyzer():
    """Get global session analyzer instance"""
    return session_analyzer

if __name__ == "__main__":
    print("🧪 Testing Trading Session Analysis System...")
    
    analyzer = TradingSessionAnalyzer()
    
    # Test session detection
    print("\n1. Testing session detection:")
    test_times = [
        "2024-01-15 05:30:00",  # Dead Zone
        "2024-01-15 10:30:00",  # Asia
        "2024-01-15 16:30:00",  # London
        "2024-01-15 22:30:00",  # New York
    ]
    
    for time_str in test_times:
        session = analyzer.get_trading_session(time_str)
        session_info = analyzer.sessions.get(session, {})
        print(f"   {time_str} WIB → {session_info.get('color', '❓')} {session_info.get('name', session)}")
    
    # Add session columns
    print("\n2. Adding session columns to database:")
    analyzer.add_session_column_to_database()
    
    # Update existing records
    print("\n3. Updating existing records:")
    analyzer.update_existing_sessions()
    
    # Test performance analysis
    print("\n4. Testing session performance analysis:")
    performance = analyzer.get_session_performance("dry_run", 30)
    
    if performance.get('success'):
        print(f"   ✅ Analyzed {performance['total_trades']} trades")
        
        for session_key, stats in performance['sessions'].items():
            if stats['total_trades'] > 0:
                print(f"   {stats['color']} {stats['name']}: {stats['total_trades']} trades, {stats['win_rate']:.1f}% WR")
    else:
        print(f"   ❌ Error: {performance.get('error')}")
    
    print("\n✅ Trading Session Analysis System ready!")