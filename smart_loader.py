"""
Smart Data Loader for BRIDGE
Loads cached data immediately, fetches fresh data in background
"""

import threading
import time


class SmartDataLoader:
    """Manages intelligent data loading with cache and background fetch"""
    
    def __init__(self, woo_client, capital_client, database, data_store):
        self.woo_client = woo_client
        self.capital_client = capital_client
        self.database = database
        self.data_store = data_store
        self.background_thread = None
        self.on_complete_callback = None
    
    def load_on_startup(self, on_complete=None, log_callback=None):
        """
        Load data on startup:
        1. Load WooCommerce from cache (instant)
        2. Fetch Capital in foreground (fast, ~10 sec)
        3. Apply saved matches
        4. Fetch WooCommerce in background (optional)
        """
        self.on_complete_callback = on_complete
        self.log_callback = log_callback
        
        def log(message):
            """Helper to log to both console and UI"""
            print(message)
            if self.log_callback:
                self.log_callback(message)
        
        try:
            # Phase 1: Load WooCommerce from cache
            log("Loading WooCommerce from cache...")
            self.data_store.set_loading(True, 10, "Loading WooCommerce from cache...")
            
            try:
                cached_woo, cache_time = self.database.get_cached_woo_products()
                
                if cached_woo:
                    self.data_store.woo_products = cached_woo
                    log(f"✓ Loaded {len(cached_woo)} WooCommerce products from cache")
                    self.data_store.set_loading(True, 30, f"Loaded {len(cached_woo)} products from cache")
                else:
                    log("No WooCommerce cache found - will fetch fresh data")
                    self.data_store.set_loading(True, 30, "No cache - click 'Fetch All Data'")
            except Exception as e:
                log(f"Error loading cache: {e}")
                cached_woo = []
            
            # Phase 2: Fetch Capital data (foreground, fast)
            log("Fetching Capital data...")
            self.data_store.set_loading(True, 40, "Fetching Capital products...")
            
            try:
                self.data_store.capital_products = self.capital_client.get_all_products()
                log(f"✓ Fetched {len(self.data_store.capital_products)} Capital products")
                
                # Cache Capital data
                self.database.cache_capital_products(self.data_store.capital_products)
                
                self.data_store.set_loading(True, 70, "Capital data loaded")
            except Exception as e:
                log(f"Error fetching Capital data: {e}")
                self.data_store.set_loading(False, 0, f"Error: {str(e)}")
                if self.on_complete_callback:
                    self.on_complete_callback()
                return
            
            # Phase 3: Apply saved matches
            log("Applying saved matches...")
            self.data_store.set_loading(True, 80, "Applying saved product matches...")
            
            try:
                saved_matches = self.database.get_all_matches()
                matches_applied = 0
                
                for capital_sku, woo_id, woo_sku, match_type, confidence, matched_at, matched_by in saved_matches:
                    # Find products and apply match
                    for cap_product in self.data_store.capital_products:
                        if cap_product.get('sku') == capital_sku:
                            for woo_product in self.data_store.woo_products:
                                if woo_product.get('id') == woo_id:
                                    # Update WooCommerce SKU to match
                                    woo_product['sku'] = capital_sku
                                    matches_applied += 1
                                    break
                            break
                
                log(f"✓ Applied {matches_applied} saved matches")
            except Exception as e:
                log(f"Error applying matches: {e}")
            
            # Phase 4: Match products
            log("Matching products...")
            self.data_store.set_loading(True, 90, "Matching products...")
            
            try:
                self.data_store.match_products()
                log("✓ Product matching complete")
            except Exception as e:
                log(f"Error matching products: {e}")
            
            # Phase 5: Done!
            self.data_store.set_loading(False, 100, "Ready")
            log("✓ Startup complete - ready to use!")
            
            if self.on_complete_callback:
                self.on_complete_callback()
            
            # Phase 6: Start background fetch of WooCommerce (optional, doesn't block)
            if cached_woo:  # Only if we used cache
                log("Starting background fetch of WooCommerce data...")
                self.background_thread = threading.Thread(
                    target=self._background_fetch_woo, 
                    daemon=True
                )
                self.background_thread.start()
                
        except Exception as e:
            log(f"FATAL ERROR in startup: {e}")
            import traceback
            traceback.print_exc()
            self.data_store.set_loading(False, 0, f"Error: {str(e)}")
            if self.on_complete_callback:
                self.on_complete_callback()
    
    def _background_fetch_woo(self):
        """Fetch WooCommerce data in background"""
        try:
            time.sleep(2)  # Give user time to start working
            
            print("Background: Fetching fresh WooCommerce data...")
            fresh_woo = self.woo_client.get_all_products()
            
            print(f"Background: Fetched {len(fresh_woo)} WooCommerce products")
            
            # Update cache
            self.database.cache_woo_products(fresh_woo)
            
            # Update data store
            self.data_store.woo_products = fresh_woo
            
            # Re-match
            self.data_store.match_products()
            
            print("✓ Background fetch complete - data refreshed")
            
            # Notify UI
            if self.on_complete_callback:
                self.on_complete_callback(background=True)
                
        except Exception as e:
            print(f"Background fetch error: {e}")
    
    def fetch_fresh_data(self, fetch_woo=True, fetch_capital=True, on_complete=None):
        """
        Fetch fresh data from APIs (manual refresh)
        
        Args:
            fetch_woo: Fetch WooCommerce data
            fetch_capital: Fetch Capital data
            on_complete: Callback when complete
        """
        def _fetch():
            try:
                if fetch_woo:
                    self.data_store.set_loading(True, 20, "Fetching WooCommerce...")
                    self.data_store.woo_products = self.woo_client.get_all_products()
                    self.database.cache_woo_products(self.data_store.woo_products)
                    print(f"✓ Fetched {len(self.data_store.woo_products)} WooCommerce products")
                
                if fetch_capital:
                    self.data_store.set_loading(True, 60, "Fetching Capital...")
                    self.data_store.capital_products = self.capital_client.get_all_products()
                    self.database.cache_capital_products(self.data_store.capital_products)
                    print(f"✓ Fetched {len(self.data_store.capital_products)} Capital products")
                
                self.data_store.set_loading(True, 90, "Matching products...")
                self.data_store.match_products()
                
                self.data_store.set_loading(False, 100, "Ready")
                
                if on_complete:
                    on_complete()
                    
            except Exception as e:
                print(f"Error fetching data: {e}")
                self.data_store.set_loading(False, 0, f"Error: {str(e)}")
        
        threading.Thread(target=_fetch, daemon=True).start()
