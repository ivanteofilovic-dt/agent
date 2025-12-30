# OAuth Setup for Okta SSO with Salesforce

This application uses OAuth 2.0 authentication for Salesforce, which is required when using Okta SSO (Single Sign-On).

## Setup Steps

### 1. Create a Connected App in Salesforce

1. Log into Salesforce (via Okta SSO)
2. Go to **Setup** → **App Manager**
3. Click **New Connected App**
4. Fill in the required fields:
   - **Connected App Name**: e.g., "Mrs. Salesforce API"
   - **API Name**: Auto-filled
   - **Contact Email**: Your email
   - **Enable OAuth Settings**: Check this box
   - **Callback URL**: `http://localhost:8080/callback` (or your app's callback URL)
   - **Selected OAuth Scopes**: 
     - `Full access (full)`
     - `Perform requests on your behalf at any time (refresh_token, offline_access)`
   - **Require Secret for Web Server Flow**: Check this box
5. Click **Save**
6. After saving, you'll see:
   - **Consumer Key** (Client ID)
   - **Consumer Secret** (Client Secret)
   - Copy these values

### 2. Get a Refresh Token

You need to perform an initial OAuth flow to get a refresh token. There are several ways to do this:

#### Option A: Using Salesforce CLI (Recommended)

```bash
# Install Salesforce CLI if not already installed
# https://developer.salesforce.com/tools/sfdxcli

# Authenticate (this will open a browser for Okta SSO)
sfdx auth:web:login -a your-alias

# Get the access token and instance URL
sfdx force:org:display -u your-alias --json
```

#### Option B: Using OAuth Playground

1. Go to [Salesforce OAuth Playground](https://test.salesforce.com/services/oauth2/authorize)
2. Use your Connected App's Consumer Key and Consumer Secret
3. Complete the OAuth flow
4. Copy the refresh token

#### Option C: Manual OAuth Flow (Python Script)

Use the provided script `get_refresh_token.py` (see below) or follow these steps:

1. Construct the authorization URL:
   ```
   https://login.salesforce.com/services/oauth2/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8080/callback
   ```
2. Open in browser, authenticate via Okta SSO
3. Copy the authorization code from the callback URL
4. Exchange the code for tokens:
   ```bash
   curl -X POST https://login.salesforce.com/services/oauth2/token \
     -d "grant_type=authorization_code" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "redirect_uri=http://localhost:8080/callback" \
     -d "code=AUTHORIZATION_CODE"
   ```
5. Save the `refresh_token` from the response

### 3. Configure Environment Variables

Add to your `.env` file:

```bash
# Set authentication method to OAuth
SALESFORCE_AUTH_METHOD=oauth

# Connected App credentials
SALESFORCE_CLIENT_ID=your_consumer_key_from_step_1
SALESFORCE_CLIENT_SECRET=your_consumer_secret_from_step_1

# Refresh token from step 2
SALESFORCE_REFRESH_TOKEN=your_refresh_token

# Instance URL (e.g., https://yourcompany.salesforce.com)
SALESFORCE_INSTANCE_URL=https://yourinstance.salesforce.com
```

### 4. Test the Connection

```bash
uv run python -c "
from salesforce_client import SalesforceClient
try:
    client = SalesforceClient()
    print('✅ Salesforce OAuth connection successful!')
    # Test query
    result = client.sf.query('SELECT Id, Name FROM Account LIMIT 1')
    print(f'✅ Test query successful: {len(result.get(\"records\", []))} records')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

## Getting Refresh Token (Python Script)

Create a file `get_refresh_token.py`:

```python
"""Helper script to get Salesforce refresh token for OAuth."""
import requests
import webbrowser
from urllib.parse import urlparse, parse_qs

# Your Connected App credentials
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
REDIRECT_URI = "http://localhost:8080/callback"

# Step 1: Open authorization URL
auth_url = (
    f"https://login.salesforce.com/services/oauth2/authorize"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=api refresh_token offline_access"
)

print("Opening browser for authorization...")
print(f"If browser doesn't open, visit: {auth_url}")
webbrowser.open(auth_url)

# Step 2: Get authorization code from callback URL
print("\nAfter authorizing, you'll be redirected to a callback URL.")
print("Copy the full callback URL and paste it here:")
callback_url = input("Callback URL: ")

# Extract authorization code
parsed = urlparse(callback_url)
params = parse_qs(parsed.query)
auth_code = params.get('code', [None])[0]

if not auth_code:
    print("❌ No authorization code found in URL")
    exit(1)

# Step 3: Exchange code for tokens
token_url = "https://login.salesforce.com/services/oauth2/token"
token_data = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "code": auth_code
}

response = requests.post(token_url, data=token_data)
tokens = response.json()

if "access_token" in tokens:
    print("\n✅ Success! Add these to your .env file:")
    print(f"\nSALESFORCE_AUTH_METHOD=oauth")
    print(f"SALESFORCE_CLIENT_ID={CLIENT_ID}")
    print(f"SALESFORCE_CLIENT_SECRET={CLIENT_SECRET}")
    print(f"SALESFORCE_REFRESH_TOKEN={tokens['refresh_token']}")
    print(f"SALESFORCE_INSTANCE_URL={tokens['instance_url']}")
else:
    print(f"\n❌ Error: {tokens}")
```

## Troubleshooting

### "Invalid refresh token"
- Refresh tokens can expire if not used for 90+ days
- You may need to regenerate the refresh token
- Check that your Connected App settings allow refresh tokens

### "Invalid client credentials"
- Verify your Consumer Key (Client ID) and Consumer Secret are correct
- Make sure there are no extra spaces or characters
- Check that the Connected App is still active

### "Insufficient access rights"
- Ensure your user profile has API access enabled
- Check that the Connected App has the necessary OAuth scopes
- Verify your user has permission to create Accounts, Contacts, and Opportunities

### "Instance URL not found"
- The instance URL should be in format: `https://yourinstance.salesforce.com`
- You can find it in Salesforce: Setup → Company Information → Instance URL
- Or from the OAuth token response

## Configuration

The application uses OAuth authentication exclusively. Add these to your `.env` file:

```bash
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_REFRESH_TOKEN=your_refresh_token
SALESFORCE_INSTANCE_URL=your_instance_url
```

## Security Notes

⚠️ **Important:**
- Keep your refresh token secure - it provides long-term access
- Rotate refresh tokens periodically
- Use environment variables or secrets management
- Never commit tokens to version control
- Consider using IP restrictions in your Connected App settings
