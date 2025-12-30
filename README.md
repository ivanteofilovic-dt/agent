# Combined Agent Platform 🤖

A unified platform combining two powerful AI agents for sales operations:

1. **Mrs. Salesforce** - Processes sales call transcripts and automatically creates Salesforce records with MEDDIC qualification
2. **Sales Trainer** - AI-powered sales coaching and training (coming soon)

## Features

### Mrs. Salesforce Agent
- 📝 **Transcript Processing**: Extracts structured data from call transcripts using Anthropic's Claude AI
- 📄 **Multiple File Formats**: Supports TXT, DOCX, DOC, and PDF file uploads
- 🏢 **Salesforce Integration**: Automatically creates Contact, Account, and Opportunity records
- 📊 **MEDDIC Qualification**: Ensures complete MEDDIC data extraction and prompts for missing fields
- 💬 **Smart Prompting**: Politely prompts users for missing MEDDIC information when needed
- 🎨 **Web UI**: Beautiful Streamlit interface for easy interaction
- 💬 **Slack Integration**: Process transcripts directly from Slack and interactively collect missing fields through chat

### Sales Trainer Agent (Coming Soon)
- 📚 Sales training modules
- 🎯 Performance coaching
- 📊 Training analytics
- 💬 Interactive Q&A

## Quick Start

### 1. Install Dependencies

Using `uv` (recommended):
```bash
uv sync
```

Or using `pip`:
```bash
pip install -e .
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Required for transcript processing
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Required for Salesforce integration (OAuth for Okta SSO)
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_REFRESH_TOKEN=your_refresh_token
SALESFORCE_INSTANCE_URL=https://yourinstance.salesforce.com

# Optional: Slack integration
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret
SLACK_PORT=3000
```

### 3. Run the Unified UI

Using `uv`:
```bash
uv run streamlit run app.py
```

Or using `pip`:
```bash
streamlit run app.py
```

Then open your browser to: **http://localhost:8501**

## Project Structure

```
combined-agent/
├── app.py                    # Unified Streamlit UI (routes to both agents)
├── main.py                   # CLI entry point
├── src/                      # Source code directory
│   ├── agent.py             # Mrs. Salesforce agent
│   ├── app.py               # Mrs. Salesforce UI (standalone)
│   ├── sales_trainer_agent.py  # Sales Trainer agent
│   ├── trainer_ui.py        # Sales Trainer UI
│   ├── transcript_processor.py
│   ├── salesforce_client.py
│   ├── models.py
│   ├── config.py
│   └── ...                  # Other modules
├── pyproject.toml           # Project dependencies
└── README.md                # This file
```

## Usage

### Unified Web UI

The main `app.py` provides a unified interface where you can:
- Switch between agents using the sidebar
- Use Mrs. Salesforce to process transcripts and create Salesforce records
- Access Sales Trainer features (when available)

### Mrs. Salesforce Agent

#### Basic Usage (Python)

```python
from src.agent import MrsSalesforceAgent

agent = MrsSalesforceAgent()

# Process a transcript
result = agent.process_call_transcript(transcript_text, auto_create=True)

# Check MEDDIC completeness
print(f"MEDDIC Completeness: {result['meddic_completeness']}%")
```

#### Command Line

```bash
uv run python main.py [path_to_transcript.txt]
```

### Sales Trainer Agent

The Sales Trainer agent is currently in development. Once available, it will provide:
- Sales call analysis and feedback
- Performance coaching
- Training recommendations

## MEDDIC Fields

The Mrs. Salesforce agent extracts and validates the following MEDDIC qualification fields:

- **Metrics**: Quantifiable business metrics or KPIs
- **Economic Buyer**: Person with budget authority
- **Decision Criteria**: Criteria used for decision making
- **Decision Process**: Steps in the decision process
- **Identify Pain**: Pain points and challenges
- **Champion**: Internal advocate or champion

## Requirements

- Python 3.12+
- uv (recommended) or pip for package management
- Salesforce account with API access (for Mrs. Salesforce)
- Anthropic API key for Claude AI

### Installing uv

If you don't have `uv` installed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or using pip:
```bash
pip install uv
```

### Getting Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key and add it to your `.env` file as `ANTHROPIC_API_KEY`

## Development

### Running Individual Agent UIs

You can also run the individual agent UIs directly:

**Mrs. Salesforce:**
```bash
uv run streamlit run src/app.py
```

**Sales Trainer:**
```bash
uv run streamlit run src/trainer_ui.py
```

### Testing

Run tests for Mrs. Salesforce:
```bash
uv run python src/test_agent.py
```

## Deployment

### 🚀 Quick Deployment (Easiest Options)

For the **easiest** deployment options, see:

📖 **[Deployment Guide](docs/DEPLOYMENT.md)**

This guide covers:
- **Streamlit Cloud** (easiest - 5 minutes)
- **Railway** (very easy, production-ready)
- **Render** (simple, free tier)
- **Docker** (for custom requirements)

### ☁️ Google Cloud Deployment (Advanced)

For deploying everything on Google Cloud, see the comprehensive guide:

📖 **[Google Cloud Deployment Guide](docs/GOOGLE_CLOUD_DEPLOYMENT.md)**

This guide covers:
- All required Google Cloud services and APIs
- Service account setup
- Secret Manager configuration
- Cloud Storage setup
- Deployment architecture
- Cost estimation

## License

Internal use for company agent competition.
