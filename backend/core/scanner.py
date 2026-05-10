"""
NIFTY SNIPER SCANNER — Indian Index Intraday Engine
Scans: NIFTY50, BANKNIFTY, FINNIFTY, MIDCAPNIFTY, SENSEX, BANKEX
Market Hours: 9:15 AM – 3:30 PM IST
Max Signals: 4-5 per day TOTAL across all indices combined.
"""
import asyncio
import logging
from datetime import datetime, time
import pytz

from services.market_data import market_data_service, INDIAN_INDICES
from services.signal_engine import signal_engine
from services.telegram_bot import telegram_service
from services.chart_service import chart_service
from services.replay_engine import replay_engine
from core.websocket_manager import manager
from core.store import (
    add_signal, set_scanner_state, get_scanner_state,
    is_in_cooldown, get_daily_signal_count, has_active_trade,
    get_active_trade
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

async def monitor_active_trade(trade: dict, current_price: float):
    """
    Monitors an active signal for TP1, TP2, or SL hits.
    Sends Telegram follow-ups.
    """
    symbol = trade['symbol']
    direction = trade['direction']
    tp1 = trade['take_profit_1']
    tp2 = trade['take_profit_2']
    sl = trade['stop_loss']
    
    # --- 1. SL HIT ---
    is_sl_hit = (direction == "LONG" and current_price <= sl) or \
                (direction == "SHORT" and current_price >= sl)
    
    if is_sl_hit:
        pnl = current_price - trade['entry'] if direction == "LONG" else trade['entry'] - current_price
        from core.store import close_active_trade
        close_active_trade(outcome="LOSS", exit_price=current_price, pnl_points=pnl)
        await telegram_service.send_trade_alert(
            f"❌ *TRADE CLOSED (SL HIT)*\n━━━━━━━━━━━━━━\n📊 *{symbol}*\n📉 *Outcome:* LOSS\n💰 *Exit:* `{current_price:,.2f}`\n📉 *P&L:* `{pnl:,.2f}` pts"
        )
        # Generate and Send Replay
        replay_path = await replay_engine.generate_trade_replay(trade, df_15m) # Using current 15m context
        if replay_path:
            await telegram_service.send_trade_alert("🧠 *NIFTY SNIPER REPLAY ENGINE — ANALYSIS*")
            await telegram_service.send_signal(trade, photo_path=replay_path)
        return

    # --- 2. TP1 HIT ---
    is_tp1_hit = (direction == "LONG" and current_price >= tp1) or \
                 (direction == "SHORT" and current_price <= tp1)
                 
    if is_tp1_hit and not trade.get('hit_tp1'):
        from core.store import update_signal
        update_signal(trade['id'], {"hit_tp1": True, "is_breakeven": True, "stop_loss": trade['entry']})
        await telegram_service.send_trade_alert(
            f"✅ *TARGET 1 REACHED (TP1)*\n━━━━━━━━━━━━━━\n📊 *{symbol}*\n💰 *Price:* `{current_price:,.2f}`\n🛡️ *Security:* SL moved to ENTRY (Risk Free)"
        )

    # --- 3. TP2 HIT (Final) ---
    is_tp2_hit = (direction == "LONG" and current_price >= tp2) or \
                 (direction == "SHORT" and current_price <= tp2)
                 
    if is_tp2_hit:
        pnl = current_price - trade['entry'] if direction == "LONG" else trade['entry'] - current_price
        from core.store import close_active_trade
        close_active_trade(outcome="WIN", exit_price=current_price, pnl_points=pnl)
        await telegram_service.send_trade_alert(
            f"🏆 *TARGET 2 REACHED (TP2)*\n━━━━━━━━━━━━━━\n📊 *{symbol}*\n💰 *Final Exit:* `{current_price:,.2f}`\n📈 *Outcome:* WIN\n💰 *Total P&L:* `{pnl:,.2f}` pts"
        )
        # Generate and Send Replay
        replay_path = await replay_engine.generate_trade_replay(trade, df_15m)
        if replay_path:
            await telegram_service.send_trade_alert("🧠 *NIFTY SNIPER REPLAY ENGINE — ANALYSIS*")
            await telegram_service.send_signal(trade, photo_path=replay_path)


# Lot sizes for profit calculation
LOT_SIZES = {
    "NIFTY50": 25,
    "BANKNIFTY": 15,
    "FINNIFTY": 40,
    "MIDCAPNIFTY": 75,
    "SENSEX": 10
}

async def generate_eod_report():
    """Compiles and sends the final performance report for the day."""
    from core.store import get_signals
    signals = get_signals(limit=20)
    today_str = datetime.now(IST).strftime("%Y-%m-%d")
    
    # Filter for today's closed signals
    today_signals = [s for s in signals if s['created_at'].startswith(today_str) and s['status'] == "CLOSED"]
    
    if not today_signals:
        await telegram_service.send_trade_alert("📉 *DAILY RECAP*\nNo trades were taken today. Market conditions did not meet institutional standards.")
        return

    wins = [s for s in today_signals if s['outcome'] == "WIN"]
    losses = [s for s in today_signals if s['outcome'] == "LOSS"]
    total_points = sum([s['pnl_points'] for s in today_signals])
    
    # Calculate estimated profit for 1 lot
    total_profit = 0
    for s in today_signals:
        lot_size = LOT_SIZES.get(s['symbol'], 25)
        total_profit += s['pnl_points'] * lot_size

    report = (
        f"📊 *DAILY RECAP — {datetime.now(IST).strftime('%d %b %Y')}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ *Total Trades:* `{len(today_signals)}`\n"
        f"🏆 *Wins:* `{len(wins)}` | ❌ *Losses:* `{len(losses)}` \n"
        f"📈 *Win Rate:* `{int(len(wins)/len(today_signals)*100)}%` \n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Total Points Covered:* `{total_points:,.2f}` pts\n"
        f"💰 *Est. Profit (1 Lot):* `₹{total_profit:,.2f}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏁 _Sniper resting for the day. See you tomorrow!_"
    )
    
    await telegram_service.send_trade_alert(report)


async def market_scanner():
    logger.info("🎯 NIFTY SNIPER ENGINE ACTIVE — Indian Index Institutional Scanner")
    eod_sent = False
    
    # ... (rest of initial state)
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
            now_ist_dt = datetime.now(IST)
            now_time = now_ist_dt.time()

            # ── EOD Report Trigger (3:30 PM - 3:35 PM) ──
            if time(15, 30) <= now_time <= time(15, 35) and not eod_sent:
                await generate_eod_report()
                eod_sent = True
            
            # Reset EOD flag at midnight or early morning
            if time(0, 0) <= now_time <= time(9, 0):
                eod_sent = False

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

            # ── Trade Monitoring ──
            active_trade = get_active_trade()
            if active_trade:
                # We need fresh price for the active trade symbol
                active_symbol = active_trade['symbol']
                active_df = await market_data_service.fetch_ohlcv(active_symbol, '1m')
                if active_df is not None and not active_df.empty:
                    last_price = float(active_df['close'].iloc[-1])
                    await monitor_active_trade(active_trade, last_price)

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
                    # ── FETCH ADVANCED CONFLUENCE BUNDLE ──
                    bundle = await market_data_service.get_advanced_confluence_data(symbol)
                    df_15m = bundle['dfs'].get('15m')
                    
                    if df_15m is None or df_15m.empty:
                        logger.warning(f"⚠️  {symbol}: No data.")
                        continue

                    curr_price = float(df_15m['close'].iloc[-1])
                    curr_vwap  = float(df_15m['vwap'].iloc[-1]) if 'vwap' in df_15m.columns else 0

                    # Update scanner state for dashboard
                    for i, item in enumerate(current_state):
                        if item["symbol"] == symbol:
                            current_state[i].update({
                                "price": round(curr_price, 2),
                                "vwap": round(curr_vwap, 2),
                                "session": bundle['session'],
                                "vix": bundle['vix'],
                                "status": "SCANNING",
                                "bias": "ANALYZING",
                            })
                            break

                    set_scanner_state(current_state)
                    await manager.broadcast({"type": "scanner_update", "data": current_state})

                    # ── ADVANCED SNIPER ANALYSIS ──
                    signal = await signal_engine.analyze_sniper_setup(bundle, symbol)

                    if signal:
                        rank = signal.get('rank', 'B')
                        logger.info(f"🎯 INSTITUTIONAL {rank} SETUP: {symbol} {signal['direction']} | Confidence: {signal['confidence']}%")
                        
                        # Only alert for A+ and A
                        if rank in ["A+", "A"]:
                            stored = add_signal(signal)

                            # Generate Chart Image
                            photo_path = chart_service.generate_signal_chart(symbol, df_15m, signal)

                            # Send Telegram alert with Photo
                            await telegram_service.send_signal(stored, photo_path=photo_path)

                            # Broadcast to WebSocket
                            await manager.broadcast({"type": "new_signal", "data": stored})

                            # Update Dashboard
                            for i, item in enumerate(current_state):
                                if item["symbol"] == symbol:
                                    current_state[i]["status"] = f"{rank} SIGNAL — {signal['direction']}"
                                    break
                            set_scanner_state(current_state)
                        else:
                            logger.info(f"⏭️  {symbol}: Low rank ({rank}). Filtering for quality.")

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
