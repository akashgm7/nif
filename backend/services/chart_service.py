import matplotlib.pyplot as plt
import pandas as pd
import os
import logging
from typing import Dict, Any

class ChartService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.output_dir = "charts"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def generate_signal_chart(self, symbol: str, df: pd.DataFrame, signal: Dict[str, Any]) -> str:
        """
        Generates a candlestick-style chart with Institutional Levels.
        """
        try:
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(12, 7))
            
            df_plot = df.tail(50).reset_index()
            
            # Draw Candlesticks
            for i, row in df_plot.iterrows():
                color = '#10b981' if row['close'] >= row['open'] else '#ef4444'
                ax.vlines(i, row['low'], row['high'], color=color, linewidth=1)
                ax.vlines(i, min(row['open'], row['close']), max(row['open'], row['close']), color=color, linewidth=5)

            # 1. VWAP Bands (Stretched detection)
            if 'vwap_upper_2' in df_plot.columns:
                ax.fill_between(range(len(df_plot)), df_plot['vwap_lower_2'], df_plot['vwap_upper_2'], color='#3b82f6', alpha=0.05)
                ax.plot(df_plot['vwap'], color='#3b82f6', alpha=0.5, linestyle=':', label='VWAP')

            # 2. Institutional Levels (PDH / PDL / ORB)
            # These would ideally come from the bundle, but we can pass them in or re-calc
            # For the demo chart, we check if they are in the signal reason or extra metadata
            # We will use horizontal lines for any levels detected in the reason text or signal data
            
            # 3. Entry, SL, TP Lines
            ax.axhline(signal['entry'], color='white', linestyle='-', linewidth=1, label=f"ENTRY ({signal['entry']})")
            ax.axhline(signal['stop_loss'], color='#ef4444', linestyle='--', linewidth=1.5, label='SL')
            ax.axhline(signal['take_profit_2'], color='#10b981', linestyle='--', linewidth=1.5, label='TP Target')

            ax.set_title(f"{symbol} [{signal.get('rank', 'A')}] Sniper Analysis", color='white', fontsize=16, pad=20)
            ax.set_ylabel("Price")
            ax.grid(True, alpha=0.05)
            ax.legend(loc='upper left', fontsize='x-small')

            # Save
            file_path = os.path.join(self.output_dir, f"{symbol}_signal.png")
            plt.savefig(file_path, bbox_inches='tight', dpi=120)
            plt.close(fig)
            
            return file_path
        except Exception as e:
            self.logger.error(f"Matplotlib chart generation error: {e}")
            return None

chart_service = ChartService()
