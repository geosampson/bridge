# WooCommerce Quantity Control for Products Sold in Increments

## 🎯 Your Requirement

**Scenario:** You sell products in 5kg packages, display price per kilo, but customers can only buy in multiples of 5kg (5kg, 10kg, 15kg, etc.).

**Example:**
- Product: Welding Wire
- Package size: 5 kg
- Display price: €10/kg (€50 for 5kg package)
- Customer can buy: 5kg, 10kg, 15kg, 20kg... (NOT 3kg or 7kg)

---

## ✅ Yes, WooCommerce Supports This!

WooCommerce has built-in and plugin solutions for enforcing quantity increments.

---

## 🔧 Solution 1: WooCommerce Min/Max Quantities (Official Plugin)

### What It Does

The **WooCommerce Min/Max Quantities** plugin allows you to set:
- **Minimum quantity** (e.g., must buy at least 5kg)
- **Maximum quantity** (e.g., can't buy more than 100kg)
- **Group of** (quantity step/increment) - **THIS IS WHAT YOU NEED!**

### How It Works

**"Group of" field** = Quantity increment/step

**Example for 5kg increments:**
```
Product: Welding Wire (5kg package)
Minimum Quantity: 1 (= 5kg)
Maximum Quantity: 20 (= 100kg)
Group of: 1 (= must buy in multiples of 1 package = 5kg increments)
```

**Result:**
- Customer can select: 1, 2, 3, 4, 5... packages
- Which equals: 5kg, 10kg, 15kg, 20kg, 25kg...
- Customer CANNOT select: 0.5, 1.5, 2.3 packages

### Configuration Steps

1. **Install the plugin**
   - Go to WooCommerce → Extensions
   - Search "Min/Max Quantities"
   - Purchase and install ($49/year)
   - Or use free alternatives (see below)

2. **Configure per product**
   - Edit the product
   - Go to **Product Data → General** tab
   - Find **Quantity Rules** section
   - Set fields:
     - **Minimum Quantity:** 1 (one 5kg package minimum)
     - **Maximum Quantity:** 20 (or whatever limit you want)
     - **Group of:** 1 (sold in whole packages only)

3. **How customers see it**
   - Quantity selector shows: 1, 2, 3, 4...
   - Cannot enter 0.5 or 1.5
   - If they try to add invalid quantity, they get an error

### Pricing Display

To show "€10/kg" but sell in 5kg packages:

**Option A: Use product title**
```
Product Name: "Welding Wire (5kg package)"
Price: €50.00
Description: "€10.00 per kg"
```

**Option B: Use WooCommerce Price Suffix**
```
Product Name: "Welding Wire"
Price: €50.00
Price Suffix: "per 5kg (€10/kg)"
```

**Option C: Use Product Add-ons or Measurement Price Calculator**
- More complex but shows per-kg pricing automatically
- Requires additional plugin

---

## 🆓 Solution 2: Free Plugins

If you don't want to pay $49/year, there are free alternatives:

### 1. **Min Max Quantity & Step Control for WooCommerce**
- **Link:** https://wordpress.org/plugins/woo-min-max-quantity-step-control-single/
- **Free:** Yes
- **Features:**
  - Set minimum, maximum, and step quantity per product
  - Same functionality as paid plugin
  - Works on product level

### 2. **WPC Product Quantity for WooCommerce**
- **Link:** https://wordpress.org/plugins/wpc-product-quantity/
- **Free:** Yes
- **Features:**
  - Control quantity number
  - Set min/max/step
  - Custom quantity options

### 3. **Min Max Quantities – Set Minimum/Maximum**
- **Link:** https://wordpress.org/plugins/wc-min-max-quantities/
- **Free:** Yes (Premium version available)
- **Features:**
  - Minimum and maximum purchase limits
  - Step control
  - Per product, category, or order

---

## 💡 Recommended Approach for Your Case

### For 5kg Package Products

**Setup:**
```
Product: Welding Wire WELDAS MASKA 44-7111
SKU: 44-7111
Package Size: 5kg
Price per kg: €25.42
Total Price: €127.10 (for 5kg)

WooCommerce Settings:
- Regular Price: 127.10
- Sale Price: (if discounted) 108.04 (30% off)
- Price Suffix: "per 5kg package (€25.42/kg)"

Quantity Rules:
- Minimum Quantity: 1
- Maximum Quantity: (leave empty for unlimited)
- Group of: 1
```

**What customer sees:**
```
WELDAS MASKA ΤΣΕΠΗΣ ΗΛΕΚΤΡΟΣΥΓΚΟΛΛΗΤΟΥ 44-7111
€127.10 per 5kg package (€25.42/kg)

Quantity: [1] [+] [-]
[Add to Cart]
```

**If they change quantity to 3:**
```
€127.10 × 3 = €381.30
(15kg total at €25.42/kg)
```

---

## 🔧 Implementation in BRIDGE

### Option 1: Add Quantity Rules to BRIDGE

I can add quantity rule management to BRIDGE so you can:
- Set minimum/maximum/step for products
- Sync quantity rules from Capital ERP
- Bulk update quantity rules by brand

**Would you like me to add this feature?**

### Option 2: Use Plugin Only

Just install one of the free plugins and configure manually in WooCommerce. BRIDGE doesn't need to manage this.

---

## 📊 Comparison of Solutions

| Solution | Cost | Features | Ease of Use |
|----------|------|----------|-------------|
| **WooCommerce Min/Max Quantities** (Official) | $49/year | Full features, official support | ⭐⭐⭐⭐⭐ |
| **Min Max Quantity & Step Control** (Free) | Free | Same features, community support | ⭐⭐⭐⭐ |
| **WPC Product Quantity** (Free) | Free | Good features, simple | ⭐⭐⭐⭐ |
| **Custom Code** | Free | Full control, requires coding | ⭐⭐ |

**Recommendation:** Start with a free plugin to test, upgrade to official if needed.

---

## 🎯 Step-by-Step Setup Guide

### Using Free Plugin (Recommended)

**Step 1: Install Plugin**
```
1. WordPress Admin → Plugins → Add New
2. Search "Min Max Quantity Step Control"
3. Install "Min Max Quantity & Step Control for WooCommerce"
4. Activate
```

**Step 2: Configure Product**
```
1. Products → All Products
2. Edit product (e.g., WELDAS MASKA 44-7111)
3. Scroll to "Product Data" section
4. Find "Quantity Rules" or "Min Max Settings"
5. Set:
   - Min Quantity: 1
   - Max Quantity: (empty or 100)
   - Step/Group of: 1
6. Update product
```

**Step 3: Test**
```
1. Visit product page on your site
2. Try to add to cart
3. Try changing quantity
4. Verify only whole numbers work
5. Verify minimum is 1
```

**Step 4: Bulk Apply (Optional)**
```
If plugin supports bulk editing:
1. Products → All Products
2. Select multiple products
3. Bulk Actions → Edit
4. Apply quantity rules to all
5. Update
```

---

## ⚠️ Important Considerations

### Pricing Display

**Challenge:** You want to show "€25.42/kg" but sell in 5kg packages (€127.10)

**Solutions:**

**1. Price Suffix (Easiest)**
```
Regular Price: 127.10
Price Suffix: "per 5kg (€25.42/kg)"

Displays as: €127.10 per 5kg (€25.42/kg)
```

**2. Product Description**
```
Regular Price: 127.10
Short Description: "Price per kilogram: €25.42"
```

**3. Custom Field**
```
Regular Price: 127.10
Custom Field "price_per_kg": 25.42
Display in template: "€127.10 (€25.42/kg)"
```

**4. WooCommerce Measurement Price Calculator Plugin**
```
- Paid plugin ($79/year)
- Automatically calculates price per unit
- Shows "€25.42/kg" and lets customer enter kg
- Converts to packages automatically
```

### Stock Management

**If you track stock by packages:**
```
Stock Quantity: 20 (= 20 packages = 100kg)
Customer buys quantity 3 = 3 packages = 15kg
Stock becomes: 17 packages
```

**If you track stock by kg:**
```
Stock Quantity: 100 (kg)
Customer buys 3 packages = 15kg
Stock becomes: 85kg
```

**Recommendation:** Track by packages (simpler with quantity rules)

---

## 🚀 Quick Start

### For Your Welding Products

**Immediate Steps:**

1. **Install free plugin**
   ```
   Plugin: "Min Max Quantity & Step Control for WooCommerce"
   Link: wordpress.org/plugins/woo-min-max-quantity-step-control-single/
   ```

2. **Configure one product as test**
   ```
   Product: WELDAS MASKA 44-7111
   Min: 1
   Max: (empty)
   Step: 1
   ```

3. **Test on frontend**
   ```
   Visit product page
   Try adding to cart
   Change quantity
   Verify works correctly
   ```

4. **Apply to all products**
   ```
   Use bulk edit or
   Configure each product individually
   ```

5. **Update price displays**
   ```
   Add price suffix: "per 5kg (€X/kg)"
   Or update product descriptions
   ```

---

## 💬 Need Help?

**If you want me to:**
- ✅ Add quantity rule management to BRIDGE
- ✅ Create bulk update feature for quantity rules
- ✅ Sync quantity rules from Capital ERP
- ✅ Add per-kg pricing display in BRIDGE

**Just let me know!**

---

## 📋 Summary

✅ **Yes, WooCommerce supports quantity increments**  
✅ **Use "Group of" field to set step value**  
✅ **Free plugins available** (no need to pay)  
✅ **Easy to configure** per product  
✅ **Works with your 5kg package requirement**  
✅ **Can show per-kg pricing** with price suffix  

**Recommended Plugin:** Min Max Quantity & Step Control for WooCommerce (Free)

**Setup Time:** 5-10 minutes per product (or use bulk edit)

**Result:** Customers can only buy in 5kg increments (1, 2, 3 packages) ✅

---

**Version:** 1.0  
**Date:** November 30, 2025  
**Topic:** WooCommerce Quantity Control  
**Status:** ✅ RESEARCHED  
**Repository:** https://github.com/geosampson/bridge
