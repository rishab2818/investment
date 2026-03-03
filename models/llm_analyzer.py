import google.generativeai as genai
import config

def analyze_company_moat(company_summary, sector, industry, news=None, implied_growth=0, f_score=0, z_score=0, transcript=None, macro_yield=0.04, sec_url=None, insider_context=None):
    """
    Uses Gemini to analyze the company's competitive moat, market runway, 
    and R&D/Acquisition potential based on standard business summary, news, SEC 10-Ks, and transcripts.
    """
    if not company_summary or company_summary == "No summary available.":
         return "Insufficient data to provide AI analysis."
         
    news_context = ""
    if news:
        news_context = "Recent News Headlines:\n" + "\n".join([f"- {n}" for n in news])
        
    transcript_context = ""
    if transcript:
        transcript_context = f"Recent Earnings Call Transcript Snippet:\n{transcript}\n"
        
    sec_context = ""
    if sec_url:
        sec_context = f"The most recent SEC 10-K filing can be found here (for contextual knowledge only): {sec_url}\n"
        
    insider_data = ""
    if insider_context:
        insider_data = f"Recent Insider Trading Activity (Last 5 transactions):\n{insider_context}\n"
         
    prompt = f"""
    You are an expert institutional equity analyst.
    Please analyze the following company in the {sector} sector ({industry} industry).
    
    Business Summary:
    {company_summary}
    
    {news_context}
    
    {transcript_context}
    
    {sec_context}
    
    {insider_data}
    
    Quantitative & Macro Context:
    - 10-Year Treasury Yield (Risk-Free Rate): {macro_yield*100:.2f}%
    - Piotroski F-Score (0-9): {f_score} (Measures financial health trend)
    - Altman Z-Score: {z_score:.2f} (Bankruptcy risk, <1.8 is high risk, >3 is safe)
    - Market Implied FCF Growth (Reverse DCF): {implied_growth*100:.1f}%
    
    Provide a concise, highly-structured qualitative analysis with the following explicit sections:
    
    **1. Competitor Discovery**
    Identify exactly 3 publicly traded, direct competitors to this company. Format them strictly as a comma-separated list of ticker symbols (e.g., MSFT, GOOGL, AMZN).
    
    **2. Deep Sentiment & Management Tone (Dissonance Analysis)**
    Based on the Transcript snippet, provide a strict "Tone Score" (e.g., Highly Optimistic, Cautiously Optimistic, Defensive, Evasive). Specifically, analyze the "Dissonance" between the PREPARED REMARKS and the Q&A SESSION. Does management sound confident in their script but evasive or defensive when pressed by analysts? Extract 1-2 short quote snippets that prove your assessment.
    
    **3. Economic Moat & Macro Impact**
    Does it possess network effects, switching costs, or intangible assets? Furthermore, how does the current {macro_yield*100:.2f}% Risk-Free rate impact their debt or specific business model?
    
    **4. Deep Value & Expectations**
    Incorporate the F-Score ({f_score}) and Z-Score ({z_score:.2f}) into an assessment of turnaround probability. Is it realistic for the company to achieve the {implied_growth*100:.1f}% FCF growth rate baked into the current stock price?
    
    **5. Structural Risk Factors (SEC 10-K Context)**
    Identify 2-3 specific, existential, or structural risk factors associated with this company's business model or supply chain (excluding generic market risks). If an SEC 10-K URL is provided, base your assessment heavily on expected "Item 1A" disclosures for this industry type.
    
    **6. Supply Chain & Customer Concentration**
    Explicitly analyze the company's supply chain and customer base. Are they highly vulnerable to single-point-of-failure geopolitical regions (e.g., Taiwan, China) or overly reliant on a monolithic customer (e.g., Apple)? 
    
    **7. Insider Trade Conviction**
    Review the Recent Insider Trading Activity provided. Grade the "Conviction" of these trades. For example, a CEO buying heavily in the open market is a high-conviction bullish signal, whereas a retiring board member selling predetermined shares is low-conviction noise.
    
    Keep the tone professional and objective. Do not provide financial advice.
    """
    
    try:
        if config.AI_PROVIDER == "openai":
            if not config.OPENAI_API_KEY:
                return "OpenAI API Key is missing. Please add it in the sidebar."
            import openai
            client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert institutional equity analyst. Keep your tone professional and objective. Do not provide financial advice. Limit the response to 4 short paragraphs."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        else:
            if not config.GEMINI_API_KEY:
                return "Gemini API Key is missing. Please add it in the sidebar."
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        return f"AI Analysis Error: Ensure your API Key is correct and you have credits. ({e})"

def answer_contextual_question(question, data, insight, chat_history):
    """
    Answers user questions based on the financial data, AI insight, and previous chat history.
    """
    history_str = ""
    for msg in chat_history:
        history_str += f"{msg['role'].capitalize()}: {msg['content']}\n"
        
    prompt = f"""
    You are an expert institutional equity analyst Assistant.
    A user is asking you a question about the following company: {data.get('name', data.get('ticker'))} ({data.get('ticker')}).
    
    Here is the quantitative data context:
    - Current Price: ${data.get('current_price', 0):.2f}
    - Intrinsic Value (DCF): ${data.get('intrinsic_value', 0):.2f}
    - Margin of Safety: {data.get('margin_of_safety', 0)*100:.1f}%
    - ROIC: {data.get('roic', 0)*100:.1f}%
    - debt_to_equity: {data.get('debt_to_equity', 0):.2f}
    - FCF Growth: {data.get('fcf_cagr', 0)*100:.1f}%
    - P/B: {data.get('price_to_book', 0):.2f}
    - Z-Score: {data.get('z_score', 0):.2f}
    - F-Score: {data.get('f_score', 0)}/9
    - Dividend Yield: {data.get('dividend_yield', 0)*100:.2f}%
    - Graham Number: ${data.get('graham_number', 0):.2f}
    - Peter Lynch Fair Value: ${data.get('peter_lynch_value', 0):.2f}
    - Earnings Power Value (EPV): ${data.get('epv', 0):.2f}
    - Sector: {data.get('sector', 'N/A')}
    
    Here is the previous AI Insight context:
    {insight}
    
    Previous Chat History:
    {history_str}
    
    User Question: {question}
    
    Provide a professional, concise answer. Analyze the numbers critically to explain why a metric might be high or low. Do not provide deterministic financial advice.
    """
    try:
        if config.AI_PROVIDER == "openai":
            if not config.OPENAI_API_KEY:
                return "OpenAI API Key is missing. Please add it in the sidebar."
            import openai
            client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a financial analyst chatbot. Keep your tone professional and objective."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        else:
            if not config.GEMINI_API_KEY:
                return "Gemini API Key is missing. Please add it in the sidebar."
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        return f"Chat Error: {e}"

def generate_portfolio_constraints(portfolio_tickers, user_prefs, fundamental_data, news_data=None):
    """
    Asks the LLM to return specific weight bounds (min, max) for tickers based on user preferences and recent news.
    Also parses explicit Sector boundary requests from the user's text.
    """
    ticker_context = ""
    for t in portfolio_tickers:
        data = fundamental_data.get(t, {})
        news_str = ""
        if news_data and t in news_data and news_data[t]:
            news_str = f" | RECENT NEWS: " + " ; ".join(news_data[t])
            
        ticker_context += f"- {t}: Sector={data.get('sector', 'N/A')}, P/B={data.get('price_to_book', 'N/A')}, Div Yield={data.get('dividend_yield', 0)*100:.1f}%, ROIC={data.get('roic', 0)*100:.1f}%{news_str}\n"

    prompt = f"""
    You are an AI Quantitative Analyst configuring constraints for a Markowitz Mean-Variance Optimizer.
    
    User Portfolio Tickers: {', '.join(portfolio_tickers)}
    User Preferences / Goals:
    {user_prefs}
    
    Fundamental Context & Live News:
    {ticker_context}
    
    Based on the User's qualitative goals and live news, output a strictly formatted JSON parsing the absolute mathematical boundaries for the optimization matrix.
    
    RULES:
    1. If the RECENT NEWS for a ticket indicates a severe black swan event (e.g., bankruptcy risk, major SEC probe, unexpected CEO resignation), you MUST set its max_weight to 0.0 to liquidate it.
    2. Read the "User Preferences". If they explicitly ask to cap or floor a specific SECTOR (e.g., "Max 20% in Technology"), translate that into the `sector_bounds` dictionary. If not specified, leave `sector_bounds` empty.
    3. Determine `ticker_bounds` `[min_weight, max_weight]` between 0.0 and 1.0 for each specific asset based on their alignment with the user's goals. Default bounds if no strong opinion is [0.0, 0.40].
    
    Output ONLY valid JSON. No markdown formatting, no explanations. 
    Example Format:
    {{
        "ticker_bounds": {{
            "AAPL": [0.0, 0.4],
            "XOM": [0.0, 0.0]  // E.g., if user banned fossil fuels or bad news hit
        }},
        "sector_bounds": {{
            "Technology": [0.0, 0.20],  // E.g., if user said "Max 20% in Tech"
            "Energy": [0.05, 1.0]       // E.g., if user said "I want at least 5% Energy"
        }}
    }}
    """
    
    try:
        import json
        if config.AI_PROVIDER == "openai":
            import openai
            client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.choices[0].message.content.strip()
        else:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            text = response.text.strip()
            
        # Clean up possible markdown code blocks
        if text.startswith("```json"): text = text[7:]
        if text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        
        return json.loads(text)
    except Exception as e:
        # Fallback to no overrides
        return {}

def generate_portfolio_narrative(original_weights, proposed_weights, user_prefs, metrics, original_metrics=None, optimized_metrics=None):
    """
    Generates the final Robo-Advisor narrative explaining the rebalance.
    """
    orig_str = ", ".join([f"{k}: {v*100:.1f}%" for k, v in original_weights.items() if v > 0.01])
    prop_str = ", ".join([f"{k}: {v*100:.1f}%" for k, v in proposed_weights.items() if v > 0.01])
    
    perf_context = ""
    if original_metrics and optimized_metrics:
        perf_context = f"""
        Historical Backtest Context (Last 5 Years):
        - Original Portfolio: {original_metrics.get('annual_return', 0)*100:.1f}% Annualized Return, {original_metrics.get('sharpe', 0):.2f} Sharpe Ratio, {original_metrics.get('max_drawdown', 0)*100:.1f}% Max Drawdown.
        - AI Optimized Portfolio: {optimized_metrics.get('annual_return', 0)*100:.1f}% Annualized Return, {optimized_metrics.get('sharpe', 0):.2f} Sharpe Ratio, {optimized_metrics.get('max_drawdown', 0)*100:.1f}% Max Drawdown.
        """
        
    prompt = f"""
    You are an expert, white-glove Robo-Advisor explaining a portfolio rebalance to a client.
    
    Their stated goals and preferences:
    "{user_prefs}"
    
    Their Original Allocation:
    {orig_str}
    
    The AI/Math Proposed Optimial Allocation:
    {prop_str}
    
    {perf_context}
    
    Write a highly professional, reassuring, and analytical 3-4 paragraph memo explaining EXACTLY why you shifted their money the way you did. 
    Connect the mathematical shifts directly to their stated qualitative goals (e.g., "To achieve your goal of capital preservation, I reduced your exposure to TSLA from 40% to 10% and reallocated it to lower-volatility dividend payers...").
    If the historical backtest metrics are provided, explicitly mention how the new portfolio historically provided a better Sharpe ratio (risk-adjusted return) or lower drawdown.
    Do not give direct financial advice, frame it as an analytical proposal.
    """
    
    try:
        if config.AI_PROVIDER == "openai":
            import openai
            client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        else:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        return f"Narrative Generation Error: {str(e)}"
