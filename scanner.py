# scanner.py
import pandas as pd
import config
from data_fetcher import get_stock_data
from valuation import calculate_value_score
from growth import calculate_growth_score

def future_estimation(price):
    """
    Estimate future stock price in 3Y and 5Y with simple CAGR scenarios.
    Returns a dict with Moderate, Good, Worse labels.
    """
    estimates = {}
    cagr_map = {'Worse': 0.05, 'Moderate': 0.10, 'Good': 0.15}
    for label, cagr in cagr_map.items():
        fut_3y = price * (1 + cagr) ** 3
        fut_5y = price * (1 + cagr) ** 5
        estimates[label] = {'3Y': round(fut_3y,2), '5Y': round(fut_5y,2)}
    return estimates

def run_scanner():
    results = []
    print(f"Scanning {len(config.TICKERS)} stocks...\n")
    
    for ticker in config.TICKERS:
        data = get_stock_data(ticker)
        if not data or not data['price']:
            continue
        
        # Value + DCF
        v_score, dcf_val = calculate_value_score(data)
        # Growth
        g_score = calculate_growth_score(data)
        # Final weighted score
        final_score = (v_score * config.VALUE_WEIGHT) + (g_score * config.GROWTH_WEIGHT)
        final_score = max(0, min(100, final_score))  # clamp 0–100
        
        # 3Y / 5Y estimations
        estimates = future_estimation(data['price'])
        
        results.append({
            "Ticker": ticker,
            "Price": round(data['price'], 2),
            "DCF": dcf_val,
            "Value": v_score,
            "Growth": g_score,
            "Final": round(final_score, 2),
            "3Y Est (Moderate)": estimates['Moderate']['3Y'],
            "3Y Est (Good)": estimates['Good']['3Y'],
            "5Y Est (Moderate)": estimates['Moderate']['5Y'],
            "5Y Est (Good)": estimates['Good']['5Y']
        })
    
    df = pd.DataFrame(results).sort_values(by="Final", ascending=False)
    
    print("\n--- RANKED STOCK LIST WITH ESTIMATIONS ---")
    print(df.to_string(index=False))
    
    return df

if __name__ == "__main__":
    run_scanner()