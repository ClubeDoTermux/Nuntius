from .openai import OpenAIProvider
from .base import ProviderRegistry


class GitHubModelsProvider(OpenAIProvider):
    name = "github"
    default_model = "gpt-4o-mini"


ProviderRegistry.register("github", GitHubModelsProvider)
