import os
from dotenv import load_dotenv, find_dotenv
from utils.llm_provider import LLMProviderFactory

# Force reload .env at module load
from dotenv import load_dotenv
load_dotenv(override=True)
print(f"📋 LLM_PROVIDER from env: {os.getenv('LLM_PROVIDER')}")
print(f"📋 GROQ_API_KEY from env: {os.getenv('GROQ_API_KEY')[:20]}...")  # Shows first 20 chars

# Load environment variables from project root or fallback to static/.env
env_loaded = load_dotenv(find_dotenv())
if not env_loaded:
    fallback_env = os.path.join(os.path.dirname(__file__), '..', 'static', '.env')
    fallback_env = os.path.normpath(fallback_env)
    if os.path.exists(fallback_env):
        load_dotenv(fallback_env)


def validate_llm_provider():
    """
    Validates the configured LLM provider from environment variables.
    Returns a tuple (status, message, provider) where status is one of:
      - 'valid'   : provider works and API requests succeed
      - 'warning' : provider is present but API request failed due to quota/rate limits
      - 'invalid' : provider not configured or key missing
    """
    provider_name = os.getenv("LLM_PROVIDER", "groq").lower()  # CHANGED: default to groq
    
    # Special handling for Groq (uses different env var name)
    if provider_name == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "invalid", "GROQ_API_KEY not found in environment. Get your free key from console.groq.com", None
    else:
        api_key_var = f"{provider_name.upper()}_API_KEY"
        api_key = os.getenv(api_key_var)
    
    if not api_key:
        return "invalid", f"API key not found for {provider_name}. Set {provider_name.upper()}_API_KEY in environment.", None
    
    provider = LLMProviderFactory.get_provider(provider_name, api_key)
    if not provider:
        return "invalid", f"Failed to initialize {provider_name} provider", None
    
    # Test connection
    is_connected, test_message = provider.test_connection()
    if is_connected:
        return "valid", f"{provider_name.capitalize()} connection successful", provider
    
    # Check if it's a quota/rate limit error
    error_text = test_message.lower()
    if any(token in error_text for token in ["insufficient_quota", "quota", "rate_limit", "429"]):
        return "warning", f"{provider_name.capitalize()} is valid but quota exceeded: {test_message}", None
    
    return "invalid", f"{provider_name.capitalize()} connection failed: {test_message}", None


def get_llm_provider():
    """
    Gets an initialized LLM provider if configured and valid.
    Returns None if the provider is invalid or not currently usable.
    """
    status, message, provider = validate_llm_provider()
    if status == "valid":
        print(f"✅ {message}")  # ADDED: success message
        return provider
    else:
        print(f"⚠️ Warning: {message}")
        return None


# Legacy support for OpenAI-specific code
def validate_openai_api_key():
    """Legacy: use validate_llm_provider() instead"""
    status, message, provider = validate_llm_provider()
    return status, message, provider


def get_openai_client():
    """Legacy: use get_llm_provider() instead"""
    return get_llm_provider()