"""Tests for config."""
from pathlib import Path
import os
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).parent.parent))

from nuntius.config import load_config, DEFAULT_CONFIG, PROVIDER_INFO, get_active_provider


def test_default_config():
    cfg = load_config()
    assert "provider" in cfg
    assert "model" in cfg
    assert "security" in cfg
    assert cfg["provider"] in PROVIDER_INFO


def test_get_active_provider():
    cfg = DEFAULT_CONFIG.copy()
    prov = get_active_provider(cfg)
    assert "api_key" in prov
    assert "base_url" in prov


def test_env_var_override(monkeypatch):
    monkeypatch.setenv("NUNTIUS_OPENAI_KEY", "sk-test-env-key")
    cfg = load_config()
    assert cfg["providers"]["openai"]["api_key"] == "sk-test-env-key"
