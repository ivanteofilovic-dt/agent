
import json
import os

# Load the rubric from JSON
RUBRIC_JSON_PATH = os.path.join(os.path.dirname(__file__), 'rubric.json')

def load_rubric():
    """Load the rubric from JSON file."""
    with open(RUBRIC_JSON_PATH, 'r') as f:
        return json.load(f)

def format_rubric_for_llm():
    """Format the rubric JSON into a clear, structured format for the LLM."""
    rubric = load_rubric()
    
    formatted = f"# {rubric['rubric_title']}\n\n"
    formatted += "## SCORING RULES - READ CAREFULLY:\n"
    formatted += "- Each metric has a MAXIMUM score (shown below). You CANNOT exceed this maximum.\n"
    formatted += "- Each domain has a MAXIMUM total (shown below). The sum of metric scores in a domain CANNOT exceed this.\n"
    formatted += "- The overall total score has a MAXIMUM of 100 points.\n"
    formatted += "- You MUST calculate: section_total = sum of metric scores in that domain\n"
    formatted += "- You MUST calculate: total_score = sum of all section_totals\n\n"
    
    total_max = 0
    for domain in rubric['domains']:
        total_max += domain['max_points']
        formatted += f"## DOMAIN {domain['id']}: {domain['name']}\n"
        formatted += f"**MAXIMUM POINTS FOR THIS DOMAIN: {domain['max_points']}**\n\n"
        
        formatted += "| Metric Name | Max Score | Measurement Criteria |\n"
        formatted += "| :--- | :--- | :--- |\n"
        
        for metric in domain['metrics']:
            metric_name = metric['metric_name']
            max_score = metric['max_score']
            measurement = metric['measurement']
            formatted += f"| **{metric_name}** | **{max_score}** | {measurement} |\n"
        
        formatted += f"\n**Domain {domain['id']} Maximum Total: {domain['max_points']} points**\n\n"
    
    formatted += f"## OVERALL MAXIMUM: {total_max} points (100 points total)\n\n"
    
    return formatted

FULL_RUBRIC = f"""
{format_rubric_for_llm()}

## CRITICAL INSTRUCTIONS:

1. **Score Each Metric**: For each metric, assign a score from 0 to the metric's MAXIMUM score (as shown in the table above).
   - Domain I metrics: MAXIMUM 10 points each
   - Domain II metrics: MAXIMUM 10 points each  
   - Domain III metrics: MAXIMUM 10 points each

2. **Calculate Section Totals**: Sum the metric scores within each domain.
   - Domain I: Sum of 3 metrics, MAXIMUM 30 points
   - Domain II: Sum of 4 metrics, MAXIMUM 40 points
   - Domain III: Sum of 3 metrics, MAXIMUM 30 points

3. **Calculate Total Score**: Sum all three domain totals.
   - MAXIMUM: 30 + 40 + 30 = 100 points

4. **Provide Justifications**: For each metric score, provide a brief justification citing specific evidence from the transcript.

5. **Feedback Summary**: Provide a comprehensive assessment highlighting strengths and areas for improvement.

6. **Recommended Actions**: Provide specific, actionable recommendations to improve the score.

## OUTPUT FORMAT:

You MUST output a JSON object with this EXACT structure. Do NOT add any fields beyond these:

{{
  "scores": [
    {{
      "section_name": "DOMAIN I: Focus & Scope: The Strategic Architect",
      "metrics": [
        {{
          "metric_name": "C-Suite Relevance",
          "score": <integer 0-10, MAXIMUM 10>,
          "justification": "<string>"
        }},
        {{
          "metric_name": "Transformation Focus",
          "score": <integer 0-10, MAXIMUM 10>,
          "justification": "<string>"
        }},
        {{
          "metric_name": "Business Value Translation",
          "score": <integer 0-10, MAXIMUM 10>,
          "justification": "<string>"
        }}
      ],
      "section_total": <integer 0-30, MAXIMUM 30, must equal sum of 3 metrics above>
    }},
    {{
      "section_name": "DOMAIN II: Deal Qualification: The MEDDPICC Master",
      "metrics": [
        {{
          "metric_name": "Metrics & Identified Pain",
          "score": <integer 0-10, MAXIMUM 10>,
          "justification": "<string>"
        }},
        {{
          "metric_name": "Economic Buyer Access",
          "score": <integer 0-10, MAXIMUM 10>,
          "justification": "<string>"
        }},
        {{
          "metric_name": "Decision Process",
          "score": <integer 0-10, MAXIMUM 10>,
          "justification": "<string>"
        }},
        {{
          "metric_name": "Champion Testing",
          "score": <integer 0-10, MAXIMUM 10>,
          "justification": "<string>"
        }}
      ],
      "section_total": <integer 0-40, MAXIMUM 40, must equal sum of 4 metrics above>
    }},
    {{
      "section_name": "DOMAIN III: Customer Interaction: Challenger & Insight Provider",
      "metrics": [
        {{
          "metric_name": "The 'Reframe' (Teaching)",
          "score": <integer 0-10, MAXIMUM 10>,
          "justification": "<string>"
        }},
        {{
          "metric_name": "Rational Drowning (Data)",
          "score": <integer 0-10, MAXIMUM 10>,
          "justification": "<string>"
        }},
        {{
          "metric_name": "Constructive Tension",
          "score": <integer 0-10, MAXIMUM 10>,
          "justification": "<string>"
        }}
      ],
      "section_total": <integer 0-30, MAXIMUM 30, must equal sum of 3 metrics above>
    }}
  ],
  "total_score": <integer 0-100, MAXIMUM 100, must equal sum of 3 section_totals>,
  "feedback_summary": "<string>",
  "recommended_actions": ["<string>", "<string>", ...]
}}

## VALIDATION CHECKLIST (You must verify before outputting):

✓ Each metric score is between 0 and 10 (inclusive)
✓ Domain I section_total = sum of its 3 metrics, and ≤ 30
✓ Domain II section_total = sum of its 4 metrics, and ≤ 40
✓ Domain III section_total = sum of its 3 metrics, and ≤ 30
✓ total_score = Domain I total + Domain II total + Domain III total, and ≤ 100
✓ All required fields are present
✓ No extra fields are added
"""
