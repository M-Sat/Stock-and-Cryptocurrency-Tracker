"""
Price history charting with interactive tooltips.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import FuncFormatter
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from yfin import get_price_history, get_stock_info


class GraphManager:
    """Manages price history graph rendering and interactions"""
    
    def __init__(self):
        self.graph_canvas = None
        self.graph_dates = None
        self.graph_opens = None
        self.graph_highs = None
        self.graph_lows = None
        self.graph_closes = None
        self.graph_x_positions = None
        self.graph_currency = None
        self.graph_tooltip_label = None
    
    def set_tooltip_label(self, label):
        """Set the label widget for displaying OHLC tooltip"""
        self.graph_tooltip_label = label
    
    def render_candlestick_chart(self, container_layout, symbol, period="1y"):
        """
        Fetch price history and display candlestick chart.
        Returns True if successful, False otherwise.
        """
        try:
            history_data = get_price_history(symbol, period)
            if history_data is None or history_data.empty:
                self.show_error(container_layout, "No data available")
                return False
            
            info = get_stock_info(symbol)
            currency = info.get('currency', 'USD') if info else 'USD'
            
            fig = Figure(figsize=(6, 4.5), dpi=100, facecolor='#161926')
            fig.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.12)
            
            ax = fig.add_subplot(111)
            
            dates = history_data.index
            opens = history_data['Open'].values
            highs = history_data['High'].values
            lows = history_data['Low'].values
            closes = history_data['Close'].values
            
            x_positions = np.arange(len(dates))
            candle_width = 0.6
            
            self._draw_candlesticks(ax, x_positions, opens, highs, lows, closes, candle_width)
            
            self._style_chart(ax, dates, x_positions, closes)
            
            if self.graph_canvas:
                self.graph_canvas.deleteLater()
            
            self.graph_canvas = FigureCanvas(fig)
            self.graph_canvas.setCursor(QCursor(Qt.CrossCursor))
            
            self.graph_dates = dates
            self.graph_closes = closes
            self.graph_opens = opens
            self.graph_highs = highs
            self.graph_lows = lows
            self.graph_x_positions = x_positions
            self.graph_currency = currency
            
            self.graph_canvas.mpl_connect('motion_notify_event', self.on_graph_hover)
            self.graph_canvas.mpl_connect('figure_leave_event', self.on_graph_leave)
            
            while container_layout.count() > 0:
                widget = container_layout.takeAt(0).widget()
                if widget:
                    widget.deleteLater()
            
            container_layout.addWidget(self.graph_canvas)
            self.graph_canvas.draw()
            
            return True
            
        except Exception as e:
            self.show_error(container_layout, f"Error: {str(e)}")
            return False
    
    def _draw_candlesticks(self, ax, x_positions, opens, highs, lows, closes, candle_width):
        """Draw candlestick bodies and wicks."""
        for i in range(len(x_positions)):
            open_price = opens[i]
            close_price = closes[i]
            high_price = highs[i]
            low_price = lows[i]
            
            is_up = close_price >= open_price
            body_color = '#00ff88' if is_up else '#ff4d4d'
            wick_color = '#00ff88' if is_up else '#ff4d4d'
            
            ax.plot([x_positions[i], x_positions[i]], [low_price, high_price], 
                   color=wick_color, linewidth=1.5, zorder=1)
            
            body_bottom = min(open_price, close_price)
            body_height = abs(close_price - open_price)
            
            if body_height == 0:
                ax.plot([x_positions[i] - candle_width/2, x_positions[i] + candle_width/2], 
                       [open_price, open_price], color=body_color, linewidth=2, zorder=2)
            else:
                rect = plt.Rectangle((x_positions[i] - candle_width/2, body_bottom), 
                                    candle_width, body_height,
                                    facecolor=body_color, edgecolor=body_color, 
                                    linewidth=1, zorder=2)
                ax.add_patch(rect)
    
    def _style_chart(self, ax, dates, x_positions, closes):
        """Apply professional styling to chart."""
        ax.set_facecolor('#161926')
        
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        ax.grid(True, alpha=0.12, color='#3f445e', linestyle='-', linewidth=0.5, zorder=0, axis='y')
        ax.set_axisbelow(True)
        
        ax.tick_params(colors='#888eb0', labelsize=10, length=6, width=1)
        
        ax.set_xlim(-1, len(dates))
        
        step = max(1, len(dates) // 8)
        x_ticks = np.arange(0, len(dates), step)
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([dates[int(i)].strftime('%m/%d') if i < len(dates) else '' for i in x_ticks])
        def price_formatter(x, pos):
            if x < 1:
                return f'{x:.4f}'
            elif x < 100:
                return f'{x:.2f}'
            else:
                return f'{x:.0f}'
        
        ax.yaxis.set_major_formatter(FuncFormatter(price_formatter))
        
        ax.figure.autofmt_xdate(rotation=45, ha='right')
    
    def on_graph_hover(self, event):
        """Update tooltip with OHLC values at cursor position."""
        if event.inaxes is None or not hasattr(self, 'graph_dates') or self.graph_tooltip_label is None:
            return
        
        try:
            x_pos = event.xdata
            if x_pos is None:
                return
            
            # Find closest candle index
            closest_idx = int(np.clip(np.round(x_pos), 0, len(self.graph_dates) - 1))
            
            date_str = self.graph_dates[closest_idx].strftime("%Y-%m-%d")
            open_price = self.graph_opens[closest_idx]
            high_price = self.graph_highs[closest_idx]
            low_price = self.graph_lows[closest_idx]
            close_price = self.graph_closes[closest_idx]
            
            self.graph_tooltip_label.setText(
                f"{date_str} | O: {open_price:.2f} H: {high_price:.2f} L: {low_price:.2f} C: {close_price:.2f} {self.graph_currency}"
            )
        except Exception:
            pass
    
    def on_graph_leave(self, event):
        """Handle mouse leave from graph"""
        if self.graph_tooltip_label:
            self.graph_tooltip_label.setText("")
    
    def show_error(self, container_layout, error_msg):
        """Show error message instead of graph"""
        # Clear container
        while container_layout.count() > 0:
            widget = container_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        error_label = QLabel(error_msg)
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #ff4d4d; font-size: 14px;")
        container_layout.addWidget(error_label)
    
    def clear(self):
        """Clear graph resources"""
        if self.graph_canvas:
            self.graph_canvas.deleteLater()
            self.graph_canvas = None
        
        self.graph_dates = None
        self.graph_opens = None
        self.graph_highs = None
        self.graph_lows = None
        self.graph_closes = None
        self.graph_x_positions = None
        self.graph_currency = None
