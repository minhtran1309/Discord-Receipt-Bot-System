#!/bin/bash
# Interactive Installation Script for Discord Receipt Bot
# This script sets up the bot environment and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}=================================================="
    echo -e "$1"
    echo -e "==================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Function to prompt for input with default value
prompt_input() {
    local prompt="$1"
    local default="$2"
    local secret="$3"
    local value=""

    if [ "$secret" = "true" ]; then
        # Hide input for secrets
        read -sp "$prompt: " value
        echo ""
    else
        if [ -n "$default" ]; then
            read -p "$prompt [$default]: " value
            value="${value:-$default}"
        else
            read -p "$prompt: " value
        fi
    fi

    echo "$value"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Function to detect architecture
detect_arch() {
    local arch=$(uname -m)
    case $arch in
        x86_64)
            echo "x86_64"
            ;;
        arm64|aarch64)
            echo "arm64"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# Function to install Miniconda
install_miniconda() {
    local os=$(detect_os)
    local arch=$(detect_arch)

    print_info "Installing Miniconda..."

    if [ "$os" = "macos" ]; then
        if [ "$arch" = "arm64" ]; then
            MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
        else
            MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
        fi
    elif [ "$os" = "linux" ]; then
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    else
        print_error "Unsupported OS for automatic Miniconda installation"
        return 1
    fi

    # Download Miniconda installer
    print_info "Downloading Miniconda installer..."
    curl -o /tmp/miniconda.sh "$MINICONDA_URL"

    # Install Miniconda
    print_info "Running Miniconda installer..."
    bash /tmp/miniconda.sh -b -p "$HOME/miniconda3"

    # Clean up
    rm /tmp/miniconda.sh

    # Initialize conda
    print_info "Initializing conda..."
    "$HOME/miniconda3/bin/conda" init bash

    # Source the conda setup
    if [ -f "$HOME/.bashrc" ]; then
        source "$HOME/.bashrc"
    elif [ -f "$HOME/.bash_profile" ]; then
        source "$HOME/.bash_profile"
    fi

    print_success "Miniconda installed successfully!"
    print_warning "Please restart your terminal or run: source ~/.bashrc"

    return 0
}

# Start installation
clear
print_header "Discord Receipt Bot - Interactive Installation"

echo "This script will help you set up the Discord Receipt Bot."
echo "You will be prompted for API keys and configuration values."
echo ""
print_warning "Make sure you have the following ready:"
echo "  - Discord Bot Token"
echo "  - Mistral API Key (for OCR)"
echo "  - OpenRouter API Key (for AI extraction)"
echo "  - Google Sheets credentials (credentials.json file)"
echo "  - Google Sheets Spreadsheet ID"
echo ""
read -p "Press Enter to continue..."

# Step 0: Check for Conda (optional)
echo ""
print_header "Step 0: Checking Conda Installation (Optional)"

USE_CONDA=false
if command_exists conda; then
    CONDA_VERSION=$(conda --version 2>/dev/null || echo "unknown")
    print_success "Conda is installed: $CONDA_VERSION"
    read -p "Do you want to use Conda for environment management? (yes/no): " use_conda_choice
    if [ "$use_conda_choice" = "yes" ]; then
        USE_CONDA=true
        print_info "Will use Conda for virtual environment"
    else
        print_info "Will use Python venv instead"
    fi
else
    print_warning "Conda is not installed"
    read -p "Do you want to install Miniconda? (yes/no): " install_conda
    if [ "$install_conda" = "yes" ]; then
        install_miniconda
        if [ $? -eq 0 ]; then
            print_success "Miniconda installation complete"
            print_warning "Please restart this script after reopening your terminal"
            exit 0
        else
            print_warning "Miniconda installation failed, will use Python venv instead"
        fi
    else
        print_info "Skipping Conda installation, will use Python venv"
    fi
fi

# Step 1: Check Python
echo ""
print_header "Step 1: Checking Python Installation"

if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python 3 is installed: $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_VERSION=$(python --version | cut -d' ' -f2)
    if [[ "$PYTHON_VERSION" == 3.* ]]; then
        print_success "Python 3 is installed: $PYTHON_VERSION"
        PYTHON_CMD="python"
    else
        print_error "Python 3 is required but Python $PYTHON_VERSION is installed"
        exit 1
    fi
else
    print_error "Python 3 is not installed"
    echo ""
    print_info "Please install Python 3.11 or higher:"
    if [ "$(detect_os)" = "macos" ]; then
        echo "  brew install python@3.11"
    else
        echo "  sudo apt-get update && sudo apt-get install python3.11"
    fi
    exit 1
fi

# Step 2: Check pip
echo ""
print_header "Step 2: Checking pip Installation"

if command_exists pip3; then
    print_success "pip3 is installed"
    PIP_CMD="pip3"
elif command_exists pip; then
    print_success "pip is installed"
    PIP_CMD="pip"
else
    print_error "pip is not installed"
    echo ""
    print_info "Installing pip..."
    $PYTHON_CMD -m ensurepip --upgrade
    PIP_CMD="pip3"
fi

# Step 3: Create virtual environment
echo ""
print_header "Step 3: Setting up Virtual Environment"

if [ "$USE_CONDA" = true ]; then
    # Use Conda environment
    VENV_NAME=$(prompt_input "Enter conda environment name" "discord_bot" "false")

    # Check if conda environment exists
    if conda env list | grep -q "^${VENV_NAME} "; then
        print_warning "Conda environment '$VENV_NAME' already exists"
        read -p "Do you want to recreate it? (yes/no): " recreate
        if [ "$recreate" = "yes" ]; then
            conda env remove -n "$VENV_NAME" -y
            print_info "Removed existing conda environment"
        else
            print_info "Using existing conda environment"
        fi
    fi

    # Create conda environment if it doesn't exist
    if ! conda env list | grep -q "^${VENV_NAME} "; then
        print_info "Creating conda environment: $VENV_NAME"
        conda create -n "$VENV_NAME" python=3.11 -y
        print_success "Conda environment created"
    fi

    # Activate conda environment
    print_info "Activating conda environment..."
    eval "$(conda shell.bash hook)"
    conda activate "$VENV_NAME"
    print_success "Conda environment activated"

else
    # Use Python venv
    VENV_NAME=$(prompt_input "Enter virtual environment name" "discord_env" "false")

    if [ -d "$VENV_NAME" ]; then
        print_warning "Virtual environment '$VENV_NAME' already exists"
        read -p "Do you want to recreate it? (yes/no): " recreate
        if [ "$recreate" = "yes" ]; then
            rm -rf "$VENV_NAME"
            print_info "Removed existing virtual environment"
        else
            print_info "Using existing virtual environment"
        fi
    fi

    if [ ! -d "$VENV_NAME" ]; then
        print_info "Creating virtual environment: $VENV_NAME"
        $PYTHON_CMD -m venv "$VENV_NAME"
        print_success "Virtual environment created"
    fi

    # Activate virtual environment
    print_info "Activating virtual environment..."
    source "$VENV_NAME/bin/activate"
    print_success "Virtual environment activated"
fi

# Step 4: Install dependencies
echo ""
print_header "Step 4: Installing Dependencies"

if [ -f "requirements.txt" ]; then
    print_info "Installing packages from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Step 5: Configure environment variables
echo ""
print_header "Step 5: Configuring Environment Variables"

print_info "Please provide the following configuration values:"
echo ""

# Discord Configuration
echo -e "${BLUE}--- Discord Configuration ---${NC}"
DISCORD_TOKEN=$(prompt_input "Discord Bot Token" "" "true")
DISCORD_GUILD_ID=$(prompt_input "Discord Guild/Server ID (optional, for faster sync)" "" "false")

# Mistral OCR Configuration
echo ""
echo -e "${BLUE}--- Mistral OCR Configuration ---${NC}"
MISTRAL_API_KEY=$(prompt_input "Mistral API Key" "" "true")
MISTRAL_OCR_MODEL=$(prompt_input "Mistral OCR Model" "mistral-ocr-latest" "false")

# OpenRouter Configuration
echo ""
echo -e "${BLUE}--- OpenRouter Configuration ---${NC}"
OPENROUTER_API_KEY=$(prompt_input "OpenRouter API Key" "" "true")
OPENROUTER_MODEL=$(prompt_input "OpenRouter Model" "openai/gpt-4o-mini" "false")

# Google Sheets Configuration
echo ""
echo -e "${BLUE}--- Google Sheets Configuration ---${NC}"
GOOGLE_CREDENTIALS_PATH=$(prompt_input "Google Credentials JSON file path" "credentials.json" "false")

# Check if credentials file exists
if [ ! -f "$GOOGLE_CREDENTIALS_PATH" ]; then
    print_warning "Credentials file not found: $GOOGLE_CREDENTIALS_PATH"
    print_info "Make sure to place your Google service account credentials JSON file at this location before running the bot"
fi

GOOGLE_SPREADSHEET_ID=$(prompt_input "Google Spreadsheet ID" "" "false")

# Application Settings
echo ""
echo -e "${BLUE}--- Application Settings ---${NC}"
CONFIDENCE_THRESHOLD=$(prompt_input "Confidence threshold (0.0-1.0)" "0.7" "false")
DATA_DIR=$(prompt_input "Data directory" "data" "false")
LOG_LEVEL=$(prompt_input "Log level (DEBUG/INFO/WARNING/ERROR)" "INFO" "false")
BOT_NAME=$(prompt_input "Bot instance name" "Receipt Bot (Local)" "false")

# Step 6: Create .env file
echo ""
print_header "Step 6: Creating .env File"

ENV_FILE=".env"

if [ -f "$ENV_FILE" ]; then
    print_warning ".env file already exists"
    read -p "Do you want to overwrite it? (yes/no): " overwrite
    if [ "$overwrite" != "yes" ]; then
        print_info "Keeping existing .env file"
        ENV_FILE=".env.new"
        print_info "Creating new configuration as .env.new"
    fi
fi

cat > "$ENV_FILE" << EOF
# Discord Configuration
DISCORD_TOKEN=$DISCORD_TOKEN
DISCORD_GUILD_ID=$DISCORD_GUILD_ID

# Mistral OCR API
MISTRAL_API_KEY=$MISTRAL_API_KEY
MISTRAL_OCR_MODEL=$MISTRAL_OCR_MODEL

# OpenRouter API (for AI extraction and item guessing)
OPENROUTER_API_KEY=$OPENROUTER_API_KEY
OPENROUTER_MODEL=$OPENROUTER_MODEL

# Google Sheets
GOOGLE_CREDENTIALS_PATH=$GOOGLE_CREDENTIALS_PATH
GOOGLE_SPREADSHEET_ID=$GOOGLE_SPREADSHEET_ID

# Application Settings
CONFIDENCE_THRESHOLD=$CONFIDENCE_THRESHOLD
DATA_DIR=$DATA_DIR
LOG_LEVEL=$LOG_LEVEL
BOT_NAME=$BOT_NAME
EOF

print_success "Configuration saved to $ENV_FILE"

# Step 7: Create data directory
echo ""
print_header "Step 7: Setting up Data Directory"

if [ ! -d "$DATA_DIR" ]; then
    mkdir -p "$DATA_DIR/receipts" "$DATA_DIR/items"
    print_success "Data directory created: $DATA_DIR"
else
    print_success "Data directory already exists: $DATA_DIR"
fi

# Create corrections.json if it doesn't exist
if [ ! -f "$DATA_DIR/corrections.json" ]; then
    echo "{}" > "$DATA_DIR/corrections.json"
    print_success "Created corrections.json"
fi

# Step 8: Test bot configuration (optional)
echo ""
print_header "Step 8: Testing Configuration (Optional)"

read -p "Do you want to test the bot configuration? (yes/no): " test_config
if [ "$test_config" = "yes" ]; then
    print_info "Running configuration test..."
    $PYTHON_CMD -c "
from bot.config import get_settings
try:
    settings = get_settings()
    print('✓ Configuration loaded successfully')
    print(f'  Bot Name: {settings.bot_name}')
    print(f'  Data Directory: {settings.data_dir}')
    print(f'  Log Level: {settings.log_level}')
except Exception as e:
    print(f'✗ Configuration error: {e}')
    exit(1)
" && print_success "Configuration test passed" || print_error "Configuration test failed"
fi

# Step 9: Installation complete
echo ""
print_header "Installation Complete!"

echo ""
print_success "The Discord Receipt Bot has been configured successfully!"
echo ""
print_info "Next steps:"
echo ""
echo "1. Make sure your Google Sheets credentials are in place:"
echo "   cp /path/to/your/credentials.json $GOOGLE_CREDENTIALS_PATH"
echo ""
echo "2. Invite the bot to your Discord server:"
echo "   https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=2147485696&scope=bot%20applications.commands"
echo ""
if [ "$USE_CONDA" = true ]; then
    echo "3. Start the bot:"
    echo "   conda activate $VENV_NAME"
    echo "   python -m bot.main"
else
    echo "3. Start the bot:"
    echo "   source $VENV_NAME/bin/activate"
    echo "   python -m bot.main"
fi
echo ""
echo "4. Test the bot in Discord:"
echo "   /receipt process [attach image]"
echo "   /clerk status"
echo ""
print_info "For more information, see README.md and docs/DEPLOYMENT.md"
echo ""

# Optional: Create start script
echo ""
read -p "Do you want to create a start script (start_bot.sh)? (yes/no): " create_start_script
if [ "$create_start_script" = "yes" ]; then
    if [ "$USE_CONDA" = true ]; then
        cat > "start_bot.sh" << EOF
#!/bin/bash
# Start Discord Receipt Bot

# Activate conda environment
eval "\$(conda shell.bash hook)"
conda activate $VENV_NAME

# Run the bot
python -m bot.main
EOF
    else
        cat > "start_bot.sh" << EOF
#!/bin/bash
# Start Discord Receipt Bot

# Activate virtual environment
source $VENV_NAME/bin/activate

# Run the bot
python -m bot.main
EOF
    fi
    chmod +x start_bot.sh
    print_success "Created start_bot.sh - run './start_bot.sh' to start the bot"
fi

echo ""
print_success "Installation script complete!"
echo ""
