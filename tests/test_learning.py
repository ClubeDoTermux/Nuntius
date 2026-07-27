import json
import tempfile
from pathlib import Path

import pytest

from nuntius.core.learning import (
    LearningLoop,
    ToolStatsTracker,
    ImprovedSkillsManager,
    _is_successful,
    _extract_pattern,
)


def test_is_successful():
    assert _is_successful("read", "file content here")
    assert _is_successful("current_time", "12:00") is True  # exempt from length check
    assert _is_successful("read", "") is False
    assert _is_successful("read", "Erro: file not found") is False
    assert _is_successful("read", "Error: permission denied") is False
    assert _is_successful("run_shell", "command output ok")


def test_extract_pattern():
    result = _extract_pattern("Pode criar um arquivo para mim?")
    assert "criar" in result
    assert "arquivo" in result
    result2 = _extract_pattern("Please can you help me make a website")
    assert "make" in result2
    assert "website" in result2


def test_tool_stats_tracker():
    tracker = ToolStatsTracker()
    tracker.record("read", success=True)
    tracker.record("read", success=True)
    tracker.record("run_shell", success=False)
    assert tracker.tool_stats["read"]["successes"] == 2
    assert tracker.tool_stats["read"]["failures"] == 0
    assert tracker.tool_stats["run_shell"]["failures"] == 1
    report = tracker.get_report()
    assert "read" in report
    assert "run_shell" in report


def test_improved_skills_manager(tmp_path):
    path = tmp_path / "test_learning.json"
    mgr = ImprovedSkillsManager(skills_path=str(path))
    mgr.record("criar website", "usar write para criar arquivos", success=True)
    mgr.record("criar website", "usar write para criar arquivos", success=True)
    mgr.record("instalar pacote", "usar pip install", success=False)

    assert "criar website" in mgr.skills
    assert mgr.skills["criar website"]["count"] == 2
    assert mgr.skills["criar website"]["success_count"] == 2

    stats = mgr.get_stats()
    assert stats["total_patterns"] == 2
    assert stats["reliable_lessons"] == 1

    lessons = mgr.get_lessons()
    assert "criar website" in lessons


def test_improved_skills_persistence(tmp_path):
    path = tmp_path / "test_learning.json"
    mgr1 = ImprovedSkillsManager(skills_path=str(path))
    mgr1.record("test", "approach", success=True)
    mgr1.record("test", "approach", success=True)

    mgr2 = ImprovedSkillsManager(skills_path=str(path))
    assert "test" in mgr2.skills
    assert mgr2.skills["test"]["count"] == 2


def test_learning_loop():
    loop = LearningLoop({"enabled": True})
    loop.evaluate_tool("read", "file content")
    loop.evaluate_tool("run_shell", "Error: command not found")
    loop.learn("criar arquivo", "usei write para criar", explicit_success=True)
    assert loop.last_pattern == "criar arquivo"
    feedback = loop.get_feedback()
    assert feedback is not None


def test_learning_loop_mark_good_bad():
    loop = LearningLoop({"enabled": True})
    loop.learn("task1", "approach1", explicit_success=True)
    result = loop.mark_good()
    assert "bem-sucedido" in result
    result = loop.mark_bad()
    assert "mal-sucedido" in result


def test_learning_loop_no_pattern():
    loop = LearningLoop({"enabled": True})
    result = loop.mark_good()
    assert "Nenhuma" in result


def test_get_stats():
    loop = LearningLoop({"enabled": True})
    loop.evaluate_tool("read", "content")
    loop.learn("do something", "used read", explicit_success=True)
    stats = loop.get_stats()
    assert "skills" in stats
    assert "tools" in stats
