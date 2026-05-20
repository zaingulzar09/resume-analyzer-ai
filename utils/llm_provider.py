"""
LLM Provider Abstraction Layer
Supports multiple AI providers: OpenAI, Gemini, Grok, Claude, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import os
import json


class LLMProvider(ABC):
    """Base abstract class for LLM providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Test if the API key is valid and working"""
        pass

    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """Send a chat completion request and return the response text"""
        pass

class GroqProvider(LLMProvider):
    """Groq Cloud API provider - Fast and FREE"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        except Exception as e:
            raise Exception(f"Failed to initialize Groq client: {str(e)}")

    def test_connection(self) -> tuple[bool, str]:
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            return True, "Groq connection successful"
        except Exception as e:
            return False, f"Groq connection failed: {str(e)}"

    def chat_completion(self, messages, model=None, temperature=0.7, max_tokens=1000):
        response = self.client.chat.completions.create(
            model=model or "llama-3.3-70b-versatile",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT-3.5, GPT-4, etc.)"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            raise Exception(f"Failed to initialize OpenAI client: {str(e)}")

    def test_connection(self) -> tuple[bool, str]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, this is a test."}
                ],
                max_tokens=10
            )
            return True, "OpenAI connection successful"
        except Exception as e:
            return False, f"OpenAI connection failed: {str(e)}"

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=model or "gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI request failed: {str(e)}")

class GeminiProvider(LLMProvider):
    """Google Gemini API provider using the new google.genai SDK"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            # NEW SDK: google.genai instead of google.generativeai
            import google.genai as genai
            self.client = genai.Client(api_key=api_key)
            self.model_name = "gemini-2.0-flash-exp"  # Latest working model
        except Exception as e:
            raise Exception(f"Failed to initialize Gemini client: {str(e)}")

    def test_connection(self) -> tuple[bool, str]:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents="Hello, this is a test."
            )
            return True, "Gemini connection successful"
        except Exception as e:
            return False, f"Gemini connection failed: {str(e)}"

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        try:
            # Convert OpenAI format to Gemini contents format
            prompt = self._convert_messages_to_prompt(messages)
            
            # New SDK API: client.models.generate_content
            response = self.client.models.generate_content(
                model=model or self.model_name,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )
            return response.text
        except Exception as e:
            raise Exception(f"Gemini request failed: {str(e)}")

    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI message format to a simple prompt"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user").upper()
            content = msg.get("content", "")
            prompt_parts.append(f"{role}: {content}")
        return "\n".join(prompt_parts)

class GrokProvider(LLMProvider):
    """xAI Grok API provider"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )
        except Exception as e:
            raise Exception(f"Failed to initialize Grok client: {str(e)}")

    def test_connection(self) -> tuple[bool, str]:
        try:
            response = self.client.chat.completions.create(
                model="grok-4.3",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, this is a test."}
                ],
                max_tokens=10
            )
            return True, "Grok connection successful"
        except Exception as e:
            return False, f"Grok connection failed: {str(e)}"

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        try:
            response = self.client.chat.completions.create(
                model=model or "grok-beta",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Grok request failed: {str(e)}")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            raise Exception(f"Failed to initialize Anthropic client: {str(e)}")

    def test_connection(self) -> tuple[bool, str]:
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "Hello, this is a test."}
                ]
            )
            return True, "Anthropic connection successful"
        except Exception as e:
            return False, f"Anthropic connection failed: {str(e)}"

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        try:
            response = self.client.messages.create(
                model=model or "claude-3-sonnet-20240229",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic request failed: {str(e)}")


class LLMProviderFactory:
    """Factory for creating LLM provider instances"""

    PROVIDERS = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "groq": GroqProvider,
        "grok": GrokProvider,
        "anthropic": AnthropicProvider,
        "claude": AnthropicProvider,
    }

    @classmethod
    def get_provider(cls, provider_name: str, api_key: str) -> Optional[LLMProvider]:
        """Get a provider instance by name"""
        provider_class = cls.PROVIDERS.get(provider_name.lower())
        if not provider_class:
            return None
        try:
            return provider_class(api_key)
        except Exception as e:
            print(f"Error creating {provider_name} provider: {str(e)}")
            return None

    @classmethod
    def get_provider_from_env(cls) -> Optional[LLMProvider]:
        """Get a provider based on environment variables"""
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        # Try to get API key for the selected provider
        api_key_var = f"{provider.upper()}_API_KEY"
        api_key = os.getenv(api_key_var)
        
        if not api_key:
            print(f"No API key found for {provider} (looking for {api_key_var})")
            return None
        
        return cls.get_provider(provider, api_key)

    @classmethod
    def list_providers(cls) -> List[str]:
        """List all available providers"""
        return list(cls.PROVIDERS.keys())
