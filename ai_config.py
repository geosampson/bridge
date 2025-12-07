"""
AI Configuration for BRIDGE
Handles Claude API integration and AI-powered features
"""

import os
import json
from pathlib import Path

class AIConfig:
    """Configuration for AI features"""
    
    def __init__(self):
        self.config_file = Path.home() / ".bridge" / "ai_config.json"
        self.config = self.load_config()
        
    def load_config(self):
        """Load AI configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                "enabled": True,
                "api_provider": "claude",  # claude, openai, local
                "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                "model": "claude-sonnet-4-5-20250929",  # Claude Sonnet 4.5 (current)
                "features": {
                    "anomaly_detection": True,
                    "auto_suggestions": True,
                    "analytics": True,
                    "chat_assistant": True
                },
                "auto_fix": False,  # AI suggests, user approves
                "analysis_frequency": "on_demand",  # on_demand, auto, scheduled
            }
    
    def save_config(self):
        """Save configuration to file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def set_api_key(self, api_key):
        """Set Claude API key"""
        self.config["api_key"] = api_key
        self.config["enabled"] = True
        self.save_config()
    
    def is_enabled(self):
        """Check if AI features are enabled"""
        return self.config.get("enabled", False) and bool(self.config.get("api_key"))
    
    def get_api_key(self):
        """Get API key from config or environment"""
        return self.config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
    
    def get_model(self):
        """Get AI model name"""
        return self.config.get("model", "claude-sonnet-4-5-20250929")
    
    def is_feature_enabled(self, feature):
        """Check if specific feature is enabled"""
        return self.config.get("features", {}).get(feature, False)
