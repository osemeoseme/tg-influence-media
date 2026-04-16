#!/bin/bash

# Setup script for Media Influence Analysis Project

set -e  # Exit on error

echo "=================================="
echo "Setting up Media Influence Project"
echo "=================================="

# Check Python version
echo ""
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
echo ""
if [ -f ".env" ]; then
    echo ".env file already exists. Skipping..."
else
    echo "Creating .env file from template..."
    cp .env.template .env
    echo ".env file created. Please edit it with your Telegram API credentials."
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/results

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Telegram API credentials"
echo "2. Get credentials from: https://my.telegram.org/apps"
echo "3. Run: python main.py all"
echo ""
echo "For detailed instructions, see QUICKSTART.md"
echo ""
