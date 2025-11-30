# BRIDGE - Installation Guide

## 📋 Prerequisites

### 1. Python
- **Version:** Python 3.8 or higher
- **Download:** https://www.python.org/downloads/
- **Important:** During installation, check "Add Python to PATH"

### 2. SQL Server ODBC Driver
- **Required for:** Capital ERP database connection
- **Download:** https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
- **Version:** ODBC Driver 17 or 18 for SQL Server

---

## 🚀 Quick Installation

### Step 1: Clone or Download Repository

**Option A: Using Git**
```bash
git clone https://github.com/geosampson/bridge.git
cd bridge
```

**Option B: Download ZIP**
1. Go to https://github.com/geosampson/bridge
2. Click "Code" → "Download ZIP"
3. Extract to a folder
4. Open command prompt in that folder

---

### Step 2: Install Python Dependencies

**Open Command Prompt in the bridge folder and run:**

```bash
pip install -r requirements.txt
```

**If you get an error, try:**
```bash
python -m pip install -r requirements.txt
```

**Or install packages individually:**
```bash
pip install customtkinter requests urllib3 pyodbc
```

---

### Step 3: Configure Credentials

**Create a file named `config.json` in the bridge folder:**

```json
{
    "woocommerce": {
        "store_url": "https://your-store.com",
        "consumer_key": "ck_your_consumer_key_here",
        "consumer_secret": "cs_your_consumer_secret_here"
    },
    "capital": {
        "server": "your-server-name-or-ip",
        "database": "your-database-name",
        "username": "your-username",
        "password": "your-password"
    }
}
```

**How to get WooCommerce credentials:**
1. Login to WordPress admin
2. Go to WooCommerce → Settings → Advanced → REST API
3. Click "Add key"
4. Set permissions to "Read/Write"
5. Copy the Consumer Key and Consumer Secret

---

### Step 4: Launch BRIDGE

**Double-click the launcher:**
```
LAUNCH_BRIDGE.bat
```

**Or run manually:**
```bash
python bridge_app.py
```

---

## 🐛 Troubleshooting

### Error: "urllib3 is not defined"

**Solution:**
```bash
pip install urllib3 requests certifi
```

### Error: "customtkinter not found"

**Solution:**
```bash
pip install customtkinter
```

### Error: "pyodbc not found"

**Solution:**
```bash
pip install pyodbc
```

**If pyodbc installation fails:**
1. Make sure you have Visual C++ Build Tools installed
2. Download from: https://visualstudio.microsoft.com/downloads/
3. Or use pre-built wheels: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyodbc

### Error: "ODBC Driver not found"

**Solution:**
1. Install ODBC Driver 17 or 18 for SQL Server
2. Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
3. Restart your computer after installation

### Error: "Permission denied" or "Access denied"

**Solution:**
- Run Command Prompt as Administrator
- Right-click "LAUNCH_BRIDGE.bat" → Run as Administrator

### Application crashes immediately

**Solution:**
1. Check config.json is properly formatted
2. Test your credentials separately
3. Check logs in the Logs tab
4. Make sure all dependencies are installed

---

## 📦 Verify Installation

**Test if all packages are installed:**

```bash
python -c "import customtkinter; import requests; import urllib3; import pyodbc; print('All packages installed successfully!')"
```

**If you see "All packages installed successfully!" - you're good to go!**

---

## 🔄 Updating BRIDGE

**To get the latest version:**

```bash
cd bridge
git pull origin master
```

**Or download the latest ZIP from GitHub and replace files.**

**After updating, run:**
```bash
pip install -r requirements.txt --upgrade
```

---

## 💻 System Requirements

### Minimum
- **OS:** Windows 10/11, macOS 10.14+, Linux
- **RAM:** 4 GB
- **Disk:** 100 MB free space
- **Internet:** Required for API access

### Recommended
- **OS:** Windows 11
- **RAM:** 8 GB or more
- **Disk:** 500 MB free space
- **Internet:** Broadband connection

---

## 🆘 Still Having Issues?

### Check Python Version
```bash
python --version
```
Should be 3.8 or higher.

### Check pip Version
```bash
pip --version
```
Should be 20.0 or higher.

### Reinstall Everything
```bash
pip uninstall customtkinter requests urllib3 pyodbc -y
pip install -r requirements.txt
```

### Get Help
- Check the logs in the "Logs" tab of BRIDGE
- Review error messages carefully
- Make sure config.json is correct
- Test database connection separately

---

## 📝 Configuration File Template

**Save this as `config.json` in the bridge folder:**

```json
{
    "woocommerce": {
        "store_url": "https://roussakis.com.gr",
        "consumer_key": "ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "consumer_secret": "cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    },
    "capital": {
        "server": "192.168.1.100",
        "database": "CAPITAL_DB",
        "username": "sa",
        "password": "YourPassword123"
    }
}
```

**Replace with your actual credentials!**

---

## ✅ Installation Complete!

Once everything is installed:
1. Double-click `LAUNCH_BRIDGE.bat`
2. Wait for the application to start
3. Click "📥 Fetch All Data"
4. Start managing your products!

**Enjoy using BRIDGE!** 🎉

---

**Version:** 2.3  
**Last Updated:** November 30, 2025  
**Repository:** https://github.com/geosampson/bridge
