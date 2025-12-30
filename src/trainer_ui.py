"""UI module for Sales Trainer agent - uses sales-trainer-agent implementation."""
import streamlit as st
import sys
import os
import asyncio
import docx
from typing import Optional
from io import BytesIO
from pypdf import PdfReader

# Add sales-trainer-agent to path for imports
sales_trainer_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sales-trainer-agent'))
if sales_trainer_path not in sys.path:
    sys.path.insert(0, sales_trainer_path)

# Create a 'src' module alias for sales-trainer-agent imports
# The sales-trainer-agent code uses 'from src.agent import ...' but files are in root
# We'll create a src module that points to the sales-trainer-agent folder
import importlib.util
import types

# Create a src module namespace (make it a package)
src_module = types.ModuleType('src')
src_module.__path__ = [sales_trainer_path]  # Make it a package
src_module.__file__ = os.path.join(sales_trainer_path, '__init__.py')
sys.modules['src'] = src_module

# Import modules directly and add them to src namespace
# IMPORTANT: Load dependencies BEFORE agent module, since agent imports them
try:
    # Import scoring_framework module FIRST (needed by agent)
    scoring_framework_path = os.path.abspath(os.path.join(sales_trainer_path, 'scoring_framework.py'))
    spec = importlib.util.spec_from_file_location("src.scoring_framework", scoring_framework_path)
    scoring_module = importlib.util.module_from_spec(spec)
    # Ensure __file__ is set correctly for relative imports
    scoring_module.__file__ = scoring_framework_path
    spec.loader.exec_module(scoring_module)
    sys.modules['src.scoring_framework'] = scoring_module
    
    # Import claude_llm module (needed by agent)
    claude_llm_path = os.path.abspath(os.path.join(sales_trainer_path, 'claude_llm.py'))
    spec = importlib.util.spec_from_file_location("src.claude_llm", claude_llm_path)
    claude_module = importlib.util.module_from_spec(spec)
    # Ensure __file__ is set correctly for relative imports
    claude_module.__file__ = claude_llm_path
    spec.loader.exec_module(claude_module)
    sys.modules['src.claude_llm'] = claude_module
    
    # Import transcriber (not needed by agent, but needed for UI)
    transcriber_path = os.path.abspath(os.path.join(sales_trainer_path, 'transcriber.py'))
    spec = importlib.util.spec_from_file_location("src.transcriber", transcriber_path)
    transcriber_module = importlib.util.module_from_spec(spec)
    transcriber_module.__file__ = transcriber_path
    spec.loader.exec_module(transcriber_module)
    sys.modules['src.transcriber'] = transcriber_module
    transcribe_audio = transcriber_module.transcribe_audio
    
    # NOW import agent module (after its dependencies are loaded)
    agent_module_path = os.path.abspath(os.path.join(sales_trainer_path, 'agent.py'))
    spec = importlib.util.spec_from_file_location("src.agent", agent_module_path)
    agent_module = importlib.util.module_from_spec(spec)
    agent_module.__file__ = agent_module_path
    spec.loader.exec_module(agent_module)
    sys.modules['src.agent'] = agent_module
    analyze_transcript = agent_module.analyze_transcript
    
    SALES_TRAINER_AVAILABLE = True
    IMPORT_ERROR = None
except Exception as e:
    SALES_TRAINER_AVAILABLE = False
    IMPORT_ERROR = str(e)
    import traceback
    IMPORT_ERROR = f"{str(e)}\n{traceback.format_exc()}"


def render_trainer_ui():
    """Render the Sales Trainer agent UI using sales-trainer-agent implementation."""
    st.markdown('<div class="main-header">🎓 Sales Trainer Agent</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.1rem; color: #666;">AI-Powered Sales Coaching and Training</p>', unsafe_allow_html=True)
    
    if not SALES_TRAINER_AVAILABLE:
        st.error(f"⚠️ Sales Trainer Agent not available: {IMPORT_ERROR}")
        st.info("""
        **Troubleshooting:**
        - Make sure the `sales-trainer-agent` folder exists with all required files
        - Check that dependencies are installed (google-adk, anthropic, etc.)
        - See the sales-trainer-agent README for setup instructions
        """)
        return
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("---")
        st.header("⚙️ Configuration")
        
        # Model selection
        model_options = [
            "gemini-1.5-pro", 
            "gemini-1.5-flash", 
            "gemini-2.0-flash-exp",
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022"
        ]
        model_name = st.selectbox("Select Model", model_options, index=0)
        
        # API Keys based on model selection
        if "gemini" in model_name:
            api_key = st.text_input("Google API Key", type="password", value=os.environ.get("GOOGLE_API_KEY", ""))
            if api_key:
                os.environ["GOOGLE_API_KEY"] = api_key
        elif "claude" in model_name:
            anthropic_key = st.text_input("Anthropic API Key", type="password", value=os.environ.get("ANTHROPIC_API_KEY", ""))
            if anthropic_key:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        
        st.markdown("---")
        if st.button("🔄 Reset", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith('trainer_'):
                    del st.session_state[key]
            st.rerun()
    
    # Main content
    st.info("""
    **Sales Trainer Agent** provides AI-powered sales coaching based on a comprehensive 100-point scoring framework.
    
    ### Features:
    - 📝 Call transcript analysis with detailed feedback
    - 🎯 Performance scoring across 3 domains (Focus & Scope, Deal Qualification, Customer Interaction)
    - 💡 Actionable recommendations
    - 🎤 Audio transcription support
    """)
    
    st.markdown("---")
    st.markdown("### 📝 Upload Sales Call Transcript")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Upload transcript file",
            type=['txt', 'docx', 'doc', 'pdf', 'mp3', 'wav', 'm4a'],
            key="trainer_transcript_uploader"
        )
    
    with col2:
        transcript_text = st.text_area(
            "Or paste transcript here",
            height=200,
            key="trainer_transcript_paste"
        )
    
    # Process uploaded file
    if uploaded_file:
        file_type = uploaded_file.name.split(".")[-1].lower() if uploaded_file.name else ""
        
        if file_type == "txt":
            transcript_text = uploaded_file.read().decode("utf-8")
            st.info("Text transcript loaded.")
            with st.expander("View Transcript"):
                st.text(transcript_text)
        
        elif file_type == "docx":
            try:
                file_bytes = uploaded_file.read()
                doc = docx.Document(BytesIO(file_bytes))
                transcript_text = "\n".join([para.text for para in doc.paragraphs])
                st.info("Word document loaded.")
                with st.expander("View Transcript"):
                    st.text(transcript_text)
            except Exception as e:
                st.error(f"Error reading DOCX file: {e}")
                transcript_text = ""
        
        elif file_type == "pdf":
            try:
                file_bytes = uploaded_file.read()
                pdf_reader = PdfReader(BytesIO(file_bytes))
                transcript_text = "\n".join([page.extract_text() for page in pdf_reader.pages])
                st.info("PDF loaded.")
                with st.expander("View Transcript"):
                    st.text(transcript_text)
            except Exception as e:
                st.error(f"Error reading PDF file: {e}")
                transcript_text = ""
        
        elif file_type in ["mp3", "wav", "m4a"]:
            st.info("Audio file detected. Transcribing...")
            # Check if Google API key is available for transcription
            if not os.environ.get("GOOGLE_API_KEY"):
                st.warning("Google API Key is required for audio transcription (using Gemini), even if using Claude for analysis.")
                google_key_transcribe = st.text_input("Enter Google API Key for Transcription", type="password", key="transcribe_key")
                if google_key_transcribe:
                    os.environ["GOOGLE_API_KEY"] = google_key_transcribe
            
            if os.environ.get("GOOGLE_API_KEY"):
                try:
                    with st.spinner("Transcribing audio... this may take a moment."):
                        audio_bytes = uploaded_file.read()
                        transcript_text = transcribe_audio(audio_bytes, mime_type=f"audio/{file_type}")
                    
                    st.success("Transcription complete!")
                    with st.expander("View Transcription"):
                        st.text(transcript_text)
                except Exception as e:
                    st.error(f"Transcription failed: {e}")
            else:
                st.error("Transcription aborted due to missing Google API Key.")
    
    # Analyze Button
    if transcript_text and transcript_text.strip():
        if st.button("🚀 Analyze Call", type="primary", use_container_width=True):
            # Validate keys before running
            valid_config = True
            if "gemini" in model_name and not os.environ.get("GOOGLE_API_KEY"):
                st.error("Please set your Google API Key in the sidebar.")
                valid_config = False
            if "claude" in model_name and not os.environ.get("ANTHROPIC_API_KEY"):
                st.error("Please set your Anthropic API Key in the sidebar.")
                valid_config = False
            
            if valid_config:
                with st.spinner(f"Analyzing transcript with {model_name}... This may take a minute."):
                    try:
                        # Run async agent in sync Streamlit app
                        result = asyncio.run(analyze_transcript(transcript_text, model_name=model_name))
                        
                        if result:
                            st.success(f"✅ Analysis Complete! Total Score: {result.total_score}/100")
                            
                            # Display Results
                            
                            # Summary
                            st.markdown("---")
                            st.markdown("### 📝 Feedback Summary")
                            st.info(result.feedback_summary)
                            
                            # Scores Breakdown
                            st.markdown("---")
                            st.markdown("### 📊 Score Breakdown")
                            
                            cols = st.columns(len(result.scores))
                            for idx, section in enumerate(result.scores):
                                with cols[idx]:
                                    score_color = "🟢" if section.section_total >= section.section_total * 0.8 else "🟡" if section.section_total >= section.section_total * 0.6 else "🔴"
                                    st.metric(label=section.section_name, value=f"{section.section_total} pts {score_color}")
                            
                            # Overall score with progress bar
                            st.markdown("---")
                            st.markdown("### 🎯 Overall Performance Score")
                            st.metric("Total Score", f"{result.total_score}/100")
                            st.progress(result.total_score / 100)
                            
                            # Detailed Feedback
                            st.markdown("---")
                            st.markdown("### 📋 Detailed Assessment")
                            for section in result.scores:
                                with st.expander(f"{section.section_name} ({section.section_total} pts)", expanded=True):
                                    for metric in section.metrics:
                                        st.markdown(f"**{metric.metric_name}**")
                                        st.progress(metric.score / 10)
                                        st.caption(f"Score: {metric.score}/10")
                                        st.write(f"_{metric.justification}_")
                                        st.divider()
                            
                            # Recommended Actions
                            st.markdown("---")
                            st.markdown("### 💡 Recommended Follow-up Actions")
                            for i, action in enumerate(result.recommended_actions, 1):
                                st.markdown(f"{i}. {action}")
                                
                        else:
                            st.error("The agent did not return a valid structured response. Check logs for details.")
                            
                    except Exception as e:
                        # Show the full error
                        st.error(f"❌ Analysis failed: {str(e)}")
                        # If we have details, we might want to expand them
                        if "JSON Parse Error" in str(e) or "Validation" in str(e):
                            with st.expander("Debug Info"):
                                st.exception(e)
                        else:
                            st.exception(e)
    
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #666;">Sales Trainer Agent 🎓 - AI-Powered Sales Coaching</p>',
        unsafe_allow_html=True
    )
