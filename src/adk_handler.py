"""Google ADK handler for Mrs. Salesforce agent."""
from typing import Dict, Any, Optional
from google.cloud import aiplatform
from agent import MrsSalesforceAgent
from models import SalesCallData


class ADKHandler:
    """Handler for Google Agent Development Kit integration."""
    
    def __init__(self):
        """Initialize the ADK handler."""
        self.agent = MrsSalesforceAgent()
    
    def handle_transcript(self, transcript: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle a transcript processing request from ADK.
        
        Args:
            transcript: The call transcript text
            session_id: Optional session ID for tracking
            
        Returns:
            Dictionary with processing results and response message
        """
        # Process the transcript
        result = self.agent.process_call_transcript(transcript, auto_create=True)
        
        # Build response message
        response_parts = []
        
        # Success message
        if result['created_records']:
            response_parts.append("✅ Successfully processed your call transcript!")
            
            if result['created_records'].get('account_id'):
                response_parts.append(f"📊 Created Account: {result['created_records']['account_id']}")
            if result['created_records'].get('contact_id'):
                response_parts.append(f"👤 Created Contact: {result['created_records']['contact_id']}")
            if result['created_records'].get('opportunity_id'):
                response_parts.append(f"💼 Created Opportunity: {result['created_records']['opportunity_id']}")
        
        # MEDDIC completeness
        completeness = result['meddic_completeness']
        response_parts.append(f"\n📈 MEDDIC Qualification: {completeness:.1f}% complete")
        
        # Missing fields prompt
        if result['missing_meddic_fields']:
            response_parts.append("\n⚠️  I noticed some MEDDIC fields are missing. To ensure perfect qualification, I'd like to gather:")
            
            prompt = self.agent.prompt_for_missing_fields(
                result['missing_meddic_fields'],
                context=result['extracted_data'].summary
            )
            response_parts.append(prompt)
            
            response_parts.append("\n💡 You can provide this information now, and I'll update the opportunity record.")
        else:
            response_parts.append("\n🎉 All MEDDIC fields are complete! Your opportunity is fully qualified.")
        
        # Summary
        if result['extracted_data'].summary:
            response_parts.append(f"\n📝 Call Summary: {result['extracted_data'].summary}")
        
        response_message = "\n".join(response_parts)
        
        return {
            "response": response_message,
            "result": result,
            "session_id": session_id,
            "needs_followup": len(result['missing_meddic_fields']) > 0,
            "missing_fields": result['missing_meddic_fields'],
            "opportunity_id": result['created_records'].get('opportunity_id')
        }
    
    def handle_meddic_update(self, opportunity_id: str, meddic_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Handle MEDDIC field updates.
        
        Args:
            opportunity_id: Salesforce Opportunity ID
            meddic_data: Dictionary of MEDDIC field names to values
            
        Returns:
            Dictionary with update results
        """
        success = self.agent.update_meddic_fields(opportunity_id, meddic_data)
        
        if success:
            return {
                "response": "✅ Successfully updated MEDDIC fields in Salesforce!",
                "success": True
            }
        else:
            return {
                "response": "❌ Failed to update MEDDIC fields. Please check your Salesforce connection.",
                "success": False
            }
    
    def handle_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle general queries about the agent.
        
        Args:
            query: User query
            context: Optional context from previous interactions
            
        Returns:
            Dictionary with response
        """
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["help", "what", "how", "can you"]):
            return {
                "response": """Hi! I'm Mrs. Salesforce, your AI sales assistant. I can help you:

📝 Process call transcripts and extract key information
🏢 Automatically create Salesforce records (Account, Contact, Opportunity)
📊 Ensure MEDDIC qualification is complete
💬 Prompt you for missing information when needed

Just paste your call transcript, and I'll take care of the rest! If any MEDDIC fields are missing, I'll politely ask you to fill them in."""
            }
        
        if "meddic" in query_lower:
            return {
                "response": """MEDDIC is a sales qualification framework. I check for these fields:

📊 Metrics Notes: Quantifiable business metrics or KPIs
💰 Economic Buyers Notes: Person with budget authority
📋 Decision Criteria Notes: Criteria used for decision making
🔄 Decision Process Notes: Steps in the decision process
😣 Identified Pain: Pain points and challenges
⭐ Champion: Internal advocate or champion (I identify from contacts mentioned)

I ensure all these fields are filled to properly qualify your opportunities!"""
            }
        
        return {
            "response": "I'm here to help you process call transcripts and create Salesforce records. Just paste your transcript when you're ready!"
        }
