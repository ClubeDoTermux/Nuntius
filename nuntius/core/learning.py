import json
import logging
import re
from datetime import datetime
from pathlib import Path

from ..config import DATA_DIR

logger = logging.getLogger("nuntius.learning")

LEARNING_PATH = DATA_DIR / "learning.json"


_INDICATORS_FAILURE = [
    "erro", "error", "failed", "failure", "not found",
    "permission denied", "timeout", "could not", "unable to",
    "não encontrado", "falhou", "negado", "inexistente",
]


def _is_successful(tool_name: str, result: str) -> bool:
    if not result:
        return False
    result_lower = result.lower().strip()
    for indicator in _INDICATORS_FAILURE:
        if result_lower.startswith(indicator) or result_lower.startswith(indicator.capitalize()):
            return False
    if len(result) < 5 and tool_name not in ("current_time", "random_number", "random_uuid"):
        return False
    return True


def _extract_pattern(user_input: str) -> str:
    text = user_input.lower().strip()
    stop_words = [
        "pode", "por favor", "pfv", "pf", "quero", "gostaria",
        "preciso", "me ajuda", "please", "can you", "could you",
        "i need", "i want", "help me",
    ]
    for w in stop_words:
        text = text.replace(w, "")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:60] or user_input[:60]


class ImprovedSkillsManager:
    def __init__(self, skills_path: str = ""):
        self.path = Path(skills_path or LEARNING_PATH)
        self.skills: dict[str, dict] = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self.skills = data.get("skills", {})
            except Exception:
                self.skills = {}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"skills": self.skills}
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def record(self, pattern: str, approach: str, success: bool):
        entry = self.skills.get(pattern)
        if entry:
            entry["count"] += 1
            entry["success_count"] += 1 if success else 0
            entry["failure_count"] += 1 if not success else 0
            entry["last_used"] = datetime.now().isoformat()
            if success and entry["count"] >= 2:
                entry["approach"] = approach
        else:
            self.skills[pattern] = {
                "approach": approach,
                "count": 1,
                "success_count": 1 if success else 0,
                "failure_count": 1 if not success else 0,
                "created": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
            }
        if self.skills[pattern]["count"] >= 2:
            self._save()

    def get_lessons(self) -> str:
        reliable = [
            p for p, d in self.skills.items()
            if d.get("count", 0) >= 2 and d.get("success_count", 0) > d.get("failure_count", 0)
        ]
        reliable.sort(
            key=lambda p: self.skills[p]["success_count"] / max(self.skills[p]["count"], 1),
            reverse=True,
        )
        if not reliable:
            return ""
        lines = ["## Lessons Learned (from past interactions)"]
        for pattern in reliable[:5]:
            entry = self.skills[pattern]
            score = entry["success_count"] / max(entry["count"], 1) * 100
            lines.append(
                f"- **{pattern}**: {entry['approach'][:120]} "
                f"(confianca: {score:.0f}%, usos: {entry['count']})"
            )
        return "\n".join(lines)

    def get_stats(self) -> dict:
        total = len(self.skills)
        reliable = sum(
            1 for d in self.skills.values()
            if d.get("count", 0) >= 2 and d.get("success_count", 0) > d.get("failure_count", 0)
        )
        return {
            "total_patterns": total,
            "reliable_lessons": reliable,
            "skills": self.skills,
        }


class ToolStatsTracker:
    def __init__(self):
        self.tool_stats: dict[str, dict] = {}

    def record(self, name: str, success: bool):
        entry = self.tool_stats.setdefault(name, {"successes": 0, "failures": 0, "total": 0})
        entry["total"] += 1
        if success:
            entry["successes"] += 1
        else:
            entry["failures"] += 1

    def get_report(self) -> str:
        if not self.tool_stats:
            return ""
        lines = ["## Tool Performance Stats"]
        for name, stats in sorted(self.tool_stats.items()):
            rate = stats["successes"] / max(stats["total"], 1) * 100
            bar = "█" * int(rate / 10) + "░" * (10 - int(rate / 10))
            lines.append(f"  {bar} {name}: {rate:.0f}% ({stats['successes']}/{stats['total']})")
        return "\n".join(lines) if len(lines) > 1 else ""


class LearningLoop:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.skills = ImprovedSkillsManager()
        self.tool_stats = ToolStatsTracker()
        self.last_pattern = ""
        self.last_approach = ""

    def evaluate_tool(self, name: str, result: str):
        success = _is_successful(name, result)
        self.tool_stats.record(name, success)
        self.last_approach = f"usou {name} para {result[:80]}"
        logger.debug(f"Tool '{name}': {'OK' if success else 'FAIL'} ({len(result)} chars)")
        return success

    def learn(self, user_input: str, response: str, explicit_success: bool | None = None):
        if not self.config.get("enabled", True):
            return
        pattern = _extract_pattern(user_input)
        approach = (response or self.last_approach)[:200]
        success = explicit_success if explicit_success is not None else self._infer_success()
        self.skills.record(pattern, approach, success)
        self.last_pattern = pattern
        self.last_approach = approach

    def _infer_success(self) -> bool:
        successes = [s for s in self.tool_stats.tool_stats.values()]
        if not successes:
            return True
        total_ok = sum(s["successes"] for s in successes)
        total_all = sum(s["total"] for s in successes)
        return total_ok >= total_all * 0.5 if total_all > 0 else True

    def get_feedback(self) -> str:
        parts = []
        lessons = self.skills.get_lessons()
        if lessons:
            parts.append(lessons)
        stats = self.tool_stats.get_report()
        if stats:
            parts.append(stats)
        return "\n\n".join(parts)

    def mark_good(self):
        if self.last_pattern:
            self.skills.record(self.last_pattern, self.last_approach, success=True)
            return f"Padrao '{self.last_pattern}' marcado como bem-sucedido."
        return "Nenhuma interacao anterior para avaliar."

    def mark_bad(self):
        if self.last_pattern:
            self.skills.record(self.last_pattern, self.last_approach, success=False)
            return f"Padrao '{self.last_pattern}' marcado como mal-sucedido."
        return "Nenhuma interacao anterior para avaliar."

    def get_stats(self) -> dict:
        return {
            "skills": self.skills.get_stats(),
            "tools": self.tool_stats.tool_stats,
        }
