"""
Stock Visibility Manager

Manages stock visibility settings for WooCommerce products.
Allows hiding stock quantities from customers while maintaining internal tracking.
"""


def hide_stock_from_woocommerce(woo_client, product_ids=None):
    """
    Hide stock quantities from WooCommerce display.
    
    This sets manage_stock to false for products, which prevents
    WooCommerce from displaying stock quantities to customers.
    
    Args:
        woo_client: WooCommerceClient instance
        product_ids: List of product IDs to update, or None for all products
    
    Returns:
        int: Number of products updated
    """
    updates = []
    
    if product_ids:
        # Update specific products
        for product_id in product_ids:
            updates.append({
                'id': product_id,
                'manage_stock': False,  # Don't show stock to customers
                'stock_status': 'instock'  # Always show as in stock
            })
    
    if updates:
        # Batch update
        result = woo_client.batch_update_products(updates)
        return len(updates)
    
    return 0


def enable_stock_tracking_internally(woo_client, product_ids):
    """
    Enable stock tracking but hide from customers.
    
    This keeps track of stock internally but doesn't display it publicly.
    
    Args:
        woo_client: WooCommerceClient instance
        product_ids: List of product IDs to update
    
    Returns:
        int: Number of products updated
    """
    updates = []
    
    for product_id in product_ids:
        updates.append({
            'id': product_id,
            'manage_stock': True,  # Track stock internally
            'stock_status': 'instock',  # Always show as in stock
            'backorders': 'no',  # Don't allow backorders
            'sold_individually': False
        })
    
    if updates:
        result = woo_client.batch_update_products(updates)
        return len(updates)
    
    return 0


def get_stock_visibility_settings():
    """
    Get recommended stock visibility settings.
    
    Returns:
        dict: Stock visibility configuration
    """
    return {
        'hide_stock_from_customers': True,
        'track_stock_internally': True,
        'always_show_in_stock': True,
        'allow_backorders': False,
        'settings': {
            'manage_stock': False,  # Don't show stock quantities
            'stock_status': 'instock',  # Always in stock
            'backorders': 'no'
        }
    }
