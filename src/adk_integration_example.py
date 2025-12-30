"""Example integration with Google ADK."""
from typing import Dict, Any
from tools import TOOLS, process_transcript, update_meddic_fields, handle_user_query


def register_tools_with_adk(agent_builder):
    """
    Register tools with Google Agent Builder/ADK.
    
    Example usage:
        from google.cloud import aiplatform
        from adk_integration_example import register_tools_with_adk
        
        agent_builder = aiplatform.AgentBuilder(...)
        register_tools_with_adk(agent_builder)
    """
    for tool in TOOLS:
        agent_builder.add_tool(
            name=tool["name"],
            description=tool["description"],
            function=tool["function"]
        )


def example_usage():
    """Example of how to use the agent tools directly."""
    
    # Example 1: Process a transcript
    transcript = """
    Sales Rep: Hi, thanks for taking the time to speak with me today.
    
    Prospect: Hi, I'm John Smith from Acme Corp. We're looking to improve our efficiency.
    
    Sales Rep: Great! Can you tell me about your current challenges?
    
    Prospect: We're handling about 500 tickets per day and need to reduce resolution time.
    Our target is under 2 hours. We have a budget of around $150,000.
    
    Sales Rep: Who's involved in the decision-making?
    
    Prospect: I'll need approval from our CFO, Mary Johnson. Our IT Director Tom Wilson 
    is championing this project. We're looking to implement by Q2 next year.
    """
    
    print("Processing transcript...")
    result = process_transcript(transcript)
    print(result["response"])
    
    # Example 2: Update MEDDIC fields if missing
    if result["needs_followup"]:
        print("\nUpdating MEDDIC fields...")
        if result["opportunity_id"]:
            meddic_update = {
                "metrics": "Reduce resolution time from 3.5 hours to under 2 hours",
                "decision_criteria": "Ease of integration, scalability, strong ROI"
            }
            update_result = update_meddic_fields(result["opportunity_id"], meddic_update)
            print(update_result["response"])
    
    # Example 3: Handle user query
    print("\nHandling query...")
    query_result = handle_user_query("What is MEDDIC?")
    print(query_result["response"])


if __name__ == "__main__":
    example_usage()





