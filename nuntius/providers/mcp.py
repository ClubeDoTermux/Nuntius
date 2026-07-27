import asyncio
import json
import shutil
from pathlib import Path


class MCPServer:
    def __init__(self, name: str, command: str, args: list[str] | None = None):
        self.name = name
        self.command = shutil.which(command.split()[0])
        self.args = args or []
        self._process: asyncio.subprocess.Process | None = None
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._request_id = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._tools: list[dict] = []
        self._running = False

    async def connect(self):
        if self._running:
            return
        if not self.command:
            raise RuntimeError(f"MCP server '{self.name}': command not found")
        self._process = await asyncio.create_subprocess_exec(
            self.command, *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._reader = self._process.stdout
        self._writer = self._process.stdin
        self._running = True
        asyncio.create_task(self._read_loop())
        await self._initialize()

    async def _send(self, method: str, params: dict | None = None) -> dict:
        self._request_id += 1
        req_id = self._request_id
        msg = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {},
        }
        future = asyncio.get_event_loop().create_future()
        self._pending[req_id] = future
        data = json.dumps(msg) + "\n"
        self._writer.write(data.encode())
        await self._writer.drain()
        try:
            return await asyncio.wait_for(future, timeout=30)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise TimeoutError(f"MCP request '{method}' timed out")

    async def _read_loop(self):
        while self._running and self._reader:
            try:
                line = await self._reader.readline()
                if not line:
                    break
                msg = json.loads(line.decode())
                if "id" in msg and msg["id"] in self._pending:
                    future = self._pending.pop(msg["id"])
                    if "error" in msg:
                        future.set_exception(RuntimeError(msg["error"].get("message", "MCP error")))
                    else:
                        future.set_result(msg.get("result", {}))
            except Exception:
                break
        self._running = False

    async def _initialize(self):
        result = await self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "nuntius", "version": "0.2.1"},
        })
        await self._send("notifications/initialized")
        self.server_info = result.get("serverInfo", {})
        tools_result = await self._send("tools/list")
        self._tools = tools_result.get("tools", [])

    async def list_tools(self) -> list[dict]:
        if not self._running:
            await self.connect()
        return self._tools

    async def call_tool(self, name: str, arguments: dict) -> str:
        if not self._running:
            await self.connect()
        result = await self._send("tools/call", {"name": name, "arguments": arguments})
        content = result.get("content", [])
        parts = []
        for c in content:
            if c.get("type") == "text":
                parts.append(c.get("text", ""))
            else:
                parts.append(json.dumps(c))
        return "\n".join(parts)

    async def close(self):
        self._running = False
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except Exception:
                self._process.kill()
            self._process = None


class MCPManager:
    def __init__(self):
        self.servers: dict[str, MCPServer] = {}

    def add_server(self, name: str, command: str, args: list[str] | None = None):
        self.servers[name] = MCPServer(name, command, args)

    async def connect_all(self):
        for server in self.servers.values():
            try:
                await server.connect()
            except Exception as e:
                print(f"MCP '{server.name}': {e}")

    async def get_all_tools(self) -> list[tuple[str, dict]]:
        tools = []
        for name, server in self.servers.items():
            try:
                st = await server.list_tools()
                for t in st:
                    tools.append((name, t))
            except Exception:
                pass
        return tools

    async def execute_tool(self, server_name: str, tool_name: str, arguments: dict) -> str:
        server = self.servers.get(server_name)
        if not server:
            return f"MCP server '{server_name}' not found"
        return await server.call_tool(tool_name, arguments)

    async def close_all(self):
        for server in self.servers.values():
            await server.close()
