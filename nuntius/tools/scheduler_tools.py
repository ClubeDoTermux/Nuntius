import logging

from ..core import scheduler
from .registry import BaseTool, register

logger = logging.getLogger("nuntius.tools.scheduler")


class ScheduleTask(BaseTool):
    name = "schedule_task"
    description = "Agenda um comando no cron do sistema. Exemplo: schedule_task(cron='0 9 * * *', command='echo ola', task_id='saudacao')"
    parameters = {
        "type": "object",
        "properties": {
            "cron": {"type": "string", "description": "Expressao cron de 5 campos: minuto hora dia mes dia_semana (ex: '0 9 * * *' = todo dia as 9h)"},
            "command": {"type": "string", "description": "Comando shell a executar"},
            "task_id": {"type": "string", "description": "ID unico para a tarefa (opcional, auto-gerado se vazio)"},
        },
        "required": ["cron", "command"],
    }

    async def execute(self, cron: str, command: str, task_id: str = "") -> str:
        return scheduler.schedule(cron, command, task_id)


class ListScheduledTasks(BaseTool):
    name = "list_scheduled_tasks"
    description = "Lista todas as tarefas Nuntius agendadas no cron do sistema"
    parameters = {
        "type": "object",
        "properties": {},
    }

    async def execute(self) -> str:
        tasks = scheduler.list_tasks()
        if not tasks:
            return "Nenhuma tarefa agendada."
        return "\n".join(
            f"  [{t['id']}] {t['cron']} -> {t['command']}" for t in tasks
        )


class RemoveScheduledTask(BaseTool):
    name = "remove_scheduled_task"
    description = "Remove uma tarefa agendada pelo task_id"
    parameters = {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "ID da tarefa a remover"},
        },
        "required": ["task_id"],
    }

    async def execute(self, task_id: str) -> str:
        return scheduler.remove_task(task_id)


class ClearScheduledTasks(BaseTool):
    name = "clear_scheduled_tasks"
    description = "Remove TODAS as tarefas Nuntius agendadas no cron"
    parameters = {
        "type": "object",
        "properties": {},
    }

    async def execute(self) -> str:
        return scheduler.clear_all_tasks()


register(ScheduleTask())
register(ListScheduledTasks())
register(RemoveScheduledTask())
register(ClearScheduledTasks())
