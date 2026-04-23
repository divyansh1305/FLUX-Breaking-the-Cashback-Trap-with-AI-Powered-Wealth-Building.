import yfinance as yf
import traceback
import datetime

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

def get_stock_info(symbol):
    try:
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            base_sym = symbol.split('-')[0].upper()
            if base_sym.startswith('^'): # index like ^NSEI
                yf_symbol = base_sym
            else:
                yf_symbol = base_sym + '.NS'
        else:
            yf_symbol = symbol.upper()
            
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="1d")
        
        now_utc = datetime.datetime.utcnow()
        now_ist = now_utc + datetime.timedelta(hours=5, minutes=30)
        is_weekday = now_ist.weekday() < 5
        is_open = False
        if is_weekday:
            market_start = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
            market_end = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)
            if market_start <= now_ist <= market_end:
                is_open = True
                
        status_msg = "Market is Open 🟢" if is_open else "Market is Closed 🔴 (Opens Mon-Fri, 9:15 AM)"
        
        if len(hist) > 0:
            current = hist['Close'].iloc[-1]
            return {"success": True, "current_price": round(current, 2), "market_status": status_msg, "symbol": yf_symbol}
        else:
            return {"success": False, "current_price": 0, "market_status": status_msg, "error": "Symbol not found in live ticker"}
    except Exception as e:
        print("Stock Fetch Error:", e)
        return {"success": False, "current_price": 0, "market_status": "Unknown", "error": str(e)}
def get_gold_rate():
    try:
        gold = yf.Ticker("GC=F") # Gold Futures
        hist = gold.history(period="1d")
        if len(hist) > 0:
            current = hist['Close'].iloc[-1]
            return {"success": True, "price": round(current, 2), "currency": "USD/oz", "status": "live"}
        return {"success": False, "price": 2040.50, "status": "simulated"}
    except:
        return {"success": False, "price": 2040.50, "status": "error"}
