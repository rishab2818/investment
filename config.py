import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configuration settings for the AI Stock Screener

# API Keys
# You can change this or set it as an environment variable
# Best Practice: create a .env file locally with GEMINI_API_KEY="your-key"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Initialize Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error configuring Gemini: {e}")

# Screener Thresholds

# 1. Compounder Strategy Thresholds
COMPOUNDER_MIN_ROIC = 0.15      # 15% MIN ROIC
COMPOUNDER_MIN_FCF_CAGR = 0.08  # 8% MIN FCF Growth
COMPOUNDER_MAX_DEBT_EQ = 1.0    # 1.0 Max Debt to Equity

# 2. Deep Value Strategy Thresholds
DEEP_VALUE_MAX_PB = 1.5         # Max Price/Book
DEEP_VALUE_MIN_RD_REV = 0.10    # 10% Min R&D to Revenue
DEEP_VALUE_PRICE_DROP = 0.30    # 30% drop from 52w High

# 3. DCF Valuation Constants
DCF_WACC = 0.09               # 9% Discount Rate (Cost of Capital)
DCF_TERMINAL_GROWTH = 0.025   # 2.5% Terminal Growth Rate
DCF_PROJECTION_YEARS = 5      # 5 Year Projection Period

# Application Constants
APP_TITLE = "ValueCompass AI"
APP_SUBTITLE = "Institutional-Grade Equities Intelligence"

# Default testing tickers if needed
DEFAULT_TICKERS = [
    "AAPL",   # Apple Inc. – Consumer electronics / Technology
    "MSFT",   # Microsoft Corp. – Software / Cloud
    "NVDA",   # NVIDIA Corp. – Semiconductors / AI chips
    "AMZN",   # Amazon.com Inc. – E-commerce / Cloud (AWS)
    "GOOGL",  # Alphabet Inc. – Search / Digital advertising
    "META",   # Meta Platforms Inc. – Social media / Ads
    "BRK-B",  # Berkshire Hathaway – Conglomerate / Insurance
    "JPM",    # JPMorgan Chase – Banking / Financial services
    "XOM",    # Exxon Mobil – Oil & Gas
    "UNH"     # UnitedHealth Group – Healthcare / Insurance
]
# DEFAULT_TICKERS = [
# "AAPL","MSFT","AMZN","NVDA","GOOGL","GOOG","META","BRK-B","LLY","AVGO",
# "TSLA","JPM","UNH","V","XOM","MA","HD","PG","COST","ABBV",
# "MRK","PEP","KO","ADBE","CRM","WMT","AMD","MCD","BAC","NFLX",
# "LIN","ACN","TMO","CSCO","ABT","INTC","CMCSA","DIS","VZ","DHR",
# "TXN","NEE","WFC","PM","RTX","AMGN","UPS","HON","BMY","LOW",
# "QCOM","IBM","INTU","SPGI","CAT","GS","BLK","BA","GE","ISRG",
# "MDT","AMAT","NOW","BKNG","ELV","PLD","LMT","GILD","DE","ADP",
# "SYK","T","AXP","MDLZ","C","REGN","TJX","VRTX","ADI","CB",
# "MMC","ETN","ZTS","PGR","TMUS","SO","DUK","PANW","BSX","CL",
# "MO","EQIX","CI","ICE","APD","ITW","MU","CDNS","HCA","SHW",
# "EOG","KLAC","SNPS","WM","MCK","MPC","NOC","FDX","AON","ORLY",
# "EMR","CME","TGT","APH","CSX","GD","USB","PSA","MAR","PXD",
# "EW","NXPI","FCX","GM","ROP","NSC","ADSK","MSI","AEP","TRV",
# "AJG","MET","SRE","F","CTAS","AIG","PCAR","AZO","HUM","AFL",
# "OXY","SPG","PAYX","PH","ROST","ALL","CMG","STZ","D","MNST",
# "KMB","KMI","A","CHTR","AEE","WMB","FAST","MS","VLO","AMP",
# "CCI","PRU","BK","COR","IDXX","TEL","PSX","GIS","CARR","EXC",
# "LRCX","ODFL","KDP","YUM","DD","GPN","EA","CSGP","CTSH",
# "RSG","BKR","EL","SLB","VRSK","HAL","NEM","PEG","ED","PCG",
# "ANET","TT","DOW","DFS","OKE","KR","WEC","DLR","MTB","SBAC",
# "ILMN","VICI","KEYS","ROK","FIS","ON","PPG","RMD","STT","CDW",
# "ABC","FANG","SYY","AWK","GLW","EFX","CPRT","CTRA","WST","ECL",
# "BIIB","LEN","WTW","GWW","IFF","HIG","DLTR","HSY","HPQ","DVN",
# "DAL","TROW","DTE","TSCO","FITB","ZBRA","EIX","ULTA","ETR","WBA",
# "PPL","CFG","LYB","HBAN","MLM","RF","HPE","PFG","FE","MKC",
# "CLX","FISV","CMS","STE","LH","VTR","EXR","NUE","PWR","BR",
# "ZBH","CNC","COF","CNP","NDAQ","AES","IRM","MCHP","WAT","CAH",
# "TDG","ARE","HUBB","BBY","ALB","K","WRB","HWM","DG","PTC",
# "INVH","MTD","PAYC","NVR","CTVA","AVB","LUV","ROL","CBOE","BRO",
# "EXPE","DRI","CHD","AIZ","WDC","JBHT","IEX","PKG","MRNA","RCL",
# "SBNY","IP","LKQ","OMC","TPR","TXT","POOL","SNA","JKHY","FMC",
# "NRG","RE","AKAM","TER","CRL","UDR","ESS","CE","MOS","LVS",
# "VRSN","SWK","CF","HST","TAP","HOLX","TRMB","XRAY","KIM","APA",
# "FRT","REG","MRO","NI","L","ALGN","INCY","MAA","CMA","WELL",
# "RJF","BEN","GL","HAS","UHS","NTRS","PARA","NWL","WY","GNRC"
# ]