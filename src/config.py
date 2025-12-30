"""Configuration settings for Mrs. Salesforce agent."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Salesforce Configuration - OAuth Authentication (for Okta SSO)
    SALESFORCE_CLIENT_ID: Optional[str] = os.getenv("SALESFORCE_CLIENT_ID")
    SALESFORCE_CLIENT_SECRET: Optional[str] = os.getenv("SALESFORCE_CLIENT_SECRET")
    SALESFORCE_REFRESH_TOKEN: Optional[str] = os.getenv("SALESFORCE_REFRESH_TOKEN")
    SALESFORCE_INSTANCE_URL: Optional[str] = os.getenv("SALESFORCE_INSTANCE_URL")
    
    @classmethod
    def is_salesforce_configured(cls) -> bool:
        """Check if Salesforce credentials are properly configured (not placeholders)."""
        # Check if all required variables are present
        if not all([cls.SALESFORCE_CLIENT_ID, cls.SALESFORCE_CLIENT_SECRET,
                   cls.SALESFORCE_REFRESH_TOKEN, cls.SALESFORCE_INSTANCE_URL]):
            return False
        
        # Check for placeholder values in instance URL
        instance_url_lower = (cls.SALESFORCE_INSTANCE_URL or "").lower()
        placeholder_urls = [
            "yourinstance", "your", "example", "placeholder", 
            "test.salesforce.com", "localhost"
        ]
        
        for placeholder in placeholder_urls:
            if placeholder in instance_url_lower:
                return False
        
        # Check for placeholder patterns in credentials
        placeholder_patterns = [
            "your_", "your ", "your", "example", "placeholder", 
            "test", "dummy", "fake"
        ]
        
        all_values = [
            cls.SALESFORCE_CLIENT_ID or "",
            cls.SALESFORCE_CLIENT_SECRET or "",
            cls.SALESFORCE_REFRESH_TOKEN or "",
            cls.SALESFORCE_INSTANCE_URL or ""
        ]
        
        for value in all_values:
            value_lower = value.lower()
            for pattern in placeholder_patterns:
                if pattern in value_lower:
                    return False
        
        # Check if values look like real credentials (minimum length checks)
        if (len(cls.SALESFORCE_CLIENT_ID or "") < 10 or
            len(cls.SALESFORCE_CLIENT_SECRET or "") < 10 or
            len(cls.SALESFORCE_REFRESH_TOKEN or "") < 10):
            return False
        
        # Check if instance URL looks valid (should contain salesforce.com)
        if "salesforce.com" not in instance_url_lower:
            return False
        
        return True
    
    # Anthropic/Claude Configuration
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    @classmethod
    def get_anthropic_api_key(cls) -> Optional[str]:
        """Get the Anthropic API key."""
        return cls.ANTHROPIC_API_KEY
    
    # Agent Configuration
    AGENT_NAME: str = "Mrs. Salesforce"
    MODEL_NAME: str = "claude-sonnet-4-20250514"
    
    # MEDDIC Fields (with notes suffix)
    MEDDIC_FIELDS = [
        "metrics_notes",
        "economic_buyers_notes",
        "decision_criteria_notes",
        "decision_process_notes",
        "identified_pain",
        "champion"
    ]
    
    # Slack Configuration
    SLACK_BOT_TOKEN: Optional[str] = os.getenv("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET: Optional[str] = os.getenv("SLACK_SIGNING_SECRET")
    SLACK_APP_TOKEN: Optional[str] = os.getenv("SLACK_APP_TOKEN")
    SLACK_PORT: int = int(os.getenv("SLACK_PORT", "3000"))
