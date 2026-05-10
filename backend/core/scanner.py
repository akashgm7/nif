"""
NIFTY SNIPER SCANNER — Indian Index Intraday Engine
Scans: NIFTY50, BANKNIFTY, FINNIFTY, MIDCAPNIFTY, SENSEX, BANKEX
Market Hours: 9:15 AM – 3:30 PM IST
Max Signals: 4-5 per day TOTAL across all indices combined.
"""
import asyncio
import logging
from datetime import datetime
import pytz

from services.market_data import market_data_service, INDIAN_INDICES
from services.signal_engine import signal_engine
from services.telegram_bot import telegram_service
from services.chart_service import chart_service
from core.websocket_manager import manager
from core.store import (
    add_signal, set_scanner_state, get_scanner_state,
    is_in_cooldown, get_daily_signal_count, has_active_trade
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
IST = pytz.timezone("Asia/Kolkata")

# All Indian indices to scan
INDICES = list(INDIAN_INDICES.keys())

# Hard limit: 5 golden setups per day total
DAILY_SIGNAL_LIMIT = 5

# Cooldown per index: 90 minutes after a signal
COOLDOWN_MINUTES = 90


async def market_scanner():
    logger.info("🎯 NIFTY SNIPER ENGINE ACTIVE — Indian Index Institutional Scanner")

    initial_state = [
        {
            "symbol": sym,
            "bias": "INITIALIZING",
            "session": "—",
            "price": 0,
            "vwap": 0,
            "vix": None,
            "status": "ANALYZING"
        }
        for sym in INDICES
    ]
    set_scanner_state(initial_state)

    scan_count = 0

    while True:
        try:
            # ── Market Hours Guard ──
            if not market_data_service.is_market_open():
                now_ist = datetime.now(IST).strftime("%H:%M IST")
                logger.info(f"⏰ Market closed ({now_ist}). Scanner waiting...")
                await manager.broadcast({
                    "type": "scanner_status",
                    "data": {"status": "MARKET_CLOSED", "time": now_ist}
                })
                await asyncio.sleep(60)
                continue

            # ── Daily Signal Limit Guard ──
            daily_count = get_daily_signal_count()
            if daily_count >= DAILY_SIGNAL_LIMIT:
                logger.info(f"🏁 Daily limit reached ({daily_count}/{DAILY_SIGNAL_LIMIT}). Sniper resting.")
                await asyncio.sleep(300)
                continue

            # ── One Active Trade at a Time Guard ──
            if has_active_trade():
                logger.info("⚡ Active trade in progress. Blocking new signals.")
                await asyncio.sleep(60)
                continue

            # ── Fetch India VIX ──
            india_vix = market_data_service.get_india_vix()
            session   = market_data_service.get_current_session()
            is_prime  = market_data_service.is_prime_window()

            scan_count += 1
            logger.info(f"🔍 Scan #{scan_count} | Session: {session} | VIX: {india_vix} | Prime: {is_prime}")

            current_state = get_scanner_state()

            for symbol in INDICES:
                # ── Cooldown check per index ──
                if is_in_cooldown(symbol, COOLDOWN_MINUTES):
                    logger.info(f"⏭️  {symbol} in cooldown. Skipping.")
                    continue

                try:
                    df_1h, df_15m, df_5m = await market_data_service.get_multi_tf_data(symbol)

                    if df_15m is None or df_15m.empty:
                        logger.warning(f"⚠️  {symbol}: No 15m data.")
                        continue

                    # Calculate VWAP
                    if df_15m is not None and not df_15m.empty:
                        df_15m = market_data_service.calculate_vwap(df_15m)

                    curr_price = float(df_15m['close'].iloc[-1])
                    curr_vwap  = float(df_15m['vwap'].iloc[-1]) if 'vwap' in df_15m.columns else 0

                    # Update scanner state
                    for i, item in enumerate(current_state):
                        if item["symbol"] == symbol:
                            current_state[i].update({
                                "price": round(curr_price, 2),
                                "vwap": round(curr_vwap, 2),
                                "session": session,
                                "vix": india_vix,
                                "status": "SCANNING",
                                "bias": "SEARCHING",
                            })
                            break

                    set_scanner_state(current_state)
                    await manager.broadcast({"type": "scanner_update", "data": current_state})

                    # ── SNIPER ANALYSIS ──
                    data_bundle = {"1h": df_1h, "15m": df_15m, "5m": df_5m}
                    signal = await signal_engine.analyze_sniper_setup(
                        data=data_bundle,
                        symbol=symbol,
                        session=session,
                        is_prime_window=is_prime,
                        india_vix=india_vix,
                    )

                    if signal:
                        daily_count = get_daily_signal_count()
                        if daily_count >= DAILY_SIGNAL_LIMIT:
                            logger.info(f"⛔ Daily limit {DAILY_SIGNAL_LIMIT} hit. Ignoring {symbol} signal.")
                            break

                        logger.info(f"🎯 GOLDEN SETUP: {symbol} {signal['direction']} | Confidence: {signal['confidence']}%")
                        stored = add_signal(signal)

                        # Generate Chart Image
                        photo_path = chart_service.generate_signal_chart(symbol, df_15m, signal)

                        # Send Telegram alert with Photo
                        await telegram_service.send_signal(stored, photo_path=photo_path)

                        # Broadcast to WebSocket clients
                        await manager.broadcast({"type": "new_signal", "data": stored})

                        # Update scanner state entry
                        for i, item in enumerate(current_state):
                            if item["symbol"] == symbol:
                                current_state[i]["status"] = f"SIGNAL — {signal['direction']}"
                                break
                        set_scanner_state(current_state)

                except asyncio.TimeoutError:
                    logger.error(f"⏱️  {symbol}: Data fetch timeout")
                    continue
                except Exception as e:
                    logger.error(f"❌ Error scanning {symbol}: {e}")
                    continue

        except Exception as e:
            logger.error(f"🔥 Scanner loop error: {e}")

        # 2-minute intervals — institutional patience
        await asyncio.sleep(120)


def start_scanner():
    asyncio.create_task(market_scanner())
