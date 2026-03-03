import pandas as pd
import numpy as np
from data.fetcher import get_historical_prices

def run_portfolio_backtest(tickers, original_weights, optimized_weights, period="5y"):
    """
    Simulates the historical performance of two portfolios (original vs optimized).
    Returns a unified dataframe of cumulative returns for plotting.
    
    Args:
        tickers (list): List of ticker symbols.
        original_weights (dict): Ticker -> Weight (Original, usually what user inputs).
        optimized_weights (dict): Ticker -> Weight (Proposed by AI/Optimizer).
        period (str): Historical period to simulate (e.g., "1y", "5y").
        
    Returns:
        dict: containing dates and cumulative return series, plus summary metrics.
    """
    pricing_data = {}
    valid_tickers = []
    
    for t in tickers:
        hist = get_historical_prices(t, period=period)
        if hist is not None and not hist.empty and "Close" in hist.columns:
            pricing_data[t] = hist["Close"]
            valid_tickers.append(t)
            
    if not pricing_data:
        return {"error": "Could not fetch historical data for any of the provided tickers."}
        
    df = pd.DataFrame(pricing_data).ffill().dropna()
    
    if df.empty:
        return {"error": "No overlapping historical data found for the portfolio."}
        
    # Calculate daily simple returns
    returns_df = df.pct_change().dropna()
    dates = returns_df.index.strftime('%Y-%m-%d').tolist()
    
    # Ensure weights are aligned and normalized for valid tickers only
    orig_sum = sum(original_weights.get(t, 0) for t in valid_tickers)
    opt_sum = sum(optimized_weights.get(t, 0) for t in valid_tickers)
    
    if orig_sum == 0 or opt_sum == 0:
        return {"error": "Invalid weights provided for the backtest."}
        
    orig_w_array = np.array([original_weights.get(t, 0) / orig_sum for t in valid_tickers])
    opt_w_array = np.array([optimized_weights.get(t, 0) / opt_sum for t in valid_tickers])
    
    # Portfolio Daily Returns (dot product of weights and daily returns)
    # Assumes daily rebalancing to target weights for simplicity in visualization
    orig_daily_ret = returns_df[valid_tickers].dot(orig_w_array)
    opt_daily_ret = returns_df[valid_tickers].dot(opt_w_array)
    
    # Cumulative Returns
    orig_cum_ret = (1 + orig_daily_ret).cumprod()
    opt_cum_ret = (1 + opt_daily_ret).cumprod()
    
    # Calculate simple summary metrics
    def calc_metrics(daily_returns, cum_returns):
        total_return = cum_returns.iloc[-1] - 1
        annualized_return = (total_return + 1) ** (252 / len(daily_returns)) - 1
        annualized_vol = daily_returns.std() * np.sqrt(252)
        sharpe = annualized_return / annualized_vol if annualized_vol > 0 else 0
        
        # Max Drawdown
        roll_max = cum_returns.cummax()
        drawdown = cum_returns / roll_max - 1.0
        mdd = drawdown.min()
        
        return {
            "total_return": total_return,
            "annual_return": annualized_return,
            "volatility": annualized_vol,
            "sharpe": sharpe,
            "max_drawdown": mdd
        }
        
    orig_metrics = calc_metrics(orig_daily_ret, orig_cum_ret)
    opt_metrics = calc_metrics(opt_daily_ret, opt_cum_ret)
    
    return {
        "dates": dates,
        "original_series": orig_cum_ret.tolist(),
        "optimized_series": opt_cum_ret.tolist(),
        "original_metrics": orig_metrics,
        "optimized_metrics": opt_metrics,
        "valid_tickers": valid_tickers
    }
