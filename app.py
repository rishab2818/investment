import streamlit as st
import config
from utils.ui_elements import set_premium_css, render_metric_card, render_ai_insight
from models.compounder import evaluate_compounder
from models.deep_value import evaluate_deep_value
from models.llm_analyzer import analyze_company_moat
import time

st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def run_screener(strategy_func, tickers):
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        status_text.text(f"Analyzing {ticker} ({i+1}/{len(tickers)})...")
        res = strategy_func(ticker)
        if res.get("passed"):
            results.append(res)
        progress_bar.progress((i + 1) / len(tickers))
        time.sleep(0.1) # prevent rate limits slightly
        
    status_text.text("Analysis complete.")
    return results

def main():
    set_premium_css()
    
    st.sidebar.title(f"📈 {config.APP_TITLE}")
    st.sidebar.caption(config.APP_SUBTITLE)
    st.sidebar.markdown("---")
    navigation = st.sidebar.radio("Navigation", ["Dashboard / Screener", "Single Stock Analysis", "Backtesting Engine"])
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("API Configuration")
    api_key_input = st.sidebar.text_input("Gemini API Key", value=config.GEMINI_API_KEY, type="password")
    if str(api_key_input) != config.GEMINI_API_KEY:
        config.GEMINI_API_KEY = str(api_key_input)
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
        except:
            pass
            
    # Allow user to specify universe
    st.sidebar.markdown("---")
    st.sidebar.subheader("Screener Universe")
    universe_str = st.sidebar.text_area("Enter Tickers (comma separated)", value=", ".join(config.DEFAULT_TICKERS))
    screener_tickers = [t.strip().upper() for t in universe_str.split(",") if t.strip()]

    if navigation == "Dashboard / Screener":
        st.title("Automated Screener")
        st.markdown("Identify high-probability opportunities based on strict math and AI analysis.")
        
        # Add dynamic sliders for screening criteria
        st.sidebar.markdown("---")
        st.sidebar.subheader("Screener Thresholds")
        st.sidebar.markdown("**Compounder Strategy**")
        cmp_roic = st.sidebar.slider("Min ROIC (%)", min_value=0, max_value=50, value=int(config.COMPOUNDER_MIN_ROIC*100), step=1) / 100
        cmp_fcf_cagr = st.sidebar.slider("Min FCF Growth (%)", min_value=0, max_value=50, value=int(config.COMPOUNDER_MIN_FCF_CAGR*100), step=1) / 100
        cmp_debt_eq = st.sidebar.slider("Max Debt/Equity", min_value=0.0, max_value=3.0, value=float(config.COMPOUNDER_MAX_DEBT_EQ), step=0.1)
        
        st.sidebar.markdown("**Deep Value Strategy**")
        val_pb = st.sidebar.slider("Max Price/Book", min_value=0.0, max_value=5.0, value=float(config.DEEP_VALUE_MAX_PB), step=0.1)
        val_rd = st.sidebar.slider("Min R&D/Rev (%)", min_value=0, max_value=30, value=int(config.DEEP_VALUE_MIN_RD_REV*100), step=1) / 100
        val_drop = st.sidebar.slider("Min 52w Drop (%)", min_value=0, max_value=80, value=int(config.DEEP_VALUE_PRICE_DROP*100), step=1) / 100
        
        tab1, tab2 = st.tabs(["Strategy 1: High Conviction Compounders", "Strategy 2: Deep Value & Moat"])
        
        with tab1:
            st.subheader("The Compounders")
            st.info(f"Criteria: ROIC > {cmp_roic*100:.0f}%, FCF Growth > {cmp_fcf_cagr*100:.0f}%, Debt/Eq < {cmp_debt_eq}")
            
            if st.button("Run Compounder Screen", key="run_cmp", type="primary"):
                # Temporarily override config for the run
                orig_cmp = (config.COMPOUNDER_MIN_ROIC, config.COMPOUNDER_MIN_FCF_CAGR, config.COMPOUNDER_MAX_DEBT_EQ)
                config.COMPOUNDER_MIN_ROIC, config.COMPOUNDER_MIN_FCF_CAGR, config.COMPOUNDER_MAX_DEBT_EQ = cmp_roic, cmp_fcf_cagr, cmp_debt_eq
                
                results = run_screener(evaluate_compounder, screener_tickers)
                
                # Restore config
                (config.COMPOUNDER_MIN_ROIC, config.COMPOUNDER_MIN_FCF_CAGR, config.COMPOUNDER_MAX_DEBT_EQ) = orig_cmp
                
                if not results:
                    st.warning("No stocks passed the criteria in the current universe.")
                else:
                    st.success(f"{len(results)} stocks passed!")
                    
                    # CSV Export
                    import pandas as pd
                    df_res = pd.DataFrame([{
                        'Ticker': r['ticker'], 'Name': r['name'], 'Sector': r['sector'],
                        'ROIC': r['metrics']['ROIC'], 'FCF_Growth': r['metrics']['FCF_CAGR'], 'Debt_Eq': r['metrics']['Debt_Eq']
                    } for r in results])
                    csv = df_res.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name='compounder_results.csv',
                        mime='text/csv',
                    )
                    
                    for res in results:
                        with st.expander(f"✅ {res['ticker']} - {res['name']} ({res['sector']})", expanded=True):
                            col1, col2, col3 = st.columns(3)
                            with col1: render_metric_card("ROIC", f"{res['metrics']['ROIC']*100:.1f}%")
                            with col2: render_metric_card("FCF Growth", f"{res['metrics']['FCF_CAGR']*100:.1f}%")
                            with col3: render_metric_card("Debt/Eq", f"{res['metrics']['Debt_Eq']:.2f}", is_positive=res['metrics']['Debt_Eq'] < 1.0)
                            
                            with st.spinner("Querying Gemini AI..."):
                                insight = analyze_company_moat(res['summary'], res['sector'], res['industry'])
                                render_ai_insight(insight, title=f"AI Analyst View on {res['ticker']}")

        with tab2:
            st.subheader("Deep Value & Moat")
            st.info(f"Criteria: P/B < {val_pb}, R&D/Rev > {val_rd*100:.0f}%, Price Drop > {val_drop*100:.0f}%")
            if st.button("Run Deep Value Screen", key="run_val", type="primary"):
                # Temporarily override config for the run
                orig_val = (config.DEEP_VALUE_MAX_PB, config.DEEP_VALUE_MIN_RD_REV, config.DEEP_VALUE_PRICE_DROP)
                config.DEEP_VALUE_MAX_PB, config.DEEP_VALUE_MIN_RD_REV, config.DEEP_VALUE_PRICE_DROP = val_pb, val_rd, val_drop
                
                results = run_screener(evaluate_deep_value, screener_tickers)
                
                # Restore config
                (config.DEEP_VALUE_MAX_PB, config.DEEP_VALUE_MIN_RD_REV, config.DEEP_VALUE_PRICE_DROP) = orig_val
                
                if not results:
                    st.warning("No stocks passed the criteria in the current universe.")
                else:
                    st.success(f"{len(results)} stocks passed!")
                    
                    # CSV Export
                    import pandas as pd
                    df_res = pd.DataFrame([{
                        'Ticker': r['ticker'], 'Name': r['name'], 'Sector': r['sector'],
                        'Price_Drop': r['metrics']['Price_Drop'], 'P_B': r['metrics']['P_B'], 'RD_Rev': r['metrics']['RD_Rev']
                    } for r in results])
                    csv = df_res.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name='deep_value_results.csv',
                        mime='text/csv',
                    )
                    
                    for res in results:
                        with st.expander(f"✅ {res['ticker']} - {res['name']} ({res['sector']})", expanded=True):
                            col1, col2, col3 = st.columns(3)
                            with col1: render_metric_card("Price Drop (52w)", f"{res['metrics']['Price_Drop']*100:.1f}%", is_positive=False)
                            with col2: render_metric_card("Price/Book", f"{res['metrics']['P_B']:.2f}", is_positive=res['metrics']['P_B'] < 1.0)
                            with col3: render_metric_card("R&D / Revenue", f"{res['metrics']['RD_Rev']*100:.1f}%")
                            
                            with st.spinner("Querying Gemini AI..."):
                                insight = analyze_company_moat(res['summary'], res['sector'], res['industry'])
                                render_ai_insight(insight, title=f"AI Analyst View on {res['ticker']}")
                                
    elif navigation == "Single Stock Analysis":
        st.title("Deep Dive Analysis")
        ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, TSLA)", "AAPL").upper()
        
        if st.button("Analyze Stock", type="primary"):
            from data.fetcher import get_stock_fundamentals
            with st.spinner(f"Pulling real-time models and AI analysis for {ticker}..."):
                data = get_stock_fundamentals(ticker)
                if "error" in data:
                    st.error(f"Error fetching data: {data['error']}")
                else:
                    col1, col2, col3 = st.columns(3)
                    with col1: render_metric_card("Current Price", f"${data['current_price']:.2f}")
                    with col2: render_metric_card("ROIC", f"{data['roic']*100:.1f}%")
                    with col3: render_metric_card("P/B", f"{data['price_to_book']:.2f}")
                    
                    col2_1, col2_2, col2_3 = st.columns(3)
                    with col2_1: render_metric_card("Piotroski F-Score", f"{data.get('f_score', 0)}/9", is_positive=data.get('f_score', 0) >= 6)
                    with col2_2: render_metric_card("Altman Z-Score", f"{data.get('z_score', 0):.2f}", is_positive=data.get('z_score', 0) > 2.99)
                    
                    st.markdown("---")
                    st.subheader("Intrinsic Valuation (DCF)")
                    if data.get("intrinsic_value", 0) > 0:
                        iv_col1, iv_col2, iv_col3 = st.columns(3)
                        with iv_col1: render_metric_card("Fair Value Price", f"${data['intrinsic_value']:.2f}", is_positive=data['intrinsic_value'] > data['current_price'])
                        with iv_col2: render_metric_card("Margin of Safety", f"{data['margin_of_safety']*100:.1f}%", is_positive=data['margin_of_safety'] > 0)
                        
                        implied_g = data.get("implied_fcf_growth", 0)
                        with iv_col3: render_metric_card("Reverse DCF Implied Growth", f"{implied_g*100:.1f}%", is_positive=implied_g < data.get("fcf_cagr", 0))
                    else:
                        st.info("Insufficient cash flow data to project a reliable DCF intrinsic value.")
                        
                    st.markdown("---")
                    if data.get("news"):
                        st.subheader("Recent News Headlines")
                        for n in data["news"]:
                            st.markdown(f"- {n}")
                    
                    st.subheader("Qualitative AI Analysis")
                    # Pass the extra info (news, implied growth) directly into the LLM analyzer
                    insight = analyze_company_moat(
                        data['summary'], 
                        data['sector'], 
                        data['industry'],
                        news=data.get('news'),
                        implied_growth=data.get('implied_fcf_growth', 0),
                        f_score=data.get('f_score', 0),
                        z_score=data.get('z_score', 0)
                    )
                    render_ai_insight(insight)

    elif navigation == "Backtesting Engine":
        st.title("Backtesting Engine")
        st.markdown("Test the Compounder and Deep Value strategies against historical data (SPY benchmark).")
        
        tickers_input = st.text_input("Enter portfolio tickers (comma separated)", "AAPL, MSFT, GOOGL")
        period = st.selectbox("Historical Period", ["1y", "3y", "5y", "10y"], index=2)
        
        if st.button("Run Simulation", type="primary"):
            from backtest.engine import run_backtest
            import plotly.graph_objects as go
            
            test_tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
            with st.spinner(f"Simulating historical {period} performance..."):
                results = run_backtest(test_tickers, period=period)
                
                if "error" in results:
                    st.error(results["error"])
                else:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1: render_metric_card("Portfolio Return", f"{results['portfolio_return']*100:.1f}%")
                    with col2: render_metric_card("Alpha (vs SPY)", f"{results['alpha']*100:.1f}%", is_positive=results['alpha']>0)
                    with col3: render_metric_card("Sharpe Ratio", f"{results['portfolio_sharpe']:.2f}")
                    with col4: render_metric_card("Max Drawdown", f"{results['portfolio_mdd']*100:.1f}%", is_positive=False)
                    
                    st.subheader("Cumulative Growth")
                    # Plotly chart
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=results['dates'], y=results['portfolio_cum_series'], name="Portfolio", line=dict(color='#10B981', width=2)))
                    fig.add_trace(go.Scatter(x=results['dates'], y=results['benchmark_cum_series'], name="SPY Benchmark", line=dict(color='#94A3B8', width=2)))
                    fig.update_layout(template="plotly_dark", plot_bgcolor="#1E293B", paper_bgcolor="#0E1117", margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if "correlation_matrix" in results and len(test_tickers) > 1:
                        st.subheader("Asset Correlation Matrix")
                        import plotly.express as px
                        corr_fig = px.imshow(results["correlation_matrix"], 
                                             text_auto=True, 
                                             aspect="auto",
                                             color_continuous_scale="RdBu_r")
                        corr_fig.update_layout(template="plotly_dark", plot_bgcolor="#1E293B", paper_bgcolor="#0E1117", margin=dict(l=20, r=20, t=40, b=20))
                        st.plotly_chart(corr_fig, use_container_width=True)
                    
                    st.markdown("---")
                    st.subheader("Institutional Risk Analysis & Tearsheet")
                    if "quantstats_html" in results:
                        import streamlit.components.v1 as components
                        components.html(results["quantstats_html"], height=1000, scrolling=True)
                    else:
                        st.warning("QuantStats report generation failed. Check the logs.")

if __name__ == "__main__":
    main()
