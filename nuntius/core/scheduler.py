import logging
import re
import shutil
import subprocess
import uuid

logger = logging.getLogger("nuntius.scheduler")

TASK_MARKER = "#NUNTIUS_TASK:"
CRON_FIELDS = 5


def _validate_cron(expr: str) -> str:
    parts = expr.strip().split()
    if len(parts) != CRON_FIELDS:
        return "Formato invalido. Use: minuto hora dia mes dia_semana (5 campos)"
    return ""


def _get_crontab() -> list[str]:
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.splitlines()
        return []
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    except Exception as e:
        logger.debug(f"crontab -l failed: {e}")
        return []


def _set_crontab(lines: list[str]):
    text = "\n".join(lines) + "\n" if lines else ""
    proc = subprocess.run(
        ["crontab", "-"],
        input=text, capture_output=True, text=True, timeout=10,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Erro ao atualizar crontab: {proc.stderr.strip()}")


def _crontab_available() -> bool:
    return shutil.which("crontab") is not None


def schedule(cron_expr: str, command: str, task_id: str = "") -> str:
    err = _validate_cron(cron_expr)
    if err:
        return err

    if not _crontab_available():
        return "crontab nao disponivel no sistema. Instale cron (apt install cron) ou use Termux: pkg install cronie."

    if not command:
        return "Comando vazio."

    task_id = task_id or str(uuid.uuid4())[:8]
    existing = _get_crontab()
    for line in existing:
        if f"{TASK_MARKER}{task_id}" in line:
            return f"Task ID '{task_id}' ja existe. Use outro ID ou remova primeiro."

    entry = f"{cron_expr.strip()} {command.strip()}  {TASK_MARKER}{task_id}"
    existing.append(entry)
    try:
        _set_crontab(existing)
        logger.info(f"Scheduled task {task_id}: {cron_expr} {command}")
        return f"Tarefa '{task_id}' agendada: '{cron_expr} {command}'"
    except RuntimeError as e:
        return str(e)


def list_tasks() -> list[dict]:
    if not _crontab_available():
        return []
    lines = _get_crontab()
    tasks = []
    for line in lines:
        if TASK_MARKER in line:
            match = re.search(rf"{TASK_MARKER}(\S+)", line)
            tid = match.group(1) if match else "?"
            parts = line.strip().split(None, CRON_FIELDS + 1)
            cron_expr = " ".join(parts[:CRON_FIELDS]) if len(parts) > CRON_FIELDS else ""
            cmd = parts[CRON_FIELDS] if len(parts) > CRON_FIELDS else ""
            cmd = re.sub(rf"\s*{TASK_MARKER}\S+", "", cmd).strip()
            tasks.append({"id": tid, "cron": cron_expr, "command": cmd})
    return tasks


def remove_task(task_id: str) -> str:
    if not _crontab_available():
        return "crontab nao disponivel."

    lines = _get_crontab()
    filtered = [l for l in lines if f"{TASK_MARKER}{task_id}" not in l]
    if len(filtered) == len(lines):
        return f"Task '{task_id}' nao encontrada."

    try:
        _set_crontab(filtered)
        logger.info(f"Removed task {task_id}")
        return f"Tarefa '{task_id}' removida."
    except RuntimeError as e:
        return str(e)


def clear_all_tasks() -> str:
    if not _crontab_available():
        return "crontab nao disponivel."
    lines = _get_crontab()
    filtered = [l for l in lines if TASK_MARKER not in l]
    removed = len(lines) - len(filtered)
    if removed == 0:
        return "Nenhuma tarefa Nuntius agendada."
    try:
        _set_crontab(filtered)
        return f"{removed} tarefa(s) removida(s)."
    except RuntimeError as e:
        return str(e)
