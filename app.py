"""Unified Streamlit UI for Combined Agents Platform."""
import streamlit as st
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Page configuration
st.set_page_config(
    page_title="Combined Agent Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (shared across both agents)
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    .stButton>button {
        width: 100%;
    }
    .field-group {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize agent selection in session state
if 'selected_agent' not in st.session_state:
    st.session_state.selected_agent = "Mrs. Salesforce"

# Sidebar for agent selection
with st.sidebar:
    st.title("🤖 Agent Selection")
    agent_choice = st.radio(
        "Select Agent:",
        ["Mrs. Salesforce", "Sales Trainer"],
        index=0 if st.session_state.selected_agent == "Mrs. Salesforce" else 1,
        key="agent_selector"
    )
    
    if agent_choice != st.session_state.selected_agent:
        st.session_state.selected_agent = agent_choice
        # Clear session state when switching agents (keep only selection)
        keys_to_clear = [k for k in st.session_state.keys() 
                        if k not in ['selected_agent', 'agent_selector']]
        for key in keys_to_clear:
            del st.session_state[key]
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📚 About")
    if agent_choice == "Mrs. Salesforce":
        st.info("""
        **Mrs. Salesforce** processes sales call transcripts and automatically creates Salesforce records with MEDDIC qualification.
        
        Features:
        - 📝 Transcript processing
        - 🏢 Salesforce integration
        - 📊 MEDDIC qualification
        - 💬 Interactive chat interface
        """)
    else:
        st.info("""
        **Sales Trainer** provides AI-powered sales coaching based on a comprehensive 100-point scoring framework.
        
        Features:
        - 📝 Call transcript analysis (text, DOCX, PDF, or audio)
        - 🎯 Performance scoring across 3 domains
        - 📊 Detailed metric-by-metric feedback
        - 💡 Actionable recommendations
        - 🎤 Audio transcription support
        """)

# Route to appropriate agent UI
if st.session_state.selected_agent == "Mrs. Salesforce":
    # Import and execute the Salesforce agent UI from src/app.py
    # We need to modify the page config call since we already set it above
    try:
        # Import all necessary modules first (they're in src/)
        from agent import MrsSalesforceAgent
        from models import SalesCallData, MEDDICData, ContactData, AccountData, OpportunityData
        from salesforce_formatter import SalesforceFormatter
        from utils import generate_deal_summary_docx
        import json
        import re
        from datetime import datetime
        from typing import Optional, Dict, Any, List
        from io import BytesIO
        from copy import deepcopy
        from docx import Document
        
        # Read and execute the Salesforce UI code
        # We'll use a modified version that doesn't set page config
        src_app_path = os.path.join(os.path.dirname(__file__), 'src', 'app.py')
        with open(src_app_path, 'r') as f:
            src_app_code = f.read()
        
        # Create a namespace with all necessary imports and modules
        # Include sys and os for path manipulation
        namespace = {
            'st': st,
            'sys': sys,
            'os': os,
            'json': json,
            're': re,
            'datetime': datetime,
            'Optional': Optional,
            'Dict': Dict,
            'Any': Any,
            'List': List,
            'BytesIO': BytesIO,
            'deepcopy': deepcopy,
            'Document': Document,
            'MrsSalesforceAgent': MrsSalesforceAgent,
            'SalesCallData': SalesCallData,
            'MEDDICData': MEDDICData,
            'ContactData': ContactData,
            'AccountData': AccountData,
            'OpportunityData': OpportunityData,
            'SalesforceFormatter': SalesforceFormatter,
            'generate_deal_summary_docx': generate_deal_summary_docx,
            '__file__': src_app_path,
            '__name__': '__main__'
        }
        
        # Replace the page config call - comment out the entire block
        # Simple string replacement for the known pattern
        page_config_block = """# Page configuration
st.set_page_config(
    page_title="Mrs. Salesforce 🤖",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)"""
        
        commented_block = """# Page configuration
# st.set_page_config(
#     page_title="Mrs. Salesforce 🤖",
#     page_icon="🤖",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )"""
        
        src_app_code = src_app_code.replace(page_config_block, commented_block)
        
        # Execute the code - imports will work because src is already in sys.path
        exec(src_app_code, namespace)
        
    except Exception as e:
        st.error(f"Error loading Mrs. Salesforce agent: {str(e)}")
        st.exception(e)
        st.info("""
        **Troubleshooting:**
        - Make sure all dependencies are installed: `uv sync` or `pip install -r requirements.txt`
        - Check that your `.env` file has the required API keys
        - See the README for setup instructions
        """)

elif st.session_state.selected_agent == "Sales Trainer":
    # Import and render the Sales Trainer UI
    try:
        from trainer_ui import render_trainer_ui
        render_trainer_ui()
    except Exception as e:
        st.error(f"Error loading Sales Trainer agent: {str(e)}")
        st.exception(e)
        st.info("""
        **Troubleshooting:**
        - Make sure all dependencies are installed: `uv sync` or `pip install -r requirements.txt`
        - Check that your `.env` file has the required API keys
        - See the README for setup instructions
        """)
