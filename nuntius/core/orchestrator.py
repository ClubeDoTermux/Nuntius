import logging
import uuid

logger = logging.getLogger("nuntius.orchestrator")


class SubAgentInfo:
    def __init__(self, agent_id: str, role: str, task: str):
        self.agent_id = agent_id
        self.role = role
        self.task = task
        self.status = "running"
        self.result = ""

    def done(self, result: str):
        self.result = result
        self.status = "done"


class Orchestrator:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.subagents: dict[str, SubAgentInfo] = {}
        self._agent_instances: dict[str, "SubAgent"] = {}

    async def delegate(
        self,
        task: str,
        role: str = "",
        system_prompt: str = "",
        tools: list[str] | None = None,
        agent_id: str = "",
    ) -> str:
        agent_id = agent_id or str(uuid.uuid4())[:8]
        info = SubAgentInfo(agent_id, role or "assistant", task)
        self.subagents[agent_id] = info

        try:
            from ..config import load_config, get_active_provider
            from ..providers.base import ProviderRegistry
            from ..agents.subagent import SubAgent
        except ImportError:
            from nuntius.config import load_config, get_active_provider
            from nuntius.providers.base import ProviderRegistry
            from nuntius.agents.subagent import SubAgent

        cfg = self.config if isinstance(self.config, dict) else load_config()
        sub = SubAgent(
            role=role,
            system_prompt=system_prompt,
            tools=tools,
            config=cfg,
        )
        self._agent_instances[agent_id] = sub

        try:
            logger.info(f"Subagent {agent_id} ({role}) started: {task[:60]}")
            result = await sub.run(task)
            info.done(result)
            logger.info(f"Subagent {agent_id} finished ({len(result)} chars)")
            summary = result[:1500]
            return f"[Subagent {agent_id} ({role})]\n{summary}"
        except Exception as e:
            info.status = "error"
            info.result = str(e)
            logger.warning(f"Subagent {agent_id} failed: {e}")
            return f"[Subagent {agent_id} erro: {e}]"
        finally:
            await sub.close()

    def list_subagents(self) -> list[dict]:
        return [
            {
                "id": sid,
                "role": info.role,
                "task": info.task[:80],
                "status": info.status,
                "result_len": len(info.result),
            }
            for sid, info in self.subagents.items()
        ]

    def get_result(self, agent_id: str) -> str:
        info = self.subagents.get(agent_id)
        if not info:
            return f"Subagent '{agent_id}' nao encontrado."
        return info.result or "(sem resultado)"

    async def close_all(self):
        for sub in self._agent_instances.values():
            try:
                await sub.close()
            except Exception:
                pass
        self._agent_instances.clear()
