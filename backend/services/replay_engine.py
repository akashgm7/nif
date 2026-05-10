import matplotlib.pyplot as plt
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class ReplayEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.output_dir = "replays"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    async def generate_trade_replay(self, signal: Dict[str, Any], historical_df: pd.DataFrame) -> str:
        """
        Generates a 'Post-Trade Review' chart showing the entry, exit, and aftermath.
        """
        try:
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Use data from start of signal to +4 hours for aftermath
            df = historical_df.copy()
            
            # Draw Candlesticks
            for i, row in df.iterrows():
                color = '#10b981' if row['close'] >= row['open'] else '#ef4444'
                ax.vlines(i, row['low'], row['high'], color=color, linewidth=1)
                ax.vlines(i, min(row['open'], row['close']), max(row['open'], row['close']), color=color, linewidth=6)

            # 1. Mark Entry Point
            entry_idx = len(df) // 4 # Approximate entry in the window
            ax.annotate('ENTRY HERE', xy=(entry_idx, signal['entry']), xytext=(entry_idx-5, signal['entry']*1.002),
                        arrowprops=dict(facecolor='#3b82f6', shrink=0.05), color='#3b82f6', weight='bold')

            # 2. Draw levels
            ax.axhline(signal['entry'], color='white', alpha=0.3, linestyle='--')
            ax.axhline(signal['stop_loss'], color='#ef4444', alpha=0.5, linestyle=':', label='SL')
            ax.axhline(signal['take_profit_2'], color='#10b981', alpha=0.5, linestyle=':', label='Target')

            # 3. Add Confluence Breakdown as Text
            reasons = "\n".join(signal.get('reasons', []))
            plt.text(0.02, 0.95, f"CONFLUENCES:\n{reasons}", transform=ax.transAxes, 
                     verticalalignment='top', bbox=dict(boxstyle='round', facecolor='black', alpha=0.5), color='gold', fontsize=9)

            # 4. Final Verdict
            outcome = signal.get('outcome', 'ANALYZING')
            pnl = signal.get('pnl_points', 0)
            ax.set_title(f"NIFTY SNIPER REPLAY: {signal['symbol']} | {outcome} ({pnl:+.2f} pts)", color='white', fontsize=16, pad=20)
            
            ax.set_ylabel("Price")
            ax.grid(True, alpha=0.05)
            ax.legend(loc='lower left')

            file_path = os.path.join(self.output_dir, f"replay_{signal['id']}.png")
            plt.savefig(file_path, bbox_inches='tight', dpi=130)
            plt.close(fig)
            
            return file_path
        except Exception as e:
            self.logger.error(f"Replay generation error: {e}")
            return None

replay_engine = ReplayEngine()
