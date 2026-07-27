from .openai import OpenAIProvider
from .base import ProviderRegistry


class NvidiaProvider(OpenAIProvider):
    name = "nvidia"
    default_model = "nvidia/llama-3.1-nemotron-70b-instruct"


ProviderRegistry.register("nvidia", NvidiaProvider)
