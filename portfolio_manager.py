"""
Portfolio operations and calculations.
"""

from PyQt5.QtWidgets import QTableWidgetItem, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDialogButtonBox, QPushButton, QWidget
from PyQt5.QtGui import QColor
from datetime import datetime
import csv
import os
from yfin import get_stock_info
from styles import COLOR_POSITIVE, COLOR_NEGATIVE, REMOVE_BUTTON_STYLESHEET, ALERT_BUTTON_STYLESHEET, DIALOG_STYLESHEET


class PortfolioManager:
    """Manages portfolio operations including add, remove, and display logic"""
    
    def __init__(self, user_email=None):
        self.portfolio = {}  # {symbol: {name, quantity, buy_price_per_unit, currency, buy_date}}
        self.total_invested = 0.0  # Track cumulative amount spent on purchases
        self.total_cashed_out = 0.0  # Track cumulative amount received from sales
        self.user_email = user_email
        self.ensure_portfolios_file()
        if user_email:
            self.load_portfolio()
    
    def ensure_portfolios_file(self):
        """Ensure portfolios.csv exists with proper headers"""
        portfolios_file = "portfolios.csv"
        if not os.path.exists(portfolios_file):
            with open(portfolios_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['email', 'symbol', 'name', 'quantity', 'buy_price_per_unit', 'currency', 'buy_date'])
    
    def set_user(self, user_email):
        """Set the current user and load their portfolio"""
        self.user_email = user_email
        self.portfolio = {}
        self.total_invested = 0.0
        self.total_cashed_out = 0.0
        self.load_portfolio()
    
    def load_portfolio(self):
        """Load portfolio data for current user from CSV"""
        if not self.user_email:
            return
        
        portfolios_file = "portfolios.csv"
        self.portfolio = {}
        self.total_invested = 0.0
        self.total_cashed_out = 0.0
        
        if not os.path.exists(portfolios_file):
            return
        
        with open(portfolios_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['email'].strip().lower() == self.user_email.lower():
                    symbol = row['symbol']
                    self.portfolio[symbol] = {
                        'name': row['name'],
                        'quantity': int(row['quantity']),
                        'buy_price_per_unit': float(row['buy_price_per_unit']),
                        'currency': row['currency'],
                        'buy_date': row['buy_date']
                    }
                    self.total_invested += float(row['quantity']) * float(row['buy_price_per_unit'])
    
    def save_portfolio(self):
        """Save portfolio data for current user to CSV"""
        if not self.user_email:
            return
        
        portfolios_file = "portfolios.csv"
        
        # Read all data except current user's data
        all_rows = []
        if os.path.exists(portfolios_file):
            with open(portfolios_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['email'].strip().lower() != self.user_email.lower():
                        all_rows.append(row)
        
        # Add current user's portfolio data
        for symbol, data in self.portfolio.items():
            all_rows.append({
                'email': self.user_email,
                'symbol': symbol,
                'name': data['name'],
                'quantity': data['quantity'],
                'buy_price_per_unit': data['buy_price_per_unit'],
                'currency': data['currency'],
                'buy_date': data['buy_date']
            })
        
        # Write all data back
        with open(portfolios_file, 'w', newline='') as f:
            if all_rows:
                writer = csv.DictWriter(f, fieldnames=['email', 'symbol', 'name', 'quantity', 'buy_price_per_unit', 'currency', 'buy_date'])
                writer.writeheader()
                writer.writerows(all_rows)
    
    def add_to_portfolio(self, symbol, name, quantity, price, currency):
        """Add asset to portfolio or increase existing position"""
        purchase_amount = quantity * price
        self.total_invested += purchase_amount
        
        if symbol in self.portfolio:
            # Add to existing position
            self.portfolio[symbol]['quantity'] += quantity
        else:
            # Create new position
            self.portfolio[symbol] = {
                'name': name,
                'quantity': quantity,
                'buy_price_per_unit': price,
                'currency': currency,
                'buy_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        self.save_portfolio()
    
    def remove_from_portfolio(self, symbol, quantity):
        """Remove quantity from portfolio"""
        if symbol not in self.portfolio:
            return False
        
        current_quantity = self.portfolio[symbol]['quantity']
        
        # Validate quantity
        if quantity > current_quantity:
            return False
        
        # Get current price for the symbol
        current_info = get_stock_info(symbol)
        current_price = current_info['price'] if current_info else self.portfolio[symbol]['buy_price_per_unit']
        
        # Calculate and track the sale amount
        sale_amount = quantity * current_price
        self.total_cashed_out += sale_amount
        
        if quantity == current_quantity:
            # Remove entire asset
            del self.portfolio[symbol]
        else:
            # Reduce quantity
            self.portfolio[symbol]['quantity'] -= quantity
        
        self.save_portfolio()
        return True
    
    def get_portfolio_data(self):
        """Get formatted portfolio data for display"""
        rows = []
        total_value = 0
        total_change = 0
        
        for symbol, data in self.portfolio.items():
            # Get current price
            current_info = get_stock_info(symbol)
            current_price = current_info['price'] if current_info else data['buy_price_per_unit']
            
            quantity = data['quantity']
            buy_price_total = data['buy_price_per_unit'] * quantity
            current_price_total = current_price * quantity
            gain_loss = current_price_total - buy_price_total
            
            total_value += current_price_total
            total_change += gain_loss
            
            rows.append({
                'symbol': symbol,
                'name': data['name'],
                'quantity': quantity,
                'buy_price_per_unit': data['buy_price_per_unit'],
                'buy_price_total': buy_price_total,
                'current_price': current_price,
                'current_price_total': current_price_total,
                'gain_loss': gain_loss
            })
        
        # Calculate cumulative change (including realized gains from sold assets)
        cumulative_change = (self.total_cashed_out + total_value) - self.total_invested
        
        return {
            'rows': rows,
            'total_value': total_value,
            'total_change': total_change,
            'cumulative_change': cumulative_change
        }
    
    def populate_portfolio_table(self, table, on_remove_clicked=None, on_alert_clicked=None):
        """Populate portfolio table with current data"""
        data = self.get_portfolio_data()
        rows = data['rows']
        
        table.setRowCount(len(rows))
        
        for row_idx, row_data in enumerate(rows):
            # Add cells
            table.setItem(row_idx, 0, QTableWidgetItem(row_data['symbol']))
            table.setItem(row_idx, 1, QTableWidgetItem(row_data['name']))
            table.setItem(row_idx, 2, QTableWidgetItem(str(row_data['quantity'])))
            table.setItem(row_idx, 3, QTableWidgetItem(f"{row_data['buy_price_per_unit']:.2f}"))
            table.setItem(row_idx, 4, QTableWidgetItem(f"{row_data['buy_price_total']:.2f}"))
            table.setItem(row_idx, 5, QTableWidgetItem(f"{row_data['current_price']:.2f}"))
            
            # Color current price based on gain/loss
            color = COLOR_POSITIVE if row_data['gain_loss'] >= 0 else COLOR_NEGATIVE
            total_current_item = QTableWidgetItem(f"{row_data['current_price_total']:.2f}")
            total_current_item.setForeground(QColor(color))
            table.setItem(row_idx, 6, total_current_item)
            
            # Add total change column with color
            sign = "+" if row_data['gain_loss'] >= 0 else ""
            total_change_item = QTableWidgetItem(f"{sign}{row_data['gain_loss']:.2f}")
            total_change_item.setForeground(QColor(color))
            table.setItem(row_idx, 7, total_change_item)
            
            # Add action buttons (Alert and Remove)
            if on_remove_clicked or on_alert_clicked:
                # Create container for buttons
                button_container = QWidget()
                button_layout = QHBoxLayout(button_container)
                button_layout.setContentsMargins(0, 0, 0, 0)
                button_layout.setSpacing(5)
                
                # Alert button
                alert_btn = QPushButton("ALERT")
                alert_btn.setStyleSheet(ALERT_BUTTON_STYLESHEET)
                alert_btn.setMaximumWidth(60)
                if on_alert_clicked:
                    alert_btn.clicked.connect(lambda checked, s=row_data['symbol']: on_alert_clicked(s))
                button_layout.addWidget(alert_btn)
                
                # Remove button
                remove_btn = QPushButton("REMOVE")
                remove_btn.setStyleSheet(REMOVE_BUTTON_STYLESHEET)
                remove_btn.setMaximumWidth(70)
                if on_remove_clicked:
                    remove_btn.clicked.connect(lambda checked, s=row_data['symbol']: on_remove_clicked(s))
                button_layout.addWidget(remove_btn)
                
                table.setCellWidget(row_idx, 8, button_container)
    
    def get_portfolio_summary(self):
        """Get portfolio summary text and color"""
        data = self.get_portfolio_data()
        total_value = data['total_value']
        cumulative_change = data['cumulative_change']
        
        change_color = COLOR_POSITIVE if cumulative_change >= 0 else COLOR_NEGATIVE
        summary_text = f"Total Portfolio Value: {total_value:.2f}"
        if cumulative_change >= 0:
            summary_text += f" | Total Change: +{cumulative_change:.2f}"
        else:
            summary_text += f" | Total Change: {cumulative_change:.2f}"
        
        return summary_text, change_color
    
    def get_max_removable_quantity(self, symbol):
        """Get maximum quantity that can be removed"""
        if symbol not in self.portfolio:
            return 0
        return self.portfolio[symbol]['quantity']
    
    def has_portfolio(self):
        """Check if portfolio has any items"""
        return len(self.portfolio) > 0


def create_quantity_dialog(parent, symbol, price, currency, on_confirm):
    """Create and show quantity input dialog for adding to portfolio"""
    dialog = QDialog(parent)
    dialog.setWindowTitle(f"Add {symbol} to Portfolio")
    dialog.resize(600, 300)
    dialog.setStyleSheet(DIALOG_STYLESHEET)
    
    layout = QVBoxLayout()
    
    # Symbol and current price info
    info_label = QLabel(f"{symbol} - Current Price: {price:.2f} {currency}")
    info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
    layout.addWidget(info_label)
    
    # Quantity input
    qty_layout = QHBoxLayout()
    qty_label = QLabel("Quantity:")
    qty_spinbox = QSpinBox()
    qty_spinbox.setMinimum(1)
    qty_spinbox.setMaximum(1000000)
    qty_spinbox.setValue(1)
    qty_layout.addWidget(qty_label)
    qty_layout.addWidget(qty_spinbox)
    qty_layout.addStretch()
    layout.addLayout(qty_layout)
    
    # Total cost calculation
    total_cost_label = QLabel(f"Total Cost: {price:.2f} {currency}")
    total_cost_label.setStyleSheet("font-weight: bold; color: #00ff88;")
    
    def update_total_cost():
        quantity = qty_spinbox.value()
        total = quantity * price
        total_cost_label.setText(f"Total Cost: {total:.2f} {currency}")
    
    qty_spinbox.valueChanged.connect(update_total_cost)
    layout.addWidget(total_cost_label)
    
    # Buttons
    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(lambda: (on_confirm(qty_spinbox.value()), dialog.accept()))
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)
    
    dialog.setLayout(layout)
    dialog.exec_()


def create_remove_dialog(parent, symbol, max_quantity, on_confirm):
    """Create and show quantity selection dialog for removing from portfolio"""
    dialog = QDialog(parent)
    dialog.setWindowTitle(f"Remove {symbol} from Portfolio")
    dialog.resize(600, 300)
    dialog.setStyleSheet(DIALOG_STYLESHEET)
    
    layout = QVBoxLayout()
    
    # Info label
    info_label = QLabel(f"{symbol} - Current Quantity: {max_quantity}")
    info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
    layout.addWidget(info_label)
    
    # Quantity input
    qty_layout = QHBoxLayout()
    qty_label = QLabel("Quantity to Remove:")
    remove_spinbox = QSpinBox()
    remove_spinbox.setMinimum(1)
    remove_spinbox.setMaximum(max_quantity)
    remove_spinbox.setValue(1)
    qty_layout.addWidget(qty_label)
    qty_layout.addWidget(remove_spinbox)
    qty_layout.addStretch()
    layout.addLayout(qty_layout)
    
    # Warning label
    warning_label = QLabel(f"Max you can remove: {max_quantity}")
    warning_label.setStyleSheet("font-size: 11px; color: #888eb0;")
    layout.addWidget(warning_label)
    
    # Buttons
    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(lambda: (on_confirm(remove_spinbox.value()), dialog.accept()))
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)
    
    dialog.setLayout(layout)
    dialog.exec_()
