# BRIDGE AI Integration

## Overview

This branch (`ai-integration`) adds powerful AI features to BRIDGE using Claude API by Anthropic. The AI assistant can detect anomalies, suggest fixes, generate insights, and answer questions about your products.

---

## 🚀 Features

### 1. **AI Anomaly Detection** 🔍
- Automatically detects price errors (zero prices, mismatches)
- Identifies data quality issues (missing descriptions, names)
- Finds stock inconsistencies
- Prioritizes issues by severity (high/medium/low)
- Suggests fixes for each issue

### 2. **AI Suggestions Panel** 💡
- Displays all detected issues in organized cards
- Color-coded by severity (red=high, orange=medium, blue=low)
- Filter by priority or auto-fixable items
- One-click approve/reject workflow
- Batch apply auto-fixable suggestions

### 3. **AI Analytics Dashboard** 📊
- Business insights from product data
- Top performing products
- Pricing optimization suggestions
- Sales trends and patterns
- Actionable recommendations

### 4. **AI Chat Assistant** 💬
- Natural language interface
- Ask questions about your products
- Get instant insights
- Quick action buttons for common tasks
- Context-aware responses

---

## 📦 Installation

### 1. Install Required Package

```bash
sudo pip3 install anthropic
```

Or using the requirements file:

```bash
sudo pip3 install -r requirements_ai.txt
```

### 2. Get Claude API Key

1. Go to [https://console.anthropic.com/](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key (starts with `sk-ant-...`)

### 3. Configure BRIDGE

When you first launch BRIDGE with AI features:

1. Go to **Settings** (or AI tab)
2. Click **"Configure AI"**
3. Paste your Claude API key
4. Click **"Save"**

Alternatively, set environment variable:

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

---

## 🎯 Usage

### AI Anomaly Detection

1. **Fetch your products** (click "Fetch All Data")
2. **Go to AI tab** → **Suggestions panel**
3. **Click "🔄 Analyze"**
4. **Review detected issues**:
   - Red cards = High priority
   - Orange cards = Medium priority
   - Blue cards = Low priority
5. **Take action**:
   - Click **"✓ Apply"** to fix automatically
   - Click **"✗ Dismiss"** to ignore
   - Click **"✓ Apply All Auto-Fixable"** for batch fixes

**Example Issues Detected:**
```
⚠️ SKU: ABC123 • Price Zero
WooCommerce price is €0.00 but Capital has €45.50
💡 Sync price from Capital (€45.50)
[✓ Apply] [✗ Dismiss]

⚠️ SKU: XYZ789 • Missing Description
Product description is missing or very short
💡 Add product description (AI can generate)
[✓ Apply] [✗ Dismiss]
```

### AI Analytics

1. **Go to AI tab** → **Analytics panel**
2. **Click "🔄 Generate Insights"**
3. **Review insights**:
   - Summary metrics
   - Top products
   - Pricing insights
   - Recommendations

**Example Insights:**
```
📈 Summary
Total Products: 1,247
Avg Price: €45.32
Total Sales: 15,432
Avg Discount: 12.5%

🏆 Top Products
1. ABC123 - Product Name - 234 sales
2. DEF456 - Product Name - 189 sales
...

💡 AI Recommendations
• 15 products may be underpriced (potential revenue increase)
• 8 products need restocking (high demand, low stock)
• 23 products could benefit from better descriptions
```

### AI Chat Assistant

1. **Go to AI tab** → **Chat panel**
2. **Type your question** or use quick actions
3. **Get instant answers**

**Example Conversations:**

```
You: Show me all HEROCK products with price differences
AI: Found 23 HEROCK products with price differences. 
    Average difference: €5.32. The largest difference is 
    SKU HCL.420 with €12.50 difference. Would you like 
    me to suggest which ones to sync?

You: Yes, suggest which to sync
AI: I recommend syncing these 15 products where WooCommerce 
    price is significantly lower than Capital:
    1. HCL.420: WOO €39.68, Capital €52.18 (+€12.50)
    2. HCL.530: WOO €24.18, Capital €32.84 (+€8.66)
    ...
    
You: Sync them all to Capital prices
AI: I've prepared updates for 15 products. Please go to 
    the Products tab, check these products, and click 
    "Sync to Capital Prices" to apply the changes.
```

**Quick Actions:**
- **Find issues** - Detect all problems
- **Top products** - Show best sellers
- **Price analysis** - Analyze pricing
- **Suggestions** - Get recommendations

---

## 🔧 Technical Details

### Architecture

```
BRIDGE App
    ├── ai_config.py          # Configuration management
    ├── ai_client.py          # Claude API integration
    ├── ai_anomaly_detector.py # Anomaly detection logic
    ├── ai_suggestions_panel.py # UI for suggestions
    ├── ai_analytics_dashboard.py # Analytics UI
    └── ai_chat_assistant.py  # Chat interface
```

### AI Models

**Default Model**: `claude-3-5-sonnet-20241022`
- Latest Claude 3.5 Sonnet
- Fast and accurate
- Cost-effective (~$0.003 per 1K tokens)

**Alternative Models**:
- `claude-3-opus-20240229` - Most capable (slower, more expensive)
- `claude-3-haiku-20240307` - Fastest (cheaper, less capable)

### Data Privacy

**What data is sent to Claude API:**
- Product SKUs, names, prices (first 100 products for analysis)
- Anonymized product data (no customer information)
- Your questions/prompts

**What is NOT sent:**
- Customer data
- Order details
- Personal information
- API keys or credentials

**Anthropic's data policy:**
- Data is NOT used to train models
- Data is NOT stored long-term
- Encrypted in transit
- See: https://www.anthropic.com/legal/privacy

### Cost Estimation

**Typical usage:**
- Anomaly detection: ~2,000 tokens (~$0.006)
- Analytics generation: ~3,000 tokens (~$0.009)
- Chat message: ~500 tokens (~$0.0015)

**Monthly estimate:**
- 50 analyses + 100 chat messages = ~$0.50-$2.00/month
- Heavy usage: ~$10-20/month

**Free tier:**
- Anthropic offers $5 free credit for new accounts
- Enough for ~1,500 analyses or 3,000 chat messages

---

## 🎨 UI Integration

### New AI Tab

The AI features are integrated into a new **"AI"** tab in BRIDGE:

```
Tabs: Overview | Products | Prices & Discounts | Unmatched | Analytics | Logs | AI ⭐
```

### AI Tab Layout

```
┌─────────────────────────────────────────────────────┐
│  🤖 AI Suggestions  |  📊 Analytics  |  💬 Chat     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [Content based on selected sub-tab]                │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### "AI not configured" message

**Solution**: Add your Claude API key in Settings

### "Error: Authentication failed"

**Causes**:
- Invalid API key
- Expired API key
- No credits remaining

**Solution**:
1. Check API key is correct
2. Verify key is active at console.anthropic.com
3. Check account has credits

### "Error: Rate limit exceeded"

**Cause**: Too many requests in short time

**Solution**: Wait 60 seconds and try again

### Slow responses

**Causes**:
- Large number of products
- Complex analysis
- Network latency

**Solutions**:
- Analyze fewer products at once
- Use faster model (claude-3-haiku)
- Check internet connection

### Package installation fails

**Error**: `Permission denied`

**Solution**:
```bash
sudo pip3 install anthropic
```

---

## 🔮 Future Enhancements

Planned for future versions:

1. **Auto-scheduling** - Run AI analysis automatically (daily/weekly)
2. **Learning mode** - AI learns from your approval/rejection patterns
3. **Bulk operations** - AI-powered batch updates
4. **Custom rules** - Define your own anomaly detection rules
5. **Export reports** - Generate PDF reports with AI insights
6. **Multi-language** - AI responses in Greek
7. **Voice interface** - Talk to AI assistant
8. **Predictive analytics** - Forecast sales and demand

---

## 📊 Example Workflows

### Workflow 1: Daily Product Audit

1. **Morning**: Open BRIDGE, fetch latest data
2. **AI Analysis**: Click "Analyze" in AI Suggestions
3. **Review**: Check high-priority issues (red cards)
4. **Fix**: Click "Apply All Auto-Fixable" for quick wins
5. **Manual review**: Approve/reject medium-priority issues
6. **Done**: Products are clean and optimized!

### Workflow 2: Pricing Optimization

1. **Analytics**: Go to AI Analytics dashboard
2. **Generate**: Click "Generate Insights"
3. **Review**: Check "Pricing Insights" section
4. **Identify**: Find underpriced/overpriced products
5. **Adjust**: Update prices based on recommendations
6. **Monitor**: Track impact over time

### Workflow 3: Product Research

1. **Chat**: Open AI Chat Assistant
2. **Ask**: "Which products have the best profit margins?"
3. **AI responds**: Lists top margin products
4. **Follow-up**: "Should I increase stock for these?"
5. **AI suggests**: Recommendations based on sales data
6. **Action**: Implement suggestions

---

## 🤝 Contributing

To improve AI features:

1. **Report issues**: Create GitHub issue with details
2. **Suggest features**: Describe use case and benefit
3. **Test**: Try different scenarios and report results
4. **Feedback**: Share what works and what doesn't

---

## 📄 License

Same as BRIDGE main project.

---

## 🙏 Acknowledgments

- **Anthropic** for Claude API
- **BRIDGE users** for feedback and testing

---

## 📞 Support

For AI-specific issues:
- Check this README first
- Review Anthropic documentation: https://docs.anthropic.com
- Create GitHub issue with "AI:" prefix
- Include error messages and screenshots

---

**Happy analyzing with AI!** 🚀🤖
