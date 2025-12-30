# Mrs. Salesforce 🤖

An AI agent that processes sales call transcripts and automatically creates Salesforce records (Contact, Account, and Opportunity) with MEDDIC qualification. Built for Google's ADK (Agent Development Kit).

## Features

- 📝 **Transcript Processing**: Extracts structured data from call transcripts using Anthropic's Claude AI
- 🏢 **Salesforce Integration**: Automatically creates Contact, Account, and Opportunity records
- 📊 **MEDDIC Qualification**: Ensures complete MEDDIC data extraction and prompts for missing fields
- 💬 **Smart Prompting**: Politely prompts users for missing MEDDIC information when needed
- 🎨 **Web UI**: Beautiful Streamlit interface for easy interaction
- 💬 **Slack Integration**: Process transcripts directly from Slack and interactively collect missing fields through chat

## MEDDIC Fields

The agent extracts and validates the following MEDDIC qualification fields:

- **Metrics**: Quantifiable business metrics or KPIs
- **Economic Buyer**: Person with budget authority
- **Decision Criteria**: Criteria used for decision making
- **Decision Process**: Steps in the decision process
- **Identify Pain**: Pain points and challenges
- **Champion**: Internal advocate or champion

## Quick Start (Testing)

**Want to test it right away?**

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Create `.env` file with your Anthropic API key:**
   ```bash
   echo "ANTHROPIC_API_KEY=your_key_here" > .env
   ```

3. **Run a quick test:**
   ```bash
   uv run python test_agent.py
   ```
   
   Or start the web UI:
   ```bash
   uv run streamlit run app.py
   ```

📖 **See [TESTING.md](TESTING.md) for complete testing instructions.**

---

## Setup

### 1. Install Dependencies

Using `uv` (recommended):

```bash
uv sync
```

Or if you prefer to install in editable mode:

```bash
uv pip install -e .
```

Using `pip` (alternative):

```bash
pip install -e .
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

**Required for transcript processing:**
- `ANTHROPIC_API_KEY` - Anthropic Claude API key (required)

**Required for Salesforce integration (OAuth for Okta SSO):**
- `SALESFORCE_CLIENT_ID` - Connected App Consumer Key
- `SALESFORCE_CLIENT_SECRET` - Connected App Consumer Secret
- `SALESFORCE_REFRESH_TOKEN` - OAuth refresh token
- `SALESFORCE_INSTANCE_URL` - Your Salesforce instance URL

📖 **See [GET_SALESFORCE_CREDENTIALS.md](GET_SALESFORCE_CREDENTIALS.md) for step-by-step instructions on obtaining all Salesforce credentials.**

### 3. Salesforce Custom Fields

To store MEDDIC data in Salesforce, you'll need to create custom fields on the Opportunity object:

- `MEDDIC_Metrics__c` (Text)
- `MEDDIC_Economic_Buyer__c` (Text)
- `MEDDIC_Decision_Criteria__c` (Text)
- `MEDDIC_Decision_Process__c` (Text)
- `MEDDIC_Identify_Pain__c` (Text)
- `MEDDIC_Champion__c` (Text)

If these fields don't exist, the agent will create the opportunity without them.

## Usage

### Basic Usage

```python
from agent import MrsSalesforceAgent

agent = MrsSalesforceAgent()

# Process a transcript
result = agent.process_call_transcript(transcript_text, auto_create=True)

# Check MEDDIC completeness
print(f"MEDDIC Completeness: {result['meddic_completeness']}%")

# Get prompt for missing fields
if result['missing_meddic_fields']:
    prompt = agent.prompt_for_missing_fields(result['missing_meddic_fields'])
    print(prompt)
```

### Command Line

Using `uv`:
```bash
uv run python main.py [path_to_transcript.txt]
```

Using `pip`:
```bash
python main.py [path_to_transcript.txt]
```

### Web UI (Streamlit)

Launch the interactive web interface:

Using `uv`:
```bash
uv run streamlit run app.py
```

Or use the convenience script:

```bash
./run_ui.sh
```

Using `pip`:
```bash
streamlit run app.py
```

Then open your browser to: **http://localhost:8501**

The UI provides:
- 📝 **Transcript Input**: Paste or upload call transcripts
- 📊 **Data Review**: View extracted contact, account, opportunity, and MEDDIC data
- ✅ **MEDDIC Validation**: See completeness score and missing fields
- 👁️ **Preview Mode**: See what would be written to Salesforce (when integration not configured)
- 🏢 **Record Creation**: Create Salesforce records with one click (when integration configured)
- 🔧 **MEDDIC Updates**: Fill missing fields and update opportunities

📖 **See [TESTING.md](TESTING.md) for a complete testing guide.**

### Slack Integration

Process transcripts directly from Slack and interactively collect missing MEDDIC fields:

1. **Set up Slack app** (see [SLACK_SETUP.md](SLACK_SETUP.md) for detailed instructions):
   - Create a Slack app at [api.slack.com/apps](https://api.slack.com/apps)
   - Configure bot token scopes and event subscriptions
   - Add environment variables to `.env`:
     ```bash
     SLACK_BOT_TOKEN=xoxb-your-token
     SLACK_SIGNING_SECRET=your-secret
     SLACK_PORT=3000
     ```

2. **Start the Slack server**:
   ```bash
   uv run python slack_app.py
   ```

3. **Use in Slack**:
   - Invite the bot to a channel: `/invite @Mrs. Salesforce`
   - Paste a transcript in the channel
   - The bot will process it and ask for missing MEDDIC fields through chat

📖 **See [SLACK_SETUP.md](SLACK_SETUP.md) for complete Slack integration setup instructions.**

### Integration with Google ADK

The agent is designed to be integrated with Google's Agent Development Kit. Use the tools defined in `tools.py`:

```python
from adk_integration_example import register_tools_with_adk
from google.cloud import aiplatform

# Initialize your agent builder
agent_builder = aiplatform.AgentBuilder(...)

# Register tools
register_tools_with_adk(agent_builder)
```

Or use the tools directly:

```python
from tools import process_transcript, update_meddic_fields

# Process a transcript
result = process_transcript(transcript_text)

# Update MEDDIC fields if needed
if result["needs_followup"]:
    update_meddic_fields(
        opportunity_id=result["opportunity_id"],
        meddic_data={"metrics": "...", "economic_buyer": "..."}
    )
```

The main components are:

- `agent.py`: Main agent class with processing logic
- `transcript_processor.py`: Handles transcript analysis and data extraction
- `salesforce_client.py`: Manages Salesforce API interactions
- `models.py`: Data models for structured data
- `tools.py`: ADK tool definitions and functions
- `adk_handler.py`: ADK-specific handler logic
- `slack_bot.py`: Slack bot handler for processing transcripts and collecting missing fields
- `slack_app.py`: Flask server for Slack event handling

## Project Structure

```
mrs-salesforce/
├── main.py                    # Entry point and example usage
├── app.py                     # Streamlit web UI
├── agent.py                   # Main agent handler
├── transcript_processor.py    # Transcript processing and extraction
├── salesforce_client.py       # Salesforce API client
├── models.py                  # Data models
├── config.py                  # Configuration management
├── utils.py                   # Utility functions (date parsing, currency detection)
├── tools.py                   # ADK tool definitions
├── adk_handler.py             # ADK-specific handler
├── adk_integration_example.py # ADK integration examples
├── slack_bot.py               # Slack bot handler
├── slack_app.py               # Flask server for Slack events
├── run_ui.sh                  # Convenience script to run UI
├── pyproject.toml             # Project dependencies
├── requirements.txt           # Python requirements
├── SLACK_SETUP.md             # Slack integration setup guide
└── README.md                  # This file
```

## How It Works

1. **Transcript Input**: Receives a sales call transcript
2. **Data Extraction**: Uses Anthropic Claude to extract structured data (Contact, Account, Opportunity, MEDDIC)
3. **MEDDIC Validation**: Checks completeness of MEDDIC fields
4. **Salesforce Creation**: Creates records in Salesforce (Account → Contact → Opportunity)
5. **Missing Field Prompting**: If MEDDIC fields are missing, generates a polite prompt for the user

## Example

```python
transcript = """
Sales Rep: Hi, I'm calling about our solution...
Prospect: I'm John from Acme Corp. We're looking to improve...
...
"""

agent = MrsSalesforceAgent()
result = agent.process_call_transcript(transcript)

# Result contains:
# - extracted_data: Full SalesCallData object
# - meddic_completeness: Percentage (0-100)
# - missing_meddic_fields: List of missing fields
# - created_records: Dict of created Salesforce record IDs
# - errors: List of any errors encountered
```

## Requirements

- Python 3.12+
- uv (recommended) or pip for package management
- Salesforce account with API access
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

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

## License

Internal use for company agent competition.
