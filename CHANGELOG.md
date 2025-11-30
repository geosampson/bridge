# BRIDGE - Changelog

## Version 2.1 - Bug Fixes & Enhancements (2025-11-30)

### 🐛 Bug Fixes

#### Unmatched Products Display
- **Fixed:** Unmatched products now display properly in the tree views
- **Fixed:** All unmatched products (not just first 100) are now shown
- Changed from old listbox implementation to new tree view with search
- Unmatched products automatically populate when data is fetched

#### Group Update in Prices & Discounts Tab
- **Added:** Group discount update functionality to Prices & Discounts tab
- **Added:** "Sync Checked to Capital" button for bulk price sync
- Now you can apply discounts or sync prices directly from the Prices tab
- Works with checkbox selection for maximum flexibility

### ✨ New Features

#### Prices & Discounts Tab - Group Update Panel
- **Set Discount (%):** Apply percentage discount to all checked products
- **Sync Checked to Capital:** Update all checked products to Capital prices
- Complements the existing "Update Checked to Capital Price" button
- All operations work with checkbox selection and drag-to-select

### 📋 Summary of Changes

**What's Fixed:**
1. Unmatched products tab now shows ALL unmatched products (978 WooCommerce + 37,141 Capital)
2. Search functionality works immediately after data fetch
3. No more manual refresh needed to see unmatched products

**What's Added:**
1. Group discount application in Prices & Discounts tab
2. Sync to Capital button in Prices & Discounts tab
3. Better consistency between Products tab and Prices tab

### 🎯 Usage Examples

#### Apply 20% Discount to Price Mismatches
1. Go to **Prices & Discounts** tab
2. Check "Show only price mismatches" (default)
3. Click checkbox header to select all
4. Enter "20" in "Set Discount (%)" field
5. Click "🏷️ Apply Discount"
6. Confirm → All mismatched products now have 20% discount

#### Sync All Mismatched Prices to Capital
1. Go to **Prices & Discounts** tab
2. Check "Show only price mismatches"
3. Click checkbox header to select all
4. Click "🔄 Sync Checked to Capital"
5. Confirm → All prices synced!

---

## Version 2.0 - Enhanced Features (2025-11-30)

### 🎯 Major Improvements

#### 1. **Brand-Based Filtering**
- Changed category filter to show only **parent categories (brands)** instead of all categories
- More intuitive filtering by brand rather than subcategories
- Filter label changed from "Category" to "Brand"

#### 2. **Enhanced Price Update Interface**
- ✅ **Checkbox selection** in Prices & Discounts tab
- Click individual checkboxes to select products
- **Click-and-drag** support for rapid multi-selection
- **Select All** button in column header
- No more manual multi-select with Ctrl/Shift keys
- Update multiple products with a single click

#### 3. **Improved Unmatched Products Tab**
- 🔍 **Search/Filter functionality** for both WooCommerce and Capital products
- Real-time filtering as you type
- **SKU/CODE display** in tree view format
- Clear button to reset filters
- Easier to find matching products without scrolling through entire lists

#### 4. **Product Variations Support**
- 🎨 Automatic fetching of **product variations** (colors, sizes, etc.)
- Variable products are expanded to show all variations
- Each variation is treated as a separate product with its own SKU
- Variations include parent product information
- Full support for updating variation prices and discounts

#### 5. **Group Price & Discount Updates**
- 💰 **Bulk price updates** for filtered products
- 🏷️ **Bulk discount application** by percentage
- 🔄 **Sync filtered products to Capital prices** with one click
- Apply changes to entire filtered groups (by brand, name, or SKU)
- Confirmation dialogs prevent accidental updates

### 📋 Detailed Changes

#### Products Tab
- Added "Group Update" panel with three operations:
  - **Set Price**: Apply a fixed price to all filtered products
  - **Set Discount**: Apply a percentage discount to all filtered products
  - **Sync to Capital Prices**: Update all filtered products to match Capital ERP prices

#### Prices & Discounts Tab
- Replaced tree selection with checkbox-based selection
- Added checkbox column (☐/☑) as first column
- Implemented click-and-drag for rapid selection
- Toggle all checkboxes with header click
- Update button now uses checked items instead of selected items

#### Unmatched Products Tab
- Replaced simple listboxes with searchable tree views
- Added search fields for WooCommerce (SKU/Name) and Capital (CODE/Name)
- Real-time filtering on keypress
- Clear filters button
- Both SKU/CODE and product name visible in columns

#### Data Fetching
- Added variation fetching after main product fetch
- Progress indicators for variation fetching
- Variations added to product list with parent reference
- Only variations with SKUs are included

### 🔧 Technical Improvements

- Enhanced `WooCommerceClient` with `get_product_variations()` method
- Added `filter_unmatched_products()` method for search functionality
- Added `get_filtered_products()` helper method
- Added `update_group_prices()`, `update_group_discount()`, and `sync_filtered_to_capital()` methods
- Improved checkbox state tracking with `price_checkboxes` dictionary
- Better event handling for click and drag operations

### 🐛 Bug Fixes

- Fixed column indexing after adding checkbox column
- Improved double-click handling to avoid conflicts with checkbox clicks
- Better error handling for variation fetching

### 📊 Performance

- Variation fetching is batched and shows progress
- Group updates use existing batch update mechanism
- No performance degradation for large product catalogs

---

## Version 1.0 - Initial Release

- WooCommerce and Capital ERP integration
- Product matching by SKU/CODE
- Price comparison and updates
- Basic filtering and search
- Analytics and reporting
- Activity logging
