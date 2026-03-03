import google.generativeai as genai
import config

def analyze_company_moat(company_summary, sector, industry, news=None, implied_growth=0, f_score=0, z_score=0):
    """
    Uses Gemini to analyze the company's competitive moat, market runway, 
    and R&D/Acquisition potential based on standard business summary.
    """
    if not company_summary or company_summary == "No summary available.":
         return "Insufficient data to provide AI analysis."
         
    news_context = ""
    if news:
        news_context = "Recent News Headlines:\n" + "\n".join([f"- {n}" for n in news])
         
    prompt = f"""
    You are an expert institutional equity analyst.
    Please analyze the following company in the {sector} sector ({industry} industry).
    
    Business Summary:
    {company_summary}
    
    {news_context}
    
    Quantitative Context:
    - Piotroski F-Score (0-9): {f_score} (Measures financial health trend)
    - Altman Z-Score: {z_score:.2f} (Bankruptcy risk, <1.8 is high risk, >3 is safe)
    - Market Implied FCF Growth (Reverse DCF): {implied_growth*100:.1f}%
    
    Provide a concise, highly-structured qualitative analysis focusing strictly on:
    1. Economic Moat: Does it possess network effects, switching costs, cost advantages, or intangible assets?
    2. Deep Value Catalysts & Financial Health: Incorporate the F-Score and Z-Score into your assessment of its survival and turnaround probability.
    3. Market Expectations: Is it realistic for the company to achieve the {implied_growth*100:.1f}% FCF growth rate baked into the current stock price?
    
    Keep the tone professional and objective. Do not provide financial advice. Limit the response to 3 short paragraphs.
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Analysis Error: Ensure GEMINI_API_KEY is correct. ({e})"
