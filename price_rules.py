"""
Price Comparison Rules Configuration

Handles special price comparison rules for products where Capital and WooCommerce
use different pricing units (e.g., per KG vs per package).
"""

import re
import json


class PriceRules:
    """Manages custom price comparison rules for different product categories"""
    
    def __init__(self, config_file=None):
        self.config_file = config_file
        self.rules = self._load_default_rules()
        
        if config_file:
            self._load_custom_rules()
    
    def _load_default_rules(self):
        """Load default price rules"""
        return {
            'weight_based': {
                'enabled': True,
                'keywords': ['ΣΥΡΜΑ', 'ΣΙΔΗΡΟΣ', 'ΧΑΛΥΒΑΣ', 'WIRE', 'STEEL'],  # Products sold by weight
                'tolerance_percent': 5,  # Allow 5% price difference
                'description': 'Products where Capital price is per KG but WooCommerce is per package'
            },
            'piece_based': {
                'enabled': True,
                'keywords': ['ΗΛΕΚΤΡΟΔΙΟ', 'ΗΛΕΚΤΡΟΔΙΑ', 'ΒΕΡΓΑ', 'ELECTRODE', 'ELECTRODES', 'RODS'],  # Products sold by piece
                'tolerance_percent': 5,
                'description': 'Products where Capital price is per KG but WooCommerce is per piece/package'
            },
            'length_based': {
                'enabled': True,
                'keywords': ['ΚΑΛΩΔΙΟ', 'ΣΩΛΗΝΑΣ', 'CABLE', 'PIPE', 'TUBE'],  # Products sold by length
                'tolerance_percent': 5,
                'description': 'Products where Capital price is per meter but WooCommerce is per roll/package'
            },
            'volume_based': {
                'enabled': False,
                'keywords': ['ΥΓΡΟ', 'ΛΑΔΙ', 'LIQUID', 'OIL'],  # Products sold by volume
                'tolerance_percent': 5,
                'description': 'Products where Capital price is per liter but WooCommerce is per container'
            }
        }
    
    def _load_custom_rules(self):
        """Load custom rules from config file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                custom_rules = json.load(f)
                self.rules.update(custom_rules)
        except FileNotFoundError:
            # Create default config file
            self.save_rules()
        except Exception as e:
            print(f"Error loading price rules: {e}")
    
    def save_rules(self):
        """Save rules to config file"""
        if not self.config_file:
            return
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving price rules: {e}")
    
    def extract_package_weight(self, product_name):
        """
        Extract package weight from product name.
        
        Examples:
            "ΣΥΡΜΑ 2KG" -> 2.0
            "ΣΥΡΜΑ 2,5KG" -> 2.5
            "WIRE 5 KG" -> 5.0
            "ΣΥΡΜΑ 15KG" -> 15.0
        
        Returns:
            float: Package weight in KG, or None if not found
        """
        # Patterns to match weight in product name
        patterns = [
            r'(\d+[,.]?\d*)\s*KG',  # "2KG", "2.5KG", "2,5KG", "2 KG"
            r'(\d+[,.]?\d*)\s*ΚΙΛΑ',  # Greek: "2 ΚΙΛΑ"
            r'(\d+[,.]?\d*)\s*ΚΓ',  # Greek abbreviation
        ]
        
        for pattern in patterns:
            match = re.search(pattern, product_name.upper())
            if match:
                weight_str = match.group(1).replace(',', '.')
                try:
                    return float(weight_str)
                except ValueError:
                    continue
        
        return None
    
    def extract_package_length(self, product_name):
        """
        Extract package length from product name.
        
        Examples:
            "ΚΑΛΩΔΙΟ 10M" -> 10.0
            "CABLE 25 METERS" -> 25.0
            "ΣΩΛΗΝΑΣ 50M" -> 50.0
        
        Returns:
            float: Package length in meters, or None if not found
        """
        patterns = [
            r'(\d+[,.]?\d*)\s*M(?:ETERS?)?',  # "10M", "10 METERS"
            r'(\d+[,.]?\d*)\s*ΜΕΤΡΑ',  # Greek: "10 ΜΕΤΡΑ"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, product_name.upper())
            if match:
                length_str = match.group(1).replace(',', '.')
                try:
                    return float(length_str)
                except ValueError:
                    continue
        
        return None
    
    def should_use_weight_rule(self, product_name):
        """Check if product should use weight-based pricing rule"""
        if not self.rules['weight_based']['enabled']:
            return False
        
        product_upper = product_name.upper()
        keywords = self.rules['weight_based']['keywords']
        
        return any(keyword in product_upper for keyword in keywords)
    
    def should_use_length_rule(self, product_name):
        """Check if product should use length-based pricing rule"""
        if not self.rules['length_based']['enabled']:
            return False
        
        product_upper = product_name.upper()
        keywords = self.rules['length_based']['keywords']
        
        return any(keyword in product_upper for keyword in keywords)
    
    def should_use_piece_rule(self, product_name):
        """Check if product should use piece-based pricing rule"""
        if not self.rules['piece_based']['enabled']:
            return False
        
        product_upper = product_name.upper()
        keywords = self.rules['piece_based']['keywords']
        
        return any(keyword in product_upper for keyword in keywords)
    
    def calculate_expected_price(self, capital_price_per_unit, product_name, rule_type='weight'):
        """
        Calculate expected WooCommerce price based on Capital price per unit.
        
        Args:
            capital_price_per_unit: Capital price (per KG, per meter, etc.)
            product_name: Product name containing package size
            rule_type: 'weight' or 'length'
        
        Returns:
            float: Expected WooCommerce price, or None if cannot calculate
        """
        if rule_type == 'weight':
            package_size = self.extract_package_weight(product_name)
        elif rule_type == 'length':
            package_size = self.extract_package_length(product_name)
        else:
            return None
        
        if package_size is None or capital_price_per_unit <= 0:
            return None
        
        return capital_price_per_unit * package_size
    
    def check_price_match(self, woo_price, capital_price, product_name):
        """
        Check if WooCommerce price matches Capital price considering special rules.
        
        Args:
            woo_price: WooCommerce price
            capital_price: Capital price (may be per unit)
            product_name: Product name
        
        Returns:
            dict: {
                'matches': bool,
                'rule_applied': str or None,
                'expected_price': float or None,
                'difference': float,
                'difference_percent': float,
                'within_tolerance': bool
            }
        """
        result = {
            'matches': False,
            'rule_applied': None,
            'expected_price': None,
            'difference': 0,
            'difference_percent': 0,
            'within_tolerance': False
        }
        
        # Check if weight-based rule applies
        if self.should_use_weight_rule(product_name):
            expected_price = self.calculate_expected_price(capital_price, product_name, 'weight')
            if expected_price:
                result['rule_applied'] = 'weight_based'
                result['expected_price'] = expected_price
                result['difference'] = abs(woo_price - expected_price)
                result['difference_percent'] = (result['difference'] / expected_price * 100) if expected_price > 0 else 0
                tolerance = self.rules['weight_based']['tolerance_percent']
                result['within_tolerance'] = result['difference_percent'] <= tolerance
                result['matches'] = result['within_tolerance']
                return result
        
        # Check if length-based rule applies
        if self.should_use_length_rule(product_name):
            expected_price = self.calculate_expected_price(capital_price, product_name, 'length')
            if expected_price:
                result['rule_applied'] = 'length_based'
                result['expected_price'] = expected_price
                result['difference'] = abs(woo_price - expected_price)
                result['difference_percent'] = (result['difference'] / expected_price * 100) if expected_price > 0 else 0
                tolerance = self.rules['length_based']['tolerance_percent']
                result['within_tolerance'] = result['difference_percent'] <= tolerance
                result['matches'] = result['within_tolerance']
                return result
        
        # Check if piece-based rule applies (manual override required)
        if self.should_use_piece_rule(product_name):
            # For piece-based products, we can't auto-calculate
            # User needs to set manual price ratio
            result['rule_applied'] = 'piece_based_manual'
            result['expected_price'] = None  # Requires manual ratio
            result['difference'] = abs(woo_price - capital_price)
            result['difference_percent'] = (result['difference'] / capital_price * 100) if capital_price > 0 else 0
            result['within_tolerance'] = False  # Always false until manual ratio set
            result['matches'] = False
            result['requires_manual_ratio'] = True
            return result
        
        # No special rule applies - use direct comparison
        result['expected_price'] = capital_price
        result['difference'] = abs(woo_price - capital_price)
        result['difference_percent'] = (result['difference'] / capital_price * 100) if capital_price > 0 else 0
        result['within_tolerance'] = result['difference'] < 0.01  # 1 cent tolerance
        result['matches'] = result['within_tolerance']
        
        return result


# Example usage
if __name__ == '__main__':
    rules = PriceRules()
    
    # Test weight extraction
    print("Weight extraction tests:")
    print(f"  'ΣΥΡΜΑ 2KG' -> {rules.extract_package_weight('ΣΥΡΜΑ 2KG')} kg")
    print(f"  'ΣΥΡΜΑ 2,5KG' -> {rules.extract_package_weight('ΣΥΡΜΑ 2,5KG')} kg")
    print(f"  'WIRE 5 KG' -> {rules.extract_package_weight('WIRE 5 KG')} kg")
    print(f"  'ΣΥΡΜΑ 15KG' -> {rules.extract_package_weight('ΣΥΡΜΑ 15KG')} kg")
    
    # Test price calculation
    print("\nPrice calculation tests:")
    capital_price_per_kg = 10.50  # €10.50 per KG
    product_name = "ΣΥΡΜΑ ΓΑΛΒΑΝΙΖΕ 2KG"
    expected = rules.calculate_expected_price(capital_price_per_kg, product_name, 'weight')
    print(f"  Capital: €{capital_price_per_kg}/kg")
    print(f"  Product: {product_name}")
    print(f"  Expected WooCommerce price: €{expected}")
    
    # Test price matching
    print("\nPrice matching tests:")
    woo_price = 21.00
    match_result = rules.check_price_match(woo_price, capital_price_per_kg, product_name)
    print(f"  WooCommerce price: €{woo_price}")
    print(f"  Rule applied: {match_result['rule_applied']}")
    print(f"  Expected price: €{match_result['expected_price']}")
    print(f"  Difference: €{match_result['difference']:.2f} ({match_result['difference_percent']:.1f}%)")
    print(f"  Matches: {match_result['matches']}")
