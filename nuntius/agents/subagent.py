import json
import logging

from ..config import load_config, get_active_provider
from ..providers.base import ProviderRegistry

logger = logging.getLogger("nuntius.subagent")
MAX_TOOL_CYCLES = 15

SYSTEM_PROMPTS = {
    "code": "You are a code specialist. Write clean, correct code. Test your work. Be thorough.",
    "shell": "You are a shell specialist. Use shell commands to accomplish tasks efficiently.",
    "search": "You are a research specialist. Search the web, read documentation, find answers.",
    "writer": "You are a writing specialist. Write clear, well-structured content.",
    "debug": "You are a debugging specialist. Find bugs, analyze errors, suggest fixes.",
}


class SubAgent:
    def __init__(
        self,
        role: str = "",
        system_prompt: str = "",
        tools: list[str] | None = None,
        provider=None,
        model: str = "",
        config: dict | None = None,
        provider_name: str = "",
    ):
        self.role = role or "assistant"
        self.config = config or load_config()
        self.messages: list[dict] = []
        self.tool_names = tools

        if system_prompt:
            self.system_prompt = system_prompt
        elif role in SYSTEM_PROMPTS:
            self.system_prompt = SYSTEM_PROMPTS[role]
        else:
            self.system_prompt = "You are a helpful AI assistant."

        if provider:
            self.provider = provider
            self._provider_name = provider_name or self.config.get("provider", "openai")
        else:
            pname = provider_name or self.config.get("provider", "openai")
            provider_cfg = self.config.get("providers", {}).get(pname, get_active_provider(self.config))
            self.provider = ProviderRegistry.create(
                pname,
                api_key=provider_cfg.get("api_key", ""),
                base_url=provider_cfg.get("base_url", ""),
            )
            self._provider_name = pname

        self.model = model or self.config.get("model", "gpt-4o-mini")
        if provider_name:
            role_cfg = self.config.get("routing", {}).get("roles", {}).get(role, {})
            if not model and role_cfg.get("model"):
                self.model = role_cfg["model"]

        sys_msg = {"role": "system", "content": self.system_prompt}
        self.messages.append(sys_msg)

    def _get_tools(self):
        from ..tools import registry
        if self.tool_names is None:
            return registry.get_openai_tools()
        all_tools = registry.get_all()
        filtered = [t for t in all_tools if t.name in self.tool_names]
        return [t.to_openai_tool() for t in filtered]

    def _filtered_tools_list(self) -> str:
        from ..tools import registry
        if self.tool_names is None:
            all_t = registry.get_all()
            return "\n".join(f"- {t.name}: {t.description}" for t in all_t)
        all_t = registry.get_all()
        filtered = [t for t in all_t if t.name in self.tool_names]
        if not filtered:
            return "(nenhuma ferramenta disponivel)"
        return "\n".join(f"- {t.name}: {t.description}" for t in filtered)

    @property
    def provider_name(self) -> str:
        return getattr(self, "_provider_name", self.config.get("provider", "openai"))

    async def run(self, task: str, stream: bool = False) -> str:
        self.messages.append({"role": "user", "content": task})
        tools = self._get_tools()
        full_response = ""
        cycle = 0

        while cycle < MAX_TOOL_CYCLES:
            cycle += 1
            response = await self.provider.chat_completion(
                messages=self.messages,
                model=self.model,
                tools=tools,
            )
            choice = response["choices"][0]
            msg = choice["message"]

            if msg.get("tool_calls"):
                self.messages.append({
                    "role": "assistant",
                    "content": msg.get("content") or "",
                    "tool_calls": msg["tool_calls"],
                })
                for tc in msg["tool_calls"]:
                    fn = tc["function"]
                    args = json.loads(fn.get("arguments", "{}"))
                    result = await self._execute_tool(fn["name"], **args)
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    })
            else:
                content = msg.get("content", "")
                self.messages.append({"role": "assistant", "content": content})
                full_response += content
                break

        return full_response

    async def _execute_tool(self, name: str, **kwargs) -> str:
        from ..tools import registry
        result = await registry.execute(name, **kwargs)
        ok = not (
            result.lower().startswith("erro")
            or result.lower().startswith("error")
            or "not found" in result.lower()
        )
        if not ok:
            result = f"[TOOL FAILED] {result}"
        return result

    async def close(self):
        await self.provider.close()
