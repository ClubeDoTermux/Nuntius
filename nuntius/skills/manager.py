import json
from pathlib import Path

from ..config import DATA_DIR


SKILLS_PATH = DATA_DIR / "skills.json"


class SkillsManager:
    def __init__(self):
        self.skills: dict[str, str] = {}
        self._load()

    def _load(self):
        if SKILLS_PATH.exists():
            try:
                self.skills = json.loads(SKILLS_PATH.read_text())
            except Exception:
                self.skills = {}

    def _save(self):
        SKILLS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SKILLS_PATH.write_text(json.dumps(self.skills, indent=2))

    def learn(self, name: str, instruction: str):
        self.skills[name] = instruction
        self._save()

    def get_skill(self, name: str) -> str:
        return self.skills.get(name, "")

    def list_skills(self) -> list[str]:
        return list(self.skills.keys())

    def forget(self, name: str):
        self.skills.pop(name, None)
        self._save()

    def learn_from_conversation(self, task: str, solution: str):
        name = task.lower().replace(" ", "_")[:40]
        instruction = f"Quando perguntarem sobre '{task}', use esta abordagem:\n{solution}"
        self.learn(name, instruction)

    def to_system_prompt(self) -> str:
        if not self.skills:
            return ""
        lines = ["## Skills aprendidas"]
        for name, instruction in sorted(self.skills.items()):
            lines.append(f"\n### {name}\n{instruction}")
        return "\n".join(lines)
