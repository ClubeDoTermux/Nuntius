import pytest

from nuntius.core import scheduler


def test_validate_cron():
    assert scheduler._validate_cron("0 9 * * *") == ""
    assert scheduler._validate_cron("0 9 * *") != ""
    assert scheduler._validate_cron("") != ""


def test_schedule_no_crontab(monkeypatch):
    monkeypatch.setattr(scheduler, "_crontab_available", lambda: False)
    result = scheduler.schedule("0 9 * * *", "echo test", "test_task")
    assert "crontab" in result.lower() or "disponivel" in result


def test_list_tasks_no_crontab(monkeypatch):
    monkeypatch.setattr(scheduler, "_crontab_available", lambda: False)
    assert scheduler.list_tasks() == []


def test_remove_task_no_crontab(monkeypatch):
    monkeypatch.setattr(scheduler, "_crontab_available", lambda: False)
    result = scheduler.remove_task("test")
    assert "crontab" in result.lower() or "disponivel" in result


def test_clear_all_tasks_no_crontab(monkeypatch):
    monkeypatch.setattr(scheduler, "_crontab_available", lambda: False)
    result = scheduler.clear_all_tasks()
    assert "crontab" in result.lower() or "disponivel" in result


def test_schedule_invalid_cron():
    result = scheduler.schedule("invalid", "echo test")
    assert "invalido" in result.lower() or "formato" in result.lower()


def test_schedule_empty_command():
    result = scheduler.schedule("0 9 * * *", "")
    assert "vazio" in result.lower()


def test_tools_registered():
    from nuntius.tools.registry import _tools
    assert "schedule_task" in _tools
    assert "list_scheduled_tasks" in _tools
    assert "remove_scheduled_task" in _tools
    assert "clear_scheduled_tasks" in _tools


def test_validate_cron_valid():
    valid = [
        "0 9 * * *",
        "*/5 * * * *",
        "30 8 * * 1-5",
        "0 0 1 1 *",
        "15 10 * * 1,3,5",
    ]
    for expr in valid:
        assert scheduler._validate_cron(expr) == "", f"Expected valid: {expr}"
