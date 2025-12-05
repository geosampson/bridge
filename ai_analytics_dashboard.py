"""
AI Analytics Dashboard for BRIDGE
Displays AI-generated insights and business analytics
"""

import customtkinter as ctk
from typing import List, Dict, Any
from ai_client import BridgeAI

class AIAnalyticsDashboard(ctk.CTkFrame):
    """Dashboard displaying AI-powered analytics and insights"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.ai = BridgeAI()
        self.insights = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the analytics dashboard UI"""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header,
            text="📊 AI Analytics Dashboard",
            font=("Arial", 18, "bold")
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            header,
            text="🔄 Generate Insights",
            command=self.generate_insights,
            width=150
        ).pack(side="right", padx=5)
        
        # Main content area (scrollable)
        self.content = ctk.CTkScrollableFrame(self)
        self.content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial message
        ctk.CTkLabel(
            self.content,
            text="Click 'Generate Insights' to analyze your products with AI",
            font=("Arial", 14)
        ).pack(pady=50)
    
    def generate_insights(self):
        """Generate AI insights from products"""
        # This will be called from main app with product data
        pass
    
    def set_insights(self, insights: Dict[str, Any]):
        """Set and display insights"""
        self.insights = insights
        self.refresh_display()
    
    def refresh_display(self):
        """Refresh the dashboard display"""
        # Clear current content
        for widget in self.content.winfo_children():
            widget.destroy()
        
        if not self.insights:
            ctk.CTkLabel(
                self.content,
                text="No insights available",
                font=("Arial", 14)
            ).pack(pady=50)
            return
        
        # Display insights sections
        self._display_summary()
        self._display_top_products()
        self._display_pricing_insights()
        self._display_recommendations()
    
    def _display_summary(self):
        """Display summary statistics"""
        summary_frame = self._create_section("📈 Summary")
        
        summary_data = self.insights.get('summary', {})
        
        # Create grid of summary cards
        grid = ctk.CTkFrame(summary_frame)
        grid.pack(fill="x", padx=10, pady=10)
        
        metrics = [
            ("Total Products", summary_data.get('total_products', 0)),
            ("Avg Price", f"€{summary_data.get('avg_price', 0):.2f}"),
            ("Total Sales", summary_data.get('total_sales', 0)),
            ("Avg Discount", f"{summary_data.get('avg_discount', 0):.1f}%")
        ]
        
        for i, (label, value) in enumerate(metrics):
            card = self._create_metric_card(grid, label, value)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            grid.columnconfigure(i, weight=1)
    
    def _display_top_products(self):
        """Display top performing products"""
        top_frame = self._create_section("🏆 Top Products")
        
        top_products = self.insights.get('top_products', [])
        
        if not top_products:
            ctk.CTkLabel(top_frame, text="No data available").pack(pady=10)
            return
        
        # Create table
        for i, product in enumerate(top_products[:10], 1):
            row = ctk.CTkFrame(top_frame)
            row.pack(fill="x", padx=10, pady=2)
            
            ctk.CTkLabel(
                row,
                text=f"{i}.",
                width=30,
                font=("Arial", 11, "bold")
            ).pack(side="left", padx=5)
            
            ctk.CTkLabel(
                row,
                text=product.get('sku', ''),
                width=100,
                font=("Arial", 11)
            ).pack(side="left", padx=5)
            
            ctk.CTkLabel(
                row,
                text=product.get('name', '')[:40],
                font=("Arial", 11),
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=5)
            
            ctk.CTkLabel(
                row,
                text=f"{product.get('sales', 0)} sales",
                width=80,
                font=("Arial", 11, "bold"),
                text_color="green"
            ).pack(side="right", padx=5)
    
    def _display_pricing_insights(self):
        """Display pricing insights"""
        pricing_frame = self._create_section("💰 Pricing Insights")
        
        pricing = self.insights.get('pricing', {})
        
        insights_text = []
        
        if pricing.get('underpriced'):
            insights_text.append(f"• {len(pricing['underpriced'])} products may be underpriced")
        
        if pricing.get('overpriced'):
            insights_text.append(f"• {len(pricing['overpriced'])} products may be overpriced")
        
        if pricing.get('optimal'):
            insights_text.append(f"• {len(pricing['optimal'])} products have optimal pricing")
        
        if insights_text:
            for text in insights_text:
                ctk.CTkLabel(
                    pricing_frame,
                    text=text,
                    font=("Arial", 12),
                    anchor="w"
                ).pack(fill="x", padx=20, pady=5)
        else:
            ctk.CTkLabel(
                pricing_frame,
                text="No pricing insights available",
                font=("Arial", 12)
            ).pack(pady=10)
    
    def _display_recommendations(self):
        """Display AI recommendations"""
        rec_frame = self._create_section("💡 AI Recommendations")
        
        recommendations = self.insights.get('recommendations', [])
        
        if not recommendations:
            ctk.CTkLabel(
                rec_frame,
                text="No recommendations at this time",
                font=("Arial", 12)
            ).pack(pady=10)
            return
        
        for i, rec in enumerate(recommendations, 1):
            rec_card = ctk.CTkFrame(rec_frame)
            rec_card.pack(fill="x", padx=10, pady=5)
            
            # Priority indicator
            priority = rec.get('priority', 'low')
            priority_colors = {
                "high": "#ff4444",
                "medium": "#ffaa00",
                "low": "#4444ff"
            }
            
            indicator = ctk.CTkFrame(rec_card, width=5, fg_color=priority_colors.get(priority))
            indicator.pack(side="left", fill="y", padx=(0, 10))
            
            # Content
            content = ctk.CTkFrame(rec_card)
            content.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            ctk.CTkLabel(
                content,
                text=f"{i}. {rec.get('title', 'Recommendation')}",
                font=("Arial", 12, "bold"),
                anchor="w"
            ).pack(fill="x")
            
            ctk.CTkLabel(
                content,
                text=rec.get('description', ''),
                font=("Arial", 11),
                wraplength=600,
                justify="left",
                anchor="w"
            ).pack(fill="x", pady=(5, 0))
            
            if rec.get('expected_impact'):
                ctk.CTkLabel(
                    content,
                    text=f"Expected impact: {rec['expected_impact']}",
                    font=("Arial", 10, "italic"),
                    text_color="green",
                    anchor="w"
                ).pack(fill="x", pady=(5, 0))
    
    def _create_section(self, title: str) -> ctk.CTkFrame:
        """Create a section with title"""
        section = ctk.CTkFrame(self.content)
        section.pack(fill="x", padx=5, pady=10)
        
        ctk.CTkLabel(
            section,
            text=title,
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=5)
        
        return section
    
    def _create_metric_card(self, parent, label: str, value: Any) -> ctk.CTkFrame:
        """Create a metric card"""
        card = ctk.CTkFrame(parent)
        
        ctk.CTkLabel(
            card,
            text=str(value),
            font=("Arial", 24, "bold")
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            card,
            text=label,
            font=("Arial", 11),
            text_color="gray"
        ).pack(pady=(0, 10))
        
        return card
