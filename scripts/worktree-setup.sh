#!/bin/bash
# Git Worktree Setup Script for IoT Security Platform
# This script runs automatically when a new Git worktree is created
# It sets up dependencies and environment variables

echo ""
echo "🚀 Setting up new Git worktree..."
echo "================================"
echo ""

# Get the current directory (worktree root)
WORKTREE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$WORKTREE_ROOT/.." && pwd)"

echo "📁 Worktree location: $WORKTREE_ROOT"
echo "📁 Project root: $PROJECT_ROOT"
echo ""

# Check Python installation
echo "🐍 Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✓ Found: $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo "   ✓ Found: $PYTHON_VERSION"
    PYTHON_CMD="python"
else
    echo "   ✗ Python not found! Please install Python 3.8+ first."
    exit 1
fi

# Check if virtual environment exists
VENV_PATH="$WORKTREE_ROOT/venv"
if [ ! -d "$VENV_PATH" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_PATH"
    echo "   ✓ Virtual environment created"
else
    echo ""
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source "$VENV_PATH/bin/activate"
if [ $? -eq 0 ]; then
    echo "   ✓ Virtual environment activated"
else
    echo "   ⚠ Could not activate venv (may need to run manually)"
fi

# Install dependencies
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements.txt"
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo ""
    echo "📥 Installing Python dependencies..."
    echo "   This may take a minute..."
    pip install --upgrade pip --quiet
    pip install -r "$REQUIREMENTS_FILE"
    if [ $? -eq 0 ]; then
        echo "   ✓ Dependencies installed successfully"
    else
        echo "   ✗ Failed to install dependencies"
    fi
else
    echo ""
    echo "⚠ requirements.txt not found at: $REQUIREMENTS_FILE"
fi

# Set up .env file
ENV_EXAMPLE="$PROJECT_ROOT/.env.example"
ENV_FILE="$WORKTREE_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        echo ""
        echo "📝 Creating .env file from .env.example..."
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo "   ✓ .env file created"
        echo "   ⚠ Remember to update .env with your actual values!"
    else
        echo ""
        echo "⚠ .env.example not found. You may need to create .env manually."
    fi
else
    echo ""
    echo "📝 .env file already exists"
fi

# Summary
echo ""
echo "✅ Worktree setup complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with your configuration"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the app: python run.py"
echo ""
