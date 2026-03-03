from fpdf import FPDF
import io
import os

class ReportPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'ValueCompass AI: Investment Memo', border=False, ln=1, align='C')
        self.set_line_width(0.5)
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def clean_text(text):
    """Ensure text is latin-1 complient for FPDF to prevent crashing on emojis or special characters"""
    if not text: return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def generate_investment_memo(ticker, data, ai_insight, peers_df=None):
    """
    Generates a PDF investment memo using fpdf2.
    Returns the PDF as a byte stream that Streamlit can download.
    """
    pdf = ReportPDF()
    pdf.add_page()
    
    # Title Section
    pdf.set_font("helvetica", 'B', 20)
    pdf.cell(0, 10, f"{data.get('name', ticker)} ({ticker})", ln=True, align="L")
    
    pdf.set_font("helvetica", 'I', 12)
    pdf.cell(0, 8, f"Sector: {data.get('sector', 'N/A')} | Industry: {data.get('industry', 'N/A')}", ln=True, align="L")
    pdf.ln(5)
    
    # Core Fundamentals
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 8, "1. Core Fundamentals", ln=True)
    pdf.set_font("helvetica", '', 11)
    
    fundamentals = [
        f"Current Price: ${data.get('current_price', 0):.2f}",
        f"ROIC: {data.get('roic', 0)*100:.1f}%",
        f"Dividend Yield: {data.get('dividend_yield', 0)*100:.2f}%",
        f"Debt to Equity: {data.get('debt_to_equity', 0):.2f}",
        f"Price to Book: {data.get('price_to_book', 0):.2f}",
        f"Piotroski F-Score: {data.get('f_score', 0)}/9",
        f"Altman Z-Score: {data.get('z_score', 0):.2f}",
        f"Beneish M-Score: {data.get('m_score', 0):.2f} (<-1.78 implies safety)",
    ]
    for item in fundamentals:
        pdf.cell(0, 6, clean_text(item), ln=True)
    pdf.ln(5)
    
    # Intrinsic Valuation
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 8, "2. DCF Intrinsic Valuation", ln=True)
    pdf.set_font("helvetica", '', 11)
    
    val_items = [
        f"Fair Value (DCF): ${data.get('intrinsic_value', 0):.2f}",
        f"Margin of Safety: {data.get('margin_of_safety', 0)*100:.1f}%",
        f"Market Implied FCF Growth: {data.get('implied_fcf_growth', 0)*100:.1f}%",
        f"Macro 10-Yr Treasury Yield: {data.get('macro_10y_yield', 0.04)*100:.2f}%"
    ]
    for item in val_items:
         pdf.cell(0, 6, clean_text(item), ln=True)
    pdf.ln(5)
    
    # Peer Comparison (if provided)
    if peers_df is not None and not peers_df.empty:
        pdf.set_font("helvetica", 'B', 14)
        pdf.cell(0, 8, "3. Peer Comparison", ln=True)
        pdf.set_font("helvetica", '', 10)
        
        # Simple text representation for FPDF without complex tables
        for index, row in peers_df.iterrows():
            peer_line = f"{row['Ticker']}: Price {row['Current Price']} | ROIC {row['ROIC']} | P/B {row['P/B']} | Div {row['Div Yield']}"
            pdf.cell(0, 6, clean_text(peer_line), ln=True)
        pdf.ln(5)
        
    # AI Qualitative Insight
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 8, "4. Qualitative AI Insight & Moat Analysis", ln=True)
    pdf.set_font("helvetica", '', 10)
    
    # FPDF needs multi_cell for long paragraphs
    clean_insight = clean_text(ai_insight).replace("**", "") # strip markdown bolding
    pdf.multi_cell(0, 6, clean_insight)
    
    # In fpdf2, output(dest='S') returns a bytearray. 
    return bytes(pdf.output(dest="S"))
