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
        Generates a candlestick-style chart using Matplotlib for reliability.
        """
        try:
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(10, 6))
            
            df_plot = df.tail(40).reset_index()
            
            # Draw simple bars instead of complex candles for speed
            for i, row in df_plot.iterrows():
                color = '#10b981' if row['close'] >= row['open'] else '#ef4444'
                ax.vlines(i, row['low'], row['high'], color=color, linewidth=1)
                ax.vlines(i, min(row['open'], row['close']), max(row['open'], row['close']), color=color, linewidth=4)

            # 1. Fibonacci Golden Zone
            fibs = signal.get('fib_levels', {})
            if fibs:
                f618 = fibs.get('0.618')
                f786 = fibs.get('0.786')
                if f618 and f786:
                    ax.axhspan(min(f618, f786), max(f618, f786), color='yellow', alpha=0.1, label='Golden Zone')

            # 2. Entry, SL, TP Lines
            ax.axhline(signal['entry'], color='#3b82f6', linestyle='--', linewidth=1.5, label='ENTRY')
            ax.axhline(signal['stop_loss'], color='#ef4444', linestyle='--', linewidth=1.5, label='SL')
            ax.axhline(signal['take_profit_1'], color='#10b981', linestyle='--', linewidth=1.5, label='TP1')
            ax.axhline(signal['take_profit_2'], color='#059669', linestyle='--', linewidth=1.5, label='TP2')

            ax.set_title(f"{symbol} Sniper Analysis - {signal['direction']}", color='white', fontsize=14, pad=20)
            ax.set_ylabel("Price")
            ax.grid(True, alpha=0.1)
            ax.legend(loc='upper left', fontsize='small')

            # Save
            file_path = os.path.join(self.output_dir, f"{symbol}_signal.png")
            plt.savefig(file_path, bbox_inches='tight', dpi=100)
            plt.close(fig)
            
            return file_path
        except Exception as e:
            self.logger.error(f"Matplotlib chart generation error: {e}")
            return None

chart_service = ChartService()
