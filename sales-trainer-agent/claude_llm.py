
import os
import json
from typing import AsyncGenerator, Optional, List
from anthropic import AsyncAnthropic
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types as genai_types

def load_rubric_json():
    """Load the rubric JSON for inclusion in system instructions."""
    rubric_path = os.path.join(os.path.dirname(__file__), 'rubric.json')
    with open(rubric_path, 'r') as f:
        return json.load(f)

class ClaudeLLM(BaseLlm):
    """
    Adapter for Anthropic's Claude models to work with Google ADK.
    """
    _client: AsyncAnthropic = None

    def __init__(self, model: str):
        super().__init__(model=model)
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            # We don't raise here to allow initialization, but it will fail on generation if not set later
            print("Warning: ANTHROPIC_API_KEY not set.")
        self._client = AsyncAnthropic(api_key=api_key)

    async def generate_content_async(
        self, 
        llm_request: LlmRequest, 
        stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        
        if not self._client.api_key:
             # Try to get it again in case it was set after init
             self._client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
             if not self._client.api_key:
                 raise ValueError("ANTHROPIC_API_KEY must be set to use Claude models.")

        # Convert ADK/Gemini Content to Anthropic Messages
        system_instruction = ""
        messages = []

        # Let's iterate through contents.
        for content in llm_request.contents:
            role = content.role
            # Map roles: 
            # Gemini: 'user', 'model'
            # Anthropic: 'user', 'assistant'
            
            anthropic_role = "user"
            if role == "model":
                anthropic_role = "assistant"
            elif role == "system":
                # Some frameworks use 'system' role in contents
                # Extract text parts for system prompt
                parts_text = []
                for part in content.parts:
                    if part.text:
                        parts_text.append(part.text)
                system_instruction += "\n".join(parts_text)
                continue
            
            # Convert parts
            anthropic_content = []
            for part in content.parts:
                if part.text:
                    anthropic_content.append({"type": "text", "text": part.text})
                # TODO: Handle other part types like images if needed
            
            if anthropic_content:
                messages.append({
                    "role": anthropic_role,
                    "content": anthropic_content
                })
        
        # Add the rubric JSON to system instruction for reference
        try:
            rubric = load_rubric_json()
            rubric_str = json.dumps(rubric, indent=2)
            system_instruction += f"\n\n=== SCORING RUBRIC (JSON) ===\n"
            system_instruction += f"This is the EXACT rubric you must use for scoring. Pay special attention to max_score and max_points:\n"
            system_instruction += f"```json\n{rubric_str}\n```\n"
            system_instruction += f"\nKEY POINTS FROM RUBRIC:\n"
            for domain in rubric['domains']:
                system_instruction += f"- {domain['name']}: MAXIMUM {domain['max_points']} points total\n"
                for metric in domain['metrics']:
                    system_instruction += f"  - {metric['metric_name']}: MAXIMUM {metric['max_score']} points\n"
            system_instruction += f"- OVERALL TOTAL: MAXIMUM 100 points (30 + 40 + 30)\n"
        except Exception as e:
            print(f"Warning: Could not load rubric JSON: {e}")
        
        # Check for JSON request
        is_json_response = False
        if llm_request.config and getattr(llm_request.config, 'response_mime_type', None) == 'application/json':
            is_json_response = True
            system_instruction += "\n\nIMPORTANT: You must output the result as a valid JSON object matching the requested schema. Do not include any explanations or markdown formatting like ```json. Just the raw JSON string."
        
        # Check for response schema - ADK might store it in different places
        response_schema = None
        
        # Try multiple ways to get the schema
        if llm_request.config:
            response_schema = getattr(llm_request.config, 'response_schema', None)
            if not response_schema:
                response_schema = getattr(llm_request.config, 'responseSchema', None)
            # Check if it's in a nested structure
            if not response_schema and hasattr(llm_request.config, 'responseSchema'):
                try:
                    response_schema = llm_request.config.responseSchema
                except:
                    pass
        
        # Also check if output_schema was set on the request (ADK might set it differently)
        if not response_schema and hasattr(llm_request, 'output_schema'):
            response_schema = llm_request.output_schema
        
        # Check tools_dict - sometimes ADK uses tools for structured output
        if not response_schema and hasattr(llm_request, 'tools_dict') and llm_request.tools_dict:
            # Tools might contain schema info, but for now we'll skip this
            pass
             
        if response_schema:
            # If schema is provided, append it to system instruction
            try:
                # response_schema might be a dict or a Schema object. Try to convert to dict/json.
                schema_dict = None
                if hasattr(response_schema, 'model_json_schema'):
                    # Pydantic model - get JSON schema
                    schema_dict = response_schema.model_json_schema()
                elif hasattr(response_schema, 'to_json_dict'):
                    schema_dict = response_schema.to_json_dict()
                elif hasattr(response_schema, 'model_dump'):
                    schema_dict = response_schema.model_dump()
                elif isinstance(response_schema, dict):
                    schema_dict = response_schema
                else:
                    # Fallback: try to dump it if it's Pydantic-like or just str
                    try:
                        schema_dict = json.loads(str(response_schema)) 
                    except:
                        schema_dict = str(response_schema)
                
                schema_str = json.dumps(schema_dict, indent=2)
                
                # Create a very explicit system instruction with example, referencing rubric max scores
                rubric = load_rubric_json()
                domain_i_max = rubric['domains'][0]['max_points']  # 30
                domain_ii_max = rubric['domains'][1]['max_points']  # 40
                domain_iii_max = rubric['domains'][2]['max_points']  # 30
                
                schema_instruction = (
                    f"\n\n{'='*60}\n"
                    f"CRITICAL: YOU MUST OUTPUT JSON IN THIS EXACT FORMAT\n"
                    f"{'='*60}\n\n"
                    f"SCORING LIMITS (from rubric.json - DO NOT EXCEED):\n"
                    f"- Each metric: MAXIMUM 10 points\n"
                    f"- Domain I (Focus & Scope): MAXIMUM {domain_i_max} points total\n"
                    f"- Domain II (Deal Qualification): MAXIMUM {domain_ii_max} points total\n"
                    f"- Domain III (Customer Interaction): MAXIMUM {domain_iii_max} points total\n"
                    f"- Overall Total: MAXIMUM 100 points ({domain_i_max} + {domain_ii_max} + {domain_iii_max})\n\n"
                    f"Your response MUST be a JSON object with these EXACT fields:\n"
                    f"- 'scores' (array of exactly 3 objects, one per domain)\n"
                    f"- 'total_score' (integer, MAXIMUM 100)\n"
                    f"- 'feedback_summary' (string)\n"
                    f"- 'recommended_actions' (array of strings)\n\n"
                    f"Each item in 'scores' must have:\n"
                    f"- 'section_name' (string matching domain name from rubric)\n"
                    f"- 'metrics' (array of metric objects)\n"
                    f"- 'section_total' (integer, must equal sum of metric scores, and NOT exceed domain max)\n\n"
                    f"Each item in 'metrics' must have:\n"
                    f"- 'metric_name' (string matching metric name from rubric)\n"
                    f"- 'score' (integer 0-10, MAXIMUM 10)\n"
                    f"- 'justification' (string)\n\n"
                    f"VALIDATION RULES (MUST FOLLOW):\n"
                    f"1. Each metric score: 0-10 (MAXIMUM 10)\n"
                    f"2. Domain I section_total: 0-{domain_i_max} (MAXIMUM {domain_i_max}, sum of 3 metrics)\n"
                    f"3. Domain II section_total: 0-{domain_ii_max} (MAXIMUM {domain_ii_max}, sum of 4 metrics)\n"
                    f"4. Domain III section_total: 0-{domain_iii_max} (MAXIMUM {domain_iii_max}, sum of 3 metrics)\n"
                    f"5. total_score: 0-100 (MAXIMUM 100, sum of 3 section_totals)\n"
                    f"6. Output ONLY valid JSON, no markdown, no explanations\n"
                    f"7. Do NOT add any fields beyond: scores, total_score, feedback_summary, recommended_actions\n"
                    f"{'='*60}\n"
                )
                
                system_instruction += schema_instruction
                
            except Exception as e:
                print(f"Warning: Could not serialize response_schema for Claude: {e}")
                import traceback
                traceback.print_exc()

        # Call Claude API
        try:
            if stream:
                full_text = ""
                async with self._client.messages.stream(
                    model=self.model,
                    max_tokens=4096,
                    system=system_instruction,
                    messages=messages,
                ) as stream_response:
                    async for text in stream_response.text_stream:
                        full_text += text
                        # Yield partial responses
                        yield LlmResponse(
                            content=genai_types.Content(
                                role="model",
                                parts=[genai_types.Part.from_text(text=text)]
                            ),
                            partial=True
                        )
                
                # Yield final aggregated response
                yield LlmResponse(
                    content=genai_types.Content(
                        role="model",
                        parts=[genai_types.Part.from_text(text=full_text)]
                    ),
                    partial=False,
                    turnComplete=True
                )
                
            else:
                response = await self._client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_instruction,
                    messages=messages,
                    stream=False
                )
                
                text_content = ""
                for block in response.content:
                    if block.type == "text":
                        text_content += block.text
                
                yield LlmResponse(
                    content=genai_types.Content(
                        role="model",
                        parts=[genai_types.Part.from_text(text=text_content)]
                    ),
                    partial=False,
                    turnComplete=True
                )

        except Exception as e:
            print(f"Error calling Claude: {e}")
            yield LlmResponse(errorMessage=str(e), errorCode="CLAUDE_ERROR")

    # We might need to implement connect() if used by ADK, but generate_content_async is the main one.
    # BaseLlm has connect() but it's for bidirectional streaming.
