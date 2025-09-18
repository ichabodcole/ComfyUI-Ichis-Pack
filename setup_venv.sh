#!/bin/bash

# Create virtual environment
uv venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Install the package in development mode
uv pip install -e .

echo "Virtual environment setup complete. To activate, run: source .venv/bin/activate" 