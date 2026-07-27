from .openai import OpenAIProvider
from .base import ProviderRegistry


class GroqProvider(OpenAIProvider):
    name = "groq"
    default_model = "llama3-70b-8192"


ProviderRegistry.register("groq", GroqProvider)
