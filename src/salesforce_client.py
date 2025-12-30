"""Salesforce API client for creating records."""
from typing import Optional, Dict, Any
import requests
from simple_salesforce import Salesforce
from config import Config
from models import ContactData, AccountData, OpportunityData, MEDDICData


class SalesforceClient:
    """Client for interacting with Salesforce API."""
    
    def __init__(self):
        """Initialize Salesforce client with OAuth authentication (for Okta SSO)."""
        if not all([Config.SALESFORCE_CLIENT_ID, Config.SALESFORCE_CLIENT_SECRET,
                   Config.SALESFORCE_REFRESH_TOKEN, Config.SALESFORCE_INSTANCE_URL]):
            raise ValueError(
                "OAuth credentials not configured. Please set:\n"
                "- SALESFORCE_CLIENT_ID\n"
                "- SALESFORCE_CLIENT_SECRET\n"
                "- SALESFORCE_REFRESH_TOKEN\n"
                "- SALESFORCE_INSTANCE_URL\n"
                "See OAUTH_SETUP.md for detailed setup instructions.\n"
                "Note: Leave these unset to use preview mode (no Salesforce connection)."
            )
        
        # Additional check for placeholder values
        if not Config.is_salesforce_configured():
            raise ValueError(
                "Salesforce credentials appear to be placeholder values.\n"
                "Please provide real credentials or remove them from .env to use preview mode.\n"
                "See GET_SALESFORCE_CREDENTIALS.md for instructions."
            )
        
        # OAuth authentication with refresh token
        # Get access token using refresh token
        token_url = f"{Config.SALESFORCE_INSTANCE_URL}/services/oauth2/token"
        token_data = {
            "grant_type": "refresh_token",
            "client_id": Config.SALESFORCE_CLIENT_ID,
            "client_secret": Config.SALESFORCE_CLIENT_SECRET,
            "refresh_token": Config.SALESFORCE_REFRESH_TOKEN
        }
        
        response = requests.post(token_url, data=token_data)
        if response.status_code != 200:
            raise ValueError(f"Failed to get access token: {response.text}")
        
        token_response = response.json()
        access_token = token_response.get("access_token")
        instance_url = token_response.get("instance_url") or Config.SALESFORCE_INSTANCE_URL
        
        # Initialize Salesforce with access token
        self.sf = Salesforce(
            instance_url=instance_url,
            session_id=access_token
        )
    
    def create_account(self, account_data: AccountData) -> Optional[str]:
        """
        Create an Account in Salesforce with Record Type "Customer".
        
        Args:
            account_data: Account information
            
        Returns:
            Account ID if successful, None otherwise
        """
        if not account_data.name:
            return None
        
        account_dict = {
            "Name": account_data.name,
        }
        
        # Set Record Type to "Customer"
        # Note: Record Type ID needs to be retrieved, but we'll try to set it by name
        # If Record Type API names are different, adjust accordingly
        try:
            # Try to get Record Type ID for "Customer"
            record_types = self.sf.query(
                "SELECT Id, Name, DeveloperName FROM RecordType WHERE SObjectType = 'Account' AND Name = 'Customer'"
            )
            if record_types.get("records"):
                account_dict["RecordTypeId"] = record_types["records"][0]["Id"]
        except Exception:
            # If Record Type lookup fails, continue without it
            pass
        
        # Add optional fields
        if account_data.industry:
            account_dict["Industry"] = account_data.industry
        if account_data.website:
            account_dict["Website"] = account_data.website
        if account_data.annual_revenue:
            account_dict["AnnualRevenue"] = account_data.annual_revenue
        if account_data.number_of_employees:
            account_dict["NumberOfEmployees"] = account_data.number_of_employees
        if account_data.billing_city:
            account_dict["BillingCity"] = account_data.billing_city
        if account_data.billing_state:
            account_dict["BillingState"] = account_data.billing_state
        if account_data.billing_country:
            account_dict["BillingCountry"] = account_data.billing_country
        if account_data.currency:
            account_dict["CurrencyIsoCode"] = account_data.currency
        if account_data.segment:
            account_dict["Segment__c"] = account_data.segment  # Adjust field API name if different
        if account_data.region:
            account_dict["Region__c"] = account_data.region  # Adjust field API name if different
        
        try:
            result = self.sf.Account.create(account_dict)
            return result.get("id") if result.get("success") else None
        except Exception as e:
            print(f"Error creating account: {e}")
            return None
    
    def create_contact(self, contact_data: ContactData, account_id: Optional[str] = None) -> Optional[str]:
        """
        Create a Contact in Salesforce with Record Type "CRM contact".
        
        Args:
            contact_data: Contact information
            account_id: Optional Account ID to link the contact
            
        Returns:
            Contact ID if successful, None otherwise
        """
        if not contact_data.last_name:
            return None
        
        contact_dict = {
            "LastName": contact_data.last_name,
        }
        
        # Set Record Type to "CRM contact"
        try:
            record_types = self.sf.query(
                "SELECT Id, Name, DeveloperName FROM RecordType WHERE SObjectType = 'Contact' AND Name = 'CRM contact'"
            )
            if record_types.get("records"):
                contact_dict["RecordTypeId"] = record_types["records"][0]["Id"]
        except Exception:
            pass
        
        # Add optional fields
        if contact_data.first_name:
            contact_dict["FirstName"] = contact_data.first_name
        if contact_data.email:
            contact_dict["Email"] = contact_data.email
        if contact_data.phone:
            contact_dict["Phone"] = contact_data.phone
        if contact_data.title:
            contact_dict["Title"] = contact_data.title
        if account_id:
            contact_dict["AccountId"] = account_id
        if contact_data.currency:
            contact_dict["CurrencyIsoCode"] = contact_data.currency
        
        try:
            result = self.sf.Contact.create(contact_dict)
            return result.get("id") if result.get("success") else None
        except Exception as e:
            print(f"Error creating contact: {e}")
            return None
    
    def create_opportunity(self, opportunity_data: OpportunityData, 
                          account_id: Optional[str] = None,
                          contact_id: Optional[str] = None) -> Optional[str]:
        """
        Create an Opportunity in Salesforce with MEDDIC data.
        
        Args:
            opportunity_data: Opportunity information including MEDDIC
            account_id: Account ID to link the opportunity
            contact_id: Contact ID to link the opportunity
            
        Returns:
            Opportunity ID if successful, None otherwise
        """
        if not opportunity_data.name:
            return None
        
        opp_dict = {
            "Name": opportunity_data.name,
            "StageName": opportunity_data.stage or "Identified",
            "ForecastCategory": opportunity_data.forecast_category or "Pipeline",
            "LeadSource": opportunity_data.lead_source or "Call",
        }
        
        # Add optional fields
        if opportunity_data.amount:
            opp_dict["Amount"] = opportunity_data.amount
        if opportunity_data.close_date:
            opp_dict["CloseDate"] = opportunity_data.close_date
        if opportunity_data.probability:
            opp_dict["Probability"] = opportunity_data.probability
        if opportunity_data.deal_summary:
            opp_dict["Description"] = opportunity_data.deal_summary
        elif opportunity_data.description:
            opp_dict["Description"] = opportunity_data.description
        if opportunity_data.next_steps:
            opp_dict["Next_Steps__c"] = opportunity_data.next_steps  # Adjust field API name if different
        if opportunity_data.type:
            opp_dict["Type"] = opportunity_data.type
        if opportunity_data.practice:
            opp_dict["Practice__c"] = opportunity_data.practice  # Adjust field API name if different
        if opportunity_data.region:
            opp_dict["Region__c"] = opportunity_data.region  # Adjust field API name if different
        if opportunity_data.currency:
            opp_dict["CurrencyIsoCode"] = opportunity_data.currency
        if opportunity_data.projected_start_date:
            opp_dict["Projected_Start_Date__c"] = opportunity_data.projected_start_date  # Adjust field API name if different
        if opportunity_data.number_of_weeks:
            opp_dict["Number_of_Weeks__c"] = opportunity_data.number_of_weeks  # Adjust field API name if different
        if account_id:
            opp_dict["AccountId"] = account_id
        
        # Add MEDDIC fields as custom fields (using notes field names)
        if opportunity_data.meddic:
            meddic = opportunity_data.meddic
            # Updated field names with "notes" suffix
            if meddic.metrics_notes:
                opp_dict["MEDDIC_Metrics_Notes__c"] = meddic.metrics_notes
            if meddic.economic_buyers_notes:
                opp_dict["MEDDIC_Economic_Buyers_Notes__c"] = meddic.economic_buyers_notes
            if meddic.decision_criteria_notes:
                opp_dict["MEDDIC_Decision_Criteria_Notes__c"] = meddic.decision_criteria_notes
            if meddic.decision_process_notes:
                opp_dict["MEDDIC_Decision_Process_Notes__c"] = meddic.decision_process_notes
            if meddic.identified_pain:
                opp_dict["MEDDIC_Identified_Pain__c"] = meddic.identified_pain
            if meddic.champion:
                opp_dict["MEDDIC_Champion__c"] = meddic.champion
        
        try:
            result = self.sf.Opportunity.create(opp_dict)
            return result.get("id") if result.get("success") else None
        except Exception as e:
            print(f"Error creating opportunity: {e}")
            # Try without MEDDIC custom fields if they don't exist
            if "MEDDIC" in str(e):
                print("MEDDIC custom fields may not exist in your Salesforce org. Creating opportunity without them.")
                # Remove MEDDIC fields and retry
                opp_dict = {k: v for k, v in opp_dict.items() if not k.startswith("MEDDIC_")}
                try:
                    result = self.sf.Opportunity.create(opp_dict)
                    return result.get("id") if result.get("success") else None
                except Exception as e2:
                    print(f"Error creating opportunity without MEDDIC fields: {e2}")
            return None
    
    def update_opportunity_meddic(self, opportunity_id: str, meddic: MEDDICData) -> bool:
        """
        Update opportunity with MEDDIC data.
        
        Args:
            opportunity_id: Salesforce Opportunity ID
            meddic: MEDDIC data
            
        Returns:
            True if successful, False otherwise
        """
        update_dict = {}
        
        if meddic.metrics_notes:
            update_dict["MEDDIC_Metrics_Notes__c"] = meddic.metrics_notes
        if meddic.economic_buyers_notes:
            update_dict["MEDDIC_Economic_Buyers_Notes__c"] = meddic.economic_buyers_notes
        if meddic.decision_criteria_notes:
            update_dict["MEDDIC_Decision_Criteria_Notes__c"] = meddic.decision_criteria_notes
        if meddic.decision_process_notes:
            update_dict["MEDDIC_Decision_Process_Notes__c"] = meddic.decision_process_notes
        if meddic.identified_pain:
            update_dict["MEDDIC_Identified_Pain__c"] = meddic.identified_pain
        if meddic.champion:
            update_dict["MEDDIC_Champion__c"] = meddic.champion
        
        if not update_dict:
            return False
        
        try:
            result = self.sf.Opportunity.update(opportunity_id, update_dict)
            return result is None  # Success returns None
        except Exception as e:
            print(f"Error updating opportunity MEDDIC: {e}")
            return False
