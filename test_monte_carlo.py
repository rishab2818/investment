import os
import sys

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.monte_carlo import run_monte_carlo_simulation

print("Testing Monte Carlo Simulation...")
result = run_monte_carlo_simulation(
    expected_return=0.15, 
    volatility=0.20, 
    initial_investment=10000, 
    years=5, 
    simulations=1000
)

if result.get("error"):
    print(f"FAILED: {result['error']}")
else:
    print("SUCCESS!")
    print(f"P5 (Worst Case):  ${result['p5_value']:,.2f}")
    print(f"P50 (Expected):   ${result['p50_value']:,.2f}")
    print(f"P95 (Best Case):  ${result['p95_value']:,.2f}")
    print(f"Sample Paths Extracted: {len(result['sample_paths'])}")
    print(f"Trading Days: {len(result['days'])}")
