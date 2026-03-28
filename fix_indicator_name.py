#!/usr/bin/env python3
"""
Script untuk memperbaiki missing 'name' key di indicator_analysis_system.py
"""

def fix_indicator_analysis():
    with open('indicator_analysis_system.py', 'r') as f:
        content = f.read()
    
    # Fix patterns yang tidak memiliki 'name' key
    fixes = [
        # RSI value LONG
        (
            "                return {\n                    'passed': passed,\n                    'description': f'RSI Level ({rsi_value:.1f})',",
            "                return {\n                    'name': indicator_name,\n                    'passed': passed,\n                    'description': f'RSI Level ({rsi_value:.1f})',"
        ),
        # ATR value
        (
            "            return {\n                'passed': passed,\n                'description': f'ATR Value ({atr_value:.6f})',",
            "            return {\n                'name': indicator_name,\n                'passed': passed,\n                'description': f'ATR Value ({atr_value:.6f})',"
        ),
        # EMA fast value
        (
            "            return {\n                'passed': ema_fast > 0,\n                'description': f'EMA Fast ({ema_fast:.6f})',",
            "            return {\n                'name': indicator_name,\n                'passed': ema_fast > 0,\n                'description': f'EMA Fast ({ema_fast:.6f})',"
        ),
        # EMA slow value
        (
            "            return {\n                'passed': ema_slow > 0,\n                'description': f'EMA Slow ({ema_slow:.6f})',",
            "            return {\n                'name': indicator_name,\n                'passed': ema_slow > 0,\n                'description': f'EMA Slow ({ema_slow:.6f})',"
        ),
        # MACD line value LONG
        (
            "                return {\n                    'passed': passed,\n                    'description': f'MACD Line ({macd_line:.6f})',",
            "                return {\n                    'name': indicator_name,\n                    'passed': passed,\n                    'description': f'MACD Line ({macd_line:.6f})',"
        ),
        # Signal line value
        (
            "            return {\n                'passed': True,  # Signal line selalu valid\n                'description': f'Signal Line ({signal_line:.6f})',",
            "            return {\n                'name': indicator_name,\n                'passed': True,  # Signal line selalu valid\n                'description': f'Signal Line ({signal_line:.6f})',"
        ),
        # Support resistance
        (
            "            return {\n                'passed': sr_level > 0,\n                'description': f'Support/Resistance ({sr_level:.6f})',",
            "            return {\n                'name': indicator_name,\n                'passed': sr_level > 0,\n                'description': f'Support/Resistance ({sr_level:.6f})',"
        ),
        # Price distance
        (
            "            return {\n                'passed': passed,\n                'description': f'Price Distance from Level ({distance:.4f})',",
            "            return {\n                'name': indicator_name,\n                'passed': passed,\n                'description': f'Price Distance from Level ({distance:.4f})',"
        ),
        # Unknown indicator
        (
            "        return {\n            'passed': False,\n            'description': f'Unknown Indicator ({indicator_name})',",
            "        return {\n            'name': indicator_name,\n            'passed': False,\n            'description': f'Unknown Indicator ({indicator_name})',"
        )
    ]
    
    # Apply fixes
    for old_pattern, new_pattern in fixes:
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            print(f"✅ Fixed pattern: {old_pattern[:50]}...")
        else:
            print(f"⚠️ Pattern not found: {old_pattern[:50]}...")
    
    # Write back
    with open('indicator_analysis_system.py', 'w') as f:
        f.write(content)
    
    print("🔧 Indicator analysis system fixed!")

if __name__ == "__main__":
    fix_indicator_analysis()