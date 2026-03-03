import os
import sys

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.optimizer import generate_rebalance_plan
from models.portfolio_backtester import run_portfolio_backtest
from data.fetcher import get_stock_fundamentals
import time

def run_test(test_name, tickers, initial_weights, user_goal, expected_constraints=None):
    print(f"\n{'='*50}")
    print(f"TEST: {test_name}")
    print(f"Goal: {user_goal}")
    print(f"Original Portfolio: {initial_weights}")
    print(f"{'='*50}")
    
    # 1. Fetch data
    print("1. Fetching fundamental data...")
    fundamental_context = {}
    for t in tickers:
        data = get_stock_fundamentals(t)
        if "error" not in data:
            fundamental_context[t] = data
        else:
            print(f"WARNING: Could not fetch {t} - {data['error']}")
        time.sleep(0.5) # rate limit protection
        
    print(f"Successfully fetched {len(fundamental_context)}/{len(tickers)} tickers.")
    
    # 2. Simulate AI Constraints OR use the actual LLM if keys exist
    # Since this is an automated unit test script, we will mock the bounds for predictable testing of the math engine.
    bounds = expected_constraints if expected_constraints else {}
    print(f"2. Simulating AI Constraints: {bounds}")
    
    # 3. Run Math Optimizer
    print("3. Running PyPortfolioOpt Optimizer...")
    objective = "max_sharpe"
    if "Conservative" in user_goal or "Dividend" in user_goal:
        objective = "min_volatility"
        
    opt_result = generate_rebalance_plan(tickers, constraint_overrides=bounds, objective=objective)
    
    if opt_result.get("error"):
        print(f"FAIL: OPTIMIZATION: {opt_result['error']}")
        return False
        
    proposed_weights = opt_result["weights"]
    
    # Print out nicely
    print("\n--- RESULTS ---")
    print("Target Weights:")
    for t, w in proposed_weights.items():
        if w > 0.001:
            print(f"  {t}: {w*100:.1f}%")
            
    print(f"Expected Annual Return: {opt_result['expected_annual_return']*100:.1f}%")
    print(f"Annual Volatility: {opt_result['annual_volatility']*100:.1f}%")
    print(f"Sharpe Ratio: {opt_result['sharpe_ratio']:.2f}")
    
    # 4. Run Isolated Backtester
    print("\n4. Running Isolated Historical Backtest (5y)...")
    bt_result = run_portfolio_backtest(tickers, initial_weights, proposed_weights, period="5y")
    
    if "error" in bt_result:
        print(f"FAIL: BACKTEST: {bt_result['error']}")
        return False
        
    orig_m = bt_result['original_metrics']
    opt_m = bt_result['optimized_metrics']
    
    print("\n--- EMPIRICAL VALIDATION (Last 5 Years) ---")
    print(f"{'Metric':<20} | {'Original':<12} | {'AI Optimized':<12} | {'Improvement'}")
    print("-" * 65)
    
    ret_imp = opt_m['annual_return'] - orig_m['annual_return']
    print(f"{'Ann. Return':<20} | {orig_m['annual_return']*100:>11.1f}% | {opt_m['annual_return']*100:>11.1f}% | {'+' if ret_imp>0 else ''}{ret_imp*100:.1f}%")
    
    vol_imp = orig_m['volatility'] - opt_m['volatility']
    print(f"{'Volatility (Risk)':<20} | {orig_m['volatility']*100:>11.1f}% | {opt_m['volatility']*100:>11.1f}% | {'+' if vol_imp>0 else ''}{vol_imp*100:.1f}% (lower=better)")
    
    sharpe_imp = opt_m['sharpe'] - orig_m['sharpe']
    print(f"{'Sharpe Ratio':<20} | {orig_m['sharpe']:>11.2f}  | {opt_m['sharpe']:>11.2f}  | {'+' if sharpe_imp>0 else ''}{sharpe_imp:.2f}")
    
    mdd_imp = orig_m['max_drawdown'] - opt_m['max_drawdown'] # Both are negative
    print(f"{'Max Drawdown':<20} | {orig_m['max_drawdown']*100:>11.1f}% | {opt_m['max_drawdown']*100:>11.1f}% | {'+' if mdd_imp<0 else ''}{-mdd_imp*100:.1f}% (better)")
    
    print("\nTest Passed")
    return True

if __name__ == "__main__":
    print("Starting AI Portfolio Optimizer robust validation suite...")
    
    # TEST 1: Tech Heavy Growth (Constrained)
    # The AI determined the user wants max growth but cap NVDA at 20% due to risk tolerance.
    t1_pass = run_test(
        test_name="High Growth Tech with AI Concentration Constraint",
        tickers=["AAPL", "MSFT", "NVDA", "INTC", "GOOGL"],
        initial_weights={"AAPL": 0.3, "MSFT": 0.3, "NVDA": 0.0, "INTC": 0.4, "GOOGL": 0.0},
        user_goal="Aggressive Growth, cap any single soaring asset at 20% Max.",
        expected_constraints={"NVDA": [0.0, 0.20], "INTC": [0.0, 0.10]} # AI punishing INTC due to bad fundamentals
    )
    
    # TEST 2: Dividend generation (Min Volatility)
    t2_pass = run_test(
        test_name="Conservative Dividend Generation",
        tickers=["XOM", "CVX", "JNJ", "KO", "PG"],
        initial_weights={"XOM": 0.5, "CVX": 0.5, "JNJ": 0.0, "KO": 0.0, "PG": 0.0},
        user_goal="Conservative, Capital Preservation, Maximize Dividend Safety",
        expected_constraints={"KO": [0.2, 0.4], "PG": [0.2, 0.4]} # AI forcing allocation to stable consumer defensives
    )
    
    # TEST 3: Edge Case (Invalid Ticker handling)
    t3_pass = run_test(
        test_name="Edge Case: Invalid Tickers Resiliency",
        tickers=["AAPL", "MSFT", "INVALID_TICKER_X123"],
        initial_weights={"AAPL": 0.5, "MSFT": 0.4, "INVALID_TICKER_X123": 0.1},
        user_goal="Balanced Growth",
        expected_constraints=None
    )
    
    print("\n" + "="*50)
    print("TEST SUITE SUMMARY")
    print(f"Test 1 (Tech Growth): {'PASS' if t1_pass else 'FAIL'}")
    print(f"Test 2 (Dividend Def): {'PASS' if t2_pass else 'FAIL'}")
    print(f"Test 3 (Edge Cases):  {'PASS' if t3_pass else 'FAIL'}")
