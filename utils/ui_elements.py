import streamlit as st

def set_premium_css():
    """Inject premium CSS styling into the Streamlit app"""
    st.markdown("""
        <style>
        /* Main background and fonts */
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
            font-family: 'Inter', sans-serif;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #E2E8F0;
            font-weight: 600;
        }
        
        /* Cards for metrics */
        .metric-card {
            background-color: #1E293B;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            border: 1px solid #334155;
            transition: transform 0.2s ease-in-out;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            border-color: #3B82F6;
        }
        
        /* Value formatting */
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #10B981; /* Default green, can be overridden */
        }
        .metric-label {
            font-size: 0.9rem;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* AI Insight Box */
        .ai-insight {
            background: linear-gradient(145deg, #1E1B4B, #312E81);
            border-left: 4px solid #6366F1;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            margin-bottom: 20px;
            font-size: 1.05rem;
            line-height: 1.6;
        }
        
        /* Button styling */
        .stButton>button {
            width: 100%;
            background-color: #3B82F6;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 24px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .stButton>button:hover {
            background-color: #2563EB;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)

def render_metric_card(label, value, is_positive=True):
    """Render a styled metric card"""
    color = "#10B981" if is_positive else "#EF4444"
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color: {color};">{value}</div>
        </div>
    """, unsafe_allow_html=True)

def render_ai_insight(text, title="Gemini AI Analyst Insight"):
    """Render an AI Insight block"""
    st.markdown(f"""
        <div class="ai-insight">
            <h4 style="margin-top: 0; color: #A5B4FC;">🤖 {title}</h4>
            {text}
        </div>
    """, unsafe_allow_html=True)
