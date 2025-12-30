
import asyncio
import os
import sys
from dotenv import load_dotenv
from src.agent import analyze_transcript
from src.scoring_framework import FULL_RUBRIC

# Load environment variables
load_dotenv()

def main():
    # Check for transcript file
    transcript_path = "src/data/transcript.txt"
    if len(sys.argv) > 1:
        transcript_path = sys.argv[1]
    
    if not os.path.exists(transcript_path):
        print(f"Error: Transcript file not found at {transcript_path}")
        return

    with open(transcript_path, "r") as f:
        transcript = f.read()

    print(f"Read transcript from {transcript_path} ({len(transcript)} chars)")

    # check for API key
    if not os.environ.get("GOOGLE_API_KEY"):
        print("CRITICAL: GOOGLE_API_KEY not set. The agent will likely fail to call the LLM.")
        print("Please export GOOGLE_API_KEY='your_key_here'")
    
    try:
        events = asyncio.run(analyze_transcript(transcript))
        
        print("\n--- Analysis Complete ---\n")
        
        # Simple event dumper to see what happened
        for i, event in enumerate(events):
            # Try to find the structured output
            # Event structure is complex, usually has 'type' and data
            # We'll try to print meaningful parts
            print(f"Event {i}: {type(event)}")
            if hasattr(event, 'type'):
                print(f"  Type: {event.type}")
            
            # If we find a model response with text, print it
            # This is a heuristic since we can't verify the event structure perfectly without running
            # But looking at the logs, we might see "ModelResponse"
            
            # Use getattr to avoid errors
            text = getattr(event, 'text', None)
            if text:
                print(f"  Text: {text[:100]}...")
                
            # If using output_schema, the result might be in a tool call or a parsed content
            
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
