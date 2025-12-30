"""Format Salesforce records for display (what would be written)."""
from typing import Dict, Any, Optional
from models import ContactData, AccountData, OpportunityData, MEDDICData


class SalesforceFormatter:
    """Formats Salesforce records for display."""
    
    @staticmethod
    def format_account(account: AccountData) -> Dict[str, Any]:
        """Format account data as it would be written to Salesforce."""
        account_dict = {
            "Name": account.name,
        }
        
        # Add optional fields
        if account.industry:
            account_dict["Industry"] = account.industry
        if account.website:
            account_dict["Website"] = account.website
        if account.annual_revenue:
            account_dict["AnnualRevenue"] = account.annual_revenue
        if account.number_of_employees:
            account_dict["NumberOfEmployees"] = account.number_of_employees
        if account.billing_city:
            account_dict["BillingCity"] = account.billing_city
        if account.billing_state:
            account_dict["BillingState"] = account.billing_state
        if account.billing_country:
            account_dict["BillingCountry"] = account.billing_country
        if account.currency:
            account_dict["CurrencyIsoCode"] = account.currency
        if account.segment:
            account_dict["Segment__c"] = account.segment
        if account.region:
            account_dict["Region__c"] = account.region
        
        # Record Type
        account_dict["RecordTypeId"] = f"<RecordType: {account.record_type}>"
        
        return account_dict
    
    @staticmethod
    def format_contact(contact: ContactData, account_id: Optional[str] = None) -> Dict[str, Any]:
        """Format contact data as it would be written to Salesforce."""
        contact_dict = {
            "LastName": contact.last_name,
        }
        
        # Add optional fields
        if contact.first_name:
            contact_dict["FirstName"] = contact.first_name
        if contact.email:
            contact_dict["Email"] = contact.email
        if contact.phone:
            contact_dict["Phone"] = contact.phone
        if contact.title:
            contact_dict["Title"] = contact.title
        if account_id:
            contact_dict["AccountId"] = account_id
        if contact.currency:
            contact_dict["CurrencyIsoCode"] = contact.currency
        
        # Record Type
        contact_dict["RecordTypeId"] = f"<RecordType: {contact.record_type}>"
        
        return contact_dict
    
    @staticmethod
    def format_opportunity(opportunity: OpportunityData, 
                          account_id: Optional[str] = None,
                          contact_id: Optional[str] = None) -> Dict[str, Any]:
        """Format opportunity data as it would be written to Salesforce."""
        opp_dict = {
            "Name": opportunity.name,
            "StageName": opportunity.stage or "Identified",
            "ForecastCategory": opportunity.forecast_category or "Pipeline",
            "LeadSource": opportunity.lead_source or "Call",
        }
        
        # Add optional fields
        if opportunity.amount:
            opp_dict["Amount"] = opportunity.amount
        if opportunity.close_date:
            opp_dict["CloseDate"] = opportunity.close_date
        if opportunity.probability:
            opp_dict["Probability"] = opportunity.probability
        if opportunity.deal_summary:
            opp_dict["Description"] = opportunity.deal_summary
        elif opportunity.description:
            opp_dict["Description"] = opportunity.description
        if opportunity.next_steps:
            opp_dict["Next_Steps__c"] = opportunity.next_steps
        if opportunity.type:
            opp_dict["Type"] = opportunity.type
        if opportunity.practice:
            opp_dict["Practice__c"] = opportunity.practice
        if opportunity.region:
            opp_dict["Region__c"] = opportunity.region
        if opportunity.currency:
            opp_dict["CurrencyIsoCode"] = opportunity.currency
        if opportunity.projected_start_date:
            opp_dict["Projected_Start_Date__c"] = opportunity.projected_start_date
        if opportunity.number_of_weeks:
            opp_dict["Number_of_Weeks__c"] = opportunity.number_of_weeks
        if account_id:
            opp_dict["AccountId"] = account_id
        
        # Add MEDDIC fields
        if opportunity.meddic:
            meddic = opportunity.meddic
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
        
        return opp_dict
    
    @staticmethod
    def print_salesforce_output(call_data, account_id: Optional[str] = None, 
                                contact_id: Optional[str] = None) -> None:
        """Print formatted output of what would be written to Salesforce."""
        print("\n" + "=" * 80)
        print("📋 WHAT WOULD BE WRITTEN TO SALESFORCE")
        print("=" * 80)
        
        # Account
        if call_data.account:
            print("\n🏢 ACCOUNT (Record Type: Customer)")
            print("-" * 80)
            account_dict = SalesforceFormatter.format_account(call_data.account)
            for key, value in account_dict.items():
                if value is not None:
                    print(f"  {key:30} = {value}")
            print(f"  {'AccountId (after creation)':30} = <will be generated>")
        
        # Contact
        if call_data.contact:
            print("\n👤 CONTACT (Record Type: CRM contact)")
            print("-" * 80)
            contact_dict = SalesforceFormatter.format_contact(call_data.contact, account_id)
            for key, value in contact_dict.items():
                if value is not None:
                    print(f"  {key:30} = {value}")
            print(f"  {'ContactId (after creation)':30} = <will be generated>")
        
        # Opportunity
        if call_data.opportunity:
            print("\n💼 OPPORTUNITY")
            print("-" * 80)
            opp_dict = SalesforceFormatter.format_opportunity(
                call_data.opportunity, 
                account_id=account_id,
                contact_id=contact_id
            )
            for key, value in opp_dict.items():
                if value is not None:
                    # Format long text fields
                    if isinstance(value, str) and len(value) > 60:
                        print(f"  {key:30} = {value[:60]}...")
                    else:
                        print(f"  {key:30} = {value}")
            print(f"  {'OpportunityId (after creation)':30} = <will be generated>")
        
        print("\n" + "=" * 80)
        print("💡 Note: These records would be created in Salesforce when integration is enabled.")
        print("=" * 80 + "\n")





