"""Main entry point for Combined Agent Platform."""
import sys
from src.agent import MrsSalesforceAgent


def main():
    """Main function to run the agent."""
    print("🤖 Combined Agent Platform")
    print("=" * 50)
    print("Available agents:")
    print("  1. Mrs. Salesforce - Process transcripts and create Salesforce records")
    print("  2. Sales Trainer - AI-powered sales coaching (coming soon)")
    print("=" * 50)
    print("\nTo use the web UI, run: streamlit run app.py")
    print("\nFor Mrs. Salesforce CLI usage:")
    
    # Initialize agent
    try:
        agent = MrsSalesforceAgent()
        
        # Example usage - you can modify this for your needs
        if len(sys.argv) > 1:
            # If transcript provided as argument
            transcript_path = sys.argv[1]
            with open(transcript_path, 'r') as f:
                transcript = f.read()
            
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
                
                if result['created_records']:
                    print("\n🎉 Created Salesforce Records:")
                    for record_type, record_id in result['created_records'].items():
                        print(f"  - {record_type}: {record_id}")
                
                if result['errors']:
                    print("\n❌ Errors:")
                    for error in result['errors']:
                        print(f"  - {error}")
        else:
            print("\nUsage: python main.py [path_to_transcript.txt]")
            print("Or run the web UI: streamlit run app.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure you have:")
        print("  1. Set up your .env file with ANTHROPIC_API_KEY")
        print("  2. Installed dependencies: uv sync or pip install -e .")
        sys.exit(1)


if __name__ == "__main__":
    main()
