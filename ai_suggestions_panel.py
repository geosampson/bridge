"""
AI Suggestions Panel for BRIDGE
Displays AI-generated suggestions with approve/reject workflow
"""

import customtkinter as ctk
from typing import List, Dict, Callable
from ai_anomaly_detector import AnomalyDetector

class AISuggestionsPanel(ctk.CTkFrame):
    """Panel displaying AI suggestions with approve/reject buttons"""
    
    def __init__(self, parent, on_approve: Callable = None, on_reject: Callable = None):
        super().__init__(parent)
        
        self.on_approve = on_approve
        self.on_reject = on_reject
        self.anomalies = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the suggestions panel UI"""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header,
            text="🤖 AI Suggestions",
            font=("Arial", 16, "bold")
        ).pack(side="left", padx=10)
        
        self.status_label = ctk.CTkLabel(
            header,
            text="No suggestions yet",
            font=("Arial", 12)
        )
        self.status_label.pack(side="left", padx=20)
        
        # Refresh button
        ctk.CTkButton(
            header,
            text="🔄 Analyze",
            command=self.analyze_products,
            width=100
        ).pack(side="right", padx=5)
        
        # Filter buttons
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Show:").pack(side="left", padx=5)
        
        self.filter_var = ctk.StringVar(value="all")
        
        for filter_type, label in [
            ("all", "All"),
            ("high", "High Priority"),
            ("auto_fixable", "Auto-Fixable")
        ]:
            ctk.CTkRadioButton(
                filter_frame,
                text=label,
                variable=self.filter_var,
                value=filter_type,
                command=self.refresh_display
            ).pack(side="left", padx=5)
        
        # Scrollable suggestions list
        self.suggestions_frame = ctk.CTkScrollableFrame(self, height=400)
        self.suggestions_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Action buttons at bottom
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            action_frame,
            text="✓ Apply All Auto-Fixable",
            command=self.apply_all_auto_fixable,
            fg_color="green",
            width=200
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            action_frame,
            text="✗ Dismiss All",
            command=self.dismiss_all,
            fg_color="gray",
            width=150
        ).pack(side="left", padx=5)
    
    def analyze_products(self):
        """Trigger AI analysis of products"""
        # This will be called from main app
        pass
    
    def set_anomalies(self, anomalies: List[Dict]):
        """Set anomalies to display"""
        self.anomalies = anomalies
        self.refresh_display()
        
        # Update status
        summary = self._get_summary()
        self.status_label.configure(
            text=f"Found {summary['total']} issues: {summary['high']} high, {summary['medium']} medium, {summary['low']} low"
        )
    
    def refresh_display(self):
        """Refresh the suggestions display based on current filter"""
        # Clear current suggestions
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()
        
        # Filter anomalies
        filter_type = self.filter_var.get()
        filtered = self._filter_anomalies(filter_type)
        
        if not filtered:
            ctk.CTkLabel(
                self.suggestions_frame,
                text="No suggestions match the current filter",
                font=("Arial", 12)
            ).pack(pady=20)
            return
        
        # Display each anomaly
        for i, anomaly in enumerate(filtered):
            self._create_suggestion_card(anomaly, i)
    
    def _filter_anomalies(self, filter_type: str) -> List[Dict]:
        """Filter anomalies based on type"""
        if filter_type == "all":
            return self.anomalies
        elif filter_type == "high":
            return [a for a in self.anomalies if a.get('severity') == 'high']
        elif filter_type == "auto_fixable":
            return [a for a in self.anomalies if a.get('auto_fixable', False)]
        return self.anomalies
    
    def _create_suggestion_card(self, anomaly: Dict, index: int):
        """Create a card for a single suggestion"""
        # Card frame
        card = ctk.CTkFrame(self.suggestions_frame)
        card.pack(fill="x", padx=5, pady=5)
        
        # Severity indicator
        severity = anomaly.get('severity', 'low')
        severity_colors = {
            "high": "#ff4444",
            "medium": "#ffaa00",
            "low": "#4444ff"
        }
        
        indicator = ctk.CTkFrame(card, width=5, fg_color=severity_colors.get(severity))
        indicator.pack(side="left", fill="y", padx=(0, 10))
        
        # Content
        content = ctk.CTkFrame(card)
        content.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        # SKU and type
        header_text = f"SKU: {anomaly.get('sku')} • {anomaly.get('type', 'unknown').replace('_', ' ').title()}"
        ctk.CTkLabel(
            content,
            text=header_text,
            font=("Arial", 12, "bold")
        ).pack(anchor="w")
        
        # Description
        ctk.CTkLabel(
            content,
            text=anomaly.get('description', ''),
            font=("Arial", 11),
            wraplength=500,
            justify="left"
        ).pack(anchor="w", pady=(5, 0))
        
        # Suggested fix
        fix_text = f"💡 {anomaly.get('suggested_fix', 'No suggestion')}"
        ctk.CTkLabel(
            content,
            text=fix_text,
            font=("Arial", 11, "italic"),
            text_color="green",
            wraplength=500,
            justify="left"
        ).pack(anchor="w", pady=(5, 0))
        
        # Action buttons
        actions = ctk.CTkFrame(card)
        actions.pack(side="right", padx=10)
        
        if anomaly.get('auto_fixable', False):
            ctk.CTkButton(
                actions,
                text="✓ Apply",
                command=lambda: self.approve_suggestion(anomaly),
                fg_color="green",
                width=80,
                height=30
            ).pack(side="top", pady=2)
        
        ctk.CTkButton(
            actions,
            text="✗ Dismiss",
            command=lambda: self.reject_suggestion(anomaly),
            fg_color="gray",
            width=80,
            height=30
        ).pack(side="top", pady=2)
    
    def approve_suggestion(self, anomaly: Dict):
        """Approve and apply a suggestion"""
        if self.on_approve:
            self.on_approve(anomaly)
        
        # Remove from list
        self.anomalies = [a for a in self.anomalies if a != anomaly]
        self.refresh_display()
    
    def reject_suggestion(self, anomaly: Dict):
        """Reject a suggestion"""
        if self.on_reject:
            self.on_reject(anomaly)
        
        # Remove from list
        self.anomalies = [a for a in self.anomalies if a != anomaly]
        self.refresh_display()
    
    def apply_all_auto_fixable(self):
        """Apply all auto-fixable suggestions"""
        auto_fixable = [a for a in self.anomalies if a.get('auto_fixable', False)]
        
        if not auto_fixable:
            return
        
        # Confirm
        if ctk.CTkInputDialog(
            text=f"Apply {len(auto_fixable)} auto-fixable suggestions?",
            title="Confirm"
        ).get_input():
            for anomaly in auto_fixable:
                if self.on_approve:
                    self.on_approve(anomaly)
            
            # Remove from list
            self.anomalies = [a for a in self.anomalies if not a.get('auto_fixable', False)]
            self.refresh_display()
    
    def dismiss_all(self):
        """Dismiss all suggestions"""
        if ctk.CTkInputDialog(
            text=f"Dismiss all {len(self.anomalies)} suggestions?",
            title="Confirm"
        ).get_input():
            self.anomalies = []
            self.refresh_display()
    
    def _get_summary(self) -> Dict[str, int]:
        """Get summary of anomalies"""
        summary = {"total": len(self.anomalies), "high": 0, "medium": 0, "low": 0}
        for a in self.anomalies:
            severity = a.get('severity', 'low')
            summary[severity] = summary.get(severity, 0) + 1
        return summary
