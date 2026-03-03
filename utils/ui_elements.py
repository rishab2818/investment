import streamlit as st

def set_premium_css():
    """Inject premium CSS styling into the Streamlit app"""
    st.markdown("""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Main background and fonts */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #020617 100%);
            color: #FAFAFA;
            font-family: 'Inter', sans-serif;
            background-attachment: fixed;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #f8fafc;
            font-weight: 700;
            letter-spacing: -0.025em;
        }
        
        /* Expander Headers */
        .streamlit-expanderHeader {
            background-color: rgba(30, 41, 59, 0.5) !important;
            border-radius: 8px !important;
            border: 1px solid rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            font-weight: 600;
        }
        
        /* Glassmorphism Cards for metrics */
        .metric-card {
            background: rgba(30, 41, 59, 0.4);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.3), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .metric-card:hover {
            transform: translateY(-4px);
            border: 1px solid rgba(56, 189, 248, 0.4);
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4), 0 0 20px rgba(56, 189, 248, 0.1);
        }
        
        .metric-card:hover::before {
            opacity: 1;
        }
        
        /* Value formatting */
        .metric-value {
            font-size: 2.2rem;
            font-weight: 700;
            margin-top: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .metric-label {
            font-size: 0.85rem;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 600;
        }
        
        /* AI Insight Box */
        .ai-insight {
            background: linear-gradient(145deg, rgba(30, 27, 75, 0.7), rgba(49, 46, 129, 0.7));
            backdrop-filter: blur(12px);
            border-left: 4px solid #818CF8;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding: 24px;
            border-radius: 12px;
            margin: 24px 0;
            font-size: 1.05rem;
            line-height: 1.7;
            box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
        }
        
        /* Button styling */
        .stButton>button {
            width: 100%;
            background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 12px 24px;
            font-weight: 600;
            letter-spacing: 0.025em;
            transition: all 0.2s;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4), 0 4px 6px -2px rgba(37, 99, 235, 0.2);
            border-color: rgba(255,255,255,0.3);
        }
        
        /* Sticky Chat container override for columns */
        .sticky-chat {
            position: sticky;
            top: 2rem;
            height: calc(100vh - 4rem);
            overflow-y: auto;
            padding-right: 10px;
        }
        
        /* Custom scrollbar for webkit */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.5);
        }
        ::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #475569;
        }
        </style>
    """, unsafe_allow_html=True)

def render_metric_card(label, value, is_positive=True, tooltip=None):
    """Render a modern glassmorphism metric card with an optional tooltip icon"""
    # Emerald-400 for positive, Rose-400 for negative, Slate-300 for neutral/N/A
    if value == "N/A":
        color = "#CBD5E1"
        icon = ""
    else:
        color = "#34D399" if is_positive else "#FB7185"
        icon = "↑" if is_positive else "↓"
        # don't show arrow if it's a static score like Piotroski that doesn't "trend" this way
        if "Score" in label or "Rating" in label:
             icon = ""
            
    tooltip_html = f"<span title='{tooltip}' style='cursor: help; color: #64748B; margin-left: 6px; font-size: 0.8rem;'>ⓘ</span>" if tooltip else ""
    
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}{tooltip_html}</div>
            <div class="metric-value" style="color: {color};">
                {value}
                <span style="font-size: 1.2rem; opacity: 0.8;">{icon}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_ai_insight(text, title="Gemini AI Analyst Insight"):
    """Render an AI Insight block"""
    st.markdown(f"""
        <div class="ai-insight">
            <h4 style="margin-top: 0; color: #E0E7FF; font-weight: 600; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.4rem;">🤖</span> {title}
            </h4>
            <div style="color: #F1F5F9;">
                {text}
            </div>
        </div>
    """, unsafe_allow_html=True)
