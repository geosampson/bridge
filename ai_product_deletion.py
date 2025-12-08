"""
Product Deletion Module for BRIDGE
Handles deletion of discontinued products from WooCommerce
"""

from typing import Dict, Any, List
import requests
from requests.auth import HTTPBasicAuth


def delete_woo_product(woo_config: Dict, woo_id: int, force=True) -> Dict[str, Any]:
    """
    Delete a product from WooCommerce
    
    Args:
        woo_config: WooCommerce configuration
        woo_id: WooCommerce product ID
        force: If True, permanently delete. If False, move to trash.
        
    Returns:
        Result dictionary
    """
    try:
        url = f"{woo_config['store_url']}/wp-json/wc/v3/products/{woo_id}"
        
        params = {'force': 'true' if force else 'false'}
        
        response = requests.delete(
            url,
            params=params,
            auth=HTTPBasicAuth(
                woo_config['consumer_key'],
                woo_config['consumer_secret']
            )
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': f'Product {woo_id} deleted successfully'
            }
        else:
            return {
                'success': False,
                'message': f'Failed to delete product: {response.text}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Error deleting product: {str(e)}'
        }


def bulk_delete_products(woo_config: Dict, woo_ids: List[int], force=True) -> Dict[str, Any]:
    """
    Delete multiple products from WooCommerce
    
    Args:
        woo_config: WooCommerce configuration
        woo_ids: List of WooCommerce product IDs
        force: If True, permanently delete. If False, move to trash.
        
    Returns:
        Summary of results
    """
    results = {
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    for woo_id in woo_ids:
        result = delete_woo_product(woo_config, woo_id, force)
        
        if result['success']:
            results['success'] += 1
        else:
            results['failed'] += 1
            results['errors'].append({
                'woo_id': woo_id,
                'error': result['message']
            })
    
    return results
