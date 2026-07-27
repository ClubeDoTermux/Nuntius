"""Tests for SkillsManager."""
from pathlib import Path
import tempfile
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from nuntius.skills.manager import SkillsManager


def test_learn_and_list():
    sm = SkillsManager()
    sm.skills.clear()
    sm._save()
    sm.learn("test_skill", "do something")
    assert "test_skill" in sm.list_skills()
    assert sm.get_skill("test_skill") == "do something"


def test_forget():
    sm = SkillsManager()
    sm.skills.clear()
    sm._save()
    sm.learn("skill_a", "instruction a")
    sm.forget("skill_a")
    assert "skill_a" not in sm.list_skills()


def test_empty_skills():
    sm = SkillsManager()
    sm.skills.clear()
    sm._save()
    assert sm.list_skills() == []
    assert sm.to_system_prompt() == ""


def test_learn_from_conversation():
    sm = SkillsManager()
    sm.skills.clear()
    sm._save()
    sm.learn_from_conversation("create website", "use write tool")
    assert len(sm.list_skills()) > 0
    assert "write" in sm.get_skill(list(sm.skills.keys())[0])
