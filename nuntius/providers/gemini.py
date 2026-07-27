from .openai import OpenAIProvider
from .base import ProviderRegistry


class GeminiProvider(OpenAIProvider):
    name = "gemini"
    default_model = "gemini-2.0-flash"


ProviderRegistry.register("gemini", GeminiProvider)
