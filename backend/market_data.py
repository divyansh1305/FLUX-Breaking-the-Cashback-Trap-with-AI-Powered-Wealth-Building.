import yfinance as yf
import traceback

def get_nifty_data():
    """
    Fetch REAL market data for NIFTY 50 using yfinance.
    Returns the current price and daily percentage change.
    Gracefully falls back to mock data if no internet.
    """
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="2d")
        if len(hist) >= 2:
            prev_close = hist['Close'].iloc[0]
            current = hist['Close'].iloc[1]
            pct_change = ((current - prev_close) / prev_close) * 100
            
            return {
                "current_price": round(current, 2),
                "change_pct": round(pct_change, 2),
                "status": "live"
            }
        else:
            # Fallback if market data is strange
            return {"current_price": 22350.50, "change_pct": 1.2, "status": "simulated"}
    except Exception as e:
        print("Market Data Error:", e)
        return {"current_price": 22350.50, "change_pct": 1.2, "status": "simulated_error"}
