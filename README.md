# 🌉 BRIDGE - WooCommerce & Capital ERP Product Manager

## Overview

BRIDGE is a comprehensive desktop application designed to manage e-shop products by synchronizing data between WooCommerce and SoftOne Capital ERP. It eliminates the need for manual data entry and provides powerful tools for price management, product matching, and analytics.

## ✨ Features

### 📊 Dashboard Overview
- Real-time statistics showing product counts from both systems
- Price mismatch indicators
- Quick action buttons for common tasks
- Recent activity log

### 📦 Product Management
- View all matched products in a sortable table
- Filter products by:
  - SKU/Code
  - Product name
  - Category
- Double-click any product to edit its details
- See WooCommerce data alongside Capital ERP data

### 💰 Prices & Discounts
- View price differences between WooCommerce and Capital
- Filter to show only mismatched prices
- Batch update multiple products to Capital prices
- Edit individual product prices and discounts
- Calculate discount percentages automatically

### 🔗 Unmatched Products
- View WooCommerce products without Capital matches
- View Capital products not in WooCommerce
- Manual matching interface

### 📈 Analytics
- Top 20 best-selling products
- Product-specific analytics including:
  - Total sales count
  - Pricing history
  - Stock status
  - Category information
  - Creation/modification dates

### 📋 Activity Logs
- Track all system activities
- View data fetch progress
- Monitor update operations

## 🚀 Key Benefits

1. **Shared Data Store**: Data is fetched once and shared across all panels - no repeated API calls
2. **Local Updates**: After updating WooCommerce, local cache is updated immediately without re-fetching
3. **Group Editing**: Filter products and update multiple items at once
4. **Price Sync**: Easily sync WooCommerce prices to match Capital ERP
5. **Discount Calculator**: Automatically calculate sale prices based on discount percentages

## 📋 Requirements

- Python 3.8 or higher
- Windows 10/11 (tested)
- Internet connection

### Python Packages
- customtkinter
- requests
- urllib3

## 🛠️ Installation

### Option 1: Using the Launcher (Windows)
1. Extract the BRIDGE folder to your desired location
2. Double-click `LAUNCH_BRIDGE.bat`
3. The launcher will automatically install missing dependencies

### Option 2: Manual Installation
```bash
# Navigate to the BRIDGE folder
cd bridge

# Install dependencies
pip install -r requirements.txt

# Run the application
python bridge_app.py
```

## 📖 How to Use

### First Launch
1. Click the **"📥 Fetch All Data"** button in the top-right corner
2. Wait for data to load from both WooCommerce and Capital ERP
3. The status bar at the bottom shows loading progress

### Managing Products
1. Go to the **"📦 Products"** tab
2. Use the filters to find specific products
3. Double-click a product to edit its details
4. Changes are saved to WooCommerce and reflected immediately

### Syncing Prices
1. Go to the **"💰 Prices & Discounts"** tab
2. The table shows products with price differences
3. Select products to update
4. Click **"📥 Update Selected to Capital Price"**
5. Confirm the batch update

### Quick Price Sync
1. On the **"📊 Overview"** tab
2. Click **"🔄 Sync Prices from Capital"**
3. All mismatched prices will be updated

### Viewing Analytics
1. Go to the **"📈 Analytics"** tab
2. Enter a SKU to view detailed analytics
3. View top-selling products list

## 🔧 Configuration

API credentials are stored in the script. To update them:

### WooCommerce Configuration
```python
WOOCOMMERCE_CONFIG = {
    "store_url": "https://roussakis.com.gr",
    "consumer_key": "your_consumer_key",
    "consumer_secret": "your_consumer_secret"
}
```

### Capital ERP Configuration
```python
CAPITAL_CONFIG = {
    "base_url": "https://401003161911.oncloud.gr/s1services",
    "username": "WEBESHOP",
    "password": "your_password",
    "company": 1,
    "fiscalyear": 2025,
    "branch": 1
}
```

## 📊 Data Mapping

### Price Matching
| WooCommerce | Capital ERP | Description |
|-------------|-------------|-------------|
| regular_price | RTLPRICE | Retail price (includes VAT) |
| sale_price | - | Calculated discount price |
| sku | CODE | Product code for matching |

### Discount Calculation
The discount percentage is calculated as:
```
discount_percent = (1 - sale_price / regular_price) * 100
```

## ⚠️ Important Notes

1. **Data Flow**: Capital ERP is READ-ONLY. All updates go to WooCommerce only.
2. **Price Matching**: Products are matched by SKU (WooCommerce) = CODE (Capital)
3. **VAT**: Capital's RTLPRICE already includes VAT - no additional calculation needed
4. **Stock**: The TRMODE field in Capital contains stock status
5. **No Full Update**: There's no "update all" button by design - some products should remain unchanged

## 🔒 Safety Features

- **No accidental updates**: All batch operations require confirmation
- **Local database**: Price history and update logs are stored locally
- **Visual indicators**: Clear ✅/❌ icons show price match status

## 🐛 Troubleshooting

### "Connection Error" on data fetch
- Check internet connection
- Verify API credentials
- Ensure WooCommerce REST API is enabled

### Products not matching
- Check that WooCommerce SKU exactly matches Capital CODE
- SKUs are compared case-insensitively with trimmed whitespace

### Slow performance
- The app is optimized to fetch data once
- After initial fetch, all operations use cached data
- Re-fetch only when needed

## 📝 Database

The application creates a local SQLite database (`bridge_data.db`) to store:
- Price history for tracking changes over time
- Update logs for audit purposes

## 🔄 Future Enhancements

- Price history graphs
- Automated scheduled sync
- Email notifications for price mismatches
- Export to Excel functionality
- Product image management

---

**Developed for ROUSSAKIS SUPPLIES IKE**

For support or feature requests, please contact your system administrator.
