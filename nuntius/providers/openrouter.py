from .openai import OpenAIProvider
from .base import ProviderRegistry


class OpenRouterProvider(OpenAIProvider):
    name = "openrouter"
    default_model = "openai/gpt-4o-mini"


ProviderRegistry.register("openrouter", OpenRouterProvider)
