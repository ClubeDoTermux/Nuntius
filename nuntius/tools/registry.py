from typing import Any, Callable
import time


_tools: dict[str, "BaseTool"] = {}

_TOOL_CACHE: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 5  # seconds


def with_cache(ttl: int = 5):
    def decorator(tool_cls):
        original_execute = tool_cls.execute
        async def cached_execute(self, **kwargs):
            key = f"{self.name}:{hash(frozenset(kwargs.items()))}"
            now = time.time()
            if key in _TOOL_CACHE:
                expiry, result = _TOOL_CACHE[key]
                if now < expiry:
                    return result + " (cached)"
            result = await original_execute(self, **kwargs)
            _TOOL_CACHE[key] = (now + ttl, result)
            return result
        tool_cls.execute = cached_execute
        return tool_cls
    return decorator


def clear_cache():
    _TOOL_CACHE.clear()


def get_cache_size() -> int:
    return len(_TOOL_CACHE)


class BaseTool:
    name: str = ""
    description: str = ""
    parameters: dict = {}

    async def execute(self, **kwargs) -> str:
        raise NotImplementedError

    def to_openai_tool(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def register(tool: BaseTool):
    _tools[tool.name] = tool


def get_all() -> list[BaseTool]:
    return list(_tools.values())


def get_openai_tools() -> list[dict]:
    return [t.to_openai_tool() for t in _tools.values()]


def get_names() -> list[str]:
    return list(_tools.keys())


async def execute(name: str, **kwargs) -> str:
    tool = _tools.get(name)
    if not tool:
        return f"Tool '{name}' not found"
    try:
        return await tool.execute(**kwargs)
    except Exception as e:
        return f"Error executing {name}: {e}"
