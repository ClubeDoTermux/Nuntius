from .openai import OpenAIProvider
from .base import ProviderRegistry


class AnthropicProvider(OpenAIProvider):
    name = "anthropic"
    default_model = "claude-sonnet-4-20250514"


ProviderRegistry.register("anthropic", AnthropicProvider)
