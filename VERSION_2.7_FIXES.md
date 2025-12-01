# Version 2.7 - Critical Fixes

## 🐛 Bugs Fixed

### 1. **Checkbox Accumulation Bug** ✅ FIXED

**Problem:** Checkboxes accumulated when filtering products multiple times. If you checked 7 products, then filtered again and checked the same 7, it would say "36 checked products" instead of 7.

**Root Cause:** Checkbox state dictionary (`product_checkboxes`) was not being cleared when filtering, so old checkbox states persisted.

**Fix:** Clear `product_checkboxes` dictionary every time `filter_products()` is called.

**Code Change:**
```python
def filter_products(self):
    # Clear current items
    for item in self.products_tree.get_children():
        self.products_tree.delete(item)
    
    # Clear checkbox state to prevent accumulation
    self.product_checkboxes.clear()  # ← NEW
```

**Result:** Now when you filter products, all checkboxes reset to unchecked state. No more accumulation!

---

### 2. **Discount Preservation When Syncing to Capital** ✅ FIXED

**Problem:** When syncing products to Capital prices, the sale_price (offer price) was being cleared, which removed all discounts. This meant:
- Regular price updated correctly ✅
- Sale price cleared ❌
- Discount disappeared ❌

**User Expectation:** When syncing to Capital prices, the discount percentage should be preserved by recalculating the sale_price based on the new regular_price.

**Example:**
```
Before sync:
- Regular price: €30.00
- Sale price: €25.50
- Discount: 15%

Old behavior (broken):
- Regular price: €35.00 (updated)
- Sale price: cleared
- Discount: 0% (lost!)

New behavior (fixed):
- Regular price: €35.00 (updated)
- Sale price: €29.75 (recalculated: €35 × 0.85)
- Discount: 15% (preserved!)
```

**Fix:** Calculate new sale_price to preserve discount percentage when syncing to Capital prices.

**Code Changes:**
```python
# Get current discount percentage
current_discount = product.get('discount', 0)

# Format new regular price
new_regular_price = float(capital_price)
price_str = f"{new_regular_price:.2f}"

# Calculate new sale price to preserve discount percentage
if current_discount and current_discount > 0:
    discount_multiplier = (100 - float(current_discount)) / 100
    new_sale_price = new_regular_price * discount_multiplier
    sale_price_str = f"{new_sale_price:.2f}"
    updates.append({
        "id": product['woo_id'],
        "regular_price": price_str,
        "sale_price": sale_price_str  # ← Preserved discount
    })
    self.log(f"Syncing {sku}: regular_price={price_str}, sale_price={sale_price_str} ({current_discount}% discount preserved)")
else:
    # No discount, just update regular price and clear sale price
    updates.append({
        "id": product['woo_id'],
        "regular_price": price_str,
        "sale_price": ""
    })
    self.log(f"Syncing {sku}: regular_price={price_str} (no discount)")
```

**Result:** Discounts are now preserved when syncing to Capital prices!

---

### 3. **Refresh Products from WooCommerce After Updates** ✅ FIXED

**Problem:** After updating prices/discounts, the displayed values in BRIDGE were based on local cache updates, not the actual values in WooCommerce. Sometimes WooCommerce would round prices or apply additional logic, so the displayed values didn't match reality.

**User Expectation:** After updating products, BRIDGE should show the actual values from WooCommerce, not just what it thinks was updated.

**Fix:** After batch updates complete, fetch the updated products from WooCommerce API and refresh the local cache with actual values.

**Code Changes:**

**New method added:**
```python
def refresh_from_woocommerce(self, updates):
    """Refresh specific products from WooCommerce after updates"""
    try:
        product_ids = [update['id'] for update in updates]
        for product_id in product_ids:
            try:
                # Fetch updated product from WooCommerce
                response = requests.get(
                    f"{WOOCOMMERCE_CONFIG['store_url']}/wp-json/wc/v3/products/{product_id}",
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
```

**New DataStore method added:**
```python
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
            
            # Recalculate discount
            regular_price = self.matched_products[i]['woo_regular_price']
            sale_price = self.matched_products[i]['woo_sale_price']
            if regular_price and sale_price and sale_price < regular_price:
                discount = ((regular_price - sale_price) / regular_price) * 100
                self.matched_products[i]['discount'] = round(discount, 2)
            else:
                self.matched_products[i]['discount'] = 0
            break
    
    self.notify_data_changed()
```

**Updated batch_update_prices:**
```python
data_store.set_loading(False, 100, "Update complete!")

# Refresh products from WooCommerce to get actual updated values
self.log("Refreshing products from WooCommerce...")
self.refresh_from_woocommerce(updates)  # ← NEW

# Refresh both Products and Prices tables
self.after(0, self.refresh_products_table)
self.after(0, self.refresh_prices_table)
self.after(100, lambda: messagebox.showinfo("Success", f"Successfully updated {len(updates)} products!"))
```

**Result:** After updates, BRIDGE now shows the actual values from WooCommerce, not just cached estimates!

---

## 📊 Impact Summary

| Issue | Before | After |
|-------|--------|-------|
| **Checkbox accumulation** | Checking 7 products 5 times = "35 checked" ❌ | Checking 7 products always = "7 checked" ✅ |
| **Sync to Capital** | Discount lost when syncing ❌ | Discount preserved when syncing ✅ |
| **Price display** | Shows cached values (may be wrong) ❌ | Shows actual WooCommerce values ✅ |

---

## 🎯 User Experience Improvements

### Before (Version 2.6)

**Workflow:**
```
1. Filter by brand "GVS" → 7 products
2. Check all 7 products
3. Apply 25% discount → Success
4. Filter again to review
5. Check same 7 products
6. Sync to Capital prices
7. Dialog says: "Sync 14 checked products?" ❌ (should be 7)
8. After sync, discount is gone ❌
9. Displayed prices may not match WooCommerce ❌
```

### After (Version 2.7)

**Workflow:**
```
1. Filter by brand "GVS" → 7 products
2. Check all 7 products
3. Apply 25% discount → Success
4. Filter again to review
5. Check same 7 products
6. Sync to Capital prices
7. Dialog says: "Sync 7 checked products?" ✅ (correct!)
8. After sync, discount is preserved ✅ (25% maintained)
9. Displayed prices match WooCommerce exactly ✅
```

---

## 🔧 Technical Details

### Checkbox State Management

**Problem:** Dictionary persisted across filter operations.

**Solution:** Clear dictionary on every filter operation.

**Affected Functions:**
- `filter_products()` - Now clears `product_checkboxes`

### Discount Preservation Logic

**Formula:**
```
new_sale_price = new_regular_price × (1 - discount_percentage / 100)
```

**Example:**
```
new_regular_price = €35.00
discount_percentage = 15%
new_sale_price = €35.00 × (1 - 15/100)
               = €35.00 × 0.85
               = €29.75
```

**Affected Functions:**
- `sync_filtered_to_capital()` - Products tab
- `sync_checked_to_capital()` - Prices tab

### WooCommerce Refresh Logic

**Process:**
1. Batch update completes
2. Extract product IDs from updates
3. Fetch each product from WooCommerce API
4. Update local cache with fresh data
5. Recalculate discounts
6. Refresh UI tables

**Performance:**
- Adds ~1-2 seconds for 10 products
- Worth it for accuracy!

**Affected Functions:**
- `batch_update_prices()` - Calls refresh after updates
- `refresh_from_woocommerce()` - NEW - Fetches from API
- `update_woo_product_from_api()` - NEW - Updates cache

---

## ⚠️ Important Notes

### Discount Preservation

**When discount is preserved:**
- ✅ Product has existing discount (sale_price < regular_price)
- ✅ Syncing to Capital prices
- ✅ New regular_price is set
- ✅ New sale_price calculated to maintain same discount %

**When discount is cleared:**
- ❌ Product has no discount (sale_price empty or equal to regular_price)
- ❌ Syncing to Capital prices
- ❌ New regular_price is set
- ❌ Sale_price is cleared (no discount to preserve)

### Checkbox Reset Behavior

**Checkboxes reset when:**
- ✅ Filtering products (any filter change)
- ✅ Clearing filters
- ✅ Changing brand selection
- ✅ Searching by SKU/name

**Checkboxes preserved when:**
- ❌ Never (always reset on filter change)

**Why?** Different filter = different products shown = checkboxes should reset for clarity.

### WooCommerce Refresh

**When refresh happens:**
- ✅ After batch price updates
- ✅ After batch discount updates
- ✅ After sync to Capital prices

**What gets refreshed:**
- ✅ Regular price
- ✅ Sale price
- ✅ Product name
- ✅ Descriptions
- ✅ Discount percentage (recalculated)

**What doesn't get refreshed:**
- ❌ Capital ERP data (only WooCommerce data)
- ❌ Stock levels (not part of price updates)
- ❌ Categories (not part of price updates)

---

## 🧪 Testing Checklist

### Test 1: Checkbox Accumulation

- [x] Filter by brand
- [x] Check 5 products
- [x] Count shows "Selected: 5 products" ✅
- [x] Filter again (same brand)
- [x] Check same 5 products
- [x] Count shows "Selected: 5 products" ✅ (not 10!)

### Test 2: Discount Preservation

- [x] Filter products with 25% discount
- [x] Check products
- [x] Sync to Capital prices
- [x] Verify discount still shows 25% ✅
- [x] Verify sale_price = regular_price × 0.75 ✅

### Test 3: WooCommerce Refresh

- [x] Update product prices
- [x] Wait for "Update complete!"
- [x] Check logs for "Refreshing products from WooCommerce..."
- [x] Verify displayed prices match WooCommerce exactly ✅

---

## 📋 Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | Nov 28 | Initial release |
| 2.1 | Nov 29 | Unmatched products visible |
| 2.2 | Nov 29 | Brand filter + editors |
| 2.3 | Nov 29 | Performance optimization (6x faster) |
| 2.4 | Nov 29 | Auto-refresh after updates |
| 2.5 | Nov 29 | Sync to Capital fix |
| 2.6 | Nov 30 | Checkbox selection in Products tab |
| **2.7** | **Nov 30** | **Checkbox accumulation fix, discount preservation, WooCommerce refresh** |

---

## 🎉 Summary

**Version 2.7 fixes three critical bugs that were causing:**
1. ❌ Incorrect checkbox counts
2. ❌ Lost discounts when syncing prices
3. ❌ Inaccurate price displays

**All fixed!** ✅

**Your BRIDGE is now:**
- ✅ Accurate (shows real WooCommerce values)
- ✅ Reliable (checkboxes work correctly)
- ✅ Smart (preserves discounts when syncing)

---

**Version:** 2.7  
**Date:** November 30, 2025  
**Status:** ✅ TESTED AND DEPLOYED  
**Repository:** https://github.com/geosampson/bridge
