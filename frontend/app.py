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

# Page Configuration
st.set_page_config(
    page_title="Hackalytics - AI Hackathon Judge",
    page_icon="🏆",
    layout="wide"
)

# Custom Theme (Organic Glassmorphism - Polished)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1A1A1A; /* Force dark text globally */
    }

    /* Organic Background */
    .stApp {
        background-color: #EBE0D6;
        background-image: 
            radial-gradient(at 0% 0%, rgba(244, 176, 164, 0.4) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(142, 169, 219, 0.4) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(168, 208, 141, 0.4) 0px, transparent 50%);
        color: #1A1A1A;
    }
    
    /* Transparent Header */
    header[data-testid="stHeader"], .stApp > header {
        background-color: transparent !important;
    }

    /* Labels & Headers - Force Dark Check */
    .stTextInput label, .stTextArea label, .stFileUploader label, label, p, h1, h2, h3, h4, 
    .stMarkdown, [data-testid="stMetricLabel"] {
        color: #1A1A1A !important;
    }

    /* Glass Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(25px);
        border-right: 1px solid rgba(255, 255, 255, 0.6);
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
         color: #1A1A1A !important;
    }
    
    /* Inputs & Textareas */
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea {
        background-color: rgba(255, 255, 255, 0.9) !important; /* Lighter background */
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: #1A1A1A !important; /* Dark text in inputs */
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .stTextInput > div > div > input::placeholder, 
    .stTextArea > div > div > textarea::placeholder {
        color: #666666 !important;
    }
    
    /* Focus State */
    .stTextInput > div > div > input:focus, 
    .stTextArea > div > div > textarea:focus {
        border: 1px solid #A8D08D;
        box-shadow: 0 0 0 2px rgba(168, 208, 141, 0.2);
        caret-color: #1A1A1A; /* Fix invisible cursor */
    }
    
    /* Input General State - ensure caret is always dark */
    .stTextInput input, .stTextArea textarea {
        caret-color: #1A1A1A !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #A8D08D 0%, #8EA9DB 100%);
        color: #1A1A1A !important;
        border: none;
        border-radius: 30px;
        font-weight: 800;
        padding: 0.7rem 2.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 8px 15px rgba(168, 208, 141, 0.4);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #97C07C 0%, #7D98CA 100%);
        transform: translateY(-2px);
        box-shadow: 0 12px 20px rgba(168, 208, 141, 0.6);
        color: #000000 !important;
    }
    
    /* File Uploader - Fix Dark Background & Text */
    [data-testid="stFileUploader"] {
        background-color: rgba(255, 255, 255, 0.6);
        border-radius: 16px;
        padding: 0; 
    }
    [data-testid="stFileUploader"] section {
        background-color: transparent !important; /* Remove internal dark block */
    }
    [data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzone"] {
        background-color: rgba(255, 255, 255, 0.6) !important;
        color: #1A1A1A !important;
        border: 1px dashed #A8D08D;
        border-radius: 12px;
    }
    /* Force text color in dropzone */
    [data-testid="stFileUploaderDropzone"] div, 
    [data-testid="stFileUploaderDropzone"] span, 
    [data-testid="stFileUploaderDropzone"] small {
        color: #1A1A1A !important;
    }
    [data-testid="stFileUploaderDropzone"] svg {
        fill: #1A1A1A !important;
    }
    /* Small Button inside uploader */
    [data-testid="stFileUploader"] button {
        background-color: #FFFFFF !important;
        color: #1A1A1A !important;
        border: 1px solid #E0E0E0 !important;
    }
    
    /* Expander - Aggressive Override */
    div[data-testid="stExpander"] details > summary {
        background-color: rgba(255, 255, 255, 0.6) !important;
        border-radius: 8px !important;
        color: #1A1A1A !important;
    }
    div[data-testid="stExpander"] details[open] > summary {
        background-color: rgba(255, 255, 255, 0.8) !important;
        color: #1A1A1A !important;
    }
    div[data-testid="stExpander"] details > summary:hover {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #1A1A1A !important;
    }
    
    /* Force internal text/icons to be dark */
    div[data-testid="stExpander"] details > summary p,
    div[data-testid="stExpander"] details > summary span,
    div[data-testid="stExpander"] details > summary div {
        color: #1A1A1A !important;
    }
    div[data-testid="stExpander"] details > summary svg {
        fill: #1A1A1A !important;
        color: #1A1A1A !important;
    }
    
    /* Metric Value */
    [data-testid="stMetricValue"] {
        color: #1A1A1A !important;
    }
    
    /* Success/Error/Info Messages */
    .stAlert {
        background-color: rgba(255, 255, 255, 0.8) !important;
        color: #1A1A1A !important;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.5);
    }
    .stAlert p {
        color: #1A1A1A !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for Setup
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=50)
    st.title("Hackalytics Config")
    
    # Keys loaded from .env
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if groq_key and gemini_key:
        st.success("API Keys Loaded ✅")
    else:
        st.error("Missing API Keys in .env")
        st.info("Please add GROQ_API_KEY and GEMINI_API_KEY to your .env file.")
    
    st.markdown("---")
    st.markdown("### How it Works")
    st.info("Uses RAG (FAISS + Gemini Embeddings) for Novelty. Uses Gemini 1.5 Pro for Design. Uses Groq (Llama 3) for Tech & Viability.")

# Main Layout
st.title("🏆 Hackalytics: AI Project Judge")
st.markdown("### Evaluate your hackathon idea against thousands of winners.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Project Details")
    project_desc = st.text_area("Project Description & Pitch", height=200, placeholder="Describe your project, the problem it solves, and its features...")
    tech_stack = st.text_area("Technical Stack", height=100, placeholder="e.g., Python, Streamlit, LangChain, FAISS, Gemini...")

with col2:
    st.subheader("Visuals (Optional)")
    uploaded_file = st.file_uploader("Upload UI Screenshot", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded UI", use_column_width=True)
        # Save temp file for evaluator
        with open("temp_image.png", "wb") as f:
            f.write(uploaded_file.getbuffer())
        image_path = "temp_image.png"
    else:
        image_path = None

@st.cache_resource
def get_evaluator(groq_key, gemini_key):
    return Evaluator(groq_api_key=groq_key, gemini_api_key=gemini_key)

if st.button("Evaluate Project 🚀", type="primary"):
    if not groq_key or not gemini_key:
        st.error("Missing API Keys. Please check your .env file.")
    elif not project_desc or not tech_stack:
        st.warning("Please provide both a description and a tech stack.")
    else:
        try:
            with st.spinner("Crunching numbers... checking novelty... analyzing UI..."):
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
                st.metric(label="Total Score (S_total)", value=f"{results['S_total']} / 10")
                if results['S_total'] >= 8.5:
                    st.success("Potential Winner! 🏆")
                elif results['S_total'] >= 6.0:
                    st.warning("Strong Contender 🥈")
                else:
                    st.error("Needs Improvement 🛠️")
            
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
                    name='Project Score'
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 10]
                        )),
                    showlegend=False,
                    height=350,
                    margin=dict(l=40, r=40, t=20, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)

            # Detailed Breakdown
            st.subheader("🔍 AI Implementation Breakdown (S_ai)")
            ai_breakdown = results['ai_breakdown']
            
            ai_cols = st.columns(4)
            ai_cols[0].metric("RAG", f"{ai_breakdown['I_rag']}/5")
            ai_cols[1].metric("Agent", f"{ai_breakdown['I_agent']}/5")
            ai_cols[2].metric("Fine-Tuning", f"{ai_breakdown['I_ft']}/5")
            ai_cols[3].metric("Safety", f"{ai_breakdown['I_safety']}/5")
            
            st.info(f"**AI Reasoning:** {results['reasoning']['ai']}")

            # Other Reasonings
            with st.expander("See General Analysis (Tech, Impact, Viability)"):
                st.write(results['reasoning']['general'])
                
            with st.expander("See Design Analysis (S_des)"):
                st.write(results['reasoning']['design'])

            # Similarity Check
            st.subheader("📚 Top 3 Similar Past Winners (Novelty Context)")
            similar_projects = results.get('similar_projects', [])
            if similar_projects:
                for i, proj in enumerate(similar_projects[:3]):
                    with st.container():
                        st.markdown(f"**{i+1}. {proj['title']}** (Similarity: {proj['similarity']:.2f})")
                        st.caption(proj['description'][:200] + "...")
                        if proj['url']:
                            st.markdown(f"[View Project]({proj['url']})")
                        st.divider()
            else:
                st.write("No similar projects found.")

        except Exception as e:
            st.error(f"An error occurred during evaluation: {str(e)}")
            st.exception(e)

