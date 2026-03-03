import config
from data.fetcher import get_stock_fundamentals

def evaluate_compounder(ticker_symbol):
    """
    Evaluates a single stock against the Compounder Strategy criteria.
    Criteria:
    - ROIC > 15%
    - FCF CAGR > 8%
    - Debt/Equity < 1.0
    """
    data = get_stock_fundamentals(ticker_symbol)
    
    if "error" in data:
        return {"ticker": ticker_symbol, "passed": False, "reason": data["error"]}
        
    passed_roic = data["roic"] >= config.COMPOUNDER_MIN_ROIC
    passed_fcf = data["fcf_cagr"] >= config.COMPOUNDER_MIN_FCF_CAGR
    passed_debt = data["debt_to_equity"] <= config.COMPOUNDER_MAX_DEBT_EQ
    
    passed_all = passed_roic and passed_fcf and passed_debt
    
    reason = []
    if not passed_roic: reason.append(f"Low ROIC ({data['roic']*100:.1f}%)")
    if not passed_fcf: reason.append(f"Low FCF Growth ({data['fcf_cagr']*100:.1f}%)")
    if not passed_debt: reason.append(f"High Debt/Eq ({data['debt_to_equity']:.2f})")
    
    return {
        "ticker": ticker_symbol,
        "name": data["name"],
        "passed": passed_all,
        "reason": ", ".join(reason) if not passed_all else "Passed all metrics.",
        "metrics": {
            "ROIC": data["roic"],
            "FCF_CAGR": data["fcf_cagr"],
            "Debt_Eq": data["debt_to_equity"]
        },
        "summary": data["summary"],
        "sector": data["sector"],
        "industry": data["industry"]
    }
