"""
Price alerts management for tracked assets.
"""

import csv
import os
from yfin import get_stock_info


class AlertsManager:
    """Manages price alerts for user assets"""
    
    def __init__(self):
        self.alerts_file = "alerts.csv"
        self.ensure_alerts_file()
    
    def ensure_alerts_file(self):
        """Ensure alerts.csv exists with proper headers"""
        if not os.path.exists(self.alerts_file):
            with open(self.alerts_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['email', 'symbol', 'below_price', 'above_price', 'check_below', 'check_above'])
    
    def save_alert(self, user_email, symbol, below_price=None, above_price=None, check_below=False, check_above=False):
        """
        Save or update alert for a symbol
        Returns: (success: bool, message: str)
        """
        user_email = user_email.lower() if user_email else None
        
        # Validate inputs
        if not user_email or not symbol:
            return False, "Invalid user or symbol"
        
        if not check_below and not check_above:
            return False, "Please select at least one alert option"
        
        # Read existing alerts
        all_rows = []
        alert_found = False
        
        if os.path.exists(self.alerts_file):
            with open(self.alerts_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['email'].lower() == user_email and row['symbol'] == symbol:
                        alert_found = True
                        # Update existing alert
                        row['below_price'] = below_price if below_price is not None else row.get('below_price', '')
                        row['above_price'] = above_price if above_price is not None else row.get('above_price', '')
                        row['check_below'] = str(check_below)
                        row['check_above'] = str(check_above)
                    all_rows.append(row)
        
        # If alert not found, create new one
        if not alert_found:
            all_rows.append({
                'email': user_email,
                'symbol': symbol,
                'below_price': below_price if below_price is not None else '',
                'above_price': above_price if above_price is not None else '',
                'check_below': str(check_below),
                'check_above': str(check_above)
            })
        
        # Write all alerts back
        with open(self.alerts_file, 'w', newline='') as f:
            if all_rows:
                writer = csv.DictWriter(f, fieldnames=['email', 'symbol', 'below_price', 'above_price', 'check_below', 'check_above'])
                writer.writeheader()
                writer.writerows(all_rows)
        
        return True, "Alert saved successfully!"
    
    def get_alert(self, user_email, symbol):
        """
        Get alert settings for a specific symbol
        Returns: (below_price, above_price, check_below, check_above) or None if not found
        """
        user_email = user_email.lower() if user_email else None
        
        if not os.path.exists(self.alerts_file):
            return None
        
        with open(self.alerts_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['email'].lower() == user_email and row['symbol'] == symbol:
                    return {
                        'below_price': float(row['below_price']) if row['below_price'] else None,
                        'above_price': float(row['above_price']) if row['above_price'] else None,
                        'check_below': row['check_below'].lower() == 'true',
                        'check_above': row['check_above'].lower() == 'true'
                    }
        
        return None
    
    def delete_alert(self, user_email, symbol):
        """Delete alert for a symbol"""
        user_email = user_email.lower() if user_email else None
        all_rows = []
        
        if not os.path.exists(self.alerts_file):
            return
        
        with open(self.alerts_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not (row['email'].lower() == user_email and row['symbol'] == symbol):
                    all_rows.append(row)
        
        with open(self.alerts_file, 'w', newline='') as f:
            if all_rows:
                writer = csv.DictWriter(f, fieldnames=['email', 'symbol', 'below_price', 'above_price', 'check_below', 'check_above'])
                writer.writeheader()
                writer.writerows(all_rows)
    
    def check_alerts(self, user_email):
        """
        Check if any alerts should trigger for the user
        Returns: list of triggered alerts with details
        """
        user_email = user_email.lower() if user_email else None
        triggered_alerts = []
        
        if not os.path.exists(self.alerts_file):
            return triggered_alerts
        
        with open(self.alerts_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['email'].lower() == user_email:
                    symbol = row['symbol']
                    check_below = row['check_below'].lower() == 'true'
                    check_above = row['check_above'].lower() == 'true'
                    below_price = float(row['below_price']) if row['below_price'] else None
                    above_price = float(row['above_price']) if row['above_price'] else None
                    
                    # Get current price
                    info = get_stock_info(symbol)
                    if not info:
                        continue
                    
                    current_price = info['price']
                    
                    # Check conditions
                    if check_below and below_price is not None and current_price <= below_price:
                        triggered_alerts.append({
                            'symbol': symbol,
                            'type': 'below',
                            'target_price': below_price,
                            'current_price': current_price,
                            'message': f"{symbol} has fallen to your desired price of ${below_price:.2f}"
                        })
                    
                    if check_above and above_price is not None and current_price >= above_price:
                        triggered_alerts.append({
                            'symbol': symbol,
                            'type': 'above',
                            'target_price': above_price,
                            'current_price': current_price,
                            'message': f"{symbol} has risen to your desired price of ${above_price:.2f}"
                        })
        
        return triggered_alerts
    
    def get_user_alerts(self, user_email):
        """Get all alerts for a user"""
        user_email = user_email.lower() if user_email else None
        alerts = {}
        
        if not os.path.exists(self.alerts_file):
            return alerts
        
        with open(self.alerts_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['email'].lower() == user_email:
                    symbol = row['symbol']
                    alerts[symbol] = {
                        'below_price': float(row['below_price']) if row['below_price'] else None,
                        'above_price': float(row['above_price']) if row['above_price'] else None,
                        'check_below': row['check_below'].lower() == 'true',
                        'check_above': row['check_above'].lower() == 'true'
                    }
        
        return alerts
