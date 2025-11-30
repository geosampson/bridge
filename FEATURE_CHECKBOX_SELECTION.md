# Feature: Checkbox Selection in Products Tab

## 🎉 New Feature - Version 2.6

You can now **select specific products** in the Products tab using checkboxes, giving you full control over which products to update!

---

## ✨ What's New

### Checkbox Column Added
- **☑ checkbox column** at the start of the Products table
- Click any checkbox to select/deselect individual products
- Click the **header checkbox (☑)** to select/deselect ALL products
- **Selection counter** shows how many products are selected

### Group Updates Now Use Checkboxes
All group update functions now work on **checked products only**:
- ✅ **Set Price** - Update only checked products
- ✅ **Set Discount** - Apply discount only to checked products
- ✅ **Sync to Capital** - Sync only checked products

---

## 🎯 How to Use

### Select Individual Products

**Method 1: Click checkboxes one by one**
```
1. Filter by brand (e.g., "3M")
2. Click checkbox next to product #1 ☑
3. Click checkbox next to product #3 ☑
4. Click checkbox next to product #5 ☑
5. Bottom shows: "Selected: 3 products"
6. Apply group update → Only those 3 products updated!
```

### Select All Products

**Method 2: Select all filtered products**
```
1. Filter by brand (e.g., "3M") → 7 products shown
2. Click header checkbox ☑ → All 7 selected
3. Bottom shows: "Selected: 7 products"
4. Apply group update → All 7 products updated!
```

### Select Range (Future Enhancement)
Currently, click individual checkboxes. In a future version, you'll be able to:
- Click first checkbox
- Hold Shift + click last checkbox
- All checkboxes in between selected

---

## 💡 Workflow Examples

### Example 1: Update Specific Products

**Scenario:** You want to update only 3 out of 10 products in a brand

```
1. Products tab → Filter by "ALFAGOMMA"
2. 10 products shown
3. Check products #2, #5, #8 (click their checkboxes)
4. Selected: 3 products
5. Enter price: 45.99
6. Click "💰 Update Prices"
7. Confirm → Only 3 products updated!
8. Other 7 products unchanged ✅
```

### Example 2: Apply Discount to Half

**Scenario:** Apply 20% discount to some products, not all

```
1. Products tab → Filter by "3M"
2. 14 products shown
3. Check first 7 products (click checkboxes)
4. Selected: 7 products
5. Enter discount: 20
6. Click "🏷️ Apply Discount"
7. Confirm → Only 7 products get discount!
8. Other 7 keep regular prices ✅
```

### Example 3: Sync Selected to Capital

**Scenario:** Sync only products that need price updates

```
1. Products tab → Filter by brand
2. Review products
3. Check only products with wrong prices
4. Selected: 5 products
5. Click "🔄 Sync to Capital"
6. Confirm → Only 5 products synced!
7. Others keep current prices ✅
```

### Example 4: Select All Then Deselect Some

**Scenario:** Update all except a few products

```
1. Products tab → Filter by "AMPCO"
2. 8 products shown
3. Click header ☑ → All 8 selected
4. Click checkbox on product #3 → Deselected
5. Click checkbox on product #6 → Deselected
6. Selected: 6 products (all except #3 and #6)
7. Apply update → 6 products updated!
```

---

## 🔧 Features

### Checkbox Behavior

✅ **Individual selection** - Click any checkbox  
✅ **Select all** - Click header checkbox  
✅ **Deselect all** - Click header checkbox again  
✅ **Selection counter** - Always shows count  
✅ **Persistent across filters** - Checkboxes reset when you filter  
✅ **Visual feedback** - ☑ (checked) vs ☐ (unchecked)  

### Group Update Functions

All three group update functions now require checkboxes:

**1. 💰 Update Prices**
- Enter price (e.g., 29.99)
- Click button
- Only **checked products** updated
- Warning if no products checked

**2. 🏷️ Apply Discount**
- Enter discount % (e.g., 15)
- Click button
- Only **checked products** get discount
- Warning if no products checked

**3. 🔄 Sync to Capital**
- Click button
- Only **checked products** synced
- Warning if no products checked

### Selection Counter

Bottom of Products tab shows:
- **"Select products to edit"** - When nothing checked
- **"Selected: 5 products"** - When 5 products checked
- Updates in real-time as you check/uncheck

---

## ⚙️ Technical Details

### Checkbox Column

- **Position:** First column (leftmost)
- **Width:** 30 pixels
- **Header:** ☑ (clickable to select/deselect all)
- **Values:** ☑ (checked) or ☐ (unchecked)
- **Behavior:** Click toggles state

### Click Handling

- **Single click on checkbox:** Toggle that checkbox
- **Single click on header:** Toggle all checkboxes
- **Double click on row:** Open product editor (not checkbox column)
- **Click on other columns:** No effect (just selection)

### State Management

```python
self.product_checkboxes = {
    "item_id_1": True,   # Checked
    "item_id_2": False,  # Unchecked
    "item_id_3": True,   # Checked
    ...
}
```

- Dictionary tracks checkbox state for each product
- Updated when checkbox clicked
- Cleared when filters change
- Used by group update functions

---

## 📊 Comparison

### Before (Version 2.5)

| Action | Behavior |
|--------|----------|
| Filter by brand | Shows all products |
| Group update | Updates **ALL** filtered products |
| Individual selection | Not possible |
| Partial updates | Not possible |

**Problem:** All-or-nothing updates only!

### After (Version 2.6)

| Action | Behavior |
|--------|----------|
| Filter by brand | Shows all products with checkboxes |
| Check specific products | Select only what you want |
| Group update | Updates **ONLY** checked products |
| Individual selection | ✅ Fully supported |
| Partial updates | ✅ Fully supported |

**Solution:** Full control over which products to update!

---

## 🎯 Use Cases

### When to Use Checkboxes

✅ **Update specific products** - Not all in a brand  
✅ **Test updates** - Try on a few products first  
✅ **Partial discounts** - Some products on sale, others not  
✅ **Selective sync** - Only sync products that need it  
✅ **Review before update** - Check exactly what will change  

### When to Select All

✅ **Standardize pricing** - All products in brand  
✅ **Brand-wide discount** - Apply to entire brand  
✅ **Full sync** - Sync all products to Capital  
✅ **Bulk updates** - When you want everything updated  

---

## ⚠️ Important Notes

### Checkboxes Reset When Filtering

When you change filters:
- All checkboxes are **unchecked**
- Selection counter resets to 0
- You need to check products again

**Why?** Different filter = different products shown!

### Must Check Products Before Update

If you try to update without checking any products:
- **Warning:** "Please check products to update"
- No update happens
- Check at least one product first

### Double-Click Still Opens Editor

- **Single click checkbox:** Toggle checkbox
- **Double click row:** Open product editor
- **Double click checkbox:** Doesn't open editor

---

## 🚀 Workflow Tips

### Tip 1: Filter First, Then Select

```
1. Filter by brand/SKU/name
2. Review filtered products
3. Check the ones you want to update
4. Apply group update
```

### Tip 2: Use Select All as Starting Point

```
1. Filter products
2. Click header ☑ to select all
3. Uncheck the ones you DON'T want
4. Apply update to the rest
```

### Tip 3: Check Selection Count

Always verify the count before updating:
- **"Selected: 5 products"** - Looks right?
- If not, adjust checkboxes
- Then proceed with update

### Tip 4: Test on One Product First

```
1. Filter products
2. Check ONLY one product
3. Apply update
4. Verify it worked
5. Then check more products
```

---

## 🔄 Integration with Other Features

### Works With All Filters

Checkboxes work with:
- ✅ Brand filter
- ✅ SKU filter
- ✅ Name filter
- ✅ Combined filters

### Works With All Updates

Checkboxes work with:
- ✅ Set Price
- ✅ Apply Discount
- ✅ Sync to Capital

### Works With Auto-Refresh

After group update:
- ✅ Products table refreshes
- ✅ Checkboxes preserved
- ✅ Selection count maintained
- ✅ Updated prices shown

---

## 📋 Quick Reference

### Keyboard Shortcuts

Currently none - use mouse to click checkboxes.

**Future enhancement:** Space bar to toggle selected row's checkbox.

### Mouse Actions

| Action | Result |
|--------|--------|
| Click checkbox | Toggle that checkbox |
| Click header ☑ | Toggle all checkboxes |
| Double-click row | Open product editor |
| Click other columns | Select row (no checkbox change) |

---

## 🎉 Summary

**Version 2.6 gives you full control over product selection!**

✅ **Checkbox column** in Products tab  
✅ **Individual selection** - Click to check/uncheck  
✅ **Select all** - Click header checkbox  
✅ **Selection counter** - Always know how many selected  
✅ **Group updates** - Only affect checked products  
✅ **Full flexibility** - Update 1, some, or all products  

**No more all-or-nothing updates - you're in control!** 🎯

---

**Version:** 2.6  
**Date:** November 30, 2025  
**Feature:** Checkbox selection in Products tab  
**Status:** ✅ ACTIVE  
**Repository:** https://github.com/geosampson/bridge
