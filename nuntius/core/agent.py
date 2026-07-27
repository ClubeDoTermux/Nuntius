import json

from ..config import load_config, get_active_provider
from ..memory.store import MemoryStore
from ..providers.openai import OpenAIProvider, ProviderError
from ..skills.manager import SkillsManager
from ..tools import registry

MAX_TOOL_CYCLES = 25


class Agent:
    def __init__(self):
        self.config = load_config()
        provider_cfg = get_active_provider(self.config)
        self.provider = OpenAIProvider(
            api_key=provider_cfg.get("api_key", ""),
            base_url=provider_cfg.get("base_url", "https://api.openai.com/v1"),
        )
        self.model = self.config.get("model", "gpt-4o-mini")
        self.memory = None
        self.conv_id = None
        self.skills = SkillsManager()
        self._tool_cycle = 0
        self.system_prompt = ""
        self.messages: list[dict] = []

        self.mcp_manager = None
        self._init_mcp()

        if self.config.get("memory", {}).get("enabled", True):
            self.memory = MemoryStore(self.config["memory"]["db_path"])
            self.conv_id = self.memory.create_conversation()

    def _init_mcp(self):
        mcp_cfg = self.config.get("mcp_servers", {})
        enabled = {k: v for k, v in mcp_cfg.items() if isinstance(v, dict) and v.get("enabled")}
        if enabled:
            try:
                from ..providers.mcp import MCPManager
                self.mcp_manager = MCPManager()
                for name, cfg in enabled.items():
                    self.mcp_manager.add_server(
                        name,
                        cfg.get("command", ""),
                        cfg.get("args", []),
                    )
            except Exception:
                pass

    def _ensure_system_prompt(self):
        if self.system_prompt:
            return
        skills_text = self.skills.to_system_prompt()
        tools_list = "\n".join(f"- {t.name}: {t.description}" for t in registry.get_all())

        mcp_tools = ""
        if self.mcp_manager:
            mcp_tools = "\n## MCP Tools\nTools loaded from external MCP servers."

        parts = [
            "You are Nuntius, a professional AI software engineering agent integrated directly into the user's terminal.",
            "You operate in a Unix-like environment (Termux/Linux/macOS) with full shell access, Python, Node.js, and git.",
            "",
            "## Your Capabilities",
            "- Create, read, edit, move, copy, delete files and directories",
            "- Execute Python, JavaScript, shell commands, and any programming language installed on the system",
            "- Install packages (pip, npm, apt, pkg, etc.)",
            "- Initialize and manage git repositories",
            "- Search the web and fetch URLs",
            "- Interact with GitHub (repos, issues) and Google Drive",
            "- Build complete projects: websites, apps, scripts, APIs, databases",
            "",
            "## How to Create Projects",
            "When asked to create a project (website, app, etc.):",
            "  1. Plan the structure first (list the files you will create)",
            "  2. Use the [bold]write[/bold] tool to create each file with complete content",
            "  3. Use [bold]run_shell[/bold] or [bold]bash[/bold] to set up dependencies (npm install, pip install, etc.)",
            "  4. Test the project using [bold]run_shell[/bold] or [bold]run_python[/bold]",
            "  IMPORTANT: Always create FULL, COMPLETE files. Never leave placeholders.",
            "",
            "## Programming Languages",
            "You can write and execute code in any language available on the system:",
            "- Python, JavaScript/Node.js, TypeScript, Go, Rust, C/C++, Java, Ruby, PHP, Shell/Bash, and more",
            "- For languages without a dedicated tool, use [bold]run_shell[/bold] (e.g., `go run main.go`, `rustc main.rs && ./main`)",
            "",
            "## Rules",
            "- Respond in the same language as the user (Portuguese, English, etc.)",
            "- Be concise, practical, and thorough",
            "- Always create COMPLETE files with all necessary code",
            "- For complex projects, show a plan before executing",
            "- Use [bold]write[/bold] for creating files, NOT shell redirection (echo > file)",
            "- Use [bold]run_shell[/bold] for commands, [bold]run_python[/bold] for Python code",
            "- If a command fails, try to fix it and retry",
            "- You have unrestricted shell access — use it to be productive",
            "",
            f"## Available Tools\n{tools_list}",
            mcp_tools,
            skills_text,
        ]
        self.system_prompt = "\n\n".join(p for p in parts if p)
        sys_msg = {"role": "system", "content": self.system_prompt}
        if not self.messages or self.messages[0].get("role") != "system":
            self.messages.insert(0, sys_msg)

    def _add_message(self, role: str, content: str = "", tool_calls: list = None):
        self._ensure_system_prompt()
        msg = {"role": role, "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)
        if self.memory and self.conv_id:
            self.memory.add_message(self.conv_id, role, content, tool_calls)

    def _add_tool_result(self, tool_call_id: str, name: str, content: str):
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
        })
        if self.memory and self.conv_id:
            self.memory.add_message(self.conv_id, "tool", f"[{name}] {content}")

    def reset_conversation(self):
        self.messages.clear()
        self.system_prompt = ""
        self._tool_cycle = 0
        if self.memory:
            self.conv_id = self.memory.create_conversation()

    async def chat(self, user_input: str) -> str:
        if user_input:
            self._add_message("user", user_input)
        tools = registry.get_openai_tools() if self.config.get("tools", {}).get("enabled", True) else None

        full_response = ""
        self._tool_cycle = 0
        while self._tool_cycle < MAX_TOOL_CYCLES:
            self._tool_cycle += 1
            response = await self.provider.chat_completion(
                messages=self.messages,
                model=self.model,
                tools=tools,
            )
            choice = response["choices"][0]
            msg = choice["message"]

            if msg.get("tool_calls"):
                self._add_message(
                    role="assistant",
                    content=msg.get("content") or "",
                    tool_calls=msg["tool_calls"],
                )
                for tc in msg["tool_calls"]:
                    fn = tc["function"]
                    args = json.loads(fn.get("arguments", "{}"))
                    result = await registry.execute(fn["name"], **args)
                    self._add_tool_result(tc["id"], fn["name"], result)
            else:
                content = msg.get("content", "")
                self._add_message("assistant", content)
                full_response += content
                break

        return full_response

    async def stream_chat(self, user_input: str):
        if user_input:
            self._add_message("user", user_input)
        tools = registry.get_openai_tools() if self.config.get("tools", {}).get("enabled", True) else None

        full_response = ""
        self._tool_cycle = 0
        while self._tool_cycle < MAX_TOOL_CYCLES:
            self._tool_cycle += 1
            collected_content = ""
            tool_calls_data = []

            async for chunk in self.provider.stream_chat(
                messages=self.messages,
                model=self.model,
                tools=tools,
            ):
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                if delta.get("content"):
                    collected_content += delta["content"]
                    yield {"type": "content", "data": delta["content"]}
                if delta.get("tool_calls"):
                    for tc in delta["tool_calls"]:
                        tool_calls_data.append(tc)

            if tool_calls_data:
                self._add_message("assistant", collected_content, tool_calls_data)
                for tc in tool_calls_data:
                    fn = tc.get("function", {})
                    name = fn.get("name", "")
                    args_raw = fn.get("arguments", "{}")
                    try:
                        args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                    except json.JSONDecodeError:
                        args = {}
                    yield {"type": "tool_start", "data": f"{name}({args})"}
                    result = await registry.execute(name, **args)
                    self._add_tool_result(tc.get("id", ""), name, result)
                    yield {"type": "tool_end", "data": (name, result)}
            else:
                self._add_message("assistant", collected_content)
                full_response = collected_content
                break

        yield {"type": "done", "data": full_response}

    def learn_from_interaction(self, user_input: str, response: str):
        if self.config.get("auto_learn", {}).get("enabled", False):
            self.skills.learn_from_conversation(user_input[:100], response[:500])

    async def close(self):
        await self.provider.close()
        if self.mcp_manager:
            await self.mcp_manager.close_all()
