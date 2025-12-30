"""Streamlit UI for Mrs. Salesforce agent - Chatbot Interface."""
import streamlit as st
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from io import BytesIO
from copy import deepcopy
from docx import Document
from agent import MrsSalesforceAgent
from models import SalesCallData, MEDDICData, ContactData, AccountData, OpportunityData
from salesforce_formatter import SalesforceFormatter
from utils import generate_deal_summary_docx

# Page configuration
st.set_page_config(
    page_title="Mrs. Salesforce 🤖",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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

# Conversation stages
STAGE_TRANSCRIPT = "transcript"
STAGE_CHAT_COLLECTION = "chat_collection"
STAGE_ACCOUNT = "account"
STAGE_ACCOUNT_VERIFY = "account_verify"
STAGE_CONTACT = "contact"
STAGE_CONTACT_VERIFY = "contact_verify"
STAGE_OPPORTUNITY = "opportunity"
STAGE_OPPORTUNITY_VERIFY = "opportunity_verify"
STAGE_FINAL_REVIEW = "final_review"
STAGE_COMPLETE = "complete"

# Initialize session state
if 'agent' not in st.session_state:
    try:
        st.session_state.agent = MrsSalesforceAgent()
        st.session_state.agent_initialized = True
        st.session_state.init_error = None
    except Exception as e:
        error_msg = str(e)
        if "Salesforce" not in error_msg and "OAuth" not in error_msg:
            st.session_state.agent = None
            st.session_state.agent_initialized = False
            st.session_state.init_error = error_msg
        else:
            try:
                st.session_state.agent = MrsSalesforceAgent()
                st.session_state.agent_initialized = True
                st.session_state.init_error = None
            except Exception as e2:
                st.session_state.agent = None
                st.session_state.agent_initialized = False
                st.session_state.init_error = str(e2)

# Initialize conversation state
if 'conversation_stage' not in st.session_state:
    st.session_state.conversation_stage = STAGE_TRANSCRIPT

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None

if 'manual_inputs' not in st.session_state:
    st.session_state.manual_inputs = {
        'account': {},
        'contact': {},
        'opportunity': {}
    }

if 'verified' not in st.session_state:
    st.session_state.verified = {
        'account': False,
        'contact': False,
        'opportunity': False
    }

if 'transcript_uploaded' not in st.session_state:
    st.session_state.transcript_uploaded = False

if 'chat_collection_mode' not in st.session_state:
    st.session_state.chat_collection_mode = False

if 'chat_data_extracted' not in st.session_state:
    st.session_state.chat_data_extracted = False

if 'questions_asked' not in st.session_state:
    st.session_state.questions_asked = []

if 'current_question_category' not in st.session_state:
    st.session_state.current_question_category = None

if 'last_assistant_message' not in st.session_state:
    st.session_state.last_assistant_message = None

# Helper functions
def get_missing_required_fields(entity_type: str, data: Optional[Any]) -> List[str]:
    """Get list of missing required fields for an entity."""
    if entity_type == 'account':
        if not data:
            return ['name', 'currency', 'region']
        missing = []
        if not data.name: missing.append('name')
        if not data.currency: missing.append('currency')
        if not data.region: missing.append('region')
        return missing
    elif entity_type == 'contact':
        if not data:
            return ['last_name', 'title', 'email']
        missing = []
        if not data.last_name: missing.append('last_name')
        if not data.title: missing.append('title')
        if not data.email: missing.append('email')
        return missing
    elif entity_type == 'opportunity':
        if not data:
            return ['name', 'amount', 'close_date']
        missing = []
        if not data.name: missing.append('name')
        if not data.amount: missing.append('amount')
        if not data.close_date: missing.append('close_date')
        return missing
    return []

def add_message(role: str, content: str):
    """Add a message to the conversation."""
    st.session_state.messages.append({
        'role': role,
        'content': content,
        'timestamp': datetime.now()
    })

def merge_manual_inputs(call_data: SalesCallData) -> SalesCallData:
    """Merge manual field inputs with extracted data."""
    result = deepcopy(call_data)
    
    # Merge account data
    if result.account and st.session_state.manual_inputs.get('account'):
        account_dict = result.account.model_dump()
        account_dict.update({k: v for k, v in st.session_state.manual_inputs['account'].items() if v})
        result.account = AccountData(**account_dict)
    elif st.session_state.manual_inputs.get('account') and any(st.session_state.manual_inputs['account'].values()):
        account_dict = st.session_state.manual_inputs['account'].copy()
        result.account = AccountData(**account_dict)
    
    # Merge contact data
    if result.contact and st.session_state.manual_inputs.get('contact'):
        contact_dict = result.contact.model_dump()
        contact_dict.update({k: v for k, v in st.session_state.manual_inputs['contact'].items() if v})
        result.contact = ContactData(**contact_dict)
    elif st.session_state.manual_inputs.get('contact') and any(st.session_state.manual_inputs['contact'].values()):
        contact_dict = st.session_state.manual_inputs['contact'].copy()
        result.contact = ContactData(**contact_dict)
    
    # Merge opportunity data
    if result.opportunity and st.session_state.manual_inputs.get('opportunity'):
        opp_dict = result.opportunity.model_dump()
        if 'amount' in st.session_state.manual_inputs['opportunity'] and st.session_state.manual_inputs['opportunity']['amount']:
            try:
                opp_dict['amount'] = float(st.session_state.manual_inputs['opportunity']['amount'])
            except (ValueError, TypeError):
                pass
        opp_dict.update({k: v for k, v in st.session_state.manual_inputs['opportunity'].items() 
                        if v and k != 'amount'})
        result.opportunity = OpportunityData(**opp_dict)
    elif st.session_state.manual_inputs.get('opportunity') and any(st.session_state.manual_inputs['opportunity'].values()):
        opp_dict = st.session_state.manual_inputs['opportunity'].copy()
        if 'amount' in opp_dict and opp_dict['amount']:
            try:
                opp_dict['amount'] = float(opp_dict['amount'])
            except (ValueError, TypeError):
                opp_dict['amount'] = None
        result.opportunity = OpportunityData(**opp_dict)
    
    return result

def format_entity_for_display(entity_type: str, data: Any) -> str:
    """Format entity data for display in chat."""
    if not data:
        return "No data available."
    
    lines = []
    if entity_type == 'account':
        lines.append("**Account Information:**")
        if data.name: lines.append(f"  • Name: {data.name}")
        if data.industry: lines.append(f"  • Industry: {data.industry}")
        if data.billing_city: lines.append(f"  • City: {data.billing_city}")
        if data.billing_state: lines.append(f"  • State: {data.billing_state}")
        if data.billing_country: lines.append(f"  • Country: {data.billing_country}")
        if data.website: lines.append(f"  • Website: {data.website}")
        if data.annual_revenue: lines.append(f"  • Annual Revenue: ${data.annual_revenue:,.0f}")
        if data.number_of_employees: lines.append(f"  • Employees: {data.number_of_employees}")
    elif entity_type == 'contact':
        lines.append("**Contact Information:**")
        if data.first_name: lines.append(f"  • First Name: {data.first_name}")
        if data.last_name: lines.append(f"  • Last Name: {data.last_name}")
        if data.email: lines.append(f"  • Email: {data.email}")
        if data.phone: lines.append(f"  • Phone: {data.phone}")
        if data.title: lines.append(f"  • Title: {data.title}")
    elif entity_type == 'opportunity':
        lines.append("**Opportunity Information:**")
        if data.name: lines.append(f"  • Name: {data.name}")
        if data.amount: lines.append(f"  • Amount: ${data.amount:,.0f}")
        if data.close_date: lines.append(f"  • Close Date: {data.close_date}")
        if data.stage: lines.append(f"  • Stage: {data.stage}")
        if data.next_steps: lines.append(f"  • Next Steps: {data.next_steps}")
    
    return "\n".join(lines) if lines else "No data available."

# Header
st.markdown('<div class="main-header">🤖 Mrs. Salesforce</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.1rem; color: #666;">Interactive Chatbot - From Call Transcripts to Salesforce Records</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Status")
    
    if not st.session_state.agent_initialized:
        st.error("⚠️ Agent not initialized")
        if 'init_error' in st.session_state and st.session_state.init_error:
            st.error(f"Error: {st.session_state.init_error}")
    else:
        salesforce_status = "✅ Ready" if getattr(st.session_state.agent, 'salesforce_available', False) else "👁️ Preview Mode"
        st.success(f"✅ Agent ready! ({salesforce_status})")
    
    st.markdown("---")
    st.header("📋 Progress")
    
    stages = {
        STAGE_TRANSCRIPT: "📝 Upload Transcript",
        STAGE_CHAT_COLLECTION: "💬 Chat Collection",
        STAGE_ACCOUNT: "🏢 Account Setup",
        STAGE_ACCOUNT_VERIFY: "✓ Account Verification",
        STAGE_CONTACT: "👤 Contact Setup",
        STAGE_CONTACT_VERIFY: "✓ Contact Verification",
        STAGE_OPPORTUNITY: "💼 Opportunity Setup",
        STAGE_OPPORTUNITY_VERIFY: "✓ Opportunity Verification",
        STAGE_FINAL_REVIEW: "📊 Final Review",
        STAGE_COMPLETE: "✅ Complete"
    }
    
    current_stage = st.session_state.conversation_stage
    for stage_key, stage_name in stages.items():
        if stage_key == current_stage:
            st.markdown(f"**→ {stage_name}**")
        elif list(stages.keys()).index(stage_key) < list(stages.keys()).index(current_stage):
            st.markdown(f"✓ {stage_name}")
        else:
            st.markdown(f"○ {stage_name}")
    
    st.markdown("---")
    if st.button("🔄 Reset Conversation"):
        for key in ['conversation_stage', 'messages', 'extracted_data', 'manual_inputs', 'verified', 'transcript_uploaded', 'chat_collection_mode', 'chat_data_extracted', 'questions_asked', 'current_question_category', 'last_assistant_message']:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.conversation_stage = STAGE_TRANSCRIPT
        st.session_state.messages = []
        st.session_state.extracted_data = None
        st.session_state.manual_inputs = {'account': {}, 'contact': {}, 'opportunity': {}}
        st.session_state.verified = {'account': False, 'contact': False, 'opportunity': False}
        st.session_state.transcript_uploaded = False
        st.session_state.chat_collection_mode = False
        st.session_state.chat_data_extracted = False
        st.session_state.questions_asked = []
        st.session_state.current_question_category = None
        st.session_state.last_assistant_message = None
        st.rerun()

# Main chat interface
st.markdown("---")

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

# Handle current stage
current_stage = st.session_state.conversation_stage

# Stage 1: Transcript Upload
if current_stage == STAGE_TRANSCRIPT:
    if not st.session_state.transcript_uploaded:
        # Welcome message
        if not st.session_state.messages:
            add_message('assistant', "👋 Hello! I'm Mrs. Salesforce, your AI sales assistant. I'll help you extract information from call transcripts and create Salesforce records.\n\nYou can either:\n1. Upload or paste your call transcript, or\n2. Provide the information through chat if you don't have a transcript.")
            st.rerun()
        
        with st.chat_message("assistant"):
            st.markdown("Please upload or paste your call transcript, or click the button below to provide information through chat:")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Upload transcript file",
                type=['txt', 'docx', 'doc'],
                key="transcript_uploader"
            )
        
        with col2:
            transcript_text = st.text_area(
                "Or paste transcript here",
                height=200,
                key="transcript_paste"
            )
        
        if uploaded_file:
            if uploaded_file.type == "text/plain":
                transcript_text = str(uploaded_file.read(), "utf-8")
            elif uploaded_file.name.endswith('.docx') or uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                try:
                    file_bytes = uploaded_file.read()
                    doc = Document(BytesIO(file_bytes))
                    transcript_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    transcript_text = ""
        
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("🚀 Process Transcript", type="primary", use_container_width=True):
                if not transcript_text.strip():
                    st.error("⚠️ Please provide a transcript to process.")
                elif not st.session_state.agent_initialized:
                    st.error("⚠️ Agent not initialized.")
                else:
                    with st.spinner("🔄 Processing transcript and extracting data..."):
                        try:
                            result = st.session_state.agent.process_call_transcript(
                                transcript_text,
                                auto_create=False
                            )
                            st.session_state.extracted_data = result.get("extracted_data")
                            st.session_state.transcript_uploaded = True
                            add_message('user', f"📄 Transcript uploaded ({len(transcript_text)} characters)")
                            add_message('assistant', "✅ Great! I've processed your transcript. Let me extract the information step by step.\n\nLet's start with the **Account** information.")
                            st.session_state.conversation_stage = STAGE_ACCOUNT
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error processing transcript: {str(e)}")
                            st.exception(e)
        
        with col2:
            if st.button("💬 Provide Info in Chat", use_container_width=True):
                st.session_state.chat_collection_mode = True
                st.session_state.conversation_stage = STAGE_CHAT_COLLECTION
                st.session_state.questions_asked = []
                st.session_state.current_question_category = None
                if not any('chat' in msg.get('content', '').lower() and 'information' in msg.get('content', '').lower() for msg in st.session_state.messages):
                    add_message('user', "I'd like to provide information through chat")
                    add_message('assistant', "Great! I'll guide you through collecting all the information we need. Let me start by asking you a few questions.\n\n**What's the name of the company or account?**")
                    st.session_state.questions_asked.append("account_name")
                    st.session_state.current_question_category = "account"
                st.rerun()

# Stage 1.5: Chat Collection (when no transcript provided)
elif current_stage == STAGE_CHAT_COLLECTION:
    # Helper function to check missing required fields
    def get_missing_required_fields_from_data(call_data: SalesCallData) -> Dict[str, List[str]]:
        """Get list of missing required fields organized by category."""
        missing = {
            'account': [],
            'contact': [],
            'opportunity': []
        }
        if not call_data.account or not call_data.account.name:
            missing['account'].append("name")
        if not call_data.account or not call_data.account.currency:
            missing['account'].append("currency")
        if not call_data.account or not call_data.account.region:
            missing['account'].append("region")
        if not call_data.contact or not call_data.contact.last_name:
            missing['contact'].append("last_name")
        if not call_data.contact or not call_data.contact.email:
            missing['contact'].append("email")
        if not call_data.contact or not call_data.contact.title:
            missing['contact'].append("title")
        if not call_data.opportunity or not call_data.opportunity.name:
            missing['opportunity'].append("name")
        if not call_data.opportunity or not call_data.opportunity.amount:
            missing['opportunity'].append("amount")
        if not call_data.opportunity or not call_data.opportunity.close_date:
            missing['opportunity'].append("close_date")
        return missing
    
    def get_next_question(call_data: Optional[SalesCallData], questions_asked: List[str]) -> Optional[tuple]:
        """
        Determine the next question to ask based on missing information.
        Returns (category, field, question_text) or None if all required info is collected.
        """
        if not call_data:
            # Start with account name
            if "account_name" not in questions_asked:
                return ("account", "name", "**What's the name of the company or account?**")
            return None
        
        missing = get_missing_required_fields_from_data(call_data)
        
        # Question mapping
        questions = {
            ("account", "name"): "**What's the name of the company or account?**",
            ("account", "currency"): "**What currency should we use?** (e.g., USD, EUR, GBP)",
            ("account", "region"): "**What region is the company located in?** (e.g., North America, Europe, Asia-Pacific)",
            ("contact", "last_name"): "**What's the contact person's last name?**",
            ("contact", "email"): "**What's the contact person's email address?**",
            ("contact", "title"): "**What's the contact person's job title?**",
            ("opportunity", "name"): "**What's the name of the opportunity or deal?**",
            ("opportunity", "amount"): "**What's the expected deal amount?** (e.g., 50000)",
            ("opportunity", "close_date"): "**What's the expected close date?** (e.g., Q2 2025, or a specific date)"
        }
        
        # Priority order: account -> contact -> opportunity
        for category in ['account', 'contact', 'opportunity']:
            for field in missing[category]:
                question_key = (category, field)
                question_id = f"{category}_{field}"
                if question_key in questions and question_id not in questions_asked:
                    return (category, field, questions[question_key])
        
        return None
    
    # Chat input for collecting information
    if prompt := st.chat_input("Type your answer here..."):
        # Add user message
        add_message('user', prompt)
        
        # Extract all user messages as a "transcript"
        user_messages = [msg['content'] for msg in st.session_state.messages if msg['role'] == 'user']
        conversation_text = "\n".join(user_messages)
        
        # Always try to extract after user provides input
        with st.spinner("🔄 Analyzing your response..."):
            try:
                # Use the transcript processor to extract data from conversation
                result = st.session_state.agent.process_call_transcript(
                    conversation_text,
                    auto_create=False
                )
                extracted = result.get("extracted_data")
                
                if extracted:
                    st.session_state.extracted_data = extracted
                    st.session_state.chat_data_extracted = True
                    
                    # Create acknowledgment message based on what we captured
                    acknowledgment_parts = []
                    if extracted.account and extracted.account.name:
                        if "account_name" not in st.session_state.questions_asked or len([q for q in st.session_state.questions_asked if q == "account_name"]) == 1:
                            acknowledgment_parts.append(f"Company: {extracted.account.name}")
                    if extracted.contact and extracted.contact.last_name:
                        if "contact_last_name" not in st.session_state.questions_asked or len([q for q in st.session_state.questions_asked if q == "contact_last_name"]) == 1:
                            contact_name = f"{extracted.contact.first_name or ''} {extracted.contact.last_name}".strip()
                            acknowledgment_parts.append(f"Contact: {contact_name}")
                    if extracted.opportunity and extracted.opportunity.name:
                        if "opportunity_name" not in st.session_state.questions_asked or len([q for q in st.session_state.questions_asked if q == "opportunity_name"]) == 1:
                            acknowledgment_parts.append(f"Opportunity: {extracted.opportunity.name}")
                    
                    # Determine next question (only one at a time)
                    next_question = get_next_question(extracted, st.session_state.questions_asked)
                    
                    if next_question:
                        category, field, question_text = next_question
                        question_id = f"{category}_{field}"
                        
                        # Only ask if we haven't asked this question yet
                        if question_id not in st.session_state.questions_asked:
                            st.session_state.questions_asked.append(question_id)
                            st.session_state.current_question_category = category
                            
                            # Acknowledge and ask next question (only one question)
                            if acknowledgment_parts:
                                acknowledgment = "Thanks! " + ", ".join(acknowledgment_parts) + ". "
                            else:
                                acknowledgment = "Got it! "
                            assistant_msg = f"{acknowledgment}{question_text}"
                            add_message('assistant', assistant_msg)
                            st.session_state.last_assistant_message = assistant_msg
                    else:
                        # All required information collected
                        if acknowledgment_parts:
                            acknowledgment = "Perfect! " + ", ".join(acknowledgment_parts) + ". "
                        else:
                            acknowledgment = "Perfect! "
                        assistant_msg = f"{acknowledgment}✅ I've collected all the necessary information. Let me organize it step by step.\n\nLet's start with the **Account** information."
                        add_message('assistant', assistant_msg)
                        st.session_state.last_assistant_message = assistant_msg
                        st.session_state.conversation_stage = STAGE_ACCOUNT
                        st.rerun()
                else:
                    # If extraction fails, ask for account name (only if not already asked)
                    if "account_name" not in st.session_state.questions_asked:
                        assistant_msg = "**What's the name of the company or account?**"
                        add_message('assistant', assistant_msg)
                        st.session_state.questions_asked.append("account_name")
                        st.session_state.last_assistant_message = assistant_msg
                    else:
                        # Try to ask the next question based on what we might have
                        if st.session_state.extracted_data:
                            next_question = get_next_question(st.session_state.extracted_data, st.session_state.questions_asked)
                            if next_question:
                                category, field, question_text = next_question
                                question_id = f"{category}_{field}"
                                if question_id not in st.session_state.questions_asked:
                                    st.session_state.questions_asked.append(question_id)
                                    add_message('assistant', question_text)
                                    st.session_state.last_assistant_message = question_text
                                else:
                                    add_message('assistant', "I'm processing your information. Could you provide more details?")
                            else:
                                add_message('assistant', "I'm processing your information. Could you provide more details about the company, contact person, or opportunity?")
                        else:
                            add_message('assistant', "I'm processing your information. Could you provide more details about the company, contact person, or opportunity?")
            except Exception as e:
                # If extraction fails, continue asking questions (only if not already asked)
                if "account_name" not in st.session_state.questions_asked:
                    assistant_msg = "**What's the name of the company or account?**"
                    add_message('assistant', assistant_msg)
                    st.session_state.questions_asked.append("account_name")
                    st.session_state.last_assistant_message = assistant_msg
                else:
                    assistant_msg = "Thanks! Please continue providing information, and I'll ask follow-up questions as needed."
                    add_message('assistant', assistant_msg)
                    st.session_state.last_assistant_message = assistant_msg
        
        st.rerun()
    
    # Show initial question if no messages yet (only on first load, and only if not already asked)
    if not st.session_state.messages or not any(msg['role'] == 'user' for msg in st.session_state.messages):
        if "account_name" not in st.session_state.questions_asked:
            # Check if we already added this message to avoid duplicates
            if not any("What's the name of the company" in msg.get('content', '') for msg in st.session_state.messages):
                assistant_msg = "**What's the name of the company or account?**"
                add_message('assistant', assistant_msg)
                st.session_state.questions_asked.append("account_name")
                st.session_state.current_question_category = "account"
                st.session_state.last_assistant_message = assistant_msg
                st.rerun()

# Stage 2: Account Setup
elif current_stage == STAGE_ACCOUNT:
    if st.session_state.extracted_data:
        call_data = merge_manual_inputs(st.session_state.extracted_data)
        account = call_data.account
        
        # Show extracted data first (only once)
        if not any(msg.get('content', '').startswith('**Account Information:**') for msg in st.session_state.messages):
            if account:
                account_info = format_entity_for_display('account', account)
                add_message('assistant', f"**Account Information:**\n\n{account_info}")
            else:
                add_message('assistant', "I couldn't extract any account information from the transcript.")
            st.rerun()
        
        # Check for missing required fields
        missing_fields = get_missing_required_fields('account', account)
        
        if missing_fields:
            if not any('Missing' in msg.get('content', '') and 'account' in msg.get('content', '').lower() for msg in st.session_state.messages[-3:]):
                add_message('assistant', f"I need the following required fields to complete the account:\n\n**Missing:** {', '.join([f.replace('_', ' ').title() for f in missing_fields])}\n\nPlease fill them in below:")
                st.rerun()
            
            # Form for missing fields
            with st.form("account_input_form"):
                st.markdown("### ✏️ Fill Missing Account Fields")
                manual_account = {}
                
                col1, col2 = st.columns(2)
                with col1:
                    if 'name' in missing_fields:
                        manual_account['name'] = st.text_input("Account Name *", value=st.session_state.manual_inputs['account'].get('name', ''))
                    if 'currency' in missing_fields:
                        manual_account['currency'] = st.text_input("Currency *", value=st.session_state.manual_inputs['account'].get('currency', account.currency if account else ''), placeholder="e.g., USD, EUR, GBP")
                    if 'region' in missing_fields:
                        manual_account['region'] = st.text_input("Region *", value=st.session_state.manual_inputs['account'].get('region', account.region if account else ''))
                
                with col2:
                    # Optional fields
                    if 'industry' not in missing_fields:
                        manual_account['industry'] = st.text_input("Industry (optional)", value=st.session_state.manual_inputs['account'].get('industry', account.industry if account else ''))
                    if 'billing_city' not in missing_fields:
                        manual_account['billing_city'] = st.text_input("City (optional)", value=st.session_state.manual_inputs['account'].get('billing_city', account.billing_city if account else ''))
                    if 'billing_country' not in missing_fields:
                        manual_account['billing_country'] = st.text_input("Country (optional)", value=st.session_state.manual_inputs['account'].get('billing_country', account.billing_country if account else ''))
                    if 'billing_state' not in missing_fields:
                        manual_account['billing_state'] = st.text_input("State/Province (optional)", value=st.session_state.manual_inputs['account'].get('billing_state', account.billing_state if account else ''))
                
                if st.form_submit_button("💾 Save Account Fields", type="primary"):
                    st.session_state.manual_inputs['account'].update(manual_account)
                    add_message('user', "✅ Account fields saved")
                    st.session_state.conversation_stage = STAGE_ACCOUNT_VERIFY
                    st.rerun()
        else:
            # All fields present, move to verification
            if not st.session_state.verified['account']:
                st.session_state.conversation_stage = STAGE_ACCOUNT_VERIFY
                st.rerun()

# Stage 3: Account Verification
elif current_stage == STAGE_ACCOUNT_VERIFY:
    call_data = merge_manual_inputs(st.session_state.extracted_data)
    account = call_data.account
    
    with st.chat_message("assistant"):
        st.markdown("**Please review and verify the Account information:**\n\n" + format_entity_for_display('account', account))
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Account looks good", type="primary", use_container_width=True):
            st.session_state.verified['account'] = True
            add_message('user', "✅ Account verified")
            add_message('assistant', "Great! Now let's move on to the **Contact** information.")
            st.session_state.conversation_stage = STAGE_CONTACT
            st.rerun()
    
    with col2:
        if st.button("✏️ Edit Account", use_container_width=True):
            st.session_state.conversation_stage = STAGE_ACCOUNT
            st.rerun()

# Stage 4: Contact Setup
elif current_stage == STAGE_CONTACT:
    call_data = merge_manual_inputs(st.session_state.extracted_data)
    contact = call_data.contact
    
    # Show extracted data first (only once)
    if not any(msg.get('content', '').startswith('**Contact Information:**') for msg in st.session_state.messages):
        if contact:
            contact_info = format_entity_for_display('contact', contact)
            add_message('assistant', f"**Contact Information:**\n\n{contact_info}")
        else:
            add_message('assistant', "I couldn't extract any contact information from the transcript.")
        st.rerun()
    
    missing_fields = get_missing_required_fields('contact', contact)
    
    if missing_fields:
        if not any('Missing' in msg.get('content', '') and 'contact' in msg.get('content', '').lower() for msg in st.session_state.messages[-3:]):
            add_message('assistant', f"I need the following required fields to complete the contact:\n\n**Missing:** {', '.join([f.replace('_', ' ').title() for f in missing_fields])}\n\nPlease fill them in below:")
            st.rerun()
        
        with st.form("contact_input_form"):
            st.markdown("### ✏️ Fill Missing Contact Fields")
            manual_contact = {}
            
            col1, col2 = st.columns(2)
            with col1:
                if 'last_name' in missing_fields:
                    manual_contact['last_name'] = st.text_input("Last Name *", value=st.session_state.manual_inputs['contact'].get('last_name', ''))
                if 'title' in missing_fields:
                    manual_contact['title'] = st.text_input("Title *", value=st.session_state.manual_inputs['contact'].get('title', ''))
                if 'email' in missing_fields:
                    manual_contact['email'] = st.text_input("Email *", value=st.session_state.manual_inputs['contact'].get('email', ''))
            
            with col2:
                # Optional fields
                if 'first_name' not in missing_fields:
                    manual_contact['first_name'] = st.text_input("First Name (optional)", value=st.session_state.manual_inputs['contact'].get('first_name', contact.first_name if contact else ''))
                if 'phone' not in missing_fields:
                    manual_contact['phone'] = st.text_input("Phone (optional)", value=st.session_state.manual_inputs['contact'].get('phone', contact.phone if contact else ''))
            
            if st.form_submit_button("💾 Save Contact Fields", type="primary"):
                st.session_state.manual_inputs['contact'].update(manual_contact)
                add_message('user', "✅ Contact fields saved")
                st.session_state.conversation_stage = STAGE_CONTACT_VERIFY
                st.rerun()
    else:
        if not st.session_state.verified['contact']:
            st.session_state.conversation_stage = STAGE_CONTACT_VERIFY
            st.rerun()

# Stage 5: Contact Verification
elif current_stage == STAGE_CONTACT_VERIFY:
    call_data = merge_manual_inputs(st.session_state.extracted_data)
    contact = call_data.contact
    
    with st.chat_message("assistant"):
        st.markdown("**Please review and verify the Contact information:**\n\n" + format_entity_for_display('contact', contact))
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Contact looks good", type="primary", use_container_width=True):
            st.session_state.verified['contact'] = True
            add_message('user', "✅ Contact verified")
            add_message('assistant', "Excellent! Now let's set up the **Opportunity** information.")
            st.session_state.conversation_stage = STAGE_OPPORTUNITY
            st.rerun()
    
    with col2:
        if st.button("✏️ Edit Contact", use_container_width=True):
            st.session_state.conversation_stage = STAGE_CONTACT
            st.rerun()

# Stage 6: Opportunity Setup
elif current_stage == STAGE_OPPORTUNITY:
    call_data = merge_manual_inputs(st.session_state.extracted_data)
    opportunity = call_data.opportunity
    
    # Show extracted data first (only once)
    if not any(msg.get('content', '').startswith('**Opportunity Information:**') for msg in st.session_state.messages):
        if opportunity:
            opp_info = format_entity_for_display('opportunity', opportunity)
            add_message('assistant', f"**Opportunity Information:**\n\n{opp_info}")
        else:
            add_message('assistant', "I couldn't extract any opportunity information from the transcript.")
        st.rerun()
    
    missing_fields = get_missing_required_fields('opportunity', opportunity)
    
    if missing_fields:
        if not any('Missing' in msg.get('content', '') and 'opportunity' in msg.get('content', '').lower() for msg in st.session_state.messages[-3:]):
            add_message('assistant', f"I need the following required fields to complete the opportunity:\n\n**Missing:** {', '.join([f.replace('_', ' ').title() for f in missing_fields])}\n\nPlease fill them in below:")
            st.rerun()
        
        with st.form("opportunity_input_form"):
            st.markdown("### ✏️ Fill Missing Opportunity Fields")
            manual_opportunity = {}
            
            col1, col2 = st.columns(2)
            with col1:
                if 'name' in missing_fields:
                    manual_opportunity['name'] = st.text_input("Opportunity Name *", value=st.session_state.manual_inputs['opportunity'].get('name', ''))
                if 'amount' in missing_fields:
                    amount_str = st.session_state.manual_inputs['opportunity'].get('amount', '')
                    if amount_str and isinstance(amount_str, (int, float)):
                        amount_str = str(amount_str)
                    manual_opportunity['amount'] = st.text_input("Amount * (e.g., 50000)", value=amount_str)
            
            with col2:
                if 'close_date' in missing_fields:
                    manual_opportunity['close_date'] = st.text_input("Close Date * (e.g., Q2 2025 or 2025-06-30)", value=st.session_state.manual_inputs['opportunity'].get('close_date', ''))
            
            if st.form_submit_button("💾 Save Opportunity Fields", type="primary"):
                st.session_state.manual_inputs['opportunity'].update(manual_opportunity)
                add_message('user', "✅ Opportunity fields saved")
                st.session_state.conversation_stage = STAGE_OPPORTUNITY_VERIFY
                st.rerun()
    else:
        if not st.session_state.verified['opportunity']:
            st.session_state.conversation_stage = STAGE_OPPORTUNITY_VERIFY
            st.rerun()

# Stage 7: Opportunity Verification
elif current_stage == STAGE_OPPORTUNITY_VERIFY:
    call_data = merge_manual_inputs(st.session_state.extracted_data)
    opportunity = call_data.opportunity
    
    with st.chat_message("assistant"):
        st.markdown("**Please review and verify the Opportunity information:**\n\n" + format_entity_for_display('opportunity', opportunity))
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Opportunity looks good", type="primary", use_container_width=True):
            st.session_state.verified['opportunity'] = True
            add_message('user', "✅ Opportunity verified")
            add_message('assistant', "Perfect! Now let me prepare the final review with all the information that will be sent to Salesforce.")
            st.session_state.conversation_stage = STAGE_FINAL_REVIEW
            st.rerun()
    
    with col2:
        if st.button("✏️ Edit Opportunity", use_container_width=True):
            st.session_state.conversation_stage = STAGE_OPPORTUNITY
            st.rerun()

# Stage 8: Final Review
elif current_stage == STAGE_FINAL_REVIEW:
    call_data = merge_manual_inputs(st.session_state.extracted_data)
    
    with st.chat_message("assistant"):
        st.markdown("## 📊 Final Review - Salesforce Records Preview\n\nHere's everything that will be created in Salesforce:")
    
    # Display formatted Salesforce data
    tabs = st.tabs(["🏢 Account", "👤 Contact", "💼 Opportunity", "📋 Deal Summary"])
    
    with tabs[0]:
        if call_data.account:
            account_dict = SalesforceFormatter.format_account(call_data.account)
            st.json(account_dict)
        else:
            st.info("No account data")
    
    with tabs[1]:
        if call_data.contact:
            contact_dict = SalesforceFormatter.format_contact(call_data.contact)
            st.json(contact_dict)
        else:
            st.info("No contact data")
    
    with tabs[2]:
        if call_data.opportunity:
            opp_dict = SalesforceFormatter.format_opportunity(call_data.opportunity)
            st.json(opp_dict)
        else:
            st.info("No opportunity data")
    
    with tabs[3]:
        # Generate deal summary
        deal_summary_parts = []
        if call_data.opportunity:
            if call_data.opportunity.deal_summary:
                deal_summary_parts.append(call_data.opportunity.deal_summary)
            elif call_data.opportunity.description:
                deal_summary_parts.append(call_data.opportunity.description)
            else:
                deal_summary_parts.append("Deal summary will be generated from transcript.")
            
            if call_data.opportunity.next_steps:
                deal_summary_parts.append(f"\n**Next Steps:** {call_data.opportunity.next_steps}")
            
            if call_data.opportunity.meddic:
                meddic = call_data.opportunity.meddic
                meddic_parts = []
                if meddic.identified_pain:
                    meddic_parts.append(f"**Pain Points:** {meddic.identified_pain}")
                if meddic.metrics_notes:
                    meddic_parts.append(f"**Metrics:** {meddic.metrics_notes}")
                if meddic.economic_buyers_notes:
                    meddic_parts.append(f"**Economic Buyer:** {meddic.economic_buyers_notes}")
                if meddic.decision_criteria_notes:
                    meddic_parts.append(f"**Decision Criteria:** {meddic.decision_criteria_notes}")
                if meddic.decision_process_notes:
                    meddic_parts.append(f"**Decision Process:** {meddic.decision_process_notes}")
                if meddic.champion:
                    meddic_parts.append(f"**Champion:** {meddic.champion}")
                
                if meddic_parts:
                    deal_summary_parts.append("\n**MEDDIC Qualification:**\n" + "\n".join(meddic_parts))
        
        deal_summary = "\n".join(deal_summary_parts) if deal_summary_parts else "No deal summary available."
        st.markdown(deal_summary)
        
        # Generate and download docx
        st.markdown("---")
        if call_data.opportunity:
            try:
                docx_bytes = generate_deal_summary_docx(call_data)
                opp_name = call_data.opportunity.name or "Deal_Summary"
                # Clean filename
                filename = re.sub(r'[^\w\s-]', '', opp_name).strip().replace(' ', '_')
                filename = f"{filename}_Deal_Summary.docx"
                
                st.download_button(
                    label="📄 Download Deal Summary as Word Document",
                    data=docx_bytes.getvalue(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error generating document: {str(e)}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        salesforce_available = getattr(st.session_state.agent, 'salesforce_available', False)
        button_label = "🚀 Create Records in Salesforce" if salesforce_available else "👁️ Preview Only (Salesforce not configured)"
        
        if st.button(button_label, type="primary", use_container_width=True):
            with st.spinner("Creating Salesforce records..."):
                try:
                    create_result = st.session_state.agent.create_records_from_data(call_data)
                    
                    if create_result.get("preview_mode"):
                        add_message('assistant', "👁️ Preview mode: Salesforce integration not configured. The records above show what would be created.")
                    else:
                        created_records = create_result.get("created_records", {})
                        if created_records:
                            records_text = "\n".join([f"  • {k}: {v}" for k, v in created_records.items()])
                            add_message('assistant', f"✅ **Success!** Records created in Salesforce:\n\n{records_text}")
                        else:
                            add_message('assistant', "⚠️ No records were created. Please check the errors.")
                    
                    if create_result.get("errors"):
                        error_text = "\n".join([f"  • {e}" for e in create_result["errors"]])
                        add_message('assistant', f"❌ **Errors:**\n\n{error_text}")
                    
                    st.session_state.conversation_stage = STAGE_COMPLETE
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)
    
    with col2:
        if st.button("✏️ Go Back to Edit", use_container_width=True):
            st.session_state.conversation_stage = STAGE_OPPORTUNITY_VERIFY
            st.rerun()

# Stage 9: Complete
elif current_stage == STAGE_COMPLETE:
    with st.chat_message("assistant"):
        st.markdown("🎉 **All done!** Your Salesforce records have been processed.\n\nYou can reset the conversation to process another transcript.")
    
    # Generate and offer download of deal summary docx
    if 'extracted_data' in st.session_state and st.session_state.extracted_data:
        call_data = merge_manual_inputs(st.session_state.extracted_data)
        if call_data.opportunity:
            try:
                docx_bytes = generate_deal_summary_docx(call_data)
                opp_name = call_data.opportunity.name or "Deal_Summary"
                # Clean filename
                filename = re.sub(r'[^\w\s-]', '', opp_name).strip().replace(' ', '_')
                filename = f"{filename}_Deal_Summary.docx"
                
                st.download_button(
                    label="📄 Download Deal Summary as Word Document",
                    data=docx_bytes.getvalue(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"Could not generate document: {str(e)}")
    
    if st.button("🔄 Process Another Transcript", type="primary", use_container_width=True):
        for key in ['conversation_stage', 'messages', 'extracted_data', 'manual_inputs', 'verified', 'transcript_uploaded', 'chat_collection_mode', 'chat_data_extracted', 'questions_asked', 'current_question_category', 'last_assistant_message']:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.conversation_stage = STAGE_TRANSCRIPT
        st.session_state.messages = []
        st.session_state.extracted_data = None
        st.session_state.manual_inputs = {'account': {}, 'contact': {}, 'opportunity': {}}
        st.session_state.verified = {'account': False, 'contact': False, 'opportunity': False}
        st.session_state.transcript_uploaded = False
        st.session_state.chat_collection_mode = False
        st.session_state.chat_data_extracted = False
        st.session_state.questions_asked = []
        st.session_state.current_question_category = None
        st.session_state.last_assistant_message = None
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #666;">Mrs. Salesforce 🤖 - Stop doing busy work; start selling.</p>',
    unsafe_allow_html=True
)
