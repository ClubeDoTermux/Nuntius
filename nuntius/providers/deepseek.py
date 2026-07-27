from .openai import OpenAIProvider
from .base import ProviderRegistry


class DeepSeekProvider(OpenAIProvider):
    name = "deepseek"
    default_model = "deepseek-chat"


ProviderRegistry.register("deepseek", DeepSeekProvider)
