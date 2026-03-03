# valuation.py
import config

def calculate_value_score(data):
    """
    Compute DCF + Value Score.
    Returns: value_score (0-100), intrinsic_value
    """
    fcf = data['fcf']
    current_price = data['price']
    
    # Handle missing or negative FCF
    if fcf is None or fcf.empty or fcf.mean() <= 0:
        fcf_val = 1  # small positive default
    else:
        fcf_val = fcf.iloc[0]
    
    # Project FCF
    projected_fcf = [fcf_val * (1.05 ** i) for i in range(1, config.PROJECTION_YEARS + 1)]
    
    # Discounted FCF
    pv_fcf = sum([val / ((1 + config.DISCOUNT_RATE) ** i) for i, val in enumerate(projected_fcf, 1)])
    
    # Terminal Value
    tv = max(0, (projected_fcf[-1] * (1 + config.TERMINAL_GROWTH)) / (config.DISCOUNT_RATE - config.TERMINAL_GROWTH))
    pv_tv = tv / ((1 + config.DISCOUNT_RATE) ** config.PROJECTION_YEARS)
    
    # Intrinsic value per share
    shares = data['info'].get('sharesOutstanding', 1)
    intrinsic_value_per_share = (pv_fcf + pv_tv) / shares
    
    # Margin of Safety
    margin_of_safety = max(0, (intrinsic_value_per_share - current_price) / intrinsic_value_per_share)
    
    # P/E score
    pe = data['info'].get('trailingPE', config.MAX_PE)
    pe_score = max(0, min(100, 100 - (pe / config.MAX_PE * 50)))
    
    # Margin of Safety score
    mos_score = min(100, margin_of_safety * 200)
    
    final_v_score = round(pe_score * 0.4 + mos_score * 0.6, 2)
    
    return final_v_score, round(intrinsic_value_per_share, 2)