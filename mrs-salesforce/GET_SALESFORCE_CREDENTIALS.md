# How to Obtain Salesforce OAuth Credentials

This guide walks you through getting all the required Salesforce environment variables for OAuth authentication.

## Required Variables

You need these 4 environment variables:
1. `SALESFORCE_CLIENT_ID` - Connected App Consumer Key
2. `SALESFORCE_CLIENT_SECRET` - Connected App Consumer Secret
3. `SALESFORCE_REFRESH_TOKEN` - OAuth refresh token
4. `SALESFORCE_INSTANCE_URL` - Your Salesforce instance URL

---

## Step 1: Create a Connected App in Salesforce

### 1.1 Log into Salesforce
- Log into Salesforce (via Okta SSO if applicable)
- You'll need administrator privileges or access to create Connected Apps

### 1.2 Navigate to App Manager
1. Click the **Setup** gear icon (⚙️) in the top right
2. In the Quick Find box, type "App Manager"
3. Click **App Manager**

### 1.3 Create New Connected App
1. Click **New Connected App** button (top right)
2. Fill in the basic information:
   - **Connected App Name**: `Mrs. Salesforce API` (or any name you prefer)
   - **API Name**: Auto-filled (usually same as Connected App Name)
   - **Contact Email**: Your email address

### 1.4 Enable OAuth Settings
1. Scroll down to **API (Enable OAuth Settings)** section
2. Check the box **Enable OAuth Settings**
3. **Callback URL**: Enter `http://localhost:8080/callback` (or `https://localhost:8080/callback`)
   - This is required but can be any valid URL format
   - You can use `http://localhost` or `http://localhost:8080/callback`
4. **Selected OAuth Scopes**: Move these from Available to Selected:
   - `Full access (full)`
   - `Perform requests on your behalf at any time (refresh_token, offline_access)`
   - Click the **Add** arrow (>) to move them
5. **Require Secret for Web Server Flow**: Check this box ✅
6. Click **Save** (may take a few minutes)

### 1.5 Get Client ID and Client Secret
After saving, you'll see a page with:
- **Consumer Key** → This is your `SALESFORCE_CLIENT_ID`
- **Consumer Secret** → This is your `SALESFORCE_CLIENT_SECRET`
  - Click **Click to reveal** to see the secret
  - **⚠️ IMPORTANT**: Copy this immediately - you won't be able to see it again!

**Copy these values now:**
```bash
SALESFORCE_CLIENT_ID=3MVG9...your_consumer_key_here
SALESFORCE_CLIENT_SECRET=ABC123...your_consumer_secret_here
```

---

## Step 2: Get Your Instance URL

### Option A: From Salesforce Setup (Easiest)
1. Go to **Setup** → **Company Information**
2. Look for **Instance URL** or **My Domain**
3. Your instance URL will be in format: `https://yourcompany.salesforce.com` or `https://yourcompany--sandbox.sandbox.salesforce.com`

### Option B: From Your Browser
- When logged into Salesforce, look at the URL in your browser
- It will be something like: `https://yourcompany.lightning.force.com`
- The instance URL is: `https://yourcompany.salesforce.com` (remove `.lightning.force`)

**Copy this value:**
```bash
SALESFORCE_INSTANCE_URL=https://yourcompany.salesforce.com
```

---

## Step 3: Get Refresh Token

This is the most involved step. You need to perform an OAuth authorization flow to get a refresh token.

### Option A: Using Salesforce CLI (Recommended - Easiest)

#### Install Salesforce CLI
1. Download from: https://developer.salesforce.com/tools/sfdxcli
2. Or install via Homebrew (Mac):
   ```bash
   brew install sfdx-cli
   ```

#### Authenticate
```bash
# Authenticate via browser (will open Okta SSO if configured)
sfdx auth:web:login -a mrs-salesforce

# Get the access token and instance URL
sfdx force:org:display -u mrs-salesforce --json
```

The output will include:
- `accessToken` - You can use this temporarily
- `instanceUrl` - Your instance URL
- But you still need a refresh token...

#### Get Refresh Token via OAuth Flow
```bash
# This will open a browser for authentication
sfdx auth:web:login --instanceurl https://yourcompany.salesforce.com

# After authentication, export the refresh token
sfdx force:org:display -u mrs-salesforce --json | grep refreshToken
```

### Option B: Using OAuth Playground (Easiest for Beginners)

1. Go to [Salesforce OAuth Playground](https://test.salesforce.com/services/oauth2/authorize)
   - For production: https://login.salesforce.com/services/oauth2/authorize
   - For sandbox: https://test.salesforce.com/services/oauth2/authorize

2. Fill in:
   - **Step 1 - Authorization**: 
     - Consumer Key: Your `SALESFORCE_CLIENT_ID`
     - Consumer Secret: Your `SALESFORCE_CLIENT_SECRET`
     - Click **Login**

3. Authorize the app (you'll be redirected through Okta SSO if configured)

4. **Step 2 - Token Request**:
   - You'll see tokens including:
     - `access_token` - Temporary (expires in ~2 hours)
     - `refresh_token` - Long-lived (this is what you need!)
     - `instance_url` - Your instance URL

**Copy the refresh_token:**
```bash
SALESFORCE_REFRESH_TOKEN=5Aep...your_refresh_token_here
```

### Option C: Using Python Script (Automated)

Create a file `get_refresh_token.py`:

```python
"""Helper script to get Salesforce refresh token."""
import requests
import webbrowser
from urllib.parse import urlparse, parse_qs

# Your Connected App credentials from Step 1
CLIENT_ID = "your_client_id_from_step_1"
CLIENT_SECRET = "your_client_secret_from_step_1"
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
    print(f"\nSALESFORCE_CLIENT_ID={CLIENT_ID}")
    print(f"SALESFORCE_CLIENT_SECRET={CLIENT_SECRET}")
    print(f"SALESFORCE_REFRESH_TOKEN={tokens['refresh_token']}")
    print(f"SALESFORCE_INSTANCE_URL={tokens['instance_url']}")
else:
    print(f"\n❌ Error: {tokens}")
```

Run it:
```bash
uv run python get_refresh_token.py
```

### Option D: Manual OAuth Flow (cURL)

1. **Construct authorization URL:**
   ```
   https://login.salesforce.com/services/oauth2/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8080/callback&scope=api%20refresh_token%20offline_access
   ```

2. **Open in browser** and authorize (you'll go through Okta SSO)

3. **Copy the authorization code** from the callback URL (the `code=` parameter)

4. **Exchange for tokens:**
   ```bash
   curl -X POST https://login.salesforce.com/services/oauth2/token \
     -d "grant_type=authorization_code" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "redirect_uri=http://localhost:8080/callback" \
     -d "code=AUTHORIZATION_CODE_FROM_STEP_2"
   ```

5. **Save the `refresh_token` and `instance_url` from the response**

---

## Step 4: Create Your .env File

Create a `.env` file in the project root with all the values:

```bash
# Salesforce OAuth Credentials
SALESFORCE_CLIENT_ID=3MVG9...your_consumer_key
SALESFORCE_CLIENT_SECRET=ABC123...your_consumer_secret
SALESFORCE_REFRESH_TOKEN=5Aep...your_refresh_token
SALESFORCE_INSTANCE_URL=https://yourcompany.salesforce.com

# Anthropic Claude API Key
ANTHROPIC_API_KEY=sk-ant-...your_anthropic_key
```

---

## Step 5: Test Your Configuration

Test that everything works:

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

---

## Troubleshooting

### "Invalid client credentials"
- Double-check your Client ID and Client Secret
- Make sure there are no extra spaces
- Verify the Connected App is still active

### "Invalid refresh token"
- Refresh tokens can expire if not used for 90+ days
- You may need to regenerate it
- Check that your Connected App has `refresh_token` scope enabled

### "Instance URL not found"
- Use the format: `https://yourcompany.salesforce.com`
- For sandboxes: `https://yourcompany--sandbox.sandbox.salesforce.com`
- You can find it in Setup → Company Information

### "Insufficient access rights"
- Ensure your user has API access enabled
- Check that the Connected App has necessary OAuth scopes
- Verify your user can create Accounts, Contacts, and Opportunities

---

## Quick Reference

| Variable | Where to Get It |
|----------|----------------|
| `SALESFORCE_CLIENT_ID` | Connected App → Consumer Key |
| `SALESFORCE_CLIENT_SECRET` | Connected App → Consumer Secret (reveal after creation) |
| `SALESFORCE_REFRESH_TOKEN` | OAuth flow (OAuth Playground, CLI, or Python script) |
| `SALESFORCE_INSTANCE_URL` | Setup → Company Information, or from browser URL |

---

## Security Reminders

⚠️ **Important:**
- Never commit your `.env` file to version control
- Keep your refresh token secure
- Rotate credentials periodically
- Use IP restrictions in Connected App settings if possible





