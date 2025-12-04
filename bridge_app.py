#!/usr/bin/env python3
"""
BRIDGE - WooCommerce & Capital ERP Product Management System
============================================================
A comprehensive tool for managing e-shop products by syncing data between
WooCommerce and SoftOne Capital ERP.

Features:
- Product matching between WooCommerce and Capital ERP
- Price and discount management
- Product data editing (description, etc.)
- Filtering by code, description, category
- Analytics and sales statistics
- Batch updates for product groups

Author: Roussakis Supplies IKE
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import pyodbc
import threading
from datetime import datetime, timedelta
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3
from collections import defaultdict

# Disable SSL warnings for Capital ERP
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CONFIGURATION
# ============================================================================

# WooCommerce API Configuration
WOOCOMMERCE_CONFIG = {
    "store_url": "https://roussakis.com.gr",
    "consumer_key": "ck_bb11ea8930c80ab895887236e037ddcfbee003e1",
    "consumer_secret": "cs_c7cc521fbe93def7c731a920632c0c23c50d0bd7"
}

# Capital ERP Configuration
CAPITAL_CONFIG = {
    "base_url": "https://401003161911.oncloud.gr/s1services",
    "username": "WEBESHOP",
    "password": "1975",
    "company": 1,
    "fiscalyear": 2025,
    "branch": 1
}

# Application Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ============================================================================
# DATA STORE - Shared data between all panels
# ============================================================================

class DataStore:
    """
    Central data store that holds all fetched data.
    This prevents repeated API calls and shares data between panels.
    """
    
    def __init__(self):
        self.woo_products = []           # All WooCommerce products
        self.capital_products = []        # All Capital ERP products
        self.woo_orders = []              # All WooCommerce orders
        self.woo_categories = []          # WooCommerce categories
        self.matched_products = []        # Products matched between systems
        self.unmatched_woo = []           # WooCommerce products without Capital match
        self.unmatched_capital = []       # Capital products without WooCommerce match
        
        self.capital_session_id = None    # Capital ERP session
        self.last_fetch_time = None       # When data was last fetched
        
        self.is_loading = False           # Loading state flag
        self.load_progress = 0            # Loading progress (0-100)
        self.load_status = ""             # Current loading status message
        
        # Callbacks for UI updates
        self.on_data_changed = []
        self.on_loading_changed = []
        
    def add_data_listener(self, callback):
        """Add a callback to be notified when data changes"""
        self.on_data_changed.append(callback)
        
    def add_loading_listener(self, callback):
        """Add a callback to be notified when loading state changes"""
        self.on_loading_changed.append(callback)
        
    def notify_data_changed(self):
        """Notify all listeners that data has changed"""
        for callback in self.on_data_changed:
            try:
                callback()
            except Exception as e:
                print(f"Error in data listener: {e}")
                
    def notify_loading_changed(self):
        """Notify all listeners that loading state changed"""
        for callback in self.on_loading_changed:
            try:
                callback()
            except Exception as e:
                print(f"Error in loading listener: {e}")
                
    def set_loading(self, is_loading, progress=0, status=""):
        """Update loading state"""
        self.is_loading = is_loading
        self.load_progress = progress
        self.load_status = status
        self.notify_loading_changed()
        
    def get_product_by_sku(self, sku):
        """Get matched product data by SKU"""
        for product in self.matched_products:
            if product.get('sku', '').strip().upper() == sku.strip().upper():
                return product
        return None
        
    def update_woo_product_locally(self, product_id, updates):
        """Update a WooCommerce product in local cache after API update"""
        for i, product in enumerate(self.woo_products):
            if product['id'] == product_id:
                self.woo_products[i].update(updates)
                break
        # Also update in matched products
        for i, product in enumerate(self.matched_products):
            if product.get('woo_id') == product_id:
                for key, value in updates.items():
                    if key == 'regular_price':
                        self.matched_products[i]['woo_regular_price'] = value
                    elif key == 'sale_price':
                        self.matched_products[i]['woo_sale_price'] = value
                    elif key == 'description':
                        self.matched_products[i]['woo_description'] = value
                    elif key == 'short_description':
                        self.matched_products[i]['woo_short_description'] = value
                break
        self.notify_data_changed()
    
    def update_woo_product_from_api(self, product_id, product_data):
        """Update a WooCommerce product from fresh API data"""
        # Update in woo_products list
        for i, product in enumerate(self.woo_products):
            if product['id'] == product_id:
                self.woo_products[i] = product_data
                break
        
        # Update in matched_products list
        for i, product in enumerate(self.matched_products):
            if product.get('woo_id') == product_id:
                # Update all WooCommerce fields from fresh data
                self.matched_products[i]['woo_regular_price'] = float(product_data.get('regular_price', 0) or 0)
                self.matched_products[i]['woo_sale_price'] = float(product_data.get('sale_price', 0) or 0)
                self.matched_products[i]['woo_description'] = product_data.get('description', '')
                self.matched_products[i]['woo_short_description'] = product_data.get('short_description', '')
                self.matched_products[i]['name'] = product_data.get('name', '')
                
                # Recalculate discount percentage
                regular_price = self.matched_products[i]['woo_regular_price']
                sale_price = self.matched_products[i]['woo_sale_price']
                if regular_price > 0 and sale_price > 0:
                    discount_percent = round((1 - sale_price / regular_price) * 100, 2)
                    self.matched_products[i]['woo_discount_percent'] = discount_percent
                else:
                    self.matched_products[i]['woo_discount_percent'] = 0
                break
        
        self.notify_data_changed()


# Global data store instance
data_store = DataStore()


# ============================================================================
# API CLIENTS
# ============================================================================

class WooCommerceClient:
    """WooCommerce REST API client"""
    
    def __init__(self, config):
        self.store_url = config["store_url"]
        self.auth = HTTPBasicAuth(config["consumer_key"], config["consumer_secret"])
        
    def get_products(self, per_page=100, page=1, **kwargs):
        """Get products from WooCommerce"""
        url = f"{self.store_url}/wp-json/wc/v3/products"
        params = {"per_page": per_page, "page": page, **kwargs}
        response = requests.get(url, auth=self.auth, params=params, timeout=60)
        response.raise_for_status()
        return response.json(), response.headers
        
    def get_all_products(self, progress_callback=None):
        """Get all products with pagination"""
        all_products = []
        page = 1
        per_page = 100
        
        while True:
            products, headers = self.get_products(per_page=per_page, page=page)
            if not products:
                break
            all_products.extend(products)
            
            total_pages = int(headers.get('X-WP-TotalPages', 1))
            if progress_callback:
                progress = min(100, int((page / total_pages) * 100))
                progress_callback(progress, f"Fetching WooCommerce products... Page {page}/{total_pages}")
                
            if page >= total_pages:
                break
            page += 1
            
        return all_products
        
    def get_orders(self, per_page=100, page=1, **kwargs):
        """Get orders from WooCommerce"""
        url = f"{self.store_url}/wp-json/wc/v3/orders"
        params = {"per_page": per_page, "page": page, **kwargs}
        response = requests.get(url, auth=self.auth, params=params, timeout=60)
        response.raise_for_status()
        return response.json(), response.headers
        
    def get_all_orders(self, status=None, after=None, progress_callback=None):
        """Get all orders with pagination"""
        all_orders = []
        page = 1
        per_page = 100
        
        params = {}
        if status:
            params['status'] = status
        if after:
            params['after'] = after
            
        while True:
            orders, headers = self.get_orders(per_page=per_page, page=page, **params)
            if not orders:
                break
            all_orders.extend(orders)
            
            total_pages = int(headers.get('X-WP-TotalPages', 1))
            if progress_callback:
                progress = min(100, int((page / total_pages) * 100))
                progress_callback(progress, f"Fetching orders... Page {page}/{total_pages}")
                
            if page >= total_pages:
                break
            page += 1
            
        return all_orders
        
    def get_categories(self):
        """Get all product categories"""
        all_categories = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.store_url}/wp-json/wc/v3/products/categories"
            params = {"per_page": per_page, "page": page}
            response = requests.get(url, auth=self.auth, params=params, timeout=30)
            response.raise_for_status()
            categories = response.json()
            
            if not categories:
                break
            all_categories.extend(categories)
            
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            if page >= total_pages:
                break
            page += 1
            
        return all_categories
        
    def get_product_variations(self, product_id):
        """Get all variations for a variable product"""
        all_variations = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.store_url}/wp-json/wc/v3/products/{product_id}/variations"
            params = {"per_page": per_page, "page": page}
            try:
                response = requests.get(url, auth=self.auth, params=params, timeout=30)
                response.raise_for_status()
                variations = response.json()
                
                if not variations:
                    break
                all_variations.extend(variations)
                
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                if page >= total_pages:
                    break
                page += 1
            except:
                # Product doesn't have variations or error occurred
                break
                
        return all_variations
        
    def update_product(self, product_id, data):
        """Update a product on WooCommerce"""
        url = f"{self.store_url}/wp-json/wc/v3/products/{product_id}"
        response = requests.put(url, auth=self.auth, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
        
    def batch_update_products(self, updates):
        """Batch update multiple products (handles both regular products and variations)"""
        print(f"[DEBUG] Updating {len(updates)} products...")
        
        results = {'update': [], 'errors': []}
        
        for update in updates:
            try:
                product_id = update.get('id')
                parent_id = update.get('parent_id')
                
                # Remove parent_id from update data as it's not a valid field
                update_data = {k: v for k, v in update.items() if k not in ['id', 'parent_id']}
                
                # Determine the correct endpoint
                if parent_id:
                    # This is a variation - use variations endpoint
                    url = f"{self.store_url}/wp-json/wc/v3/products/{parent_id}/variations/{product_id}"
                    print(f"[DEBUG] Updating variation {product_id} of parent {parent_id}")
                else:
                    # This is a regular product
                    url = f"{self.store_url}/wp-json/wc/v3/products/{product_id}"
                    print(f"[DEBUG] Updating product {product_id}")
                
                print(f"[DEBUG] Update data: {update_data}")
                
                response = requests.put(url, auth=self.auth, json=update_data, timeout=30)
                response.raise_for_status()
                result = response.json()
                
                results['update'].append(result)
                print(f"[SUCCESS] Updated product/variation {product_id}")
                
            except requests.exceptions.HTTPError as e:
                error_msg = f"Product {product_id} failed: {e.response.text if hasattr(e, 'response') else str(e)}"
                print(f"[ERROR] {error_msg}")
                results['errors'].append({'id': product_id, 'error': error_msg})
            except Exception as e:
                error_msg = f"Product {product_id} failed: {str(e)}"
                print(f"[ERROR] {error_msg}")
                results['errors'].append({'id': product_id, 'error': error_msg})
        
        success_count = len(results['update'])
        error_count = len(results['errors'])
        print(f"[DEBUG] Update complete: {success_count} succeeded, {error_count} failed")
        
        return results


class CapitalClient:
    """SoftOne Capital ERP API client"""
    
    def __init__(self, config):
        self.base_url = config["base_url"]
        self.config = config
        self.session = requests.Session()
        self.session.verify = False
        self.session_id = None
        
    def login(self):
        """Login to Capital ERP and get session ID"""
        login_data = {
            "service": "login",
            "company": self.config["company"],
            "fiscalyear": self.config["fiscalyear"],
            "branch": self.config["branch"],
            "username": self.config["username"],
            "password": self.config["password"]
        }
        
        response = self.session.post(self.base_url, json=login_data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            self.session_id = result.get("sessionid")
            return self.session_id
        else:
            raise Exception(f"Capital login failed: {result.get('message', 'Unknown error')}")
            
    def get_products(self, fields=None, filters=None):
        """Get products from Capital ERP"""
        if not self.session_id:
            self.login()
            
        if fields is None:
            # Default fields for product matching
            fields = "CODE;DESCR;RTLPRICE;WHSPRICE;TRMODE;DISCOUNT;MAXDISCOUNT;BALANCEQTY"
            
        request_data = {
            "service": "getdata",
            "sessionid": self.session_id,
            "action": "read",
            "tablename": "STOCKITEMS",
            "fields": fields
        }
        
        if filters:
            request_data["filters"] = filters
            
        response = self.session.post(self.base_url, json=request_data, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            # Data can be in different formats depending on Capital version
            data = result.get("data", [])
            if not data:
                data = result.get("STOCKITEMS", [])
            if not data:
                data = result.get("rows", [])
            return data
        else:
            raise Exception(f"Failed to get Capital products: {result.get('message', 'Unknown error')}")


# ============================================================================
# PRODUCT MATCHER
# ============================================================================

class ProductMatcher:
    """Matches products between WooCommerce and Capital ERP"""
    
    @staticmethod
    def match_products(woo_products, capital_products):
        """
        Match products between WooCommerce and Capital by SKU/CODE
        Returns: matched, unmatched_woo, unmatched_capital
        """
        matched = []
        unmatched_woo = []
        unmatched_capital = list(capital_products)  # Copy to track unmatched
        
        # Create lookup dictionary for Capital products
        # Store both original and normalized (without leading zeros) versions
        capital_lookup = {}
        capital_lookup_normalized = {}
        for cap_product in capital_products:
            code = str(cap_product.get('CODE', '')).strip().upper()
            if code:
                capital_lookup[code] = cap_product
                # Also store normalized version (remove leading zeros)
                code_normalized = code.lstrip('0') or '0'  # Keep at least one zero if all zeros
                capital_lookup_normalized[code_normalized] = cap_product
                
        for woo_product in woo_products:
            # Skip parent products (variable products without SKU or with type='variable')
            # Only match variations and regular products
            product_type = woo_product.get('type', '')
            is_variation = woo_product.get('is_variation', False)
            
            # Skip if it's a parent variable product (not a variation)
            if product_type == 'variable' and not is_variation:
                continue
            
            sku = str(woo_product.get('sku', '')).strip().upper()
            
            # Skip products without SKU
            if not sku:
                unmatched_woo.append(woo_product)
                continue
            
            # Try exact match first
            cap_product = None
            if sku in capital_lookup:
                cap_product = capital_lookup[sku]
            # If no exact match, try normalized match (ignore leading zeros)
            else:
                sku_normalized = sku.lstrip('0') or '0'
                if sku_normalized in capital_lookup_normalized:
                    cap_product = capital_lookup_normalized[sku_normalized]
            
            if cap_product:
                
                # Calculate discount percentage
                regular_price = float(woo_product.get('regular_price') or 0)
                sale_price = float(woo_product.get('sale_price') or 0)
                discount_percent = 0
                if regular_price > 0 and sale_price > 0:
                    discount_percent = round((1 - sale_price / regular_price) * 100, 2)
                    
                matched_product = {
                    'sku': sku,
                    'woo_id': woo_product['id'],
                    'parent_id': woo_product.get('parent_id'),  # For variations
                    'woo_name': woo_product.get('name', ''),
                    'woo_regular_price': regular_price,
                    'woo_sale_price': sale_price,
                    'woo_discount_percent': discount_percent,
                    'woo_stock_quantity': woo_product.get('stock_quantity'),
                    'woo_stock_status': woo_product.get('stock_status'),
                    'woo_total_sales': woo_product.get('total_sales', 0),
                    'woo_description': woo_product.get('description', ''),
                    'woo_short_description': woo_product.get('short_description', ''),
                    'woo_categories': [cat.get('name', '') for cat in woo_product.get('categories', [])],
                    'woo_permalink': woo_product.get('permalink', ''),
                    'woo_date_created': woo_product.get('date_created', ''),
                    'woo_date_modified': woo_product.get('date_modified', ''),
                    
                    'capital_code': cap_product.get('CODE', ''),
                    'capital_descr': cap_product.get('DESCR', ''),
                    'capital_rtlprice': float(cap_product.get('RTLPRICE') or 0),
                    'capital_whsprice': float(cap_product.get('WHSPRICE') or 0),
                    'capital_trmode': cap_product.get('TRMODE', 0),
                    'capital_discount': float(cap_product.get('DISCOUNT') or 0),
                    'capital_maxdiscount': float(cap_product.get('MAXDISCOUNT') or 0),
                    'capital_stock': float(cap_product.get('BALANCEQTY') or 0),
                    
                    'price_match': abs(regular_price - float(cap_product.get('RTLPRICE') or 0)) < 0.01,
                }
                
                matched.append(matched_product)
                
                # Remove from unmatched capital
                unmatched_capital = [p for p in unmatched_capital 
                                     if str(p.get('CODE', '')).strip().upper() != sku]
            else:
                unmatched_woo.append(woo_product)
                
        return matched, unmatched_woo, unmatched_capital


# ============================================================================
# DATABASE FOR CACHING AND ANALYTICS
# ============================================================================

class LocalDatabase:
    """SQLite database for caching and analytics"""
    
    def __init__(self, db_path="bridge_data.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Product sales history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                product_name TEXT,
                order_id INTEGER,
                order_date TEXT,
                quantity INTEGER,
                price REAL,
                total REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Price history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                regular_price REAL,
                sale_price REAL,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Update logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS update_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT,
                field_updated TEXT,
                old_value TEXT,
                new_value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def record_price_history(self, sku, regular_price, sale_price):
        """Record price change"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO price_history (sku, regular_price, sale_price)
            VALUES (?, ?, ?)
        ''', (sku, regular_price, sale_price))
        conn.commit()
        conn.close()
        
    def record_update(self, sku, field, old_value, new_value):
        """Record an update"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO update_logs (sku, field_updated, old_value, new_value)
            VALUES (?, ?, ?, ?)
        ''', (sku, field, str(old_value), str(new_value)))
        conn.commit()
        conn.close()
        
    def get_price_history(self, sku, days=90):
        """Get price history for a product"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute('''
            SELECT regular_price, sale_price, recorded_at
            FROM price_history
            WHERE sku = ? AND recorded_at >= ?
            ORDER BY recorded_at
        ''', (sku, cutoff))
        
        results = cursor.fetchall()
        conn.close()
        return results


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class BridgeApp(ctk.CTk):
    """Main Bridge Application Window"""
    
    def __init__(self):
        super().__init__()
        
        self.title("BRIDGE - WooCommerce & Capital ERP Product Manager")
        self.geometry("1600x900")
        self.minsize(1200, 700)
        
        # Initialize clients
        self.woo_client = WooCommerceClient(WOOCOMMERCE_CONFIG)
        self.capital_client = CapitalClient(CAPITAL_CONFIG)
        self.db = LocalDatabase()
        
        # Setup UI
        self.setup_ui()
        
        # Register for data updates
        data_store.add_data_listener(self.on_data_updated)
        data_store.add_loading_listener(self.on_loading_updated)
        
    def setup_ui(self):
        """Setup the main UI"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Top bar with status and controls
        self.create_top_bar()
        
        # Main content area with tabs
        self.create_main_content()
        
        # Status bar at bottom
        self.create_status_bar()
        
    def create_top_bar(self):
        """Create top bar with controls"""
        top_frame = ctk.CTkFrame(self, height=60)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        top_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            top_frame, 
            text="🌉 BRIDGE", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=10)
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            top_frame, 
            text="WooCommerce & Capital ERP Product Manager",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Fetch data button
        self.fetch_btn = ctk.CTkButton(
            top_frame,
            text="📥 Fetch All Data",
            command=self.start_data_fetch,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=150
        )
        self.fetch_btn.grid(row=0, column=2, padx=10, pady=10)
        
        # Checkbox for including variations (add to top frame)
        self.fetch_variations_var = ctk.BooleanVar(value=False)  # Default to False for speed
        variations_checkbox = ctk.CTkCheckBox(
            top_frame,
            text="Include variations (slower)",
            variable=self.fetch_variations_var,
            font=ctk.CTkFont(size=11)
        )
        variations_checkbox.grid(row=0, column=3, padx=10, pady=10)
        
        # Tooltip for variations checkbox
        ctk.CTkLabel(
            top_frame,
            text="⚠️ Variations add ~5-10 min (parallel mode)",
            text_color="orange",
            font=ctk.CTkFont(size=9)
        ).grid(row=1, column=3, padx=10, pady=0)
        
        self.last_fetch_label = ctk.CTkLabel(
            top_frame,
            text="Not fetched yet",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.last_fetch_label.grid(row=0, column=3, padx=20, pady=10)
        
    def create_main_content(self):
        """Create main content area with tabview"""
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Create tabs
        self.tab_overview = self.tabview.add("📊 Overview")
        self.tab_products = self.tabview.add("📦 Products")
        self.tab_prices = self.tabview.add("💰 Prices & Discounts")
        self.tab_unmatched = self.tabview.add("🔗 Unmatched")
        self.tab_analytics = self.tabview.add("📈 Analytics")
        self.tab_logs = self.tabview.add("📋 Logs")
        
        # Initialize tab content
        self.setup_overview_tab()
        self.setup_products_tab()
        self.setup_prices_tab()
        self.setup_unmatched_tab()
        self.setup_analytics_tab()
        self.setup_logs_tab()
        
    def create_status_bar(self):
        """Create status bar at bottom"""
        status_frame = ctk.CTkFrame(self, height=40)
        status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        status_frame.grid_columnconfigure(1, weight=1)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(status_frame, width=200)
        self.progress_bar.grid(row=0, column=0, padx=10, pady=10)
        self.progress_bar.set(0)
        
        # Status message
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Product counts
        self.counts_label = ctk.CTkLabel(
            status_frame,
            text="WOO: 0 | CAPITAL: 0 | MATCHED: 0",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.counts_label.grid(row=0, column=2, padx=20, pady=10)
        
    # ========================================================================
    # OVERVIEW TAB
    # ========================================================================
    
    def setup_overview_tab(self):
        """Setup overview tab with dashboard"""
        self.tab_overview.grid_columnconfigure(0, weight=1)
        self.tab_overview.grid_columnconfigure(1, weight=1)
        self.tab_overview.grid_rowconfigure(1, weight=1)
        
        # Stats cards row
        stats_frame = ctk.CTkFrame(self.tab_overview)
        stats_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        # WooCommerce card
        self.woo_card = self.create_stat_card(stats_frame, "WooCommerce Products", "0", "🛒")
        self.woo_card.grid(row=0, column=0, padx=10, pady=10)
        
        # Capital card
        self.capital_card = self.create_stat_card(stats_frame, "Capital Products", "0", "🏢")
        self.capital_card.grid(row=0, column=1, padx=10, pady=10)
        
        # Matched card
        self.matched_card = self.create_stat_card(stats_frame, "Matched Products", "0", "✅")
        self.matched_card.grid(row=0, column=2, padx=10, pady=10)
        
        # Price mismatches card
        self.mismatch_card = self.create_stat_card(stats_frame, "Price Mismatches", "0", "⚠️")
        self.mismatch_card.grid(row=0, column=3, padx=10, pady=10)
        
        # Recent activity
        activity_frame = ctk.CTkFrame(self.tab_overview)
        activity_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        activity_label = ctk.CTkLabel(
            activity_frame,
            text="📋 Recent Updates",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        activity_label.pack(pady=10)
        
        self.activity_text = ctk.CTkTextbox(activity_frame, width=400, height=300)
        self.activity_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Quick actions
        actions_frame = ctk.CTkFrame(self.tab_overview)
        actions_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        actions_label = ctk.CTkLabel(
            actions_frame,
            text="⚡ Quick Actions",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        actions_label.pack(pady=10)
        
        ctk.CTkButton(
            actions_frame,
            text="🔄 Sync Prices from Capital",
            command=self.sync_prices_from_capital,
            width=250
        ).pack(pady=5)
        
        ctk.CTkButton(
            actions_frame,
            text="📊 View Price Mismatches",
            command=lambda: self.tabview.set("💰 Prices & Discounts"),
            width=250
        ).pack(pady=5)
        
        ctk.CTkButton(
            actions_frame,
            text="🔗 Match Unmatched Products",
            command=lambda: self.tabview.set("🔗 Unmatched"),
            width=250
        ).pack(pady=5)
        
    def create_stat_card(self, parent, title, value, icon):
        """Create a statistics card"""
        card = ctk.CTkFrame(parent, width=180, height=100)
        card.grid_propagate(False)
        
        icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=24))
        icon_label.pack(pady=(10, 0))
        
        value_label = ctk.CTkLabel(
            card, 
            text=value, 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        value_label.pack()
        
        title_label = ctk.CTkLabel(
            card, 
            text=title, 
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        title_label.pack()
        
        # Store reference to value label for updates
        card.value_label = value_label
        
        return card
        
    # ========================================================================
    # PRODUCTS TAB
    # ========================================================================
    
    def setup_products_tab(self):
        """Setup products management tab"""
        self.tab_products.grid_columnconfigure(0, weight=1)
        self.tab_products.grid_rowconfigure(1, weight=1)
        
        # Filters frame
        filter_frame = ctk.CTkFrame(self.tab_products)
        filter_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Search by code/SKU
        ctk.CTkLabel(filter_frame, text="SKU/Code:").grid(row=0, column=0, padx=5, pady=5)
        self.product_sku_filter = ctk.CTkEntry(filter_frame, width=150)
        self.product_sku_filter.grid(row=0, column=1, padx=5, pady=5)
        
        # Search by name
        ctk.CTkLabel(filter_frame, text="Name:").grid(row=0, column=2, padx=5, pady=5)
        self.product_name_filter = ctk.CTkEntry(filter_frame, width=200)
        self.product_name_filter.grid(row=0, column=3, padx=5, pady=5)
        
        # Brand filter (parent categories only)
        ctk.CTkLabel(filter_frame, text="Brand:").grid(row=0, column=4, padx=5, pady=5)
        self.product_category_filter = ctk.CTkComboBox(
            filter_frame, 
            width=180,
            values=["All Brands"]
        )
        self.product_category_filter.grid(row=0, column=5, padx=5, pady=5)
        self.product_category_filter.set("All Brands")
        
          # Filter button
        ctk.CTkButton(
            filter_frame,
            text="🔍 Filter",
            command=self.filter_products,
            width=100
        ).grid(row=0, column=6, padx=10, pady=5)
        
        # Clear button
        ctk.CTkButton(
            filter_frame,
            text="❌ Clear",
            command=self.clear_product_filters,
            width=100
        ).grid(row=0, column=7, padx=10, pady=5)
        
        # Group update frame
        group_update_frame = ctk.CTkFrame(self.tab_products)
        group_update_frame.grid(row=0, column=0, sticky="e", padx=10, pady=(50, 0))
        
        ctk.CTkLabel(
            group_update_frame,
            text="Group Update (Checked Products):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, padx=5, pady=5, columnspan=4)
        
        # Price update
        ctk.CTkLabel(group_update_frame, text="Set Price (€):").grid(row=1, column=0, padx=5, pady=5)
        self.group_price_entry = ctk.CTkEntry(group_update_frame, width=100, placeholder_text="e.g., 29.99")
        self.group_price_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkButton(
            group_update_frame,
            text="💰 Update Prices",
            command=self.update_group_prices,
            width=120,
            fg_color="green"
        ).grid(row=1, column=2, padx=5, pady=5)
        
        # Discount update
        ctk.CTkLabel(group_update_frame, text="Set Discount (%):").grid(row=2, column=0, padx=5, pady=5)
        self.group_discount_entry = ctk.CTkEntry(group_update_frame, width=100, placeholder_text="e.g., 15")
        self.group_discount_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ctk.CTkButton(
            group_update_frame,
            text="🏷️ Apply Discount",
            command=self.update_group_discount,
            width=120,
            fg_color="orange"
        ).grid(row=2, column=2, padx=5, pady=5)
        
        # Sync to Capital button
        ctk.CTkButton(
            group_update_frame,
            text="🔄 Sync to Capital Prices",
            command=self.sync_filtered_to_capital,
            width=120,
            fg_color="blue"
        ).grid(row=3, column=0, columnspan=3, padx=5, pady=5)
        
        # Refresh buttons frame
        refresh_frame = ctk.CTkFrame(group_update_frame)
        refresh_frame.grid(row=4, column=0, columnspan=3, padx=5, pady=5)
        
        ctk.CTkButton(
            refresh_frame,
            text="🔄 Refresh Capital Prices",
            command=self.refresh_capital_prices_for_checked,
            width=180,
            fg_color="green"
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            refresh_frame,
            text="🔄 Refresh WooCommerce Prices",
            command=self.refresh_woo_prices_for_checked,
            width=180,
            fg_color="orange"
        ).pack(side="left", padx=2)
        
        # Products treeview
        tree_frame = ctk.CTkFrame(self.tab_products)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        # Create treeview with scrollbars
        columns = (
            "☑", "SKU", "Name", "WOO Price", "Capital Price", 
            "Sale Price", "Discount %", "WOO Stock", "Capital Stock", "Total Sales", "Match"
        )
        
        self.products_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
        # Track checkbox states
        self.product_checkboxes = {}
        
        # Configure columns
        self.products_tree.heading("☑", text="☑", command=self.toggle_all_products)
        self.products_tree.heading("SKU", text="SKU")
        self.products_tree.heading("Name", text="Product Name")
        self.products_tree.heading("WOO Price", text="WOO Price €")
        self.products_tree.heading("Capital Price", text="Capital Price €")
        self.products_tree.heading("Sale Price", text="Sale Price €")
        self.products_tree.heading("Discount %", text="Discount %")
        self.products_tree.heading("WOO Stock", text="WOO Stock")
        self.products_tree.heading("Capital Stock", text="Capital Stock")
        self.products_tree.heading("Total Sales", text="Sales")
        self.products_tree.heading("Match", text="Match")
        
        self.products_tree.column("☑", width=30, anchor="center")
        self.products_tree.column("SKU", width=120)
        self.products_tree.column("Name", width=300)
        self.products_tree.column("WOO Price", width=100)
        self.products_tree.column("Capital Price", width=100)
        self.products_tree.column("Sale Price", width=100)
        self.products_tree.column("Discount %", width=80)
        self.products_tree.column("WOO Stock", width=80)
        self.products_tree.column("Capital Stock", width=90)
        self.products_tree.column("Total Sales", width=60)
        self.products_tree.column("Match", width=60)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.products_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.products_tree.xview)
        self.products_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.products_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
                # Click to toggle checkbox, double-click to edit
        self.products_tree.bind("<Button-1>", self.on_product_click)
        self.products_tree.bind("<Double-Button-1>", self.on_product_double_click)        
        # Selection count label
        self.selection_label = ctk.CTkLabel(
            self.tab_products,
            text="Select products to edit",
            font=ctk.CTkFont(size=12)
        )
        self.selection_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
    def refresh_products_table(self):
        """Refresh products table while preserving current filters"""
        # Simply call filter_products which will re-apply current filters
        self.filter_products()
    
    def filter_products(self):
        """Filter products based on criteria"""
        sku_filter = self.product_sku_filter.get().strip().upper()
        name_filter = self.product_name_filter.get().strip().lower()
        category_filter = self.product_category_filter.get()
        
        # Clear current items
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Clear checkbox state to prevent accumulation
        self.product_checkboxes.clear()
            
        # Filter and display
        for product in data_store.matched_products:
            sku = product.get('sku', '')
            name = product.get('woo_name', '')
            categories = product.get('woo_categories', [])
            
            # Apply filters
            if sku_filter and sku_filter not in sku.upper():
                continue
            if name_filter and name_filter not in name.lower():
                continue
            if category_filter != "All Brands":
                # Match brand against beginning of product name
                if not name.startswith(category_filter):
                    continue
                    
            # Add to treeview
            match_status = "✅" if product.get('price_match') else "❌"
            
            item_id = self.products_tree.insert("", "end", values=(
                "☐",  # Unchecked by default
                sku,
                name[:50] + "..." if len(name) > 50 else name,
                f"{product.get('woo_regular_price', 0):.2f}",
                f"{product.get('capital_rtlprice', 0):.2f}",
                f"{product.get('woo_sale_price', 0):.2f}" if product.get('woo_sale_price') else "-",
                f"{product.get('woo_discount_percent', 0):.1f}%" if product.get('woo_discount_percent') is not None else "-",
                product.get('woo_stock_quantity', '-'),
                f"{product.get('capital_stock', 0):.0f}" if product.get('capital_stock') is not None else "-",
                product.get('woo_total_sales', 0),
                match_status
            ))
            # Track checkbox state
            self.product_checkboxes[item_id] = False
            
    def clear_product_filters(self):
        """Clear all product filters"""
        self.product_sku_filter.delete(0, "end")
        self.product_name_filter.delete(0, "end")
        self.product_category_filter.set("All Brands")
        self.filter_products()
        
    def get_filtered_products(self):
        """Get list of currently filtered products"""
        filtered_products = []
        for item in self.products_tree.get_children():
            values = self.products_tree.item(item, "values")
            sku = values[0]
            product = data_store.get_product_by_sku(sku)
            if product:
                filtered_products.append(product)
        return filtered_products
        
    def update_group_prices(self):
        """Update prices for checked products"""
        price_str = self.group_price_entry.get().strip()
        if not price_str:
            messagebox.showwarning("Warning", "Please enter a price")
            return
            
        try:
            price = float(price_str)
        except ValueError:
            messagebox.showerror("Error", "Invalid price format")
            return
        
        # Get checked products
        checked_items = [item_id for item_id, checked in self.product_checkboxes.items() if checked]
        
        if not checked_items:
            messagebox.showwarning("Warning", "Please check products to update")
            return
            
        if not messagebox.askyesno("Confirm", f"Update {len(checked_items)} checked products to €{price:.2f}?"):
            return
            
        updates = []
        for item in checked_items:
            values = self.products_tree.item(item, "values")
            sku = values[1]  # SKU is now in column 1 (after checkbox)
            product = data_store.get_product_by_sku(sku)
            if product:
                updates.append({
                    "id": product['woo_id'],
                    "parent_id": product.get('parent_id'),
                    "regular_price": f"{price:.2f}"
                })
                self.log(f"Updating {sku}: regular_price={price:.2f}")
            
        if updates:
            self.log(f"Updating {len(updates)} products to €{price:.2f}")
            threading.Thread(target=self.batch_update_prices, args=(updates,)).start()
            self.group_price_entry.delete(0, "end")
        else:
            messagebox.showwarning("Warning", "No valid products found to update")
        
    def update_group_discount(self):
        """Apply discount percentage to checked products"""
        discount_str = self.group_discount_entry.get().strip()
        if not discount_str:
            messagebox.showwarning("Warning", "Please enter a discount percentage")
            return
            
        try:
            discount_percent = float(discount_str)
            if discount_percent < 0 or discount_percent > 100:
                raise ValueError("Discount must be between 0 and 100")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid discount: {str(e)}")
            return
        
        # Get checked products
        checked_items = [item_id for item_id, checked in self.product_checkboxes.items() if checked]
        
        if not checked_items:
            messagebox.showwarning("Warning", "Please check products to update")
            return
            
        if not messagebox.askyesno("Confirm", f"Apply {discount_percent}% discount to {len(checked_items)} checked products?"):
            return
            
        updates = []
        for item in checked_items:
            values = self.products_tree.item(item, "values")
            sku = values[1]  # SKU is now in column 1 (after checkbox)
            product = data_store.get_product_by_sku(sku)
            if product:
                regular_price = product.get('woo_regular_price', 0)
                if regular_price > 0:
                    sale_price = regular_price * (1 - discount_percent / 100)
                    updates.append({
                        "id": product['woo_id'],
                        "parent_id": product.get('parent_id'),
                        "sale_price": f"{sale_price:.2f}"
                    })
                    self.log(f"Applying {discount_percent}% discount to {sku}: sale_price={sale_price:.2f}")
                
        if updates:
            self.log(f"Applying {discount_percent}% discount to {len(updates)} products")
            threading.Thread(target=self.batch_update_prices, args=(updates,)).start()
            self.group_discount_entry.delete(0, "end")
        else:
            messagebox.showwarning("Warning", "No valid products found to update")
        
    def sync_filtered_to_capital(self):
        """Sync checked products to Capital prices"""
        # Get checked products
        checked_items = [item_id for item_id, checked in self.product_checkboxes.items() if checked]
        
        if not checked_items:
            messagebox.showwarning("Warning", "Please check products to sync")
            return
            
        if not messagebox.askyesno("Confirm", f"Sync {len(checked_items)} checked products to Capital prices?"):
            return
            
        updates = []
        for item in checked_items:
            values = self.products_tree.item(item, "values")
            sku = values[1]  # SKU is now in column 1 (after checkbox)
            product = data_store.get_product_by_sku(sku)
            if product:
                capital_price = product.get('capital_rtlprice')
                if capital_price and capital_price > 0:
                    # Get current discount percentage
                    current_discount = product.get('woo_discount_percent', 0)
                    
                    # Format new regular price
                    new_regular_price = float(capital_price)
                    price_str = f"{new_regular_price:.2f}"
                    
                    # Calculate new sale price to preserve discount percentage
                    if current_discount is not None and float(current_discount) > 0:
                        discount_multiplier = (100 - float(current_discount)) / 100
                        new_sale_price = new_regular_price * discount_multiplier
                        sale_price_str = f"{new_sale_price:.2f}"
                        updates.append({
                            "id": product['woo_id'],
                            "parent_id": product.get('parent_id'),
                            "regular_price": price_str,
                            "sale_price": sale_price_str
                        })
                        self.log(f"Syncing {sku}: regular_price={price_str}, sale_price={sale_price_str} ({current_discount}% discount preserved)")
                    else:
                        # No discount, just update regular price and clear sale price
                        updates.append({
                            "id": product['woo_id'],
                            "parent_id": product.get('parent_id'),
                            "regular_price": price_str,
                            "sale_price": ""
                        })
                        self.log(f"Syncing {sku}: regular_price={price_str} (no discount)")
                
        if updates:
            self.log(f"Syncing {len(updates)} products to Capital prices")
            threading.Thread(target=self.batch_update_prices, args=(updates,)).start()
        else:
            messagebox.showwarning("Warning", "No valid Capital prices found to sync")
        
    def on_product_click(self, event):
        """Handle click on product tree (for checkbox toggle)"""
        region = self.products_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.products_tree.identify_column(event.x)
            item = self.products_tree.identify_row(event.y)
            
            # Check if clicked on checkbox column
            if column == "#1" and item:  # First column is checkbox
                # Toggle checkbox
                current_state = self.product_checkboxes.get(item, False)
                new_state = not current_state
                self.product_checkboxes[item] = new_state
                
                # Update display
                values = list(self.products_tree.item(item, "values"))
                values[0] = "☑" if new_state else "☐"
                self.products_tree.item(item, values=values)
                
                # Update selection count
                checked_count = sum(1 for checked in self.product_checkboxes.values() if checked)
                self.selection_label.configure(text=f"Selected: {checked_count} products")
    
    def toggle_all_products(self):
        """Toggle all checkboxes in Products tab"""
        # Check if any are checked
        any_checked = any(self.product_checkboxes.values())
        new_state = not any_checked
        
        # Update all checkboxes
        for item in self.products_tree.get_children():
            self.product_checkboxes[item] = new_state
            values = list(self.products_tree.item(item, "values"))
            values[0] = "☑" if new_state else "☐"
            self.products_tree.item(item, values=values)
        
        # Update selection count
        checked_count = sum(1 for checked in self.product_checkboxes.values() if checked)
        self.selection_label.configure(text=f"Selected: {checked_count} products")
    
    def on_product_double_click(self, event):
        """Handle double-click on product to edit"""
        region = self.products_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.products_tree.identify_column(event.x)
            item = self.products_tree.identify_row(event.y)
            
            # Don't open editor if clicked on checkbox column
            if column != "#1" and item:
                values = self.products_tree.item(item, "values")
                sku = values[1]  # SKU is now in column 1 (after checkbox)
                self.open_product_editor(sku)
            
    # ========================================================================
    # PRICES TAB
    # ========================================================================
    
    def setup_prices_tab(self):
        """Setup prices and discounts management tab"""
        self.tab_prices.grid_columnconfigure(0, weight=1)
        self.tab_prices.grid_rowconfigure(1, weight=1)
        
        # Controls frame
        controls_frame = ctk.CTkFrame(self.tab_prices)
        controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Show only mismatches checkbox
        self.show_mismatches_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            controls_frame,
            text="Show only price mismatches",
            variable=self.show_mismatches_var,
            command=self.refresh_prices_table
        ).grid(row=0, column=0, padx=10, pady=5)
        
        # Search
        ctk.CTkLabel(controls_frame, text="Search:").grid(row=0, column=1, padx=5, pady=5)
        self.price_search = ctk.CTkEntry(controls_frame, width=200)
        self.price_search.grid(row=0, column=2, padx=5, pady=5)
        self.price_search.bind("<Return>", lambda e: self.refresh_prices_table())
        
        # Search button
        ctk.CTkButton(
            controls_frame,
            text="🔍 Search",
            command=self.refresh_prices_table,
            width=100
        ).grid(row=0, column=3, padx=10, pady=5)
        
        # Group update panel (similar to Products tab)
        group_update_frame = ctk.CTkFrame(self.tab_prices)
        group_update_frame.grid(row=0, column=0, sticky="e", padx=10, pady=(50, 0))
        
        ctk.CTkLabel(
            group_update_frame,
            text="Group Update (Checked Products):",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, padx=5, pady=5, columnspan=3)
        
        # Discount update
        ctk.CTkLabel(group_update_frame, text="Set Discount (%):").grid(row=1, column=0, padx=5, pady=5)
        self.prices_group_discount_entry = ctk.CTkEntry(group_update_frame, width=100, placeholder_text="e.g., 15")
        self.prices_group_discount_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkButton(
            group_update_frame,
            text="🏷️ Apply Discount",
            command=self.apply_discount_to_checked,
            width=120,
            fg_color="orange"
        ).grid(row=1, column=2, padx=5, pady=5)
        
        # Sync to Capital button
        ctk.CTkButton(
            group_update_frame,
            text="🔄 Sync Checked to Capital",
            command=self.sync_checked_to_capital,
            width=250,
            fg_color="blue"
        ).grid(row=2, column=0, columnspan=3, padx=5, pady=5)
        
        # Prices treeview
        tree_frame = ctk.CTkFrame(self.tab_prices)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        columns = (
            "Select", "SKU", "Name", "WOO Regular", "Capital RTLPRICE", 
            "Difference", "WOO Sale", "Discount %"
        )
        
        # Enable extended selection mode for multi-select with shift+click and ctrl+click
        self.prices_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")
        
        self.prices_tree.heading("Select", text="☑", command=self.toggle_all_prices)
        self.prices_tree.heading("SKU", text="SKU")
        self.prices_tree.heading("Name", text="Product Name")
        self.prices_tree.heading("WOO Regular", text="WOO Regular €")
        self.prices_tree.heading("Capital RTLPRICE", text="Capital €")
        self.prices_tree.heading("Difference", text="Diff €")
        self.prices_tree.heading("WOO Sale", text="Sale Price €")
        self.prices_tree.heading("Discount %", text="Discount %")
        
        self.prices_tree.column("Select", width=50, anchor="center")
        self.prices_tree.column("SKU", width=120)
        self.prices_tree.column("Name", width=250)
        self.prices_tree.column("WOO Regular", width=100)
        self.prices_tree.column("Capital RTLPRICE", width=100)
        self.prices_tree.column("Difference", width=80)
        self.prices_tree.column("WOO Sale", width=100)
        self.prices_tree.column("Discount %", width=80)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.prices_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.prices_tree.xview)
        self.prices_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.prices_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Bind events for checkbox and drag selection
        self.prices_tree.bind("<Button-1>", self.on_price_click)
        self.prices_tree.bind("<Double-1>", self.on_price_double_click)
        self.prices_tree.bind("<B1-Motion>", self.on_price_drag)
        
        # Track checkbox states
        self.price_checkboxes = {}  # item_id -> checked state
        
        # Bottom actions
        actions_frame = ctk.CTkFrame(self.tab_prices)
        actions_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        self.price_count_label = ctk.CTkLabel(
            actions_frame,
            text="0 products shown",
            font=ctk.CTkFont(size=12)
        )
        self.price_count_label.grid(row=0, column=0, padx=10, pady=5)
        
        ctk.CTkButton(
            actions_frame,
            text="📥 Update Checked to Capital Price",
            command=self.update_selected_to_capital_price,
            fg_color="green"
        ).grid(row=0, column=1, padx=10, pady=5)
        
        ctk.CTkButton(
            actions_frame,
            text="🔄 Refresh Capital Prices",
            command=self.refresh_capital_prices_for_checked_prices_tab,
            fg_color="green"
        ).grid(row=0, column=2, padx=10, pady=5)
        
        ctk.CTkButton(
            actions_frame,
            text="🔄 Refresh WooCommerce Prices",
            command=self.refresh_woo_prices_for_checked_prices_tab,
            fg_color="orange"
        ).grid(row=0, column=3, padx=10, pady=5)
        
    def refresh_prices_table(self):
        """Refresh the prices table"""
        # Clear current items
        for item in self.prices_tree.get_children():
            self.prices_tree.delete(item)
            
        show_mismatches = self.show_mismatches_var.get()
        search_text = self.price_search.get().strip().lower()
        
        count = 0
        for product in data_store.matched_products:
            # Filter by mismatch
            if show_mismatches and product.get('price_match'):
                continue
                
            # Filter by search
            if search_text:
                if (search_text not in product.get('sku', '').lower() and 
                    search_text not in product.get('woo_name', '').lower()):
                    continue
                    
            woo_price = product.get('woo_regular_price', 0)
            capital_price = product.get('capital_rtlprice', 0)
            difference = woo_price - capital_price
            
            item_id = self.prices_tree.insert("", "end", values=(
                "☐",  # Checkbox unchecked by default
                product.get('sku', ''),
                product.get('woo_name', '')[:40],
                f"{woo_price:.2f}",
                f"{capital_price:.2f}",
                f"{difference:+.2f}",
                f"{product.get('woo_sale_price', 0):.2f}" if product.get('woo_sale_price') else "-",
                f"{product.get('woo_discount_percent', 0):.1f}%" if product.get('woo_discount_percent') is not None else "-"
            ))
            self.price_checkboxes[item_id] = False  # Track unchecked state
            count += 1
            
        self.price_count_label.configure(text=f"{count} products shown")
        
    def toggle_all_prices(self):
        """Toggle all checkboxes in prices table"""
        # Check if any are unchecked
        any_unchecked = any(not checked for checked in self.price_checkboxes.values())
        
        # Set all to checked if any unchecked, otherwise uncheck all
        for item_id in self.price_checkboxes:
            self.price_checkboxes[item_id] = any_unchecked
            values = list(self.prices_tree.item(item_id, "values"))
            values[0] = "☑" if any_unchecked else "☐"
            self.prices_tree.item(item_id, values=values)
            
    def on_price_click(self, event):
        """Handle click on price row to toggle checkbox"""
        region = self.prices_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.prices_tree.identify_column(event.x)
            item = self.prices_tree.identify_row(event.y)
            
            if item and column == "#1":  # First column is checkbox
                # Toggle checkbox
                current_state = self.price_checkboxes.get(item, False)
                self.price_checkboxes[item] = not current_state
                
                values = list(self.prices_tree.item(item, "values"))
                values[0] = "☑" if not current_state else "☐"
                self.prices_tree.item(item, values=values)
                return "break"  # Prevent default selection
                
    def on_price_drag(self, event):
        """Handle drag to select multiple checkboxes"""
        item = self.prices_tree.identify_row(event.y)
        column = self.prices_tree.identify_column(event.x)
        
        if item and column == "#1":  # Dragging over checkbox column
            # Check the checkbox
            if item in self.price_checkboxes:
                self.price_checkboxes[item] = True
                values = list(self.prices_tree.item(item, "values"))
                values[0] = "☑"
                self.prices_tree.item(item, values=values)
        
    def on_price_double_click(self, event):
        """Handle double-click on price row"""
        item = self.prices_tree.identify_row(event.y)
        column = self.prices_tree.identify_column(event.x)
        
        # Don't open editor if clicking on checkbox column
        if item and column != "#1":
            values = self.prices_tree.item(item, "values")
            sku = values[1]  # SKU is now in column 1 (after checkbox)
            self.open_price_editor(sku)
            
    def update_selected_to_capital_price(self):
        """Update checked products to Capital price"""
        # Get all checked items
        checked_items = [item_id for item_id, checked in self.price_checkboxes.items() if checked]
        
        if not checked_items:
            messagebox.showwarning("Warning", "Please check products to update")
            return
            
        if not messagebox.askyesno("Confirm", f"Update {len(checked_items)} products to Capital price?"):
            return
            
        updates = []
        for item in checked_items:
            values = self.prices_tree.item(item, "values")
            sku = values[1]  # SKU is now in column 1 (after checkbox)
            product = data_store.get_product_by_sku(sku)
            if product:
                capital_price = product.get('capital_rtlprice')
                if capital_price and capital_price > 0:
                    # Ensure price is formatted correctly as string with 2 decimals
                    price_str = f"{float(capital_price):.2f}"
                    updates.append({
                        "id": product['woo_id'],
                        "parent_id": product.get('parent_id'),
                        "regular_price": price_str,
                        "sale_price": ""  # Clear sale price when syncing to Capital
                    })
                    self.log(f"Updating {sku}: regular_price={price_str}")
                
        if updates:
            self.log(f"Updating {len(updates)} products to Capital prices")
            threading.Thread(target=self.batch_update_prices, args=(updates,)).start()
        else:
            messagebox.showwarning("Warning", "No valid Capital prices found to update")
            
    def apply_discount_to_checked(self):
        """Apply discount percentage to all checked products in Prices tab"""
        discount_str = self.prices_group_discount_entry.get().strip()
        if not discount_str:
            messagebox.showwarning("Warning", "Please enter a discount percentage")
            return
            
        try:
            discount_percent = float(discount_str)
            if discount_percent < 0 or discount_percent > 100:
                raise ValueError("Discount must be between 0 and 100")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid discount: {str(e)}")
            return
            
        # Get all checked items
        checked_items = [item_id for item_id, checked in self.price_checkboxes.items() if checked]
        
        if not checked_items:
            messagebox.showwarning("Warning", "Please check products to update")
            return
            
        if not messagebox.askyesno("Confirm", f"Apply {discount_percent}% discount to {len(checked_items)} checked products?"):
            return
            
        updates = []
        for item in checked_items:
            values = self.prices_tree.item(item, "values")
            sku = values[1]  # SKU is now in column 1 (after checkbox)
            product = data_store.get_product_by_sku(sku)
            if product:
                regular_price = product.get('woo_regular_price', 0)
                if regular_price > 0:
                    sale_price = regular_price * (1 - discount_percent / 100)
                    updates.append({
                        "id": product['woo_id'],
                        "parent_id": product.get('parent_id'),
                        "sale_price": f"{sale_price:.2f}"
                    })
                    
        if updates:
            threading.Thread(target=self.batch_update_prices, args=(updates,)).start()
            self.prices_group_discount_entry.delete(0, "end")
            
    def sync_checked_to_capital(self):
        """Sync checked products to Capital prices in Prices tab"""
        # Get all checked items
        checked_items = [item_id for item_id, checked in self.price_checkboxes.items() if checked]
        
        if not checked_items:
            messagebox.showwarning("Warning", "Please check products to update")
            return
            
        if not messagebox.askyesno("Confirm", f"Sync {len(checked_items)} checked products to Capital prices?"):
            return
            
        updates = []
        for item in checked_items:
            values = self.prices_tree.item(item, "values")
            sku = values[1]  # SKU is now in column 1 (after checkbox)
            product = data_store.get_product_by_sku(sku)
            if product:
                capital_price = product.get('capital_rtlprice')
                if capital_price and capital_price > 0:
                    # Get current discount percentage
                    current_discount = product.get('woo_discount_percent', 0)
                    
                    # Format new regular price
                    new_regular_price = float(capital_price)
                    price_str = f"{new_regular_price:.2f}"
                    
                    # Calculate new sale price to preserve discount percentage
                    if current_discount is not None and float(current_discount) > 0:
                        discount_multiplier = (100 - float(current_discount)) / 100
                        new_sale_price = new_regular_price * discount_multiplier
                        sale_price_str = f"{new_sale_price:.2f}"
                        updates.append({
                            "id": product['woo_id'],
                            "parent_id": product.get('parent_id'),
                            "regular_price": price_str,
                            "sale_price": sale_price_str
                        })
                        self.log(f"Syncing {sku}: regular_price={price_str}, sale_price={sale_price_str} ({current_discount}% discount preserved)")
                    else:
                        # No discount, just update regular price and clear sale price
                        updates.append({
                            "id": product['woo_id'],
                            "parent_id": product.get('parent_id'),
                            "regular_price": price_str,
                            "sale_price": ""
                        })
                        self.log(f"Syncing {sku}: regular_price={price_str} (no discount)")
                    
        if updates:
            self.log(f"Syncing {len(updates)} products to Capital prices")
            threading.Thread(target=self.batch_update_prices, args=(updates,)).start()
        else:
            messagebox.showwarning("Warning", "No valid Capital prices found to sync")
            
    def refresh_from_woocommerce(self, updates):
        """Refresh specific products from WooCommerce after updates"""
        try:
            for update in updates:
                product_id = update['id']
                parent_id = update.get('parent_id')
                try:
                    # Determine correct endpoint based on whether it's a variation
                    if parent_id:
                        # This is a variation
                        url = f"{WOOCOMMERCE_CONFIG['store_url']}/wp-json/wc/v3/products/{parent_id}/variations/{product_id}"
                    else:
                        # This is a regular product
                        url = f"{WOOCOMMERCE_CONFIG['store_url']}/wp-json/wc/v3/products/{product_id}"
                    
                    # Fetch updated product from WooCommerce
                    response = requests.get(
                        url,
                        auth=HTTPBasicAuth(
                            WOOCOMMERCE_CONFIG['consumer_key'],
                            WOOCOMMERCE_CONFIG['consumer_secret']
                        ),
                        timeout=10
                    )
                    if response.status_code == 200:
                        product_data = response.json()
                        # Update local cache with fresh data
                        data_store.update_woo_product_from_api(product_id, product_data)
                        self.log(f"Refreshed product {product_data.get('sku', product_id)} from WooCommerce")
                except Exception as e:
                    self.log(f"Warning: Could not refresh product {product_id}: {str(e)}")
                    
        except Exception as e:
            self.log(f"Error refreshing products from WooCommerce: {str(e)}")
    
    def batch_update_prices(self, updates):
        """Batch update prices in background thread"""
        try:
            data_store.set_loading(True, 0, "Updating prices...")
            
            # Process in batches of 50
            batch_size = 50
            for i in range(0, len(updates), batch_size):
                batch = updates[i:i+batch_size]
                self.log(f"Sending batch {i//batch_size + 1}: {len(batch)} products")
                if batch:
                    self.log(f"Sample update: ID={batch[0]['id']}, regular_price={batch[0].get('regular_price')}, sale_price={batch[0].get('sale_price')}")
                
                result = self.woo_client.batch_update_products(batch)
                
                # Log any errors from WooCommerce
                if 'update' in result:
                    for product in result['update']:
                        if 'error' in product:
                            self.log(f"ERROR: Product {product.get('id')} failed: {product['error'].get('message', 'Unknown error')}")
                        else:
                            self.log(f"Updated product {product.get('id')}: {product.get('sku', 'N/A')}")
                
                progress = min(100, int((i + len(batch)) / len(updates) * 100))
                data_store.set_loading(True, progress, f"Updated {i + len(batch)}/{len(updates)} products")
                
                # Update local cache
                for update in batch:
                    local_update = {}
                    if 'regular_price' in update:
                        local_update['regular_price'] = float(update['regular_price']) if update['regular_price'] else 0
                    if 'sale_price' in update:
                        # Empty string means clear the sale price
                        local_update['sale_price'] = float(update['sale_price']) if update['sale_price'] else 0
                    data_store.update_woo_product_locally(update['id'], local_update)
                    
            data_store.set_loading(False, 100, "Update complete!")
            
            # Refresh products from WooCommerce to get actual updated values
            self.log("Refreshing products from WooCommerce...")
            self.refresh_from_woocommerce(updates)
            
            # Refresh both Products and Prices tables
            self.after(0, self.refresh_products_table)
            self.after(0, self.refresh_prices_table)
            self.after(100, lambda: messagebox.showinfo("Success", f"Successfully updated {len(updates)} products!"))
            
        except Exception as e:
            data_store.set_loading(False, 0, "Update failed")
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to update prices: {str(e)}"))
            print(f"Batch update error: {e}")
            
    # ========================================================================
    # UNMATCHED TAB
    # ========================================================================
    
    def setup_unmatched_tab(self):
        """Setup unmatched products tab"""
        self.tab_unmatched.grid_columnconfigure(0, weight=1)
        self.tab_unmatched.grid_columnconfigure(1, weight=1)
        self.tab_unmatched.grid_rowconfigure(2, weight=1)
        
        # Title
        ctk.CTkLabel(
            self.tab_unmatched,
            text="Unmatched Products - Match WooCommerce products with Capital ERP",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Search filters row
        filter_frame = ctk.CTkFrame(self.tab_unmatched)
        filter_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        # WooCommerce search
        ctk.CTkLabel(filter_frame, text="Search WooCommerce:").grid(row=0, column=0, padx=5, pady=5)
        self.unmatched_woo_search = ctk.CTkEntry(filter_frame, width=200, placeholder_text="SKU or Name")
        self.unmatched_woo_search.grid(row=0, column=1, padx=5, pady=5)
        self.unmatched_woo_search.bind("<KeyRelease>", lambda e: self.filter_unmatched_products())
        
        # Capital search
        ctk.CTkLabel(filter_frame, text="Search Capital:").grid(row=0, column=2, padx=5, pady=5)
        self.unmatched_capital_search = ctk.CTkEntry(filter_frame, width=200, placeholder_text="CODE or Name")
        self.unmatched_capital_search.grid(row=0, column=3, padx=5, pady=5)
        self.unmatched_capital_search.bind("<KeyRelease>", lambda e: self.filter_unmatched_products())
        
        # Clear filters button
        ctk.CTkButton(
            filter_frame,
            text="❌ Clear",
            command=self.clear_unmatched_filters,
            width=80
        ).grid(row=0, column=4, padx=10, pady=5)
        
        # Left frame - Unmatched WooCommerce products
        left_frame = ctk.CTkFrame(self.tab_unmatched)
        left_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            left_frame,
            text="🛍️ WooCommerce Products (No Capital Match)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, pady=10)
        
        # Use Treeview to show SKU and Name
        woo_tree_frame = ctk.CTkFrame(left_frame)
        woo_tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        woo_tree_frame.grid_columnconfigure(0, weight=1)
        woo_tree_frame.grid_rowconfigure(0, weight=1)
        
        woo_columns = ("SKU", "Name")
        self.unmatched_woo_tree = ttk.Treeview(woo_tree_frame, columns=woo_columns, show="headings", height=15)
        self.unmatched_woo_tree.heading("SKU", text="SKU")
        self.unmatched_woo_tree.heading("Name", text="Product Name")
        self.unmatched_woo_tree.column("SKU", width=120)
        self.unmatched_woo_tree.column("Name", width=300)
        
        woo_vsb = ttk.Scrollbar(woo_tree_frame, orient="vertical", command=self.unmatched_woo_tree.yview)
        self.unmatched_woo_tree.configure(yscrollcommand=woo_vsb.set)
        self.unmatched_woo_tree.grid(row=0, column=0, sticky="nsew")
        woo_vsb.grid(row=0, column=1, sticky="ns")
        
        # Double-click to edit
        self.unmatched_woo_tree.bind("<Double-1>", self.on_unmatched_woo_double_click)
        
        # Right frame - Unmatched Capital products
        right_frame = ctk.CTkFrame(self.tab_unmatched)
        right_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            right_frame,
            text="🏢 Capital Products (Not in WooCommerce)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, pady=10)
        
        # Use Treeview to show CODE and Name
        capital_tree_frame = ctk.CTkFrame(right_frame)
        capital_tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        capital_tree_frame.grid_columnconfigure(0, weight=1)
        capital_tree_frame.grid_rowconfigure(0, weight=1)
        
        capital_columns = ("CODE", "Name")
        self.unmatched_capital_tree = ttk.Treeview(capital_tree_frame, columns=capital_columns, show="headings", height=15)
        self.unmatched_capital_tree.heading("CODE", text="CODE")
        self.unmatched_capital_tree.heading("Name", text="Product Name")
        self.unmatched_capital_tree.column("CODE", width=120)
        self.unmatched_capital_tree.column("Name", width=300)
        
        capital_vsb = ttk.Scrollbar(capital_tree_frame, orient="vertical", command=self.unmatched_capital_tree.yview)
        self.unmatched_capital_tree.configure(yscrollcommand=capital_vsb.set)
        self.unmatched_capital_tree.grid(row=0, column=0, sticky="nsew")
        capital_vsb.grid(row=0, column=1, sticky="ns")
        
        # Double-click to edit
        self.unmatched_capital_tree.bind("<Double-1>", self.on_unmatched_capital_double_click)
        
        # Match button
        ctk.CTkButton(
            self.tab_unmatched,
            text="🔗 Match Selected Products",
            command=self.match_selected_products
        ).grid(row=3, column=0, columnspan=2, pady=10)
        
    def filter_unmatched_products(self):
        """Filter unmatched products based on search criteria"""
        woo_search = self.unmatched_woo_search.get().strip().lower()
        capital_search = self.unmatched_capital_search.get().strip().lower()
        
        # Clear current items
        for item in self.unmatched_woo_tree.get_children():
            self.unmatched_woo_tree.delete(item)
        for item in self.unmatched_capital_tree.get_children():
            self.unmatched_capital_tree.delete(item)
            
        # Filter WooCommerce unmatched
        for product in data_store.unmatched_woo:
            sku = product.get('sku', '').lower()
            name = product.get('name', '').lower()
            
            if not woo_search or woo_search in sku or woo_search in name:
                self.unmatched_woo_tree.insert("", "end", values=(
                    product.get('sku', ''),
                    product.get('name', '')[:50]
                ))
                
        # Filter Capital unmatched
        for product in data_store.unmatched_capital:
            code = product.get('CODE', '').lower()
            descr = product.get('DESCR', '').lower()
            
            if not capital_search or capital_search in code or capital_search in descr:
                self.unmatched_capital_tree.insert("", "end", values=(
                    product.get('CODE', ''),
                    product.get('DESCR', '')[:50]
                ))
                
    def clear_unmatched_filters(self):
        """Clear unmatched product filters"""
        self.unmatched_woo_search.delete(0, "end")
        self.unmatched_capital_search.delete(0, "end")
        self.filter_unmatched_products()
        
    def on_unmatched_woo_double_click(self, event):
        """Handle double-click on unmatched WooCommerce product"""
        selection = self.unmatched_woo_tree.selection()
        if selection:
            values = self.unmatched_woo_tree.item(selection[0], "values")
            sku = values[0]
            # Find the full product data
            for product in data_store.unmatched_woo:
                if product.get('sku', '') == sku:
                    self.open_unmatched_woo_editor(product)
                    break
                    
    def on_unmatched_capital_double_click(self, event):
        """Handle double-click on unmatched Capital product"""
        selection = self.unmatched_capital_tree.selection()
        if selection:
            values = self.unmatched_capital_tree.item(selection[0], "values")
            code = values[0]
            # Find the full product data
            for product in data_store.unmatched_capital:
                if product.get('CODE', '') == code:
                    self.open_unmatched_capital_editor(product)
                    break
                    
    def open_unmatched_woo_editor(self, product):
        """Open editor dialog for unmatched WooCommerce product"""
        UnmatchedWooEditorDialog(self, product, self.woo_client)
        
    def open_unmatched_capital_editor(self, product):
        """Open editor dialog for unmatched Capital product"""
        UnmatchedCapitalEditorDialog(self, product, self.db)
        
    def match_selected_products(self):
        """Match selected products manually"""
        woo_selection = self.unmatched_woo_tree.selection()
        capital_selection = self.unmatched_capital_tree.selection()
        
        if not woo_selection or not capital_selection:
            messagebox.showwarning("Warning", "Please select a product from each list to match")
            return
            
        # Get selected items
        woo_item = self.unmatched_woo_tree.item(woo_selection[0], "values")
        capital_item = self.unmatched_capital_tree.item(capital_selection[0], "values")
        
        woo_sku = woo_item[0]
        capital_code = capital_item[0]
        
        # Confirm match
        if not messagebox.askyesno(
            "Confirm Manual Match",
            f"Match these products?\n\n"
            f"WooCommerce:\n  SKU: {woo_sku}\n  Name: {woo_item[1]}\n\n"
            f"Capital:\n  CODE: {capital_code}\n  Description: {capital_item[1]}\n\n"
            f"This will create a matched product entry."
        ):
            return
        
        try:
            # Find full product data
            woo_product = None
            for product in data_store.unmatched_woo:
                if product.get('sku', '') == woo_sku:
                    woo_product = product
                    break
            
            capital_product = None
            for product in data_store.unmatched_capital:
                if product.get('CODE', '') == capital_code:
                    capital_product = product
                    break
            
            if not woo_product or not capital_product:
                messagebox.showerror("Error", "Could not find full product data")
                return
            
            # Create matched product entry
            regular_price = float(woo_product.get('regular_price') or 0)
            sale_price = float(woo_product.get('sale_price') or 0)
            discount_percent = 0
            if regular_price > 0 and sale_price > 0:
                discount_percent = round((1 - sale_price / regular_price) * 100, 2)
            
            matched_product = {
                'sku': woo_sku,
                'woo_id': woo_product['id'],
                'parent_id': woo_product.get('parent_id'),
                'woo_name': woo_product.get('name', ''),
                'woo_regular_price': regular_price,
                'woo_sale_price': sale_price,
                'woo_discount_percent': discount_percent,
                'woo_stock_quantity': woo_product.get('stock_quantity'),
                'woo_stock_status': woo_product.get('stock_status'),
                'woo_total_sales': woo_product.get('total_sales', 0),
                'woo_description': woo_product.get('description', ''),
                'woo_short_description': woo_product.get('short_description', ''),
                'woo_categories': [cat.get('name', '') for cat in woo_product.get('categories', [])],
                'woo_permalink': woo_product.get('permalink', ''),
                'woo_date_created': woo_product.get('date_created', ''),
                'woo_date_modified': woo_product.get('date_modified', ''),
                
                'capital_code': capital_product.get('CODE', ''),
                'capital_descr': capital_product.get('DESCR', ''),
                'capital_rtlprice': float(capital_product.get('RTLPRICE') or 0),
                'capital_whsprice': float(capital_product.get('WHSPRICE') or 0),
                'capital_trmode': capital_product.get('TRMODE', 0),
                'capital_discount': float(capital_product.get('DISCOUNT') or 0),
                'capital_maxdiscount': float(capital_product.get('MAXDISCOUNT') or 0),
                'capital_stock': float(capital_product.get('BALANCEQTY') or 0),
                
                'price_match': abs(regular_price - float(capital_product.get('RTLPRICE') or 0)) < 0.01,
                'manually_matched': True
            }
            
            # Add to matched products
            data_store.matched_products.append(matched_product)
            
            # Remove from unmatched lists
            data_store.unmatched_woo = [p for p in data_store.unmatched_woo if p.get('sku', '') != woo_sku]
            data_store.unmatched_capital = [p for p in data_store.unmatched_capital if p.get('CODE', '') != capital_code]
            
            # Refresh UI
            data_store.notify_data_changed()
            
            self.log(f"Manually matched: WOO SKU {woo_sku} <-> Capital CODE {capital_code}")
            messagebox.showinfo("Success", f"Successfully matched products!\n\nSKU: {woo_sku}\nCODE: {capital_code}\n\nThe matched product now appears in Products and Prices tabs.")
            
        except Exception as e:
            self.log(f"Error in manual matching: {str(e)}")
            messagebox.showerror("Error", f"Failed to match products: {str(e)}")

        
    # ========================================================================
    # ANALYTICS TAB
    # ========================================================================
    
    def setup_analytics_tab(self):
        """Setup analytics tab"""
        self.tab_analytics.grid_columnconfigure(0, weight=1)
        self.tab_analytics.grid_rowconfigure(1, weight=1)
        
        # Controls
        controls_frame = ctk.CTkFrame(self.tab_analytics)
        controls_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(controls_frame, text="Search SKU:").grid(row=0, column=0, padx=5, pady=5)
        self.analytics_sku_entry = ctk.CTkEntry(controls_frame, width=150)
        self.analytics_sku_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkButton(
            controls_frame,
            text="📊 View Analytics",
            command=self.view_product_analytics
        ).grid(row=0, column=2, padx=10, pady=5)
        
        # Analytics content
        self.analytics_content = ctk.CTkFrame(self.tab_analytics)
        self.analytics_content.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Top sellers
        top_sellers_frame = ctk.CTkFrame(self.analytics_content)
        top_sellers_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            top_sellers_frame,
            text="🏆 Top Selling Products",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        self.top_sellers_text = ctk.CTkTextbox(top_sellers_frame, height=200)
        self.top_sellers_text.pack(fill="x", padx=10, pady=10)
        
        # Product details
        details_frame = ctk.CTkFrame(self.analytics_content)
        details_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            details_frame,
            text="📦 Product Details",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        self.product_details_text = ctk.CTkTextbox(details_frame, height=300)
        self.product_details_text.pack(fill="both", expand=True, padx=10, pady=10)
        
    def view_product_analytics(self):
        """View analytics for a product"""
        sku = self.analytics_sku_entry.get().strip().upper()
        if not sku:
            messagebox.showwarning("Warning", "Please enter a SKU")
            return
            
        product = data_store.get_product_by_sku(sku)
        if not product:
            messagebox.showinfo("Not Found", f"No product found with SKU: {sku}")
            return
            
        # Display product details
        details = f"""
=== Product Details for {sku} ===

📦 Product Name: {product.get('woo_name', 'N/A')}
🏷️ SKU: {product.get('sku', 'N/A')}

💰 Pricing:
  - WooCommerce Regular Price: €{product.get('woo_regular_price', 0):.2f}
  - WooCommerce Sale Price: €{product.get('woo_sale_price', 0):.2f}
  - Capital RTLPRICE: €{product.get('capital_rtlprice', 0):.2f}
  - Discount: {product.get('woo_discount_percent', 0):.1f}%

📊 Sales:
  - Total Sales: {product.get('woo_total_sales', 0)} units

📦 Stock:
  - Stock Status: {product.get('woo_stock_status', 'N/A')}
  - Stock Quantity: {product.get('woo_stock_quantity', 'N/A')}
  - Capital TRMODE: {product.get('capital_trmode', 'N/A')}

📁 Categories: {', '.join(product.get('woo_categories', []))}

🔗 Link: {product.get('woo_permalink', 'N/A')}

📅 Dates:
  - Created: {product.get('woo_date_created', 'N/A')}
  - Modified: {product.get('woo_date_modified', 'N/A')}
"""
        
        self.product_details_text.delete("1.0", "end")
        self.product_details_text.insert("1.0", details)
        
    # ========================================================================
    # LOGS TAB
    # ========================================================================
    
    def setup_logs_tab(self):
        """Setup logs tab"""
        self.tab_logs.grid_columnconfigure(0, weight=1)
        self.tab_logs.grid_rowconfigure(0, weight=1)
        
        self.logs_text = ctk.CTkTextbox(self.tab_logs, wrap="word")
        self.logs_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Clear button
        ctk.CTkButton(
            self.tab_logs,
            text="🗑️ Clear Logs",
            command=lambda: self.logs_text.delete("1.0", "end")
        ).grid(row=1, column=0, pady=10)
        
    def log(self, message):
        """Add a log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.logs_text.insert("end", log_entry)
        self.logs_text.see("end")
        
    # ========================================================================
    # DATA FETCHING
    # ========================================================================
    
    def start_data_fetch(self):
        """Start fetching data in background thread"""
        if data_store.is_loading:
            messagebox.showwarning("Warning", "Already fetching data...")
            return
            
        self.fetch_btn.configure(state="disabled", text="⏳ Fetching...")
        threading.Thread(target=self.fetch_all_data, daemon=True).start()
        
    def fetch_all_data(self):
        """Fetch all data from WooCommerce and Capital"""
        try:
            data_store.set_loading(True, 0, "Starting data fetch...")
            self.log("Starting data fetch...")
            
            # Fetch WooCommerce products
            data_store.set_loading(True, 10, "Fetching WooCommerce products...")
            self.log("Fetching WooCommerce products...")
            
            def woo_progress(progress, status):
                data_store.set_loading(True, 10 + int(progress * 0.3), status)
                
            data_store.woo_products = self.woo_client.get_all_products(progress_callback=woo_progress)
            self.log(f"Fetched {len(data_store.woo_products)} WooCommerce products")
            
            # Fetch product variations for variable products (only if enabled)
            if self.fetch_variations_var.get():
                data_store.set_loading(True, 40, "Fetching product variations (parallel)...")
                self.log("Fetching product variations in parallel...")
                
                variation_count = 0
                variable_products = [p for p in data_store.woo_products if p.get('type') == 'variable']
                
                # Parallel fetching with ThreadPoolExecutor
                def fetch_variations_for_product(product):
                    """Fetch variations for a single product"""
                    try:
                        variations = self.woo_client.get_product_variations(product['id'])
                        result = []
                        if variations:
                            for variation in variations:
                                variation_product = {
                                    'id': variation['id'],
                                    'parent_id': product['id'],
                                    'name': f"{product['name']} - {', '.join([attr['option'] for attr in variation.get('attributes', [])])}",
                                    'sku': variation.get('sku', ''),
                                    'regular_price': variation.get('regular_price', ''),
                                    'sale_price': variation.get('sale_price', ''),
                                    'stock_quantity': variation.get('stock_quantity'),
                                    'stock_status': variation.get('stock_status'),
                                    'description': variation.get('description', ''),
                                    'short_description': product.get('short_description', ''),
                                    'categories': product.get('categories', []),
                                    'permalink': variation.get('permalink', ''),
                                    'date_created': variation.get('date_created', ''),
                                    'date_modified': variation.get('date_modified', ''),
                                    'total_sales': product.get('total_sales', 0),
                                    'attributes': variation.get('attributes', []),
                                    'is_variation': True
                                }
                                if variation_product['sku']:
                                    result.append(variation_product)
                        return result
                    except Exception as e:
                        self.log(f"Error fetching variations for product {product.get('id')}: {e}")
                        return []
                
                # Use ThreadPoolExecutor for parallel fetching (10 concurrent threads)
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = {executor.submit(fetch_variations_for_product, product): product for product in variable_products}
                    
                    completed = 0
                    for future in as_completed(futures):
                        variations = future.result()
                        data_store.woo_products.extend(variations)
                        variation_count += len(variations)
                        
                        completed += 1
                        if completed % 10 == 0:  # Update progress every 10 products
                            progress = int(completed / len(variable_products) * 100)
                            data_store.set_loading(True, 40 + int(progress * 0.05), f"Fetching variations... {completed}/{len(variable_products)}")
                        
                self.log(f"Fetched {variation_count} product variations from {len(variable_products)} variable products (parallel mode)")
            else:
                self.log("Skipping product variations (checkbox not enabled)")
                data_store.set_loading(True, 40, "Skipping variations...")
            
            # Fetch WooCommerce categories
            data_store.set_loading(True, 45, "Fetching categories...")
            data_store.woo_categories = self.woo_client.get_categories()
            self.log(f"Fetched {len(data_store.woo_categories)} categories")
            
            # Fetch WooCommerce orders (last 90 days)
            data_store.set_loading(True, 50, "Fetching orders...")
            self.log("Fetching WooCommerce orders...")
            
            after_date = (datetime.now() - timedelta(days=90)).isoformat()
            
            def order_progress(progress, status):
                data_store.set_loading(True, 50 + int(progress * 0.2), status)
                
            data_store.woo_orders = self.woo_client.get_all_orders(
                after=after_date,
                progress_callback=order_progress
            )
            self.log(f"Fetched {len(data_store.woo_orders)} orders")
            
            # Fetch Capital products
            data_store.set_loading(True, 75, "Fetching Capital ERP products...")
            self.log("Fetching Capital ERP products...")
            
            data_store.capital_products = self.capital_client.get_products()
            self.log(f"Fetched {len(data_store.capital_products)} Capital products")
            
            # Match products
            data_store.set_loading(True, 90, "Matching products...")
            self.log("Matching products...")
            
            matched, unmatched_woo, unmatched_capital = ProductMatcher.match_products(
                data_store.woo_products,
                data_store.capital_products
            )
            
            data_store.matched_products = matched
            data_store.unmatched_woo = unmatched_woo
            data_store.unmatched_capital = unmatched_capital
            
            self.log(f"Matched: {len(matched)}, Unmatched WOO: {len(unmatched_woo)}, Unmatched Capital: {len(unmatched_capital)}")
            
            # Update fetch time
            data_store.last_fetch_time = datetime.now()
            
            data_store.set_loading(False, 100, "Data fetch complete!")
            self.log("Data fetch complete!")
            
            # Notify data changed
            data_store.notify_data_changed()
            
        except Exception as e:
            data_store.set_loading(False, 0, f"Error: {str(e)}")
            self.log(f"Error fetching data: {str(e)}")
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            
        finally:
            self.after(0, lambda: self.fetch_btn.configure(state="normal", text="📥 Fetch All Data"))
            
    # ========================================================================
    # SELECTIVE REFRESH METHODS
    # ========================================================================
    
    def refresh_capital_prices_for_checked(self):
        """Refresh Capital prices for checked products in Products tab"""
        checked_items = [item_id for item_id, checked in self.product_checkboxes.items() if checked]
        
        if not checked_items:
            messagebox.showwarning("Warning", "Please check products to refresh")
            return
        
        # Get SKUs of checked products
        skus = []
        for item in checked_items:
            values = self.products_tree.item(item, "values")
            sku = values[1]  # SKU is in column 1
            skus.append(sku)
        
        self.log(f"Refreshing Capital prices for {len(skus)} products...")
        threading.Thread(target=self.refresh_capital_prices_background, args=(skus,), daemon=True).start()
    
    def refresh_woo_prices_for_checked(self):
        """Refresh WooCommerce prices for checked products in Products tab"""
        checked_items = [item_id for item_id, checked in self.product_checkboxes.items() if checked]
        
        if not checked_items:
            messagebox.showwarning("Warning", "Please check products to refresh")
            return
        
        # Get product IDs and parent IDs of checked products
        products_to_refresh = []
        for item in checked_items:
            values = self.products_tree.item(item, "values")
            sku = values[1]  # SKU is in column 1
            product = data_store.get_product_by_sku(sku)
            if product:
                products_to_refresh.append({
                    'id': product['woo_id'],
                    'parent_id': product.get('parent_id'),
                    'sku': sku
                })
        
        self.log(f"Refreshing WooCommerce prices for {len(products_to_refresh)} products...")
        threading.Thread(target=self.refresh_woo_prices_background, args=(products_to_refresh,), daemon=True).start()
    
    def refresh_capital_prices_for_checked_prices_tab(self):
        """Refresh Capital prices for checked products in Prices tab"""
        checked_items = [item_id for item_id, checked in self.price_checkboxes.items() if checked]
        
        if not checked_items:
            messagebox.showwarning("Warning", "Please check products to refresh")
            return
        
        # Get SKUs of checked products
        skus = []
        for item in checked_items:
            values = self.prices_tree.item(item, "values")
            sku = values[1]  # SKU is in column 1
            skus.append(sku)
        
        self.log(f"Refreshing Capital prices for {len(skus)} products...")
        threading.Thread(target=self.refresh_capital_prices_background, args=(skus,), daemon=True).start()
    
    def refresh_woo_prices_for_checked_prices_tab(self):
        """Refresh WooCommerce prices for checked products in Prices tab"""
        checked_items = [item_id for item_id, checked in self.price_checkboxes.items() if checked]
        
        if not checked_items:
            messagebox.showwarning("Warning", "Please check products to refresh")
            return
        
        # Get product IDs and parent IDs of checked products
        products_to_refresh = []
        for item in checked_items:
            values = self.prices_tree.item(item, "values")
            sku = values[1]  # SKU is in column 1
            product = data_store.get_product_by_sku(sku)
            if product:
                products_to_refresh.append({
                    'id': product['woo_id'],
                    'parent_id': product.get('parent_id'),
                    'sku': sku
                })
        
        self.log(f"Refreshing WooCommerce prices for {len(products_to_refresh)} products...")
        threading.Thread(target=self.refresh_woo_prices_background, args=(products_to_refresh,), daemon=True).start()
    
    def refresh_capital_prices_background(self, skus):
        """Background thread to refresh Capital prices for specific SKUs"""
        try:
            data_store.set_loading(True, 0, "Refreshing Capital prices...")
            
            # Build filter for Capital API to get only these SKUs
            # Capital API filter format: "CODE IN ('SKU1','SKU2','SKU3')"
            sku_list = "','".join(skus)
            filters = f"CODE IN ('{sku_list}')"
            
            # Fetch from Capital
            capital_products = self.capital_client.get_products(filters=filters)
            self.log(f"Fetched {len(capital_products)} products from Capital")
            
            # Update matched products with new Capital prices
            updated_count = 0
            for cap_product in capital_products:
                code = str(cap_product.get('CODE', '')).strip().upper()
                for i, matched_product in enumerate(data_store.matched_products):
                    if matched_product.get('sku', '').strip().upper() == code:
                        # Update Capital fields
                        data_store.matched_products[i]['capital_rtlprice'] = float(cap_product.get('RTLPRICE') or 0)
                        data_store.matched_products[i]['capital_whsprice'] = float(cap_product.get('WHSPRICE') or 0)
                        data_store.matched_products[i]['capital_discount'] = float(cap_product.get('DISCOUNT') or 0)
                        data_store.matched_products[i]['capital_maxdiscount'] = float(cap_product.get('MAXDISCOUNT') or 0)
                        data_store.matched_products[i]['capital_stock'] = float(cap_product.get('BALANCEQTY') or 0)
                        
                        # Recalculate price match
                        woo_price = matched_product.get('woo_regular_price', 0)
                        cap_price = float(cap_product.get('RTLPRICE') or 0)
                        data_store.matched_products[i]['price_match'] = abs(woo_price - cap_price) < 0.01
                        
                        updated_count += 1
                        self.log(f"Updated Capital price for {code}: €{cap_price:.2f}")
                        break
            
            data_store.set_loading(False, 100, "Capital prices refreshed!")
            self.log(f"Successfully refreshed {updated_count} Capital prices")
            
            # Notify data changed to refresh UI
            data_store.notify_data_changed()
            
            self.after(0, lambda: messagebox.showinfo("Success", f"Refreshed {updated_count} Capital prices"))
            
        except Exception as e:
            data_store.set_loading(False, 0, "Refresh failed")
            self.log(f"Error refreshing Capital prices: {str(e)}")
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to refresh Capital prices: {str(e)}"))
    
    def refresh_woo_prices_background(self, products_to_refresh):
        """Background thread to refresh WooCommerce prices for specific products"""
        try:
            data_store.set_loading(True, 0, "Refreshing WooCommerce prices...")
            
            updated_count = 0
            for i, product_info in enumerate(products_to_refresh):
                try:
                    product_id = product_info['id']
                    parent_id = product_info.get('parent_id')
                    sku = product_info['sku']
                    
                    # Determine correct endpoint
                    if parent_id:
                        url = f"{WOOCOMMERCE_CONFIG['store_url']}/wp-json/wc/v3/products/{parent_id}/variations/{product_id}"
                    else:
                        url = f"{WOOCOMMERCE_CONFIG['store_url']}/wp-json/wc/v3/products/{product_id}"
                    
                    # Fetch from WooCommerce
                    response = requests.get(
                        url,
                        auth=HTTPBasicAuth(
                            WOOCOMMERCE_CONFIG['consumer_key'],
                            WOOCOMMERCE_CONFIG['consumer_secret']
                        ),
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        product_data = response.json()
                        
                        # Update matched product
                        for j, matched_product in enumerate(data_store.matched_products):
                            if matched_product.get('woo_id') == product_id:
                                # Update WooCommerce fields
                                regular_price = float(product_data.get('regular_price', 0) or 0)
                                sale_price = float(product_data.get('sale_price', 0) or 0)
                                
                                data_store.matched_products[j]['woo_regular_price'] = regular_price
                                data_store.matched_products[j]['woo_sale_price'] = sale_price
                                
                                # Recalculate discount
                                if regular_price > 0 and sale_price > 0:
                                    discount_percent = round((1 - sale_price / regular_price) * 100, 2)
                                    data_store.matched_products[j]['woo_discount_percent'] = discount_percent
                                else:
                                    data_store.matched_products[j]['woo_discount_percent'] = 0
                                
                                # Recalculate price match
                                cap_price = matched_product.get('capital_rtlprice', 0)
                                data_store.matched_products[j]['price_match'] = abs(regular_price - cap_price) < 0.01
                                
                                updated_count += 1
                                self.log(f"Updated WooCommerce price for {sku}: €{regular_price:.2f}")
                                break
                    
                    # Update progress
                    progress = int((i + 1) / len(products_to_refresh) * 100)
                    data_store.set_loading(True, progress, f"Refreshed {i + 1}/{len(products_to_refresh)} products")
                    
                except Exception as e:
                    self.log(f"Error refreshing {sku}: {str(e)}")
            
            data_store.set_loading(False, 100, "WooCommerce prices refreshed!")
            self.log(f"Successfully refreshed {updated_count} WooCommerce prices")
            
            # Notify data changed to refresh UI
            data_store.notify_data_changed()
            
            self.after(0, lambda: messagebox.showinfo("Success", f"Refreshed {updated_count} WooCommerce prices"))
            
        except Exception as e:
            data_store.set_loading(False, 0, "Refresh failed")
            self.log(f"Error refreshing WooCommerce prices: {str(e)}")
            self.after(0, lambda: messagebox.showerror("Error", f"Failed to refresh WooCommerce prices: {str(e)}"))
    
    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================
    
    def on_data_updated(self):
        """Handle data update notification"""
        self.after(0, self.refresh_all_ui)
        
    def on_loading_updated(self):
        """Handle loading state update"""
        self.after(0, self.update_loading_ui)
        
    def update_loading_ui(self):
        """Update loading UI elements"""
        self.progress_bar.set(data_store.load_progress / 100)
        self.status_label.configure(text=data_store.load_status)
        
    def refresh_all_ui(self):
        """Refresh all UI elements with current data"""
        # Update counts
        self.counts_label.configure(
            text=f"WOO: {len(data_store.woo_products)} | CAPITAL: {len(data_store.capital_products)} | MATCHED: {len(data_store.matched_products)}"
        )
        
        # Update last fetch time
        if data_store.last_fetch_time:
            self.last_fetch_label.configure(
                text=f"Last fetch: {data_store.last_fetch_time.strftime('%H:%M:%S')}"
            )
            
        # Update overview cards
        self.woo_card.value_label.configure(text=str(len(data_store.woo_products)))
        self.capital_card.value_label.configure(text=str(len(data_store.capital_products)))
        self.matched_card.value_label.configure(text=str(len(data_store.matched_products)))
        
        # Count price mismatches
        mismatches = sum(1 for p in data_store.matched_products if not p.get('price_match'))
        self.mismatch_card.value_label.configure(text=str(mismatches))
        
        # Update brand filter - extract unique brands from product names
        # Brands are typically the first word/part of the product name (e.g., "3M", "ABICOR BINZEL")
        brands_set = set()
        for product in data_store.woo_products:
            name = product.get('name', '')
            # Extract first part of name as brand (before first space or dash)
            if name:
                # Try to extract brand from beginning of product name
                parts = name.split()
                if parts:
                    # Check if first part looks like a brand (uppercase, alphanumeric)
                    potential_brand = parts[0].strip()
                    if potential_brand and len(potential_brand) <= 30:
                        brands_set.add(potential_brand)
        
        brands = ["All Brands"] + sorted(brands_set)
        self.product_category_filter.configure(values=brands)
        
        # Refresh products table
        self.filter_products()
        
        # Refresh prices table
        self.refresh_prices_table()
        
        # Refresh unmatched products (now using tree views with search)
        self.filter_unmatched_products()
            
        # Update top sellers
        self.update_top_sellers()
        
    def update_top_sellers(self):
        """Update top sellers display"""
        # Sort by total_sales
        sorted_products = sorted(
            data_store.matched_products,
            key=lambda x: x.get('woo_total_sales', 0),
            reverse=True
        )[:20]
        
        self.top_sellers_text.delete("1.0", "end")
        
        text = "Top 20 Best Selling Products:\n\n"
        for i, product in enumerate(sorted_products, 1):
            text += f"{i}. {product.get('sku', 'N/A')} - {product.get('woo_name', 'N/A')[:40]}\n"
            text += f"   Sales: {product.get('woo_total_sales', 0)} | Price: €{product.get('woo_regular_price', 0):.2f}\n\n"
            
        self.top_sellers_text.insert("1.0", text)
        
    # ========================================================================
    # PRODUCT EDITORS
    # ========================================================================
    
    def open_product_editor(self, sku):
        """Open product editor dialog"""
        product = data_store.get_product_by_sku(sku)
        if not product:
            messagebox.showerror("Error", f"Product not found: {sku}")
            return
            
        ProductEditorDialog(self, product, self.woo_client, self.db)
        
    def open_price_editor(self, sku):
        """Open price editor dialog"""
        product = data_store.get_product_by_sku(sku)
        if not product:
            messagebox.showerror("Error", f"Product not found: {sku}")
            return
            
        PriceEditorDialog(self, product, self.woo_client, self.db)
        
    def sync_prices_from_capital(self):
        """Quick action to sync prices from Capital"""
        mismatches = [p for p in data_store.matched_products if not p.get('price_match')]
        
        if not mismatches:
            messagebox.showinfo("Info", "All prices are already synchronized!")
            return
            
        if messagebox.askyesno("Confirm", f"Update {len(mismatches)} products to Capital prices?"):
            updates = [{
                "id": p['woo_id'],
                "regular_price": str(p['capital_rtlprice'])
            } for p in mismatches]
            
            threading.Thread(target=self.batch_update_prices, args=(updates,)).start()


# ============================================================================
# DIALOG WINDOWS
# ============================================================================

class ProductEditorDialog(ctk.CTkToplevel):
    """Dialog for editing product details"""
    
    def __init__(self, parent, product, woo_client, db):
        super().__init__(parent)
        
        self.product = product
        self.woo_client = woo_client
        self.db = db
        
        self.title(f"Edit Product: {product.get('sku', 'Unknown')}")
        self.geometry("700x600")
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup editor UI"""
        # Product info
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text=f"SKU: {self.product.get('sku', 'N/A')}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        ctk.CTkLabel(
            info_frame,
            text=self.product.get('woo_name', 'No name'),
            font=ctk.CTkFont(size=14)
        ).pack(pady=5)
        
        # Form
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Regular price
        ctk.CTkLabel(form_frame, text="Regular Price (€):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.regular_price_entry = ctk.CTkEntry(form_frame, width=150)
        self.regular_price_entry.grid(row=0, column=1, padx=10, pady=10)
        self.regular_price_entry.insert(0, str(self.product.get('woo_regular_price', '')))
        
        ctk.CTkLabel(
            form_frame,
            text=f"Capital: €{self.product.get('capital_rtlprice', 0):.2f}",
            text_color="gray"
        ).grid(row=0, column=2, padx=10, pady=10)
        
        # Sale price
        ctk.CTkLabel(form_frame, text="Sale Price (€):").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.sale_price_entry = ctk.CTkEntry(form_frame, width=150)
        self.sale_price_entry.grid(row=1, column=1, padx=10, pady=10)
        if self.product.get('woo_sale_price'):
            self.sale_price_entry.insert(0, str(self.product.get('woo_sale_price', '')))
            
        # Discount calculator
        ctk.CTkButton(
            form_frame,
            text="Calculate Discount",
            command=self.calculate_discount,
            width=120
        ).grid(row=1, column=2, padx=10, pady=10)
        
        # Short description
        ctk.CTkLabel(form_frame, text="Short Description:").grid(row=2, column=0, padx=10, pady=10, sticky="nw")
        self.short_desc_text = ctk.CTkTextbox(form_frame, width=400, height=80)
        self.short_desc_text.grid(row=2, column=1, columnspan=2, padx=10, pady=10)
        self.short_desc_text.insert("1.0", self.product.get('woo_short_description', ''))
        
        # Description
        ctk.CTkLabel(form_frame, text="Description:").grid(row=3, column=0, padx=10, pady=10, sticky="nw")
        self.desc_text = ctk.CTkTextbox(form_frame, width=400, height=150)
        self.desc_text.grid(row=3, column=1, columnspan=2, padx=10, pady=10)
        self.desc_text.insert("1.0", self.product.get('woo_description', ''))
        
        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save Changes",
            command=self.save_changes,
            fg_color="green"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancel",
            command=self.destroy,
            fg_color="gray"
        ).pack(side="right", padx=10)
        
    def calculate_discount(self):
        """Calculate sale price based on discount percentage"""
        try:
            regular = float(self.regular_price_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid regular price")
            return
            
        discount = ctk.CTkInputDialog(
            text="Enter discount percentage:",
            title="Calculate Discount"
        ).get_input()
        
        if discount:
            try:
                discount_pct = float(discount)
                sale_price = regular * (1 - discount_pct / 100)
                self.sale_price_entry.delete(0, "end")
                self.sale_price_entry.insert(0, f"{sale_price:.2f}")
            except ValueError:
                messagebox.showerror("Error", "Invalid discount percentage")
                
    def save_changes(self):
        """Save changes to WooCommerce"""
        try:
            data = {}
            
            # Price
            regular_price = self.regular_price_entry.get().strip()
            if regular_price:
                data['regular_price'] = regular_price
                
            sale_price = self.sale_price_entry.get().strip()
            data['sale_price'] = sale_price if sale_price else ""
            
            # Descriptions
            short_desc = self.short_desc_text.get("1.0", "end").strip()
            data['short_description'] = short_desc
            
            description = self.desc_text.get("1.0", "end").strip()
            data['description'] = description
            
            # Update WooCommerce
            self.woo_client.update_product(self.product['woo_id'], data)
            
            # Record in database
            if 'regular_price' in data:
                self.db.record_update(
                    self.product['sku'],
                    'regular_price',
                    self.product.get('woo_regular_price'),
                    data['regular_price']
                )
                
            # Update local cache
            data_store.update_woo_product_locally(self.product['woo_id'], data)
            
            messagebox.showinfo("Success", "Product updated successfully!")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update: {str(e)}")


class PriceEditorDialog(ctk.CTkToplevel):
    """Dialog for quick price editing"""
    
    def __init__(self, parent, product, woo_client, db):
        super().__init__(parent)
        
        self.product = product
        self.woo_client = woo_client
        self.db = db
        
        self.title(f"Edit Price: {product.get('sku', 'Unknown')}")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup price editor UI"""
        # Product info
        ctk.CTkLabel(
            self,
            text=f"SKU: {self.product.get('sku', 'N/A')}",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        ctk.CTkLabel(
            self,
            text=self.product.get('woo_name', 'No name')[:50],
            font=ctk.CTkFont(size=12)
        ).pack(pady=5)
        
        # Price comparison
        compare_frame = ctk.CTkFrame(self)
        compare_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            compare_frame,
            text=f"WooCommerce Price: €{self.product.get('woo_regular_price', 0):.2f}",
            font=ctk.CTkFont(size=14)
        ).pack(pady=5)
        
        ctk.CTkLabel(
            compare_frame,
            text=f"Capital Price: €{self.product.get('capital_rtlprice', 0):.2f}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="green"
        ).pack(pady=5)
        
        # New price entry
        entry_frame = ctk.CTkFrame(self)
        entry_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(entry_frame, text="New Regular Price (€):").pack(pady=5)
        self.price_entry = ctk.CTkEntry(entry_frame, width=150)
        self.price_entry.pack(pady=5)
        self.price_entry.insert(0, str(self.product.get('capital_rtlprice', '')))
        
        ctk.CTkLabel(entry_frame, text="New Sale Price (€):").pack(pady=5)
        self.sale_entry = ctk.CTkEntry(entry_frame, width=150)
        self.sale_entry.pack(pady=5)
        if self.product.get('woo_sale_price'):
            self.sale_entry.insert(0, str(self.product.get('woo_sale_price', '')))
            
        # Quick buttons
        quick_frame = ctk.CTkFrame(self)
        quick_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            quick_frame,
            text="Use Capital Price",
            command=self.use_capital_price
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            quick_frame,
            text="Clear Sale Price",
            command=lambda: self.sale_entry.delete(0, "end")
        ).pack(side="left", padx=5)
        
        # Save/Cancel
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save",
            command=self.save_price,
            fg_color="green"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancel",
            command=self.destroy,
            fg_color="gray"
        ).pack(side="right", padx=10)
        
    def use_capital_price(self):
        """Set price to Capital price"""
        self.price_entry.delete(0, "end")
        self.price_entry.insert(0, str(self.product.get('capital_rtlprice', '')))
        
    def save_price(self):
        """Save price changes"""
        try:
            data = {}
            
            price = self.price_entry.get().strip()
            if price:
                data['regular_price'] = price
                
            sale = self.sale_entry.get().strip()
            data['sale_price'] = sale if sale else ""
            
            self.woo_client.update_product(self.product['woo_id'], data)
            
            # Record history
            if 'regular_price' in data:
                self.db.record_price_history(
                    self.product['sku'],
                    float(data.get('regular_price', 0)),
                    float(data.get('sale_price', 0)) if data.get('sale_price') else 0
                )
                
            # Update local cache
            data_store.update_woo_product_locally(self.product['woo_id'], data)
            
            messagebox.showinfo("Success", "Price updated!")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update: {str(e)}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app = BridgeApp()
    app.mainloop()


class UnmatchedWooEditorDialog(ctk.CTkToplevel):
    """Dialog for editing unmatched WooCommerce products"""
    
    def __init__(self, parent, product, woo_client):
        super().__init__(parent)
        
        self.product = product
        self.woo_client = woo_client
        
        self.title(f"Edit WooCommerce Product: {product.get('sku', 'Unknown')}")
        self.geometry("600x700")
        self.transient(parent)
        self.grab_set()
        
        # Main frame
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # SKU (read-only)
        ctk.CTkLabel(main_frame, text="SKU:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        sku_entry = ctk.CTkEntry(main_frame, width=400)
        sku_entry.insert(0, product.get('sku', ''))
        sku_entry.configure(state="readonly")
        sku_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Name
        ctk.CTkLabel(main_frame, text="Name:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.name_entry = ctk.CTkEntry(main_frame, width=400)
        self.name_entry.insert(0, product.get('name', ''))
        self.name_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Regular Price
        ctk.CTkLabel(main_frame, text="Regular Price (€):", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.regular_price_entry = ctk.CTkEntry(main_frame, width=200)
        self.regular_price_entry.insert(0, str(product.get('regular_price', '')))
        self.regular_price_entry.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # Sale Price
        ctk.CTkLabel(main_frame, text="Sale Price (€):", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.sale_price_entry = ctk.CTkEntry(main_frame, width=200)
        self.sale_price_entry.insert(0, str(product.get('sale_price', '')))
        self.sale_price_entry.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        # Discount calculator
        ctk.CTkButton(
            main_frame,
            text="🧮 Calculate Discount",
            command=self.calculate_discount,
            width=150
        ).grid(row=4, column=1, sticky="w", padx=10, pady=5)
        
        # Short Description
        ctk.CTkLabel(main_frame, text="Short Description:", font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, sticky="nw", padx=10, pady=5)
        self.short_desc_text = ctk.CTkTextbox(main_frame, width=400, height=100)
        self.short_desc_text.grid(row=5, column=1, padx=10, pady=5)
        self.short_desc_text.insert("1.0", product.get('short_description', ''))
        
        # Description
        ctk.CTkLabel(main_frame, text="Description:", font=ctk.CTkFont(weight="bold")).grid(row=6, column=0, sticky="nw", padx=10, pady=5)
        self.desc_text = ctk.CTkTextbox(main_frame, width=400, height=150)
        self.desc_text.grid(row=6, column=1, padx=10, pady=5)
        self.desc_text.insert("1.0", product.get('description', ''))
        
        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save Changes",
            command=self.save_changes,
            fg_color="green"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancel",
            command=self.destroy,
            fg_color="gray"
        ).pack(side="right", padx=10)
        
    def calculate_discount(self):
        """Calculate sale price based on discount percentage"""
        try:
            regular = float(self.regular_price_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid regular price")
            return
            
        discount = ctk.CTkInputDialog(
            text="Enter discount percentage:",
            title="Calculate Discount"
        ).get_input()
        
        if discount:
            try:
                discount_pct = float(discount)
                sale_price = regular * (1 - discount_pct / 100)
                self.sale_price_entry.delete(0, "end")
                self.sale_price_entry.insert(0, f"{sale_price:.2f}")
            except ValueError:
                messagebox.showerror("Error", "Invalid discount percentage")
                
    def save_changes(self):
        """Save changes to WooCommerce"""
        try:
            data = {}
            
            # Name
            name = self.name_entry.get().strip()
            if name:
                data['name'] = name
            
            # Price
            regular_price = self.regular_price_entry.get().strip()
            if regular_price:
                data['regular_price'] = regular_price
                
            sale_price = self.sale_price_entry.get().strip()
            data['sale_price'] = sale_price if sale_price else ""
            
            # Descriptions
            short_desc = self.short_desc_text.get("1.0", "end").strip()
            data['short_description'] = short_desc
            
            description = self.desc_text.get("1.0", "end").strip()
            data['description'] = description
            
            # Update WooCommerce
            self.woo_client.update_product(self.product['id'], data)
            
            messagebox.showinfo("Success", "Product updated successfully!")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update: {str(e)}")


class UnmatchedCapitalEditorDialog(ctk.CTkToplevel):
    """Dialog for editing unmatched Capital products"""
    
    def __init__(self, parent, product, db):
        super().__init__(parent)
        
        self.product = product
        self.db = db
        
        self.title(f"Edit Capital Product: {product.get('CODE', 'Unknown')}")
        self.geometry("600x600")
        self.transient(parent)
        self.grab_set()
        
        # Main frame
        main_frame = ctk.CTkScrollableFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # CODE
        ctk.CTkLabel(main_frame, text="CODE:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.code_entry = ctk.CTkEntry(main_frame, width=400)
        self.code_entry.insert(0, product.get('CODE', ''))
        self.code_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # NAME
        ctk.CTkLabel(main_frame, text="NAME:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.name_entry = ctk.CTkEntry(main_frame, width=400)
        self.name_entry.insert(0, product.get('NAME', ''))
        self.name_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # DESCR
        ctk.CTkLabel(main_frame, text="DESCRIPTION:", font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, sticky="nw", padx=10, pady=5)
        self.descr_text = ctk.CTkTextbox(main_frame, width=400, height=150)
        self.descr_text.grid(row=2, column=1, padx=10, pady=5)
        self.descr_text.insert("1.0", product.get('DESCR', ''))
        
        # RTLPRICE
        ctk.CTkLabel(main_frame, text="Retail Price (€):", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.rtlprice_entry = ctk.CTkEntry(main_frame, width=200)
        self.rtlprice_entry.insert(0, str(product.get('RTLPRICE', '')))
        self.rtlprice_entry.grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        # WHLPRICE
        ctk.CTkLabel(main_frame, text="Wholesale Price (€):", font=ctk.CTkFont(weight="bold")).grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.whlprice_entry = ctk.CTkEntry(main_frame, width=200)
        self.whlprice_entry.insert(0, str(product.get('WHLPRICE', '')))
        self.whlprice_entry.grid(row=4, column=1, sticky="w", padx=10, pady=5)
        
        # Discount calculator
        ctk.CTkButton(
            main_frame,
            text="🧮 Calculate Discount Price",
            command=self.calculate_discount,
            width=180
        ).grid(row=5, column=1, sticky="w", padx=10, pady=5)
        
        # Info label
        ctk.CTkLabel(
            main_frame,
            text="Note: Changes to Capital products are saved locally only.\nSync with Capital ERP system separately.",
            text_color="gray",
            wraplength=400
        ).grid(row=6, column=0, columnspan=2, padx=10, pady=20)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="💾 Save Changes",
            command=self.save_changes,
            fg_color="green"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="❌ Cancel",
            command=self.destroy,
            fg_color="gray"
        ).pack(side="right", padx=10)
        
    def calculate_discount(self):
        """Calculate discounted price based on percentage"""
        try:
            retail = float(self.rtlprice_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid retail price")
            return
            
        discount = ctk.CTkInputDialog(
            text="Enter discount percentage:",
            title="Calculate Discount"
        ).get_input()
        
        if discount:
            try:
                discount_pct = float(discount)
                discounted_price = retail * (1 - discount_pct / 100)
                messagebox.showinfo("Discounted Price", f"Price after {discount_pct}% discount: €{discounted_price:.2f}")
            except ValueError:
                messagebox.showerror("Error", "Invalid discount percentage")
                
    def save_changes(self):
        """Save changes to local database"""
        try:
            # Update product data
            self.product['CODE'] = self.code_entry.get().strip()
            self.product['NAME'] = self.name_entry.get().strip()
            self.product['DESCR'] = self.descr_text.get("1.0", "end").strip()
            
            rtlprice = self.rtlprice_entry.get().strip()
            if rtlprice:
                self.product['RTLPRICE'] = float(rtlprice)
                
            whlprice = self.whlprice_entry.get().strip()
            if whlprice:
                self.product['WHLPRICE'] = float(whlprice)
            
            # Save to database (implement as needed)
            # self.db.update_capital_product(self.product)
            
            messagebox.showinfo("Success", "Product updated locally!")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update: {str(e)}")


