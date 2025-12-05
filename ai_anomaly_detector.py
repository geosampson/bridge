"""
AI Anomaly Detector for BRIDGE
Detects data quality issues and pricing anomalies
"""

from typing import List, Dict, Any
from ai_client import BridgeAI

class AnomalyDetector:
    """Detects anomalies in product data using AI and rules"""
    
    def __init__(self, ai_client: BridgeAI = None):
        self.ai = ai_client or BridgeAI()
        
    def detect_all_anomalies(self, products: List[Dict]) -> List[Dict]:
        """
        Detect all types of anomalies in products
        
        Returns:
            List of anomaly dictionaries with:
            - sku: Product SKU
            - type: Anomaly type
            - severity: high/medium/low
            - description: Human-readable description
            - suggested_fix: Recommended action
            - auto_fixable: Whether this can be auto-fixed
        """
        anomalies = []
        
        # Rule-based detection (fast, always works)
        anomalies.extend(self._detect_price_anomalies(products))
        anomalies.extend(self._detect_data_quality_issues(products))
        anomalies.extend(self._detect_stock_issues(products))
        
        # AI-powered detection (if available)
        if self.ai.is_available():
            ai_anomalies = self.ai.detect_anomalies(products)
            anomalies.extend(ai_anomalies)
        
        # Remove duplicates and sort by severity
        anomalies = self._deduplicate_anomalies(anomalies)
        anomalies = sorted(anomalies, key=lambda x: self._severity_score(x['severity']), reverse=True)
        
        return anomalies
    
    def _detect_price_anomalies(self, products: List[Dict]) -> List[Dict]:
        """Detect price-related anomalies"""
        anomalies = []
        
        for p in products:
            sku = p.get('sku')
            woo_price = p.get('woo_regular_price', 0)
            capital_price = p.get('capital_rtlprice', 0)
            sale_price = p.get('woo_sale_price')
            
            # Zero price in WooCommerce
            if woo_price == 0 and capital_price > 0:
                anomalies.append({
                    "sku": sku,
                    "type": "price_zero",
                    "severity": "high",
                    "description": f"WooCommerce price is €0.00 but Capital has €{capital_price:.2f}",
                    "suggested_fix": f"Sync price from Capital (€{capital_price:.2f})",
                    "auto_fixable": True
                })
            
            # Large price difference (>20%)
            if woo_price > 0 and capital_price > 0:
                diff_percent = abs(woo_price - capital_price) / capital_price * 100
                if diff_percent > 20:
                    anomalies.append({
                        "sku": sku,
                        "type": "price_mismatch",
                        "severity": "medium" if diff_percent < 50 else "high",
                        "description": f"Price difference: {diff_percent:.1f}% (WOO: €{woo_price:.2f}, Capital: €{capital_price:.2f})",
                        "suggested_fix": f"Review pricing or sync to Capital (€{capital_price:.2f})",
                        "auto_fixable": False  # Needs review
                    })
            
            # Sale price higher than regular price
            if sale_price and sale_price > woo_price:
                anomalies.append({
                    "sku": sku,
                    "type": "invalid_sale_price",
                    "severity": "high",
                    "description": f"Sale price (€{sale_price:.2f}) higher than regular price (€{woo_price:.2f})",
                    "suggested_fix": "Remove sale price or fix regular price",
                    "auto_fixable": True
                })
            
            # Extreme discount (>70%)
            discount = p.get('woo_discount_percent', 0)
            if discount > 70:
                anomalies.append({
                    "sku": sku,
                    "type": "extreme_discount",
                    "severity": "medium",
                    "description": f"Unusually high discount: {discount:.1f}%",
                    "suggested_fix": "Verify discount is intentional",
                    "auto_fixable": False
                })
        
        return anomalies
    
    def _detect_data_quality_issues(self, products: List[Dict]) -> List[Dict]:
        """Detect data quality issues"""
        anomalies = []
        
        for p in products:
            sku = p.get('sku')
            name = p.get('woo_name', '')
            short_desc = p.get('woo_short_description', '')
            desc = p.get('woo_description', '')
            
            # Missing or very short name
            if not name or len(name) < 5:
                anomalies.append({
                    "sku": sku,
                    "type": "missing_name",
                    "severity": "high",
                    "description": "Product name is missing or too short",
                    "suggested_fix": "Add descriptive product name",
                    "auto_fixable": False
                })
            
            # Missing description
            if not desc or len(desc) < 20:
                anomalies.append({
                    "sku": sku,
                    "type": "missing_description",
                    "severity": "low",
                    "description": "Product description is missing or very short",
                    "suggested_fix": "Add product description (AI can generate)",
                    "auto_fixable": True  # AI can generate
                })
            
            # Missing short description
            if not short_desc or len(short_desc) < 10:
                anomalies.append({
                    "sku": sku,
                    "type": "missing_short_description",
                    "severity": "low",
                    "description": "Short description is missing",
                    "suggested_fix": "Add short description (AI can generate)",
                    "auto_fixable": True
                })
        
        return anomalies
    
    def _detect_stock_issues(self, products: List[Dict]) -> List[Dict]:
        """Detect stock-related issues"""
        anomalies = []
        
        for p in products:
            sku = p.get('sku')
            stock = p.get('woo_stock_quantity')
            stock_status = p.get('woo_stock_status')
            sales = p.get('woo_total_sales', 0)
            
            # Out of stock but marked as in stock
            if stock == 0 and stock_status == 'instock':
                anomalies.append({
                    "sku": sku,
                    "type": "stock_status_mismatch",
                    "severity": "medium",
                    "description": "Stock quantity is 0 but status is 'instock'",
                    "suggested_fix": "Update stock status to 'outofstock'",
                    "auto_fixable": True
                })
            
            # High sales but low stock
            if sales > 10 and stock is not None and stock < 5:
                anomalies.append({
                    "sku": sku,
                    "type": "low_stock_popular",
                    "severity": "medium",
                    "description": f"Popular product (sold {sales}) but low stock ({stock})",
                    "suggested_fix": "Consider restocking",
                    "auto_fixable": False
                })
        
        return anomalies
    
    def _deduplicate_anomalies(self, anomalies: List[Dict]) -> List[Dict]:
        """Remove duplicate anomalies (same SKU + type)"""
        seen = set()
        unique = []
        
        for a in anomalies:
            key = (a.get('sku'), a.get('type'))
            if key not in seen:
                seen.add(key)
                unique.append(a)
        
        return unique
    
    def _severity_score(self, severity: str) -> int:
        """Convert severity to numeric score for sorting"""
        scores = {"high": 3, "medium": 2, "low": 1}
        return scores.get(severity, 0)
    
    def get_anomaly_summary(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """Get summary statistics of anomalies"""
        total = len(anomalies)
        by_severity = {"high": 0, "medium": 0, "low": 0}
        by_type = {}
        auto_fixable = 0
        
        for a in anomalies:
            severity = a.get('severity', 'low')
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            atype = a.get('type', 'unknown')
            by_type[atype] = by_type.get(atype, 0) + 1
            
            if a.get('auto_fixable', False):
                auto_fixable += 1
        
        return {
            "total": total,
            "by_severity": by_severity,
            "by_type": by_type,
            "auto_fixable": auto_fixable,
            "needs_review": total - auto_fixable
        }
