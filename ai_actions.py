"""
AI Actions Module for BRIDGE
Executable actions that the AI can perform with user approval
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import requests
from requests.auth import HTTPBasicAuth


class BridgeActions:
    """Executable actions for AI assistant"""
    
    def __init__(self, woo_config: Dict, capital_config: Dict, data_store):
        self.woo_config = woo_config
        self.capital_config = capital_config
        self.data_store = data_store
        
    # ========================================================================
    # BRAND DETECTION AND ASSIGNMENT
    # ========================================================================
    
    def detect_brands_in_products(self, products: List[Dict]) -> List[Dict]:
        """
        Detect brand names in product titles and suggest brand assignments
        
        Returns:
            List of products with detected brands that need assignment
        """
        # Common brand patterns (expand this list based on your inventory)
        brand_keywords = [
            'nike', 'adidas', 'puma', 'reebok', 'under armour',
            'samsung', 'lg', 'sony', 'apple', 'huawei',
            'bosch', 'siemens', 'philips', 'panasonic',
            'dell', 'hp', 'lenovo', 'asus', 'acer',
            # Add more brands specific to your business
        ]
        
        detected = []
        
        for product in products:
            name = product.get('woo_name', '').lower()
            current_brand = product.get('woo_brand', '').lower()
            
            # Skip if brand already assigned
            if current_brand:
                continue
            
            # Check for brand keywords in name
            for brand in brand_keywords:
                if brand in name:
                    detected.append({
                        'sku': product.get('sku'),
                        'name': product.get('woo_name'),
                        'detected_brand': brand.title(),
                        'current_brand': current_brand,
                        'woo_id': product.get('woo_id')
                    })
                    break
        
        return detected
    
    def assign_brand_to_product(self, woo_id: int, brand_name: str) -> Dict[str, Any]:
        """
        Assign brand to a WooCommerce product
        
        Args:
            woo_id: WooCommerce product ID
            brand_name: Brand name to assign
            
        Returns:
            Result dictionary with success status
        """
        try:
            # WooCommerce API endpoint for updating product
            url = f"{self.woo_config['store_url']}/wp-json/wc/v3/products/{woo_id}"
            
            # Update product with brand attribute
            # Note: This assumes you have a "Brand" attribute set up in WooCommerce
            data = {
                "attributes": [
                    {
                        "name": "Brand",
                        "options": [brand_name],
                        "visible": True
                    }
                ]
            }
            
            response = requests.put(
                url,
                json=data,
                auth=HTTPBasicAuth(
                    self.woo_config['consumer_key'],
                    self.woo_config['consumer_secret']
                )
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': f'Brand "{brand_name}" assigned to product {woo_id}'
                }
            else:
                return {
                    'success': False,
                    'message': f'Failed to assign brand: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error assigning brand: {str(e)}'
            }
    
    def bulk_assign_brands(self, assignments: List[Dict]) -> Dict[str, Any]:
        """
        Assign brands to multiple products
        
        Args:
            assignments: List of dicts with 'woo_id' and 'brand_name'
            
        Returns:
            Summary of results
        """
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for assignment in assignments:
            result = self.assign_brand_to_product(
                assignment['woo_id'],
                assignment['brand_name']
            )
            
            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'woo_id': assignment['woo_id'],
                    'error': result['message']
                })
        
        return results
    
    # ========================================================================
    # PRODUCT DATA EDITING
    # ========================================================================
    
    def update_product_name(self, woo_id: int, new_name: str) -> Dict[str, Any]:
        """Update product name in WooCommerce"""
        try:
            url = f"{self.woo_config['store_url']}/wp-json/wc/v3/products/{woo_id}"
            
            data = {"name": new_name}
            
            response = requests.put(
                url,
                json=data,
                auth=HTTPBasicAuth(
                    self.woo_config['consumer_key'],
                    self.woo_config['consumer_secret']
                )
            )
            
            if response.status_code == 200:
                return {'success': True, 'message': f'Name updated to "{new_name}"'}
            else:
                return {'success': False, 'message': f'Failed: {response.text}'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def update_product_description(self, woo_id: int, new_description: str) -> Dict[str, Any]:
        """Update product description in WooCommerce"""
        try:
            url = f"{self.woo_config['store_url']}/wp-json/wc/v3/products/{woo_id}"
            
            data = {"description": new_description}
            
            response = requests.put(
                url,
                json=data,
                auth=HTTPBasicAuth(
                    self.woo_config['consumer_key'],
                    self.woo_config['consumer_secret']
                )
            )
            
            if response.status_code == 200:
                return {'success': True, 'message': 'Description updated'}
            else:
                return {'success': False, 'message': f'Failed: {response.text}'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def update_product_sku(self, woo_id: int, new_sku: str) -> Dict[str, Any]:
        """Update product SKU in WooCommerce"""
        try:
            url = f"{self.woo_config['store_url']}/wp-json/wc/v3/products/{woo_id}"
            
            data = {"sku": new_sku}
            
            response = requests.put(
                url,
                json=data,
                auth=HTTPBasicAuth(
                    self.woo_config['consumer_key'],
                    self.woo_config['consumer_secret']
                )
            )
            
            if response.status_code == 200:
                return {'success': True, 'message': f'SKU updated to "{new_sku}"'}
            else:
                return {'success': False, 'message': f'Failed: {response.text}'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    # ========================================================================
    # VARIATION PATTERN DETECTION
    # ========================================================================
    
    def detect_product_variations(self, products: List[Dict]) -> List[Dict]:
        """
        Detect products that are variations of the same base product
        
        Returns:
            List of product families with their variations
        """
        # Common variation patterns
        size_patterns = [
            r'\b(XS|S|M|L|XL|XXL|XXXL)\b',
            r'\b(\d+(?:\.\d+)?)\s*(cm|mm|m|inch|"|\')\b',
            r'\b(Small|Medium|Large|Extra Large)\b'
        ]
        
        color_patterns = [
            r'\b(Black|White|Red|Blue|Green|Yellow|Orange|Purple|Pink|Brown|Gray|Grey)\b',
            r'\b(Μαύρο|Άσπρο|Κόκκινο|Μπλε|Πράσινο|Κίτρινο)\b'  # Greek colors
        ]
        
        # Group products by base name (remove size/color indicators)
        product_families = {}
        
        for product in products:
            name = product.get('woo_name', '')
            sku = product.get('sku', '')
            
            # Remove size and color indicators to get base name
            base_name = name
            for pattern in size_patterns + color_patterns:
                base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
            
            # Clean up extra spaces and dashes
            base_name = re.sub(r'\s+', ' ', base_name).strip()
            base_name = re.sub(r'\s*-\s*$', '', base_name)
            
            # Group by base name
            if base_name not in product_families:
                product_families[base_name] = []
            
            # Extract variation attributes
            variation_attrs = {
                'sku': sku,
                'full_name': name,
                'woo_id': product.get('woo_id'),
                'size': None,
                'color': None
            }
            
            # Detect size
            for pattern in size_patterns:
                match = re.search(pattern, name, re.IGNORECASE)
                if match:
                    variation_attrs['size'] = match.group(0)
                    break
            
            # Detect color
            for pattern in color_patterns:
                match = re.search(pattern, name, re.IGNORECASE)
                if match:
                    variation_attrs['color'] = match.group(0)
                    break
            
            product_families[base_name].append(variation_attrs)
        
        # Filter to only families with multiple variations
        variation_families = []
        for base_name, variations in product_families.items():
            if len(variations) > 1:
                variation_families.append({
                    'base_name': base_name,
                    'variation_count': len(variations),
                    'variations': variations
                })
        
        # Sort by variation count (most variations first)
        variation_families.sort(key=lambda x: x['variation_count'], reverse=True)
        
        return variation_families
    
    # ========================================================================
    # SMART PRODUCT MATCHING
    # ========================================================================
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def fuzzy_match_products(self, 
                            unmatched_capital: List[Dict],
                            unmatched_woo: List[Dict],
                            threshold: float = 0.7) -> List[Dict]:
        """
        Find potential matches between unmatched Capital and WooCommerce products
        
        Args:
            unmatched_capital: List of Capital products without WooCommerce match
            unmatched_woo: List of WooCommerce products without Capital match
            threshold: Minimum similarity score (0-1) to consider a match
            
        Returns:
            List of potential matches with similarity scores
        """
        potential_matches = []
        
        for cap_product in unmatched_capital:
            cap_sku = str(cap_product.get('sku', '')).strip()
            cap_name = cap_product.get('name', '').strip()
            
            for woo_product in unmatched_woo:
                woo_sku = str(woo_product.get('sku', '')).strip()
                woo_name = woo_product.get('name', '').strip()
                
                # Skip if either name is empty
                if not cap_name or not woo_name:
                    continue
                
                # Calculate similarity scores
                sku_similarity = self.calculate_similarity(cap_sku, woo_sku) if cap_sku and woo_sku else 0
                name_similarity = self.calculate_similarity(cap_name, woo_name)
                
                # Check for partial SKU match (ignoring leading zeros)
                sku_partial_match = False
                if cap_sku and woo_sku:
                    cap_sku_clean = cap_sku.lstrip('0')
                    woo_sku_clean = woo_sku.lstrip('0')
                    if cap_sku_clean == woo_sku_clean:
                        sku_partial_match = True
                        sku_similarity = 1.0
                
                # Combined score (weighted: 60% name, 40% SKU)
                combined_score = (name_similarity * 0.6) + (sku_similarity * 0.4)
                
                # If score exceeds threshold, add as potential match
                if combined_score >= threshold or sku_partial_match:
                    potential_matches.append({
                        'capital_sku': cap_sku,
                        'capital_name': cap_name,
                        'capital_id': cap_product.get('id'),
                        'woo_sku': woo_sku,
                        'woo_name': woo_name,
                        'woo_id': woo_product.get('id'),
                        'name_similarity': round(name_similarity, 3),
                        'sku_similarity': round(sku_similarity, 3),
                        'combined_score': round(combined_score, 3),
                        'sku_partial_match': sku_partial_match
                    })
        
        # Sort by combined score (best matches first)
        potential_matches.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return potential_matches
    
    def create_product_match(self, capital_sku: str, woo_id: int) -> Dict[str, Any]:
        """
        Create a match between Capital and WooCommerce product
        This updates the internal data store
        
        Args:
            capital_sku: Capital product SKU
            woo_id: WooCommerce product ID
            
        Returns:
            Result dictionary
        """
        try:
            # Find products in data store
            capital_product = None
            for p in self.data_store.capital_products:
                if str(p.get('sku', '')).strip() == capital_sku:
                    capital_product = p
                    break
            
            woo_product = None
            for p in self.data_store.woo_products:
                if p.get('id') == woo_id:
                    woo_product = p
                    break
            
            if not capital_product or not woo_product:
                return {
                    'success': False,
                    'message': 'Product not found in data store'
                }
            
            # Update WooCommerce product SKU to match Capital
            update_result = self.update_product_sku(woo_id, capital_sku)
            
            if update_result['success']:
                return {
                    'success': True,
                    'message': f'Matched Capital SKU {capital_sku} with WooCommerce product {woo_id}'
                }
            else:
                return update_result
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating match: {str(e)}'
            }
