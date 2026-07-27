from typing import Any, Callable


_tools: dict[str, "BaseTool"] = {}


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
