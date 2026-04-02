# 📈 Market Pulse

A real-time desktop stock and cryptocurrency tracker built with Python and PyQt5. Track assets, manage your portfolio, set price alerts, and run LSTM-based price predictions — all from a sleek dark-themed desktop interface.

![Market Pulse](icon.png)

---

## Features

- **Live Price Tracking** — Search any stock or crypto and see real-time prices, daily change, and percentage movement, auto-refreshed every 60 seconds.
- **Interactive Candlestick Charts** — Full OHLC candlestick chart with hover tooltips and switchable time periods (1D / 1W / 1M / 1Y / MAX).
- **Portfolio Management** — Add and remove positions, track unrealized P&L, and see cumulative returns including realized gains from sold assets.
- **Price Alerts** — Set above/below price thresholds per asset; alerts are checked on every refresh cycle.
- **LSTM Price Prediction** — Train a deep learning model on 5 years of historical data and generate price forecasts at +1, +7, +30, and +365 day horizons.
- **User Accounts** — Sign up / sign in system with SHA-256 hashed passwords stored locally in CSV files.

---

## Screenshots

| Home Tab | Prediction Output |
|----------|------------------|
| Candlestick chart with live price | LSTM validation vs actual + future projections |

---

## Project Structure

```
market-pulse/
├── main.py               # App entry point & main UI (StockTrackerUI)
├── auth_manager.py       # User sign-up / sign-in with CSV persistence
├── portfolio_manager.py  # Portfolio CRUD, P&L calculations, table rendering
├── graph_manager.py      # Candlestick chart rendering via Matplotlib
├── alerts_manager.py     # Price alert storage and trigger checks
├── predict.py            # Standalone LSTM training & prediction script
├── yfin.py               # yfinance wrapper (search, price, history)
├── styles.py             # All Qt stylesheets and color constants
├── icon.png              # App window icon
├── requirements.txt
└── .gitignore
```

> **Runtime CSV files** (`users.csv`, `portfolios.csv`, `alerts.csv`) are created automatically on first run and are excluded from version control via `.gitignore`.

---

## Installation

**Requirements:** Python 3.9+

```bash
# 1. Clone the repository
git clone https://github.com/your-username/market-pulse.git
cd market-pulse

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python main.py
```

> **Note on TensorFlow:** `tensorflow` is only required if you use the Prediction tab. If you want to skip it, you can run the app without it — the Prediction tab will simply fail gracefully when triggered.

---

## Usage

### Home Tab
1. Type a stock ticker or company name (e.g. `Apple`, `BTC-USD`) into the search bar and press **SEARCH**.
2. Click a result to load the live price and candlestick chart.
3. Switch chart time periods using the period buttons (1D / 1W / 1M / 1Y / MAX).
4. Click **ADD TO PORTFOLIO** to record a position (requires sign-in).
5. Click **PREDICT** to launch the LSTM model for the selected asset.

### Portfolio Tab
- Sign up or sign in to access your portfolio.
- Each row shows symbol, quantity, buy price, current value, and unrealised P&L (green/red).
- Use **ALERT** to set a price threshold notification for any holding.
- Use **REMOVE** to sell/close a position.
- The summary bar shows total portfolio value and cumulative return (including realised gains).

### Prediction Tab
- Select an asset from the Home tab and click **PREDICT**, or type a ticker directly.
- The model trains on 5 years of daily OHLC + volume data using an LSTM architecture.
- Results are displayed as a validation chart (predicted vs actual 1-day prices) and a bar chart of future price projections.
- Training runs in a background thread so the UI stays responsive.

---

## How the Prediction Model Works

`predict.py` builds a multi-output LSTM that predicts **log returns** (not raw prices) to improve stationarity:

| Step | Detail |
|------|--------|
| Features | Close, MA50, MA200, Volume, Log Return |
| Sequence length | 100 trading days |
| Architecture | LSTM(64) → Dropout → LSTM(64) → Dropout → Dense(32) → Dense(4) |
| Loss | Huber loss |
| Outputs | Predicted log return at t+1, t+7, t+30, t+365 |
| Post-processing | Returns are converted back to price via `P_prev × exp(r)` |

Early stopping (patience=5) is used to prevent overfitting. A `MinMaxScaler` is applied per feature independently.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `PyQt5` | Desktop GUI framework |
| `yfinance` | Market data (prices, history, search) |
| `matplotlib` | Candlestick chart rendering |
| `numpy` | Numerical operations |
| `pandas` | Data manipulation |
| `tensorflow` | LSTM model training and inference |
| `scikit-learn` | Data scaling, MAE evaluation |

---

## Disclaimer

This application is intended for **educational and informational purposes only**. Price predictions generated by the LSTM model are not financial advice. Always do your own research before making any investment decisions.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
