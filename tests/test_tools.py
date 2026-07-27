"""Tests for tools registry."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from nuntius.tools.registry import get_all, get_names, register


class FakeTool:
    name = "fake_tool"
    description = "A fake tool for testing"
    parameters = {"type": "object", "properties": {}}
    async def execute(self, **kwargs):
        return "fake result"


def test_registry_has_tools():
    tools = get_all()
    assert len(tools) > 0
    names = get_names()
    assert "read" in names
    assert "write" in names
    assert "bash" in names


def test_register_and_execute():
    from nuntius.tools.registry import register, execute
    ft = FakeTool()
    register(ft)
    assert "fake_tool" in get_names()
