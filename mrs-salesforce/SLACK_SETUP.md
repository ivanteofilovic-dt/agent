# Slack Integration Setup Guide

This guide will help you set up the Slack integration for Mrs. Salesforce, allowing you to process call transcripts directly from Slack and interactively collect missing MEDDIC fields.

## Overview

The Slack integration allows you to:
- 📝 Paste call transcripts in Slack channels
- 🤖 Automatically extract Salesforce fields and create records
- 💬 Interactively provide missing MEDDIC fields through chat
- 📊 Get real-time feedback on record creation

## Prerequisites

1. A Slack workspace where you have permission to install apps
2. Python 3.12+ installed
3. All dependencies installed (see main README.md)
4. Salesforce and Anthropic API credentials configured (see main README.md)

## Step 1: Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From scratch"**
3. Enter app name: `Mrs. Salesforce` (or your preferred name)
4. Select your workspace
5. Click **"Create App"**

## Step 2: Configure Bot Token Scopes

1. In your app settings, go to **"OAuth & Permissions"** in the left sidebar
2. Scroll down to **"Scopes"** → **"Bot Token Scopes"**
3. Add the following scopes:
   - `app_mentions:read` - Read mentions
   - `channels:history` - Read channel messages
   - `channels:read` - View basic channel information
   - `chat:write` - Send messages
   - `files:read` - Read files shared in channels
   - `im:history` - Read direct messages
   - `im:read` - View basic direct message information
   - `im:write` - Send direct messages

## Step 3: Install App to Workspace

1. Still in **"OAuth & Permissions"**, scroll to the top
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)
   - This is your `SLACK_BOT_TOKEN`

## Step 4: Get Signing Secret

1. In your app settings, go to **"Basic Information"**
2. Scroll down to **"App Credentials"**
3. Copy the **"Signing Secret"**
   - This is your `SLACK_SIGNING_SECRET`

## Step 5: Configure Event Subscriptions

1. In your app settings, go to **"Event Subscriptions"**
2. Toggle **"Enable Events"** to **On**
3. Set **"Request URL"** to your server endpoint:
   - For local development: `http://your-ngrok-url.ngrok.io/slack/events`
   - For production: `https://your-domain.com/slack/events`
4. Under **"Subscribe to bot events"**, add:
   - `message.channels` - Listen to messages in channels
   - `message.im` - Listen to direct messages
   - `file_shared` - Listen to file uploads
5. Click **"Save Changes"**

## Step 6: Create Slash Command (Optional)

1. In your app settings, go to **"Slash Commands"**
2. Click **"Create New Command"**
3. Configure:
   - **Command**: `/mrs-salesforce`
   - **Request URL**: Same as Event Subscriptions URL + `/slack/events`
   - **Short Description**: `Process a sales call transcript`
   - **Usage Hint**: `[transcript text]`
4. Click **"Save"**

## Step 7: Set Up Local Development (ngrok)

For local development, you'll need to expose your local server:

1. Install ngrok: [https://ngrok.com/download](https://ngrok.com/download)
2. Start your Flask app (see Step 8)
3. In another terminal, run:
   ```bash
   ngrok http 3000
   ```
4. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
5. Use this URL in Step 5 for the Request URL

## Step 8: Configure Environment Variables

Add the following to your `.env` file:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_PORT=3000
```

**Important**: Never commit these tokens to version control!

## Step 9: Run the Slack App

Start the Slack integration server:

```bash
# Using uv
uv run python slack_app.py

# Or using pip
python slack_app.py
```

The server will start on port 3000 (or the port specified in `SLACK_PORT`).

## Step 10: Test the Integration

1. Invite the bot to a channel:
   - In Slack, type `/invite @Mrs. Salesforce` in any channel
2. Send a test message:
   - Type `help` to see available commands
3. Process a transcript:
   - Paste a call transcript in the channel
   - Or use the slash command: `/mrs-salesforce [transcript text]`

## Usage

### Processing Transcripts

Simply paste a call transcript in a channel where the bot is present, or send it as a direct message. The bot will:

1. Extract contact, account, and opportunity information
2. Create records in Salesforce
3. Check MEDDIC completeness
4. If fields are missing, ask you to provide them through chat

### Providing Missing Fields

When the bot asks for missing MEDDIC fields, you can:

- Provide all fields at once:
  ```
  Metrics: Increase revenue by 20%
  Economic Buyer: John Smith, CFO
  Identified Pain: Current system is too slow
  ```

- Provide fields one at a time (the bot will keep asking until all are collected)

- Use natural language - the bot uses AI to extract the relevant information

### Example Conversation

```
You: [pastes transcript]

Mrs. Salesforce: ✅ Salesforce Records Created:
• Account: 001XX000004ABCD
• Contact: 003XX000004EFGH
• Opportunity: 006XX000004IJKL

Extracted Data:
Contact: John Doe (john@example.com)
Account: Acme Corp
Opportunity: Acme Corp - Cloud Migration
Amount: $50,000.00

MEDDIC Completeness: 50%

Hi! I've processed your call transcript, but I need a bit more information to complete the MEDDIC qualification. Please provide the following:

• Metrics Notes: Quantifiable business metrics or KPIs - notes
• Economic Buyers Notes: Person with budget authority - notes
• Decision Criteria Notes: Criteria used for decision making - notes

You: Metrics: They want to reduce costs by 30% and improve efficiency. Economic Buyer: Sarah Johnson, the CFO. Decision Criteria: Price, implementation time, and support quality.

Mrs. Salesforce: ✅ Updated! Still need:

• Decision Process Notes: Steps in the decision process - notes

You: They'll evaluate proposals in Q2, get approval from the board in Q3, and start implementation in Q4.

Mrs. Salesforce: 🎉 Perfect! All MEDDIC fields have been collected and the opportunity has been updated.
```

## Troubleshooting

### Bot not responding

1. Check that the bot is invited to the channel
2. Verify the server is running and accessible
3. Check server logs for errors
4. Verify Event Subscriptions URL is correct and accessible

### "Slack not configured" error

1. Verify `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` are set in `.env`
2. Restart the server after updating `.env`

### File uploads not working

Currently, the bot primarily supports text transcripts pasted directly. File upload support is limited to text files. For best results, paste transcript text directly.

### Events not being received

1. Verify the Request URL in Event Subscriptions is correct
2. Check that ngrok (for local dev) is running
3. Verify the URL is accessible (try visiting it in a browser)
4. Check Slack app logs in the Slack API dashboard

## Production Deployment

For production deployment:

1. Deploy the Flask app to a cloud service (Heroku, AWS, GCP, etc.)
2. Set up a public HTTPS endpoint
3. Update the Request URL in Slack app settings
4. Set environment variables in your hosting platform
5. Consider using a process manager like systemd or supervisor

## Security Notes

- Never commit tokens to version control
- Use environment variables for all secrets
- Keep your Signing Secret secure
- Regularly rotate tokens if compromised
- Use HTTPS in production
- Consider rate limiting for production deployments

## Support

For issues or questions:
- Check the main [README.md](README.md)
- Review [TESTING.md](TESTING.md) for testing instructions
- Check server logs for detailed error messages





