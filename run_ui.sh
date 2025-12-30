#!/bin/bash
# Script to run the Streamlit UI

echo "🚀 Starting Mrs. Salesforce UI..."

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "Using uv to run Streamlit..."
    uv run streamlit run app.py
else
    echo "Using standard streamlit command..."
    streamlit run app.py
fi
