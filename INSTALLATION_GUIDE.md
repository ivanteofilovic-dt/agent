# Installation Guide for Non-Technical Users

This guide will help you install and run the Combined Agent Platform on your Mac, even if you don't have any development tools installed.

## Quick Start (One Command)

Simply double-click the `install_and_run.sh` file, or run this command in Terminal:

```bash
./install_and_run.sh
```

**That's it!** The script will:
1. ✅ Install Homebrew (if needed)
2. ✅ Install Python 3.12+ (if needed)
3. ✅ Install uv package manager (if needed)
4. ✅ Install all project dependencies
5. ✅ Set up environment configuration
6. ✅ Launch the application

## Step-by-Step Instructions

### 1. Open Terminal

- Press `Cmd + Space` to open Spotlight
- Type "Terminal" and press Enter
- Or go to Applications → Utilities → Terminal

### 2. Navigate to the Project Folder

In Terminal, type:
```bash
cd ~/Code/combined-agent
```

(Or wherever you saved the project folder)

### 3. Run the Installation Script

Type:
```bash
./install_and_run.sh
```

### 4. Follow the Prompts

The script will:
- Ask for your password (to install Homebrew) - this is safe
- Install everything automatically
- Create a `.env` file if needed
- Ask if you want to edit the `.env` file

### 5. Configure Your API Keys

**Important:** You need at least one API key for the app to work:

1. **Anthropic API Key (Required)**
   - Go to https://console.anthropic.com/
   - Sign up or log in
   - Navigate to "API Keys"
   - Click "Create Key"
   - Copy the key
   - Open the `.env` file in the project folder
   - Replace `your_anthropic_api_key_here` with your actual key

2. **Salesforce Credentials (Optional)**
   - Only needed if you want to create Salesforce records
   - See `docs/GET_SALESFORCE_CREDENTIALS.md` for instructions

### 6. The App Will Launch

Once everything is installed, the app will automatically:
- Start the web server
- Open your browser to http://localhost:8501
- Show you the application interface

## Troubleshooting

### "Permission denied" error
If you get a permission error, make the script executable:
```bash
chmod +x install_and_run.sh
```

### "Command not found: uv"
If uv is not found after installation:
1. Close and reopen Terminal
2. Run the script again

Or manually add to your PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### The app doesn't start
- Make sure you've added your `ANTHROPIC_API_KEY` to the `.env` file
- Check that the `.env` file is in the project root folder
- Try running the script again

### Need to stop the app
Press `Ctrl + C` in the Terminal window

## What Gets Installed?

The script installs:
- **Homebrew**: Package manager for macOS
- **Python 3.12+**: Programming language required by the app
- **uv**: Fast Python package manager
- **All project dependencies**: Libraries and tools needed by the app

All installations are safe and standard development tools.

## Running the App Again

After the first installation, you can run the app anytime by:

1. Opening Terminal
2. Navigating to the project folder: `cd ~/Code/combined-agent`
3. Running: `./install_and_run.sh`

Or use the simpler run script:
```bash
./run_ui.sh
```

## Need Help?

- Check the main [README.md](README.md) for more details
- See [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md) for environment variable setup
- See [docs/QUICKSTART.md](docs/QUICKSTART.md) for quick start guide
