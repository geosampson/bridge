# BRIDGE - Quick Reference Guide

## 🚀 Common Tasks

### View All Unmatched Products

**Problem:** You have 978 unmatched WooCommerce products and 37,141 unmatched Capital products.

**Solution:**
1. Click **"📥 Fetch All Data"** button (if not already fetched)
2. Go to **"🔗 Unmatched"** tab
3. All products will be displayed automatically in tree views
4. Use search fields to filter by SKU/CODE or name

**Note:** No limit - all unmatched products are shown!

---

### Apply Discount to All Price Mismatches

**Scenario:** You want to apply a 15% discount to all products with price mismatches.

**Steps:**
1. Go to **"💰 Prices & Discounts"** tab
2. Ensure "Show only price mismatches" is checked ✓
3. Click the **☑** checkbox in the header to select all
4. Enter **15** in "Set Discount (%)" field
5. Click **"🏷️ Apply Discount"**
6. Confirm the update

**Result:** All mismatched products now have 15% discount applied.

---

### Sync All Products from a Brand to Capital Prices

**Scenario:** You want to sync all "3M" brand products to Capital prices.

**Steps:**
1. Go to **"📦 Products"** tab
2. Select **"3M"** from the "Brand:" dropdown
3. Click **"🔍 Filter"**
4. In "Group Update" panel, click **"🔄 Sync to Capital Prices"**
5. Confirm the update

**Result:** All 3M products now match Capital ERP prices.

---

### Apply 20% Discount to a Specific Brand

**Scenario:** You want to apply 20% discount to all "ABICOR BINZEL" products.

**Steps:**
1. Go to **"📦 Products"** tab
2. Select **"ABICOR BINZEL"** from "Brand:" dropdown
3. Click **"🔍 Filter"**
4. Enter **20** in "Set Discount (%)" field
5. Click **"🏷️ Apply Discount"**
6. Confirm the update

**Result:** All ABICOR BINZEL products have 20% discount.

---

### Update Specific Products to Capital Prices

**Scenario:** You want to update only certain products (not all mismatches).

**Steps:**
1. Go to **"💰 Prices & Discounts"** tab
2. Uncheck "Show only price mismatches" to see all products
3. Use search to filter products
4. **Click and drag** down the checkbox column to select multiple products
5. Click **"📥 Update Checked to Capital Price"**
6. Confirm the update

**Result:** Only selected products are updated.

---

### Find and Match Unmatched Products

**Scenario:** You want to find a specific unmatched product by code.

**Steps:**
1. Go to **"🔗 Unmatched"** tab
2. Type the SKU or product name in "Search WooCommerce:" field
3. Type the CODE or product name in "Search Capital:" field
4. Products filter in real-time as you type
5. Select one product from each side
6. Click **"🔗 Match Selected Products"**

**Result:** Products are matched (manual matching workflow to be implemented).

---

## 🎯 Feature Comparison

### Products Tab vs Prices & Discounts Tab

| Feature | Products Tab | Prices & Discounts Tab |
|---------|-------------|----------------------|
| **Filter by Brand** | ✅ Yes | ❌ No |
| **Filter by Name/SKU** | ✅ Yes | ✅ Yes (Search) |
| **Show Only Mismatches** | ❌ No | ✅ Yes |
| **Checkbox Selection** | ❌ No | ✅ Yes |
| **Click-and-Drag Select** | ❌ No | ✅ Yes |
| **Group Set Price** | ✅ Yes (filtered) | ❌ No |
| **Group Set Discount** | ✅ Yes (filtered) | ✅ Yes (checked) |
| **Sync to Capital** | ✅ Yes (filtered) | ✅ Yes (checked) |

**When to use Products Tab:**
- Filter by brand and apply bulk updates
- Set fixed prices for entire brands
- Work with filtered product groups

**When to use Prices & Discounts Tab:**
- Focus on price mismatches only
- Select specific products with checkboxes
- Quick drag-to-select for many products

---

## 💡 Tips & Tricks

### Rapid Selection with Drag

1. Go to Prices & Discounts tab
2. Click on the first checkbox you want to select
3. **Hold the mouse button** and **drag down**
4. Release when you've selected all desired products
5. Much faster than clicking each checkbox!

### Select All Mismatches

1. Go to Prices & Discounts tab
2. Ensure "Show only price mismatches" is checked
3. Click the **☑** in the checkbox column header
4. All visible products are now selected

### Brand-Specific Discount Campaign

1. Products tab → Select brand → Filter
2. Enter discount percentage
3. Click "Apply Discount"
4. Done! Entire brand has the discount

### Search Unmatched Products

- Type as you search - filtering is instant
- Search works on both SKU/CODE and product name
- Clear button resets both search fields
- No need to press Enter

---

## ⚠️ Important Notes

### About Brands

- Brands are **parent categories only** (not subcategories)
- Based on your WooCommerce category structure
- If a product doesn't show in brand filter, check its category hierarchy

### About Unmatched Products

- **978 WooCommerce products** don't have a Capital match
- **37,141 Capital products** aren't in WooCommerce
- All products are now visible (no 100-item limit)
- Use search to find specific products quickly

### About Updates

- All updates require confirmation
- Updates are batched (50 products at a time)
- Progress bar shows update status
- Local cache updates immediately (no re-fetch needed)

### About Variations

- Product variations (colors, sizes) are automatically fetched
- Each variation appears as a separate product
- Variations have their own SKU
- Can be updated independently

---

## 🔄 Workflow Examples

### Weekly Price Sync Workflow

1. **Monday:** Fetch all data
2. **Tuesday:** Check price mismatches (Prices tab)
3. **Wednesday:** Sync mismatches to Capital (click header → Sync)
4. **Thursday:** Apply promotional discounts by brand (Products tab)
5. **Friday:** Review and adjust individual products

### New Brand Setup Workflow

1. Filter by new brand (Products tab)
2. Review all products in the brand
3. Sync all to Capital prices
4. Apply brand-specific discount if needed
5. Verify in Prices & Discounts tab

### Seasonal Discount Campaign

1. Products tab → Select brand
2. Filter products
3. Apply seasonal discount (e.g., 25%)
4. Repeat for other brands
5. Monitor in Prices & Discounts tab

---

## 📞 Need Help?

- Check the **README.md** for detailed feature descriptions
- Review **CHANGELOG.md** for version history
- See **IMPROVEMENTS_SUMMARY.md** for technical details

**Repository:** https://github.com/geosampson/bridge
