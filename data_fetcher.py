import yfinance as yf
import pandas as pd

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Financials for growth/value metrics
        hist = stock.history(period="5y")
        cash_flow = stock.cashflow
        balance_sheet = stock.balance_sheet
        financials = stock.financials
        
        return {
            "info": info,
            "fcf": cash_flow.loc['Free Cash Flow'] if 'Free Cash Flow' in cash_flow.index else None,
            "eps": financials.loc['Diluted EPS'] if 'Diluted EPS' in financials.index else None,
            "revenue": financials.loc['Total Revenue'] if 'Total Revenue' in financials.index else None,
            "equity": balance_sheet.loc['Stockholders Equity'] if 'Stockholders Equity' in balance_sheet.index else None,
            "price": info.get('currentPrice')
        }
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None