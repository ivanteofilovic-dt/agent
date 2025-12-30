"""Main entry point for Mrs. Salesforce agent."""
import sys
from agent import MrsSalesforceAgent


def main():
    """Main function to run the agent."""
    print("🤖 Mrs. Salesforce - Your AI Sales Assistant")
    print("=" * 50)
    
    # Initialize agent
    agent = MrsSalesforceAgent()
    
    # Example usage - you can modify this for your ADK integration
    if len(sys.argv) > 1:
        # If transcript provided as argument
        transcript_path = sys.argv[1]
        with open(transcript_path, 'r') as f:
            transcript = f.read()
    else:
        # Example transcript
        transcript = """
        Sales Rep: Hi, thanks for taking the time to speak with me today. I'm Sarah from TechSolutions.
        
        Prospect: Hi Sarah, I'm John Smith, VP of Operations at Acme Corp. We're looking to improve our customer service efficiency.
        
        Sales Rep: Great to meet you, John. Can you tell me more about the challenges you're facing?
        
        Prospect: Well, our customer service team is handling about 500 tickets per day, but our resolution time has increased by 30% over the past year. We're looking for a solution that can help us reduce this time while maintaining quality.
        
        Sales Rep: I understand. What's your target resolution time?
        
        Prospect: We'd like to get back to under 2 hours average. Currently we're at about 3.5 hours.
        
        Sales Rep: And who else is involved in the decision-making process for this type of solution?
        
        Prospect: I'll need to get approval from our CFO, Mary Johnson, since this will be a significant investment. We're looking at a budget of around $150,000 for the right solution.
        
        Sales Rep: Perfect. And what's your timeline for implementing a solution?
        
        Prospect: We'd like to have something in place by Q2 of next year. We'll be evaluating options over the next 3 months.
        
        Sales Rep: Who would be your internal champion for this project?
        
        Prospect: Our IT Director, Tom Wilson, has been pushing for this solution. He'll be heavily involved in the evaluation.
        
        Sales Rep: Excellent. Can you tell me what criteria you'll use to evaluate solutions?
        
        Prospect: We're looking for ease of integration, scalability, and strong ROI. We need to see a clear path to reducing our operational costs.
        """
    
    # Process the transcript
    print("\n📝 Processing call transcript...")
    result = agent.process_call_transcript(transcript, auto_create=True)
    
    # Display results
    print("\n✅ Extraction Complete!")
    print(f"MEDDIC Completeness: {result['meddic_completeness']:.1f}%")
    
    if result.get('preview_mode'):
        print(f"\n{result.get('message', '')}")
    else:
        if result['missing_meddic_fields']:
            print("\n⚠️  Missing MEDDIC Fields:")
            for field in result['missing_meddic_fields']:
                print(f"  - {field.replace('_', ' ').title()}")
            
            # Generate prompt for missing fields
            prompt = agent.prompt_for_missing_fields(
                result['missing_meddic_fields'],
                context=result['extracted_data'].summary
            )
            print("\n💬 Prompt for User:")
            print(prompt)
        
        if result['created_records']:
            print("\n🎉 Created Salesforce Records:")
            for record_type, record_id in result['created_records'].items():
                print(f"  - {record_type}: {record_id}")
        
        if result['errors']:
            print("\n❌ Errors:")
            for error in result['errors']:
                print(f"  - {error}")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
