import yfinance as yf
import pandas as pd
import numpy as np

def calculate_sharpe_ratio(returns, risk_free_rate=0.04):
    """Calculate annualized Sharpe Ratio"""
    if len(returns) == 0 or returns.std() == 0: return 0
    # Annualized return assuming daily data (252 trading days)
    ann_return = returns.mean() * 252
    ann_vol = returns.std() * np.sqrt(252)
    return (ann_return - risk_free_rate) / ann_vol

def calculate_max_drawdown(prices):
    """Calculate maximum drawdown from peak"""
    if len(prices) == 0: return 0
    rolling_max = prices.cummax()
    drawdowns = (prices - rolling_max) / rolling_max
    return drawdowns.min()

def run_backtest(tickers, period="5y", benchmark="SPY"):
    """
    Simulates equal-weight portfolio of 'tickers' over 'period'.
    Compares against 'benchmark'.
    """
    if not tickers:
        return {"error": "No tickers provided for backtest."}
        
    try:
        # Download data
        all_tickers = tickers + [benchmark]
        data = yf.download(all_tickers, period=period)["Close"]
        
        # If only one ticker + benchmark, yf changes DataFrame structure
        if len(all_tickers) == 2:
            pass # Keep as is, it's a 2-column DF
            
        data = data.dropna()
        if data.empty:
            return {"error": "Insufficient historical data."}
            
        returns = data.pct_change().dropna()
        
        # Portfolio returns (equal weight)
        port_returns = returns[tickers].mean(axis=1)
        bench_returns = returns[benchmark]
        
        # Cumulative performance
        port_cum = (1 + port_returns).cumprod()
        bench_cum = (1 + bench_returns).cumprod()
        
        # Metrics
        port_sharpe = calculate_sharpe_ratio(port_returns)
        bench_sharpe = calculate_sharpe_ratio(bench_returns)
        
        port_mdd = calculate_max_drawdown(port_cum)
        bench_mdd = calculate_max_drawdown(bench_cum)
        
        # Total Return
        port_total_ret = port_cum.iloc[-1] - 1
        bench_total_ret = bench_cum.iloc[-1] - 1
        
        # Alpha (simple outperformance)
        alpha = port_total_ret - bench_total_ret
        
        # Correlation Matrix
        correlation_matrix = returns[tickers].corr()
        
        # --- QUANTSTATS INTEGRATION ---
        import quantstats as qs
        import tempfile
        import os
        
        qs.extend_pandas()
        
        # Ensure returns are timezone naive for QuantStats
        try:
            port_returns.index = port_returns.index.tz_localize(None)
            bench_returns.index = bench_returns.index.tz_localize(None)
        except Exception:
            pass
            
        # Generate HTML report
        # We save it to a temp file, read the HTML, then delete it
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, "qs_report.html")
        
        try:
            qs.reports.html(port_returns, bench_returns, output=temp_file_path, title="ValueCompass AI Tearsheet")
            with open(temp_file_path, "r", encoding="utf-8") as f:
                quantstats_html = f.read()
            os.remove(temp_file_path)
        except Exception as qse:
            quantstats_html = f"<div>Error generating QuantStats report: {qse}</div>"
        
        return {
            "portfolio_return": port_total_ret,
            "benchmark_return": bench_total_ret,
            "alpha": alpha,
            "portfolio_sharpe": port_sharpe,
            "benchmark_sharpe": bench_sharpe,
            "portfolio_mdd": port_mdd,
            "benchmark_mdd": bench_mdd,
            "dates": data.index,
            "portfolio_cum_series": port_cum,
            "benchmark_cum_series": bench_cum,
            "correlation_matrix": correlation_matrix,
            "quantstats_html": quantstats_html
        }
        
    except Exception as e:
        return {"error": str(e)}
