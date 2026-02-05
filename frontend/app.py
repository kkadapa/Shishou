import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import os
import sys

# Add backend to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from evaluator import Evaluator

from dotenv import load_dotenv

# Load env vars
load_dotenv()

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Hackalytics",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS: ROBOTIC CYBERPUNK THEME ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Roboto+Mono:wght@300;400;700&display=swap');

    /* BACKGROUND & GLOBAL VARIABLES */
    :root {
        --neon-cyan: #00F2FF;
        --neon-magenta: #FF00E5;
        --dark-bg: #050505;
        --grid-line: rgba(0, 242, 255, 0.1);
        --glass-bg: rgba(5, 5, 5, 0.7);
    }

    .stApp {
        background-color: var(--dark-bg);
        background-image: 
            linear-gradient(var(--grid-line) 1px, transparent 1px),
            linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
        background-size: 40px 40px;
        background-position: center center;
        font-family: 'Roboto Mono', monospace;
        color: #E0E0E0;
    }
    
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: white;
        text-shadow: 0 0 10px var(--neon-cyan);
    }

    /* ROBOTIC FACE ANIMATION */
    @keyframes flash {
        0% { filter: brightness(1) drop-shadow(0 0 5px var(--neon-cyan)); opacity: 0.9; }
        5% { filter: brightness(1.5) drop-shadow(0 0 15px var(--neon-cyan)); opacity: 1; }
        10% { filter: brightness(1) drop-shadow(0 0 5px var(--neon-cyan)); opacity: 0.9; }
        15% { filter: brightness(1.2) drop-shadow(0 0 10px var(--neon-cyan)); opacity: 1; }
        50% { filter: brightness(1) drop-shadow(0 0 5px var(--neon-cyan)); opacity: 0.8; }
        52% { opacity: 0.4; }
        54% { opacity: 0.8; }
        100% { filter: brightness(1) drop-shadow(0 0 5px var(--neon-cyan)); opacity: 0.9; }
    }
    
    .robotic-hero {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 180px;
        animation: flash 4s infinite linear;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #0A0A0A;
        border-right: 1px solid var(--neon-cyan);
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
         color: #E0E0E0 !important;
    }

    /* INPUTS */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea {
        background-color: rgba(0, 0, 0, 0.5);
        border: 1px solid #333;
        color: var(--neon-cyan);
        font-family: 'Roboto Mono', monospace;
        caret-color: var(--neon-magenta) !important;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus, 
    .stTextArea > div > div > textarea:focus {
        border-color: var(--neon-cyan);
        box-shadow: 0 0 10px rgba(0, 242, 255, 0.3);
        color: white;
    }

    /* BUTTONS */
    .stButton > button {
        background: linear-gradient(45deg, #00C2CC, #00F2FF);
        color: #000;
        font-family: 'Orbitron', sans-serif;
        font-weight: bold;
        border: none;
        border-radius: 0;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px var(--neon-cyan);
        color: #000;
    }

    /* EXPANDERS */
    .streamlit-expanderHeader {
        background-color: rgba(10, 10, 10, 0.8) !important;
        border: 1px solid var(--neon-cyan) !important;
        border-radius: 4px;
        color: var(--neon-cyan) !important;
        font-family: 'Orbitron', sans-serif;
    }
    .streamlit-expanderHeader:hover {
        background-color: rgba(0, 242, 255, 0.1) !important;
        color: white !important;
    }
    div[data-testid="stExpander"] details > summary p,
    div[data-testid="stExpander"] details > summary span,
    div[data-testid="stExpander"] details > summary svg {
        color: var(--neon-cyan) !important;
        fill: var(--neon-cyan) !important;
    }

    /* DRAG & DROP */
    [data-testid="stFileUploader"] {
        border: 1px dashed var(--neon-cyan);
        background-color: rgba(0, 242, 255, 0.05);
        padding: 20px;
    }
    /* File Uploader Text */
    [data-testid="stFileUploaderDropzone"] div, 
    [data-testid="stFileUploaderDropzone"] span, 
    [data-testid="stFileUploaderDropzone"] small {
        color: #E0E0E0 !important;
    }

    /* ALERTS */
     div[data-baseweb="alert"] {
         border-radius: 0;
         background-color: rgba(0, 0, 0, 0.8);
         border: 1px solid var(--neon-cyan);
         color: white;
    }
</style>
""", unsafe_allow_html=True)

# Helper for image encoding
import base64
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Sidebar for Setup
with st.sidebar:
    # Try to verify keys exist
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    st.markdown("<h3 style='color: var(--neon-cyan);'>SYSTEM ID</h3>", unsafe_allow_html=True)
    
    if groq_key and gemini_key:
        st.success("ACCESS GRANTED ✅")
    else:
        st.error("ACCESS DENIED ❌")
        st.info("Please add keys to .env")
    
    st.markdown("---")
    st.markdown("### PROTOCOL")
    st.info("Scanning for Novelty, Tech Stack, and Visual Patterns.")

# Render Hero
try:
    img_b64 = get_base64_of_bin_file("frontend/assets/robotic_face.png")
    st.markdown(
        f'<img src="data:image/png;base64,{img_b64}" class="robotic-hero">',
        unsafe_allow_html=True
    )
except FileNotFoundError:
    st.warning("⚠️ Asset missing: robotic_face.png")

st.markdown("<h1 style='text-align: center; color: white;'>HACKALYTICS_V2.0</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #00F2FF; letter-spacing: 4px; font-family: Orbitron;'>AI JUDGEMENT SYSTEM_ONLINE</p>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("INPUT_DATA_STREAM")
    project_desc = st.text_area("Project Description", height=200, placeholder="Initialize project parameters...")
    tech_stack = st.text_area("Tech Stack", height=100, placeholder="Define system dependencies...")

with col2:
    st.subheader("VISUAL_INPUT")
    uploaded_file = st.file_uploader("Upload Interface", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Visual Data Received", use_column_width=True)
        # Save temp file for evaluator
        with open("temp_image.png", "wb") as f:
            f.write(uploaded_file.getbuffer())
        image_path = "temp_image.png"
    else:
        image_path = None

@st.cache_resource
def get_evaluator(groq_key, gemini_key):
    return Evaluator(groq_api_key=groq_key, gemini_api_key=gemini_key)

if st.button("EXECUTE EVALUATION 🚀", type="primary"):
    if not groq_key or not gemini_key:
        st.error("MISSING CREDENTIALS")
    elif not project_desc or not tech_stack:
        st.warning("INSUFFICIENT DATA")
    else:
        try:
            with st.spinner("PROCESSING..."):
                evaluator = get_evaluator(groq_key, gemini_key)
                results = evaluator.audit_project(project_desc, tech_stack, image_path)
                
                # Cleanup temp image
                if image_path and os.path.exists(image_path):
                    os.remove(image_path)

            # Display Results
            st.divider()
            
            # Top Level Score
            score_col1, score_col2 = st.columns([1, 2])
            with score_col1:
                st.metric(label="TOTAL SCORE", value=f"{results['S_total']:.1f} / 10")
                if results['S_total'] >= 8.5:
                    st.success("EXCEPTIONAL")
                elif results['S_total'] >= 6.0:
                    st.warning("OPTIMIZATION REQUIRED")
                else:
                    st.error("CRITICAL FAILURE")
            
            with score_col2:
                # Radar Chart
                categories = ['Novelty', 'Tech', 'Impact', 'Viability', 'AI', 'Design']
                metrics = results['metrics']
                values = [
                    metrics['S_nov'], metrics['S_tech'], metrics['S_imp'], 
                    metrics['S_via'], metrics['S_ai'], metrics['S_des']
                ]
                
                fig = go.Figure(data=go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name='Project Score',
                    line=dict(color='#00F2FF'),
                    fillcolor='rgba(0, 242, 255, 0.2)'
                ))
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', family="Orbitron"),
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 10],
                            tickfont=dict(color='white')
                        ),
                        bgcolor='rgba(255,255,255,0.05)'
                    ),
                    showlegend=False,
                    height=350,
                    margin=dict(l=40, r=40, t=20, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)

            # Detailed Breakdown
            st.subheader("🔍 LOGS: AI_BREAKDOWN")
            ai_breakdown = results['ai_breakdown']
            
            ai_cols = st.columns(4)
            ai_cols[0].metric("RAG", f"{ai_breakdown['I_rag']}/5")
            ai_cols[1].metric("Agent", f"{ai_breakdown['I_agent']}/5")
            ai_cols[2].metric("Fine-Tuning", f"{ai_breakdown['I_ft']}/5")
            ai_cols[3].metric("Safety", f"{ai_breakdown['I_safety']}/5")
            
            st.info(f"**ANALYSIS:** {results['reasoning']['ai']}")

            # Other Reasonings
            with st.expander("VIEW: GENERAL_ANALYSIS"):
                st.write(results['reasoning']['general'])
                
            with st.expander("VIEW: DESIGN_ANALYSIS"):
                st.write(results['reasoning']['design'])

            # Similarity Check
            st.subheader("📚 RELEVANT ARCHIVES")
            similar_projects = results.get('similar_projects', [])
            if similar_projects:
                for i, proj in enumerate(similar_projects[:3]):
                    with st.container():
                        st.markdown(f"**{i+1}. {proj['title']}** (Similarity: {proj['similarity']:.2f})")
                        st.caption(proj['description'][:200] + "...")
                        if proj['url']:
                            st.markdown(f"[ACCESS DATA]({proj['url']})")
                        st.divider()
            else:
                st.write("NO MATCHES FOUND.")

        except Exception as e:
            st.error(f"SYSTEM ERROR: {str(e)}")
            st.exception(e)
