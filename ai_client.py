"""
AI Client for BRIDGE
Handles communication with Claude API for intelligent analysis
"""

import json
import anthropic
from typing import List, Dict, Any, Optional
from ai_config import AIConfig
from ai_system_knowledge import get_system_knowledge

class BridgeAI:
    """AI assistant for BRIDGE using Claude API"""
    
    def __init__(self, knowledge_base=None):
        self.config = AIConfig()
        self.client = None
        self.knowledge_base = knowledge_base
        if self.config.is_enabled():
            self.client = anthropic.Anthropic(api_key=self.config.get_api_key())
    
    def is_available(self):
        """Check if AI is available"""
        return self.client is not None
    
    def analyze_products(self, products: List[Dict], analysis_type: str = "anomalies") -> Dict[str, Any]:
        """
        Analyze products for issues, patterns, or insights
        
        Args:
            products: List of product dictionaries
            analysis_type: Type of analysis (anomalies, pricing, trends, etc.)
        
        Returns:
            Dictionary with analysis results and suggestions
        """
        if not self.is_available():
            return {"error": "AI not configured"}
        
        # Prepare product data for AI (anonymize if needed)
        product_summary = self._prepare_product_data(products)
        
        # Create prompt based on analysis type
        prompt = self._create_analysis_prompt(product_summary, analysis_type)
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.config.get_model(),
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse response
            result = self._parse_ai_response(response.content[0].text)
            return result
            
        except Exception as e:
            return {"error": f"AI analysis failed: {str(e)}"}
    
    def detect_anomalies(self, products: List[Dict]) -> List[Dict]:
        """
        Detect anomalies in product data
        
        Returns:
            List of anomalies with severity, description, and suggested fix
        """
        result = self.analyze_products(products, "anomalies")
        return result.get("anomalies", [])
    
    def suggest_actions(self, products: List[Dict]) -> List[Dict]:
        """
        Get AI suggestions for product improvements
        
        Returns:
            List of suggested actions with rationale
        """
        result = self.analyze_products(products, "suggestions")
        return result.get("suggestions", [])
    
    def generate_insights(self, products: List[Dict]) -> Dict[str, Any]:
        """
        Generate business insights from product data
        
        Returns:
            Dictionary with insights, trends, and recommendations
        """
        result = self.analyze_products(products, "insights")
        return result
    
    def chat(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Chat with AI assistant about products
        
        Args:
            message: User message
            context: Optional context (current products, filters, etc.)
        
        Returns:
            AI response
        """
        if not self.is_available():
            return "AI assistant is not configured. Please add your Claude API key in settings."
        
        # Build context-aware prompt
        prompt = self._create_chat_prompt(message, context)
        
        try:
            response = self.client.messages.create(
                model=self.config.get_model(),
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_description(self, product: Dict) -> str:
        """
        Generate product description using AI
        
        Args:
            product: Product dictionary
        
        Returns:
            Generated description
        """
        if not self.is_available():
            return ""
        
        prompt = f"""Generate a professional product description for an e-commerce site.

Product Details:
- Name: {product.get('woo_name', 'Unknown')}
- SKU: {product.get('sku', 'Unknown')}
- Brand: {product.get('woo_brand', 'Unknown')}
- Price: €{product.get('woo_regular_price', 0):.2f}
- Category: {', '.join([cat for cat in product.get('woo_categories', [])])}

Requirements:
- Professional tone
- 2-3 sentences
- Highlight key features
- SEO-friendly
- Greek language

Generate only the description, no additional text."""

        try:
            response = self.client.messages.create(
                model=self.config.get_model(),
                max_tokens=512,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            return f"Error generating description: {str(e)}"
    
    def _prepare_product_data(self, products: List[Dict]) -> str:
        """Prepare product data for AI analysis"""
        # Create summary of products (first 100 to avoid token limits)
        sample = products[:100] if len(products) > 100 else products
        
        summary = {
            "total_products": len(products),
            "sample_size": len(sample),
            "products": []
        }
        
        for p in sample:
            summary["products"].append({
                "sku": p.get('sku'),
                "name": p.get('woo_name', '')[:50],  # Truncate long names
                "woo_price": p.get('woo_regular_price', 0),
                "capital_price": p.get('capital_rtlprice', 0),
                "sale_price": p.get('woo_sale_price'),
                "discount": p.get('woo_discount_percent', 0),
                "stock": p.get('woo_stock_quantity'),
                "sales": p.get('woo_total_sales', 0),
                "price_match": p.get('price_match', False)
            })
        
        return json.dumps(summary, indent=2)
    
    def _create_analysis_prompt(self, product_data: str, analysis_type: str) -> str:
        """Create prompt for AI analysis"""
        
        if analysis_type == "anomalies":
            return f"""Analyze the following product data and identify anomalies or potential issues.

Product Data:
{product_data}

Please identify:
1. Products with price = 0 (likely sync errors)
2. Large price differences between WooCommerce and Capital (>20%)
3. Products with missing or very short descriptions
4. Unusual discount percentages (>50% or negative)
5. Stock inconsistencies
6. Any other data quality issues

For each anomaly, provide:
- SKU
- Issue type
- Severity (high/medium/low)
- Description
- Suggested fix

Return response as JSON:
{{
  "anomalies": [
    {{
      "sku": "ABC123",
      "type": "price_zero",
      "severity": "high",
      "description": "Product price is €0.00",
      "suggested_fix": "Sync price from Capital (€45.50)"
    }}
  ],
  "summary": "Found X issues affecting Y products"
}}"""

        elif analysis_type == "suggestions":
            return f"""Analyze the following product data and provide actionable suggestions for improvement.

Product Data:
{product_data}

Please suggest:
1. Pricing optimizations (products that could be priced higher/lower)
2. Discount opportunities (slow-moving products)
3. Products needing better descriptions
4. Stock management recommendations
5. Sales opportunities

For each suggestion, provide:
- SKU or product group
- Action type
- Rationale
- Expected impact
- Priority

Return response as JSON:
{{
  "suggestions": [
    {{
      "sku": "ABC123",
      "action": "increase_price",
      "rationale": "High sales, low stock, price below market",
      "expected_impact": "5-10% revenue increase",
      "priority": "high"
    }}
  ]
}}"""

        elif analysis_type == "insights":
            return f"""Analyze the following product data and generate business insights.

Product Data:
{product_data}

Please provide:
1. Top performing products (by sales)
2. Pricing trends and patterns
3. Discount effectiveness analysis
4. Stock level insights
5. Revenue opportunities
6. Key recommendations

Return response as JSON with insights and recommendations."""

        else:
            return f"Analyze this product data: {product_data}"
    
    def _create_chat_prompt(self, message: str, context: Optional[Dict]) -> str:
        """Create prompt for chat interaction"""
        # Start with system knowledge
        base_prompt = get_system_knowledge()
        
        # Add knowledge base context if available
        if self.knowledge_base:
            kb_context = self.knowledge_base.get_relevant_context(message)
            if kb_context:
                base_prompt += kb_context
        
        base_prompt += f"\n\n{'='*80}\n"
        base_prompt += f"USER QUESTION: {message}\n"
        base_prompt += f"{'='*80}\n"

        if context:
            # Check if data is loaded
            if not context.get("data_loaded", False):
                base_prompt += "\n**IMPORTANT**: No product data has been loaded yet. Please ask the user to click 'Fetch All Data' first.\n"
            else:
                # Add summary statistics
                base_prompt += f"\n**Database Summary:**\n"
                base_prompt += f"- Total matched products: {context.get('total_matched_products', 0)}\n"
                base_prompt += f"- Products with zero price: {context.get('zero_prices', 0)}\n"
                base_prompt += f"- Products with price mismatches: {context.get('price_mismatches', 0)}\n"
                base_prompt += f"- Products with brand issues: {context.get('brand_issues', 0)}\n"
                base_prompt += f"- Products without descriptions: {context.get('no_description_count', 0)}\n"
                
                # Add relevant product data based on query
                if any(keyword in message.lower() for keyword in ["zero", "price", "0", "€0"]):
                    if context.get("zero_price_products"):
                        base_prompt += f"\n**Products with zero price (SKUs):** {', '.join(context['zero_price_products'][:30])}\n"
                
                if any(keyword in message.lower() for keyword in ["brand", "category", "categorize"]):
                    if context.get("brand_issue_products"):
                        base_prompt += f"\n**Products with brand issues:**\n"
                        for item in context['brand_issue_products'][:10]:
                            base_prompt += f"  - SKU {item['sku']}: {item['name']} (brand: '{item['brand']}')\n"
                
                # For general queries, include sample products
                if "all_products" in context and len(context["all_products"]) > 0:
                    # Limit to first 50 products to avoid token limits
                    sample_size = min(50, len(context["all_products"]))
                    base_prompt += f"\n**Sample of {sample_size} products from database:**\n"
                    base_prompt += json.dumps(context["all_products"][:sample_size], indent=2)
        
        base_prompt += "\n\n" + "="*80 + "\n"
        base_prompt += "RESPONSE INSTRUCTIONS\n"
        base_prompt += "="*80 + "\n\n"
        base_prompt += """1. **Use System Knowledge**: Apply the business rules and data structure knowledge above
2. **Remember**: Capital ERP is the source of truth - WooCommerce should match Capital
3. **Be Specific**: Include SKUs, product names, exact counts from the data
4. **Prioritize Issues**: Use HIGH/MEDIUM/LOW severity based on system knowledge
5. **Suggest Fixes**: Explain WHAT to fix, WHY, and WHICH system needs updating
6. **Ask for Approval**: End with "Would you like me to help fix these issues?" if issues found
7. **No Data**: If data not loaded, ask user to click 'Fetch All Data'

Provide a clear, actionable response based on system knowledge and current data:
"""
        
        return base_prompt
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response (try to extract JSON)"""
        try:
            # Try to find JSON in response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                return {"raw_response": response_text}
        except json.JSONDecodeError:
            return {"raw_response": response_text}
