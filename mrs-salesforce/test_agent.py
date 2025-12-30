"""Test script for Mrs. Salesforce agent."""
from agent import MrsSalesforceAgent


def test_transcript_processing():
    """Test transcript processing without Salesforce integration."""
    agent = MrsSalesforceAgent()
    
    # Test transcript
    test_transcript = """
    Sales Rep: Hi, thanks for taking the time to speak with me today. I'm Sarah from TechSolutions.
    
    Prospect: Hi Sarah, I'm John Smith, VP of Operations at Acme Corp. 
    We're looking to improve our customer service efficiency.
    
    Sales Rep: Great to meet you, John. Can you tell me more about the challenges you're facing?
    
    Prospect: Well, our customer service team is handling about 500 tickets per day, 
    but our resolution time has increased by 30% over the past year. 
    We're looking for a solution that can help us reduce this time while maintaining quality.
    
    Sales Rep: I understand. What's your target resolution time?
    
    Prospect: We'd like to get back to under 2 hours average. Currently we're at about 3.5 hours.
    
    Sales Rep: And who else is involved in the decision-making process for this type of solution?
    
    Prospect: I'll need to get approval from our CFO, Mary Johnson, since this will be 
    a significant investment. We're looking at a budget of around $150,000 for the right solution.
    
    Sales Rep: Perfect. And what's your timeline for implementing a solution?
    
    Prospect: We'd like to have something in place by Q2 of next year. 
    We'll be evaluating options over the next 3 months.
    
    Sales Rep: Who would be your internal champion for this project?
    
    Prospect: Our IT Director, Tom Wilson, has been pushing for this solution. 
    He'll be heavily involved in the evaluation.
    
    Sales Rep: Excellent. Can you tell me what criteria you'll use to evaluate solutions?
    
    Prospect: We're looking for ease of integration, scalability, and strong ROI. 
    We need to see a clear path to reducing our operational costs.
    """
    
    print("Testing transcript processing...")
    print("=" * 50)
    
    # Process without auto-creating (to test extraction)
    result = agent.process_call_transcript(test_transcript, auto_create=False)
    
    print(f"\n✅ Extraction Complete!")
    print(f"MEDDIC Completeness: {result['meddic_completeness']:.1f}%")
    
    if result['extracted_data'].contact:
        print("\n📇 Contact Information:")
        contact = result['extracted_data'].contact
        print(f"  Name: {contact.first_name} {contact.last_name}")
        print(f"  Email: {contact.email}")
        print(f"  Title: {contact.title}")
    
    if result['extracted_data'].account:
        print("\n🏢 Account Information:")
        account = result['extracted_data'].account
        print(f"  Name: {account.name}")
        print(f"  Industry: {account.industry}")
    
    if result['extracted_data'].opportunity:
        print("\n💼 Opportunity Information:")
        opp = result['extracted_data'].opportunity
        print(f"  Name: {opp.name}")
        print(f"  Stage: {opp.stage}")
        print(f"  Amount: ${opp.amount:,.0f}" if opp.amount else "  Amount: Not specified")
        print(f"  Close Date: {opp.close_date or 'Not specified'}")
        
        if opp.meddic:
            print("\n📊 MEDDIC Data:")
            meddic = opp.meddic
            print(f"  Metrics: {meddic.metrics or 'Not specified'}")
            print(f"  Economic Buyer: {meddic.economic_buyer or 'Not specified'}")
            print(f"  Decision Criteria: {meddic.decision_criteria or 'Not specified'}")
            print(f"  Decision Process: {meddic.decision_process or 'Not specified'}")
            print(f"  Pain Points: {meddic.identify_pain or 'Not specified'}")
            print(f"  Champion: {meddic.champion or 'Not specified'}")
    
    if result['missing_meddic_fields']:
        print(f"\n⚠️  Missing MEDDIC Fields: {', '.join(result['missing_meddic_fields'])}")
        prompt = agent.prompt_for_missing_fields(
            result['missing_meddic_fields'],
            context=result['extracted_data'].summary
        )
        print("\n💬 Prompt for Missing Fields:")
        print(prompt)
    else:
        print("\n🎉 All MEDDIC fields are complete!")
    
    if result['extracted_data'].summary:
        print(f"\n📝 Call Summary:\n{result['extracted_data'].summary}")
    
    print("\n" + "=" * 50)
    print("Test completed successfully!")


if __name__ == "__main__":
    try:
        test_transcript_processing()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        print("\nMake sure you have:")
        print("1. Set ANTHROPIC_API_KEY in your .env file")
        print("2. Installed all dependencies:")
        print("   - Using uv: uv sync")
        print("   - Using pip: pip install -e .")
