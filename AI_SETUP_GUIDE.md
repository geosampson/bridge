# BRIDGE AI Assistant - Setup Guide

## 🚀 Quick Setup

### Step 1: Switch to AI Branch
```bash
cd /path/to/bridge
git checkout ai-integration
git pull origin ai-integration
```

### Step 2: Install Dependencies
```bash
sudo pip3 install anthropic
```

### Step 3: Configure API Key

**The API key has been provided to you separately for security reasons.**

Create the `.anthropic_key` file:
```bash
echo "YOUR-API-KEY-HERE" > .anthropic_key
```

Or run the setup script:
```bash
./setup_ai.sh
```

### Step 4: Launch BRIDGE

Use the launch script:
```bash
./run_bridge.sh
```

Or launch manually:
```bash
python3.11 bridge_app.py
```

### Step 5: Use AI Assistant

1. Click on **"🤖 AI Assistant"** tab
2. Start chatting!

---

## 🎯 Example Questions

- "Show me products with price issues"
- "Which products have zero prices?"
- "What are my best-selling products?"
- "Find HEROCK products that need syncing"
- "Analyze my pricing strategy"
- "Which products are underpriced?"

---

## 🔧 Troubleshooting

### AI Assistant shows "Not Available"

Make sure the `.anthropic_key` file exists:
```bash
ls -la .anthropic_key
```

If not, create it with your API key.

### Module not found error

Install the package:
```bash
sudo pip3 install anthropic
```

---

## 💰 Cost

**Free tier**: $5 credit (~1,500 messages)  
**After**: ~$0.0015 per message  
**Monthly**: $1-5 for normal usage

---

## 📚 More Documentation

- `AI_INTEGRATION_README.md` - Full documentation
- `AI_QUICK_START.md` - Quick start guide
- `AI_INTEGRATION_SUMMARY.md` - Feature summary

---

**Enjoy your AI-powered BRIDGE!** 🤖🌉✨
