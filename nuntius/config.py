import os
from pathlib import Path

import yaml

CONFIG_DIR = Path(os.getenv("NUNTIUS_CONFIG_DIR", Path.home() / ".config" / "nuntius"))
DATA_DIR = Path(os.getenv("NUNTIUS_DATA_DIR", Path.home() / ".local" / "share" / "nuntius"))
CONFIG_PATH = CONFIG_DIR / "config.yaml"

PROVIDER_INFO = {
    "openai": {
        "name": "OpenAI",
        "url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "site": "https://platform.openai.com/api-keys",
        "free": False,
    },
    "deepseek": {
        "name": "DeepSeek",
        "url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "site": "https://platform.deepseek.com/api_keys",
        "free": False,
    },
    "groq": {
        "name": "Groq",
        "url": "https://api.groq.com/openai/v1",
        "models": ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"],
        "site": "https://console.groq.com/keys",
        "free": True,
    },
    "ollama": {
        "name": "Ollama (local)",
        "url": "http://localhost:11434/v1",
        "models": [
            "llama3.2", "llama3.1", "mistral", "codellama",
            "qwen2.5", "phi4", "llava",
        ],
        "site": "",
        "free": True,
    },
}

DEFAULT_CONFIG = {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "providers": {name: {"api_key": "", "base_url": info["url"]} for name, info in PROVIDER_INFO.items()},
    "platforms": {
        "telegram": {"enabled": False, "token": ""},
        "discord": {"enabled": False, "token": ""},
        "github": {"enabled": False, "token": ""},
        "drive": {"enabled": False, "credentials_path": ""},
    },
    "security": {"bash_approval": True},
    "auto_learn": {"enabled": True},
    "memory": {"enabled": True, "db_path": str(DATA_DIR / "nuntius.db")},
    "tools": {"enabled": True},
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH) as f:
        user = yaml.safe_load(f) or {}
    merged = DEFAULT_CONFIG.copy()
    if "providers" in user:
        for k, v in user["providers"].items():
            if k in merged["providers"]:
                merged["providers"][k].update(v)
            else:
                merged["providers"][k] = v
    for key in ("provider", "model", "memory", "tools", "platforms", "security", "auto_learn"):
        if key in user:
            merged[key] = user[key]
    return merged


def save_config(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)


def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_active_provider(cfg: dict) -> dict:
    name = cfg.get("provider", "openai")
    return cfg.get("providers", {}).get(name, cfg["providers"]["openai"])
