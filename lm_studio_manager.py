#!/usr/bin/env python3
"""
Script to manage models in LM Studio via HTTP API.
Allows listing, loading and unloading models automatically.
"""

import requests
import time
from typing import List, Dict, Optional
import argparse
import sys


class LMStudioManager:
    """Client to manage models in LM Studio."""
    
    def __init__(self, base_url: str = "http://192.168.159.104:1234"):
        """
        Initialize the LM Studio client.
        
        Args:
            base_url: Base URL of LM Studio server (without /v1)
        """
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/v1"
        self.models_endpoint = f"{self.api_base}/models"
        
    def check_server(self) -> bool:
        """
        Verify if the LM Studio server is active.
        
        Returns:
            True if the server responds, False otherwise
        """
        try:
            response = requests.get(self.models_endpoint, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: Cannot connect to LM Studio at {self.base_url}")
            print(f"   Details: {e}")
            return False
    
    def list_models(self) -> List[Dict]:
        """
        List all available models in LM Studio.
        
        Returns:
            List of dictionaries with model information
        """
        try:
            response = requests.get(self.models_endpoint, timeout=10)
            response.raise_for_status()
            data = response.json()
            models = data.get('data', [])
            return models
        except requests.exceptions.RequestException as e:
            print(f"❌ Error listing models: {e}")
            return []
    
    def get_loaded_model(self) -> Optional[str]:
        """
        Get the model currently loaded in memory.
        
        Returns:
            Name of the loaded model or None if there is none
        """
        models = self.list_models()
        if models:
            # LM Studio typically returns the loaded model in the first position
            return models[0].get('id')
        return None
    
    def load_model(self, model_path: str, timeout: int = 60) -> bool:
        """
        Load a model into memory via a test request.
        
        Note: LM Studio loads models automatically when making requests.
        This function makes a minimal request to force loading.
        
        Args:
            model_path: Path or ID of the model to load
            timeout: Maximum wait time in seconds
            
        Returns:
            True if the model was loaded successfully
        """
        print(f"🔄 Attempting to load model: {model_path}")
        
        chat_endpoint = f"{self.api_base}/chat/completions"
        payload = {
            "model": model_path,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                chat_endpoint,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Verify that the model is loaded
            time.sleep(2)  # Give time for loading to complete
            loaded = self.get_loaded_model()
            
            if loaded:
                print(f"✅ Model loaded successfully: {loaded}")
                return True
            else:
                print(f"⚠️  Warning: The model may not have loaded correctly")
                return False
                
        except requests.exceptions.Timeout:
            print(f"❌ Timeout loading model (>{timeout}s)")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def unload_model(self) -> bool:
        """
        Attempt to unload the current model from memory.
        
        Note: LM Studio does not have an official endpoint to unload models.
        This function is a placeholder - unloading must be done from the UI.
        
        Returns:
            False (not directly supported by the API)
        """
        print("⚠️  LM Studio does not provide an API endpoint to unload models.")
        print("   You must do it manually from the LM Studio interface.")
        return False
    
    def print_models_info(self):
        """Print detailed information about available models."""
        if not self.check_server():
            return
            
        print("\n📋 Available models in LM Studio:")
        print("-" * 80)
        
        models = self.list_models()
        if not models:
            print("  No models found.")
            return
        
        for idx, model in enumerate(models, 1):
            model_id = model.get('id', 'Unknown')
            created = model.get('created', 'N/A')
            owned_by = model.get('owned_by', 'N/A')
            
            print(f"\n  {idx}. {model_id}")
            print(f"     Owner: {owned_by}")
            print(f"     Created: {created}")
            
            if idx == 1:
                print(f"     Status: ✅ LOADED IN MEMORY")
        
        print("\n" + "-" * 80)


def main():
    """Main script function."""
    parser = argparse.ArgumentParser(
        description='Model manager for LM Studio',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  %(prog)s --list                           # List available models
  %(prog)s --load "model-name"              # Load a specific model
  %(prog)s --url http://192.168.1.10:1234   # Use remote server
        """
    )
    
    parser.add_argument(
        '--url',
        default='http://localhost:1234',
        help='LM Studio server URL (default: http://localhost:1234)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available models'
    )
    
    parser.add_argument(
        '--load',
        metavar='MODEL',
        help='Load a specific model into memory'
    )
    
    parser.add_argument(
        '--unload',
        action='store_true',
        help='Unload the current model (requires UI)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show the currently loaded model'
    )
    
    args = parser.parse_args()
    
    # Create manager instance
    manager = LMStudioManager(base_url=args.url)
    
    # Verify connection
    if not manager.check_server():
        print("\n💡 Make sure LM Studio is running and the local server is active.")
        sys.exit(1)
    
    # Execute commands
    if args.list:
        manager.print_models_info()
    
    elif args.load:
        manager.load_model(args.load)
    
    elif args.unload:
        manager.unload_model()
    
    elif args.status:
        loaded = manager.get_loaded_model()
        if loaded:
            print(f"✅ Currently loaded model: {loaded}")
        else:
            print("⚠️  No model loaded in memory")
    
    else:
        # No arguments, show general information
        print("🔍 Checking LM Studio status...")
        manager.print_models_info()
        print("\nUse --help to see all available options.")


if __name__ == "__main__":
    main()
