# growth.py
import config

def calculate_growth_score(data):
    """
    Compute Growth score (Peter Lynch style)
    """
    eps = data['eps']
    revenue = data['revenue']
    
    # Handle missing data
    if eps is None or eps.empty:
        eps_growth = 0
    else:
        eps = eps.dropna()
        eps_growth = eps.pct_change(periods=3, fill_method=None).iloc[-1] if len(eps) > 3 else 0
        eps_growth = max(0, eps_growth)  # negative growth → 0
    
    if revenue is None or revenue.empty:
        rev_growth = 0
    else:
        revenue = revenue.dropna()
        rev_growth = revenue.pct_change(periods=3, fill_method=None).iloc[-1] if len(revenue) > 3 else 0
        rev_growth = max(0, rev_growth)
    
    # PEG ratio
    pe = data['info'].get('trailingPE', 1)
    growth_pct = eps_growth * 100
    peg = pe / growth_pct if growth_pct > 0 else 10
    peg = min(peg, 10)  # cap extreme PEG
    
    # Scoring
    peg_score = 100 if peg <= 1 else (50 if peg <= 2 else 0)
    growth_comp_score = min(100, (eps_growth * 200) + (rev_growth * 100))
    
    final_g_score = round((peg_score * 0.5) + (growth_comp_score * 0.5), 2)
    final_g_score = max(0, min(100, final_g_score))  # clamp
    
    return final_g_score