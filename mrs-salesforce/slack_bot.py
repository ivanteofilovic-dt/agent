"""Slack bot handler for Mrs. Salesforce."""
import json
import re
import requests
from typing import Dict, Any, Optional, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from agent import MrsSalesforceAgent
from config import Config
from models import MEDDICData


class SlackBotHandler:
    """Handles Slack bot interactions and transcript processing."""
    
    def __init__(self):
        """Initialize the Slack bot handler."""
        if not Config.SLACK_BOT_TOKEN:
            raise ValueError("SLACK_BOT_TOKEN not configured")
        
        self.client = WebClient(token=Config.SLACK_BOT_TOKEN)
        self.agent = MrsSalesforceAgent()
        
        # Store conversation state: {user_id: {opportunity_id, missing_fields, context}}
        self.conversation_state: Dict[str, Dict[str, Any]] = {}
    
    def handle_message(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle incoming Slack messages.
        
        Args:
            event: Slack event data
            
        Returns:
            Response dictionary or None
        """
        # Ignore bot messages
        if event.get("subtype") == "bot_message":
            return None
        
        text = event.get("text", "")
        user_id = event.get("user")
        channel = event.get("channel")
        
        if not text or not user_id or not channel:
            return None
        
        # Check if user is in a conversation about missing fields
        if user_id in self.conversation_state:
            return self._handle_field_collection(user_id, channel, text)
        
        # Check if message contains a transcript or file
        if self._is_transcript_message(text):
            return self._process_transcript(user_id, channel, text)
        
        # Check for file uploads
        if event.get("files"):
            return self._handle_file_upload(user_id, channel, event.get("files", []))
        
        # Help command
        if text.lower().startswith("help") or text.lower().startswith("hi"):
            return self._send_help_message(channel)
        
        return None
    
    def handle_file_shared(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle file shared events.
        
        Args:
            event: Slack file shared event
            
        Returns:
            Response dictionary or None
        """
        file_id = event.get("file_id")
        user_id = event.get("user_id")
        channel_id = event.get("channel_id")
        
        if not file_id or not user_id or not channel_id:
            return None
        
        try:
            # Download file content
            file_content = self._download_file(file_id)
            
            if file_content:
                return self._process_transcript(user_id, channel_id, file_content)
            else:
                return self._send_message(
                    channel_id,
                    "📎 I received your file, but I can only process text files (.txt) at the moment. Please paste the transcript text directly in the channel."
                )
        except SlackApiError as e:
            print(f"Error handling file: {e}")
            return self._send_message(
                channel_id,
                f"❌ Error processing file: {str(e)}"
            )
    
    def _download_file(self, file_id: str) -> Optional[str]:
        """Download file content from Slack."""
        try:
            # Get file info
            file_info = self.client.files_info(file=file_id)
            file_data = file_info.get("file", {})
            
            # Check if it's a text file
            filetype = file_data.get("filetype", "").lower()
            mimetype = file_data.get("mimetype", "").lower()
            
            if filetype not in ["text", "txt", "docx", "pdf"] and "text" not in mimetype:
                return None
            
            # Get file content
            file_url = file_data.get("url_private")
            if not file_url:
                return None
            
            # Download file using requests with bot token
            headers = {"Authorization": f"Bearer {Config.SLACK_BOT_TOKEN}"}
            response = requests.get(file_url, headers=headers)
            
            if response.status_code == 200:
                # For text files, return content directly
                if filetype in ["text", "txt"] or "text/plain" in mimetype:
                    return response.text
                # For other formats, you might need additional processing
                # For now, return None to indicate we can't process it
                return None
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
        
        return None
    
    def _is_transcript_message(self, text: str) -> bool:
        """Check if message looks like a transcript."""
        # Simple heuristic: if message is long and contains dialogue patterns
        if len(text) < 100:
            return False
        
        # Check for common transcript patterns
        transcript_patterns = [
            r"\w+:\s+",  # "Speaker: " pattern
            r"\[.*?\]",  # Timestamps or metadata
            r"\(.*?\)",  # Parenthetical notes
        ]
        
        matches = sum(1 for pattern in transcript_patterns if re.search(pattern, text))
        return matches >= 1
    
    def _process_transcript(self, user_id: str, channel: str, transcript: str) -> Dict[str, Any]:
        """
        Process a transcript and create Salesforce records.
        
        Args:
            user_id: Slack user ID
            channel: Slack channel ID
            transcript: Transcript text
            
        Returns:
            Response dictionary
        """
        try:
            # Send processing message
            self._send_message(channel, "🔄 Processing transcript...")
            
            # Process transcript
            result = self.agent.process_call_transcript(transcript, auto_create=True)
            
            extracted_data = result.get("extracted_data")
            missing_fields = result.get("missing_meddic_fields", [])
            created_records = result.get("created_records", {})
            errors = result.get("errors", [])
            
            # Build response message
            message_parts = []
            
            if errors:
                message_parts.append("❌ *Errors encountered:*\n" + "\n".join(f"• {e}" for e in errors))
            
            if created_records:
                message_parts.append("✅ *Salesforce Records Created:*")
                if created_records.get("account_id"):
                    message_parts.append(f"• Account: {created_records['account_id']}")
                if created_records.get("contact_id"):
                    message_parts.append(f"• Contact: {created_records['contact_id']}")
                if created_records.get("opportunity_id"):
                    message_parts.append(f"• Opportunity: {created_records['opportunity_id']}")
            
            # Show extracted data summary
            if extracted_data:
                summary_parts = []
                if extracted_data.contact:
                    contact = extracted_data.contact
                    summary_parts.append(f"*Contact:* {contact.first_name or ''} {contact.last_name or ''} ({contact.email or 'No email'})")
                if extracted_data.account:
                    account = extracted_data.account
                    summary_parts.append(f"*Account:* {account.name or 'Unknown'}")
                if extracted_data.opportunity:
                    opp = extracted_data.opportunity
                    summary_parts.append(f"*Opportunity:* {opp.name or 'Unknown'}")
                    if opp.amount:
                        summary_parts.append(f"*Amount:* ${opp.amount:,.2f}")
                
                if summary_parts:
                    message_parts.append("\n*Extracted Data:*\n" + "\n".join(summary_parts))
            
            # Check MEDDIC completeness
            completeness = result.get("meddic_completeness", 0)
            message_parts.append(f"\n*MEDDIC Completeness:* {completeness:.0f}%")
            
            # If fields are missing, start conversation
            if missing_fields and created_records.get("opportunity_id"):
                opportunity_id = created_records["opportunity_id"]
                self.conversation_state[user_id] = {
                    "opportunity_id": opportunity_id,
                    "missing_fields": missing_fields,
                    "channel": channel,
                    "context": extracted_data.summary if extracted_data else None
                }
                
                prompt = self.agent.prompt_for_missing_fields(
                    missing_fields,
                    context=extracted_data.summary if extracted_data else None
                )
                message_parts.append(f"\n\n{prompt}")
            elif missing_fields:
                message_parts.append("\n⚠️ *Note:* Some MEDDIC fields are missing, but no opportunity was created to update.")
            
            # Send response
            response_text = "\n".join(message_parts)
            return self._send_message(channel, response_text)
            
        except Exception as e:
            error_msg = f"❌ Error processing transcript: {str(e)}"
            return self._send_message(channel, error_msg)
    
    def _handle_field_collection(self, user_id: str, channel: str, text: str) -> Dict[str, Any]:
        """
        Handle user responses for missing MEDDIC fields.
        
        Args:
            user_id: Slack user ID
            channel: Slack channel ID
            text: User's response text
            
        Returns:
            Response dictionary
        """
        state = self.conversation_state.get(user_id)
        if not state:
            return None
        
        missing_fields = state.get("missing_fields", [])
        opportunity_id = state.get("opportunity_id")
        
        if not missing_fields or not opportunity_id:
            # Clear state and exit
            del self.conversation_state[user_id]
            return None
        
        # Try to extract field values from user's message
        # This is a simple implementation - you could make it smarter with NLP
        field_values = self._extract_field_values_from_text(text, missing_fields)
        
        # Update opportunity with collected fields
        if field_values:
            success = self.agent.update_meddic_fields(opportunity_id, field_values)
            
            if success:
                # Remove updated fields from missing list
                remaining_fields = [f for f in missing_fields if f not in field_values]
                
                if remaining_fields:
                    state["missing_fields"] = remaining_fields
                    prompt = self.agent.prompt_for_missing_fields(
                        remaining_fields,
                        context=state.get("context")
                    )
                    return self._send_message(channel, f"✅ Updated! Still need:\n\n{prompt}")
                else:
                    # All fields collected
                    del self.conversation_state[user_id]
                    return self._send_message(
                        channel,
                        "🎉 Perfect! All MEDDIC fields have been collected and the opportunity has been updated."
                    )
            else:
                return self._send_message(
                    channel,
                    "❌ Failed to update opportunity. Please try again or contact support."
                )
        else:
            # Couldn't extract fields - ask user to be more specific
            field_descriptions = {
                "metrics_notes": "quantifiable business metrics or KPIs",
                "economic_buyers_notes": "person with budget authority",
                "decision_criteria_notes": "criteria used for decision making",
                "decision_process_notes": "steps in the decision process",
                "identified_pain": "pain points and challenges",
                "champion": "internal advocate or champion"
            }
            
            missing_list = "\n".join(
                f"• *{f.replace('_', ' ').title()}*: {field_descriptions.get(f, f)}"
                for f in missing_fields
            )
            
            return self._send_message(
                channel,
                f"I couldn't extract the missing fields from your message. Please provide information for:\n\n{missing_list}\n\nYou can provide them one at a time or all together."
            )
    
    def _extract_field_values_from_text(self, text: str, missing_fields: List[str]) -> Dict[str, str]:
        """
        Extract field values from user's text message using LLM.
        
        Args:
            text: User's message text
            missing_fields: List of missing field names
            
        Returns:
            Dictionary mapping field names to values
        """
        field_values = {}
        
        # Use the agent's transcript processor to extract field values using LLM
        try:
            from transcript_processor import TranscriptProcessor
            from config import Config
            from anthropic import Anthropic
            
            if not Config.ANTHROPIC_API_KEY:
                # Fallback to simple extraction
                return self._simple_field_extraction(text, missing_fields)
            
            client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            
            # Create prompt for field extraction
            field_descriptions = {
                "metrics_notes": "Quantifiable business metrics, KPIs, or ROI metrics",
                "economic_buyers_notes": "Person with budget authority or decision-making power",
                "decision_criteria_notes": "Criteria the prospect will use to evaluate solutions",
                "decision_process_notes": "Steps, timeline, and stakeholders in the decision process",
                "identified_pain": "Pain points, challenges, or problems",
                "champion": "Internal advocate or person who supports the solution"
            }
            
            missing_fields_desc = "\n".join(
                f"- {field}: {field_descriptions.get(field, field)}"
                for field in missing_fields
            )
            
            prompt = f"""Extract MEDDIC field values from the following user message. The user is providing information to fill in missing MEDDIC fields.

Missing fields to extract:
{missing_fields_desc}

User message:
{text}

Return a JSON object mapping field names to their extracted values. Only include fields that you can clearly extract from the message. If a field is not mentioned, don't include it.

Example format:
{{
    "metrics_notes": "...",
    "economic_buyers_notes": "...",
    "identified_pain": "..."
}}

Return ONLY the JSON object, no additional text."""

            message = client.messages.create(
                model=Config.MODEL_NAME,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text if message.content else ""
            
            # Parse JSON response
            text_clean = response_text.strip()
            if text_clean.startswith("```json"):
                text_clean = text_clean[7:]
            elif text_clean.startswith("```"):
                text_clean = text_clean[3:]
            if text_clean.endswith("```"):
                text_clean = text_clean[:-3]
            text_clean = text_clean.strip()
            
            import json
            extracted = json.loads(text_clean)
            
            # Only return fields that are in missing_fields
            for field in missing_fields:
                if field in extracted and extracted[field]:
                    field_values[field] = str(extracted[field]).strip()
            
        except Exception as e:
            print(f"Error extracting fields with LLM: {e}")
            # Fallback to simple extraction
            return self._simple_field_extraction(text, missing_fields)
        
        return field_values
    
    def _simple_field_extraction(self, text: str, missing_fields: List[str]) -> Dict[str, str]:
        """Simple keyword-based field extraction as fallback."""
        field_values = {}
        text_lower = text.lower()
        
        # Check if user is providing all fields at once
        for field in missing_fields:
            field_keywords = {
                "metrics_notes": ["metric", "kpi", "roi", "measure"],
                "economic_buyers_notes": ["economic buyer", "budget", "decision maker", "authority"],
                "decision_criteria_notes": ["criteria", "evaluation", "decision"],
                "decision_process_notes": ["process", "timeline", "steps", "stakeholder"],
                "identified_pain": ["pain", "problem", "challenge", "issue"],
                "champion": ["champion", "advocate", "supporter", "internal"]
            }
            
            keywords = field_keywords.get(field, [])
            for keyword in keywords:
                if keyword in text_lower:
                    pattern = rf"{keyword}[:\s]+([^\.\n]+)"
                    match = re.search(pattern, text_lower, re.IGNORECASE)
                    if match:
                        field_values[field] = match.group(1).strip()
                        break
        
        # If we couldn't extract specific fields, but there's only one missing field,
        # assume the entire message is for that field
        if not field_values and len(missing_fields) == 1:
            field_values[missing_fields[0]] = text.strip()
        
        return field_values
    
    def _handle_file_upload(self, user_id: str, channel: str, files: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Handle file uploads."""
        # For now, we'll ask users to paste transcript text
        # File handling can be enhanced later
        return self._send_message(
            channel,
            "📎 I see you uploaded a file. For now, please paste the transcript text directly in the channel, or I'll process text files automatically."
        )
    
    def _send_help_message(self, channel: str) -> Dict[str, Any]:
        """Send help message to user."""
        help_text = """👋 *Hi! I'm Mrs. Salesforce*

I can help you process sales call transcripts and create Salesforce records with MEDDIC qualification.

*How to use:*
1. Paste a call transcript in this channel
2. I'll extract contact, account, and opportunity information
3. I'll create records in Salesforce
4. If MEDDIC fields are missing, I'll ask you to provide them through chat

*Commands:*
• `help` - Show this message
• Paste a transcript - Process it automatically

*What I extract:*
• Contact information (name, email, phone, title)
• Account information (company, industry, location)
• Opportunity details (name, amount, close date)
• MEDDIC qualification data

Let me know if you have any questions! 🚀"""
        
        return self._send_message(channel, help_text)
    
    def _send_message(self, channel: str, text: str) -> Dict[str, Any]:
        """
        Send a message to a Slack channel.
        
        Args:
            channel: Slack channel ID
            text: Message text (supports Slack markdown)
            
        Returns:
            Response dictionary
        """
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                mrkdwn=True
            )
            return {"ok": True, "ts": response.get("ts")}
        except SlackApiError as e:
            print(f"Error sending message: {e}")
            return {"ok": False, "error": str(e)}
    
    def clear_conversation_state(self, user_id: str):
        """Clear conversation state for a user."""
        if user_id in self.conversation_state:
            del self.conversation_state[user_id]
