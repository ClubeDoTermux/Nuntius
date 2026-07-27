from .openai import OpenAIProvider
from .base import ProviderRegistry


class OllamaProvider(OpenAIProvider):
    name = "ollama"
    default_model = "llama3.2"


ProviderRegistry.register("ollama", OllamaProvider)
