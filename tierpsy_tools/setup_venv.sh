#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

ENV_DIR=".venv"
REQ_FILE="requirements.txt"

# 1. Check if requirements.txt exists
if [ ! -f "$REQ_FILE" ]; then
    echo "Error: $REQ_FILE not found in the current directory."
    exit 1
fi

# 2. Create the virtual environment
echo "Creating virtual environment in '$ENV_DIR'..."
python3 -m venv "$ENV_DIR"

# 3. Activate the environment
echo "Activating virtual environment..."
source "$ENV_DIR"/bin/activate

# 4. Upgrade pip and install requirements
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

echo "Installing packages from $REQ_FILE..."
python3 -m pip install -r "$REQ_FILE"

echo "Setup complete! To activate the environment manually, run: source $ENV_DIR/bin/activate"