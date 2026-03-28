#!/usr/bin/env python3
"""
OpenClaw AI System — client untuk trading bot.

Fungsi utama:
  - consult_gate()         : tanya bridge apakah sinyal boleh dibuka
  - generate_entry_reasoning(): buat narasi entry (tetap pakai Gemini/AI model)
  - generate_exit_reasoning() : buat narasi exit

Bridge (openclaw_bridge.py) yang jalan terpisah menyediakan data history
dan gate logic. OpenClaw agent membaca bridge untuk analisis via Telegram.
"""

import os
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

BRIDGE_URL    = os.getenv('OPENCLAW_BRIDGE_URL', 'http://127.0.0.1:18790')
BRIDGE_SECRET = os.getenv('OPENCLAW_BRIDGE_SECRET', 'changeme')
GATE_ENABLED  = os.getenv('OPENCLAW_GATE_ENABLED', 'true').lower() == 'true'
GATE_TIMEOUT  = float(os.getenv('OPENCLAW_GATE_TIMEOUT', '3.0'))  # detik


async def consult_gate(signal: Dict, mode: str = 'dry_run') -> Dict:
    """
    Tanya OpenClaw bridge apakah sinyal ini boleh dibuka.

    Returns:
        { approved: bool, reason: str, stats: {...} }
        Kalau bridge tidak tersedia → approved=True (fail-open, bot tetap jalan)
    """
    if not GATE_ENABLED:
        return {'approved': True, 'reason': 'Gate disabled', 'stats': {}}

    payload = {
        'symbol':    signal.get('symbol', ''),
        'direction': signal.get('direction', ''),
        'session':   signal.get('session', 'UNKNOWN'),
        'ict_score': signal.get('ict_score', 0),
        'rr_ratio':  signal.get('rr_ratio', 0),
        'mode':      mode,
    }

    try:
        timeout = aiohttp.ClientTimeout(total=GATE_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f'{BRIDGE_URL}/gate/signal',
                json=payload,
                headers={'X-Bridge-Secret': BRIDGE_SECRET}
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"⚠️  OpenClaw bridge returned {resp.status}, fail-open")
                    return {'approved': True, 'reason': f'Bridge error {resp.status}', 'stats': {}}

    except asyncio.TimeoutError:
        print(f"⚠️  OpenClaw bridge timeout ({GATE_TIMEOUT}s), fail-open")
        return {'approved': True, 'reason': 'Bridge timeout', 'stats': {}}
    except Exception as e:
        print(f"⚠️  OpenClaw bridge unavailable: {e}, fail-open")
        return {'approved': True, 'reason': f'Bridge unavailable: {e}', 'stats': {}}


async def generate_entry_reasoning(signal: Dict) -> str:
    """
    Generate narasi entry — tetap pakai Gemini AI.
    Wrapper ini memastikan backward-compat dengan crypto_bot_parallel.py
    """
    try:
        from gemini_ai_system import get_gemini_analyst
        analyst = get_gemini_analyst()
        if analyst:
            return await analyst.generate_entry_reasoning(signal)
    except Exception as e:
        print(f"⚠️  Entry reasoning error: {e}")
    return ""


async def generate_exit_reasoning(position_data: Dict, exit_reason: str) -> str:
    """Generate narasi exit — tetap pakai Gemini AI."""
    try:
        from gemini_ai_system import get_gemini_analyst
        analyst = get_gemini_analyst()
        if analyst:
            return await analyst.generate_exit_reasoning(position_data, exit_reason)
    except Exception as e:
        print(f"⚠️  Exit reasoning error: {e}")
    return ""


# Singleton
_instance: Optional['OpenClawClient'] = None


class OpenClawClient:
    """Wrapper class untuk backward-compat jika ada kode yang pakai instance."""

    async def consult_gate(self, signal: Dict, mode: str = 'dry_run') -> Dict:
        return await consult_gate(signal, mode)

    async def generate_entry_reasoning(self, signal: Dict) -> str:
        return await generate_entry_reasoning(signal)

    async def generate_exit_reasoning(self, position_data: Dict, exit_reason: str) -> str:
        return await generate_exit_reasoning(position_data, exit_reason)


def get_openclaw_client() -> OpenClawClient:
    global _instance
    if _instance is None:
        _instance = OpenClawClient()
    return _instance
