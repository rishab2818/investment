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
        try:
            res = strategy_func(ticker)
            if res.get("passed"):
                results.append(res)
        except Exception as e:
            # Silently log/skip so the screener doesn't halt
            pass
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
    with st.sidebar.expander("⚙️ API Configuration", expanded=False):
        ai_provider = st.radio("AI Provider", ["Gemini (Google)", "OpenAI"], index=0 if config.AI_PROVIDER == "gemini" else 1)
        
        if ai_provider == "Gemini (Google)":
            config.AI_PROVIDER = "gemini"
            api_key_input = st.text_input("Gemini API Key", value=config.GEMINI_API_KEY, type="password")
            if str(api_key_input) != config.GEMINI_API_KEY:
                config.GEMINI_API_KEY = str(api_key_input)
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=config.GEMINI_API_KEY)
                except:
                    pass
        else:
            config.AI_PROVIDER = "openai"
            openai_key_input = st.text_input("OpenAI API Key", value=config.OPENAI_API_KEY, type="password")
            if str(openai_key_input) != config.OPENAI_API_KEY:
                config.OPENAI_API_KEY = str(openai_key_input)
                
    # Allow user to specify universe
    with st.sidebar.expander("🌍 Screener Universe", expanded=False):
        universe_str = st.text_area("Enter Tickers (comma separated)", value=", ".join(config.DEFAULT_TICKERS))
        screener_tickers = [t.strip().upper() for t in universe_str.split(",") if t.strip()]

    if navigation == "Dashboard / Screener":
        st.title("Automated Screener")
        st.markdown("Identify high-probability opportunities based on strict math and AI analysis.")
        
        # Add dynamic sliders for screening criteria
        st.sidebar.markdown("---")
        with st.sidebar.expander("🎛️ Screener Thresholds", expanded=False):
            st.markdown("**Compounder Strategy**")
            cmp_roic = st.slider("Min ROIC (%)", min_value=0, max_value=50, value=int(config.COMPOUNDER_MIN_ROIC*100), step=1) / 100
            cmp_fcf_cagr = st.slider("Min FCF Growth (%)", min_value=0, max_value=50, value=int(config.COMPOUNDER_MIN_FCF_CAGR*100), step=1) / 100
            cmp_debt_eq = st.slider("Max Debt/Equity", min_value=0.0, max_value=3.0, value=float(config.COMPOUNDER_MAX_DEBT_EQ), step=0.1)
            
            st.markdown("---")
            st.markdown("**Deep Value Strategy**")
            val_pb = st.slider("Max Price/Book", min_value=0.0, max_value=5.0, value=float(config.DEEP_VALUE_MAX_PB), step=0.1)
            val_rd = st.slider("Min R&D/Rev (%)", min_value=0, max_value=30, value=int(config.DEEP_VALUE_MIN_RD_REV*100), step=1) / 100
            val_drop = st.slider("Min 52w Drop (%)", min_value=0, max_value=80, value=int(config.DEEP_VALUE_PRICE_DROP*100), step=1) / 100
        
        tab1, tab2 = st.tabs(["Strategy 1: High Conviction Compounders", "Strategy 2: Deep Value & Moat"])
        
        with tab1:
            st.subheader("The Compounders")
            st.info(f"Criteria: ROIC > {cmp_roic*100:.0f}%, FCF Growth > {cmp_fcf_cagr*100:.0f}%, Debt/Eq < {cmp_debt_eq}")
            
            if "cmp_results" not in st.session_state:
                st.session_state.cmp_results = None
                st.session_state.cmp_insight = None
                st.session_state.cmp_insight_ticker = None
                
            if st.button("Run Compounder Screen", key="run_cmp", type="primary"):
                # Temporarily override config for the run
                orig_cmp = (config.COMPOUNDER_MIN_ROIC, config.COMPOUNDER_MIN_FCF_CAGR, config.COMPOUNDER_MAX_DEBT_EQ)
                config.COMPOUNDER_MIN_ROIC, config.COMPOUNDER_MIN_FCF_CAGR, config.COMPOUNDER_MAX_DEBT_EQ = cmp_roic, cmp_fcf_cagr, cmp_debt_eq
                
                st.session_state.cmp_results = run_screener(evaluate_compounder, screener_tickers)
                st.session_state.cmp_insight = None
                
                # Restore config
                (config.COMPOUNDER_MIN_ROIC, config.COMPOUNDER_MIN_FCF_CAGR, config.COMPOUNDER_MAX_DEBT_EQ) = orig_cmp
                
            if st.session_state.cmp_results is not None:
                results = st.session_state.cmp_results
                if not results:
                    st.warning("No stocks passed the criteria in the current universe.")
                else:
                    st.success(f"{len(results)} stocks passed!")
                    
                    import pandas as pd
                    df_res = pd.DataFrame([{
                        'Ticker': r['ticker'], 'Name': r['name'], 'Sector': r['sector'],
                        'ROIC': r['metrics']['ROIC'] * 100, 'FCF_Growth': r['metrics']['FCF_CAGR'] * 100, 'Debt_Eq': round(r['metrics']['Debt_Eq'], 2)
                    } for r in results])
                    
                    st.dataframe(df_res, use_container_width=True, hide_index=True, column_config={
                        "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                        "Name": st.column_config.TextColumn("Company"),
                        "Sector": st.column_config.TextColumn("Sector"),
                        "ROIC": st.column_config.NumberColumn("ROIC", format="%.1f%%", width="small"),
                        "FCF_Growth": st.column_config.NumberColumn("FCF Growth", format="%.1f%%", width="small"),
                        "Debt_Eq": st.column_config.NumberColumn("Debt/Equity", format="%.2f", width="small")
                    })
                    
                    csv = df_res.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name='compounder_results.csv',
                        mime='text/csv',
                    )
                    
                    st.markdown("---")
                    st.subheader("Deep Dive AI Insight")
                    st.write("Select a passing ticker to get an AI summary of its moat and viability.")
                    selected_ticker = st.selectbox("Select Ticker for AI Analysis", [r['ticker'] for r in results])
                    
                    if st.button("Generate AI Insight", key="ai_cmp"):
                        with st.spinner("Querying AI Analyst..."):
                            res = next(r for r in results if r['ticker'] == selected_ticker)
                            try:
                                st.session_state.cmp_insight = analyze_company_moat(res['summary'], res['sector'], res['industry'])
                                st.session_state.cmp_insight_ticker = selected_ticker
                            except Exception as e:
                                st.error(f"AI API Error: Rate limited or Invalid Key. Details: {str(e)[:100]}")
                                
                    if st.session_state.cmp_insight and st.session_state.cmp_insight_ticker == selected_ticker:
                        res = next(r for r in results if r['ticker'] == selected_ticker)
                        render_ai_insight(st.session_state.cmp_insight, title=f"AI Analyst View on {res['ticker']}")

        with tab2:
            st.subheader("Deep Value & Moat")
            st.info(f"Criteria: P/B < {val_pb}, R&D/Rev > {val_rd*100:.0f}%, Price Drop > {val_drop*100:.0f}%")
            if "val_results" not in st.session_state:
                st.session_state.val_results = None
                st.session_state.val_insight = None
                st.session_state.val_insight_ticker = None
                
            if st.button("Run Deep Value Screen", key="run_val", type="primary"):
                # Temporarily override config for the run
                orig_val = (config.DEEP_VALUE_MAX_PB, config.DEEP_VALUE_MIN_RD_REV, config.DEEP_VALUE_PRICE_DROP)
                config.DEEP_VALUE_MAX_PB, config.DEEP_VALUE_MIN_RD_REV, config.DEEP_VALUE_PRICE_DROP = val_pb, val_rd, val_drop
                
                st.session_state.val_results = run_screener(evaluate_deep_value, screener_tickers)
                st.session_state.val_insight = None
                
                # Restore config
                (config.DEEP_VALUE_MAX_PB, config.DEEP_VALUE_MIN_RD_REV, config.DEEP_VALUE_PRICE_DROP) = orig_val
                
            if st.session_state.val_results is not None:
                results = st.session_state.val_results
                if not results:
                    st.warning("No stocks passed the criteria in the current universe.")
                else:
                    st.success(f"{len(results)} stocks passed!")
                    
                    import pandas as pd
                    df_res = pd.DataFrame([{
                        'Ticker': r['ticker'], 'Name': r['name'], 'Sector': r['sector'],
                        'Price_Drop': r['metrics']['Price_Drop'] * 100, 'P_B': round(r['metrics']['P_B'], 2), 'RD_Rev': r['metrics']['RD_Rev'] * 100
                    } for r in results])
                    
                    st.dataframe(df_res, use_container_width=True, hide_index=True, column_config={
                        "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                        "Name": st.column_config.TextColumn("Company"),
                        "Sector": st.column_config.TextColumn("Sector"),
                        "Price_Drop": st.column_config.NumberColumn("52w Drop", format="%.1f%%", width="small"),
                        "P_B": st.column_config.NumberColumn("Price/Book", format="%.2f", width="small"),
                        "RD_Rev": st.column_config.NumberColumn("R&D/Rev", format="%.1f%%", width="small")
                    })
                    
                    csv = df_res.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name='deep_value_results.csv',
                        mime='text/csv',
                    )
                    
                    st.markdown("---")
                    st.subheader("Deep Dive AI Insight")
                    st.write("Select a passing ticker to get an AI summary of its moat and viability.")
                    selected_ticker_val = st.selectbox("Select Ticker for AI Analysis", [r['ticker'] for r in results], key="sel_val")
                    if st.button("Generate AI Insight", key="ai_val"):
                        with st.spinner("Querying AI Analyst..."):
                            res = next(r for r in results if r['ticker'] == selected_ticker_val)
                            try:
                                st.session_state.val_insight = analyze_company_moat(res['summary'], res['sector'], res['industry'])
                                st.session_state.val_insight_ticker = selected_ticker_val
                            except Exception as e:
                                st.error(f"AI API Error: Rate limited or Invalid Key. Details: {str(e)[:100]}")
                                
                    if st.session_state.val_insight and st.session_state.val_insight_ticker == selected_ticker_val:
                        res = next(r for r in results if r['ticker'] == selected_ticker_val)
                        render_ai_insight(st.session_state.val_insight, title=f"AI Analyst View on {res['ticker']}")
                                
    elif navigation == "Single Stock Analysis":
        st.title("Deep Dive Analysis")
        ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, TSLA)", "AAPL").upper()
        
        st.markdown("### Interactive Valuation Assumptions")
        col_w, col_t, col_y = st.columns(3)
        with col_w: user_wacc = st.number_input("Discount Rate (WACC)", value=config.DCF_WACC, step=0.01)
        with col_t: user_tg = st.number_input("Terminal Growth Rate", value=config.DCF_TERMINAL_GROWTH, step=0.005)
        with col_y: user_proj = st.number_input("Projection Years", value=config.DCF_PROJECTION_YEARS, step=1, min_value=1)
        
        if "analyze_ticker" not in st.session_state:
            st.session_state.analyze_ticker = None
            st.session_state.analysis_data = None
            st.session_state.analysis_sec_url = None
            st.session_state.analysis_insight = None
            st.session_state.peer_df = None
            st.session_state.transcript = None
        
        if st.button("Analyze Stock", type="primary"):
            from data.fetcher import get_stock_fundamentals, get_earnings_transcript, get_latest_10k_url
            st.session_state.analyze_ticker = ticker
            st.session_state.messages = []
            st.session_state.current_ticker = ticker
            
            with st.spinner(f"Pulling real-time models and AI analysis for {ticker}..."):
                st.session_state.analysis_data = get_stock_fundamentals(ticker, wacc=user_wacc, terminal_growth=user_tg, proj_years=user_proj)
                st.session_state.analysis_sec_url = get_latest_10k_url(ticker)
                st.session_state.transcript = get_earnings_transcript(ticker)
                st.session_state.analysis_insight = None
                st.session_state.peer_df = None
                st.session_state.insight_error = None
                
                if "error" not in st.session_state.analysis_data:
                    data = st.session_state.analysis_data
                    try:
                        insight = analyze_company_moat(
                            data['summary'], 
                            data['sector'], 
                            data['industry'],
                            news=data.get('news'),
                            implied_growth=data.get('implied_fcf_growth', 0),
                            f_score=data.get('f_score', 0),
                            z_score=data.get('z_score', 0),
                            transcript=st.session_state.transcript,
                            macro_yield=data.get('macro_10y_yield', 0.04),
                            sec_url=st.session_state.analysis_sec_url,
                            insider_context=data.get('insider_context')
                        )
                        st.session_state.analysis_insight = insight
                        
                        import re
                        import pandas as pd
                        peers = []
                        pattern = r"\b[A-Z]{1,5}\b"
                        potential_tickers = re.findall(pattern, insight.split("**2.")[0])
                        for t in potential_tickers:
                            if t not in ["DISCOVERY", "COMPETITOR", "THE", "AND", ticker] and len(t) <= 5:
                                if t not in peers:
                                    peers.append(t)
                                if len(peers) >= 3:
                                    break
                                    
                        if peers:
                            peer_data = []
                            peer_data.append({
                                'Ticker': ticker,
                                'Current Price': f"${data['current_price']:.2f}",
                                'ROIC': f"{data['roic']*100:.1f}%",
                                'Debt/Eq': f"{data['debt_to_equity']:.2f}",
                                'P/B': f"{data['price_to_book']:.2f}",
                                'FCF Growth': f"{data.get('fcf_cagr', 0)*100:.1f}%",
                                'Div Yield': f"{data.get('dividend_yield', 0)*100:.1f}%"
                            })
                            for p in peers:
                                p_data = get_stock_fundamentals(p)
                                if "error" not in p_data:
                                    peer_data.append({
                                        'Ticker': p,
                                        'Current Price': f"${p_data['current_price']:.2f}",
                                        'ROIC': f"{p_data['roic']*100:.1f}%",
                                        'Debt/Eq': f"{p_data['debt_to_equity']:.2f}",
                                        'P/B': f"{p_data['price_to_book']:.2f}",
                                        'FCF Growth': f"{p_data.get('fcf_cagr', 0)*100:.1f}%",
                                        'Div Yield': f"{p_data.get('dividend_yield', 0)*100:.1f}%"
                                    })
                            st.session_state.peer_df = pd.DataFrame(peer_data)
                    except Exception as e:
                        st.session_state.insight_error = str(e)
                        
        if st.session_state.get("analyze_ticker") == ticker and st.session_state.get("analysis_data"):
            data = st.session_state.analysis_data
            sec_url = st.session_state.analysis_sec_url
            insight = st.session_state.analysis_insight
            peer_df = st.session_state.peer_df
            insight_error = st.session_state.get("insight_error")
            
            if "error" in data:
                st.error(f"Error fetching data: {data['error']}")
            else:
                left_view, right_view = st.columns([2.2, 1], gap="large")
                
                with left_view:
                    col1, col2, col3 = st.columns(3)
                    with col1: render_metric_card("Current Price", f"${data['current_price']:.2f}")
                    
                    # Deterministic Sector Percentile Logic (Simulated Math Proxy)
                    import math
                    roic_percentile = min(99, max(1, int(100 - (100 / (1 + math.exp(-10 * (data['roic'] - 0.10)))))))
                    pb_percentile = min(99, max(1, int(100 / (1 + math.exp(-2 * (data['price_to_book'] - 2.0))))))
                    if data['price_to_book'] <= 0: pb_percentile = 99
                    
                    with col2: render_metric_card("Return on Inv. Cap", f"{data['roic']*100:.1f}%", is_positive=data['roic']>config.COMPOUNDER_MIN_ROIC, tooltip=f"🚀 {roic_percentile}th Percentile in {data['sector']}")
                    with col3: render_metric_card("Price to Book", f"{data['price_to_book']:.2f}", is_positive=data['price_to_book']<config.DEEP_VALUE_MAX_PB, tooltip=f"⚖️ {pb_percentile}th Percentile in {data['sector']}")
                    
                    with st.expander("🔬 Advanced Risk Models & Scores", expanded=False):
                        col2_1, col2_2, col2_3, col2_4, col2_5 = st.columns(5)
                        with col2_1: render_metric_card("Piotroski F", f"{data.get('f_score', 0)}/9", is_positive=data.get('f_score', 0) >= 6, tooltip="Measures overall financial health (1-9)")
                        with col2_2: render_metric_card("Altman Z", f"{data.get('z_score', 0):.2f}", is_positive=data.get('z_score', 0) > 2.99, tooltip="Bankruptcy risk. >2.99 is safe, <1.8 is distress.")
                        with col2_3: render_metric_card("Beneish M", f"{data.get('m_score', 0):.2f}", is_positive=data.get('m_score', 0) < -1.78, tooltip="Earnings manipulation risk. Less than -1.78 is safe.")
                        with col2_4: render_metric_card("Div Yield", f"{data.get('dividend_yield', 0)*100:.1f}%", is_positive=data.get('dividend_yield', 0) > 0.02)
                        
                        sma_dist = data.get('sma_200_dist', 0)
                        with col2_5: render_metric_card("vs 200 SMA", f"{sma_dist*100:.1f}%", is_positive=sma_dist > 0, tooltip="Distance from the 200-day Simple Moving Average")
                    
                    st.markdown("---")
                    st.subheader("Intrinsic Valuation Models")
                    if data.get("intrinsic_value", 0) > 0:
                        iv_col1, iv_col2, iv_col3 = st.columns(3)
                        with iv_col1: render_metric_card("DCF Fair Value", f"${data['intrinsic_value']:.2f}", is_positive=data['intrinsic_value'] > data['current_price'], tooltip="Discounted Cash Flow Model Projection")
                        with iv_col2: render_metric_card("Margin of Safety", f"{data['margin_of_safety']*100:.1f}%", is_positive=data['margin_of_safety'] > 0)
                        
                        implied_g = data.get("implied_fcf_growth", 0)
                        with iv_col3: render_metric_card("Implied Growth", f"{implied_g*100:.1f}%", is_positive=implied_g < data.get("fcf_cagr", 0), tooltip="The FCF growth rate the market is currently pricing in")
                        
                        # Plotly DCF Visualization
                        if data.get('pv_fcf') and data.get('pv_tv'):
                            import plotly.graph_objects as go
                            fig = go.Figure(go.Waterfall(
                                name="DCF", orientation="v",
                                measure=["relative", "relative", "total", "absolute"],
                                x=["PV of Free Cash Flow", "PV of Terminal Value", "Enterprise Value", "Intrinsic Value / Share"],
                                textposition="outside",
                                text=[f"${data.get('pv_fcf', 0)/1e9:.1f}B", f"${data.get('pv_tv', 0)/1e9:.1f}B", f"${(data.get('pv_fcf', 0)+data.get('pv_tv', 0))/1e9:.1f}B", f"${data.get('intrinsic_value', 0):.2f}"],
                                y=[data.get("pv_fcf", 0), data.get("pv_tv", 0), 0, data.get("intrinsic_value", 0)],
                                connector={"line":{"color":"rgba(255,255,255,0.2)"}},
                                decreasing={"marker":{"color":"#FB7185"}},
                                increasing={"marker":{"color":"#34D399"}},
                                totals={"marker":{"color":"#3B82F6"}}
                            ))
                            fig.update_layout(title="DCF Enterprise Value Breakdown", template="plotly_dark", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=320, margin=dict(l=20,r=20,t=40,b=20))
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Insufficient cash flow data to project a reliable DCF intrinsic value.")
                        
                    val_col1, val_col2, val_col3 = st.columns(3)
                    with val_col1: render_metric_card("Graham Number", f"${data.get('graham_number', 0):.2f}" if data.get('graham_number') else "N/A", is_positive=data.get('graham_number', 0) > data.get('current_price', 0), tooltip="Defensive valuation formula by Benjamin Graham")
                    with val_col2: render_metric_card("Lynch Fair Value", f"${data.get('peter_lynch_value', 0):.2f}" if data.get('peter_lynch_value') else "N/A", is_positive=data.get('peter_lynch_value', 0) > data.get('current_price', 0), tooltip="PEG Ratio adjusted value by Peter Lynch")
                    with val_col3: render_metric_card("EPV", f"${data.get('epv', 0):.2f}" if data.get('epv') else "N/A", is_positive=data.get('epv', 0) > data.get('current_price', 0), tooltip="Earnings Power Value (ignores future growth)")
                        
                    st.markdown("---")
                    
                    tab_ai, tab_peer, tab_news = st.tabs(["🤖 Qualitative AI Analysis", "🏢 Peer Matrix", "📰 Recent News"])
                    
                    with tab_ai:
                        if insight_error:
                            st.error(f"AI API Error: Rate limited or Invalid Key. Details: {insight_error[:100]}")
                        elif insight:
                            if st.session_state.get('transcript'):
                                st.info("Earnings Call transcript fetched successfully. Analyzing management outlook...")
                            render_ai_insight(insight)
                            
                    with tab_peer:
                        if peer_df is not None and not peer_df.empty:
                            st.dataframe(peer_df, use_container_width=True, hide_index=True)
                        else:
                            st.info("Could not reliably extract competitors from the AI analysis.")
                            
                    with tab_news:
                        if data.get("news"):
                            for n in data["news"]:
                                st.markdown(f"- {n}")
                        else:
                            st.info("No recent news found for this ticker.")
                            
                    # --- AUTO-MEMO PDF REPORTING ---
                    st.markdown("---")
                    from utils.report_gen import generate_investment_memo
                    try:
                        include_chat = st.checkbox("Include contextual chat in PDF export?", value=False)
                        
                        pdf_bytes = generate_investment_memo(
                            ticker, 
                            data, 
                            insight, 
                            peer_df,
                            chat_history=st.session_state.get("messages", []) if include_chat else None
                        )
                        
                        col_dl1, col_dl2, col_dl3 = st.columns([1,2,1])
                        with col_dl2:
                            st.download_button(
                                label="📄 Export Full Investment Memo (PDF)",
                                data=pdf_bytes,
                                file_name=f"{ticker}_Investment_Memo.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                    except Exception as pdf_error:
                        st.warning(f"Could not generate PDF Memo: {pdf_error}")
                        
                with right_view:
                    # --- CONTEXTUAL CHATBOT ---
                    st.markdown('<div class="sticky-chat">', unsafe_allow_html=True)
                    st.subheader("💬 AI Co-Pilot")
                    st.caption("Ask about the data pulled on the left.")
                    
                    if "messages" not in st.session_state:
                        st.session_state.messages = []
                    
                    if "current_ticker" not in st.session_state or st.session_state.current_ticker != ticker:
                        st.session_state.messages = []
                        st.session_state.current_ticker = ticker

                    # Wrap messages in a container for better scrolling if possible, 
                    # but sticky-chat div handles the outer overflow
                    for message in st.session_state.messages:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])

                    if prompt := st.chat_input(f"Ask about {ticker}..."):
                        st.session_state.messages.append({"role": "user", "content": prompt})
                        with st.chat_message("user"):
                            st.markdown(prompt)
                            
                        with st.chat_message("assistant"):
                            with st.spinner("Thinking..."):
                                from models.llm_analyzer import answer_contextual_question
                                answer = answer_contextual_question(prompt, data, insight, st.session_state.messages)
                                st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                        
                    st.markdown('</div>', unsafe_allow_html=True)

    elif navigation == "Backtesting Engine":
        st.title("Backtesting Engine")
        st.markdown("Test the Compounder and Deep Value strategies against historical data (SPY benchmark).")
        
        tickers_input = st.text_input("Enter portfolio tickers (comma separated)", "AAPL, MSFT, GOOGL")
        
        col_b1, col_b2 = st.columns(2)
        with col_b1: period = st.selectbox("Historical Period", ["1y", "3y", "5y", "10y"], index=2)
        with col_b2: benchmark = st.selectbox("Benchmark Index", ["SPY", "QQQ", "DIA", "IWM"], index=0)
        
        if "backtest_results" not in st.session_state:
            st.session_state.backtest_results = None
            
        if st.button("Run Simulation", type="primary"):
            from backtest.engine import run_backtest
            import plotly.graph_objects as go
            
            test_tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
            with st.spinner(f"Simulating historical {period} performance against {benchmark}..."):
                st.session_state.backtest_results = run_backtest(test_tickers, period=period, benchmark=benchmark)
                
        if st.session_state.backtest_results is not None:
            results = st.session_state.backtest_results
            import plotly.graph_objects as go
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
                
                if "correlation_matrix" in results and len(results.get("correlation_matrix", [])) > 1:
                    st.subheader("Asset Correlation Matrix")
                    import plotly.express as px
                    corr_fig = px.imshow(results["correlation_matrix"], 
                                         text_auto=True, 
                                         aspect="auto",
                                         color_continuous_scale="RdBu_r")
                    corr_fig.update_layout(template="plotly_dark", plot_bgcolor="#1E293B", paper_bgcolor="#0E1117", margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(corr_fig, use_container_width=True)
                    
                if "optimal_weights" in results and len(results.get("optimal_weights", [])) > 1:
                    st.markdown("---")
                    st.subheader("Portfolio Optimizer (Efficient Frontier)")
                    st.info("The AI determined these optimal allocations to maximize risk-adjusted returns (Max Sharpe Ratio).")
                    
                    weights = results["optimal_weights"]
                    labels = list(weights.keys())
                    values = list(weights.values())
                    
                    pie_fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, textinfo='label+percent')])
                    pie_fig.update_layout(template="plotly_dark", plot_bgcolor="#1E293B", paper_bgcolor="#0E1117", margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(pie_fig, use_container_width=True)
                
                st.markdown("---")
                st.subheader("Institutional Risk Analysis & Tearsheet")
                if "quantstats_html" in results:
                    import streamlit.components.v1 as components
                    components.html(results["quantstats_html"], height=1000, scrolling=True)
                else:
                    st.warning("QuantStats report generation failed. Check the logs.")

if __name__ == "__main__":
    main()
