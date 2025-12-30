
import os
import json
import asyncio
from typing import List, Optional, Any
from pydantic import BaseModel, Field, model_validator
from google.adk import Agent
from google.adk.models import Gemini
from google.adk.runners import InMemoryRunner
from src.scoring_framework import FULL_RUBRIC, load_rubric
from src.claude_llm import ClaudeLLM

# Define the output schema for the agent
class ScoreBreakdown(BaseModel):
    metric_name: str
    score: int = Field(ge=0, le=10)
    justification: str

class SectionScore(BaseModel):
    section_name: str
    metrics: List[ScoreBreakdown]
    section_total: int
    
    @model_validator(mode='after')
    def validate_section(self):
        """Validate that section_total matches sum of metrics and doesn't exceed domain max."""
        rubric = load_rubric()
        
        # Find the domain max points for this section
        domain_max = None
        for domain in rubric['domains']:
            if domain['name'] in self.section_name or f"DOMAIN {domain['id']}" in self.section_name:
                domain_max = domain['max_points']
                break
        
        # Calculate actual total from metrics
        calculated_total = sum(m.score for m in self.metrics)
        
        # Validate section_total matches calculated
        if self.section_total != calculated_total:
            raise ValueError(
                f"Section total {self.section_total} does not match sum of metric scores {calculated_total} "
                f"for section '{self.section_name}'"
            )
        
        # Validate doesn't exceed domain max
        if domain_max and self.section_total > domain_max:
            raise ValueError(
                f"Section total {self.section_total} exceeds domain maximum {domain_max} "
                f"for section '{self.section_name}'"
            )
        
        return self

class ScoringResult(BaseModel):
    scores: List[SectionScore]
    total_score: int = Field(ge=0, le=100)
    feedback_summary: str
    recommended_actions: List[str]
    
    @model_validator(mode='after')
    def validate_total(self):
        """Validate that total_score matches sum of section totals."""
        calculated_total = sum(s.section_total for s in self.scores)
        
        if self.total_score != calculated_total:
            raise ValueError(
                f"Total score {self.total_score} does not match sum of section totals {calculated_total}"
            )
        
        if self.total_score > 100:
            raise ValueError(f"Total score {self.total_score} exceeds maximum of 100")
        
        return self

# Create the agent
def create_sales_coach_agent(model_name: str = "gemini-1.5-pro") -> Agent:
    if model_name.lower().startswith("claude"):
        # Use custom Claude LLM adapter
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("Warning: ANTHROPIC_API_KEY not found in environment variables.")
        model = ClaudeLLM(model=model_name)
    else:
        # Default to Gemini
        # Ensure API key is present (will rely on environment variable)
        if not os.environ.get("GOOGLE_API_KEY"):
             print("Warning: GOOGLE_API_KEY not found in environment variables.")
        model = Gemini(model=model_name)

    agent = Agent(
        name="SalesCoach",
        model=model,
        instruction=FULL_RUBRIC,
        output_schema=ScoringResult
    )
    return agent

async def analyze_transcript(transcript: str, model_name: str = "gemini-1.5-pro") -> Optional[ScoringResult]:
    agent = create_sales_coach_agent(model_name)
    runner = InMemoryRunner(agent=agent)
    
    # We wrap the transcript in a user message
    user_message = f"Please analyze the following sales call transcript:\n\n{transcript}"
    
    events = await runner.run_debug(user_message, verbose=False)
    
    last_error = None
    
    # Try to find the text response which should be JSON
    for event in reversed(events):
        # Check for error messages in events
        if hasattr(event, 'error_message') and event.error_message:
            last_error = event.error_message
        
        # For LlmResponse, content is usually in 'content' attribute
        # For ADK events, they inherit from LlmResponse
        # Let's try to extract text from content.parts
        text = None
        
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if part.text:
                    text = part.text
                    break
        
        # Fallback: check 'text' attribute if it exists directly
        if not text and hasattr(event, 'text'):
            text = event.text

        if text:
            # Try to parse JSON
            try:
                # Clean up potential markdown code blocks
                cleaned_text = text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                elif cleaned_text.startswith("```"):
                     # Sometime language tag is missing or different
                    cleaned_text = cleaned_text[3:]
                
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                
                data = json.loads(cleaned_text)
                
                # Validate and create the result
                result = ScoringResult(**data)
                
                # Additional validation: ensure we have exactly 3 sections
                if len(result.scores) != 3:
                    raise ValueError(f"Expected 3 sections, got {len(result.scores)}")
                
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                # Keep searching, maybe another event has the JSON
                print(f"Failed to parse or validate JSON: {e}")
                print(f"Raw text was: {text}")
                last_error = f"JSON Parse/Validation Error: {e}. Raw Text: {text[:200]}..."
                continue
    
    # If we are here, we failed
    if last_error:
        raise RuntimeError(f"Agent Error: {last_error}")
    
    print("Could not parse structured scoring result from agent events.")
    # Check if we can dump event types for debugging
    event_types = [type(e).__name__ for e in events]
    raise RuntimeError(f"No valid response found. Event types: {event_types}")

if __name__ == "__main__":
    # Simple test
    pass
