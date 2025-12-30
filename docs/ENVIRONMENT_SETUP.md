# Environment Variables Setup Guide

## Required Environment Variables

### For Basic Functionality (Transcript Processing Only)

If you only want to test transcript extraction without Salesforce integration, you only need:

```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**How to get an Anthropic API Key:**
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in with your Anthropic account
3. Navigate to "API Keys" in the dashboard
4. Click "Create Key"
5. Copy the API key and add it to your `.env` file

### For Full Functionality (With Salesforce Integration)

You need all of the following:

#### Salesforce Credentials - OAuth Authentication

We use OAuth authentication which is required for Okta SSO environments:

```bash
SALESFORCE_CLIENT_ID=your_connected_app_client_id
SALESFORCE_CLIENT_SECRET=your_connected_app_client_secret
SALESFORCE_REFRESH_TOKEN=your_refresh_token
SALESFORCE_INSTANCE_URL=https://yourinstance.salesforce.com
```

**📖 For step-by-step instructions on obtaining all Salesforce credentials, see [GET_SALESFORCE_CREDENTIALS.md](GET_SALESFORCE_CREDENTIALS.md).**

**For detailed OAuth setup information, see [OAUTH_SETUP.md](OAUTH_SETUP.md).**

#### Anthropic/Claude (Required for transcript processing)

```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Setup Steps

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file with your credentials:**
   ```bash
   # Use your preferred editor
   nano .env
   # or
   code .env
   # or
   vim .env
   ```

3. **Fill in your credentials:**
   - Replace `your_anthropic_api_key_here` with your actual Anthropic API key
   - Replace Salesforce OAuth credentials with your actual values (see OAUTH_SETUP.md)

4. **Verify the setup:**
   ```bash
   # Test the agent (will check if credentials are loaded)
   uv run python test_agent.py
   ```

## Environment Variable Reference

| Variable | Required | Description | Example |
|----------|----------|------------|---------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic Claude API key for transcript processing | `sk-ant-...` |
| `SALESFORCE_CLIENT_ID` | For Salesforce | Connected App Consumer Key | `3MVG9...` |
| `SALESFORCE_CLIENT_SECRET` | For Salesforce | Connected App Consumer Secret | `ABC123...` |
| `SALESFORCE_REFRESH_TOKEN` | For Salesforce | OAuth refresh token | `5Aep...` |
| `SALESFORCE_INSTANCE_URL` | For Salesforce | Salesforce instance URL | `https://yourinstance.salesforce.com` |

## Security Notes

⚠️ **Important Security Practices:**
- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore`
- Use strong passwords for Salesforce
- Rotate API keys regularly
- For production, use environment variables or secrets management systems

## Testing Your Configuration

### Test Claude API Only:
```bash
uv run python test_agent.py
```

### Test Salesforce Connection:
```bash
uv run python -c "
from salesforce_client import SalesforceClient
try:
    client = SalesforceClient()
    print('✅ Salesforce connection successful!')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

### Test Full Agent:
```bash
uv run python main.py
```

## Troubleshooting

### "Anthropic API key not configured"
- Make sure `ANTHROPIC_API_KEY` is set in your `.env` file
- Check that the `.env` file is in the project root
- Verify the API key is valid and has Claude API access
- Check that your Anthropic account has API access enabled

### "Salesforce credentials not configured"
- This is expected if you only want to test transcript processing
- To use Salesforce features, add all Salesforce credentials to `.env`

### "Invalid Salesforce credentials"
- Verify your Client ID and Client Secret are correct
- Check that your refresh token is valid (not expired)
- Ensure the Connected App is active in Salesforce
- Verify the instance URL is correct
- See [OAUTH_SETUP.md](OAUTH_SETUP.md) for detailed OAuth setup

### "Permission denied" errors
- Check that your Salesforce user has API access enabled
- Verify your user has permission to create Accounts, Contacts, and Opportunities
- Check that your user profile allows API access
