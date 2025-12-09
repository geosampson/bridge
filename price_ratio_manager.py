"""
Manual Price Ratio Manager

Allows users to manually define price ratios for products where automatic
calculation is not possible (e.g., ΗΛΕΚΤΡΟΔΙΟ sold per piece instead of per KG).
"""

import json
import os


class PriceRatioManager:
    """Manages manual price ratios for products"""
    
    def __init__(self, config_file='price_ratios.json'):
        self.config_file = config_file
        self.ratios = self._load_ratios()
    
    def _load_ratios(self):
        """Load price ratios from config file"""
        if not os.path.exists(self.config_file):
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading price ratios: {e}")
            return {}
    
    def save_ratios(self):
        """Save price ratios to config file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.ratios, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving price ratios: {e}")
    
    def set_ratio(self, sku, ratio, description=''):
        """
        Set manual price ratio for a product.
        
        Args:
            sku: Product SKU
            ratio: Price multiplier (e.g., 2.5 means WooCommerce price = Capital price × 2.5)
            description: Optional description of why this ratio is used
        """
        self.ratios[sku] = {
            'ratio': float(ratio),
            'description': description
        }
        self.save_ratios()
    
    def get_ratio(self, sku):
        """
        Get manual price ratio for a product.
        
        Returns:
            float: Price ratio, or None if not set
        """
        if sku in self.ratios:
            return self.ratios[sku]['ratio']
        return None
    
    def has_ratio(self, sku):
        """Check if a product has a manual price ratio set"""
        return sku in self.ratios
    
    def remove_ratio(self, sku):
        """Remove manual price ratio for a product"""
        if sku in self.ratios:
            del self.ratios[sku]
            self.save_ratios()
    
    def get_all_ratios(self):
        """Get all manual price ratios"""
        return self.ratios.copy()
    
    def calculate_expected_price(self, sku, capital_price):
        """
        Calculate expected WooCommerce price using manual ratio.
        
        Args:
            sku: Product SKU
            capital_price: Capital price
        
        Returns:
            float: Expected WooCommerce price, or None if no ratio set
        """
        ratio = self.get_ratio(sku)
        if ratio is None:
            return None
        
        return capital_price * ratio


# Integration with price_rules.py
def check_price_with_manual_ratio(woo_price, capital_price, sku, ratio_manager, tolerance_percent=5):
    """
    Check if price matches using manual ratio.
    
    Args:
        woo_price: WooCommerce price
        capital_price: Capital price
        sku: Product SKU
        ratio_manager: PriceRatioManager instance
        tolerance_percent: Tolerance percentage
    
    Returns:
        dict: Price check result
    """
    result = {
        'matches': False,
        'rule_applied': 'manual_ratio',
        'expected_price': None,
        'difference': 0,
        'difference_percent': 0,
        'within_tolerance': False,
        'ratio': None
    }
    
    ratio = ratio_manager.get_ratio(sku)
    if ratio is None:
        result['rule_applied'] = None
        return result
    
    expected_price = capital_price * ratio
    result['expected_price'] = expected_price
    result['ratio'] = ratio
    result['difference'] = abs(woo_price - expected_price)
    result['difference_percent'] = (result['difference'] / expected_price * 100) if expected_price > 0 else 0
    result['within_tolerance'] = result['difference_percent'] <= tolerance_percent
    result['matches'] = result['within_tolerance']
    
    return result
