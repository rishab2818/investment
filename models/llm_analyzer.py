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
