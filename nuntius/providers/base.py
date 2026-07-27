from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional


class ProviderRegistry:
    _providers: dict[str, type] = {}

    @classmethod
    def register(cls, name: str, provider_cls: type):
        cls._providers[name] = provider_cls

    @classmethod
    def get(cls, name: str) -> type:
        return cls._providers.get(name)

    @classmethod
    def list(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def create(cls, name: str, api_key: str = "", base_url: str = ""):
        provider_cls = cls.get(name)
        if not provider_cls:
            raise ValueError(f"Provider desconhecido: '{name}'. Registrados: {', '.join(cls.list())}")
        return provider_cls(api_key=api_key, base_url=base_url)


class BaseProvider(ABC):
    name: str = ""
    default_model: str = ""

    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict],
        model: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
    ) -> dict:
        ...

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[dict],
        model: str,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[dict, None]:
        ...

    @abstractmethod
    async def close(self):
        ...
