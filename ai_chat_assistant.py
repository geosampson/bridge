"""
AI Chat Assistant for BRIDGE
Natural language interface for product management
"""

import customtkinter as ctk
from typing import Dict, Any
from ai_client import BridgeAI
import threading

class AIChatAssistant(ctk.CTkFrame):
    """Chat interface for AI assistant"""
    
    def __init__(self, parent, get_context: callable = None, execute_action: callable = None):
        super().__init__(parent)
        
        self.ai = BridgeAI()
        self.get_context = get_context  # Function to get current app context
        self.execute_action = execute_action  # Function to execute approved actions
        self.chat_history = []
        self.pending_actions = []  # Store suggested actions awaiting approval
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the chat assistant UI"""
        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header,
            text="💬 AI Assistant",
            font=("Arial", 18, "bold")
        ).pack(side="left", padx=10)
        
        self.status_label = ctk.CTkLabel(
            header,
            text="Ready" if self.ai.is_available() else "Not configured",
            font=("Arial", 12),
            text_color="green" if self.ai.is_available() else "red"
        )
        self.status_label.pack(side="left", padx=20)
        
        ctk.CTkButton(
            header,
            text="🗑️ Clear Chat",
            command=self.clear_chat,
            width=100
        ).pack(side="right", padx=5)
        
        # Chat display area
        self.chat_display = ctk.CTkTextbox(
            self,
            wrap="word",
            font=("Arial", 12)
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=10)
        self.chat_display.configure(state="disabled")
        
        # Input area
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        self.input_field = ctk.CTkEntry(
            input_frame,
            placeholder_text="Ask me anything about your products...",
            font=("Arial", 12)
        )
        self.input_field.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_field.bind("<Return>", lambda e: self.send_message())
        
        self.send_button = ctk.CTkButton(
            input_frame,
            text="Send",
            command=self.send_message,
            width=100
        )
        self.send_button.pack(side="right")
        
        # Quick actions
        quick_frame = ctk.CTkFrame(self)
        quick_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(quick_frame, text="Quick actions:").pack(side="left", padx=5)
        
        quick_actions = [
            ("Find issues", "Find all products with price or data issues"),
            ("Top products", "Show me the top 10 best-selling products"),
            ("Price analysis", "Analyze pricing across all products"),
            ("Suggestions", "Give me suggestions for improving my products")
        ]
        
        for label, prompt in quick_actions:
            ctk.CTkButton(
                quick_frame,
                text=label,
                command=lambda p=prompt: self.send_quick_action(p),
                width=100,
                height=25,
                font=("Arial", 10)
            ).pack(side="left", padx=2)
        
        # Welcome message
        if self.ai.is_available():
            self._add_message("AI", "Hello! I'm your AI assistant. I can help you analyze products, find issues, and provide insights. What would you like to know?")
        else:
            self._add_message("System", "AI assistant is not configured. Please add your Claude API key in Settings to enable AI features.")
    
    def send_message(self):
        """Send user message to AI"""
        message = self.input_field.get().strip()
        if not message:
            return
        
        # Clear input
        self.input_field.delete(0, "end")
        
        # Add user message to chat
        self._add_message("You", message)
        
        # Show typing indicator
        self.status_label.configure(text="Thinking...", text_color="orange")
        self.send_button.configure(state="disabled")
        
        # Get AI response in background
        threading.Thread(target=self._get_ai_response, args=(message,), daemon=True).start()
    
    def send_quick_action(self, prompt: str):
        """Send a quick action prompt"""
        self.input_field.delete(0, "end")
        self.input_field.insert(0, prompt)
        self.send_message()
    
    def _get_ai_response(self, message: str):
        """Get AI response (runs in background thread)"""
        try:
            # Check for approval keywords
            message_lower = message.lower().strip()
            if message_lower in ["yes", "y", "approve", "proceed", "do it", "go ahead"]:
                if self.pending_actions:
                    self.after(0, self.execute_pending_actions)
                    self.after(0, lambda: self.status_label.configure(text="Ready", text_color="green"))
                    self.after(0, lambda: self.send_button.configure(state="normal"))
                    return
            
            if message_lower in ["no", "n", "cancel", "stop", "don't", "dont"]:
                if self.pending_actions:
                    self.after(0, self.cancel_pending_actions)
                    self.after(0, lambda: self.status_label.configure(text="Ready", text_color="green"))
                    self.after(0, lambda: self.send_button.configure(state="normal"))
                    return
            
            # Get current context
            context = self.get_context() if self.get_context else None
            
            # Get AI response
            response = self.ai.chat(message, context)
            
            # Add to chat (must be done in main thread)
            self.after(0, lambda: self._add_message("AI", response))
            self.after(0, lambda: self.status_label.configure(text="Ready", text_color="green"))
            self.after(0, lambda: self.send_button.configure(state="normal"))
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.after(0, lambda: self._add_message("System", error_msg))
            self.after(0, lambda: self.status_label.configure(text="Error", text_color="red"))
            self.after(0, lambda: self.send_button.configure(state="normal"))
    
    def _add_message(self, sender: str, message: str):
        """Add a message to the chat display"""
        self.chat_history.append({"sender": sender, "message": message})
        
        # Enable editing
        self.chat_display.configure(state="normal")
        
        # Add sender label
        if sender == "You":
            self.chat_display.insert("end", f"\n{sender}: ", "user")
        elif sender == "AI":
            self.chat_display.insert("end", f"\n{sender}: ", "ai")
        else:
            self.chat_display.insert("end", f"\n{sender}: ", "system")
        
        # Add message
        self.chat_display.insert("end", f"{message}\n")
        
        # Configure tags for styling (font removed for Windows compatibility)
        self.chat_display.tag_config("user", foreground="#4444ff")
        self.chat_display.tag_config("ai", foreground="#00aa00")
        self.chat_display.tag_config("system", foreground="#888888")
        
        # Disable editing
        self.chat_display.configure(state="disabled")
        
        # Scroll to bottom
        self.chat_display.see("end")
    
    def clear_chat(self):
        """Clear chat history"""
        self.chat_history = []
        self.pending_actions = []
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        
        if self.ai.is_available():
            self._add_message("AI", "Chat cleared. How can I help you?")
    
    def show_action_approval(self, actions: list):
        """Show action approval dialog"""
        if not actions:
            return
        
        # Store pending actions
        self.pending_actions = actions
        
        # Create approval message
        approval_msg = "\n\n🔧 **Suggested Actions:**\n"
        for i, action in enumerate(actions, 1):
            approval_msg += f"{i}. {action.get('description', 'Unknown action')}\n"
        approval_msg += "\nWould you like me to proceed with these actions? (Reply 'yes' to approve, 'no' to cancel)"
        
        self._add_message("AI", approval_msg)
    
    def execute_pending_actions(self):
        """Execute all pending actions after user approval"""
        if not self.pending_actions:
            self._add_message("System", "No pending actions to execute.")
            return
        
        if not self.execute_action:
            self._add_message("System", "Action execution is not available. Please use the manual tools in other tabs.")
            return
        
        self._add_message("System", f"Executing {len(self.pending_actions)} actions...")
        
        # Execute actions (this would call back to the main app)
        for action in self.pending_actions:
            action_type = action.get('type')
            action_data = action.get('data', {})
            
            try:
                result = self.execute_action(action_type, action_data)
                self._add_message("System", f"✓ {action.get('description')}: {result}")
            except Exception as e:
                self._add_message("System", f"✗ {action.get('description')}: Failed - {str(e)}")
        
        self.pending_actions = []
        self._add_message("AI", "All actions completed. Is there anything else I can help with?")
    
    def cancel_pending_actions(self):
        """Cancel pending actions"""
        count = len(self.pending_actions)
        self.pending_actions = []
        self._add_message("System", f"Cancelled {count} pending action(s).")
