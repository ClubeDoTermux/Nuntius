import pytest

from nuntius.agents.subagent import SubAgent, SYSTEM_PROMPTS
from nuntius.core.orchestrator import Orchestrator, SubAgentInfo


def test_subagent_creation():
    sub = SubAgent(role="code")
    assert sub.role == "code"
    assert sub.system_prompt == SYSTEM_PROMPTS["code"]
    assert len(sub.messages) == 1
    assert sub.messages[0]["role"] == "system"
    assert sub.messages[0]["content"] == SYSTEM_PROMPTS["code"]


def test_subagent_custom_prompt():
    sub = SubAgent(system_prompt="Voce e um testador.")
    assert sub.system_prompt == "Voce e um testador."


def test_subagent_tool_filter():
    sub = SubAgent(tools=["read", "write"])
    assert sub.tool_names == ["read", "write"]
    from nuntius.tools.registry import _tools
    assert "read" in _tools
    assert "write" in _tools


def test_subagent_unknown_role():
    sub = SubAgent(role="unknown_role_xyz")
    assert sub.system_prompt == "You are a helpful AI assistant."


def test_orchestrator_init():
    orch = Orchestrator()
    assert orch.subagents == {}
    assert orch._agent_instances == {}


def test_subagent_info():
    info = SubAgentInfo("id1", "code", "write a test")
    assert info.agent_id == "id1"
    assert info.role == "code"
    assert info.task == "write a test"
    assert info.status == "running"
    info.done("finished")
    assert info.status == "done"
    assert info.result == "finished"


def test_orchestrator_list_empty():
    orch = Orchestrator()
    assert orch.list_subagents() == []


def test_orchestrator_get_result_not_found():
    orch = Orchestrator()
    result = orch.get_result("nonexistent")
    assert "nao encontrado" in result


def test_tools_registered():
    from nuntius.tools.registry import _tools
    assert "delegate" in _tools
    assert "list_subagents" in _tools


def test_orchestrator_delegate_no_provider():
    orch = Orchestrator()
    import asyncio
    result = asyncio.run(orch.delegate("say hello", role="writer"))
    assert "subagent" in result.lower() or result.strip()


def test_subagent_role_prompts():
    assert "code" in SYSTEM_PROMPTS
    assert "shell" in SYSTEM_PROMPTS
    assert "search" in SYSTEM_PROMPTS
    assert "writer" in SYSTEM_PROMPTS
    assert "debug" in SYSTEM_PROMPTS
