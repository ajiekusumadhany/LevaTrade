#!/usr/bin/env python3
"""
Pair Performance Analysis System
Menganalisis performa setiap trading pair dengan data market terbaru
"""
import sqlite3
import json
import asyncio
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from market_data_system import get_market_data_system

class PairPerformanceAnalyzer:
    def __init__(self):
        self.dry_run_db = "dry_run_trades.db"
        self.real_db = "real_trades.db"
        self.market_data_system = get_market_data_system()
        
        # Volume categories (24h volume)
        self.volume_categories = {
            'KOIN_BESAR': {'min': 500_000_000, 'color': '🟢', 'description': 'Volume > $500M'},
            'MENENGAH': {'min': 100_000_000, 'color': '🟡', 'description': 'Volume $100M - $500M'},
            'KOIN_KECIL': {'min': 0, 'color': '🔴', 'description': 'Volume < $100M'}
        }
        
        # Market cap categories
        self.market_cap_categories = {
            'BESAR': {'min': 5_000_000_000, 'color': '🟢', 'description': 'Market Cap > $5B'},
            'MENENGAH': {'min': 1_000_000_000, 'color': '🟡', 'description': 'Market Cap $1B - $5B'},
            'KECIL': {'min': 0, 'color': '🔴', 'description': 'Market Cap < $1B'}
        }
    
    def categorize_volume(self, volume_24h: float) -> Dict:
        """Categorize volume based on 24h volume"""
        if volume_24h >= self.volume_categories['KOIN_BESAR']['min']:
            return {'category': 'KOIN_BESAR', **self.volume_categories['KOIN_BESAR']}
        elif volume_24h >= self.volume_categories['MENENGAH']['min']:
            return {'category': 'MENENGAH', **self.volume_categories['MENENGAH']}
        else:
            return {'category': 'KOIN_KECIL', **self.volume_categories['KOIN_KECIL']}
    
    def categorize_market_cap(self, market_cap: float) -> Dict:
        """Categorize market cap"""
        if market_cap >= self.market_cap_categories['BESAR']['min']:
            return {'category': 'BESAR', **self.market_cap_categories['BESAR']}
        elif market_cap >= self.market_cap_categories['MENENGAH']['min']:
            return {'category': 'MENENGAH', **self.market_cap_categories['MENENGAH']}
        else:
            return {'category': 'KECIL', **self.market_cap_categories['KECIL']}
    
    async def get_current_market_data(self, symbol: str) -> Dict:
        """Get current market data for a symbol"""
        try:
            market_data = await self.market_data_system.get_market_data(symbol)
            return market_data
        except Exception as e:
            print(f"⚠️ Could not get current market data for {symbol}: {e}")
            return {}
    
    async def get_pair_performance(self, mode: str = "dry_run", days: int = 30) -> Dict:
        """Get comprehensive pair performance analysis"""
        db_path = self.dry_run_db if mode == "dry_run" else self.real_db
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Get all trades for the period
            cursor.execute('''
                SELECT symbol, direction, pnl, pnl_percentage, exit_reason, entry_time,
                       market_cap, total_volume_24h, market_cap_category, volume_category
                FROM trade_history 
                WHERE entry_time >= ?
                ORDER BY entry_time DESC
            ''', (cutoff_date,))
            
            trades = cursor.fetchall()
            conn.close()
            
            # Group trades by symbol
            pair_stats = {}
            
            for trade in trades:
                symbol = trade[0]
                direction = trade[1]
                pnl = trade[2]
                pnl_percentage = trade[3]
                exit_reason = trade[4]
                entry_time = trade[5]
                
                # Handle market data (may be None for old trades)
                stored_market_cap = trade[6] if len(trade) > 6 and trade[6] else 0
                stored_volume_24h = trade[7] if len(trade) > 7 and trade[7] else 0
                stored_market_cap_category = trade[8] if len(trade) > 8 and trade[8] else ""
                stored_volume_category = trade[9] if len(trade) > 9 and trade[9] else ""
                
                if symbol not in pair_stats:
                    pair_stats[symbol] = {
                        'symbol': symbol,
                        'total_trades': 0,
                        'total_pnl': 0,
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'long_trades': 0,
                        'short_trades': 0,
                        'win_rate': 0,
                        'long_percentage': 0,
                        'short_percentage': 0,
                        'avg_pnl': 0,
                        'max_win': 0,
                        'max_loss': 0,
                        'exit_reasons': {},
                        'stored_market_cap': stored_market_cap,
                        'stored_volume_24h': stored_volume_24h,
                        'stored_market_cap_category': stored_market_cap_category,
                        'stored_volume_category': stored_volume_category,
                        'current_market_data': None  # Will be filled later
                    }
                
                stats = pair_stats[symbol]
                stats['total_trades'] += 1
                stats['total_pnl'] += pnl
                
                # Direction tracking
                if direction == 'LONG':
                    stats['long_trades'] += 1
                else:
                    stats['short_trades'] += 1
                
                # Win/Loss tracking
                if pnl > 0:
                    stats['winning_trades'] += 1
                    stats['max_win'] = max(stats['max_win'], pnl_percentage)
                else:
                    stats['losing_trades'] += 1
                    stats['max_loss'] = min(stats['max_loss'], pnl_percentage)
                
                # Exit reasons
                if exit_reason not in stats['exit_reasons']:
                    stats['exit_reasons'][exit_reason] = 0
                stats['exit_reasons'][exit_reason] += 1
                
                # Update stored market data with most recent
                if stored_market_cap > 0:
                    stats['stored_market_cap'] = stored_market_cap
                if stored_volume_24h > 0:
                    stats['stored_volume_24h'] = stored_volume_24h
                if stored_market_cap_category:
                    stats['stored_market_cap_category'] = stored_market_cap_category
                if stored_volume_category:
                    stats['stored_volume_category'] = stored_volume_category
            
            # Calculate percentages and get current market data
            for symbol, stats in pair_stats.items():
                if stats['total_trades'] > 0:
                    stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
                    stats['long_percentage'] = (stats['long_trades'] / stats['total_trades']) * 100
                    stats['short_percentage'] = (stats['short_trades'] / stats['total_trades']) * 100
                    stats['avg_pnl'] = stats['total_pnl'] / stats['total_trades']
                
                # Get current market data
                try:
                    current_data = await self.get_current_market_data(symbol)
                    if current_data:
                        stats['current_market_data'] = current_data
                        
                        # Categorize current data
                        current_volume = current_data.get('total_volume_24h', 0)
                        current_market_cap = current_data.get('market_cap', 0)
                        
                        stats['current_volume_category'] = self.categorize_volume(current_volume)
                        stats['current_market_cap_category'] = self.categorize_market_cap(current_market_cap)
                        
                        # Update with current values
                        stats['current_market_cap'] = current_market_cap
                        stats['current_volume_24h'] = current_volume
                        stats['current_price'] = current_data.get('current_price', 0)
                        stats['price_change_24h'] = current_data.get('price_change_percentage_24h', 0)
                    else:
                        # Use stored data if current not available
                        stats['current_volume_category'] = self.categorize_volume(stats['stored_volume_24h'])
                        stats['current_market_cap_category'] = self.categorize_market_cap(stats['stored_market_cap'])
                        stats['current_market_cap'] = stats['stored_market_cap']
                        stats['current_volume_24h'] = stats['stored_volume_24h']
                        stats['current_price'] = 0
                        stats['price_change_24h'] = 0
                        
                except Exception as e:
                    print(f"⚠️ Error getting current data for {symbol}: {e}")
                    # Use stored data as fallback
                    stats['current_volume_category'] = self.categorize_volume(stats['stored_volume_24h'])
                    stats['current_market_cap_category'] = self.categorize_market_cap(stats['stored_market_cap'])
                    stats['current_market_cap'] = stats['stored_market_cap']
                    stats['current_volume_24h'] = stats['stored_volume_24h']
                    stats['current_price'] = 0
                    stats['price_change_24h'] = 0
            
            # Sort by total PnL (highest to lowest)
            sorted_pairs = sorted(pair_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
            
            return {
                'mode': mode,
                'days_analyzed': days,
                'total_pairs': len(pair_stats),
                'pairs': dict(sorted_pairs),
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Error analyzing pair performance: {e}")
            return {'error': str(e), 'success': False}
    
    def get_pair_categories_summary(self, pair_data: Dict) -> Dict:
        """Get summary of pairs by categories"""
        if not pair_data.get('success'):
            return {'error': 'No pair data available'}
        
        volume_summary = {'KOIN_BESAR': [], 'MENENGAH': [], 'KOIN_KECIL': []}
        market_cap_summary = {'BESAR': [], 'MENENGAH': [], 'KECIL': []}
        
        for symbol, stats in pair_data['pairs'].items():
            # Volume categorization
            vol_category = stats.get('current_volume_category', {}).get('category', 'KOIN_KECIL')
            volume_summary[vol_category].append({
                'symbol': symbol,
                'total_pnl': stats['total_pnl'],
                'win_rate': stats['win_rate'],
                'total_trades': stats['total_trades'],
                'volume_24h': stats.get('current_volume_24h', 0)
            })
            
            # Market cap categorization
            mc_category = stats.get('current_market_cap_category', {}).get('category', 'KECIL')
            market_cap_summary[mc_category].append({
                'symbol': symbol,
                'total_pnl': stats['total_pnl'],
                'win_rate': stats['win_rate'],
                'total_trades': stats['total_trades'],
                'market_cap': stats.get('current_market_cap', 0)
            })
        
        # Sort each category by PnL
        for category in volume_summary:
            volume_summary[category].sort(key=lambda x: x['total_pnl'], reverse=True)
        
        for category in market_cap_summary:
            market_cap_summary[category].sort(key=lambda x: x['total_pnl'], reverse=True)
        
        return {
            'volume_categories': volume_summary,
            'market_cap_categories': market_cap_summary,
            'category_definitions': {
                'volume': self.volume_categories,
                'market_cap': self.market_cap_categories
            }
        }
    
    def get_trading_recommendations(self, pair_data: Dict) -> List[str]:
        """Generate trading recommendations based on pair performance"""
        if not pair_data.get('success'):
            return ["No data available for recommendations"]
        
        recommendations = []
        pairs = pair_data['pairs']
        
        if not pairs:
            return ["No trading pairs found in the specified period"]
        
        # Best performing pairs
        best_pairs = list(pairs.items())[:3]
        worst_pairs = list(pairs.items())[-3:]
        
        # Volume-based recommendations
        koin_kecil_pairs = []
        for symbol, stats in pairs.items():
            vol_category = stats.get('current_volume_category', {}).get('category', 'KOIN_KECIL')
            if vol_category == 'KOIN_KECIL' and stats['total_trades'] > 0:
                koin_kecil_pairs.append((symbol, stats))
        
        recommendations.append(f"🏆 Best Performing Pairs: {', '.join([p[0] for p in best_pairs])}")
        recommendations.append(f"💔 Worst Performing Pairs: {', '.join([p[0] for p in worst_pairs])}")
        
        if koin_kecil_pairs:
            recommendations.append(f"⚠️ AVOID Low Volume Pairs (<$100M): {', '.join([p[0] for p in koin_kecil_pairs[:5]])}")
        
        # High win rate pairs
        high_wr_pairs = [(s, st) for s, st in pairs.items() if st['win_rate'] > 60 and st['total_trades'] >= 3]
        if high_wr_pairs:
            high_wr_pairs.sort(key=lambda x: x[1]['win_rate'], reverse=True)
            recommendations.append(f"🎯 High Win Rate Pairs (>60%): {', '.join([p[0] for p in high_wr_pairs[:3]])}")
        
        return recommendations

# Global instance
pair_analyzer = PairPerformanceAnalyzer()

def get_pair_analyzer():
    """Get global pair analyzer instance"""
    return pair_analyzer

if __name__ == "__main__":
    async def test_pair_analysis():
        print("🧪 Testing Pair Performance Analysis System...")
        
        analyzer = PairPerformanceAnalyzer()
        
        # Test pair performance analysis
        print("\n📊 Testing Pair Performance Analysis...")
        performance = await analyzer.get_pair_performance("dry_run", 30)
        
        if performance.get('success'):
            print(f"✅ Analyzed {performance['total_pairs']} pairs")
            
            for symbol, stats in list(performance['pairs'].items())[:5]:
                vol_cat = stats.get('current_volume_category', {})
                mc_cat = stats.get('current_market_cap_category', {})
                
                print(f"\n💰 {symbol}:")
                print(f"   Total PnL: ${stats['total_pnl']:.2f}")
                print(f"   Win Rate: {stats['win_rate']:.1f}% ({stats['winning_trades']}/{stats['total_trades']})")
                print(f"   LONG: {stats['long_percentage']:.1f}% | SHORT: {stats['short_percentage']:.1f}%")
                print(f"   Volume: {vol_cat.get('color', '❓')} {vol_cat.get('category', 'Unknown')} (${stats.get('current_volume_24h', 0):,.0f})")
                print(f"   Market Cap: {mc_cat.get('color', '❓')} {mc_cat.get('category', 'Unknown')} (${stats.get('current_market_cap', 0):,.0f})")
        else:
            print(f"❌ Error: {performance.get('error')}")
        
        print("\n✅ Pair Performance Analysis System ready!")
    
    asyncio.run(test_pair_analysis())