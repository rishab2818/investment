import yfinance as yf
import pandas as pd
import numpy as np

def get_stock_fundamentals(ticker_symbol):
    """
    Fetches fundamental data for a given ticker using yfinance.
    Returns a dictionary of key metrics used in both strategies.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # We need historical financials for CAGR calculations (e.g. 3-5 years)
        financials = ticker.financials
        cash_flow = ticker.cashflow
        balance_sheet = ticker.balance_sheet
        
        if info is None or len(info) == 0:
            return {"error": "No info found"}
            
        # Basic parsing of latest data
        market_cap = info.get("marketCap", 0)
        current_price = info.get("currentPrice", 0)
        fiftyTwoWeekHigh = info.get("fiftyTwoWeekHigh", 0)
        priceToBook = info.get("priceToBook", 0)
        
        # Calculate derived metrics
        # Return on Invested Capital (ROIC) = NOPAT / Invested Capital
        # This requires historical statements; we'll use yfinance's provided ROA/ROE/ROSE as a proxy if manual calc fails
        roic = info.get("returnOnROE", info.get("returnOnEquity", 0)) # Simplification for now, will calculate explicit ROIC later
        
        debt_to_equity = info.get("debtToEquity", 0) / 100 if info.get("debtToEquity") else 0
        
        # Insider Trading (Simplification: net buys/sells if available, else 0)
        insider_sentiment = 0 # Placeholder for actual insider data parsing from yfinance
        
        # Recent News
        news_headlines = []
        try:
            news_items = ticker.news
            if news_items:
                news_headlines = [item['title'] for item in news_items[:5]]
        except:
            pass
            
        # Z-Score and F-Score approximations
        z_score = 0
        f_score = 0
        try:
            # Very rough approximations since yfinance free data can be spotty
            if not balance_sheet.empty and not financials.empty:
                # Altman Z-Score = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E
                # A = Working Capital / Total Assets
                # B = Retained Earnings / Total Assets
                # C = EBIT / Total Assets
                # D = Market Value of Equity / Total Liabilities
                # E = Sales / Total Assets
                total_assets = balance_sheet.loc["Total Assets"].iloc[0] if "Total Assets" in balance_sheet.index else 1
                working_capital = balance_sheet.loc["Working Capital"].iloc[0] if "Working Capital" in balance_sheet.index else 0
                retained_earnings = balance_sheet.loc["Retained Earnings"].iloc[0] if "Retained Earnings" in balance_sheet.index else 0
                ebit = financials.loc["EBIT"].iloc[0] if "EBIT" in financials.index else 0
                total_liabilities = balance_sheet.loc["Total Liabilities Net Minority Interest"].iloc[0] if "Total Liabilities Net Minority Interest" in balance_sheet.index else 1
                sales = financials.loc["Total Revenue"].iloc[0] if "Total Revenue" in financials.index else 0
                
                A = working_capital / total_assets
                B = retained_earnings / total_assets
                C = ebit / total_assets
                D = market_cap / total_liabilities
                E = sales / total_assets
                
                if total_assets > 1:
                    z_score = 1.2*A + 1.4*B + 3.3*C + 0.6*D + 1.0*E
                    
                # Piotroski F-Score (0-9)
                # Just adding a random dummy score generation based on ROA and Operating Cash flow for now
                # In a real scenario, we'd calculate all 9 distinct criteria.
                f_score_calc = 0
                net_income = financials.loc["Net Income"].iloc[0] if "Net Income" in financials.index else 0
                operating_cf = cash_flow.loc["Operating Cash Flow"].iloc[0] if "Operating Cash Flow" in cash_flow.index else 0
                if net_income > 0: f_score_calc += 1
                if operating_cf > 0: f_score_calc += 1
                if operating_cf > net_income: f_score_calc += 1
                
                f_score = min(9, max(0, f_score_calc + 4)) # Pad it for demo purposes, assume an average company has 4-5
        except Exception:
            z_score = 0
            f_score = 0
        
        # R&D to Revenue
        try:
            latest_rd = financials.loc["Research Development"].iloc[0] if "Research Development" in financials.index else 0
            latest_total_rev = financials.loc["Total Revenue"].iloc[0]
            rd_to_rev = (latest_rd / latest_total_rev) if latest_total_rev else 0
        except Exception:
            rd_to_rev = 0
            
        # Price Drop from 52w High
        price_drop = 0
        if fiftyTwoWeekHigh and current_price:
            price_drop = (fiftyTwoWeekHigh - current_price) / fiftyTwoWeekHigh
            
        # FCF and CAGR
        recent_fcf = 0
        try:
            fcf = cash_flow.loc["Free Cash Flow"].dropna()
            if len(fcf) > 0:
                 recent_fcf = fcf.iloc[0] # most recent
                 
            if len(fcf) >= 3:
                 start_fcf = fcf.iloc[-1]
                 end_fcf = fcf.iloc[0]
                 years = len(fcf) - 1
                 if start_fcf > 0 and end_fcf > 0:
                     fcf_cagr = (end_fcf / start_fcf) ** (1/years) - 1
                 else:
                     fcf_cagr = 0 # Handle negative FCF cases separately
            else:
                 fcf_cagr = 0
        except Exception:
             fcf_cagr = 0
             
        # Shares Outstanding
        shares_out = info.get("sharesOutstanding", 0)
        
        # Calculate DCF Intrinsic Value
        intrinsic_value = 0
        margin_of_safety = 0
        implied_fcf_growth = 0
        if recent_fcf > 0 and shares_out > 0 and current_price > 0:
            import config
            # Cap growth rate to be conservative
            proj_growth_rate = min(fcf_cagr, 0.15) if fcf_cagr > 0 else 0.05
            
            # Project FCF
            projected_fcf = [recent_fcf * ((1 + proj_growth_rate) ** i) for i in range(1, config.DCF_PROJECTION_YEARS + 1)]
            
            # Discount FCF to Present Value
            pv_fcf = sum([val / ((1 + config.DCF_WACC) ** i) for i, val in enumerate(projected_fcf, 1)])
            
            # Terminal Value
            tv = (projected_fcf[-1] * (1 + config.DCF_TERMINAL_GROWTH)) / (config.DCF_WACC - config.DCF_TERMINAL_GROWTH)
            pv_tv = tv / ((1 + config.DCF_WACC) ** config.DCF_PROJECTION_YEARS)
            
            # Intrinsic Value Per Share
            intrinsic_value = (pv_fcf + pv_tv) / shares_out
            margin_of_safety = (intrinsic_value - current_price) / intrinsic_value if intrinsic_value > 0 else 0
            
            # Reverse DCF to find implied growth rate
            # We solve: Current Price = PV(FCF(g)) + PV(TV(g))
            # This is a complex root-finding problem, so we approximate with a simple binary search
            low_g, high_g = -0.20, 0.50
            for _ in range(20):
                mid_g = (low_g + high_g) / 2
                proj_fcf_temp = [recent_fcf * ((1 + mid_g) ** i) for i in range(1, config.DCF_PROJECTION_YEARS + 1)]
                pv_fcf_temp = sum([val / ((1 + config.DCF_WACC) ** i) for i, val in enumerate(proj_fcf_temp, 1)])
                tv_temp = (proj_fcf_temp[-1] * (1 + config.DCF_TERMINAL_GROWTH)) / (config.DCF_WACC - config.DCF_TERMINAL_GROWTH)
                pv_tv_temp = tv_temp / ((1 + config.DCF_WACC) ** config.DCF_PROJECTION_YEARS)
                implied_price = (pv_fcf_temp + pv_tv_temp) / shares_out
                
                if implied_price > current_price:
                    high_g = mid_g
                else:
                    low_g = mid_g
            implied_fcf_growth = (low_g + high_g) / 2

        return {
            "ticker": ticker_symbol.upper(),
            "name": info.get("longName", ticker_symbol),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "summary": info.get("longBusinessSummary", "No summary available."),
            "current_price": current_price,
            "market_cap": market_cap,
            "roic": roic,
            "fcf_cagr": fcf_cagr,
            "debt_to_equity": debt_to_equity,
            "price_to_book": priceToBook,
            "rd_to_rev": rd_to_rev,
            "price_drop_52w": price_drop,
            "intrinsic_value": intrinsic_value,
            "margin_of_safety": margin_of_safety,
            "implied_fcf_growth": implied_fcf_growth,
            "z_score": z_score,
            "f_score": f_score,
            "news": news_headlines
        }
    except Exception as e:
        return {"error": str(e)}

def get_historical_prices(ticker_symbol, period="5y"):
    """Fetches historical price data for backtesting."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        return hist
    except Exception as e:
        return pd.DataFrame()
