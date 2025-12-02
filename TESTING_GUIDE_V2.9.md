# Testing Guide for Version 2.9 - Variation Fix

## Quick Start Testing

### Prerequisites
1. Pull latest code from GitHub: `git pull origin master`
2. Launch BRIDGE application
3. Enter your WooCommerce and Capital credentials

### Test 1: Verify Variation Detection (2 minutes)

**Purpose**: Confirm variations are being fetched with parent_id

1. ✅ Check "Fetch Variations" checkbox
2. Click "🔄 Fetch Data"
3. Wait for fetch to complete
4. Go to **Logs** tab
5. Look for messages like:
   ```
   Fetching product variations in parallel...
   Fetched X variations for Y variable products
   ```

### Test 2: Update a Single Variation (3 minutes)

**Purpose**: Verify variation updates persist in WooCommerce

**Test with GVS brand products** (known variations):
1. Go to **Products** tab
2. Filter by brand: Select "GVS" from dropdown
3. You should see products like HD9Y, HVSTEYL, GATHEBNXL
4. Check one product (e.g., HD9Y)
5. Enter a test price in "Set Price" field (e.g., 25.00)
6. Click "💰 Set Price"
7. Wait for "Successfully updated" message
8. **Go to Logs tab** and verify you see:
   ```
   [DEBUG] Updating variation {id} of parent {parent_id}
   [SUCCESS] Updated product/variation {id}
   ```
9. **Important**: After update completes, the app will auto-refresh
10. Verify the new price is still showing (not reverted)

**Expected Result**: ✅ Price persists after refresh

### Test 3: Apply Discount to Variations (3 minutes)

**Purpose**: Verify discount calculations work for variations

1. Still in **Products** tab with GVS brand
2. Check 2-3 products
3. Enter discount percentage (e.g., 10)
4. Click "% Apply Discount"
5. Check logs for:
   ```
   Applying 10% discount to {sku}: sale_price={calculated_price}
   [DEBUG] Updating variation {id} of parent {parent_id}
   ```
6. After auto-refresh, verify:
   - Discount column shows "10.0%"
   - Sale price is 10% less than regular price

**Expected Result**: ✅ Discounts persist and calculate correctly

### Test 4: Sync to Capital Prices (3 minutes)

**Purpose**: Verify Capital price sync works for variations

1. Go to **Products** tab
2. Filter by brand: GVS
3. Check products where Capital price differs from WooCommerce
4. Click "⬅️ Sync to Capital Prices"
5. Confirm the operation
6. Check logs for:
   ```
   Syncing {sku}: regular_price={capital_price}
   [DEBUG] Updating variation {id} of parent {parent_id}
   ```
7. After auto-refresh, verify prices match Capital

**Expected Result**: ✅ Prices sync correctly and persist

### Test 5: Mixed Batch Update (5 minutes)

**Purpose**: Verify updates work for both regular products and variations

1. Go to **Products** tab
2. Clear brand filter (show all products)
3. Check 5-10 products (mix of regular and variations)
4. Apply a group price update or discount
5. Check logs to see both types of updates:
   ```
   [DEBUG] Updating product {id}           <- Regular product
   [DEBUG] Updating variation {id} of parent {parent_id}  <- Variation
   ```
6. Verify all updates persist after refresh

**Expected Result**: ✅ Both product types update successfully

## Troubleshooting

### Issue: "Fetch Variations" checkbox not visible
**Solution**: Scroll down in the Fetch Data section - it's below the credentials

### Issue: No variations showing after fetch
**Possible causes**:
1. "Fetch Variations" was not checked
2. No variable products in WooCommerce
3. Variable products have no variations defined

**Solution**: 
- Ensure checkbox is checked before fetching
- Verify in WooCommerce admin that products have variations

### Issue: Updates still reverting
**Check logs for**:
1. Error messages about invalid product ID
2. Authentication failures
3. Network timeouts

**Solutions**:
1. Verify WooCommerce API credentials
2. Check WooCommerce API permissions (read/write)
3. Ensure WooCommerce REST API is enabled

### Issue: "parent_id" showing in error messages
**This is normal** - The logs will show parent_id for debugging. If you see errors, check:
1. Is the parent product still in WooCommerce?
2. Does the variation still exist?
3. Has the variation been deleted from WooCommerce?

## Success Indicators

✅ **Logs show correct endpoints**:
- Regular products: "Updating product {id}"
- Variations: "Updating variation {id} of parent {parent_id}"

✅ **Updates persist after refresh**:
- Prices don't revert to original values
- Discounts remain applied
- Capital sync stays synchronized

✅ **No API errors in logs**:
- No "invalid_product_id" errors
- No "must use variations endpoint" errors
- Success messages for all updates

## Performance Notes

- **Without variations**: ~8 minutes fetch time
- **With variations**: ~15 minutes fetch time (depends on number of variable products)
- **Updates**: Same speed for both regular products and variations
- **Batch operations**: Process 50 products at a time

## What Changed in v2.9

### Technical Changes
- Added `parent_id` field throughout data flow
- Modified 8 update functions to include parent_id
- Enhanced ProductMatcher to preserve parent_id
- Improved logging to show endpoint types

### User-Visible Changes
- **None** - The fix is transparent to users
- Updates now work correctly for variations
- No UI changes required
- No configuration changes needed

## Next Steps After Testing

1. ✅ If all tests pass: Use normally for production work
2. ❌ If any test fails: Check logs and report issue with:
   - Exact steps to reproduce
   - Log excerpts showing the error
   - Product SKU that failed
   - Whether it's a variation or regular product

## Quick Reference: Variation vs Regular Product

| Feature | Regular Product | Product Variation |
|---------|----------------|-------------------|
| Has parent_id | No (None) | Yes (parent product ID) |
| API endpoint | /products/{id} | /products/{parent_id}/variations/{id} |
| In logs | "Updating product {id}" | "Updating variation {id} of parent {parent_id}" |
| Categories | Own categories | Inherits from parent |
| Attributes | Optional | Required (color, size, etc.) |

---

**Version**: 2.9  
**Testing Time**: ~15 minutes for full suite  
**Critical Test**: Test 2 (single variation update)
