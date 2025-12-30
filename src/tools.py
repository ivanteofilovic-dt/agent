"""Tool definitions for Google ADK integration."""
from typing import Dict, Any, Optional
from adk_handler import ADKHandler


# Initialize handler
_handler = ADKHandler()


def process_transcript(transcript: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a call transcript and create Salesforce records.
    
    This is the main tool function that can be registered with Google ADK.
    
    Args:
        transcript: The call transcript text to process
        session_id: Optional session ID for tracking
        
    Returns:
        Dictionary with processing results and agent response
    """
    return _handler.handle_transcript(transcript, session_id)


def update_meddic_fields(opportunity_id: str, meddic_data: Dict[str, str]) -> Dict[str, Any]:
    """
    Update MEDDIC fields for an opportunity.
    
    Args:
        opportunity_id: Salesforce Opportunity ID
        meddic_data: Dictionary mapping MEDDIC field names to values
                    (e.g., {"metrics": "...", "economic_buyer": "..."})
        
    Returns:
        Dictionary with update results
    """
    return _handler.handle_meddic_update(opportunity_id, meddic_data)


def handle_user_query(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Handle general user queries about the agent.
    
    Args:
        query: User's question or query
        context: Optional context from previous interactions
        
    Returns:
        Dictionary with response
    """
    return _handler.handle_query(query, context)


# Tool definitions for ADK registration
TOOLS = [
    {
        "name": "process_transcript",
        "description": "Process a sales call transcript, extract key information, and create Salesforce records (Account, Contact, Opportunity) with MEDDIC qualification.",
        "parameters": {
            "type": "object",
            "properties": {
                "transcript": {
                    "type": "string",
                    "description": "The full text of the sales call transcript"
                },
                "session_id": {
                    "type": "string",
                    "description": "Optional session ID for tracking the conversation"
                }
            },
            "required": ["transcript"]
        },
        "function": process_transcript
    },
    {
        "name": "update_meddic_fields",
        "description": "Update MEDDIC qualification fields for an existing Salesforce opportunity.",
        "parameters": {
            "type": "object",
            "properties": {
                "opportunity_id": {
                    "type": "string",
                    "description": "The Salesforce Opportunity ID"
                },
                "meddic_data": {
                    "type": "object",
                    "description": "Dictionary of MEDDIC field names to values",
                    "properties": {
                        "metrics": {"type": "string"},
                        "economic_buyer": {"type": "string"},
                        "decision_criteria": {"type": "string"},
                        "decision_process": {"type": "string"},
                        "identify_pain": {"type": "string"},
                        "champion": {"type": "string"}
                    }
                }
            },
            "required": ["opportunity_id", "meddic_data"]
        },
        "function": update_meddic_fields
    },
    {
        "name": "handle_user_query",
        "description": "Handle general queries about the agent's capabilities or MEDDIC framework.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The user's question or query"
                },
                "context": {
                    "type": "object",
                    "description": "Optional context from previous interactions"
                }
            },
            "required": ["query"]
        },
        "function": handle_user_query
    }
]





