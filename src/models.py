"""Data models for Mrs. Salesforce agent."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ContactData(BaseModel):
    """Contact information extracted from transcript."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    record_type: str = "CRM contact"  # Always use "CRM contact"
    currency: Optional[str] = None  # Inherited from Account currency


class AccountData(BaseModel):
    """Account information extracted from transcript."""
    name: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    annual_revenue: Optional[float] = None
    number_of_employees: Optional[int] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_country: Optional[str] = None
    currency: Optional[str] = None  # Assumed from HQ location
    segment: Optional[str] = None  # Agent assumes which segment fits
    region: Optional[str] = None  # From Google Search/Input
    record_type: str = "Customer"  # Always use "Customer"


class MEDDICData(BaseModel):
    """MEDDIC qualification data with notes fields."""
    metrics_notes: Optional[str] = Field(None, description="Quantifiable business metrics or KPIs - notes")
    economic_buyers_notes: Optional[str] = Field(None, description="Person with budget authority - notes")
    decision_criteria_notes: Optional[str] = Field(None, description="Criteria used for decision making - notes")
    decision_process_notes: Optional[str] = Field(None, description="Steps in the decision process - notes")
    identified_pain: Optional[str] = Field(None, description="Pain points and challenges")
    champion: Optional[str] = Field(None, description="Internal advocate or champion - agent decides who from contacts")
    
    # Legacy field names for backward compatibility
    @property
    def metrics(self) -> Optional[str]:
        return self.metrics_notes
    
    @property
    def economic_buyer(self) -> Optional[str]:
        return self.economic_buyers_notes
    
    @property
    def decision_criteria(self) -> Optional[str]:
        return self.decision_criteria_notes
    
    @property
    def decision_process(self) -> Optional[str]:
        return self.decision_process_notes
    
    @property
    def identify_pain(self) -> Optional[str]:
        return self.identified_pain
    
    def get_missing_fields(self) -> List[str]:
        """Return list of missing MEDDIC fields."""
        missing = []
        for field in ["metrics_notes", "economic_buyers_notes", "decision_criteria_notes", 
                     "decision_process_notes", "identified_pain", "champion"]:
            value = getattr(self, field)
            if not value or (isinstance(value, str) and not value.strip()):
                missing.append(field)
        return missing
    
    def get_completeness_score(self) -> float:
        """Calculate MEDDIC completeness as a percentage."""
        total = 6
        filled = sum(1 for field in ["metrics_notes", "economic_buyers_notes", "decision_criteria_notes",
                                     "decision_process_notes", "identified_pain", "champion"]
                    if getattr(self, field) and str(getattr(self, field)).strip())
        return (filled / total) * 100


class OpportunityData(BaseModel):
    """Opportunity information extracted from transcript."""
    name: Optional[str] = None  # Format: "Customer name - project name"
    stage: str = "Identified"  # Always start with "Identified"
    forecast_category: str = "Pipeline"  # Always start with "Pipeline"
    amount: Optional[float] = None  # Agent assumes from company data if not mentioned
    close_date: Optional[str] = None  # Parse from Q references (e.g., Q2 = end of June)
    probability: Optional[int] = None
    deal_summary: Optional[str] = None  # Description with timestamps for edits
    next_steps: Optional[str] = None  # Not mandatory but important
    description: Optional[str] = None  # Legacy field, maps to deal_summary
    lead_source: Optional[str] = "Call"  # If Google in call, use "partner-google"
    meddic: Optional[MEDDICData] = None
    type: Optional[str] = None  # Agent assumes from input
    practice: Optional[str] = None  # Agent assumes from input
    region: Optional[str] = None  # Agent assumes from contact location
    currency: Optional[str] = None  # Same as Account currency
    projected_start_date: Optional[str] = None  # From input
    number_of_weeks: Optional[int] = None  # Agent estimates from company data


class SalesCallData(BaseModel):
    """Complete sales call data extracted from transcript."""
    contact: Optional[ContactData] = None
    account: Optional[AccountData] = None
    opportunity: Optional[OpportunityData] = None
    transcript: str
    summary: Optional[str] = None
