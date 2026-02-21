"""
Abstract AI provider layer supporting Gemini, Anthropic (Claude), and OpenAI.

Provides a unified interface for generating text completions across
multiple AI providers, with a factory function for provider selection.
"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI text generation providers."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate a text completion from the given prompt.

        Args:
            prompt: The user prompt to send to the model.
            system_prompt: Optional system-level instruction for the model.

        Returns:
            The generated text response.
        """
        ...


class GeminiProvider(AIProvider):
    """Google Gemini AI provider using the google-genai SDK."""

    def __init__(self, api_key: str):
        from google import genai

        self._genai = genai
        self.client = genai.Client(api_key=api_key)
        logger.info("GeminiProvider initialized")

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        config = self._genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
        )
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=config,
        )
        return response.text


class AnthropicProvider(AIProvider):
    """Anthropic Claude AI provider."""

    def __init__(self, api_key: str):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)
        logger.info("AnthropicProvider initialized")

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.content[0].text


class OpenAIProvider(AIProvider):
    """OpenAI GPT AI provider."""

    def __init__(self, api_key: str):
        import openai

        self.client = openai.OpenAI(api_key=api_key)
        logger.info("OpenAIProvider initialized")

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content


def get_ai_provider(provider_name: str | None = None) -> AIProvider:
    """Factory function to create the appropriate AI provider.

    Args:
        provider_name: One of "gemini", "anthropic", or "openai".
            If None, uses the default from application settings.

    Returns:
        An initialized AIProvider instance.

    Raises:
        ValueError: If the provider name is unknown or the API key
            is not configured for the selected provider.
    """
    from app.config import settings

    if provider_name is None:
        provider_name = settings.default_ai_provider

    provider_name = provider_name.lower().strip()

    if provider_name == "gemini":
        api_key = settings.gemini_api_key
        if not api_key:
            raise ValueError(
                "Gemini API key not configured. Set GEMINI_API_KEY in environment."
            )
        return GeminiProvider(api_key=api_key)

    elif provider_name == "anthropic":
        api_key = settings.anthropic_api_key
        if not api_key:
            raise ValueError(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY in environment."
            )
        return AnthropicProvider(api_key=api_key)

    elif provider_name == "openai":
        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError(
                "OpenAI API key not configured. Set OPENAI_API_KEY in environment."
            )
        return OpenAIProvider(api_key=api_key)

    else:
        raise ValueError(
            f"Unknown AI provider: '{provider_name}'. "
            f"Supported providers: gemini, anthropic, openai"
        )
