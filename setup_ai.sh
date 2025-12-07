#!/bin/bash
# Setup script for BRIDGE AI features

echo "🤖 Setting up BRIDGE AI Assistant..."
echo ""

# Check if anthropic package is installed
if ! python3.11 -c "import anthropic" 2>/dev/null; then
    echo "📦 Installing anthropic package..."
    sudo pip3 install anthropic
    echo "✅ Package installed!"
else
    echo "✅ Anthropic package already installed"
fi

# Set API key from local file
if [ -f ".anthropic_key" ]; then
    export ANTHROPIC_API_KEY=$(cat .anthropic_key)
    echo "✅ API key loaded from .anthropic_key"
else
    echo "⚠️  .anthropic_key file not found"
    echo "Please create .anthropic_key file with your API key:"
    echo "  echo 'your-api-key-here' > .anthropic_key"
    echo ""
    echo "Get your API key from: https://console.anthropic.com/"
    exit 1
fi

# Add to bashrc for persistence
if ! grep -q "ANTHROPIC_API_KEY" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# BRIDGE AI Assistant API Key" >> ~/.bashrc
    echo "export ANTHROPIC_API_KEY=\$(cat ~/bridge/.anthropic_key 2>/dev/null || echo '')" >> ~/.bashrc
    echo "✅ Added API key to ~/.bashrc for persistence"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To launch BRIDGE with AI:"
echo "  cd /path/to/bridge"
echo "  python3.11 bridge_app.py"
echo ""
echo "Or run:"
echo "  ./run_bridge.sh"
