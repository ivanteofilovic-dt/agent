
import sys
import os

# Add project root to sys.path to allow 'from src...' imports
# This handles cases where streamlit is run from inside src or root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import asyncio
import docx
from src.transcriber import transcribe_audio
from src.agent import analyze_transcript

st.set_page_config(page_title="Sales Trainer Agent", layout="wide")

st.title("Sales Trainer Agent 🤖")
st.markdown("Upload a sales call transcript (Text, DOCX, or Audio) to get instant feedback based on our 100-point framework.")

# Sidebar for API Key configuration
with st.sidebar:
    st.header("Configuration")
    
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

# File Upload
uploaded_file = st.file_uploader("Upload Transcript", type=["txt", "docx", "mp3", "wav", "m4a"])

if uploaded_file:
    transcript_text = ""
    
    # Determine file type
    file_type = uploaded_file.name.split(".")[-1].lower()
    
    if file_type == "txt":
        transcript_text = uploaded_file.read().decode("utf-8")
        st.info("Text transcript loaded.")
        with st.expander("View Transcript"):
            st.text(transcript_text)
    
    elif file_type == "docx":
        try:
            doc = docx.Document(uploaded_file)
            transcript_text = "\n".join([para.text for para in doc.paragraphs])
            st.info("Word document loaded.")
            with st.expander("View Transcript"):
                st.text(transcript_text)
        except Exception as e:
            st.error(f"Error reading DOCX file: {e}")
            
    elif file_type in ["mp3", "wav", "m4a"]:
        st.info("Audio file detected. Transcribing...")
        # Check if Google API key is available for transcription regardless of selected agent model
        if not os.environ.get("GOOGLE_API_KEY"):
            st.warning("Google API Key is required for audio transcription (using Gemini), even if using Claude for analysis.")
            google_key_transcribe = st.text_input("Enter Google API Key for Transcription", type="password")
            if google_key_transcribe:
                os.environ["GOOGLE_API_KEY"] = google_key_transcribe
        
        if os.environ.get("GOOGLE_API_KEY"):
            try:
                with st.spinner("Transcribing audio... this may take a moment."):
                    # Save to temp file might be needed or pass bytes directly if transcriber supports it
                    # Our transcriber accepts bytes
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
    if transcript_text:
        if st.button("Analyze Call"):
            # Validate keys before running
            valid_config = True
            if "gemini" in model_name and not os.environ.get("GOOGLE_API_KEY"):
                st.error("Please set your Google API Key in the sidebar.")
                valid_config = False
            if "claude" in model_name and not os.environ.get("ANTHROPIC_API_KEY"):
                st.error("Please set your Anthropic API Key in the sidebar.")
                valid_config = False
            
            if valid_config:
                with st.spinner(f"Analyzing transcript with {model_name}..."):
                    try:
                        # Run async agent in sync Streamlit app
                        result = asyncio.run(analyze_transcript(transcript_text, model_name=model_name))
                        
                        if result:
                            st.success(f"Analysis Complete! Total Score: {result.total_score}/100")
                            
                            # Display Results
                            
                            # Summary
                            st.subheader("Feedback Summary")
                            st.write(result.feedback_summary)
                            
                            # Scores Breakdown
                            st.subheader("Score Breakdown")
                            
                            cols = st.columns(len(result.scores))
                            for idx, section in enumerate(result.scores):
                                with cols[idx]:
                                    st.metric(label=section.section_name, value=f"{section.section_total} pts")
                            
                            # Detailed Feedback
                            st.subheader("Detailed Assessment")
                            for section in result.scores:
                                with st.expander(f"{section.section_name} ({section.section_total} pts)", expanded=True):
                                    for metric in section.metrics:
                                        st.markdown(f"**{metric.metric_name}**")
                                        st.progress(metric.score / 10)
                                        st.caption(f"Score: {metric.score}/10")
                                        st.write(f"_{metric.justification}_")
                                        st.divider()
                            
                            # Recommended Actions
                            st.subheader("Recommended Follow-up Actions")
                            for action in result.recommended_actions:
                                st.markdown(f"- {action}")
                                
                        else:
                            # This path should now be unreachable due to raise in agent.py, but keeping for safety
                            st.error("The agent did not return a valid structured response. Check logs for details.")
                            
                    except Exception as e:
                        # Show the full error including what we bubbled up from agent.py
                        st.error(f"Analysis failed: {str(e)}")
                        # If we have details, we might want to expand them
                        if "JSON Parse Error" in str(e):
                            with st.expander("Debug Info"):
                                st.exception(e)
                        else:
                            st.exception(e)
