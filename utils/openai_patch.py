"""
This module provides patched versions of OpenAI client initialization
to handle common issues like proxies, SSL verification, etc.
"""

import os
import sys
from openai import OpenAI
import inspect

def patch_openai():
    """
    Monkey patch OpenAI client to handle proxy issues.
    This is a workaround for environments with proxy settings that
    cause issues with the OpenAI client.
    """
    try:
        original_init = OpenAI.__init__
        
        def patched_init(self, *args, **kwargs):
            # Remove problematic keyword arguments
            if 'proxies' in kwargs:
                print("Removing 'proxies' from OpenAI client initialization")
                del kwargs['proxies']
                
            # Call the original __init__ with the cleaned kwargs
            return original_init(self, *args, **kwargs)
        
        # Apply the patch
        OpenAI.__init__ = patched_init
        print("OpenAI client successfully patched to handle proxy issues")
    except Exception as e:
        print(f"Failed to patch OpenAI client: {e}")

def create_safe_client(api_key=None):
    """
    Create an OpenAI client with safe defaults that works in most environments.
    """
    # Apply patches first
    patch_openai()
    
    # Clean environment variables that might interfere
    env_vars_to_clear = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']
    original_env = {}
    
    # Save and clear proxy environment variables
    for var in env_vars_to_clear:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]
    
    try:
        # If no API key provided, try to get from environment
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
            
        if not api_key:
            print("No API key provided")
            return None
            
        # Create client with minimal settings
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        print(f"Error creating OpenAI client: {e}")
        return None
    finally:
        # Restore original environment variables
        for var, value in original_env.items():
            os.environ[var] = value

# Apply the patch when this module is imported
patch_openai() 