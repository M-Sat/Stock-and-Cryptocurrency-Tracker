import yfinance as yf
from datetime import datetime, timedelta

def search_symbols(query):
    search = yf.Search(query)
    matches = []
    for r in search.quotes:
        symbol = r.get("symbol")
        name = r.get("shortname") or r.get("longname")
        qtype = r.get("quoteType")
        if symbol and name and qtype in ("EQUITY", "CRYPTOCURRENCY") and not symbol.endswith("=F"):
            matches.append((symbol, name, qtype))
    return matches

def get_stock_info(symbol):
    try:
        info = yf.Ticker(symbol).info
        price = info.get("regularMarketPrice")
        if price is not None:
            return {
                "price": price,
                "currency": info.get("currency", "USD"),
                "change": info.get("regularMarketChange"),
                "change_percent": info.get("regularMarketChangePercent"),
            }
    except:
        pass
    return None

def get_price_history(symbol, period="1y"):
    """Fetch historical price data. Periods: 1d, 1wk, 1mo, 1y, max."""
    try:
        ticker = yf.Ticker(symbol)
        end_date = datetime.now()
        
        period_config = {
            "1d": {"days": 1, "interval": "60m"},
            "1wk": {"days": 7, "interval": "1d"},
            "1mo": {"days": 30, "interval": "1d"},
            "1y": {"days": 365, "interval": "1d"},
            "max": {"days": None, "interval": "1wk"}
        }
        
        config = period_config.get(period, period_config["1y"])
        
        if config["days"] is None:
            history = ticker.history(period="max", interval=config["interval"])
        else:
            start_date = end_date - timedelta(days=config["days"])
            history = ticker.history(start=start_date, end=end_date, interval=config["interval"])
        
        if history.empty:
            return None
        return history
    except:
        return None