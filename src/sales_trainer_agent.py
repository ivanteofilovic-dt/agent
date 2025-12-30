"""Sales Trainer Agent - AI-powered sales coaching and training."""
from typing import Dict, Any, Optional, List
from anthropic import Anthropic
from config import Config
import os
import json
import re


class SalesTrainerAgent:
    """AI agent that helps train sales teams with coaching and analytics."""
    
    def __init__(self):
        """Initialize the sales trainer agent."""
        api_key = Config.get_anthropic_api_key()
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = Anthropic(api_key=api_key)
        self.model_name = Config.MODEL_NAME
        self.initialized = True
    
    def analyze_sales_performance(self, transcript: str, metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a sales call transcript and provide performance feedback.
        
        Args:
            transcript: The sales call transcript
            metrics: Optional performance metrics
            
        Returns:
            Dictionary with analysis results
        """
        if not transcript or not transcript.strip():
            return {
                "status": "error",
                "message": "Transcript is empty. Please provide a valid sales call transcript.",
                "suggestions": [],
                "score": None
            }
        
        # Create analysis prompt
        analysis_prompt = self._create_analysis_prompt(transcript, metrics)
        
        try:
            # Call Claude to analyze the transcript
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": analysis_prompt}
                ]
            )
            
            # Extract text from response
            response_text = message.content[0].text if message.content else ""
            
            # Parse the response
            analysis_result = self._parse_analysis_response(response_text)
            
            return {
                "status": "success",
                "message": analysis_result.get("summary", "Analysis complete."),
                "suggestions": analysis_result.get("suggestions", []),
                "score": analysis_result.get("score"),
                "strengths": analysis_result.get("strengths", []),
                "areas_for_improvement": analysis_result.get("areas_for_improvement", []),
                "detailed_feedback": analysis_result.get("detailed_feedback", {})
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error analyzing transcript: {str(e)}",
                "suggestions": [],
                "score": None
            }
    
    def provide_coaching(self, question: str, context: Optional[str] = None) -> str:
        """
        Provide coaching advice based on a question.
        
        Args:
            question: The coaching question
            context: Optional context about the sales situation
            
        Returns:
            Coaching response
        """
        if not question or not question.strip():
            return "Please ask a specific sales coaching question."
        
        # Create coaching prompt
        coaching_prompt = self._create_coaching_prompt(question, context)
        
        try:
            # Call Claude for coaching advice
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": coaching_prompt}
                ]
            )
            
            # Extract text from response
            response_text = message.content[0].text if message.content else ""
            return response_text.strip()
        except Exception as e:
            return f"I encountered an error while providing coaching advice: {str(e)}. Please try again."
    
    def _create_analysis_prompt(self, transcript: str, metrics: Optional[Dict[str, Any]] = None) -> str:
        """Create the prompt for sales performance analysis."""
        metrics_text = ""
        if metrics:
            metrics_text = f"\n\nAdditional Metrics:\n{json.dumps(metrics, indent=2)}"
        
        return f"""You are an expert sales coach and trainer. Analyze the following sales call transcript and provide comprehensive performance feedback.

Analyze the call across these key dimensions:
1. **Discovery & Qualification**: How well did the rep uncover pain points, needs, and qualification criteria?
2. **Active Listening**: Did the rep listen more than they talked? Did they ask follow-up questions?
3. **Value Communication**: How effectively did the rep communicate value and benefits?
4. **Objection Handling**: How well did the rep handle objections or concerns?
5. **Closing & Next Steps**: Did the rep secure clear next steps and move the deal forward?
6. **Rapport Building**: How well did the rep build trust and rapport with the prospect?
7. **Product Knowledge**: Did the rep demonstrate strong product knowledge?
8. **Time Management**: Was the call well-structured and time-efficient?

Provide your analysis in the following JSON format:
{{
    "score": <overall_score_0_to_100>,
    "summary": "<brief_summary_of_overall_performance>",
    "strengths": ["<strength1>", "<strength2>", ...],
    "areas_for_improvement": ["<area1>", "<area2>", ...],
    "suggestions": [
        {{
            "category": "<category_name>",
            "suggestion": "<specific_actionable_suggestion>",
            "priority": "<high|medium|low>"
        }},
        ...
    ],
    "detailed_feedback": {{
        "discovery": "<feedback>",
        "listening": "<feedback>",
        "value_communication": "<feedback>",
        "objection_handling": "<feedback>",
        "closing": "<feedback>",
        "rapport": "<feedback>",
        "product_knowledge": "<feedback>",
        "time_management": "<feedback>"
    }}
}}

Be specific, actionable, and constructive. Reference specific moments from the transcript when possible.

Sales Call Transcript:
{transcript}{metrics_text}

Provide your analysis as valid JSON only, no additional text before or after."""
    
    def _create_coaching_prompt(self, question: str, context: Optional[str] = None) -> str:
        """Create the prompt for coaching advice."""
        context_text = ""
        if context:
            context_text = f"\n\nContext:\n{context}"
        
        return f"""You are an expert sales coach with years of experience training top-performing sales teams. Provide helpful, actionable coaching advice.

The sales rep is asking: {question}{context_text}

Provide:
- Clear, practical advice
- Specific techniques or frameworks when relevant
- Examples or scenarios if helpful
- Encouragement and constructive feedback

Be conversational, supportive, and focused on helping them improve their sales performance."""
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the analysis response from Claude."""
        try:
            # Try to extract JSON from the response
            # Look for JSON block in markdown code fences
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text
            
            # Parse JSON
            result = json.loads(json_str)
            
            # Validate and set defaults
            if "score" not in result:
                result["score"] = None
            if "suggestions" not in result:
                result["suggestions"] = []
            if "strengths" not in result:
                result["strengths"] = []
            if "areas_for_improvement" not in result:
                result["areas_for_improvement"] = []
            if "detailed_feedback" not in result:
                result["detailed_feedback"] = {}
            if "summary" not in result:
                result["summary"] = "Analysis complete."
            
            return result
        except (json.JSONDecodeError, AttributeError) as e:
            # If JSON parsing fails, create a structured response from the text
            return {
                "score": None,
                "summary": "Analysis completed. See suggestions below.",
                "strengths": [],
                "areas_for_improvement": [],
                "suggestions": [
                    {
                        "category": "General",
                        "suggestion": response_text[:500] if response_text else "Unable to parse analysis.",
                        "priority": "medium"
                    }
                ],
                "detailed_feedback": {}
            }
