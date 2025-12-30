#!/bin/bash

# Combined Agent Platform - Installation and Run Script
# This script installs everything needed and runs the app

# Don't exit on error for checks, but do exit for critical failures
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

print_step "Combined Agent Platform - Installation & Setup"

# Step 1: Check for Homebrew
print_info "Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found. Installing Homebrew..."
    print_info "This will require your password and may take a few minutes."
    set -e  # Exit on error for installation
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    set +e  # Don't exit on error for checks
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -f "/usr/local/bin/brew" ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    
    print_success "Homebrew installed successfully!"
else
    print_success "Homebrew is already installed"
fi

# Step 2: Check for Python 3.12+
print_info "Checking for Python 3.12 or higher..."
PYTHON_VERSION=$(python3 --version 2>/dev/null | cut -d' ' -f2 || echo "0.0.0")
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
    print_warning "Python 3.12+ not found. Installing Python 3.12..."
    set -e  # Exit on error for installation
    brew install python@3.12
    set +e  # Don't exit on error for checks
    print_success "Python 3.12 installed successfully!"
else
    print_success "Python $PYTHON_VERSION is installed (meets requirement of 3.12+)"
fi

# Step 3: Install uv
print_info "Checking for uv (package manager)..."
if ! command -v uv &> /dev/null; then
    print_warning "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi
    
    # Also try to add to PATH if it's in a common location
    export PATH="$HOME/.local/bin:$PATH"
    export PATH="$HOME/.cargo/bin:$PATH"
    
    print_success "uv installed successfully!"
else
    print_success "uv is already installed"
fi

# Ensure uv is in PATH
if ! command -v uv &> /dev/null; then
    # Try to find uv in common locations
    if [ -f "$HOME/.local/bin/uv" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    elif [ -f "$HOME/.cargo/bin/uv" ]; then
        export PATH="$HOME/.cargo/bin:$PATH"
    fi
fi

# Verify uv is accessible
if ! command -v uv &> /dev/null; then
    print_error "uv is installed but not in PATH. Please restart your terminal and run this script again."
    print_info "Or manually add uv to your PATH:"
    print_info "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    exit 1
fi

# Step 4: Install project dependencies
print_step "Installing project dependencies..."
print_info "This may take a few minutes the first time..."
set -e  # Exit on error for installation
if uv sync; then
    set +e  # Don't exit on error for checks
    print_success "Dependencies installed successfully!"
else
    set +e  # Don't exit on error for checks
    print_error "Failed to install dependencies. Please check the error messages above."
    exit 1
fi

# Step 5: Check for .env file
print_step "Checking environment configuration..."
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating template..."
    
    cat > .env << 'EOF'
# Required for transcript processing
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Required for Salesforce integration (OAuth for Okta SSO)
# Leave these empty if you only want to test transcript processing
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_REFRESH_TOKEN=your_refresh_token
SALESFORCE_INSTANCE_URL=https://yourinstance.salesforce.com

# Optional: Slack integration
# SLACK_BOT_TOKEN=xoxb-your-token
# SLACK_SIGNING_SECRET=your-secret
# SLACK_PORT=3000
EOF
    
    print_success ".env file created!"
    print_warning "⚠️  IMPORTANT: You need to edit the .env file with your API keys before the app will work fully."
    print_info "At minimum, you need to set ANTHROPIC_API_KEY"
    print_info "Get your Anthropic API key from: https://console.anthropic.com/"
    echo ""
    read -p "Would you like to open the .env file now to edit it? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Try to open with default editor
        if command -v code &> /dev/null; then
            code .env
        elif command -v nano &> /dev/null; then
            nano .env
        elif command -v vim &> /dev/null; then
            vim .env
        else
            print_info "Please edit the .env file manually with your preferred text editor."
        fi
    fi
else
    print_success ".env file already exists"
    
    # Check if ANTHROPIC_API_KEY is set (but not the placeholder)
    if grep -q "ANTHROPIC_API_KEY=your_anthropic_api_key_here" .env 2>/dev/null || ! grep -q "^ANTHROPIC_API_KEY=" .env 2>/dev/null; then
        print_warning "ANTHROPIC_API_KEY appears to be missing or not configured in .env"
        print_info "The app may not work without an Anthropic API key"
        print_info "Get your API key from: https://console.anthropic.com/"
    else
        # Check if it's actually set to something meaningful
        API_KEY=$(grep "^ANTHROPIC_API_KEY=" .env 2>/dev/null | cut -d'=' -f2- | tr -d ' ' | tr -d '"' | tr -d "'")
        if [ -z "$API_KEY" ] || [ "$API_KEY" = "your_anthropic_api_key_here" ]; then
            print_warning "ANTHROPIC_API_KEY appears to be missing or not configured in .env"
            print_info "The app may not work without an Anthropic API key"
        fi
    fi
fi

# Step 6: Run the application
print_step "Starting the application..."
print_success "Installation complete! Starting the app..."
print_info "The app will open in your browser at: http://localhost:8501"
print_info "Press Ctrl+C to stop the app when you're done."
echo ""

# Run the app
uv run streamlit run app.py
