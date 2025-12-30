"""Main agent handler for Mrs. Salesforce."""
from typing import Dict, Any, Optional, List
from transcript_processor import TranscriptProcessor
from salesforce_client import SalesforceClient
from salesforce_formatter import SalesforceFormatter
from models import SalesCallData, MEDDICData
from config import Config


class MrsSalesforceAgent:
    """Main agent that processes transcripts and creates Salesforce records."""
    
    def __init__(self):
        """Initialize the agent."""
        self.transcript_processor = TranscriptProcessor()
        
        # Only try to initialize Salesforce if credentials are properly configured
        if Config.is_salesforce_configured():
            try:
                self.salesforce_client = SalesforceClient()
                self.salesforce_available = True
            except Exception as e:
                self.salesforce_client = None
                self.salesforce_available = False
                print(f"ℹ️  Salesforce integration not available: {str(e)}")
                print("   Will print what would be written to Salesforce instead.")
        else:
            self.salesforce_client = None
            self.salesforce_available = False
            # Don't print message here - will be shown in UI or when needed
    
    def process_call_transcript(self, transcript: str, 
                                auto_create: bool = True) -> Dict[str, Any]:
        """
        Process a call transcript and create Salesforce records.
        
        Args:
            transcript: The call transcript text
            auto_create: If True, automatically create records. If False, return data for review.
            
        Returns:
            Dictionary with processing results
        """
        # Extract data from transcript
        call_data = self.transcript_processor.extract_data(transcript)
        
        # Check MEDDIC completeness
        meddic_completeness = 0
        missing_meddic_fields = []
        if call_data.opportunity and call_data.opportunity.meddic:
            meddic_completeness = call_data.opportunity.meddic.get_completeness_score()
            missing_meddic_fields = call_data.opportunity.meddic.get_missing_fields()
        
        result = {
            "extracted_data": call_data,
            "meddic_completeness": meddic_completeness,
            "missing_meddic_fields": missing_meddic_fields,
            "created_records": {},
            "errors": []
        }
        
        if not auto_create:
            return result
        
        # Create Salesforce records or print what would be written
        if not self.salesforce_available:
            # Print what would be written to Salesforce
            SalesforceFormatter.print_salesforce_output(call_data)
            result["preview_mode"] = True
            result["message"] = "Salesforce integration not configured. See output above for what would be written."
            return result
        
        # Create Account
        account_id = None
        if call_data.account:
            account_id = self.salesforce_client.create_account(call_data.account)
            if account_id:
                result["created_records"]["account_id"] = account_id
            else:
                result["errors"].append("Failed to create account")
        
        # Create Contact (linked to Account if available)
        contact_id = None
        if call_data.contact:
            contact_id = self.salesforce_client.create_contact(
                call_data.contact, 
                account_id=account_id
            )
            if contact_id:
                result["created_records"]["contact_id"] = contact_id
            else:
                result["errors"].append("Failed to create contact")
        
        # Create Opportunity (linked to Account and Contact)
        opportunity_id = None
        if call_data.opportunity:
            opportunity_id = self.salesforce_client.create_opportunity(
                call_data.opportunity,
                account_id=account_id,
                contact_id=contact_id
            )
            if opportunity_id:
                result["created_records"]["opportunity_id"] = opportunity_id
            else:
                result["errors"].append("Failed to create opportunity")
        
        return result
    
    def create_records_from_data(self, call_data: SalesCallData) -> Dict[str, Any]:
        """
        Create Salesforce records from SalesCallData object.
        
        Args:
            call_data: SalesCallData object with contact, account, and opportunity data
            
        Returns:
            Dictionary with processing results
        """
        # Check MEDDIC completeness
        meddic_completeness = 0
        missing_meddic_fields = []
        if call_data.opportunity and call_data.opportunity.meddic:
            meddic_completeness = call_data.opportunity.meddic.get_completeness_score()
            missing_meddic_fields = call_data.opportunity.meddic.get_missing_fields()
        
        result = {
            "extracted_data": call_data,
            "meddic_completeness": meddic_completeness,
            "missing_meddic_fields": missing_meddic_fields,
            "created_records": {},
            "errors": []
        }
        
        # Create Salesforce records or print what would be written
        if not self.salesforce_available:
            # Print what would be written to Salesforce
            SalesforceFormatter.print_salesforce_output(call_data)
            result["preview_mode"] = True
            result["message"] = "Salesforce integration not configured. See output above for what would be written."
            return result
        
        # Create Account
        account_id = None
        if call_data.account:
            account_id = self.salesforce_client.create_account(call_data.account)
            if account_id:
                result["created_records"]["account_id"] = account_id
            else:
                result["errors"].append("Failed to create account")
        
        # Create Contact (linked to Account if available)
        contact_id = None
        if call_data.contact:
            contact_id = self.salesforce_client.create_contact(
                call_data.contact, 
                account_id=account_id
            )
            if contact_id:
                result["created_records"]["contact_id"] = contact_id
            else:
                result["errors"].append("Failed to create contact")
        
        # Create Opportunity (linked to Account and Contact)
        opportunity_id = None
        if call_data.opportunity:
            opportunity_id = self.salesforce_client.create_opportunity(
                call_data.opportunity,
                account_id=account_id,
                contact_id=contact_id
            )
            if opportunity_id:
                result["created_records"]["opportunity_id"] = opportunity_id
            else:
                result["errors"].append("Failed to create opportunity")
        
        return result
    
    def prompt_for_missing_fields(self, missing_fields: List[str], 
                                  context: Optional[str] = None) -> str:
        """
        Generate a prompt message for missing fields.
        
        Args:
            missing_fields: List of missing MEDDIC field names
            context: Optional context about the call
            
        Returns:
            Prompt message for the user
        """
        if not missing_fields:
            return "All MEDDIC fields are complete! Great job!"
        
        field_descriptions = {
            "metrics_notes": "Quantifiable business metrics or KPIs - notes",
            "economic_buyers_notes": "Person with budget authority - notes",
            "decision_criteria_notes": "Criteria used for decision making - notes",
            "decision_process_notes": "Steps in the decision process - notes",
            "identified_pain": "Pain points and challenges",
            "champion": "Internal advocate or champion (agent decides who from contacts)"
        }
        
        message = f"Hi! I've processed your call transcript, but I need a bit more information to complete the MEDDIC qualification. Please provide the following:\n\n"
        
        for field in missing_fields:
            desc = field_descriptions.get(field, field)
            message += f"• {field.replace('_', ' ').title()}: {desc}\n"
        
        if context:
            message += f"\nContext: {context}\n"
        
        message += "\nPlease provide this information so I can complete your Salesforce entry."
        
        return message
    
    def update_meddic_fields(self, opportunity_id: str, meddic_data: Dict[str, str]) -> bool:
        """
        Update opportunity with additional MEDDIC data.
        
        Args:
            opportunity_id: Salesforce Opportunity ID
            meddic_data: Dictionary of MEDDIC field names to values
            
        Returns:
            True if successful, False otherwise
        """
        if not self.salesforce_client:
            return False
        
        meddic = MEDDICData(**meddic_data)
        return self.salesforce_client.update_opportunity_meddic(opportunity_id, meddic)
