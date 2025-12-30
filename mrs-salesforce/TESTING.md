# Testing Guide

This guide will help you test Mrs. Salesforce without needing Salesforce integration.

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

### 2. Set Up Environment Variables

Create a `.env` file with at minimum:

```bash
# Required: Anthropic Claude API Key
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Salesforce (skip for now - will show preview)
# SALESFORCE_CLIENT_ID=...
# SALESFORCE_CLIENT_SECRET=...
# SALESFORCE_REFRESH_TOKEN=...
# SALESFORCE_INSTANCE_URL=...
```

**Get your Anthropic API Key:**
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys"
4. Create a new API key
5. Copy it to your `.env` file

### 3. Test the Agent

#### Option A: Test Script (Recommended for First Test)

```bash
uv run python test_agent.py
```

This will:
- Test transcript processing
- Show extracted data
- Display MEDDIC completeness
- Print what would be written to Salesforce (preview mode)

#### Option B: Command Line Interface

```bash
uv run python main.py
```

This runs with a built-in example transcript. To use your own transcript:

```bash
uv run python main.py path/to/transcript.txt
```

#### Option C: Web UI (Best for Interactive Testing)

```bash
uv run streamlit run app.py
```

Then open your browser to: http://localhost:8501

The UI allows you to:
- Paste transcripts or upload files
- View extracted data in organized tabs
- See MEDDIC completeness
- Preview what would be written to Salesforce

---

## Testing Without Salesforce

Since Salesforce is optional, you can test everything without it:

1. **Don't set Salesforce credentials** - just leave them out of `.env`
2. The agent will automatically enter "preview mode"
3. You'll see formatted output showing what would be written to Salesforce
4. All data extraction and MEDDIC validation still works

---

## Example Test Transcripts

### Minimal Test

```bash
uv run python -c "
from agent import MrsSalesforceAgent
agent = MrsSalesforceAgent()
transcript = '''
Sales Rep: Hi, I'm calling about our solution.
Prospect: Hi, I'm John from Acme Corp. We need help with customer service.
'''
result = agent.process_call_transcript(transcript)
print('✅ Test complete!')
"
```

### Full Test

Use the example in `main.py` or create your own transcript file.

---

## What to Expect

### Successful Test Output

```
🤖 Mrs. Salesforce - Your AI Sales Assistant
==================================================

📝 Processing call transcript...

ℹ️  Salesforce integration not configured. Will print what would be written to Salesforce.

================================================================================
📋 WHAT WOULD BE WRITTEN TO SALESFORCE
================================================================================

🏢 ACCOUNT (Record Type: Customer)
--------------------------------------------------------------------------------
  Name                           = Acme Corp
  Industry                       = ...
  ...

👤 CONTACT (Record Type: CRM contact)
--------------------------------------------------------------------------------
  LastName                       = ...
  ...

💼 OPPORTUNITY
--------------------------------------------------------------------------------
  Name                           = ...
  StageName                      = Identified
  ...

✅ Extraction Complete!
MEDDIC Completeness: 83.3%
```

### If Something Goes Wrong

**"Anthropic API key not configured"**
- Make sure `ANTHROPIC_API_KEY` is in your `.env` file
- Check for typos or extra spaces
- Verify the API key is valid

**"Module not found" errors**
- Run `uv sync` or `pip install -e .` again
- Make sure you're in the project directory

**Empty or incomplete extraction**
- Check that your transcript has enough detail
- Try a longer, more detailed transcript
- Verify the API key has sufficient credits/quota

---

## Testing Different Scenarios

### Test with Complete MEDDIC Data

Use a detailed transcript that mentions:
- Metrics/KPIs
- Budget/economic buyer
- Decision criteria
- Decision process
- Pain points
- Champion/internal advocate

### Test with Missing MEDDIC Fields

Use a shorter transcript - the agent should:
- Extract available data
- Identify missing MEDDIC fields
- Generate prompts for missing information

### Test with Multiple Contacts

Include multiple people in the transcript - the agent should identify them.

---

## Next Steps

Once testing works:
1. Review the extracted data quality
2. Check MEDDIC completeness
3. Verify the preview output matches your expectations
4. When ready, add Salesforce credentials to enable actual record creation

---

## Troubleshooting

### Streamlit UI Not Starting

```bash
# Check if port 8501 is in use
lsof -ti:8501

# Kill process if needed
kill -9 $(lsof -ti:8501)

# Or use different port
streamlit run app.py --server.port 8502
```

### Import Errors

```bash
# Make sure you're in the project directory
cd /path/to/mrs-salesforce

# Reinstall dependencies
uv sync --reinstall
```

### API Rate Limits

If you hit rate limits:
- Wait a few minutes
- Check your Anthropic API usage dashboard
- Consider upgrading your API plan

---

## Quick Test Checklist

- [ ] Dependencies installed (`uv sync`)
- [ ] `.env` file created with `ANTHROPIC_API_KEY`
- [ ] Test script runs: `uv run python test_agent.py`
- [ ] CLI runs: `uv run python main.py`
- [ ] UI starts: `uv run streamlit run app.py`
- [ ] Preview output shows correctly
- [ ] MEDDIC completeness calculated
- [ ] Missing fields identified

---

## Need Help?

- Check [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) for environment setup
- Check [README.md](README.md) for general documentation
- Review error messages - they usually indicate what's missing





