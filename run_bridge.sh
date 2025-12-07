#!/bin/bash
# Launch BRIDGE with AI features enabled

# Load API key from local file
if [ -f ".anthropic_key" ]; then
    export ANTHROPIC_API_KEY=$(cat .anthropic_key)
fi

# Launch BRIDGE
python3.11 bridge_app.py
