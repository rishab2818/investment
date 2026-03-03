import config
from data.fetcher import get_stock_fundamentals

def evaluate_deep_value(ticker_symbol):
    """
    Evaluates a single stock against the Deep Value / R&D Moat criteria.
    Criteria:
    - Price Drop > 30% from 52w High
    - Price to Book < 1.5
    - R&D to Revenue > 10%
    """
    data = get_stock_fundamentals(ticker_symbol)
    
    if "error" in data:
        return {"ticker": ticker_symbol, "passed": False, "reason": data["error"]}
        
    passed_drop = data["price_drop_52w"] >= config.DEEP_VALUE_PRICE_DROP
    passed_pb = data["price_to_book"] <= config.DEEP_VALUE_MAX_PB
    passed_rd = data["rd_to_rev"] >= config.DEEP_VALUE_MIN_RD_REV
    
    # We might want to make this OR depending on how strict we are. Let's start strict (AND).
    passed_all = passed_drop and passed_pb and passed_rd
    
    reason = []
    if not passed_drop: reason.append(f"Insufficient Drawdown ({data['price_drop_52w']*100:.1f}%)")
    if not passed_pb: reason.append(f"High P/B ({data['price_to_book']:.2f})")
    if not passed_rd: reason.append(f"Low R&D ({data['rd_to_rev']*100:.1f}%)")
    
    return {
        "ticker": ticker_symbol,
        "name": data["name"],
        "passed": passed_all,
        "reason": ", ".join(reason) if not passed_all else "Passed all metrics.",
        "metrics": {
            "Price_Drop": data["price_drop_52w"],
            "P_B": data["price_to_book"],
            "RD_Rev": data["rd_to_rev"]
        },
        "summary": data["summary"],
        "sector": data["sector"],
        "industry": data["industry"]
    }
