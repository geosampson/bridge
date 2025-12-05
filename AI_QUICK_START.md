# AI Features - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Package (1 minute)

```bash
cd /path/to/bridge
sudo pip3 install anthropic
```

### Step 2: Get API Key (2 minutes)

1. Visit: https://console.anthropic.com/
2. Sign up (free $5 credit included!)
3. Go to **API Keys** → **Create Key**
4. Copy your key (starts with `sk-ant-...`)

### Step 3: Configure BRIDGE (1 minute)

**Option A: Environment Variable**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Option B: Config File**
Create `~/.bridge/ai_config.json`:
```json
{
  "enabled": true,
  "api_key": "sk-ant-your-key-here",
  "model": "claude-3-5-sonnet-20241022"
}
```

### Step 4: Use AI Features (1 minute)

**Note**: The AI features are ready to use but not yet integrated into the main BRIDGE UI. You can:

1. **Import and use programmatically**:
```python
from ai_client import BridgeAI
from ai_anomaly_detector import AnomalyDetector

# Initialize
ai = BridgeAI()
detector = AnomalyDetector(ai)

# Detect anomalies
anomalies = detector.detect_all_anomalies(products)

# Get AI insights
insights = ai.generate_insights(products)

# Chat with AI
response = ai.chat("Show me products with price issues")
```

2. **Wait for UI integration** (coming in next update):
   - AI tab will be added to BRIDGE
   - Visual interface for all features
   - One-click anomaly detection
   - Interactive chat assistant

---

## 📋 What's Included

### ✅ Ready to Use (Programmatic)

- `ai_client.py` - Claude API integration
- `ai_config.py` - Configuration management
- `ai_anomaly_detector.py` - Anomaly detection
- `ai_suggestions_panel.py` - Suggestions UI (needs integration)
- `ai_analytics_dashboard.py` - Analytics UI (needs integration)
- `ai_chat_assistant.py` - Chat UI (needs integration)

### 🔨 Next Steps (UI Integration)

The AI modules are complete and functional, but need to be integrated into the main BRIDGE application (`bridge_app.py`). This will add:

1. **New "AI" tab** in main interface
2. **Automatic anomaly detection** on data fetch
3. **Visual suggestions panel** with approve/reject
4. **Analytics dashboard** with insights
5. **Chat assistant** interface

---

## 💡 Example Usage

### Detect Price Issues

```python
from ai_anomaly_detector import AnomalyDetector

detector = AnomalyDetector()
anomalies = detector.detect_all_anomalies(your_products)

for anomaly in anomalies:
    print(f"SKU: {anomaly['sku']}")
    print(f"Issue: {anomaly['description']}")
    print(f"Fix: {anomaly['suggested_fix']}")
    print(f"Auto-fixable: {anomaly['auto_fixable']}")
    print("---")
```

### Get AI Insights

```python
from ai_client import BridgeAI

ai = BridgeAI()
insights = ai.generate_insights(your_products)

print(f"Top products: {insights.get('top_products')}")
print(f"Recommendations: {insights.get('recommendations')}")
```

### Chat with AI

```python
from ai_client import BridgeAI

ai = BridgeAI()

response = ai.chat("Which products should I discount?")
print(response)

response = ai.chat("Show me products with zero prices")
print(response)
```

---

## 🎯 Costs

**Free Tier**: $5 credit (enough for ~1,500 analyses)

**After free tier**:
- Anomaly detection: ~$0.006 per analysis
- Analytics: ~$0.009 per generation
- Chat: ~$0.0015 per message

**Typical monthly cost**: $1-5 for normal usage

---

## 🔜 Coming Soon

**UI Integration Update** will add:
- Visual AI tab in BRIDGE
- One-click anomaly detection
- Interactive suggestions panel
- Analytics dashboard
- Chat assistant interface

**Stay tuned!** 🚀

---

## 📞 Questions?

See full documentation: `AI_INTEGRATION_README.md`
