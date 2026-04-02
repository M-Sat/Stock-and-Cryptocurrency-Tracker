import subprocess
import sys
import os
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QPushButton, QListWidget, 
                             QLabel, QFrame, QListWidgetItem, QTabWidget, QTableWidget,
                             QDialog, QMessageBox, QTextEdit, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap

from yfin import search_symbols, get_stock_info
from styles import (MAIN_STYLESHEET, PERIOD_BUTTON_NORMAL, PERIOD_BUTTON_SELECTED,
                    DIALOG_STYLESHEET, PORTFOLIO_TABLE_STYLESHEET, REFRESH_BUTTON_STYLESHEET,
                    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, RESULTS_LIST_MAX_HEIGHT, 
                    PERIOD_BUTTON_MAX_WIDTH, COLOR_POSITIVE, COLOR_NEGATIVE)
from portfolio_manager import PortfolioManager, create_quantity_dialog, create_remove_dialog
from graph_manager import GraphManager
from auth_manager import AuthManager
from alerts_manager import AlertsManager


class PredictionWorker(QObject):
    """Runs prediction subprocess in background thread."""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    
    def run_predict(self, symbol):
        """Run predict.py subprocess and capture output."""
        try:
            process = subprocess.Popen(
                [sys.executable, 'predict.py', symbol],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                self.output_signal.emit(line.rstrip())
            
            process.wait()
            self.finished_signal.emit()
        except Exception as e:
            self.output_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit()


class StockTrackerUI(QMainWindow):
    """Main application window for the stock tracker"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Market Pulse | Real-Time Tracker")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        icon_path = 'icon.png'
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.current_symbol = None
        self.current_period = "1y"
        self.current_asset_info = None
        
        self.auth_manager = AuthManager()
        self.portfolio_manager = PortfolioManager()
        self.graph_manager = GraphManager()
        self.alerts_manager = AlertsManager()
        self.portfolio_content_widget = None
        self.portfolio_auth_widget = None
        self.portfolio_title_layout = None
        self.signout_btn = None
        
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_prices)
        self.prediction_worker = None
        self.prediction_thread = None
        
        self.apply_styles()
        self.setup_ui()
        
        # Configure graph manager tooltip
        self.graph_manager.set_tooltip_label(self.graph_tooltip)
        
        # Start the auto-refresh timer
        self.refresh_timer.start(60000)  # 60 seconds in milliseconds
        
        self.showMaximized()

    def apply_styles(self):
        """Apply main stylesheet to the application"""
        self.setStyleSheet(MAIN_STYLESHEET)

    def setup_ui(self):
        """Initialize main UI with tabs."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tabs)

        self.home_tab = QWidget()
        self.setup_home_tab()
        self.tabs.addTab(self.home_tab, "HOME")

        self.portfolio_tab = QWidget()
        self.setup_portfolio_tab()
        self.tabs.addTab(self.portfolio_tab, "PORTFOLIO")

        self.prediction_tab = QWidget()
        self.setup_prediction_tab()
        self.tabs.addTab(self.prediction_tab, "PREDICTION")

    def setup_home_tab(self):
        """Initialize home tab with search and display."""
        layout = QVBoxLayout(self.home_tab)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(25)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter stock or crypto name...")
        self.search_input.returnPressed.connect(self.run_search)
        
        self.search_btn = QPushButton("SEARCH")
        self.search_btn.clicked.connect(self.run_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        self.results_list = QListWidget()
        self.results_list.setMaximumHeight(RESULTS_LIST_MAX_HEIGHT)
        self.results_list.itemClicked.connect(self.on_item_selected)
        
        layout.addWidget(QLabel("SEARCH RESULTS"))
        layout.addWidget(self.results_list)

        self.display_card = QFrame()
        self.display_card.setObjectName("Card")
        card_layout = QHBoxLayout(self.display_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(40)
        
        left_panel = self._create_asset_info_panel()
        right_panel = self._create_graph_panel()
        
        card_layout.addWidget(left_panel, stretch=1)
        card_layout.addWidget(right_panel, stretch=1)

        layout.addWidget(self.display_card, stretch=1)

    def _create_asset_info_panel(self):
        """Create the left panel showing asset information"""
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignCenter)
        
        self.lbl_symbol = QLabel("MARKET WATCH")
        self.lbl_symbol.setObjectName("SymbolLabel")
        self.lbl_symbol.setAlignment(Qt.AlignCenter)
        
        self.lbl_name = QLabel("Select an asset to view details")
        self.lbl_name.setObjectName("NameLabel")
        self.lbl_name.setAlignment(Qt.AlignCenter)
        
        self.lbl_price = QLabel("—")
        self.lbl_price.setObjectName("PriceLabel")
        self.lbl_price.setAlignment(Qt.AlignCenter)
        
        self.lbl_change = QLabel("")
        self.lbl_change.setAlignment(Qt.AlignCenter)

        left_layout.addStretch(1)
        left_layout.addWidget(self.lbl_symbol)
        left_layout.addWidget(self.lbl_name)
        left_layout.addSpacing(40)
        left_layout.addWidget(self.lbl_price)
        left_layout.addWidget(self.lbl_change)
        left_layout.addSpacing(30)
        
        self.add_portfolio_btn = QPushButton("ADD TO PORTFOLIO")
        self.add_portfolio_btn.setStyleSheet("""
            QPushButton {
                background-color: #26c281; color: white;
                border-radius: 8px; padding: 12px 25px;
                font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #1da361; }
        """)
        self.add_portfolio_btn.clicked.connect(self.show_quantity_dialog)
        left_layout.addWidget(self.add_portfolio_btn)
        
        self.predict_btn = QPushButton("PREDICT")
        self.predict_btn.setStyleSheet("""
            QPushButton {
                background-color: #26c281; color: white;
                border-radius: 8px; padding: 12px 25px;
                font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #1da361; }
        """)
        self.predict_btn.clicked.connect(self.on_predict_clicked)
        left_layout.addWidget(self.predict_btn)
        left_layout.addStretch(1)
        
        return left_panel

    def _create_graph_panel(self):
        """Initialize graph display panel."""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        period_layout = QHBoxLayout()
        period_layout.setContentsMargins(0, 0, 0, 0)
        period_layout.setSpacing(6)
        
        self.period_buttons = {}
        periods = [("1D", "1d"), ("1W", "1wk"), ("1M", "1mo"), ("1Y", "1y"), ("ALL", "max")]
        
        for label, period in periods:
            btn = QPushButton(label)
            btn.setMaximumWidth(PERIOD_BUTTON_MAX_WIDTH)
            btn.setStyleSheet(PERIOD_BUTTON_NORMAL)
            btn.clicked.connect(lambda checked, p=period: self.switch_period(p))
            period_layout.addWidget(btn)
            self.period_buttons[period] = btn
        
        self.period_buttons["1y"].setStyleSheet(PERIOD_BUTTON_SELECTED)
        
        period_layout.addStretch()
        right_layout.addLayout(period_layout)
        
        self.graph_tooltip = QLabel("")
        self.graph_tooltip.setAlignment(Qt.AlignCenter)
        self.graph_tooltip.setStyleSheet("color: #007bff; font-size: 12px; font-weight: bold;")
        right_layout.addWidget(self.graph_tooltip)
        
        self.graph_container = QWidget()
        self.graph_container_layout = QVBoxLayout(self.graph_container)
        self.graph_container_layout.setContentsMargins(0, 0, 0, 0)
        graph_label = QLabel("Select an asset to view price history")
        graph_label.setAlignment(Qt.AlignCenter)
        graph_label.setStyleSheet("color: #888eb0; font-size: 14px;")
        self.graph_container_layout.addWidget(graph_label)
        
        right_layout.addWidget(self.graph_container, stretch=1)
        
        ohlc_label = QLabel("O: Open | H: High | L: Low | C: Close")
        ohlc_label.setAlignment(Qt.AlignCenter)
        ohlc_label.setStyleSheet("color: #667a8f; font-size: 10px; margin-top: 8px;")
        right_layout.addWidget(ohlc_label)
        
        return right_panel

    def setup_portfolio_tab(self):
        """Initialize portfolio tab."""
        outer_layout = QVBoxLayout(self.portfolio_tab)
        outer_layout.setContentsMargins(0, 20, 0, 20)
        outer_layout.setSpacing(15)
        
        self.portfolio_title_layout = QHBoxLayout()
        title = QLabel("YOUR PORTFOLIO")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        self.portfolio_title_layout.addWidget(title)
        self.portfolio_title_layout.addStretch()
        
        refresh_btn = QPushButton("REFRESH PRICES")
        refresh_btn.setMaximumWidth(150)
        refresh_btn.clicked.connect(self.manual_refresh_prices)
        refresh_btn.setStyleSheet(REFRESH_BUTTON_STYLESHEET)
        self.portfolio_title_layout.addWidget(refresh_btn)
        
        self.signout_btn = QPushButton("SIGN OUT")
        self.signout_btn.setMaximumWidth(100)
        self.signout_btn.clicked.connect(self.handle_signout)
        self.signout_btn.setStyleSheet(REFRESH_BUTTON_STYLESHEET)
        self.signout_btn.setVisible(False)
        self.portfolio_title_layout.addWidget(self.signout_btn)
        
        outer_layout.addLayout(self.portfolio_title_layout)
        
        self.portfolio_content_stack = QWidget()
        stack_layout = QVBoxLayout(self.portfolio_content_stack)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        
        self.portfolio_content_widget = self._create_portfolio_content()
        stack_layout.addWidget(self.portfolio_content_widget)
        
        self.portfolio_auth_widget = self._create_portfolio_auth_screen()
        stack_layout.addWidget(self.portfolio_auth_widget)
        
        outer_layout.addWidget(self.portfolio_content_stack, stretch=1)
        
        self.update_portfolio_view()

    def setup_prediction_tab(self):
        """Initialize prediction tab."""
        layout = QVBoxLayout(self.prediction_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("PREDICTION")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)
        
        self.prediction_container = QWidget()
        container_layout = QVBoxLayout(self.prediction_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        self.prediction_output = QTextEdit()
        self.prediction_output.setReadOnly(True)
        self.prediction_output.setStyleSheet("""
            QTextEdit {
                background-color: #0b0e14;
                color: #00ff88;
                border: 1px solid #667a8f;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        container_layout.addWidget(self.prediction_output)
        
        self.prediction_image_label = QLabel()
        self.prediction_image_label.setAlignment(Qt.AlignCenter)
        self.prediction_image_label.setScaledContents(False)
        self.prediction_image_label.setStyleSheet("""
            QLabel {
                background-color: #0b0e14;
                border: 1px solid #667a8f;
                border-radius: 4px;
                padding: 0px;
            }
        """)
        self.prediction_image_label.setVisible(False)
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.prediction_image_label)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #0b0e14;
                border: 1px solid #667a8f;
                border-radius: 4px;
            }
            QScrollBar {
                background-color: #0b0e14;
                border: none;
            }
            QScrollBar:vertical {
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #667a8f;
                border-radius: 6px;
            }
        """)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVisible(False)
        self.prediction_scroll_area = scroll_area
        
        container_layout.addWidget(scroll_area)
        
        layout.addWidget(self.prediction_container, stretch=1)
        
        self.prediction_status = QLabel("Ready. Select a stock and click PREDICT.")
        self.prediction_status.setAlignment(Qt.AlignCenter)
        self.prediction_status.setStyleSheet("color: #888eb0; font-size: 12px;")
        layout.addWidget(self.prediction_status)

    def on_predict_clicked(self):
        """Run prediction in background thread."""
        if self.current_symbol is None:
            return
        
        self.tabs.setCurrentIndex(2)
        
        self.prediction_output.clear()
        self.prediction_image_label.setPixmap(QPixmap())
        self.prediction_output.setVisible(True)
        self.prediction_scroll_area.setVisible(False)
        self.prediction_status.setText(f"Running prediction for {self.current_symbol}...")
        self.prediction_status.setStyleSheet("color: #007bff; font-size: 12px;")
        
        self.prediction_worker = PredictionWorker()
        self.prediction_thread = threading.Thread(target=self.prediction_worker.run_predict, args=(self.current_symbol,))
        
        self.prediction_worker.output_signal.connect(self.on_prediction_output)
        self.prediction_worker.finished_signal.connect(self.on_prediction_finished)
        
        self.prediction_thread.daemon = True
        self.prediction_thread.start()
    
    def on_prediction_output(self, line):
        """Handle prediction output from worker thread."""
        # Check if plot has been saved
        if "[PLOT_SAVED]" in line:
            # Load and display the prediction plot image
            self.display_prediction_image()
        else:
            # Display text output
            self.prediction_output.append(line)
            # Auto-scroll to bottom
            self.prediction_output.verticalScrollBar().setValue(
                self.prediction_output.verticalScrollBar().maximum()
            )
    
    def display_prediction_image(self):
        """Load and display prediction plot image."""
        try:
            pixmap = QPixmap('prediction_plot.png')
            if not pixmap.isNull():
                # Calculate available space
                available_width = self.prediction_container.width() - 40  # Account for margins and borders
                available_height = self.prediction_container.height() - 40
                
                # Scale to fill the available space while maintaining aspect ratio
                if available_width > 100 and available_height > 100:
                    # Scale by width first
                    scaled_pixmap = pixmap.scaledToWidth(
                        available_width,
                        Qt.SmoothTransformation
                    )
                    # If height is too large, scale by height instead
                    if scaled_pixmap.height() > available_height:
                        scaled_pixmap = pixmap.scaledToHeight(
                            available_height,
                            Qt.SmoothTransformation
                        )
                else:
                    scaled_pixmap = pixmap.scaledToWidth(800, Qt.SmoothTransformation)
                
                self.prediction_image_label.setPixmap(scaled_pixmap)
                
                # Hide text, show image and scroll area
                self.prediction_output.setVisible(False)
                self.prediction_scroll_area.setVisible(True)
        except Exception as e:
            self.prediction_output.append(f"\nError loading image: {str(e)}")
    
    def on_prediction_finished(self):
        """Update UI when prediction completes."""
        self.prediction_status.setText("Prediction complete!")
        self.prediction_status.setStyleSheet("color: #26c281; font-size: 12px;")
    def _create_portfolio_content(self):
        """Create portfolio display (table and summary)."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(9)
        self.portfolio_table.setHorizontalHeaderLabels(
            ["Symbol", "Name", "Quantity", "Buy Price/Unit", "Total Bought", "Current Price/Unit", "Total Current", "Total Change", "Action"]
        )
        self.portfolio_table.setStyleSheet(PORTFOLIO_TABLE_STYLESHEET)
        self.portfolio_table.verticalHeader().setVisible(False)
        for i in range(9):
            self.portfolio_table.horizontalHeader().setSectionResizeMode(i, 1)
        
        layout.addWidget(self.portfolio_table)
        layout.addStretch(1)
        
        self.portfolio_summary = QLabel("Total Portfolio Value: —")
        self.portfolio_summary.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ff88;")
        layout.addWidget(self.portfolio_summary)
        
        return content

    def _create_portfolio_auth_screen(self):
        """Create portfolio authentication screen."""
        auth_widget = QWidget()
        layout = QVBoxLayout(auth_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        title = QLabel("PORTFOLIO")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #ffffff;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(40)
        
        signup_btn = QPushButton("SIGN UP")
        signup_btn.setMaximumWidth(200)
        signup_btn.setMinimumHeight(50)
        signup_btn.clicked.connect(self.show_signup_dialog)
        signup_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        signin_btn = QPushButton("SIGN IN")
        signin_btn.setMaximumWidth(200)
        signin_btn.setMinimumHeight(50)
        signin_btn.clicked.connect(self.show_signin_dialog)
        signin_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(signup_btn)
        button_layout.addSpacing(20)
        button_layout.addWidget(signin_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addSpacing(40)
        
        return auth_widget

    def show_signup_dialog(self):
        """Show signup dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Sign Up")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(DIALOG_STYLESHEET)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel("Create Account")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addSpacing(15)
        
        # Name field
        name_label = QLabel("Full Name:")
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter your full name")
        layout.addWidget(name_label)
        layout.addWidget(name_input)
        
        layout.addSpacing(10)
        
        # Email field
        email_label = QLabel("Email Address:")
        email_input = QLineEdit()
        email_input.setPlaceholderText("Enter your email")
        layout.addWidget(email_label)
        layout.addWidget(email_input)
        
        layout.addSpacing(10)
        
        # Password field
        password_label = QLabel("Password:")
        password_input = QLineEdit()
        password_input.setPlaceholderText("Create a password (min 4 characters)")
        password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(password_label)
        layout.addWidget(password_input)
        
        layout.addSpacing(20)
        
        # Message label
        message_label = QLabel("")
        message_label.setStyleSheet("color: #ff4444; font-size: 11px;")
        layout.addWidget(message_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        def on_signup():
            name = name_input.text().strip()
            email = email_input.text().strip()
            password = password_input.text().strip()
            
            success, message = self.auth_manager.sign_up(name, email, password)
            
            if success:
                self.portfolio_manager.set_user(email)
                self.update_portfolio_view()
                dialog.accept()
            else:
                message_label.setText(message)
        
        signup_btn = QPushButton("SIGN UP")
        signup_btn.clicked.connect(on_signup)
        cancel_btn = QPushButton("CANCEL")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(signup_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def show_signin_dialog(self):
        """Show signin dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Sign In")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(DIALOG_STYLESHEET)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel("Sign In")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addSpacing(15)
        
        # Email field
        email_label = QLabel("Email Address:")
        email_input = QLineEdit()
        email_input.setPlaceholderText("Enter your email")
        layout.addWidget(email_label)
        layout.addWidget(email_input)
        
        layout.addSpacing(10)
        
        # Password field
        password_label = QLabel("Password:")
        password_input = QLineEdit()
        password_input.setPlaceholderText("Enter your password")
        password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(password_label)
        layout.addWidget(password_input)
        
        layout.addSpacing(20)
        
        # Message label
        message_label = QLabel("")
        message_label.setStyleSheet("color: #ff4444; font-size: 11px;")
        layout.addWidget(message_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        def on_signin():
            email = email_input.text().strip()
            password = password_input.text().strip()
            
            success, message, user_name = self.auth_manager.sign_in(email, password)
            
            if success:
                self.portfolio_manager.set_user(email)
                self.update_portfolio_view()
                dialog.accept()
            else:
                message_label.setText(message)
        
        signin_btn = QPushButton("SIGN IN")
        signin_btn.clicked.connect(on_signin)
        cancel_btn = QPushButton("CANCEL")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(signin_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def handle_signout(self):
        """Handle sign out"""
        self.auth_manager.sign_out()
        self.portfolio_manager = PortfolioManager()
        self.update_portfolio_view()

    def update_portfolio_view(self):
        """Update portfolio tab to show auth or content based on sign-in status"""
        if self.auth_manager.is_signed_in():
            # User is signed in, show portfolio content
            self.portfolio_content_widget.setVisible(True)
            self.portfolio_auth_widget.setVisible(False)
            self.signout_btn.setVisible(True)
            self.refresh_portfolio_display()
        else:
            # User is not signed in, show auth screen
            self.portfolio_content_widget.setVisible(False)
            self.portfolio_auth_widget.setVisible(True)
            self.signout_btn.setVisible(False)

    def on_tab_changed(self, index):
        """Update portfolio view when switching tabs."""
        if index == 1:  # Portfolio tab
            self.update_portfolio_view()

    def run_search(self):
        """Search for stocks and cryptocurrencies."""
        query = self.search_input.text().strip()
        if not query:
            return
        
        self.results_list.clear()
        matches = search_symbols(query)
        
        for symbol, name, qtype in matches[:10]:
            item = QListWidgetItem(f"{qtype}: {name} ({symbol})")
            item.setData(Qt.UserRole, (symbol, name))
            self.results_list.addItem(item)

    def on_item_selected(self, item):
        """Handle selection of search result"""
        symbol, name = item.data(Qt.UserRole)
        self.current_symbol = symbol
        self.current_period = "1y"
        info = get_stock_info(symbol)
        
        if info:
            self.update_display(symbol, name, info)

    def update_display(self, symbol, name, info):
        """Update display with selected asset information"""
        self.lbl_symbol.setText(symbol.upper())
        self.lbl_name.setText(name)
        
        # Store current asset info for portfolio operations
        self.current_asset_info = {**info, 'name': name}
        
        price_str = f"{info['price']:.6f}" if info['price'] < 1 else f"{info['price']:.2f}"
        self.lbl_price.setText(f"{price_str} {info['currency']}")
        
        if info['change'] is not None:
            color = COLOR_POSITIVE if info['change'] >= 0 else COLOR_NEGATIVE
            sign = "+" if info['change'] >= 0 else ""
            self.lbl_change.setText(f"{sign}{info['change']:.2f} ({sign}{info['change_percent']:.2f}%)")
            self.lbl_change.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 500;")
        
        # Display price history graph
        self.display_price_history(symbol)

    def switch_period(self, period):
        """Change graph period."""
        if self.current_symbol is None:
            return
        
        self.current_period = period
        
        for p, btn in self.period_buttons.items():
            btn.setStyleSheet(PERIOD_BUTTON_SELECTED if p == period else PERIOD_BUTTON_NORMAL)
        
        self.display_price_history(self.current_symbol, period)

    def display_price_history(self, symbol, period="1y"):
        """Render price history candlestick chart."""
        self.graph_manager.render_candlestick_chart(
            self.graph_container_layout, symbol, period
        )

    def refresh_portfolio_display(self):
        """Update portfolio table and summary."""
        self.portfolio_manager.populate_portfolio_table(self.portfolio_table, self.show_remove_dialog, self.show_alert_dialog)
        summary_text, color = self.portfolio_manager.get_portfolio_summary()
        self.portfolio_summary.setText(summary_text)
        self.portfolio_summary.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")

    def show_alert_dialog(self, symbol):
        """Show dialog to set price alerts for an asset"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Set Price Alert for {symbol}")
        dialog.setMinimumWidth(500)
        dialog.setStyleSheet(DIALOG_STYLESHEET)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel(f"Price Alerts for {symbol}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addSpacing(15)
        
        # Get existing alert if any
        current_alert = self.alerts_manager.get_alert(self.auth_manager.get_current_user(), symbol)
        
        # Alert below price
        check_below = QLineEdit() if current_alert and current_alert.get('check_below') else None
        below_layout = QHBoxLayout()
        below_checkbox = QLineEdit()
        below_checkbox.setPlaceholderText("$")
        below_checkbox.setMaximumWidth(100)
        if current_alert and current_alert.get('check_below'):
            below_checkbox.setText(str(current_alert.get('below_price', '')))
        below_label = QLabel("Alert me when this asset falls below:")
        below_layout.addWidget(below_label)
        below_layout.addWidget(below_checkbox)
        below_layout.addStretch()
        layout.addLayout(below_layout)
        
        layout.addSpacing(10)
        
        # Alert above price
        above_layout = QHBoxLayout()
        above_checkbox = QLineEdit()
        above_checkbox.setPlaceholderText("$")
        above_checkbox.setMaximumWidth(100)
        if current_alert and current_alert.get('check_above'):
            above_checkbox.setText(str(current_alert.get('above_price', '')))
        above_label = QLabel("Alert me when this asset rises above:")
        above_layout.addWidget(above_label)
        above_layout.addWidget(above_checkbox)
        above_layout.addStretch()
        layout.addLayout(above_layout)
        
        layout.addSpacing(20)
        
        # Message label
        message_label = QLabel("")
        message_label.setStyleSheet("color: #ff4444; font-size: 11px;")
        layout.addWidget(message_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        def on_confirm():
            below_price_text = below_checkbox.text().strip()
            above_price_text = above_checkbox.text().strip()
            
            # Validation
            if not below_price_text and not above_price_text:
                message_label.setText("Please set at least one price alert")
                return
            
            try:
                below_price = float(below_price_text) if below_price_text else None
                above_price = float(above_price_text) if above_price_text else None
            except ValueError:
                message_label.setText("Please enter valid prices")
                return
            
            # Save alert
            self.alerts_manager.save_alert(
                self.auth_manager.get_current_user(),
                symbol,
                below_price,
                above_price,
                bool(below_price_text),
                bool(above_price_text)
            )
            
            dialog.accept()
        
        save_btn = QPushButton("SAVE ALERT")
        save_btn.clicked.connect(on_confirm)
        delete_btn = QPushButton("DELETE ALERT")
        delete_btn.clicked.connect(lambda: [
            self.alerts_manager.delete_alert(self.auth_manager.get_current_user(), symbol),
            dialog.accept()
        ])
        cancel_btn = QPushButton("CANCEL")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def show_quantity_dialog(self):
        """Show dialog to select quantity for adding to portfolio"""
        if self.current_symbol is None or self.current_asset_info is None:
            return
        
        if not self.auth_manager.is_signed_in():
            QMessageBox.warning(self, "Not Signed In", "Please sign in to your portfolio first!")
            self.tabs.setCurrentIndex(1)
            return
        
        def on_confirm(quantity):
            self.add_to_portfolio(quantity)
        
        create_quantity_dialog(
            self,
            self.current_symbol,
            self.current_asset_info['price'],
            self.current_asset_info['currency'],
            on_confirm
        )

    def add_to_portfolio(self, quantity):
        """Add selected asset to portfolio"""
        self.portfolio_manager.add_to_portfolio(
            self.current_symbol,
            self.current_asset_info['name'],
            quantity,
            self.current_asset_info['price'],
            self.current_asset_info['currency']
        )
        
        # Refresh portfolio display
        self.refresh_portfolio_display()
        
        # Switch to portfolio tab
        self.tabs.setCurrentIndex(1)

    def show_remove_dialog(self, symbol):
        """Display dialog to remove assets from portfolio."""
        max_quantity = self.portfolio_manager.get_max_removable_quantity(symbol)
        if max_quantity == 0:
            return
        
        def on_confirm(quantity):
            self.remove_from_portfolio(symbol, quantity)
        
        create_remove_dialog(self, symbol, max_quantity, on_confirm)

    def remove_from_portfolio(self, symbol, quantity):
        """Remove assets from portfolio."""
        success = self.portfolio_manager.remove_from_portfolio(symbol, quantity)
        if success:
            self.refresh_portfolio_display()

    def auto_refresh_prices(self):
        """Refresh prices periodically."""
        # Refresh currently viewed asset price
        if self.current_symbol and self.current_asset_info:
            info = get_stock_info(self.current_symbol)
            if info:
                self.current_asset_info = {**info, 'name': self.current_asset_info['name']}
                price_str = f"{info['price']:.6f}" if info['price'] < 1 else f"{info['price']:.2f}"
                self.lbl_price.setText(f"{price_str} {info['currency']}")
                
                if info['change'] is not None:
                    color = COLOR_POSITIVE if info['change'] >= 0 else COLOR_NEGATIVE
                    sign = "+" if info['change'] >= 0 else ""
                    self.lbl_change.setText(f"{sign}{info['change']:.2f} ({sign}{info['change_percent']:.2f}%)")
                    self.lbl_change.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 500;")
        
        # Refresh portfolio items if signed in
        if self.auth_manager.is_signed_in() and self.portfolio_manager.has_portfolio():
            self.refresh_portfolio_display()

    def manual_refresh_prices(self):
        """Refresh all prices immediately."""
        # Refresh currently viewed asset price
        if self.current_symbol and self.current_asset_info:
            info = get_stock_info(self.current_symbol)
            if info:
                self.current_asset_info = {**info, 'name': self.current_asset_info['name']}
                price_str = f"{info['price']:.6f}" if info['price'] < 1 else f"{info['price']:.2f}"
                self.lbl_price.setText(f"{price_str} {info['currency']}")
                
                if info['change'] is not None:
                    color = COLOR_POSITIVE if info['change'] >= 0 else COLOR_NEGATIVE
                    sign = "+" if info['change'] >= 0 else ""
                    self.lbl_change.setText(f"{sign}{info['change']:.2f} ({sign}{info['change_percent']:.2f}%)")
                    self.lbl_change.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 500;")
        
        # Refresh portfolio items if signed in
        if self.auth_manager.is_signed_in() and self.portfolio_manager.has_portfolio():
            self.refresh_portfolio_display()



def main():
    """Start the application."""
    app = QApplication(sys.argv)
    window = StockTrackerUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
