import logging

from .registry import BaseTool, register

logger = logging.getLogger("nuntius.tools.orchestrator")

_orchestrator = None


def _get_orch():
    global _orchestrator
    if _orchestrator is None:
        from ..core.orchestrator import Orchestrator
        _orchestrator = Orchestrator()
    return _orchestrator


async def close_orchestrator():
    global _orchestrator
    if _orchestrator:
        await _orchestrator.close_all()
        _orchestrator = None


class Delegate(BaseTool):
    name = "delegate"
    description = "Delega uma tarefa a um subagente isolado com funcao especifica. Use para tarefas complexas que merecem foco dedicado."
    parameters = {
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "Descricao detalhada da tarefa para o subagente"},
            "role": {
                "type": "string",
                "description": "Funcao do subagente: 'code', 'shell', 'search', 'writer', 'debug', ou personalizado",
                "enum": ["code", "shell", "search", "writer", "debug", ""],
            },
            "system_prompt": {
                "type": "string",
                "description": "Instrucao personalizada para o subagente (opcional, substitui role se fornecido)",
            },
            "tools": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Lista de ferramentas permitidas (ex: ['run_python', 'run_shell', 'read', 'write']). Vazio = todas",
            },
        },
        "required": ["task"],
    }

    async def execute(self, task: str, role: str = "", system_prompt: str = "", tools: list[str] = None) -> str:
        orch = _get_orch()
        return await orch.delegate(task, role=role, system_prompt=system_prompt, tools=tools)


class ListSubAgents(BaseTool):
    name = "list_subagents"
    description = "Lista todos os subagentes ativos e seus status"
    parameters = {
        "type": "object",
        "properties": {},
    }

    async def execute(self) -> str:
        orch = _get_orch()
        agents = orch.list_subagents()
        if not agents:
            return "Nenhum subagente ativo."
        lines = ["Subagentes:"]
        for a in agents:
            status_icon = "✅" if a["status"] == "done" else "⏳" if a["status"] == "running" else "❌"
            lines.append(f"  {status_icon} [{a['id']}] {a['role']}: {a['task']} ({a['status']}, {a['result_len']} chars)")
        return "\n".join(lines)


register(Delegate())
register(ListSubAgents())
