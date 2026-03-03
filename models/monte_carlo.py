import numpy as np
import pandas as pd

def run_monte_carlo_simulation(expected_return, volatility, initial_investment=10000, years=5, simulations=10000):
    """
    Runs a Geometric Brownian Motion (GBM) Monte Carlo simulation to project future portfolio values.
    
    Args:
        expected_return (float): The expected annualized return of the optimized portfolio.
        volatility (float): The annualized risk/volatility of the optimized portfolio.
        initial_investment (float): Starting dollar value.
        years (int): Number of years to project forward.
        simulations (int): Number of parallel realities to calculate.
        
    Returns:
        dict: A dictionary containing the percentiles and sample paths for plotting.
    """
    trading_days_per_year = 252
    total_days = int(years * trading_days_per_year)
    
    if total_days <= 0:
        return {"error": "Prediction horizon must be greater than 0."}
        
    try:
        # Calculate daily drift and volatility
        daily_return = expected_return / trading_days_per_year
        daily_vol = volatility / np.sqrt(trading_days_per_year)
        
        # Generate random shock matrix (simulations x total_days)
        Z = np.random.normal(0, 1, (simulations, total_days))
        
        # Calculate daily returns (Geometric Brownian Motion formula)
        daily_returns = np.exp((daily_return - 0.5 * daily_vol**2) + daily_vol * Z)
        
        # Initialize price paths
        price_paths = np.zeros((simulations, total_days))
        price_paths[:, 0] = initial_investment
        
        # Simulate paths across time (vectorized cumulative product is much faster than a loop)
        # price_paths = initial_investment * cumprod(daily_returns)
        cumulative_returns = np.cumprod(daily_returns, axis=1)
        price_paths[:, 1:] = initial_investment * cumulative_returns[:, :-1]
        
        # Extract final values
        final_values = price_paths[:, -1]
        
        # Calculate percentiles
        p5 = np.percentile(final_values, 5)
        p50 = np.percentile(final_values, 50)
        p95 = np.percentile(final_values, 95)
        
        return {
            "initial_investment": initial_investment,
            "p5_value": p5,
            "p50_value": p50,
            "p95_value": p95,
            # We don't want to send 10,000 paths to the frontend, so we extract 100 random samples for the "Cone" visualization
            "sample_paths": price_paths[np.random.choice(simulations, 100, replace=False), :].tolist(),
            "days": list(range(total_days)),
            "error": None
        }
    except Exception as e:
        return {"error": f"Monte Carlo simulation failed: {str(e)}"}
