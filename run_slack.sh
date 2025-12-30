#!/bin/bash
# Convenience script to run the Slack integration server

echo "🚀 Starting Mrs. Salesforce Slack Integration..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Make sure to set SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET"
    echo ""
fi

# Run the Slack app
if command -v uv &> /dev/null; then
    echo "Using uv..."
    uv run python slack_app.py
else
    echo "Using python..."
    python slack_app.py
fi





