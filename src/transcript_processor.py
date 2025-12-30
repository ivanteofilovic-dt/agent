"""Process call transcripts and extract sales data."""
import json
import re
from typing import Dict, Any
from models import ContactData, AccountData, OpportunityData, MEDDICData, SalesCallData
from config import Config
from utils import (
    parse_close_date, detect_currency_from_location, estimate_opportunity_amount,
    format_opportunity_name, detect_lead_source, format_deal_summary
)
from anthropic import Anthropic


class TranscriptProcessor:
    """Process call transcripts and extract structured data."""
    
    def __init__(self):
        """Initialize the transcript processor."""
        if Config.ANTHROPIC_API_KEY:
            self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            self.model_name = Config.MODEL_NAME
        else:
            self.client = None
            self.model_name = None
    
    def extract_data(self, transcript: str) -> SalesCallData:
        """
        Extract structured data from call transcript.
        
        Args:
            transcript: The call transcript text
            
        Returns:
            SalesCallData object with extracted information
        """
        if not self.client:
            raise ValueError("Anthropic API key not configured. Please set ANTHROPIC_API_KEY environment variable.")
        
        # Create prompt for data extraction
        extraction_prompt = self._create_extraction_prompt(transcript)
        
        # Call Claude to extract data
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": extraction_prompt}
            ]
        )
        
        # Extract text from response
        response_text = message.content[0].text if message.content else ""
        
        # Parse the response
        extracted_data = self._parse_extraction_response(response_text)
        
        # Post-process extracted data with utility functions
        extracted_data = self._post_process_data(extracted_data, transcript)
        
        # Create summary
        summary = self._generate_summary(transcript)
        
        return SalesCallData(
            contact=extracted_data.get("contact"),
            account=extracted_data.get("account"),
            opportunity=extracted_data.get("opportunity"),
            transcript=transcript,
            summary=summary
        )
    
    def _create_extraction_prompt(self, transcript: str) -> str:
        """Create the prompt for data extraction."""
        return f"""You are an expert sales data extraction assistant. Extract all relevant information from the following sales call transcript and format it as JSON.

Extract the following information:

CONTACT INFORMATION:
- First Name
- Last Name
- Email
- Phone
- Job Title

ACCOUNT INFORMATION:
- Company Name
- Industry (use Google knowledge if needed)
- Website
- Annual Revenue (if mentioned)
- Number of Employees (if mentioned)
- Location (City, State, Country)
- Segment (assume which segment fits based on company size and industry)
- Region (from location)

OPPORTUNITY INFORMATION:
- Project Name or Offering Name (for opportunity name: "Customer name - project name")
- Deal Amount (if mentioned, otherwise estimate based on company size)
- Expected Close Date (if mentioned as quarter like "Q2", extract as-is for parsing)
- Next Steps (if mentioned)
- Type (assume from input - e.g., "New Business", "Renewal", "Upsell")
- Practice (assume from input - e.g., "Cloud", "Data", "Security")
- Projected Start Date (if mentioned)
- Number of Weeks (estimate from timeline if mentioned)

MEDDIC QUALIFICATION DATA (use "notes" suffix):
- Metrics notes: Quantifiable business metrics, KPIs, or ROI metrics mentioned
- Economic Buyers notes: Person with budget authority or decision-making power
- Decision criteria notes: Criteria the prospect will use to evaluate solutions
- Decision process notes: Steps, timeline, and stakeholders in the decision process
- Identified pain: Pain points, challenges, or problems discussed
- Champion: Internal advocate or person who supports the solution (identify from contacts mentioned)

IMPORTANT NOTES:
- Opportunity name format: "Customer name - project name"
- Stage should always be "Identified" for new opportunities
- If Google/Googler is mentioned in call, note it for lead source
- For close dates, extract quarter references as-is (e.g., "Q2", "Q2 2025", "end of Q3")

Return the data as a JSON object with this exact structure:
{{
    "contact": {{
        "first_name": "...",
        "last_name": "...",
        "email": "...",
        "phone": "...",
        "title": "..."
    }},
    "account": {{
        "name": "...",
        "industry": "...",
        "website": "...",
        "annual_revenue": null,
        "number_of_employees": null,
        "billing_city": "...",
        "billing_state": "...",
        "billing_country": "...",
        "segment": "...",
        "region": "..."
    }},
    "opportunity": {{
        "name": "...",
        "amount": null,
        "close_date": null,
        "next_steps": null,
        "type": null,
        "practice": null,
        "projected_start_date": null,
        "number_of_weeks": null,
        "meddic": {{
            "metrics_notes": "...",
            "economic_buyers_notes": "...",
            "decision_criteria_notes": "...",
            "decision_process_notes": "...",
            "identified_pain": "...",
            "champion": "..."
        }}
    }}
}}

TRANSCRIPT:
{transcript}

Return ONLY the JSON object, no additional text."""
    
    def _parse_extraction_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the extraction response from the model."""
        # Clean the response - remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            data = json.loads(text)
            
            # Parse into Pydantic models
            contact = ContactData(**data.get("contact", {})) if data.get("contact") else None
            account = AccountData(**data.get("account", {})) if data.get("account") else None
            
            # Parse MEDDIC data - handle both old and new field names
            meddic_data = data.get("opportunity", {}).get("meddic", {})
            # Map old field names to new ones if needed
            if "metrics" in meddic_data and "metrics_notes" not in meddic_data:
                meddic_data["metrics_notes"] = meddic_data.pop("metrics", None)
            if "economic_buyer" in meddic_data and "economic_buyers_notes" not in meddic_data:
                meddic_data["economic_buyers_notes"] = meddic_data.pop("economic_buyer", None)
            if "decision_criteria" in meddic_data and "decision_criteria_notes" not in meddic_data:
                meddic_data["decision_criteria_notes"] = meddic_data.pop("decision_criteria", None)
            if "decision_process" in meddic_data and "decision_process_notes" not in meddic_data:
                meddic_data["decision_process_notes"] = meddic_data.pop("decision_process", None)
            if "identify_pain" in meddic_data and "identified_pain" not in meddic_data:
                meddic_data["identified_pain"] = meddic_data.pop("identify_pain", None)
            
            meddic = MEDDICData(**meddic_data) if meddic_data else None
            
            # Parse opportunity
            opp_data = data.get("opportunity", {})
            # Set defaults
            opp_data.setdefault("stage", "Identified")
            opp_data.setdefault("forecast_category", "Pipeline")
            opp_data.setdefault("lead_source", "Call")
            
            if meddic:
                opp_data["meddic"] = meddic
            opportunity = OpportunityData(**opp_data) if opp_data else None
            
            return {
                "contact": contact,
                "account": account,
                "opportunity": opportunity
            }
        except json.JSONDecodeError as e:
            # Fallback: try to extract JSON from the response
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return self._parse_extraction_response(json_match.group(0))
            raise ValueError(f"Failed to parse extraction response: {e}")
    
    def _generate_summary(self, transcript: str) -> str:
        """Generate a summary of the call."""
        if not self.client:
            return ""
        
        prompt = f"""Summarize the following sales call transcript in 2-3 sentences. Focus on key points discussed, next steps, and any important decisions made.

TRANSCRIPT:
{transcript}

SUMMARY:"""
        
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text if message.content else ""
        return response_text.strip()
    
    def _post_process_data(self, extracted_data: Dict[str, Any], transcript: str) -> Dict[str, Any]:
        """Post-process extracted data with utility functions."""
        account = extracted_data.get("account")
        contact = extracted_data.get("contact")
        opportunity = extracted_data.get("opportunity")
        
        # Detect currency from account location
        if account:
            currency = detect_currency_from_location(
                country=account.billing_country,
                city=account.billing_city,
                region=account.region
            )
            account.currency = currency
            # Set contact currency to match account
            if contact:
                contact.currency = currency
        
        # Process opportunity
        if opportunity and account:
            # Format opportunity name
            if account.name and opportunity.name:
                # If opportunity name doesn't already include account name
                if account.name not in opportunity.name:
                    opportunity.name = format_opportunity_name(account.name, opportunity.name)
            
            # Detect lead source
            opportunity.lead_source = detect_lead_source(transcript)
            
            # Parse close date
            if opportunity.close_date:
                parsed_date = parse_close_date(opportunity.close_date)
                if parsed_date:
                    opportunity.close_date = parsed_date
            
            # Set currency from account
            opportunity.currency = account.currency
            
            # Estimate amount if not provided
            if not opportunity.amount and account:
                opportunity.amount = estimate_opportunity_amount(
                    industry=account.industry,
                    company_size=account.number_of_employees
                )
            
            # Format deal summary with timestamp
            if opportunity.deal_summary or opportunity.description:
                summary_text = opportunity.deal_summary or opportunity.description or ""
                opportunity.deal_summary = format_deal_summary(
                    summary_text,
                    next_steps=opportunity.next_steps
                )
                opportunity.description = opportunity.deal_summary  # Keep for backward compatibility
        
        return extracted_data
